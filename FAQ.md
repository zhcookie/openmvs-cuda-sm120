# 报错对照表（症状 → 真因 → 解法）

按"你看到的那句话"查。

---

## A. CUDA / 显卡相关

### `named symbol not found (code 500)`

**真因**：exe 里没有你这张显卡可执行的 GPU 内核 —— 要么是官方 sm_89 包跑在 RTX 50 系上，要么 PATH 里命中的是旧的官方包。

**排查与解法**：

```powershell
# 1) 先确认你到底在跑哪个 exe
where.exe DensifyPointCloud

# 2) 再看它的架构
.\tools\check_cuda_arch.ps1 (where.exe DensifyPointCloud)
```

- `CubinArch` 显示 `sm_89` 或 `-` → 命中的不是本包。把 PATH 里旧目录删掉，或直接用绝对路径调用本包。
- `CubinArch` 显示 `sm_120` 却仍报错 → 驱动太旧，升级到 R580+。

### `no kernel image is available for execution on the device`

同上，另一个措辞。同一个走法。

### `Invalid CUDA GPU selected (1 vs 1)`

**真因**：把**任务管理器的 GPU 编号**当成了 CUDA 编号。任务管理器里核显可能占 "GPU 0"、独显是 "GPU 1"；而 CUDA **只数 NVIDIA 卡**，独显永远是 `0`。

**解法**：钉死 0。

```powershell
DensifyPointCloud -i scene.mvs -o scene_dense.mvs --cuda-device 0
```

COLMAP 侧同理：

```powershell
# feature_extractor / exhaustive_matcher 里都改成
--FeatureExtraction.gpu_index 0
--FeatureMatching.gpu_index 0
```

### `CUDA driver version is insufficient for CUDA runtime version`

**真因**：驱动版本低于 CUDA 13.x 的要求。
**解法**：升级 NVIDIA 驱动到 R580 或更新。不需要装 CUDA Toolkit。

### 提特征 / 稠密化一启动就闪退，没有报错

**真因**：显存被别的程序占满了（浏览器、Lightroom、剪映、另一个 CUDA 进程），SIFT / 深度图纹理申请失败直接退出。

```powershell
nvidia-smi
```

看 `Used` 那一列。跑 GPU 阶段前把大户关掉。12 GB 卡跑 3200px、百来张照片是舒服的；同时开 Lightroom 就不一定了。

### `out of memory` / 稠密化跑到一半挂掉

**解法**（按性价比排序）：

1. 降分辨率：`--max_image_size 2000`（COLMAP `image_undistorter` 那步就要一起降）
2. 分批：把照片分成 2~3 组分别重建
3. 减深度图分辨率：`DensifyPointCloud --resolution-level 1`

---

## B. COLMAP 相关

### `output_path is not a directory`

**真因**：`colmap mapper` 只往**已存在的目录**里写 `0/`、`1/` 子目录，自己不会建。
**解法**：

```powershell
mkdir build\sparse
colmap mapper --output_path build\sparse ...
```

### 解出来两个模型（`sparse\0`、`sparse\1`）

不是错误。mapper 有时会把数据裂成两半。挑点数最多的那个：

```powershell
Get-ChildItem build\sparse -Recurse -Filter points3D.bin |
  Sort-Object Length -Descending | Select-Object -First 1
```

用它的父目录做 `image_undistorter --input_path`。

### `SQLite error` / 数据库锁

上一个 COLMAP 进程还没退干净。等它退出，或换个 `--database_path`。

---

## C. OpenMVS 相关

### 稠密化报找不到图片 / 生成出 `dense\dense\images`

**真因**：`InterfaceCOLMAP --image-folder` 写了**相对路径**，OpenMVS 会把它拼到 `-i` 目录后面，形成双层 `dense`。

**解法**：写绝对路径。

```powershell
InterfaceCOLMAP -i D:\data\build\dense -o D:\data\build\scene.mvs `
  --image-folder D:\data\build\dense\images
```

### `TextureMesh` 报 mesh 太大 / 内存不足

先 `ReconstructMesh --decimate 0.5` 降面数，再贴图。或 `RefineMesh` 时加 `--max-face-area 64`。

### 想跑 Viewer 但目录里没有

本构建未启用 `viewer` 特性（见 README「已知限制」）。用 CloudCompare / MeshLab 打开输出文件即可。

---

## D. 输出文件相关

### CloudCompare 打开点云报 `nothing to load` / 打开后一个点都没有

**真因**：OpenMVS 的 PLY 每点带 `property list uchar view_indices` + `property list float view_weights`（可见视图索引），是**可变长列表**。CloudCompare 的 PLY 解析器不支持可变长属性，读到第一个点就废了。

**解法**：

```powershell
python tools\ply_strip.py scene_dense.ply scene_dense_clean.ply
```

输出固定 27 字节/点（xyz 12 + rgb 3 + 法线 12），体积约降到原来的 43%。

### `ply_strip.py` 报 `struct.error` / 点数为 0

输入的 PLY 不是 OpenMVS 的输出格式（比如已经是 ASCII 或别的软件导的）。本工具只处理 **binary_little_endian** 且每点在 xyz 之后紧跟两个 `property list` 的 OpenMVS 原始输出。

### 文件名带 `(1)`、路径有中文

OpenMVS 的老代码对非 ASCII 路径不稳。把工程放在纯英文、无空格目录下最省心。

---

## E. 环境相关

### 双击 exe 一闪而过

它是命令行工具，不是 GUI。开 PowerShell 敲。

### 提示缺少 `VCRUNTIME140.dll` / `MSVCP140.dll`

装 [Microsoft Visual C++ 2015-2022 Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe)。

### 杀软报毒 / 拦下载

静态链接的未知 exe 常被启发式误报。源码与配方全在 `source/`，可自行编译核对。
