from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from aiohttp import web
from models import User, Advertisement, engine, Base, Session


async def app_context(app: web.Application):
    print('START')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print('SHUTDOWN')


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request['session'] = session
        response = await handler(request)
        return response


class AdvertisementView(web.View):

    @property
    def session(self) -> Session:
        return self.request['session']

    @property
    def advertisement_id(self) -> int:
        return int(self.request.match_info['advertisement_id'])

    async def get(self):
        advertisement = await self.session.get(Advertisement, self.advertisement_id)
        if advertisement is not None:
            return web.json_response({
                'id': advertisement.id,
                'title': advertisement.title,
                'description': advertisement.description,
                'owner': advertisement.owner,
                'creation_time': advertisement.creation_time.strftime("%Y-%m-%d %H:%M")
            })
        return web.json_response({'error': 'Advertisement not found'})

    async def post(self):
        data = await self.request.json()
        try:
            advertisement = Advertisement(**data)
            self.session.add(advertisement)
            try:
                await self.session.commit()
                return web.json_response({'message': 'Advertisement created successfully', 'id': advertisement.id})
            except IntegrityError:
                await self.session.rollback()
                return web.json_response({'message': 'Advertisement already exists'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def patch(self):
        advertisement = await self.session.get(Advertisement, self.advertisement_id)
        if advertisement is None:
            return web.json_response({'error': 'Advertisement not found'})
        data = await self.request.json()
        try:
            for field, value in data.items():
                if hasattr(advertisement, field):
                    setattr(advertisement, field, value)
            self.session.add(advertisement)
            await self.session.commit()
            return web.json_response({'message': 'Advertisement updated successfully', 'id': advertisement.id})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def delete(self):
        advertisement = await self.session.get(Advertisement, self.advertisement_id)
        if advertisement is None:
            return web.json_response({'error': 'Advertisement not found'})
        try:
            await self.session.delete(advertisement)
            await self.session.commit()
            return web.json_response({'message': 'Advertisement deleted successfully'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)


class UserView(web.View):

    @property
    def session(self) -> Session:
        return self.request['session']

    @property
    def user_id(self) -> int:
        return int(self.request.match_info['user_id'])

    async def get(self):
        user = await self.session.get(User, self.user_id)
        if user is not None:
            return web.json_response({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'creation_time': user.creation_time.strftime("%Y-%m-%d %H:%M")
            })
        return web.json_response({'error': 'User not found'})

    async def post(self):
        data = await self.request.json()
        try:
            user = User(**data)
            self.session.add(user)
            try:
                await self.session.commit()
                return web.json_response({'message': 'User created successfully', 'id': user.id})
            except IntegrityError:
                await self.session.rollback()
                return web.json_response({'message': 'User already exists'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def patch(self):
        user = await self.session.get(User, self.user_id)
        if user is None:
            return web.json_response({'error': 'User not found'})
        data = await self.request.json()

        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])
        try:
            for field, value in data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            self.session.add(user)
            await self.session.commit()
            return web.json_response({'message': 'User updated successfully', 'id': user.id})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def delete(self):
        user = await self.session.get(User, self.user_id)
        if user is None:
            return web.json_response({'error': 'User not found'})
        try:
            await self.session.delete(user)
            await self.session.commit()
            return web.json_response({'message': 'User deleted successfully'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)


async def create_app():
    app = web.Application()

    app.cleanup_ctx.append(app_context)
    app.middlewares.append(session_middleware)

    app.router.add_route('GET', '/advertisements/{advertisement_id}', AdvertisementView)
    app.router.add_route('POST', '/advertisements', AdvertisementView)
    app.router.add_route('PATCH', '/advertisements/{advertisement_id}', AdvertisementView)
    app.router.add_route('DELETE', '/advertisements/{advertisement_id}', AdvertisementView)

    app.router.add_route('POST', '/users', UserView)
    app.router.add_route('PATCH', '/users/{user_id}', UserView)
    app.router.add_route('DELETE', '/users/{user_id}', UserView)
    app.router.add_route('GET', '/users/{user_id}', UserView)

    return app


if __name__ == '__main__':
    web.run_app(create_app(), host='localhost', port=8080)
