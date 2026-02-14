#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AutoIntern Complete Startup Script for E2E Testing
    Starts all services: PostgreSQL, Redis, Backend API, Frontend

.DESCRIPTION
    This script will:
    1. Start PostgreSQL (if using Docker)
    2. Start Redis
    3. Create test users
    4. Start backend API
    5. Start frontend development server
    
    All services will run in parallel. Use Ctrl+C to stop all services.

.NOTES
    Prerequisites:
    - Docker installed and running
    - Node.js 18+ installed
    - Python 3.10+ installed
    - Git installed

.EXAMPLE
    PS> .\start-all-services.ps1
#>

param(
    [switch]$SkipDocker = $false,
    [switch]$SkipBackend = $false,
    [switch]$SkipFrontend = $false
)

$ErrorActionPreference = "Continue"

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           AutoIntern Complete Service Startup                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

$prerequisites = @{
    "docker" = "docker --version";
    "node" = "node --version";
    "python" = "python --version";
    "git" = "git --version"
}

$missing = @()
foreach ($tool in $prerequisites.Keys) {
    try {
        Invoke-Expression $prerequisites[$tool] | Out-Null
        Write-Host "  ✓ $tool is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ $tool is NOT installed" -ForegroundColor Red
        $missing += $tool
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Please install them before running this script." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
$projectRoot = Get-Location
Write-Host "📂 Project Root: $projectRoot" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. START DOCKER SERVICES
# ============================================================================
if (-not $SkipDocker) {
    Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Blue
    Write-Host "│ 1️⃣  Starting Docker Services (PostgreSQL, Redis)              │" -ForegroundColor Blue
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Blue
    Write-Host ""
    
    # Check if Docker is running
    try {
        docker ps | Out-Null
    }
    catch {
        Write-Host "❌ Docker daemon is not running!" -ForegroundColor Red
        Write-Host "   Please start Docker Desktop and run this script again." -ForegroundColor Yellow
        exit 1
    }
    
    # Check existing containers
    $postgresExists = docker ps -a --filter "name=autointern-postgres" --quiet
    $redisExists = docker ps -a --filter "name=autointern-redis" --quiet
    
    # Start PostgreSQL
    if ([string]::IsNullOrEmpty($postgresExists)) {
        Write-Host "🐘 Creating PostgreSQL container..." -ForegroundColor Cyan
        docker run -d `
            --name autointern-postgres `
            -e POSTGRES_USER=autointern `
            -e POSTGRES_PASSWORD=change-me `
            -e POSTGRES_DB=autointern `
            -p 5432:5432 `
            postgres:15 | Out-Null
    }
    else {
        $postgresRunning = docker ps --filter "name=autointern-postgres" --quiet
        if ([string]::IsNullOrEmpty($postgresRunning)) {
            Write-Host "🔄 Starting existing PostgreSQL container..." -ForegroundColor Cyan
            docker start autointern-postgres | Out-Null
        }
        else {
            Write-Host "✓ PostgreSQL container already running" -ForegroundColor Green
        }
    }
    
    # Start Redis
    if ([string]::IsNullOrEmpty($redisExists)) {
        Write-Host "🔴 Creating Redis container..." -ForegroundColor Cyan
        docker run -d `
            --name autointern-redis `
            -p 6379:6379 `
            redis:7 | Out-Null
    }
    else {
        $redisRunning = docker ps --filter "name=autointern-redis" --quiet
        if ([string]::IsNullOrEmpty($redisRunning)) {
            Write-Host "🔄 Starting existing Redis container..." -ForegroundColor Cyan
            docker start autointern-redis | Out-Null
        }
        else {
            Write-Host "✓ Redis container already running" -ForegroundColor Green
        }
    }
    
    Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host "✓ Docker services ready!" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# 2. SEED TEST USERS
# ============================================================================
Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Blue
Write-Host "│ 2️⃣  Seeding Test Users                                        │" -ForegroundColor Blue
Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Blue
Write-Host ""

Push-Location "services/api"

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Write-Host "⚠️  requirements.txt not found!" -ForegroundColor Red
    Write-Host "   This script must be run from the project root." -ForegroundColor Yellow
    Pop-Location
    exit 1
}

# Install Python dependencies silently
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt 2>$null

# Run seeder
Write-Host "🌱 Running test user seeder..." -ForegroundColor Cyan
python seed_test_users.py
Write-Host ""

Pop-Location

# ============================================================================
# 3. START BACKEND API
# ============================================================================
if (-not $SkipBackend) {
    Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Blue
    Write-Host "│ 3️⃣  Starting Backend API (uvicorn)                            │" -ForegroundColor Blue
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Blue
    Write-Host ""
    
    Push-Location "services/api"
    
    Write-Host "🚀 Starting FastAPI server on http://localhost:8000..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C in this window to stop the backend" -ForegroundColor Yellow
    Write-Host "   (Other services will continue running)" -ForegroundColor DarkGray
    Write-Host ""
    
    # Start backend in a separate window
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectRoot/services/api'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`""
    
    Pop-Location
    
    Start-Sleep -Seconds 2
}

# ============================================================================
# 4. START FRONTEND
# ============================================================================
if (-not $SkipFrontend) {
    Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Blue
    Write-Host "│ 4️⃣  Starting Frontend (Next.js)                              │" -ForegroundColor Blue
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Blue
    Write-Host ""
    
    Push-Location "services/web/apps/dashboard"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing Node dependencies..." -ForegroundColor Cyan
        npm install --legacy-peer-deps
    }
    
    Write-Host "🚀 Starting Next.js dev server on http://localhost:3000..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C in this window to stop the frontend" -ForegroundColor Yellow
    Write-Host "   (Other services will continue running)" -ForegroundColor DarkGray
    Write-Host ""
    
    # Start frontend in current terminal
    npm run dev
    
    Pop-Location
}

# ============================================================================
# FINAL INSTRUCTIONS
# ============================================================================
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                   🎉 Services Started!                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📋 TEST CREDENTIALS:" -ForegroundColor Cyan
Write-Host "   Email:    test@example.com" -ForegroundColor White
Write-Host "   Password: TestPass123!" -ForegroundColor White
Write-Host ""

Write-Host "🌐 URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

Write-Host "🧪 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "   2. Click 'Sign In'" -ForegroundColor White
Write-Host "   3. Enter: test@example.com / TestPass123!" -ForegroundColor White
Write-Host "   4. You should be logged in to the dashboard" -ForegroundColor White
Write-Host ""

Write-Host "🧬 RUN E2E TESTS:" -ForegroundColor Cyan
Write-Host "   cd services/web/apps/dashboard" -ForegroundColor White
Write-Host "   npx playwright test" -ForegroundColor White
Write-Host "   (or: npx playwright test --ui)" -ForegroundColor White
Write-Host ""

Write-Host "📚 FULL GUIDE:" -ForegroundColor Cyan
Write-Host "   See E2E_TESTING_COMPLETE_GUIDE.md" -ForegroundColor White
Write-Host ""

Write-Host "❌ TO STOP ALL SERVICES:" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C in each window" -ForegroundColor White
Write-Host "   Then run: docker-compose down" -ForegroundColor White
Write-Host ""
