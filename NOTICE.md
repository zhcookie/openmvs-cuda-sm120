# 出处、修改说明与许可义务

## 1. 上游

| 项目 | 值 |
|---|---|
| 项目 | OpenMVS — Open Multi-View Stereo reconstruction library |
| 仓库 | <https://github.com/cdcseacave/openMVS> |
| 主页 | <https://cdcseacave.github.io/> |
| 本项目所用版本 | **tag `v2.3.0`**（release 名：Add multi-texture support to mesh texturing，2024-01-07） |
| 上游最新版本 | `v2.4.0`（2026-01-20，新增 ROI estimation 与新 Viewer）—— **本构建未跟进** |
| 源码包 SHA512 | `c8af808393836d0ac508cf4f1d123cf297b451927fe4ad95dd27e041099818cd6d077f95b03e34cd9fe92bf0277cce8e9386311531093d6469b8e07f08b15aba` |
| 许可证 | **AGPL-3.0-only** |

`source/port/` 目录就是 vcpkg 官方仓库里 `ports/openmvs/` 的原样副本（portfile + 8 个 patch + `vcpkg.json` + `usage`），其中的 SHA512 与上表一致，可据此确认上游代码未被替换。

## 2. 本构建的性质：**非官方社区构建**

- 由使用者自行在本地编译，**不是** OpenMVS 项目发布的版本。
- 上游维护者**不提供**对本构建的支持。问题请提到本仓库，不要打扰 `cdcseacave/openMVS`。
- 与上游的差异仅限**构建配置**，未改动算法逻辑：
  - 通过自定义三元组 `source/triplets/x64-windows-sm120.cmake` 把 `CMAKE_CUDA_ARCHITECTURES` 设为 `120`；
  - 启用特性 `cuda`、`openmp`、`tools`；未启用 `viewer`、`python`、`ceres`；
  - 应用 `source/port/` 中的 8 个上游 vcpkg 补丁（`ambiguous-uint_t.diff`、`cmake.diff`、`common-log.diff`、`devendor.diff`、`interface-metashape.diff`、`missing-include.diff`、`no-absolute-paths.patch`、`cuda-13.diff`）；
  - 使用 CUDA Toolkit 13.1 编译；CRT 动态、库静态。
- 依据 AGPL-3.0 §5，以上改动在此明确标注。

## 3. 对应源码（Corresponding Source）怎么拿

AGPL-3.0 要求分发二进制时提供对应源码。本仓库**自带完整复现配方**，按以下顺序即可得到与 `bin/` 完全对应的源码树：

1. 取上游 `v2.3.0`：
   ```powershell
   git clone --branch v2.3.0 --depth 1 https://github.com/cdcseacave/openMVS
   ```
   或 tarball：`https://github.com/cdcseacave/openMVS/archive/refs/tags/v2.3.0.tar.gz`（校验用上表 SHA512）
2. 打上本仓库 `source/port/` 里的 8 个补丁（顺序与 `portfile.cmake` 中 `PATCHES` 一致）
3. 用 `source/triplets/x64-windows-sm120.cmake` 作为 vcpkg 三元组，按 [BUILD.md](BUILD.md) 执行

完整命令见 [BUILD.md](BUILD.md)，日志见 `logs/`。

## 4. 第三方组件（静态链接进 exe）

以下组件被静态链接进 `bin/*.exe`，因此整个可执行文件受 AGPL-3.0 约束。各组件自身许可证以其仓库为准：

| 组件 | 用途 | 典型许可证 |
|---|---|---|
| Boost（assert / graph / iostreams / pool / serialization / system / program_options / python） | 基础设施 | BSL-1.0 |
| OpenCV（core / imgproc / imgcodecs / features2d / calib3d） | 图像 IO 与处理 | Apache-2.0 |
| CGAL | 计算几何 | GPL-3.0 / LGPL-3.0（按模块） |
| Eigen3 | 线性代数 | MPL-2.0 |
| VCGLib | 网格数据结构 | GPL-3.0 |
| OpenEXR / Imath | 高动态范围图像 | BSD-3-Clause |
| libjpeg-turbo / libpng / tiff / zlib / zstd / liblzma / brotli / libwebp | 编解码与压缩 | BSD / zlib 类 |
| tinyxml2 / tinygltf / nlohmann-json | 解析 | zlib / MIT / MIT |
| OpenMP 运行时 | 多线程 | 随编译器（LLVM Apache-2.0 WITH LLVM-exception） |
| Microsoft Visual C++ 运行库 | 动态 CRT | Microsoft 可再分发组件条款 |

> 上表是"打进 exe 的东西"，不是"你需要额外安装的东西"。运行时**只需要** Windows 系统库 + VC++ 2015-2022 x64 运行库。

## 5. 你的义务（如果你再分发）

AGPL-3.0 是强 copyleft：

- 再分发 `bin/` 里的 exe（无论收费与否）→ 必须一并提供对应源码（本仓库即可）；
- 修改后再分发 → 必须标注修改，并以 AGPL-3.0 发布；
- 把它做成网络服务提供给他人使用 → 必须向使用者提供源码。

完整条款见 [LICENSE](LICENSE)。

## 6. 免责

本构建按"现状"提供，不附带任何明示或暗示的担保，包括但不限于适销性与特定用途适用性。使用风险自负。

## 7. 商标

OpenMVS、NVIDIA、CUDA、GeForce、RTX、Blackwell、COLMAP、CloudCompare 等名称与商标归各自所有者。本仓库与上述任何一方均无隶属或背书关系。
