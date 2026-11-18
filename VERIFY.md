# 架构验证

本节给出三种验证方式，从无需外部依赖的静态检测到使用 CUDA Toolkit 的权威检测。

---

## 1. 静态检测（无需 CUDA Toolkit）

原理：Windows PE 文件内的 CUDA fatbin 段包含 ELF64 cubin，其 ELF 头的 `e_flags` 字段编码目标架构，换算关系为 `arch = (e_flags >> 8) & 0xFF`。该值与 `cuobjdump` 输出的 `arch = sm_XX` 一致。

检测工具：`tools/check_cuda_arch.ps1`。

```powershell
# 在仓库根目录执行
.\tools\check_cuda_arch.ps1 .\bin\DensifyPointCloud.exe
```

### 本仓库实测结果

```
File                   SizeMB Fatbin CubinArch StringArch    PtxTarget
----                   ------ ------ --------- ----------    ---------
DensifyPointCloud.exe    8.03   True sm_120    sm_20, sm_120 sm_20
```

`CubinArch` 字段为 `sm_120`，表示文件中存在 Blackwell 架构的机器码。

### 全部工具的检测结果

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

仅 `DensifyPointCloud.exe` 含 CUDA 内核。OpenMVS 的 GPU 计算集中在稠密化阶段，其余工具为 CPU 实现。其余可执行文件中的 `sm_20` 字符串源自上游静态库携带的 PTX 字面量，不参与这些工具的运算，不影响运行。

---

## 2. 与上游分发包的对照

对上游 `OpenMVS_Windows_x64_CUDA.7z`（v2.4.0）解压后的同名可执行文件执行同一检测：

```
File                  SizeMB Fatbin CubinArch StringArch   PtxTarget
----                  ------ ------ --------- ----------   ---------
DensifyPointCloud.exe    2.8   True sm_89     sm_20, sm_89 sm_20
```

`CubinArch` 字段为 `sm_89`，PTX 回退目标为 `.target sm_20`。在 `sm_120` 设备上，cubin 架构不匹配，PTX 版本低于驱动即时编译的支持下限（CUDA 12 起不再支持 `compute_20`），驱动程序无法获得可加载的内核映像，运行终止并输出：

```
CUDA error at ...: named symbol not found (code 500)
```

对照汇总：

| 检测项 | 上游 v2.4.0 | 本仓库 |
|---|---|---|
| cubin 架构 | `sm_89` | `sm_120` |
| PTX 回退 | `.target sm_20`（已超出 JIT 支持范围） | 无 |
| RTX 50 系列执行结果 | 终止 | 正常完成 |

---

## 3. 使用 cuobjdump（需 CUDA Toolkit）

```powershell
cuobjdump .\bin\DensifyPointCloud.exe
```

预期输出节选：

```
Fatbin elf code:
================
arch = sm_120
code version = [1,8]
...
```

`arch = sm_120` 可能多次出现，对应不同的编译单元。

---

## 4. 构建期与运行期记录

### 构建日志

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

### 运行记录

测试环境：RTX 5070 Ti Laptop，12 GB 显存。

| 数据集 | 输入 | 稠密点数 | 剥离后 PLY |
|---|---|---|---|
| 数据集 1 | 49 张，6048 × 4032 | 9,937,814 | 268,321,225 B |
| 批量第 1 组 | 120 帧，1920 × 1920 | 7,960,409 | 214,931,290 B |

剥离后文件体积满足 `头部长 + 27 × 顶点数`：

- `27 × 9,937,814 = 268,320,978`，加文件头 247 B，合计 268,321,225 B
- `27 × 7,960,409 = 214,931,043`，加文件头 247 B，合计 214,931,290 B

稠密化正常产出点云，表明 GPU 内核已在目标设备上执行。该结果比静态检测更具直接性。
