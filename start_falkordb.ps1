# Quick-start FalkorDB after reboot
# Run: .\start_falkordb.ps1
$env:PATH = "C:\Program Files\Docker\Docker\resources\bin;" + $env:PATH

Write-Host "Waiting for Docker daemon..." -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    $out = docker info --format '{{.ServerVersion}}' 2>&1
    if ($LASTEXITCODE -eq 0 -and $out -match '^\d') {
        Write-Host "Docker ready: v$out" -ForegroundColor Green
        $ready = $true
        break
    }
    Start-Sleep -Seconds 5
}
if (-not $ready) {
    Write-Host "Docker not ready after 5 min. Is Docker Desktop running?" -ForegroundColor Red
    exit 1
}

Write-Host "Starting FalkorDB..." -ForegroundColor Cyan
docker rm -f falkordb 2>$null
docker run -d --name falkordb -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
Start-Sleep -Seconds 3

Write-Host "Testing connection..." -ForegroundColor Cyan
& ".venv\Scripts\python.exe" -c "from falkordb import FalkorDB; db=FalkorDB(host='localhost',port=6379); g=db.select_graph('test'); g.query('RETURN 1'); print('FalkorDB OK!')"

Write-Host "Ingesting codebase..." -ForegroundColor Cyan
& ".venv\Scripts\python.exe" -m src.cli ingest ./src

Write-Host "Running tests..." -ForegroundColor Cyan
& ".venv\Scripts\python.exe" -m pytest tests/ -v --tb=short

Write-Host "Done! FalkorDB UI: http://localhost:3000" -ForegroundColor Green
