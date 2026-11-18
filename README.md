# OpenMVS 2.3.0 · Windows x64 · CUDA sm_120（Blackwell / RTX 50 系）

面向 NVIDIA Blackwell 架构（计算能力 `sm_120`，RTX 50 系列）编译的 OpenMVS 预编译分发包。解压即可运行，运行时不依赖 CUDA Toolkit、vcpkg 或编译环境。

[最新版本](../../releases/latest) ｜ [架构验证](VERIFY.md) ｜ [构建复现](BUILD.md) ｜ [错误索引](FAQ.md) ｜ [来源与许可](NOTICE.md)

---

## 1. 概述

OpenMVS（Open Multi-View Stereo）用于将 COLMAP 输出的稀疏模型与原始影像转换为稠密点云、网格及带纹理模型。上游发布的 Windows CUDA 预编译包面向 Ampere 与 Ada 架构（`sm_80` / `sm_89`）构建，在 Blackwell 架构（`sm_120`）设备上启动时因缺少对应 GPU 内核而终止。

本仓库提供的二进制在同一代码基线上以 CUDA 13.1 与 vcpkg 构建，编译参数为 `CMAKE_CUDA_ARCHITECTURES=120`。GPU 内核仅包含 `sm_120`，库为静态链接，每个命令行工具均以单一可执行文件形式分发。

| 项目 | 取值 |
|---|---|
| 上游版本 | OpenMVS v2.3.0（`cdcseacave/openMVS`，tag `v2.3.0`） |
| 构建日期 | 2026-10-01 |
| CUDA Toolkit | 13.1（仅构建期依赖） |
| 目标平台 | Windows x64 |
| 目标架构 | `sm_120` |
| 链接方式 | 库静态链接、CRT 动态链接 |
| 许可证 | AGPL-3.0（与上游一致，详见 [NOTICE.md](NOTICE.md)） |

---

## 2. 与上游预编译包的差异

上游在 v2.4.0 中发布了 Windows CUDA 预编译包 `OpenMVS_Windows_x64_CUDA.7z`（累计下载 3,473 次）。该包构建时间早于 Blackwell 架构产品上市，未包含 `sm_120` 内核。对两个分发包执行同一检测脚本，结果如下（检测方法见 [VERIFY.md](VERIFY.md)）：

| 检测项 | 上游 v2.4.0 CUDA 包 | 本仓库 |
|---|---|---|
| 内嵌 cubin 架构 | `sm_89` | `sm_120` |
| PTX 回退目标 | `.target sm_20` | 无 |
| 在 RTX 50 系列上的执行结果 | 终止，报 `named symbol not found (code 500)` | 正常完成稠密化 |
| 分发形态 | 73 个文件，含 40 个 DLL，动态链接 | 9 个可执行文件，静态链接 |
| 附带组件 | `Viewer.exe`、`Tests.exe`、`pyOpenMVS.dll` | 不含，见第 7 节 |
| 版本 | 2.4.0 | 2.3.0 |

`named symbol not found` 的成因如下。CUDA 二进制通过两条路径提供设备代码：其一为针对具体架构编译的 cubin，其二为由驱动程序即时编译的 PTX。上游包的 cubin 面向 `sm_89`，其 PTX 回退目标为 `.target sm_20`；自 CUDA 12 起，`compute_20` 已不在驱动即时编译的支持范围内。两条路径均无法提供可在 `sm_120` 设备上加载的内核映像，驱动程序因而报告符号缺失。该错误与命令行参数无关，调整任何选项均不改变结果。

---

## 3. 部署与验证

### 3.1 获取与解压

