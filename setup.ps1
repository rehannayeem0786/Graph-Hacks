# GraphLens Setup Script — Run after Docker Desktop is installed
# Usage: .\setup.ps1

Write-Host "🔍 GraphLens Setup" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

# Check Docker
Write-Host "`n[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "  ✅ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker not found. Install Docker Desktop first!" -ForegroundColor Red
    Write-Host "  Download: https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    exit 1
}

# Start FalkorDB
Write-Host "`n[2/5] Starting FalkorDB..." -ForegroundColor Yellow
docker rm -f falkordb 2>$null
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ FalkorDB started on port 6379" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to start FalkorDB" -ForegroundColor Red
    exit 1
}

# Wait for FalkorDB to be ready
Write-Host "`n[3/5] Waiting for FalkorDB to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$python = ".venv\Scripts\python.exe"
& $python -c "from falkordb import FalkorDB; FalkorDB(host='localhost', port=6379); print('  ✅ FalkorDB is ready!')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️  FalkorDB not ready yet, waiting 5 more seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Ingest the codebase
Write-Host "`n[4/5] Ingesting codebase into FalkorDB..." -ForegroundColor Yellow
& $python -m src.cli ingest ./src
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Codebase ingested!" -ForegroundColor Green
} else {
    Write-Host "  ❌ Ingestion failed" -ForegroundColor Red
    exit 1
}

# Run tests
Write-Host "`n[5/5] Running tests..." -ForegroundColor Yellow
& $python -m pytest tests/ -v --tb=short

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "   Start the server: python -m src.cli serve" -ForegroundColor Cyan
Write-Host "   Open dashboard:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Ask a question:   python -m src.cli ask 'What is the most critical module?'" -ForegroundColor Cyan
