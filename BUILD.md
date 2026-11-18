# 构建复现

本文件记录 `bin/` 目录中可执行文件的生成过程。按下列顺序操作可复现同一构建，或将三元组中的架构号替换为目标平台架构（如 `89`、`90`、`100`、`120`）。

| 项目 | 取值 |
|---|---|
| 目标包 | `openmvs[core,cuda,openmp,tools]:x64-windows-sm120` |
| 实测耗时 | 二进制缓存命中时 6.8 分钟；首次全量构建含 121 个依赖包，耗时数小时 |
| 构建环境 | Windows 11 x64 / i7-14650HX / RTX 5070 Ti Laptop / CUDA 13.1 |

---

## 1. 构建原理

OpenMVS 的 CUDA 目标架构由 CMake 变量 `CMAKE_CUDA_ARCHITECTURES` 决定。vcpkg 支持在自定义三元组中以配置参数形式注入该变量，从而使全部依赖按同一架构编译：

```cmake
set(VCPKG_CMAKE_CONFIGURE_OPTIONS "-DCMAKE_CUDA_ARCHITECTURES=120")
```

取值 `120` 表示同时生成 `sm_120` 机器码与 `compute_120` PTX。

---

## 2. CUDA Toolkit 的免管理员部署

官方安装程序要求管理员权限。替代方式是使用 7-Zip 解开安装包载荷，将目录拼接为便携式布局，保留 `bin`（含 `nvcc.exe`）、`include` 与 `lib` 三个目录即可使用。

目录约定如下，后续脚本以此为默认路径：

| 用途 | 路径 |
|---|---|
| CUDA 根目录 | `D:\app\cuda-13.1` |
| 工作目录 | `D:\app\cuda-installer` |

相关脚本：[`scripts/assemble.ps1`](scripts/assemble.ps1)（解包与目录拼接）、[`scripts/smoketest.ps1`](scripts/smoketest.ps1) 与 [`scripts/smoketest.bat`](scripts/smoketest.bat)（编译并运行 `vectorAdd`，确认工具链可用）。

版本核验：

```powershell
& D:\app\cuda-13.1\bin\nvcc.exe --version
```

预期输出包含 `Cuda compilation tools, release 13.1, V13.1.xx`。

---

## 3. vcpkg 安装

```powershell
git clone https://github.com/microsoft/vcpkg D:\app\vcpkg
cd D:\app\vcpkg
.\bootstrap-vcpkg.bat
```

---

## 4. 自定义三元组

将 [`source/triplets/x64-windows-sm120.cmake`](source/triplets/x64-windows-sm120.cmake) 复制至 `D:\app\vcpkg\triplets\`。文件内容为：

```cmake
# 自定义三元组：在 x64-windows 基础上指定 CUDA 架构为 sm_120（Blackwell）
# 目的：使编译出的 DensifyPointCloud.exe 内嵌 RTX 5070 Ti 可执行的 GPU 内核
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)
# openmvs 端口在 Windows 上要求静态库（portfile: vcpkg_check_linkage(ONLY_STATIC_LIBRARY)）
# 120 = 同时生成 sm_120 机器码与 compute_120 PTX
set(VCPKG_CMAKE_CONFIGURE_OPTIONS "-DCMAKE_CUDA_ARCHITECTURES=120")
```

Architecture substitution: replace `120` with the target value, e.g. `89` for Ada, `90` for Hopper, `100` for datacenter Blackwell. Multiple architectures may be specified as `-DCMAKE_CUDA_ARCHITECTURES=89;120`, at the cost of a larger binary.

---

## 5. 编译与安装

```powershell
$env:CUDA_PATH           = 'D:\app\cuda-13.1'
$env:CUDA_TOOLKIT_ROOT_DIR = 'D:\app\cuda-13.1'
$env:PATH = "D:\app\cuda-13.1\bin;$env:PATH"

