"""Fresh-machine smoke against the actual frozen executable; no system Python in the app."""
import json,os,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
exe=ROOT/'resources/backend'/('tramonto-backend.exe' if os.name=='nt' else 'tramonto-backend')
spice=ROOT/'resources/ngspice'/('ngspice.exe' if os.name=='nt' else 'ngspice')

def launch(data):
 process=subprocess.Popen([str(exe),'--data',str(data),'--assets',str(ROOT/'resources/portal'),'--ngspice',str(spice)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 record=json.loads(process.stdout.readline());origin='http://127.0.0.1:'+str(record['port'])
 return process,origin,record['session']
def request(origin,token,path,method='GET',data=None,csrf=None,expected=200):
 headers={'Cookie':'session='+token}
 if data is not None:headers['Content-Type']='application/json'
 if csrf:headers['X-CSRF-Token']=csrf
 req=urllib.request.Request(origin+path,headers=headers,method=method,data=None if data is None else json.dumps(data).encode())
 try:
  with urllib.request.urlopen(req,timeout=15) as response:
   assert response.status==expected,(path,response.status)
   return json.loads(response.read())
 except urllib.error.HTTPError as exc:
  assert exc.code==expected,(path,exc.code,exc.read().decode());return {}
with tempfile.TemporaryDirectory() as folder:
 data=Path(folder);process,origin,token=launch(data)
 try:
  assert request(origin,token,'/health')['ai'] is False
  me=request(origin,token,'/api/me');csrf=me['csrf'];request(origin,'','/api/tramonto/notebooks',expected=403)
  request(origin,token,'/api/notte/status',expected=404);request(origin,token,'/api/chat',expected=404)
  request(origin,token,'/api/tramonto/notebooks','POST',{'title':'Denied'},expected=403)
  book=request(origin,token,'/api/tramonto/notebooks','POST',{'title':'Offline notebook'},csrf,201)
  circuit={'components':[{'id':name,'type':kind,'label':name,'value':value,'x':x,'y':200,'rotation':0} for name,kind,value,x in [('V1','voltage','5V',100),('R1','resistor','1k',350),('G','ground','',100),('S','scope','',650)]], 'wires':[{'id':'w'+str(i),'from':{'component':a,'port':ap},'to':{'component':b,'port':bp}} for i,(a,ap,b,bp) in enumerate([('V1',1,'G',0),('R1',1,'G',0),('V1',0,'R1',0),('S',0,'V1',0),('S',1,'G',0)])]}
  note=request(origin,token,'/api/tramonto/notes','POST',{'notebook_id':book['id'],'title':'Persistence','subject':'generale','content':{'html':'<p>Small <span style="font-size: 32px;">large</span></p>','circuit':circuit}},csrf,201)
  detail=request(origin,token,'/api/tramonto/notes/'+str(note['id']));assert '32px' in detail['content']['html']
  job=request(origin,token,'/api/tramonto/simulations','POST',{'note_id':note['id'],'options':{'analysis':'tran','stop':.002,'samples':100}},csrf,202)
  for _ in range(50):
   state=request(origin,token,'/api/tramonto/simulations/'+job['job_id'])
   if state['done']:break
   time.sleep(.2)
  assert state['done'] and not state['result'].get('error'),state
  result=state['result'];assert len(result['x'])>50 and abs(result['series'][0]['values'][-1]-5)<.001,result
  note_id=note['id']
 finally:process.terminate();process.wait(timeout=10)
 process,origin,token=launch(data)
 try:
  persisted=request(origin,token,'/api/tramonto/notes/'+str(note_id));assert '32px' in persisted['content']['html'];assert len(persisted['content']['circuit']['wires'])==5
 finally:process.terminate();process.wait(timeout=10)
print('Frozen notebook OK: local authentication/CSRF, no AI routes, actual ngspice samples, offline notes retained after restart.')
