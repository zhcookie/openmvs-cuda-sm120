# Changelog

## v2.3.0-sm120.1 — 2026-11-18

首个公开发布版本。

### 构建

- OpenMVS `v2.3.0`，CUDA Toolkit 13.1（V13.1.80），vcpkg 三元组 `x64-windows-sm120`
- `CMAKE_CUDA_ARCHITECTURES=120`，GPU 内核仅含 `sm_120`（Blackwell / RTX 50 系列）
- 启用特性 `core, cuda, openmp, tools`；未启用 `viewer`、`python`、`ceres`
- CRT 动态链接、库静态链接，运行时无需 CUDA Toolkit
- 构建日志：`logs/vcpkg_openmvs.log`，记录 `All requested installations completed successfully in: 6.8 min`

### 产物

- `bin/`：9 个可执行文件与 2 个上游流程脚本，合计 58.3 MB
  - DensifyPointCloud、InterfaceCOLMAP、InterfaceMetashape、InterfaceMVSNet、InterfacePolycam
  - ReconstructMesh、RefineMesh、TextureMesh、TransformScene
- `DensifyPointCloud.exe` 内含 `sm_120` cubin，可用 `tools/check_cuda_arch.ps1` 复现检测

### 工具

- `tools/check_cuda_arch.ps1`：读取 PE 文件内嵌的 CUDA 架构，无需安装 CUDA Toolkit
- `tools/ply_strip.py`：剥离 OpenMVS 输出 PLY 的可变长属性，输出固定 27 字节/顶点，供 CloudCompare 加载
- `examples/run_pipeline.py`：七阶段处理流程示例，覆盖特征提取、匹配、稀疏重建、去畸变、格式转换、稠密化与属性剥离

### 验证数据

测试环境：RTX 5070 Ti Laptop（12 GB）、i7-14650HX、32 GB 内存。

- 49 张 6048 × 4032 影像：9,937,814 点，剥离后 PLY 268,321,225 B，重投影误差 0.918 px
- 120 帧 1920 × 1920 影像：7,960,409 点，剥离后 PLY 214,931,290 B
- 稠密化阶段 GPU 耗时约 1 分钟每组

### 文档

- README：概述、与上游差异、部署与验证、系统要求、工具说明、处理流程、实测数据、错误索引、已知限制、许可与来源
- BUILD：构建复现步骤与 5 项已知构建问题
- VERIFY：三种架构验证方式及上游分发包对照
- FAQ：按错误信息索引的现象、根因与处理方式
- NOTICE：来源、修改标注、第三方组件与许可义务

### 已知差异

- 不含 `Viewer.exe`、`Tests.exe` 与 `pyOpenMVS.dll`
- 版本为 2.3.0，未跟进上游 2.4.0
- 仅含 `sm_120` 内核，不含 `sm_89`、`sm_90`、`sm_100`
