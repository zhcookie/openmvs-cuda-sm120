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
