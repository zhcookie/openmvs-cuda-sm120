# OpenMVS 2.3.0 · Windows x64 · CUDA **sm_120**（Blackwell / RTX 50 系）

> 一份**真正为 RTX 50 系（Blackwell，`sm_120`）编译**的 OpenMVS 预编译包。
> 解压即用：**不用装 CUDA Toolkit**，**不用自己编译**，**不用 vcpkg**。

[下载最新 Release](../../releases/latest) ｜ [验证内核架构](VERIFY.md) ｜ [自己重新编译](BUILD.md) ｜ [报错对照表](FAQ.md) ｜ [出处与许可](NOTICE.md)

---

## 1. 这是什么

OpenMVS（Open Multi-View Stereo）是把「COLMAP 算出的稀疏模型 + 一组照片」变成**稠密点云 / 网格 / 带纹理模型**的工具链。官方只发布面向旧显卡的 CUDA 构建，NVIDIA RTX 50 系（Blackwell，计算能力 **`sm_120`**）装上去会直接报错退出。

本仓库提供一份在 **CUDA 13.1 + vcpkg** 下、用 `CMAKE_CUDA_ARCHITECTURES=120` 编译出来的 Windows x64 构建：GPU 内核只有 `sm_120`，静态链接，**单个 exe 即可运行**。

- 上游版本：OpenMVS **v2.3.0**（`cdcseacave/openMVS` tag `v2.3.0`）
- 编译日期：2026-10-01
- CUDA Toolkit：13.1（构建期使用，运行时不需要）
- 许可证：**AGPL-3.0**（与上游一致，见 [NOTICE.md](NOTICE.md)）

---

## 2. 为什么需要这个包（不是"官方没做"，是"官方那份跑不了"）

官方 v2.4.0 **确实**发布了 Windows CUDA 预编译包 `OpenMVS_Windows_x64_CUDA.7z`（3,473 次下载）。但它是在 RTX 50 系上市前编的，里面**没有** `sm_120` 内核。对比实测（扫描方法见 [VERIFY.md](VERIFY.md)）：

| | 官方 `OpenMVS_Windows_x64_CUDA.7z`（v2.4.0） | 本仓库 |
|---|---|---|
| GPU 内核架构 | **仅 `sm_89`**（Ada / RTX 40 系），PTX 兜底只到 `.target sm_20` | **`sm_120`**（Blackwell / RTX 50 系） |
| RTX 50 系能否运行 | ❌ 立刻报 `named symbol not found (code 500)` | ✅ 正常出点云 |
| 文件形态 | **73 个文件 / 40 个 DLL**，动态链接，缺一个 DLL 就起不来 | **9 个 exe 静态链接**，单文件即可跑 |
| 额外组件 | 含 `Viewer.exe`、`Tests.exe`、`pyOpenMVS.dll`（Python 绑定） | 不含（见「已知限制」） |
| 需要 VC++ 运行库 | 是 | 是（`vcruntime140` 系列，Windows 一般已自带） |
| 版本 | 2.4.0 | **2.3.0** |

**为什么会报 `named symbol not found`**：CUDA 二进制要么带目标架构的机器码（cubin），要么带 PTX 让驱动现场编译。官方包的 cubin 是 `sm_89`，PTX 兜底却是 `.target sm_20` —— 而 CUDA 12 起已不支持 `compute_20` 的 JIT。两头都落空，驱动找不到任何能在这张卡上执行的 kernel，于是报 "named symbol not found"。这不是参数问题，调任何选项都没用。

---

## 3. 快速开始（3 分钟）

### 3.1 下载

到 [Releases](../../releases/latest) 下载 `openmvs-2.3.0-sm120-win-x64.zip`，解压到一个**纯英文、无空格**的目录，例如：

```
D:\app\openmvs\openmvs-sm120\
```

