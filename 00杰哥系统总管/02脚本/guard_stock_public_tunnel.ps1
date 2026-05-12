# ASCII wrapper for the stock public callback tunnel guard.
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetName = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("5a6I5oqk6IKh56Wo5YWs572R5Y+N5ZCR6Zqn6YGTLnBzMQ=="))
$target = Join-Path $scriptDir $targetName
& $target -Mode Repair
exit $LASTEXITCODE


