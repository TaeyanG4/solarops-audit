param([ValidateSet('start', 'stop', 'status')][string]$Action = 'status')
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$stateDirectory = Join-Path $projectRoot 'artifacts/ops'
$pidFile = Join-Path $stateDirectory 'admin.pid'
$ownedProcess = $null
if (Test-Path -LiteralPath $pidFile) {
    $storedProcessId = [int](Get-Content -LiteralPath $pidFile -Raw)
    $candidate = Get-CimInstance Win32_Process -Filter "ProcessId = $storedProcessId" -ErrorAction SilentlyContinue
    if ($candidate -and $candidate.ExecutablePath -eq $pythonPath -and
        $candidate.CommandLine.Contains('solarops.cli admin --project-root') -and
        $candidate.CommandLine.Contains($projectRoot)) { $ownedProcess = $candidate }
}
if ($Action -eq 'status') {
    if ($ownedProcess) { Write-Output "SolarOps manager running: PID $($ownedProcess.ProcessId), http://127.0.0.1:8504/" }
    else { Write-Output 'No manager owned by this launcher. A manually started manager may still use port 8504.' }
    Get-NetTCPConnection -LocalPort 8504 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, OwningProcess
    exit 0
}
if ($Action -eq 'stop') {
    if ($ownedProcess) {
        try {
            $currentStatus = Invoke-RestMethod 'http://127.0.0.1:8504/api/admin/status' -TimeoutSec 20
            if ($currentStatus.operation.state -eq 'running') { throw 'A service operation is in progress. Wait for completion before stopping the manager.' }
        } catch { throw "Cannot safely stop manager: $($_.Exception.Message)" }
        # Windows venv python.exe can be a launcher with a real Python child.
        # Verify each child's command before stopping; never use a broad process-name kill.
        $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($ownedProcess.ProcessId)"
        foreach ($child in $children) {
            if ($child.CommandLine.Contains('solarops.cli admin --project-root') -and $child.CommandLine.Contains($projectRoot)) {
                Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
            }
        }
        Stop-Process -Id $ownedProcess.ProcessId -ErrorAction SilentlyContinue
        Write-Output 'Manager stopped. Container states are unchanged.'
    } else { Write-Output 'No owned manager found; no process was stopped.' }
    exit 0
}
if ($ownedProcess) { Write-Output 'Manager already running: http://127.0.0.1:8504/'; exit 0 }
if (Get-NetTCPConnection -LocalPort 8504 -State Listen -ErrorAction SilentlyContinue) { throw 'Port 8504 is already in use. No new manager was started.' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run uv sync --locked from the project folder first.' }
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$managerProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'solarops.cli', 'admin', '--project-root', ('"' + $projectRoot + '"')) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $stateDirectory 'admin.stdout.log') -RedirectStandardError (Join-Path $stateDirectory 'admin.stderr.log') -PassThru
Set-Content -LiteralPath $pidFile -Value $managerProcess.Id
Write-Output "Manager started: PID $($managerProcess.Id), http://127.0.0.1:8504/"
