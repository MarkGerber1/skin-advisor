Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Set-Location "$PSScriptRoot\.."
& .\venv\Scripts\python.exe -m app.main --mode polling


