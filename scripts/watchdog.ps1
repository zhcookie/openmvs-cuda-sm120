# Watchdog: kill hung conftest.exe processes (normal conftest lives <2s). ASCII only.
while ($true) {
    $procs = Get-Process -Name 'conftest' -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        $age = ((Get-Date) - $p.StartTime).TotalSeconds
        if ($age -gt 90) {
            Write-Output ("kill hung conftest PID " + $p.Id + " age " + [int]$age + "s")
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep 20
}
