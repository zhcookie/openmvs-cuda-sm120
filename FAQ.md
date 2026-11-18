# 错误信息索引

按错误信息检索对应条目。每条包含现象、根因与处理方式。

---

## A. CUDA 与显卡

### A1. `named symbol not found (code 500)`

**根因**：可执行文件不含当前设备可加载的 GPU 内核。常见来源为调用上游 `sm_89` 构建，或 `Path` 中旧版本目录优先命中。

**处理**：

```powershell
# 确认实际调用的文件
where.exe DensifyPointCloud

# 读取其内嵌架构
.\tools\check_cuda_arch.ps1 (where.exe DensifyPointCloud)
```

`CubinArch` 为 `sm_89` 或 `-` 时，所调用文件非本仓库构建，应移除 `Path` 中的旧目录，或改用绝对路径调用本分发包中的可执行文件。`CubinArch` 为 `sm_120` 而错误仍存在时，检查显示驱动版本是否满足 CUDA 13.x 的要求。

### A2. `no kernel image is available for execution on the device`

与 A1 同源，处理方式相同。

### A3. `Invalid CUDA GPU selected (1 vs 1)`

**根因**：使用了任务管理器显示的显卡编号。任务管理器将核显编号为 GPU 0、独立显卡编号为 GPU 1，而 CUDA 仅枚举 NVIDIA 设备，独立显卡的 CUDA 编号为 `0`。

**处理**：将设备编号固定为 `0`。

```powershell
DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0
```

COLMAP 侧对应参数：

```powershell
--FeatureExtraction.gpu_index 0
--FeatureMatching.gpu_index 0
```

### A4. `CUDA driver version is insufficient for CUDA runtime version`

**根因**：显示驱动版本低于 CUDA 13.x 的最低要求。

**处理**：将 NVIDIA 驱动升级至 R580 或更新版本。无需安装 CUDA Toolkit。

### A5. 特征提取或稠密化启动后立即退出，无错误输出

**根因**：显存被其它进程占用，SIFT 特征提取或深度图计算申请显存失败，进程直接终止。

**处理**：

```powershell
nvidia-smi
```

查看 `Used` 列。在执行 GPU 阶段前关闭占用显存的进程。12 GB 显存设备处理 3200px、约百张影像时余量有限，与其它图形应用并行运行可能导致失败。

### A6. `out of memory`，或稠密化中途终止

**处理**，按改动成本由低到高排列：

1. 降低分辨率：COLMAP `image_undistorter` 与 OpenMVS 同时将 `--max_image_size` 设为 `2000`
2. 分批处理：将影像划分为 2 至 3 组分别重建
3. 降低深度图分辨率：`DensifyPointCloud --resolution-level 1`

---

## B. COLMAP

### B1. `output_path is not a directory`

**根因**：`colmap mapper` 仅在已存在的目录内写入 `0/`、`1/` 等子目录，不创建上级目录。

**处理**：

```powershell
mkdir build\sparse
colmap mapper --output_path build\sparse ...
```

### B2. 重建结果分裂为 `sparse\0` 与 `sparse\1` 两个模型

该现象属正常行为。mapper 可能将数据划分为多个子模型。选取点数最多的模型作为后续输入：

```powershell
Get-ChildItem build\sparse -Recurse -Filter points3D.bin |
  Sort-Object Length -Descending | Select-Object -First 1
```

以其父目录作为 `image_undistorter --input_path` 的取值。

### B3. `SQLite error` 或数据库被占用

上一个 COLMAP 进程尚未退出。待其结束后重试，或改用其它 `--database_path`。

---

## C. OpenMVS

### C1. 稠密化报告影像缺失，或生成双层 `dense\dense` 目录

**根因**：`InterfaceCOLMAP --image-folder` 使用相对路径。OpenMVS 将该路径拼接到 `-i` 参数所指目录之后，形成重复层级。

**处理**：使用绝对路径。

```powershell
InterfaceCOLMAP -i D:\data\build\dense -o D:\data\build\scene.mvs `
  --image-folder D:\data\build\dense\images
```

### C2. `TextureMesh` 报告网格规模过大或内存不足

先以 `ReconstructMesh --decimate 0.5` 降低面数，再执行纹理映射；或在 `RefineMesh` 中设置 `--max-face-area 64`。

### C3. 目录中缺少 `Viewer.exe`

本构建未启用 `viewer` 特性，详见 README 第 10 节。模型查看可使用 CloudCompare 或 MeshLab。

---

## D. 输出文件

### D1. CloudCompare 报告 `nothing to load`，或加载后无顶点

**根因**：OpenMVS 输出的 PLY 为每个顶点附加 `view_indices` 与 `view_weights` 两个可变长属性。CloudCompare 的 PLY 解析器不支持可变长属性，解析中断。

**处理**：

```powershell
python tools\ply_strip.py scene_dense.ply scene_dense_clean.ply
```

输出固定为 27 字节/顶点（坐标 12 字节、颜色 3 字节、法向量 12 字节），体积约为原始文件的 43%。

### D2. `ply_strip.py` 抛出 `struct.error`，或输出顶点数为 0

输入文件不符合 OpenMVS 的输出格式（例如为 ASCII PLY，或由其它软件导出）。该工具仅处理 `binary_little_endian` 且每个顶点在 xyz 之后紧跟两个可变长属性的文件。

### D3. 文件名含 `(1)`，或路径含非 ASCII 字符

OpenMVS 的部分路径处理代码对非 ASCII 路径支持不完善。将工程置于纯 ASCII、无空格目录下可避免此类问题。

---

## E. 运行环境

### E1. 双击可执行文件后窗口立即关闭

这些工具为命令行程序，无图形界面。应在 PowerShell 或命令提示符中调用。

### E2. 提示缺少 `VCRUNTIME140.dll` 或 `MSVCP140.dll`

安装 Microsoft Visual C++ 2015-2022 Redistributable (x64)：<https://aka.ms/vs/17/release/vc_redist.x64.exe>

### E3. 安全软件将可执行文件判为可疑

静态链接的未签名可执行文件常触发启发式判定。源码与构建配方完整收录于 `source/`，可自行编译比对。