> 也可以直接 `git clone` 本仓库，可执行文件就在 `bin\`。

### 3.2 加入 PATH（可选，推荐）

PowerShell（当前用户，不污染系统变量）：

```powershell
$p = [Environment]::GetEnvironmentVariable('Path','User')
[Environment]::SetEnvironmentVariable('Path', "$p;D:\app\openmvs\openmvs-sm120", 'User')
```

**新开**一个终端生效。

### 3.3 验证能跑

```powershell
DensifyPointCloud -h
```

看到 `OpenMVS x64 v2.3.0` + 一堆参数说明 = 成功。
如果看到 `named symbol not found` / `no kernel image is available`，说明你拿到的不是这份 sm_120 构建。

---

## 4. 系统要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / 11 x64 |
| GPU | NVIDIA **RTX 50 系**（Blackwell，`sm_120`）。实测 RTX 5070 Ti Laptop 12 GB |
| 驱动 | 支持 CUDA 13.x 的驱动（R580 及以上）。驱动太旧会报 `CUDA driver version is insufficient` |
| 运行库 | VC++ 2015-2022 x64 运行库（绝大多数 Windows 已装） |
| CUDA Toolkit | **不需要**（静态链接） |
| 磁盘 | 稠密化中间文件很大：100 张 3200px 照片约需 2~3 GB/组 |

> ⚠️ **本包只含 `sm_120`，不含 `sm_89` / `sm_90` / 其它架构。** RTX 40 系及更早的卡请用官方包，或用 [BUILD.md](BUILD.md) 改成自己的架构重编。

---

## 5. 仓库结构

```
openmvs-cuda-sm120/
├─ bin/                      9 个 exe + 2 个上游管线脚本（开箱即用）
├─ examples/
│  └─ run_pipeline.py        完整 7 阶段流水线示例（COLMAP→OpenMVS→干净 PLY）
├─ tools/
│  └─ ply_strip.py           PLY 剥离工具：让 CloudCompare 能打开 OpenMVS 的点云
├─ source/
│  ├─ port/                  vcpkg 的 openmvs 端口全套（portfile + 8 个 patch + vcpkg.json）
│  └─ triplets/              x64-windows-sm120.cmake（核心配方：强制架构 120）
├─ scripts/                  构建脚本（CUDA 免管理员组装 / vcpkg 循环 / conftest 看门狗）
├─ logs/                     真实构建日志与运行日志（可对照排查）
├─ VERIFY.md                 怎么证明内核是 sm_120
├─ BUILD.md                  怎么从源码复现这一份
├─ FAQ.md                    报错 → 原因 → 解法
├─ NOTICE.md                 出处、第三方组件、AGPL 义务
└─ CHANGELOG.md
```

---

## 6. 工具速查

| 可执行文件 | 干什么 | 典型命令 |
|---|---|---|
| `InterfaceCOLMAP.exe` | COLMAP 结果 → OpenMVS 场景（`.mvs`） | `InterfaceCOLMAP -i dense -o scene.mvs --image-folder <绝对路径>` |
| `DensifyPointCloud.exe` | **稠密化**：稀疏点 → 几百万点云（GPU，最慢） | `DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0` |
| `ReconstructMesh.exe` | 点云 → 网格 | `ReconstructMesh -i scene_dense.mvs -o mesh.mvs` |
| `RefineMesh.exe` | 网格细化（保边） | `RefineMesh -i mesh.mvs -o mesh_refine.mvs` |
| `TextureMesh.exe` | 贴纹理，输出带贴图的模型 | `TextureMesh -i mesh_refine.mvs -o textured.mvs` |
| `TransformScene.exe` | 场景坐标变换 / 缩放 | `TransformScene -i scene.mvs -o out.mvs --scale 0.5` |
| `InterfaceMetashape.exe` | Metashape 工程 → `.mvs` | 见 `-h` |
| `InterfaceMVSNet.exe` | MVSNet 深度图 → `.mvs` | 见 `-h` |
| `InterfacePolycam.exe` | Polycam 导出 → `.mvs` | 见 `-h` |
| `MvgMvsPipeline.py` | 上游自带的一键管线脚本 | `python MvgMvsPipeline.py -h` |
| `MvgOptimizeSfM.py` | 优化 SfM 位姿 | `python MvgOptimizeSfM.py -h` |

**没有 `Viewer.exe`**：本构建未编 viewer 特性（需要 GLFW/GLEW 图形依赖）。想看模型请用 CloudCompare / MeshLab 打开输出的 PLY/OBJ。

---

## 7. 完整流水线（照片 → 稠密点云）

下面是实测跑通的 7 个阶段，`examples/run_pipeline.py` 已把它们串成一条命令。

### 7.1 COLMAP 阶段（稀疏重建）

```powershell
set COLMAP="D:\app\colmap\COLMAP-4.2.0-windows-2022-CUDA-cuDSS-Caspar-GUI\COLMAP.bat"
set IMG=D:\data\my_photos
set BUILD=D:\data\build

