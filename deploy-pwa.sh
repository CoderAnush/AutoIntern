#!/bin/bash

# AutoIntern PWA Deployment Script
# Deploys the Next.js PWA to your phone locally

set -e

echo "🚀 AutoIntern PWA Deployment Script"
echo "===================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$SCRIPT_DIR/services/web/apps/dashboard"

echo "📁 Frontend directory: $FRONTEND_DIR"
echo ""

# Check if node_modules exists
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd "$FRONTEND_DIR"
    npm install
    echo "✅ Dependencies installed"
    echo ""
fi

# Get machine IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
else
    # Windows (Git Bash)
    IP_ADDRESS=$(ipconfig | grep -i "ipv4" | head -1 | grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | head -1)
fi

echo "🌐 Your Machine IP: $IP_ADDRESS"
echo ""

# Create .env.local if it doesn't exist
if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
    echo "⚙️  Creating .env.local..."
    cat > "$FRONTEND_DIR/.env.local" << EOF
# PWA Configuration
NEXT_PUBLIC_API_URL=http://$IP_ADDRESS:8000
EOF
    echo "✅ .env.local created"
    echo ""
fi

# Display instructions
echo "📱 PHONE INSTALLATION INSTRUCTIONS"
echo "=================================="
echo ""
echo "1️⃣  Starting development server..."
cd "$FRONTEND_DIR"
echo ""
echo "2️⃣  On your phone, open a browser and go to:"
echo ""
echo "   🔗 http://$IP_ADDRESS:3000"
echo ""
echo "3️⃣  You should see the AutoIntern app"
echo ""
echo "4️⃣  To install as app:"
echo ""
echo "   📱 Android (Chrome):"
echo "      - Menu (⋮) → Install app"
echo "      - OR Look for Install App button"
echo ""
echo "   🍎 iPhone/iPad (Safari):"
echo "      - Tap Share (↗️)"
echo "      - Tap Add to Home Screen"
echo "      - Tap Add"
echo ""
echo "📝 NOTES:"
echo "  • Make sure phone is on same WiFi as computer"
echo "  • Both computer and phone must stay awake"
echo "  • Service worker takes 10 seconds to register"
echo "  • If install doesn't show, wait and refresh page"
echo ""
echo "🚀 Starting server now..."
echo ""

# Start the development server
npm run dev
