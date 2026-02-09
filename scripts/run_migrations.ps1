# Run Alembic migrations for services/api
Push-Location (Join-Path $PSScriptRoot '..\services\api')
alembic -c alembic.ini upgrade head
Pop-Location
