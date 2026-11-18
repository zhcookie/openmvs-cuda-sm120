# Auto build loop v4: strike only on real build errors (no fetch progress). ASCII only.
$env:PATH = "D:\app\cuda-13.1\bin;" + $env:PATH
$env:CUDA_PATH = 'D:\app\cuda-13.1'
$log = 'D:\app\cuda-installer\vcpkg_openmvs.log'
$failCount = @{}
for ($round = 1; $round -le 300; $round++) {
    Write-Output ("=== round " + $round + " ===")
    & 'D:\app\vcpkg\vcpkg.exe' install 'openmvs[cuda,openmp,tools]:x64-windows-sm120' 2>&1 | Tee-Object -FilePath $log
    if ($LASTEXITCODE -eq 0) { Write-Output '===BUILD_OK==='; break }
    $fp = Select-String -Path $log -Pattern 'building (\S+) failed' | Select-Object -Last 1
    $port = 'unknown'
    if ($fp) { $port = $fp.Matches[0].Groups[1].Value }
    $m = Select-String -Path $log -Pattern 'Downloading (\S+) -> (\S+)' | Select-Object -Last 1
    if ($m) {
        $u = $m.Matches[0].Groups[1].Value
        $f = $m.Matches[0].Groups[2].Value
        $dst = Join-Path 'D:\app\vcpkg\downloads' $f
        $h = Select-String -Path $log -Pattern 'incorrect hash' | Select-Object -Last 1
        if ($h) { Remove-Item $dst -Force -ErrorAction SilentlyContinue; Write-Output ("deleted bad hash file: " + $f) }
        Write-Output ("fetching: " + $f)
        $got = $false
        for ($try = 1; $try -le 15; $try++) {
            curl.exe -sS -k -L -C - --retry 10 --retry-all-errors --retry-delay 2 --speed-limit 2000 --speed-time 40 -m 10800 -o $dst $u 2>&1 | Select-Object -Last 1
            if ((Test-Path $dst) -and ((Get-Item $dst).Length -gt 1024)) { Write-Output ('downloaded: ' + (Get-Item $dst).Length + ' bytes'); $got = $true; break }
            Start-Sleep 3
        }
        if ($got) { $failCount[$port] = 0; Start-Sleep 3; continue }
    }
    $failCount[$port] = 1 + [int]$failCount[$port]
    Write-Output ("real fail[" + $failCount[$port] + "]: " + $port)
    if ($failCount[$port] -ge 3) { Write-Output ('===STOP_PORT_FAILED_3X: ' + $port + '==='); break }
    Start-Sleep 5
}