:: 1) 提特征
%COLMAP% feature_extractor --database_path %BUILD%\database.db --image_path %IMG% ^
  --ImageReader.single_camera 1 --ImageReader.camera_model SIMPLE_RADIAL ^
  --SiftExtraction.max_num_features 8192 --FeatureExtraction.max_image_size 3200 ^
  --FeatureExtraction.use_gpu 1 --FeatureExtraction.gpu_index 0

:: 2) 两两匹配
%COLMAP% exhaustive_matcher --database_path %BUILD%\database.db ^
  --FeatureMatching.use_gpu 1 --FeatureMatching.gpu_index 0

:: 3) 解算稀疏（输出目录必须先存在！）
mkdir %BUILD%\sparse
%COLMAP% mapper --database_path %BUILD%\database.db --image_path %IMG% --output_path %BUILD%\sparse

:: 4) 去畸变（MVS 只认理想相机）
%COLMAP% image_undistorter --image_path %IMG% --input_path %BUILD%\sparse\0 ^
  --output_path %BUILD%\dense --output_type COLMAP --max_image_size 3200
```

> `gpu_index 0` 是 **CUDA 编号**，不是任务管理器的 "GPU 1"。核显占 0 号的机器上，N 卡在 CUDA 里仍然是 0。

### 7.2 OpenMVS 阶段（稠密化）

```powershell
:: 5) 转格式（--image-folder 必须绝对路径，否则会拼出 dense\dense 断链）
InterfaceCOLMAP -i %BUILD%\dense -o %BUILD%\scene.mvs --image-folder %BUILD%\dense\images

:: 6) 稠密化（最慢，约 1 分钟/百张）
cd /d %BUILD%
DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0

