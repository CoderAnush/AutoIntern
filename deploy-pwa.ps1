# AutoIntern PWA Deployment Script (Windows)
# Deploys the Next.js PWA to your phone locally

param(
    [switch]$Build = $false,
    [switch]$Production = $false
)

Write-Host "🚀 AutoIntern PWA Deployment Script (Windows)" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptDir "services\web\apps\dashboard"

Write-Host "📁 Frontend directory: $FrontendDir" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "$FrontendDir\node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    Set-Location $FrontendDir
    npm install
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Get machine IP address
Write-Host "🌐 Getting your machine IP address..." -ForegroundColor Cyan
$IPAddress = ((ipconfig | findstr /R /C:"IPv4 Address.*192\|IPv4 Address.*10\|IPv4 Address.*172") -split ':\s+')[1].Trim() | Select-Object -First 1

if (-not $IPAddress) {
    $IPAddress = "localhost"
    Write-Host "⚠️  Could not detect IP. Using 'localhost' for local testing." -ForegroundColor Yellow
} else {
    Write-Host "✅ Your Machine IP: $IPAddress" -ForegroundColor Green
}
Write-Host ""

# Create .env.local if it doesn't exist
$EnvLocalFile = Join-Path $FrontendDir ".env.local"
if (-not (Test-Path $EnvLocalFile)) {
    Write-Host "⚙️  Creating .env.local..." -ForegroundColor Yellow
    $EnvContent = @"
# PWA Configuration
NEXT_PUBLIC_API_URL=http://$IPAddress`:8000
"@
    Set-Content -Path $EnvLocalFile -Value $EnvContent
    Write-Host "✅ .env.local created" -ForegroundColor Green
    Write-Host ""
}

# Display instructions
Write-Host "📱 PHONE INSTALLATION INSTRUCTIONS" -ForegroundColor Green
Write-Host "=================================="
Write-Host ""
Write-Host "1️⃣  Starting development server..." -ForegroundColor Cyan
Write-Host ""

Set-Location $FrontendDir

# Build if requested
if ($Build) {
    Write-Host "🔨 Building for production..." -ForegroundColor Yellow
    npm run build
    Write-Host ""
}

Write-Host "2️⃣  On your phone, open a browser and go to:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   🔗 http://$IPAddress`:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "3️⃣  You should see the AutoIntern app" -ForegroundColor Cyan
Write-Host ""
Write-Host "4️⃣  To install as app:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   📱 Android (Chrome):" -ForegroundColor Cyan
Write-Host "      - Menu (⋮) → Install app" -ForegroundColor Gray
Write-Host "      - OR Look for 'Install App' button" -ForegroundColor Gray
Write-Host ""
Write-Host "   🍎 iPhone/iPad (Safari):" -ForegroundColor Cyan
Write-Host "      - Tap Share (↗️)" -ForegroundColor Gray
Write-Host "      - Tap 'Add to Home Screen'" -ForegroundColor Gray
Write-Host "      - Tap 'Add'" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 NOTES:" -ForegroundColor Yellow
Write-Host "  • Make sure phone is on same WiFi as computer" -ForegroundColor Gray
Write-Host "  • Both computer and phone must stay awake" -ForegroundColor Gray
Write-Host "  • Service worker takes ~10 seconds to register" -ForegroundColor Gray
Write-Host "  • If install doesn't show, wait and refresh page" -ForegroundColor Gray
Write-Host "  • For production: Run with -Production flag" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Starting server now..." -ForegroundColor Green
Write-Host ""

# Start the development server
if ($Production) {
    Write-Host "🏭 Running in production mode..." -ForegroundColor Yellow
    npm run build
    npm start
} else {
    npm run dev
}
