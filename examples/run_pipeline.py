#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_pipeline.py —— 一组照片 → 一个干净的稠密点云（7 阶段全自动）

阶段划分（每段对应现实里的一步，块首注释写明这块最终干了什么）：

  阶段 1/7 提特征(COLMAP)   → build\\database.db
  阶段 2/7 配对(COLMAP)     → 数据库里多一份"匹配账本"
  阶段 3/7 解算稀疏(COLMAP) → build\\sparse\\        （第一次出现 3D）
  阶段 4/7 去畸变(COLMAP)   → build\\dense\\
  阶段 5/7 转格式(OpenMVS)  → build\\scene.mvs
  阶段 6/7 稠密化(OpenMVS)  → build\\scene_dense.ply    （GPU，最慢）
  阶段 7/7 洗列表(本仓库工具) → build\\scene_dense_clean.ply   ★最终产物

用法：
    python run_pipeline.py                                # 用下面 CONFIG 的默认值
    python run_pipeline.py --images D:\\data\\photos --out D:\\data\\build
    python run_pipeline.py --limit 3                      # 只跑前 3 组

前置：
    - COLMAP 已安装（改 CONFIG['colmap']）
    - OpenMVS 已解压（改 CONFIG['openmvs']，本仓库 bin\\ 即可）
    - 本仓库 tools\\ply_strip.py 在位
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ─────────────────────── 配置区：要改就改这里 ───────────────────────
CONFIG = {
    # COLMAP 启动器（Windows 一般是 COLMAP.bat）
    'colmap':  r'D:\app\colmap\COLMAP-4.2.0-windows-2022-CUDA-cuDSS-Caspar-GUI\COLMAP.bat',
    # OpenMVS 目录（本仓库 bin/ 的绝对路径）
    'openmvs': r'D:\app\openmvs\openmvs-sm120',
    # ply_strip.py 绝对路径
    'strip':   str(Path(__file__).resolve().parent.parent / 'tools' / 'ply_strip.py'),
    # 输入：要么是"一组照片的目录"，要么是"多组照片的父目录"（每组一个子目录）
    'images':  r'D:\data\photos',
    # 输出根目录：每组会在下面得到自己的 build 目录
    'out':     r'D:\data\build',
    # 相机与特征参数
    'max_image_size': 3200,
    'max_features':   8192,
    'camera_model':   'SIMPLE_RADIAL',
    'single_camera':  1,
    # CUDA 设备编号（只数 N 卡，独显通常是 0）
    'gpu_index':      0,
}
# ────────────────────────────────────────────────────────────────


def run(cmd, cwd=None, stage=''):
    """跑一条命令；非 0 退出码视为这一阶段失败。"""
    printable = ' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in cmd)
    print(f'\n[{stage}] {printable}')
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode != 0:
        print(f'!! {stage} 失败（exit={r.returncode}），跳过这一组')
        return False
    return True


