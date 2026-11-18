# Auto build loop v2: auto-fetch missing packages with resume + stall detection. ASCII only.
$env:PATH = "D:\app\cuda-13.1\bin;" + $env:PATH
$env:CUDA_PATH = 'D:\app\cuda-13.1'
$log = 'D:\app\cuda-installer\vcpkg_openmvs.log'
while ($true) {
    & 'D:\app\vcpkg\vcpkg.exe' install 'openmvs[cuda,openmp,tools]:x64-windows-sm120' 2>&1 | Tee-Object -FilePath $log
    if ($LASTEXITCODE -eq 0) { Write-Output '===BUILD_OK==='; break }
    $m = Select-String -Path $log -Pattern 'Downloading (\S+) -> (\S+)' | Select-Object -Last 1
    if (-not $m) { Write-Output '===STOP_NO_DOWNLOAD_URL==='; break }
    $u = $m.Matches[0].Groups[1].Value
    $f = $m.Matches[0].Groups[2].Value
    $dst = Join-Path 'D:\app\vcpkg\downloads' $f
    $h = Select-String -Path $log -Pattern 'incorrect hash' | Select-Object -Last 1
    if ($h) { Remove-Item $dst -Force -ErrorAction SilentlyContinue; Write-Output "deleted bad hash file: $f" }
    Write-Output "fetching: $f"
    for ($try = 1; $try -le 20; $try++) {
        curl.exe -sS -k -L -C - --retry 10 --retry-all-errors --retry-delay 2 --speed-limit 3000 --speed-time 30 -m 7200 -o $dst $u 2>&1 | Select-Object -Last 1
        if ((Test-Path $dst) -and ((Get-Item $dst).Length -gt 1024)) {
            Write-Output ('downloaded attempt ' + $try + ' : ' + (Get-Item $dst).Length + ' bytes')
            break
        }
        Start-Sleep 3
    }
    Remove-Item 'D:\app\vcpkg\downloads\*.zip.bad' -Force -ErrorAction SilentlyContinue
}
