'use strict';
const {app,BrowserWindow,Menu,session,dialog,shell,net}=require('electron');
const {spawn}=require('node:child_process');const path=require('node:path');const fs=require('node:fs');
let backend,win,origin,closing=false,quitting=false;
const releaseURL='https://github.com/Dvlce/tramonto-desktop/releases';
if(process.env.TRAMONTO_TEST_DATA)app.setPath('userData',path.resolve(process.env.TRAMONTO_TEST_DATA));
if(!app.requestSingleInstanceLock()){app.quit();}else{
app.on('second-instance',()=>{if(win){if(win.isMinimized())win.restore();win.show();win.focus();}});
app.whenReady().then(launch).catch(()=>{dialog.showErrorBox('Tramonto','Impossibile avviare il quaderno locale. Reinstalla la stessa versione; i tuoi dati restano nella cartella dell’app.');app.quit();});
app.on('activate',()=>{if(win)win.show();});
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',()=>{quitting=true;});app.on('will-quit',()=>{backend?.kill();});
}
async function launch(){
 const resources=app.isPackaged?process.resourcesPath:path.join(__dirname,'resources');
 const executable=path.join(resources,'backend',process.platform==='win32'?'tramonto-backend.exe':'tramonto-backend');
 const spice=path.join(resources,'ngspice',process.platform==='win32'?'ngspice.exe':'ngspice');
 const assets=path.join(resources,'portal'),data=path.join(app.getPath('userData'),'notebook');fs.mkdirSync(data,{recursive:true,mode:0o700});
 backend=spawn(executable,['--data',data,'--assets',assets,'--ngspice',spice],{windowsHide:true,stdio:['ignore','pipe','pipe']});
 const ready=await new Promise((resolve,reject)=>{let buffer='';const timer=setTimeout(()=>{backend.kill();reject(new Error('Startup timeout'));},45000);backend.once('error',e=>{clearTimeout(timer);reject(e);});backend.once('exit',()=>{clearTimeout(timer);reject(new Error('Backend exited'));});backend.stdout.on('data',chunk=>{buffer+=chunk.toString();if(buffer.length>2048){clearTimeout(timer);reject(new Error('Invalid bootstrap'));return;}if(buffer.includes('\n')){clearTimeout(timer);try{resolve(JSON.parse(buffer.split('\n')[0]));}catch(e){reject(e);}buffer='';backend.stdout.removeAllListeners('data');}});backend.stderr.on('data',()=>{});});
 if(!Number.isInteger(ready.port)||ready.port<1||ready.port>65535||typeof ready.session!=='string')throw new Error('Invalid bootstrap');
 origin='http://127.0.0.1:'+ready.port;const localSession=session.fromPartition('tramonto-local');
 await localSession.cookies.set({url:origin,name:'session',value:ready.session,httpOnly:true,sameSite:'strict',path:'/'});ready.session='';
 localSession.setPermissionRequestHandler((_contents,_permission,callback)=>callback(false));
 localSession.on('will-download',(_event,item)=>item.setSaveDialogOptions({defaultPath:path.join(app.getPath('downloads'),item.getFilename())}));
 win=new BrowserWindow({width:1440,height:940,minWidth:720,minHeight:520,title:'Tramonto · Quaderno locale',backgroundColor:'#f4f5ee',show:false,webPreferences:{session:localSession,contextIsolation:true,sandbox:true,nodeIntegration:false,webSecurity:true}});
 win.webContents.setWindowOpenHandler(()=>({action:'deny'}));win.webContents.on('will-navigate',(event,url)=>{if(new URL(url).origin!==origin)event.preventDefault();});
 win.webContents.on('will-prevent-unload',async event=>{if(await save())event.preventDefault();});
 win.on('close',event=>{if(closing)return;event.preventDefault();closeSafely();});win.once('ready-to-show',()=>win.show());
 backend.on('exit',()=>{if(!closing&&!quitting){dialog.showErrorBox('Tramonto','Il servizio del quaderno si è arrestato. Chiudi e riapri l’app.');win?.webContents.stop();}});
 Menu.setApplicationMenu(Menu.buildFromTemplate([
 ...(process.platform==='darwin'?[{label:'Tramonto',submenu:[{role:'about'},{type:'separator'},{role:'quit'}]}]:[]),
 {label:'Quaderno',submenu:[{label:'Salva pagina',accelerator:'CmdOrCtrl+S',click:save},{label:'Stampa / PDF',accelerator:'CmdOrCtrl+P',click:()=>win.webContents.executeJavaScript('TramontoWorkspace.showPrint()')},{label:'Esporta PDF della pagina',click:pdf},{type:'separator'},{label:'Backup di tutti i quaderni',click:()=>win.webContents.downloadURL(origin+'/api/desktop/backup')},{label:'Apri cartella dei dati',click:()=>shell.openPath(data)},{type:'separator'},{label:'Controlla aggiornamenti',click:checkUpdates},{role:'close'}]},
 {label:'Modifica',submenu:[{role:'undo'},{role:'redo'},{type:'separator'},{role:'cut'},{role:'copy'},{role:'paste'},{role:'selectAll'}]},
 {label:'Vista',submenu:[{role:'resetZoom'},{role:'zoomIn'},{role:'zoomOut'},{type:'separator'},{role:'togglefullscreen'}]}
 ]));
 await win.loadURL(origin+'/tramonto');
 if(process.env.TRAMONTO_SMOKE){await win.webContents.executeJavaScript('new Promise(resolve=>{const timer=setInterval(()=>{if(window.TramontoLab&&document.querySelector("#newNote")){clearInterval(timer);resolve(true);}},50)})');}
}
async function save(){try{return await win.webContents.executeJavaScript('typeof TramontoTools!=="undefined" ? TramontoTools.saveDoc() : true');}catch{return false;}}
async function closeSafely(){if(closing)return;if(!await save()){const choice=await dialog.showMessageBox(win,{type:'warning',message:'La pagina non è stata salvata.',detail:'Rimani nel quaderno per riprovare oppure chiudi perdendo le ultime modifiche.',buttons:['Rimani nel quaderno','Chiudi senza salvare'],defaultId:0,cancelId:0});if(choice.response===0)return;}closing=true;win.destroy();app.quit();}
async function pdf(){if(!await save())return;const file=await dialog.showSaveDialog(win,{defaultPath:'Tramonto.pdf',filters:[{name:'PDF',extensions:['pdf']}]});if(file.canceled)return;try{if(!await win.webContents.executeJavaScript('TramontoWorkspace.preparePrint()'))return;const bytes=await win.webContents.printToPDF({pageSize:'A4',printBackground:true,preferCSSPageSize:true});fs.writeFileSync(file.filePath,bytes);}finally{await win.webContents.executeJavaScript('TramontoWorkspace.cleanupPrint()');}}
async function checkUpdates(){try{const response=await net.fetch('https://api.github.com/repos/Dvlce/tramonto-desktop/releases/latest',{headers:{Accept:'application/vnd.github+json'}});if(!response.ok)throw new Error();const release=await response.json();const answer=await dialog.showMessageBox(win,{message:'Versione installata: '+app.getVersion(),detail:'Ultima release: '+release.tag_name+'\nI quaderni locali vengono conservati quando installi un aggiornamento.',buttons:['Apri download','Chiudi'],cancelId:1});if(answer.response===0)await shell.openExternal(releaseURL);}catch{dialog.showErrorBox('Tramonto','Non è stato possibile controllare gli aggiornamenti. I quaderni rimangono utilizzabili offline.');}}