从 [Releases](../../releases/latest) 下载 `openmvs-2.3.0-sm120-win-x64.zip`，解压至不含空格及非 ASCII 字符的目录，例如 `D:\app\openmvs\openmvs-sm120`。亦可克隆本仓库，可执行文件位于 `bin\`。

### 3.2 环境变量配置

以下命令将工具目录追加至当前用户的 `Path` 变量，不修改系统级配置：

```powershell
$p = [Environment]::GetEnvironmentVariable('Path','User')
[Environment]::SetEnvironmentVariable('Path', "$p;D:\app\openmvs\openmvs-sm120", 'User')
```

配置完成后需新开终端会话方可生效。

### 3.3 运行验证

```powershell
DensifyPointCloud -h
```

正常输出以 `OpenMVS x64 v2.3.0` 起始，随后为参数列表。若出现 `named symbol not found` 或 `no kernel image is available`，表明所调用的可执行文件不是本仓库提供的构建，应检查 `Path` 中是否存在旧版本目录。

---

## 4. 系统要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / 11 x64 |
| GPU | NVIDIA RTX 50 系列（Blackwell，`sm_120`）。实测设备为 RTX 5070 Ti Laptop，12 GB 显存 |
| 显示驱动 | 支持 CUDA 13.x 的驱动版本（R580 及以上）。驱动版本过低时报 `CUDA driver version is insufficient` |
| 运行库 | Visual C++ 2015-2022 x64 运行库（`vcruntime140` 系列） |
| CUDA Toolkit | 非必需 |
| 磁盘空间 | 稠密化阶段的中间文件占用较大，单组 100 张 3200px 影像约需 2 至 3 GB |

本分发包仅包含 `sm_120` 内核，不含 `sm_89`、`sm_90`、`sm_100` 等其它架构。RTX 40 系列及更早设备应使用上游预编译包，或按 [BUILD.md](BUILD.md) 以目标架构重新构建。

---

## 5. 仓库结构

```
openmvs-cuda-sm120/
├─ bin/                      9 个可执行文件与 2 个上游流程脚本
├─ examples/
│  └─ run_pipeline.py        七阶段处理流程示例
├─ tools/
│  ├─ check_cuda_arch.ps1    读取可执行文件内嵌的 CUDA 架构
│  └─ ply_strip.py           PLY 可变长属性剥离工具
├─ source/
│  ├─ port/                  vcpkg 端口定义：portfile 与 8 个补丁
│  └─ triplets/              x64-windows-sm120.cmake，指定 CUDA 架构 120
├─ scripts/                  构建脚本：CUDA 部署、vcpkg 循环安装、测试超时处理
├─ logs/                     构建日志与首次运行日志
├─ VERIFY.md                 架构验证方法
├─ BUILD.md                  构建复现步骤
├─ FAQ.md                    错误信息索引
├─ NOTICE.md                 来源、修改说明与许可义务
└─ CHANGELOG.md
```

---

## 6. 工具说明

| 可执行文件 | 功能 | 典型调用 |
|---|---|---|
| `InterfaceCOLMAP.exe` | 将 COLMAP 结果转换为 OpenMVS 场景文件 | `InterfaceCOLMAP -i dense -o scene.mvs --image-folder <绝对路径>` |
| `DensifyPointCloud.exe` | 稠密化：由稀疏点生成稠密点云（GPU 阶段） | `DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0` |
| `ReconstructMesh.exe` | 由点云重建网格 | `ReconstructMesh -i scene_dense.mvs -o mesh.mvs` |
| `RefineMesh.exe` | 网格细化 | `RefineMesh -i mesh.mvs -o mesh_refine.mvs` |
| `TextureMesh.exe` | 纹理映射 | `TextureMesh -i mesh_refine.mvs -o textured.mvs` |
| `TransformScene.exe` | 场景坐标变换与缩放 | `TransformScene -i scene.mvs -o out.mvs --scale 0.5` |
| `InterfaceMetashape.exe` | 将 Metashape 工程转换为场景文件 | 见 `-h` |
| `InterfaceMVSNet.exe` | 将 MVSNet 深度图转换为场景文件 | 见 `-h` |
| `InterfacePolycam.exe` | 将 Polycam 导出转换为场景文件 | 见 `-h` |
| `MvgMvsPipeline.py` | 上游提供的流程脚本 | `python MvgMvsPipeline.py -h` |
| `MvgOptimizeSfM.py` | SfM 位姿优化 | `python MvgOptimizeSfM.py -h` |

本构建未启用 `viewer` 特性，因而不包含 `Viewer.exe`。模型查看可使用 CloudCompare 或 MeshLab 打开输出的 PLY / OBJ 文件。

---

## 7. 处理流程

以下七个阶段为实测通过的完整链路，`examples/run_pipeline.py` 已将其整合为单条命令。

### 7.1 COLMAP 阶段

```powershell
set COLMAP="D:\app\colmap\COLMAP-4.2.0-windows-2022-CUDA-cuDSS-Caspar-GUI\COLMAP.bat"
set IMG=D:\data\my_photos
set BUILD=D:\data\build

