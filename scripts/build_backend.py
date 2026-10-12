import shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--name','tramonto-backend','--paths',str(root/'backend/source'),'--distpath',str(root/'build/frozen'),'--workpath',str(root/'build/pyinstaller'),'--specpath',str(root/'build'),str(root/'backend/server.py')],check=True)
target=root/'resources/backend';shutil.rmtree(target,ignore_errors=True);shutil.copytree(root/'build/frozen/tramonto-backend',target)
