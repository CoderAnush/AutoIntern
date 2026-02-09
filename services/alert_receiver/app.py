from aiohttp import web
import asyncio

routes = web.RouteTableDef()

# Simple in-memory store of recent alerts (for smoke tests)
RECENT_ALERTS = []
MAX_RECENT = 50

@routes.get('/health')
async def health(request):
    return web.json_response({'status': 'ok'})

@routes.post('/')
async def handle_alert(request):
    data = await request.json()
    print('Alert received:', data)
    # Store a compact representation for inspection
    RECENT_ALERTS.insert(0, data)
    if len(RECENT_ALERTS) > MAX_RECENT:
        RECENT_ALERTS.pop()
    return web.json_response({'status': 'ok'})

@routes.get('/alerts')
async def list_alerts(request):
    count = int(request.query.get('count', '10'))
    return web.json_response({'count': len(RECENT_ALERTS), 'alerts': RECENT_ALERTS[:count]})

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5001)
