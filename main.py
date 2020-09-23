import asyncio
from aiohttp import web, WSMsgType


async def create_app():
    app = web.Application()
    app.wsnotification = {}
    app.router.add_route('POST', '/send-notification/',
                         SendNotification, name='send_notification')
    app.router.add_route(
        'GET', '/ws_notification/{user}', PushNotification, name='notification')
    app.on_cleanup.append(on_shutdown)
    return app


async def on_shutdown(app):
    await app.shutdown()


class SendNotification(web.View):

    async def post(self):
        app = self.request.app
        data = await self.request.post()
        user = data.get('user')
        from_user = data.get('author')
        title = data.get('title')
        message = data.get('message')
        response = {'text': message, 'title': title, 'from_user': from_user}
        ws = app.wsnotification.get(user)
        if ws is not None:
            await ws.send_json(response)
            text = 'ok'
        else:
            text = 'bad'
        return web.Response(status=200, text=text)


class PushNotification(web.View):

    async def get(self):
        app = self.request.app
        self.user = self.request.match_info['user']

        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        app.wsnotification[self.user] = ws

        async for msg in ws:
            if msg.type == WSMsgType.text:
                if msg.data == 'close':
                    await ws.close()

            elif msg.type == WSMsgType.error:
                print(f'Ошибка {ws.exception()}')

        await self.disconnect(ws)
        return ws

    async def disconnect(self, socket, silent=False):
        """ Закрываем соединение и отправлем сообщение о выходе. """
        app = self.request.app
        app.wsnotification.pop(self.user, None)
        if not socket.closed:
            await socket.close()
        if silent:
            return
