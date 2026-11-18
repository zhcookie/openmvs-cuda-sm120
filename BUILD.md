# 从源码复现这份 sm_120 构建

本文件记录生成 `bin/` 里那批 exe 的**完整配方**。按顺序走一遍即可复现（或改成你自己的架构，例如 `89` / `90` / `100` / `120`）。

- 目标：`openmvs[core,cuda,openmp,tools]:x64-windows-sm120`
- 实测耗时：约 6.8 分钟（二进制缓存命中）/ 首次全量约数小时（vcpkg 编译 121 个依赖包）
- 编译环境：Windows 11 x64 · i7-14650HX · RTX 5070 Ti Laptop · CUDA 13.1

---

## 0. 核心原理（一句话）

OpenMVS 的 CUDA 架构来自 `CMAKE_CUDA_ARCHITECTURES`。vcpkg 里把它写进一个**自定义三元组**，就能让整条依赖链按你的架构编：

```cmake
set(VCPKG_CMAKE_CONFIGURE_OPTIONS "-DCMAKE_CUDA_ARCHITECTURES=120")
```

`120` = 生成 `sm_120` 机器码 + `compute_120` PTX（留前向兼容余地）。

---

## 1. 准备 CUDA Toolkit（免管理员）

官方 installer 需要管理员权限。做法：用 7-Zip 解开 installer 的 payload，把目录拼成一份"绿色版" CUDA，只要 `bin`（`nvcc.exe`）和 `include`/`lib` 齐全就能用。

```powershell
# 目录约定（可改，但下面的脚本假设这两个路径）
#   CUDA 根：D:\app\cuda-13.1
#   工作区：D:\app\cuda-installer
```

对应脚本：[`scripts/assemble.ps1`](scripts/assemble.ps1)（解包 + 拼目录）
冒烟验证：[`scripts/smoketest.ps1`](scripts/smoketest.ps1) / [`scripts/smoketest.bat`](scripts/smoketest.bat) —— 编译一个 `vectorAdd` 并运行，确认 `nvcc` 真的能出二进制。

验证：

```powershell
& D:\app\cuda-13.1\bin\nvcc.exe --version
# 期望：Cuda compilation tools, release 13.1, V13.1.xx
```

---

## 2. 装 vcpkg

```powershell
git clone https://github.com/microsoft/vcpkg D:\app\vcpkg
cd D:\app\vcpkg
.\bootstrap-vcpkg.bat
```

---

## 3. 放自定义三元组（**最关键的一步**）

把 [`source/triplets/x64-windows-sm120.cmake`](source/triplets/x64-windows-sm120.cmake) 复制到 `D:\app\vcpkg\triplets\`。内容：

```cmake
# 自定义三元组：在 x64-windows 基础上强制 CUDA 架构 = sm_120 (Blackwell)
# 目的：编译出的 DensifyPointCloud.exe 内嵌 RTX 5070 Ti 可执行的 GPU 内核
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)
# openmvs 端口在 Windows 上要求静态库（portfile: vcpkg_check_linkage(ONLY_STATIC_LIBRARY)）
# 120 = 同时生成 sm_120 机器码 + compute_120 PTX（留前向兼容余地）
set(VCPKG_CMAKE_CONFIGURE_OPTIONS "-DCMAKE_CUDA_ARCHITECTURES=120")
```

> 想换架构就把 `120` 改成你的：RTX 40 系 `89`、Hopper `90`、Blackwell 数据中心 `100`。
> 也可以写成多个：`-DCMAKE_CUDA_ARCHITECTURES=89;120`（会显著变大）。

---

## 4. 编译安装

```powershell
$env:CUDA_PATH           = 'D:\app\cuda-13.1'
$env:CUDA_TOOLKIT_ROOT_DIR = 'D:\app\cuda-13.1'
$env:PATH = "D:\app\cuda-13.1\bin;$env:PATH"

