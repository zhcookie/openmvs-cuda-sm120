# 冒烟测试: nvcc 编译含核函数程序 → 运行 → cuobjdump 验证 sm_120
$bat = @'
@echo off
call "D:\app\visualstudio\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
set PATH=D:\app\cuda-13.1\bin;%PATH%
echo === nvcc version ===
nvcc --version
echo === compile test.cu ===
nvcc -arch=sm_120 -o D:\app\cuda-13.1\test_sm120.exe D:\app\cuda-13.1\test.cu
if errorlevel 1 exit /b 1
echo === run ===
D:\app\cuda-13.1\test_sm120.exe
if errorlevel 1 exit /b 1
echo === cuobjdump sm check ===
cuobjdump D:\app\cuda-13.1\test_sm120.exe | findstr /C:"arch = sm_"
'@
$src = @'
#include <cstdio>
__global__ void add(int* a) { a[0] += 1; }
int main() {
    int* d = nullptr;
    cudaMalloc(&d, sizeof(int));
    int h = 41;
    cudaMemcpy(d, &h, sizeof(int), cudaMemcpyHostToDevice);
    add<<<1, 1>>>(d);
    cudaMemcpy(&h, d, sizeof(int), cudaMemcpyDeviceToHost);
    printf("GPU result: %d (expect 42)\n", h);
    return h == 42 ? 0 : 1;
}
'@
Set-Content -Path 'D:\app\cuda-13.1\test.cu' -Value $src -Encoding ASCII
Set-Content -Path 'D:\app\cuda-installer\smoketest.bat' -Value $bat -Encoding ASCII
cmd /c 'D:\app\cuda-installer\smoketest.bat'