:: 阶段 1：特征提取
%COLMAP% feature_extractor --database_path %BUILD%\database.db --image_path %IMG% ^
  --ImageReader.single_camera 1 --ImageReader.camera_model SIMPLE_RADIAL ^
  --SiftExtraction.max_num_features 8192 --FeatureExtraction.max_image_size 3200 ^
  --FeatureExtraction.use_gpu 1 --FeatureExtraction.gpu_index 0

:: 阶段 2：特征匹配
%COLMAP% exhaustive_matcher --database_path %BUILD%\database.db ^
  --FeatureMatching.use_gpu 1 --FeatureMatching.gpu_index 0

:: 阶段 3：稀疏重建（输出目录须预先存在）
mkdir %BUILD%\sparse
%COLMAP% mapper --database_path %BUILD%\database.db --image_path %IMG% --output_path %BUILD%\sparse

:: 阶段 4：去畸变
%COLMAP% image_undistorter --image_path %IMG% --input_path %BUILD%\sparse\0 ^
  --output_path %BUILD%\dense --output_type COLMAP --max_image_size 3200
```

`gpu_index` 与 `--cuda-device` 的取值为 CUDA 设备编号。CUDA 仅枚举 NVIDIA 设备，独立显卡的编号在含核显的系统中仍为 `0`，与任务管理器显示的编号不一致。

### 7.2 OpenMVS 阶段

```powershell
:: 阶段 5：格式转换（--image-folder 须为绝对路径）
InterfaceCOLMAP -i %BUILD%\dense -o %BUILD%\scene.mvs --image-folder %BUILD%\dense\images

:: 阶段 6：稠密化
cd /d %BUILD%
DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0

