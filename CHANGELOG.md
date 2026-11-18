# Changelog

## v2.3.0-sm120.1 — 2026-11-18

首个公开版本。

**构建**
- OpenMVS `v2.3.0`，CUDA Toolkit 13.1（V13.1.80），vcpkg 三元组 `x64-windows-sm120`
- `CMAKE_CUDA_ARCHITECTURES=120` → GPU 内核仅 `sm_120`（Blackwell / RTX 50 系）
- 特性：`core, cuda, openmp, tools`（无 `viewer` / `python` / `ceres`）
- CRT 动态、库静态 → 单 exe 可运行，无需 CUDA Toolkit
- 编译日志：`logs/vcpkg_openmvs.log`（`All requested installations completed successfully in: 6.8 min`）

**产物**
- `bin/`：9 个 exe + 2 个上游管线脚本，共 58.3 MB
  - DensifyPointCloud / InterfaceCOLMAP / InterfaceMetashape / InterfaceMVSNet / InterfacePolycam
  - ReconstructMesh / RefineMesh / TextureMesh / TransformScene
- `DensifyPointCloud.exe` 内含 `sm_120` cubin（`tools/check_cuda_arch.ps1` 可复现）

**工具**
- `tools/check_cuda_arch.ps1`：零依赖读取 PE 内嵌 CUDA 架构（等价 `cuobjdump` 的 `arch = sm_XX`）
- `tools/ply_strip.py`：剥离 OpenMVS PLY 的可变长 `property list`，使 CloudCompare 可加载（27 字节/点）
- `examples/run_pipeline.py`：7 阶段流水线示例（COLMAP 提特征→匹配→稀疏→去畸变→转 MVS→稠密化→洗 PLY）

**验证数据**（RTX 5070 Ti Laptop 12 GB / i7-14650HX / 32 GB）
- 49 张 6048×4032 → 9,937,814 点，干净 PLY 268,321,225 B，重投影误差 0.918 px
- 120 帧 1920×1920 → 7,960,409 点，干净 PLY 214,931,290 B
- 稠密化 GPU 耗时约 1 分钟/组

**文档**
- README（中英双语）、BUILD（复现配方 + 5 个踩坑）、VERIFY（3 种验证法 + 官方包对照）、FAQ（20+ 报错对照）、NOTICE（出处 / 修改标注 / 第三方组件 / AGPL 义务）

**已知差异**
- 不含 `Viewer.exe`、`Tests.exe`、`pyOpenMVS.dll`（官方包有）
- 版本为 2.3.0，未跟进上游 2.4.0
- 仅 `sm_120`，不含 `sm_89` / `sm_90` / `sm_100`
