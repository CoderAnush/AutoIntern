#!/bin/bash

# AutoIntern Complete System Start Script

echo "🚀 AutoIntern Complete System Startup"
echo "======================================"
echo ""

# Check if services are running
echo "⏸️  Checking for existing services..."

# Kill existing services gracefully
for port in 3000 3001 8000; do
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    echo "✓ Port $port cleared"
done

sleep 2

# Start backend
echo ""
echo "🔧 Starting Backend API..."
cd "c:\Users\anush\Desktop\AutoIntern\AutoIntern" || exit
source "services\api\venv\Scripts\activate" 2>/dev/null || python -m venv services/api/venv
source "services\api\venv\Scripts\activate" 2>/dev/null
pip install -q fastapi uvicorn requests 2>/dev/null || true

python mock_api.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID) on http://localhost:8000"

sleep 3

# Verify backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed"
fi

# Start frontend
echo ""
echo "🎨 Starting Frontend..."
cd "services/web/apps/dashboard" || exit

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install -q
fi

# Check if we should build
if [ ! -d "build" ]; then
    echo "🔨 Building frontend..."
    npm run build > build.log 2>&1
fi

serve -s build -l 3001 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID) on http://localhost:3001"

sleep 3

echo ""
echo "======================================"
echo "✅ AutoIntern System Ready!"
echo "======================================"
echo ""
echo "🌐 Access Points:"
echo "   Frontend:  http://localhost:3001"
echo "   Backend:   http://localhost:8000"
echo "   API Health: http://localhost:8000/health"
echo ""
echo "📝 Test Credentials:"
echo "   Email: test@example.com"
echo "   Password: TestPass123!"
echo ""
echo "💡 Tip: Open http://localhost:3001 in your browser"
echo ""
echo "🛑 To stop services, press Ctrl+C"
echo "   Or kill manually with: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Keep script running
wait