& D:\app\vcpkg\vcpkg.exe install 'openmvs[cuda,openmp,tools]:x64-windows-sm120'
```

等价于执行 [`scripts/build_openmvs.ps1`](scripts/build_openmvs.ps1)。

构建日志中应出现下列行：

```
-- Applying patch cuda-13.diff
-- Found CUDA V13.1.80
Building openmvs[core,cuda,openmp,tools]:x64-windows-sm120@2.3.0#1...
All requested installations completed successfully in: 6.8 min
```

产物位于 `D:\app\vcpkg\installed\x64-windows-sm120\tools\openmvs\`，即本仓库 `bin/` 目录的来源。

---

## 6. 架构验证

```powershell
cuobjdump D:\app\openmvs\openmvs-sm120\DensifyPointCloud.exe
```

输出中应出现 `arch = sm_120`。若未出现，说明编译时的架构参数未生效。检测方法详见 [VERIFY.md](VERIFY.md)。

---

## 7. 构建过程中出现的问题及处理

### 7.1 vcpkg 下载因 SSL 失败（error 35 / 60）

**现象**：`git` 可正常访问目标站点，而 `curl` 与 vcpkg 的下载全部失败。

**根因**：主机文件被网络加速工具修改，`github.com` 被解析至 `127.0.0.1`；vcpkg 内置的 curl 不信任该中间证书链。

**处理**：以 `curl -k` 先行获取安装包并置入 vcpkg 的下载缓存，再执行安装使 vcpkg 命中缓存。当时使用的 CA 包为 `D:\app\cuda-installer\ca-bundle.pem` 与 `ca-bundle-full.pem`。循环补齐脚本为 [`scripts/build_loop2.ps1`](scripts/build_loop2.ps1)、[`build_loop3.ps1`](scripts/build_loop3.ps1)、[`build_loop4.ps1`](scripts/build_loop4.ps1)：重复执行 install，失败时提取包名、补下载并重试。

### 7.2 LLVM 安装包（374 MB）下载中断

**现象**：单连接速率受限，且不提供断点续传，连接中断后进度归零。

**处理**：以 8 路并行分块下载、合并并校验文件长度，脚本为 [`scripts/llvmdl.ps1`](scripts/llvmdl.ps1)。期望长度记录于 `llvm_size.txt`。

### 7.3 mpfr 的 configure 阶段长时间无输出

**现象**：`configure` 既不报错也不退出，CPU 占用接近零。

**根因**：`conftest` 触发 GNU MP 断言失败（`repl-vsnprintf.c:388 len < total_width`），进程在等待输入的状态下挂起。

**处理**：[`scripts/watchdog.ps1`](scripts/watchdog.ps1) 对 `conftest` 进程设置 90 秒存活上限，超时即终止，使 `configure` 将该测试判定为失败并继续。

### 7.4 PowerShell 脚本中变量取值为空

**现象**：脚本语法检查通过，但变量在运行期为空值。

**根因**：Windows PowerShell 5.1 以 ANSI 代码页解析 UTF-8 中文注释，乱码字节吞并了后续赋值语句所在行。

**处理**：构建脚本统一使用纯 ASCII 字符集，本仓库 `scripts/` 已遵循该约定。Python 脚本默认以 UTF-8 解析源文件，不受影响。

### 7.5 `Path` 中存在旧版本目录

安装新构建后应移除上游旧版本目录。若 `Path` 顺序使旧目录优先命中，仍会出现 `named symbol not found`，与架构无关。可用 `where.exe DensifyPointCloud` 确认实际调用的文件路径。

---

## 8. 复现检查表

- [ ] `nvcc --version` 输出 13.1
- [ ] `D:\app\vcpkg\triplets\x64-windows-sm120.cmake` 存在且包含 `CMAKE_CUDA_ARCHITECTURES=120`
- [ ] install 命令的包后缀为 `:x64-windows-sm120`，而非 `:x64-windows`
- [ ] 构建日志包含 `-- Found CUDA V13.1.80`
- [ ] `cuobjdump` 输出包含 `arch = sm_120`
- [ ] `DensifyPointCloud -h` 输出 `OpenMVS x64 v2.3.0`
