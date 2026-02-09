from aiohttp import web
import asyncio

routes = web.RouteTableDef()

@routes.post('/')
async def handle_alert(request):
    data = await request.json()
    print('Alert received:', data)
    return web.json_response({'status': 'ok'})

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5001)
