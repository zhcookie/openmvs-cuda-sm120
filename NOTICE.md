# 来源、修改说明与许可义务

## 1. 上游信息

| 项目 | 取值 |
|---|---|
| 项目 | OpenMVS — Open Multi-View Stereo reconstruction library |
| 仓库 | <https://github.com/cdcseacave/openMVS> |
| 项目主页 | <https://cdcseacave.github.io/> |
| 本构建对应版本 | tag `v2.3.0`（发布名：Add multi-texture support to mesh texturing，2024-01-07） |
| 上游最新版本 | `v2.4.0`（2026-01-20，新增 ROI estimation 与新版 Viewer），本构建未跟进 |
| 源码包 SHA512 | `c8af808393836d0ac508cf4f1d123cf297b451927fe4ad95dd27e041099818cd6d077f95b03e34cd9fe92bf0277cce8e9386311531093d6469b8e07f08b15aba` |
| 许可证 | AGPL-3.0-only |

`source/port/` 为 vcpkg 官方仓库中 `ports/openmvs/` 的原样副本（`portfile.cmake`、8 个补丁、`vcpkg.json`、`usage`）。其中记录的 SHA512 与上表一致，可据此确认上游代码未被替换。

## 2. 构建性质与修改说明

本分发包为非官方社区构建，由使用者自行编译生成，不属于 OpenMVS 项目发布的版本。上游维护者对本分发包不提供支持，相关问题应提交至本仓库。

与上游的差异限于构建配置，算法实现未作改动：

- 通过自定义三元组 `source/triplets/x64-windows-sm120.cmake` 将 `CMAKE_CUDA_ARCHITECTURES` 设为 `120`；
- 启用特性 `cuda`、`openmp`、`tools`；未启用 `viewer`、`python`、`ceres`；
- 应用 `source/port/` 中的 8 个补丁：`ambiguous-uint_t.diff`、`cmake.diff`、`common-log.diff`、`devendor.diff`、`interface-metashape.diff`、`missing-include.diff`、`no-absolute-paths.patch`、`cuda-13.diff`；
- 使用 CUDA Toolkit 13.1 编译，CRT 动态链接、库静态链接。

依据 AGPL-3.0 第 5 条，上述修改在此明确标注。

## 3. 对应源码的获取方式

AGPL-3.0 要求分发二进制时一并提供对应源码。本仓库收录复现所需的全部材料，按下列顺序可获得与 `bin/` 对应的源码树：

1. 获取上游 `v2.3.0`：

   ```powershell
   git clone --branch v2.3.0 --depth 1 https://github.com/cdcseacave/openMVS
   ```

   或下载归档：`https://github.com/cdcseacave/openMVS/archive/refs/tags/v2.3.0.tar.gz`，以第 1 节所列 SHA512 校验。

2. 应用 `source/port/` 中的 8 个补丁，顺序与 `portfile.cmake` 中 `PATCHES` 列表一致。

3. 以 `source/triplets/x64-windows-sm120.cmake` 作为 vcpkg 三元组，按 [BUILD.md](BUILD.md) 执行构建。

构建日志见 `logs/` 目录。

## 4. 静态链接的第三方组件

下列组件以静态方式链接至 `bin/*.exe`，因此全部可执行文件均受 AGPL-3.0 约束。各组件自身许可证以其上游仓库为准。

| 组件 | 用途 | 许可证类型 |
|---|---|---|
| Boost（assert / graph / iostreams / pool / serialization / system / program_options / python） | 基础设施 | BSL-1.0 |
| OpenCV（core / imgproc / imgcodecs / features2d / calib3d） | 图像读写与处理 | Apache-2.0 |
| CGAL | 计算几何 | GPL-3.0 或 LGPL-3.0（按模块） |
| Eigen3 | 线性代数 | MPL-2.0 |
| VCGLib | 网格数据结构 | GPL-3.0 |
| OpenEXR / Imath | 高动态范围图像 | BSD-3-Clause |
| libjpeg-turbo / libpng / tiff / zlib / zstd / liblzma / brotli / libwebp | 编解码与压缩 | BSD 系或 zlib 系 |
| tinyxml2 / tinygltf / nlohmann-json | 数据解析 | zlib / MIT / MIT |
| OpenMP 运行时 | 多线程 | Apache-2.0 WITH LLVM-exception |
| Microsoft Visual C++ 运行库 | 动态 CRT | Microsoft 可再分发组件条款 |

上表所列组件已包含于可执行文件内部，无需另行安装。运行环境仅需 Windows 系统库与 Visual C++ 2015-2022 x64 运行库。

## 5. 再分发时的许可义务

AGPL-3.0 为强 copyleft 许可，再分发时适用以下义务：

- 分发 `bin/` 中的可执行文件（无论是否收费），须同时提供对应源码，本仓库即为该源码材料；
- 修改后再分发，须标注修改内容，并以 AGPL-3.0 发布；
- 将其作为网络服务提供给他人使用，须向使用者提供源码。

完整条款见 [LICENSE](LICENSE)。

## 6. 免责声明

本构建按现状提供，不附带任何明示或暗示的担保，包括但不限于适销性与特定用途适用性。使用风险由使用者承担。

## 7. 商标

OpenMVS、NVIDIA、CUDA、GeForce、RTX、Blackwell、COLMAP、CloudCompare 等名称与商标归各自权利人所有。本仓库与上述主体无隶属关系，亦未获得其背书。
