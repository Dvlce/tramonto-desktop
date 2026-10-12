"""Build the pinned macOS simulator without X11, readline or extra runtimes."""
import hashlib,os,shutil,subprocess,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://downloads.sourceforge.net/project/ngspice/ng-spice-rework/47/ngspice-47.tar.gz'
DIGEST='894e649651f1838a14095e5a5439e7d3aa63e87ede14d283173fda4fcdef675f'
work=ROOT/'build/spice-source';work.mkdir(parents=True,exist_ok=True);archive=work/'ngspice-47.tar.gz'
if not archive.exists():
 with urllib.request.urlopen(URL,timeout=90) as response:archive.write_bytes(response.read())
if hashlib.sha256(archive.read_bytes()).hexdigest()!=DIGEST:raise ValueError('ngspice source checksum mismatch')
with tarfile.open(archive) as package:
 for member in package.getmembers():
  if not (work/member.name).resolve().is_relative_to(work.resolve()) or member.issym() or member.islnk():raise ValueError('Unsafe ngspice archive')
 package.extractall(work)
source=work/'ngspice-47'
subprocess.run(['./configure','--with-x=no','--with-readline=no','--disable-xspice','--disable-cider','--disable-openmp'],cwd=source,check=True)
subprocess.run(['make','-j'+str(min(8,os.cpu_count() or 2))],cwd=source,check=True)
shutil.rmtree(ROOT/'resources/ngspice',ignore_errors=True)
subprocess.run([__import__('sys').executable,str(ROOT/'scripts/bundle_spice.py'),str(source/'src/ngspice')],check=True)
