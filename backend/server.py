"""Standalone notebook server. No AI services, model dependencies or AI routes."""
import argparse,asyncio,json,os,secrets,sqlite3,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from aiohttp import web
SOURCE=Path(__file__).resolve().parent/'source'
sys.path.insert(0,str(SOURCE))
from config import Settings
from security import Keys,secret_file
from store import Store
from http_guard import HTTPGuard
import lab
from tramonto import setup_tramonto
from local_spice import DesktopSpice
lab.Spice=DesktopSpice

async def start(data_root,assets,spice):
    data_root.mkdir(parents=True,exist_ok=True)
    settings=Settings(root=assets,admins=(1,))
    store=Store(data_root/'notebook.sqlite3');store.register(1,'Quaderno locale');store.authorize(1)
    keys=Keys(store,secret_file(data_root/'auth.key'));keys.is_admin=lambda uid:uid==1
    DesktopSpice.executable=spice
    service=SimpleNamespace(store=store,keys=keys,settings=settings,is_admin=lambda uid:uid==1,spice_jobs={})
    guard=HTTPGuard(keys,'');expected_host=None
    @web.middleware
    async def protection(request,handler):
        if request.host!=expected_host:return web.Response(status=403,text='Invalid local host')
        admitted=guard.enter()
        try:
            if not admitted:raise web.HTTPTooManyRequests()
            if request.path!='/health':
                request['identity']=keys.identify(request.cookies.get('session',''))
                if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),request['identity']['csrf']):raise PermissionError()
            await guard.check(request)
            response=await handler(request)
        except web.HTTPException as exc:response=exc
        except PermissionError:response=web.json_response({'error':'Local session expired','code':'auth_expired'},status=403)
        except (ValueError,KeyError,json.JSONDecodeError) as exc:response=web.json_response({'error':str(exc) or 'Invalid request'},status=400)
        finally:
            if admitted:guard.leave()
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' blob: data:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"})
        return response
    app=web.Application(middlewares=[protection],client_max_size=10*1024*1024)
    async def health(_):return web.json_response({'ready':True,'product':'tramonto-notebook','ai':False})
    async def me(request):return web.json_response({'user_id':1,'is_admin':True,'name':'Quaderno locale','csrf':request['identity']['csrf'],'telegram_linked':False})
    async def home(_):return web.HTTPFound('/tramonto')
    async def motion(_):return web.FileResponse(assets/'portal-motion.js')
    async def backup(_):
        path=data_root/'desktop-backup.sqlite3'
        with sqlite3.connect(path) as destination:store.db.backup(destination)
        return web.FileResponse(path,headers={'Content-Disposition':'attachment; filename="Tramonto-backup.sqlite3"'})
    app.add_routes([web.get('/',home),web.get('/health',health),web.get('/api/me',me),web.get('/assets/portal-motion.js',motion),web.get('/api/desktop/backup',backup)])
    setup_tramonto(app,service)
    runner=web.AppRunner(app,access_log=None);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1];expected_host='127.0.0.1:'+str(port)
    session,_=keys.create_session(1,remember=True,label='Tramonto desktop')
    # One private bootstrap record to the parent process; never persisted to logs.
    print(json.dumps({'port':port,'session':session}),flush=True)
    try:await asyncio.Event().wait()
    finally:await runner.cleanup();store.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True,type=Path);parser.add_argument('--assets',required=True,type=Path);parser.add_argument('--ngspice',required=True);args=parser.parse_args()
    try:asyncio.run(start(args.data.resolve(),args.assets.resolve(),args.ngspice))
    except KeyboardInterrupt:pass
