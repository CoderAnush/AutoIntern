# PowerShell helper to start dev environment
$envFile = Join-Path $PSScriptRoot '..\.env'
if (-not (Test-Path $envFile)) {
    Copy-Item -Path "$PSScriptRoot\..\.env.example" -Destination $envFile
    Write-Host "Created .env from .env.example"
}

docker compose up --build -d
Write-Host "Docker compose started" 
