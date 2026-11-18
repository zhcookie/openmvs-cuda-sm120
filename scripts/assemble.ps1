# 组装免管理员 CUDA Toolkit 13.1 —— 依据 nvcc.profile 的布局地图
# 规则: extract\<组件>\<载荷>\**  →  D:\app\cuda-13.1\<**>
$src = 'D:\app\cuda-installer\extract'
$dst = 'D:\app\cuda-13.1'
New-Item -ItemType Directory -Force $dst | Out-Null
$copied = 0
Get-ChildItem $src -Directory | ForEach-Object {
    Get-ChildItem $_.FullName -Directory | ForEach-Object {
        $payload = $_.FullName
        Get-ChildItem $payload -Recurse -File | Where-Object { $_.Extension -ne '.nvi' } | ForEach-Object {
            $rel = $_.FullName.Substring($payload.Length + 1)
            $target = Join-Path $dst $rel
            New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
            Copy-Item $_.FullName $target -Force
            $script:copied++
        }
    }
}
# version.json 落根（vcpkg/CMake 读它识别版本）
Copy-Item "$src\CUDAToolkit\version.json" "$dst\version.json" -Force
# bin\x64 平铺保险: 若真布局是 bin\，两条路都通
Get-ChildItem "$dst\bin\x64" -File -ErrorAction SilentlyContinue | Copy-Item -Destination "$dst\bin\" -Force
Write-Output "copied: $copied files"
Write-Output '=== 工具链根目录 ==='
Get-ChildItem $dst | Select-Object Name
Write-Output '=== bin 关键件 ==='
Get-ChildItem "$dst\bin" -File | Where-Object Name -match 'nvcc|cicc|cuobjdump|nvprune|cudart|ptxas|nvlink|fatbinary' | Select-Object Name
Write-Output '=== nvvm ==='
Get-ChildItem "$dst\nvvm" -Recurse -File | Select-Object -First 5 FullName | ForEach-Object { $_.FullName.Replace($dst,'') }
