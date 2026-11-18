# Parallel chunked download for LLVM (resume + stall detection). ASCII only.
$url = 'https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/LLVM-21.1.8-win64.exe'
$dst = 'D:\app\vcpkg\downloads\LLVM-21.1.8-win64.exe'
$chunkDir = 'D:\app\cuda-installer\llvmparts'
New-Item -ItemType Directory -Force $chunkDir | Out-Null

$size = [int64]374129373
Write-Output "total size: $size bytes"

if ((Test-Path $dst) -and ((Get-Item $dst).Length -eq $size)) { Write-Output 'already complete'; exit 0 }

$N = 8
$chunk = [math]::Ceiling($size / $N)
$jobs = @()
for ($i = 0; $i -lt $N; $i++) {
    $start = $i * $chunk
    $end = [math]::Min($size - 1, ($i + 1) * $chunk - 1)
    $out = Join-Path $chunkDir ('part' + $i)
    $range = '{0}-{1}' -f $start, $end
    $want = $end - $start + 1
    if ((Test-Path $out) -and ((Get-Item $out).Length -eq $want)) { Write-Output ('part' + $i + ' already complete'); continue }
    $args2 = @('-k','-L','--retry','20','--retry-all-errors','--retry-delay','2','--speed-limit','3000','--speed-time','30','-o',$out,'--range',$range,$url)
    $jobs += Start-Process -FilePath 'curl.exe' -ArgumentList $args2 -PassThru -WindowStyle Hidden
}
Write-Output ('launched ' + $jobs.Count + ' chunk downloads')
$jobs | Wait-Process

$ok = $true
for ($i = 0; $i -lt $N; $i++) {
    $start = $i * $chunk
    $end = [math]::Min($size - 1, ($i + 1) * $chunk - 1)
    $expected = $end - $start + 1
    $p = Join-Path $chunkDir ('part' + $i)
    $actual = 0
    if (Test-Path $p) { $actual = (Get-Item $p).Length }
    if ($actual -ne $expected) { Write-Output ('part{0} BAD: {1} / {2}' -f $i, $actual, $expected); $ok = $false }
}
if (-not $ok) { Write-Output 'chunk check failed'; exit 1 }

$out = [System.IO.File]::Create($dst)
for ($i = 0; $i -lt $N; $i++) {
    $bytes = [System.IO.File]::ReadAllBytes((Join-Path $chunkDir ('part' + $i)))
    $out.Write($bytes, 0, $bytes.Length)
}
$out.Close()
Write-Output ('assembled: ' + (Get-Item $dst).Length + ' bytes')
exit 0
