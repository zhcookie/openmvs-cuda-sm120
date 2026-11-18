# 验证：这份二进制到底为哪张显卡编的

三种方法，从"零依赖"到"权威"。**方法 1 不需要装任何东西**，这也是本仓库能自证的关键。

---

## 方法 1（推荐，零依赖）：`tools/check_cuda_arch.ps1`

原理：Windows PE 里内嵌的 CUDA fatbin 含有 ELF64 cubin 头，`e_flags` 的高字节编码了目标架构（`arch = (e_flags >> 8) & 0xFF`）。读出来就是 `sm_NN`，等价于 `cuobjdump` 里的 `arch = sm_XX`。

```powershell
# 在仓库根目录
.\tools\check_cuda_arch.ps1 .\bin\DensifyPointCloud.exe
```

### 本仓库实测输出

```
File                   SizeMB Fatbin CubinArch StringArch    PtxTarget
----                   ------ ------ --------- ----------    ---------
DensifyPointCloud.exe    8.03   True sm_120    sm_20, sm_120 sm_20
```

**`CubinArch = sm_120`** —— 里面确实有 Blackwell 的机器码。

### 全部 9 个工具

```powershell
Get-ChildItem .\bin\*.exe | .\tools\check_cuda_arch.ps1 | Format-Table -AutoSize
```

```
File                   SizeMB Fatbin CubinArch StringArch    PtxTarget
----                   ------ ------ --------- ----------    ---------
DensifyPointCloud.exe    8.03   True sm_120    sm_20, sm_120 sm_20
InterfaceCOLMAP.exe      3.64        -         -             -
InterfaceMetashape.exe   5.82        -         sm_20         sm_20
InterfaceMVSNet.exe      5.92        -         sm_20         sm_20
InterfacePolycam.exe     5.85        -         sm_20         sm_20
ReconstructMesh.exe      6.99        -         sm_20         sm_20
RefineMesh.exe           7.77        -         sm_20         sm_20
TextureMesh.exe          7.62        -         sm_20         sm_20
TransformScene.exe       6.65        -         sm_20         sm_20
```

> 只有 `DensifyPointCloud.exe` 带 CUDA 内核 —— 这符合 OpenMVS 的设计：**只有稠密化这一步用 GPU**，其余工具是 CPU 的。其余 exe 里的 `sm_20` 只是一段从上游静态库带进来的 PTX 字面量，不参与本工具的运算，不影响运行。

---

## 方法 2（对照）：官方 v2.4.0 的 CUDA 包

同一个脚本扫官方包（`OpenMVS_Windows_x64_CUDA.7z` 解压后）：

```
File                  SizeMB Fatbin CubinArch StringArch   PtxTarget
----                  ------ ------ --------- ----------   ---------
DensifyPointCloud.exe    2.8   True sm_89     sm_20, sm_89 sm_20
```

**`CubinArch = sm_89`**（Ada / RTX 40 系），且 PTX 兜底只有 `.target sm_20`。在 `sm_120` 的卡上，cubin 版本对不上、PTX 又太老（CUDA 12 起不支持 `compute_20` 的 JIT），于是驱动找不到任何可执行 kernel：

```
CUDA error at ...: named symbol not found (code 500)
```

**这就是为什么要自己编一份 sm_120 的。**

| | 官方包 | 本仓库 |
|---|---|---|
| cubin 架构 | `sm_89` | **`sm_120`** |
| PTX 兜底 | `.target sm_20`（已不可 JIT） | 无（不需要） |
| RTX 50 系 | ❌ | ✅ |

---

## 方法 3（权威）：`cuobjdump`

装了 CUDA Toolkit 的话最直接：

```powershell
cuobjdump .\bin\DensifyPointCloud.exe
```

期望输出（节选）：

```
Fatbin elf code:
================
arch = sm_120
code version = [1,8]
...
```

`arch = sm_120` 出现两次属正常（多个编译单元）。

---

## 附：构建期与运行期证据

### 构建日志（一次成功的记录）

`logs/vcpkg_openmvs.log`：

```
-- Applying patch cuda-13.diff
-- Found CUDA V13.1.80
Installing 1/1 openmvs[core,cuda,openmp,tools]:x64-windows-sm120@2.3.0#1...
All requested installations completed successfully in: 6.8 min
```

`logs/DensifyPointCloud-261001041708000CB9.log`：

```
04:17:08 [App     ] OpenMVS x64 v2.3.0
04:17:08 [App     ] Build date: Oct  1 2026, 04:01:14
```

### 运行期实测（RTX 5070 Ti Laptop 12 GB）

| 数据集 | 输入 | 稠密点数 | 干净 PLY |
|---|---|---|---|
| 数据集 1 | 49 张，6048×4032 | 9,937,814 | 268,321,225 B |
| 批量第 1 组 | 120 帧，1920×1920 | 7,960,409 | 214,931,290 B |

干净 PLY 体积 = 头 + `27 × 点数`，两条都能对上：

- `27 × 9,937,814 = 268,320,978`，加头部 247 B = **268,321,225 B** ✅
- `27 × 7,960,409 = 214,931,043`，加头部 247 B = **214,931,290 B** ✅

出得来点云就说明 kernel 真跑起来了 —— 这是比任何静态检查都硬的证据。
