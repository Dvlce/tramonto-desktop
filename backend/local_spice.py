"""Bounded execution of generated circuits using the bundled native ngspice."""
import asyncio,json,math,os,subprocess,tempfile
from pathlib import Path

class DesktopSpice:
    executable=''
    def __init__(self,root):self.root=Path(root);self.lock=asyncio.Lock()
    @property
    def available(self):return Path(self.executable).is_file()
    async def run(self,prepared):
        if not self.available:raise ValueError('Il simulatore incluso nell’app non è disponibile.')
        async with self.lock:
            with tempfile.TemporaryDirectory(prefix='tramonto-circuit-') as folder:
                work=Path(folder);(work/'circuit.cir').write_text(prepared['netlist'],encoding='utf-8')
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                process=await asyncio.create_subprocess_exec(self.executable,'-n','-b','circuit.cir',cwd=folder,stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL,env={**os.environ,'SPICE_SCRIPTS':folder,'SPICE_LIB_DIR':folder,'LC_ALL':'C'},creationflags=creationflags)
                try:await asyncio.wait_for(process.wait(),10)
                except (asyncio.TimeoutError,asyncio.CancelledError):
                    if process.returncode is None:process.kill()
                    await process.wait();raise
                path=work/'result.dat'
                if not path.is_file() or path.stat().st_size>4*1024*1024:raise ValueError('Nessun risultato: verifica massa, alimentazione e collegamenti.')
                rows=[];traces=prepared['traces']
                with path.open() as source:
                    next(source,None)
                    for line in source:
                        if len(rows)>=100000:raise ValueError('Troppi campioni: riduci la durata.')
                        row=[float(v) for v in line.split()]
                        if len(row)!=len(traces)+1 or any(not math.isfinite(v) for v in row):raise ValueError('Risultati del circuito non validi.')
                        rows.append(row)
                if not rows:raise ValueError('Nessun campione ottenuto.')
                return {'engine':'ngspice','analysis':prepared['options']['analysis'],'x':[r[0] for r in rows],'series':[{**t,'values':[r[i+1] for r in rows]} for i,t in enumerate(traces)],'total_samples':len(rows),'display_samples':len(rows),'downsampled':False,'netlist':prepared['netlist'],'nodes':prepared['nodes']}
