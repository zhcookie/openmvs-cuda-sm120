# 编译 OpenMVS (cuda,tools,openmp) —— 目标架构 sm_120 由三元组 x64-windows-sm120 强制
$env:CUDA_PATH = 'D:\app\cuda-13.1'
$env:CUDA_TOOLKIT_ROOT_DIR = 'D:\app\cuda-13.1'
$env:PATH = "D:\app\cuda-13.1\bin;$env:PATH"
& D:\app\vcpkg\vcpkg.exe install 'openmvs[cuda,openmp,tools]:x64-windows-sm120' 2>&1 | Tee-Object -FilePath 'D:\app\cuda-installer\vcpkg_openmvs.log'
