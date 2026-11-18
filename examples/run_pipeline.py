#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_pipeline.py — 输入一组影像，输出一个可用于 CloudCompare 的稠密点云

本脚本将处理流程划分为七个阶段，每个阶段对应一个处理步骤：

  阶段 1/7  特征提取（COLMAP）   输出 build\\database.db
  阶段 2/7  特征匹配（COLMAP）   结果写入数据库
  阶段 3/7  稀疏重建（COLMAP）   输出 build\\sparse\\
  阶段 4/7  去畸变（COLMAP）     输出 build\\dense\\
  阶段 5/7  格式转换（OpenMVS）  输出 build\\scene.mvs
  阶段 6/7  稠密化（OpenMVS）    输出 build\\scene_dense.ply（GPU 阶段）
  阶段 7/7  属性剥离（本仓库工具）输出 build\\scene_dense_clean.ply（最终产物）

调用方式：

    python run_pipeline.py
    python run_pipeline.py --images D:\\data\\photos --out D:\\data\\build
    python run_pipeline.py --limit 3

前置条件：

    - 已安装 COLMAP，路径由 CONFIG['colmap'] 指定
    - 已解压 OpenMVS（本仓库 bin\\ 目录），路径由 CONFIG['openmvs'] 指定
    - tools\\ply_strip.py 位于仓库内

任一阶段以非零退出码结束时，该组影像的处理中止，脚本记录原因并继续处理下一组。
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ─────────────────────── 配置区 ───────────────────────
CONFIG = {
    # COLMAP 启动器路径（Windows 下一般为 COLMAP.bat）
    'colmap':  r'D:\app\colmap\COLMAP-4.2.0-windows-2022-CUDA-cuDSS-Caspar-GUI\COLMAP.bat',
    # OpenMVS 目录（本仓库 bin/ 的绝对路径）
    'openmvs': r'D:\app\openmvs\openmvs-sm120',
    # ply_strip.py 绝对路径
    'strip':   str(Path(__file__).resolve().parent.parent / 'tools' / 'ply_strip.py'),
    # 输入：单组影像目录，或包含多组子目录的父目录
    'images':  r'D:\data\photos',
    # 输出根目录：每组在该目录下生成独立的 build 目录
    'out':     r'D:\data\build',
    # 影像与特征参数
    'max_image_size': 3200,
    'max_features':   8192,
    'camera_model':   'SIMPLE_RADIAL',
    'single_camera':  1,
    # CUDA 设备编号（仅枚举 NVIDIA 设备，独立显卡通常为 0）
    'gpu_index':      0,
}
# ──────────────────────────────────────────────────────


def run(cmd, cwd=None, stage=''):
    """执行单条命令。返回 True 表示退出码为 0，返回 False 表示该阶段失败。"""
    printable = ' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in cmd)
    print(f'\n[{stage}] {printable}')
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode != 0:
        print(f'{stage} 阶段失败（退出码 {r.returncode}），终止该组处理')
        return False
    return True