:: 阶段 7：剥离可变长属性
python tools\ply_strip.py scene_dense.ply scene_dense_clean.ply
```

最终产物为 `scene_dense_clean.ply`。

### 7.3 阶段 7 的作用

OpenMVS 输出的 PLY 为每个顶点附加两个可变长属性 `view_indices` 与 `view_weights`，记录该点被哪些视图观测及对应权重。CloudCompare 的 PLY 解析器不支持可变长属性，加载时报告 `nothing to load`。`tools/ply_strip.py` 仅保留 `x, y, z`、`red, green, blue` 与法向量 `nx, ny, nz`，固定为 27 字节/顶点：

| 文件 | 大小 | 说明 |
|---|---|---|
| `scene_dense.ply` | 617,272,238 B | 原始输出，含两个可变长属性 |
| `scene_dense_clean.ply` | 268,321,225 B | 剥离后，9,937,814 顶点 × 27 B 加文件头 |

### 7.4 网格与纹理（可选）

```powershell
ReconstructMesh -i scene_dense.mvs -o scene_dense_mesh.mvs
RefineMesh      -i scene_dense_mesh.mvs -o scene_dense_mesh_refine.mvs
TextureMesh     -i scene_dense_mesh_refine.mvs -o scene_dense_mesh_refine_texture.mvs
```

---

## 8. 实测数据

测试环境：RTX 5070 Ti Laptop（12 GB）、i7-14650HX、32 GB 内存。

| 数据集 | 输入 | 注册率 | 重投影误差 | 稠密点数 | 剥离后 PLY | GPU 耗时 |
|---|---|---|---|---|---|---|
| 数据集 1 | 49 张，6048 × 4032（NIKON Z6_3） | 49/49 | 0.918 px | 9,937,814 | 268,321,225 B | 约 1 分钟 |
| 批量第 1 组 | 120 帧，1920 × 1920（视频抽帧） | 全部注册 | 未记录 | 7,960,409 | 214,931,290 B | 约 1 分钟 |

---

## 9. 错误信息索引

| 错误信息 | 根因 | 处理方式 |
|---|---|---|
| `named symbol not found (code 500)` | 可执行文件不含当前设备架构的 GPU 内核 | 改用本分发包，并以 `cuobjdump` 或 `tools/check_cuda_arch.ps1` 确认架构 |
| `no kernel image is available for execution on the device` | 同上 | 同上 |
| `Invalid CUDA GPU selected (1 vs 1)` | 使用了任务管理器显示的设备编号 | 将设备编号统一设为 `0` |
| 特征提取或稠密化启动后立即退出 | 显存被其它进程占用 | 以 `nvidia-smi` 确认占用情况，释放显存后重试 |
| CloudCompare 报告 `nothing to load` | PLY 含可变长属性 | 执行 `tools/ply_strip.py` |
| `output_path is not a directory` | COLMAP mapper 要求输出目录预先存在 | 先创建输出目录 |
| 影像无法定位或生成双层 `dense\dense` 目录 | `--image-folder` 使用了相对路径 | 改为绝对路径 |

完整列表见 [FAQ.md](FAQ.md)。

---

## 10. 已知限制

1. GPU 内核仅含 `sm_120`，适用于 RTX 50 系列；其它架构需按 [BUILD.md](BUILD.md) 重新构建。
2. 仅提供 Windows x64 构建，不含 Linux 与 macOS 版本。
3. 不含 `Viewer.exe`，未启用 `viewer` 特性。
4. 不含 `pyOpenMVS` Python 绑定；如需该功能，应以 `openmvs[core,cuda,openmp,tools,python]` 重新构建。
5. 版本为 2.3.0。上游 2.4.0 新增 ROI estimation 与新版 Viewer，本构建未在该版本上验证 `sm_120` 编解码路径。
6. 库为静态链接、CRT 为动态链接，运行环境需具备 Visual C++ 2015-2022 x64 运行库。
7. 本分发包为非官方构建，上游不提供技术支持；问题应提交至本仓库。

---

## 11. 许可与来源

- 二进制与构建配置基于 OpenMVS v2.3.0，许可证为 AGPL-3.0，[LICENSE](LICENSE) 为上游原文。
- Boost、OpenCV、CGAL、Eigen、VCGLib、OpenEXR 等组件以静态方式链接至可执行文件，因此全部二进制同样受 AGPL-3.0 约束。分发、修改与再发布须提供对应源码。
- 复现本构建所需的对应源码材料均收录于仓库：`source/port/`（上游 tag、SHA512、8 个补丁）、`source/triplets/x64-windows-sm120.cmake`、`scripts/` 与 [BUILD.md](BUILD.md)。
- 上游地址：<https://github.com/cdcseacave/openMVS>，tag `v2.3.0`。
- 详细声明见 [NOTICE.md](NOTICE.md)。

---

## English summary

**Scope.** A Windows x64 build of OpenMVS v2.3.0 compiled with `CMAKE_CUDA_ARCHITECTURES=120`, providing GPU kernels for the Blackwell architecture (`sm_120`, RTX 50 series) only. Libraries are linked statically; the CUDA Toolkit is not required at runtime.

**Relation to upstream.** The upstream `OpenMVS_Windows_x64_CUDA.7z` for v2.4.0 contains `sm_89` cubins and a `.target sm_20` PTX fallback. Since CUDA 12, `compute_20` is outside the range supported by driver-side JIT, so the package terminates on `sm_120` devices with `named symbol not found (code 500)`. The binaries in this repository contain `sm_120` cubins; the check is reproducible with `tools/check_cuda_arch.ps1` or `cuobjdump`.

**Requirements.** Windows 10/11 x64, an RTX 50 series GPU, an NVIDIA driver supporting CUDA 13.x (R580 or later), and the Visual C++ 2015-2022 x64 runtime.

**Usage.**

```powershell
DensifyPointCloud -h
InterfaceCOLMAP -i dense -o scene.mvs --image-folder C:\abs\path\dense\images
DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0
python tools\ply_strip.py scene_dense.ply scene_dense_clean.ply
```

**Exclusions.** `Viewer.exe`, the `pyOpenMVS` bindings, Linux and macOS builds, and kernels for architectures other than `sm_120`. The packaged version is 2.3.0; upstream latest is 2.4.0.

**License.** AGPL-3.0, inherited from upstream. Because the binaries are linked statically, each executable is covered by AGPL-3.0. The corresponding source recipe is contained in `source/` and [BUILD.md](BUILD.md).

**Status.** Unofficial community build; upstream does not provide support for it. Issues should be filed in this repository.
