# Script for updating Poetry dependencies
Write-Host "Updating poetry.lock..." -ForegroundColor Green

# Update lock file
poetry lock

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstalling dependencies..." -ForegroundColor Green
    poetry install --no-interaction
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nDependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nError installing dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`nError updating poetry.lock" -ForegroundColor Red
    Write-Host "Try running commands manually:" -ForegroundColor Yellow
    Write-Host "  poetry lock" -ForegroundColor Yellow
    Write-Host "  poetry install --no-interaction" -ForegroundColor Yellow
    exit 1
}