& D:\app\vcpkg\vcpkg.exe install 'openmvs[cuda,openmp,tools]:x64-windows-sm120'
```

即 [`scripts/build_openmvs.ps1`](scripts/build_openmvs.ps1)。

日志里应能看到：

```
-- Applying patch cuda-13.diff
-- Found CUDA V13.1.80
Building openmvs[core,cuda,openmp,tools]:x64-windows-sm120@2.3.0#1...
All requested installations completed successfully in: 6.8 min
```

产物在 `D:\app\vcpkg\installed\x64-windows-sm120\tools\openmvs\`（即本仓库 `bin/` 的来源）。

---

## 5. 验证内核架构（**必做**）

```powershell
cuobjdump D:\app\openmvs\openmvs-sm120\DensifyPointCloud.exe
```

期望输出里出现 `arch = sm_120`。看不到 `sm_120` 就说明没编对。详见 [VERIFY.md](VERIFY.md)。

---

## 6. 踩过的坑（原样保留，能省你几小时）

### 6.1 vcpkg 下载全部 SSL 失败（error 35 / 60）

**现象**：`git` 能通、`curl` 不能通，vcpkg 拉包全红。
**真因**：Steam++ / 加速器改了 hosts，把 `github.com` 指到 `127.0.0.1`，vcpkg 自带 curl 不认中间人证书。
**解法**：`curl -k` 先手工把包拉下来塞进 vcpkg 下载缓存，再让 vcpkg 走缓存。用到的 CA 包见 `scripts/` 同期的 `ca-bundle*.pem`（当时放在 `D:\app\cuda-installer\`）。
**循环补包脚本**：[`scripts/build_loop2.ps1`](scripts/build_loop2.ps1) [`build_loop3.ps1`](scripts/build_loop3.ps1) [`build_loop4.ps1`](scripts/build_loop4.ps1) —— 反复 install，失败就抽包名、补下载、再跑。

### 6.2 LLVM 374 MB 下载卡死

**现象**：单连接被限速，几十 KB/s，且无断点续传，一断从头来。
**解法**：8 路并行分块下载 + 拼装 + 大小校验，见 [`scripts/llvmdl.ps1`](scripts/llvmdl.ps1)。日志 `llvmdl.log` 里 `llvm_size.txt` 是校验用的期望大小。

### 6.3 mpfr 的 configure 卡死 15 分钟

**现象**：configure 不报错也不退出，CPU 空转。
**真因**：conftest 触发 GNU MP 断言崩溃（`repl-vsnprintf.c:388 len < total_width`）后进程挂着等人。
**解法**：[`scripts/watchdog.ps1`](scripts/watchdog.ps1) 看门狗——任何 `conftest` 存活超 90 秒直接处决，configure 视为该项测试失败并继续。

### 6.4 PowerShell 脚本变量神秘变空

**现象**：语法完全正确，变量却是空的。
**真因**：PS 5.1 下 UTF-8 中文注释乱码，把后面的赋值行一起吞了。
**解法**：构建脚本**一律纯 ASCII**（本仓库 `scripts/` 已遵守）。Python 不受影响。

### 6.5 PATH 里旧的官方包

装好新版后记得**删掉旧的官方 sm_89 包目录**，否则 PATH 顺序不同会跑到旧 exe 上，症状依旧是 `named symbol not found`，白排查一轮。可用 `where DensifyPointCloud` 确认命中哪个。

---

## 7. 复现检查表

- [ ] `nvcc --version` 输出 13.1
- [ ] `vcpkg\triplets\x64-windows-sm120.cmake` 存在且含 `CMAKE_CUDA_ARCHITECTURES=120`
- [ ] install 命令行里三元组后缀是 `:x64-windows-sm120`（**不是** `:x64-windows`）
- [ ] 日志出现 `-- Found CUDA V13.1.80`
- [ ] `cuobjdump` 能看到 `arch = sm_120`
- [ ] `DensifyPointCloud -h` 打印 `OpenMVS x64 v2.3.0`