:: 7) 洗列表：剥掉 CloudCompare 读不了的 property list
python tools\ply_strip.py scene_dense.ply scene_dense_clean.ply
```

最终得到 `scene_dense_clean.ply`。

### 7.3 为什么需要第 7 步

OpenMVS 的 PLY 每点附带 `property list view_indices / view_weights`（可见视图索引），是**可变长列表**。CloudCompare 的 PLY 解析器不支持可变长属性，于是直接报 `nothing to load`。`tools/ply_strip.py` 只保留 `x,y,z + rgb + 法线` = **27 字节/点**，文件立刻变小、CloudCompare 正常加载：

| 文件 | 大小 | 说明 |
|---|---|---|
| `scene_dense.ply` | 617,272,238 B | 原始，含两个可变长列表，CC 读不了 |
| `scene_dense_clean.ply` | 268,321,225 B | 干净，993 万点 × 27 B + 头 |

### 7.4 继续做网格与纹理（可选）

```powershell
ReconstructMesh -i scene_dense.mvs -o scene_dense_mesh.mvs
RefineMesh      -i scene_dense_mesh.mvs -o scene_dense_mesh_refine.mvs
TextureMesh     -i scene_dense_mesh_refine.mvs -o scene_dense_mesh_refine_texture.mvs
```

---

## 8. 实测数据（RTX 5070 Ti Laptop 12 GB / i7-14650HX / 32 GB）

| 数据集 | 输入 | 注册 | 重投影误差 | 稠密点数 | 干净 PLY | GPU 耗时 |
|---|---|---|---|---|---|---|
| 数据集 1 | 49 张，6048×4032（NIKON Z6_3） | 49/49 | 0.918 px | **9,937,814** | 268,321,225 B | ≈ 1 分钟 |
| 批量第 1 组 | 120 帧，1920×1920（视频抽帧） | 全部 | — | **7,960,409** | 214,931,290 B | ≈ 1 分钟 |

---

## 9. 常见错误（详见 [FAQ.md](FAQ.md)）

| 报错 | 真因 | 一眼解法 |
|---|---|---|
| `named symbol not found (code 500)` | 二进制没有你显卡的 kernel | 换成本包；`cuobjdump` 查架构 |
| `no kernel image is available for execution on the device` | 同上 | 同上 |
| `Invalid CUDA GPU selected (1 vs 1)` | 把任务管理器的 GPU 编号当成了 CUDA 编号 | `--cuda-device 0` / `gpu_index 0` |
| 点 Extract / Densify 秒退 | 显存被别的程序占满 | 先 `nvidia-smi`，关掉 Lightroom / 浏览器 |
| CloudCompare `nothing to load` | PLY 里带 `property list` | 跑 `tools/ply_strip.py` |
| `output_path is not a directory` | COLMAP mapper 要求输出目录已存在 | 先 `mkdir sparse` |
| 找不到图片 / 双层 `dense\dense` | `--image-folder` 用了相对路径 | 改绝对路径 |

---

## 10. 已知限制（请先看这里再提问）

1. **只有 `sm_120`**：RTX 50 系专用。其它架构请自编，见 [BUILD.md](BUILD.md)。
2. **只有 Windows x64**：没编 Linux / macOS。
3. **不含 `Viewer.exe`**：未启用 `viewer` 特性。
4. **不含 `pyOpenMVS`（Python 绑定）**：需要的话用 `openmvs[core,cuda,openmp,tools,python]` 自行加编。
5. **版本是 2.3.0，不是 2.4.0**：上游 2.4.0（2026-01）新增 ROI estimation 与新 Viewer，但本构建未在 2.4.0 上做过 sm_120 验证。
6. **静态链接 + 动态 CRT**：需要系统有 VC++ 2015-2022 x64 运行库。
7. **非官方构建**：由社区成员自行编译，上游不提供支持；提 issue 到本仓库，不要打扰上游维护者。

---

## 11. 许可证与出处

- 本仓库二进制与源码配方基于 **OpenMVS v2.3.0**，许可证 **AGPL-3.0**（[LICENSE](LICENSE) 为上游原文）。
- 静态链接把 Boost / OpenCV / CGAL / Eigen / VCGLib / OpenEXR 等一并打进 exe，因此**整个二进制同样受 AGPL-3.0 约束**：分发、修改、再发布都必须开源并提供对应源码。
- 复现本构建所需的**对应源码配方**全部在本仓库内：`source/port/`（上游 tag + SHA512 + 8 个 patch）、`source/triplets/x64-windows-sm120.cmake`、`scripts/`、[BUILD.md](BUILD.md)。
- 上游地址：<https://github.com/cdcseacave/openMVS> · tag `v2.3.0`
- 详细声明见 [NOTICE.md](NOTICE.md)。

---

## English (short version)

**What this is** — A prebuilt Windows x64 OpenMVS **v2.3.0** compiled with `CMAKE_CUDA_ARCHITECTURES=120`, i.e. GPU kernels for **Blackwell / RTX 50 series (`sm_120`)** only. Statically linked: drop the folder anywhere, no CUDA Toolkit required.

**Why** — The official `OpenMVS_Windows_x64_CUDA.7z` (v2.4.0) ships `sm_89` cubins with a `sm_20` PTX fallback, which CUDA 12+ can no longer JIT. On an RTX 50 card it dies with `named symbol not found (code 500)`. This build contains real `sm_120` code (verified by scanning the embedded fatbin, see [VERIFY.md](VERIFY.md)).

**Requirements** — Windows 10/11 x64, RTX 50 series GPU, NVIDIA driver supporting CUDA 13.x (R580+), VC++ 2015-2022 x64 runtime. No CUDA Toolkit.

**Usage**

```powershell
DensifyPointCloud -h
InterfaceCOLMAP -i dense -o scene.mvs --image-folder C:\abs\path\dense\images
DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0
python tools\ply_strip.py scene_dense.ply scene_dense_clean.ply
```

**Not included** — `Viewer.exe`, `pyOpenMVS` bindings, Linux/macOS builds, other SM architectures. Version is 2.3.0 (upstream latest is 2.4.0).

**License** — AGPL-3.0, inherited from upstream. Binaries are statically linked, so the whole executable is AGPL-3.0. Full reproduction recipe (upstream tag + SHA512 + 8 patches + vcpkg triplet + build scripts) is in `source/` and [BUILD.md](BUILD.md).

**Unofficial build** — Community build, not supported by upstream. Please file issues here, not on `cdcseacave/openMVS`.
