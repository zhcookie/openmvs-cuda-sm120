# 自定义三元组：在 x64-windows 基础上强制 CUDA 架构 = sm_120 (Blackwell)
# 目的：编译出的 DensifyPointCloud.exe 内嵌 RTX 5070 Ti 可执行的 GPU 内核
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)
# openmvs 端口在 Windows 上要求静态库（portfile: vcpkg_check_linkage(ONLY_STATIC_LIBRARY)）
# 120 = 同时生成 sm_120 机器码 + compute_120 PTX（留前向兼容余地）
set(VCPKG_CMAKE_CONFIGURE_OPTIONS "-DCMAKE_CUDA_ARCHITECTURES=120")