def process_group(img_dir: Path, build: Path, cfg: dict):
    build.mkdir(parents=True, exist_ok=True)
    db = build / 'database.db'
    colmap, mvs = cfg['colmap'], Path(cfg['openmvs'])

    # 阶段 1/7：特征提取。在每张影像上提取特征点并写入数据库。
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
        ], stage='阶段 1/7 特征提取')
        if not ok:
            return None

    # 阶段 2/7：特征匹配。对全部影像两两匹配，结果写入数据库。
    if not run([
        colmap, 'exhaustive_matcher',
        '--database_path', db,
        '--FeatureMatching.use_gpu', 1,
        '--FeatureMatching.gpu_index', cfg['gpu_index'],
    ], stage='阶段 2/7 特征匹配'):
        return None

    # 阶段 3/7：稀疏重建。解算相机位姿与稀疏点云。输出目录须预先存在。
    sparse = build / 'sparse'
    sparse.mkdir(exist_ok=True)
    if not (sparse / '0').exists():
        if not run([
            colmap, 'mapper',
            '--database_path', db,
            '--image_path', img_dir,
            '--output_path', sparse,
        ], stage='阶段 3/7 稀疏重建'):
            return None

    # 阶段 4/7：模型选择与去畸变。当重建结果分裂为多个子模型时，选取点数最多者。
    models = sorted(sparse.rglob('points3D.bin'),
                    key=lambda p: p.stat().st_size, reverse=True)
    if not models:
        print('未生成稀疏模型，终止该组处理')
        return None
    model_dir = models[0].parent
    print(f'选用的模型目录：{model_dir}')

    dense = build / 'dense'
    if not run([
        colmap, 'image_undistorter',
        '--image_path', img_dir,
        '--input_path', model_dir,
        '--output_path', dense,
        '--output_type', 'COLMAP',
        '--max_image_size', cfg['max_image_size'],
    ], stage='阶段 4/7 去畸变'):
        return None

    # 阶段 5/7：格式转换。将 COLMAP 结果转换为 OpenMVS 场景文件。
    # --image-folder 须为绝对路径，否则会与 -i 目录拼接形成重复层级。
    scene = build / 'scene.mvs'
    if not run([
        mvs / 'InterfaceCOLMAP.exe',
        '-i', dense,
        '-o', scene,
        '--image-folder', (dense / 'images').resolve(),
    ], stage='阶段 5/7 格式转换'):
        return None

    # 阶段 6/7：稠密化。逐像素估计深度并生成稠密点云，为流程中耗时最长的阶段。
    ply_raw = build / 'scene_dense.ply'
    if not ply_raw.exists():
        if not run([
            mvs / 'DensifyPointCloud.exe',
            '-i', scene,
            '-o', build / 'scene_dense.mvs',
            '--cuda-device', cfg['gpu_index'],
        ], cwd=build, stage='阶段 6/7 稠密化'):
            return None

    # 阶段 7/7：属性剥离。移除 CloudCompare 无法解析的可变长属性。
    ply_clean = build / 'scene_dense_clean.ply'
    if not run([
        sys.executable, cfg['strip'], ply_raw, ply_clean,
    ], stage='阶段 7/7 属性剥离'):
        return None

    print(f'\n处理完成：{ply_clean}（{ply_clean.stat().st_size:,} 字节）')
    return ply_clean


def main():
    ap = argparse.ArgumentParser(description='影像到稠密点云的七阶段处理流程')
    ap.add_argument('--images', help='影像目录，或包含多组子目录的父目录')
    ap.add_argument('--out', help='输出根目录')
    ap.add_argument('--limit', type=int, default=0, help='仅处理前 N 组，0 表示全部')
    a = ap.parse_args()

    cfg = dict(CONFIG)
    if a.images:
        cfg['images'] = a.images
    if a.out:
        cfg['out'] = a.out

    for key in ('colmap', 'openmvs', 'strip'):
        if not Path(cfg[key]).exists():
            sys.exit(f'未找到 {key} 指向的路径：{cfg[key]}，请修改文件顶部的 CONFIG')

    src = Path(cfg['images'])
    out_root = Path(cfg['out'])
    out_root.mkdir(parents=True, exist_ok=True)

    # 输入目录既可能是单组影像，也可能是多组的父目录
    has_images = (any(src.glob('*.jpg')) or any(src.glob('*.JPG'))
                  or any(src.glob('*.png')))
    groups = ([(src.name, src)] if has_images
              else [(d.name, d) for d in sorted(p for p in src.iterdir() if p.is_dir())])
    if a.limit:
        groups = groups[:a.limit]

    print(f'待处理组数：{len(groups)}，输出目录：{out_root}')
    results = []
    for name, gdir in groups:
        print(f'\n处理中：{name}')
        results.append((name, process_group(gdir, out_root / name, cfg)))

    print('\n结果汇总')
    for name, res in results:
        status = f'完成 {res}' if res else '失败或跳过'
        print(f'  {name:30s} {status}')


if __name__ == '__main__':
    main()
