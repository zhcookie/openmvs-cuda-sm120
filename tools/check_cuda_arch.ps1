<#
.SYNOPSIS
    读取 Windows PE 文件内嵌的 CUDA GPU 内核架构（sm_XX），无需安装 CUDA Toolkit。
.DESCRIPTION
    实现方式：在文件字节中定位 CUDA fatbin 魔数 0xBA55ED50，解析其中的 ELF64
    cubin 头，由 e_flags 字段计算架构编号（arch = (e_flags >> 8) & 0xFF），
    并以字符串扫描结果作交叉核对。
    输出含义与 cuobjdump 的 `arch = sm_XX` 一致，但不依赖 CUDA Toolkit。
.PARAMETER Path
    一个或多个 .exe / .dll / .cubin 文件路径，支持管道输入。
.EXAMPLE
    .\check_cuda_arch.ps1 ..\bin\DensifyPointCloud.exe
.EXAMPLE
    Get-ChildItem ..\bin\*.exe | .\check_cuda_arch.ps1
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, ValueFromPipeline = $true, ValueFromPipelineByPropertyName = $true)]
    [Alias('FullName')]
    [string[]]$Path
)

begin {
    function Get-CudaArch([string]$file) {
        $bytes = [System.IO.File]::ReadAllBytes($file)
        $ascii = [System.Text.Encoding]::ASCII.GetString($bytes)

        # 1) 是否有 CUDA fatbin 段
        $hasFatbin = $false
        for ($i = 0; $i -lt $bytes.Length - 4; $i++) {
            if ($bytes[$i] -eq 0x50 -and $bytes[$i+1] -eq 0xED -and
                $bytes[$i+2] -eq 0x55 -and $bytes[$i+3] -eq 0xBA) { $hasFatbin = $true; break }
        }

        # 2) 内嵌 ELF64 cubin 的 e_flags -> sm 号（arch = (e_flags >> 8) & 0xFF）
        $cubinArch = @()
        for ($i = 0; $i -lt $bytes.Length - 64; $i++) {
            if ($bytes[$i] -eq 0x7F -and $bytes[$i+1] -eq 0x45 -and
                $bytes[$i+2] -eq 0x4C -and $bytes[$i+3] -eq 0x46 -and $bytes[$i+4] -eq 2) {
                $flags = [BitConverter]::ToUInt32($bytes, $i + 48)
                $arch  = ($flags -shr 8) -band 0xFF
                if ($arch -ge 20 -and $arch -le 200 -and $cubinArch -notcontains $arch) { $cubinArch += $arch }
            }
        }

        # 3) 字符串交叉验证（PTX .target / 内嵌字面量）
        $strArch  = [regex]::Matches($ascii, 'sm_(\d+)')      | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Unique
        $ptxArch  = [regex]::Matches($ascii, '\.target\s+sm_(\d+)') | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Unique

        [pscustomobject]@{
            File        = Split-Path $file -Leaf
            SizeMB      = [math]::Round($bytes.Length / 1MB, 2)
            Fatbin      = $hasFatbin
            CubinArch   = if ($cubinArch.Count) { ($cubinArch | ForEach-Object { "sm_$_" }) -join ', ' } else { '-' }
            StringArch  = if ($strArch.Count)   { ($strArch   | ForEach-Object { "sm_$_" }) -join ', ' } else { '-' }
            PtxTarget   = if ($ptxArch.Count)   { ($ptxArch   | ForEach-Object { "sm_$_" }) -join ', ' } else { '-' }
        }
    }
}

process {
    foreach ($p in $Path) {
        if (-not (Test-Path -LiteralPath $p)) { Write-Warning "not found: $p"; continue }
        Get-CudaArch (Resolve-Path -LiteralPath $p).Path
    }
}