def process_group(img_dir: Path, build: Path, cfg: dict) -> Path | None:
    build.mkdir(parents=True, exist_ok=True)
    db = build / 'database.db'
    colmap, mvs = cfg['colmap'], Path(cfg['openmvs'])

    # ───── 阶段 1/7：提特征 —— 在每张照片上找 ~1 万个特征点，存进数据库 ─────
    if not db.exists():
        ok = run([
            colmap, 'feature_extractor',
            '--database_path', db,
            '--image_path', img_dir,
            '--ImageReader.single_camera', cfg['single_camera'],
            '--ImageReader.camera_model', cfg['camera_model'],
            '--SiftExtraction.max_num_features', cfg['max_features'],
            '--FeatureExtraction.max_image_size', cfg['max_image_size'],
            '--FeatureExtraction.use_gpu', 1,
            '--FeatureExtraction.gpu_index', cfg['gpu_index'],
        ], stage='1/7 提特征')
        if not ok:
            return None

    # ───── 阶段 2/7：配对 —— 两两比较指纹，找出哪些照片拍到了同一点 ─────
    if not run([
        colmap, 'exhaustive_matcher',
        '--database_path', db,
        '--FeatureMatching.use_gpu', 1,
        '--FeatureMatching.gpu_index', cfg['gpu_index'],
    ], stage='2/7 配对'):
        return None

    # ───── 阶段 3/7：解算稀疏 —— 反推相机位置 + 稀疏 3D 点（第一次出现 3D）─────
    sparse = build / 'sparse'
    sparse.mkdir(exist_ok=True)          # mapper 不会自己建目录
    if not (sparse / '0').exists():
        if not run([
            colmap, 'mapper',
            '--database_path', db,
            '--image_path', img_dir,
            '--output_path', sparse,
        ], stage='3/7 解算稀疏'):
            return None

    # ───── 阶段 4/7：挑模型 + 去畸变 —— MVS 只认理想相机 ─────
    models = sorted(sparse.rglob('points3D.bin'),
                    key=lambda p: p.stat().st_size, reverse=True)
    if not models:
        print('!! 没解出模型，跳过这一组')
        return None
    model_dir = models[0].parent
    print(f'   挑中的模型：{model_dir}')

    dense = build / 'dense'
    if not run([
        colmap, 'image_undistorter',
        '--image_path', img_dir,
        '--input_path', model_dir,
        '--output_path', dense,
        '--output_type', 'COLMAP',
        '--max_image_size', cfg['max_image_size'],
    ], stage='4/7 去畸变'):
        return None

    # ───── 阶段 5/7：转格式 —— COLMAP 成果翻译成 OpenMVS 场景（纯搬运）─────
    scene = build / 'scene.mvs'
    if not run([
        mvs / 'InterfaceCOLMAP.exe',
        '-i', dense,
        '-o', scene,
        '--image-folder', (dense / 'images').resolve(),   # 必须绝对路径！
    ], stage='5/7 转格式'):
        return None

    # ───── 阶段 6/7：稠密化 —— 逐像素估深度，把稀疏点加密成几百万点（GPU，最慢）─────
    ply_raw = build / 'scene_dense.ply'
    if not ply_raw.exists():
        if not run([
            mvs / 'DensifyPointCloud.exe',
            '-i', scene,
            '-o', build / 'scene_dense.mvs',
            '--cuda-device', cfg['gpu_index'],
        ], cwd=build, stage='6/7 稠密化'):
            return None

    # ───── 阶段 7/7：洗列表 —— 剥掉 CloudCompare 读不了的可变长列表 ─────
    ply_clean = build / 'scene_dense_clean.ply'
    if not run([
        sys.executable, cfg['strip'], ply_raw, ply_clean,
    ], stage='7/7 洗列表'):
        return None

    print(f'\n✅ 完成：{ply_clean}  ({ply_clean.stat().st_size:,} bytes)')
    return ply_clean


def main():
    ap = argparse.ArgumentParser(description='照片 → 稠密点云 7 阶段流水线')
    ap.add_argument('--images', help='照片目录，或包含多组子目录的父目录')
    ap.add_argument('--out', help='输出根目录')
    ap.add_argument('--limit', type=int, default=0, help='只处理前 N 组（0=全部）')
    a = ap.parse_args()

    cfg = dict(CONFIG)
    if a.images:
        cfg['images'] = a.images
    if a.out:
        cfg['out'] = a.out

    for key in ('colmap', 'openmvs', 'strip'):
        if not Path(cfg[key]).exists():
            sys.exit(f'找不到 {key}: {cfg[key]} —— 先改文件顶部的 CONFIG')

    src = Path(cfg['images'])
    out_root = Path(cfg['out'])
    out_root.mkdir(parents=True, exist_ok=True)

    # 输入可能是"一组照片"本身，也可能是"多组的父目录"
    has_images = any(src.glob('*.jpg')) or any(src.glob('*.JPG')) or any(src.glob('*.png'))
    groups = [(src.name, src)] if has_images else \
             [(d.name, d) for d in sorted(p for p in src.iterdir() if p.is_dir())]
    if a.limit:
        groups = groups[:a.limit]

    print(f'共 {len(groups)} 组，输出到 {out_root}')
    results = []
    for name, gdir in groups:
        print(f'\n════════ 开始处理：{name} ════════')
        results.append((name, process_group(gdir, out_root / name, cfg)))

    print('\n════════ 汇总 ════════')
    for name, res in results:
        print(f'  {name:30s} {"OK  " + str(res) if res else "失败 / 跳过"}')


if __name__ == '__main__':
    main()
