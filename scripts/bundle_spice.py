"""Copy ngspice and native libraries so users need no separate installation."""
import argparse,os,re,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('binary',type=Path);args=p.parse_args();binary=args.binary.resolve();target=Path(__file__).resolve().parents[1]/'resources/ngspice';target.mkdir(parents=True,exist_ok=True)
if os.name=='nt':
 for f in binary.parent.iterdir():
  if f.suffix.lower() in ('.exe','.dll'):shutil.copy2(f,target/f.name)
else:
 destination=target/'ngspice';shutil.copy2(binary,destination);destination.chmod(0o755)
 if __import__('sys').platform=='darwin':
  pending=[(binary,destination)];copied={binary}
  while pending:
   original,local=pending.pop();dependencies=subprocess.check_output(['otool','-L',str(original)],text=True).splitlines()[1:]
   subprocess.run(['chmod','u+w',str(local)],check=True)
   for row in dependencies:
    dependency=Path(row.strip().split(' (')[0])
    if str(dependency).startswith(('/usr/lib/','/System/')):continue
    if not dependency.is_absolute():raise RuntimeError('Unresolved ngspice library: '+str(dependency))
    resolved=dependency.resolve();new=target/dependency.name
    if resolved not in copied:shutil.copy2(resolved,new);copied.add(resolved);pending.append((resolved,new))
    subprocess.run(['install_name_tool','-change',str(dependency),'@loader_path/'+new.name,str(local)],check=True)
   if local.suffix=='.dylib':subprocess.run(['install_name_tool','-id','@loader_path/'+local.name,str(local)],check=True)
   subprocess.run(['codesign','--force','--sign','-',str(local)],check=True,stdout=subprocess.DEVNULL)
print('Bundled native ngspice:',target)
