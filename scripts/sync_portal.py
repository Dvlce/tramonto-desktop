"""Vendor only public notebook sources, never user data, models or server secrets."""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CODE=['config.py','security.py','store.py','http_guard.py','tramonto.py','lab.py','network_catalog.py']
ASSETS=['tramonto.html','tramonto.css','tramonto.js','tramonto-lab.js','tramonto-font.js','tramonto-math.js','tramonto-study.js','tramonto-tools.js','portal-motion.js']
parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);args=parser.parse_args();source=args.source.resolve()
code=ROOT/'backend/source';assets=ROOT/'resources/portal';code.mkdir(parents=True,exist_ok=True);assets.mkdir(parents=True,exist_ok=True)
for name in CODE:shutil.copy2(source/name,code/name)
for name in ASSETS:shutil.copy2(source/name,assets/name)
shutil.copytree(source/'vendor',assets/'vendor',dirs_exist_ok=True)
# Desktop navigation only exposes the standalone notebook. Every route is local.
p=assets/'tramonto.html';html=p.read_text(encoding='utf-8');html=re.sub(r'<a\b[^>]*href="(?:/|/notte|/privacy|/cookies|/policy)[^"]*"[^>]*>.*?</a>','',html,flags=re.S);html=html.replace('sul server','su questo computer').replace('sul Raspberry','su questo computer');p.write_bytes(html.encode('utf-8'))
revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
manifest={'source':'https://github.com/Dvlce/alba-tramonto','revision':revision,'ai':False,'files':{}}
for base in [code,assets]:
 for item in sorted(base.rglob('*')):
  if item.is_file():manifest['files'][item.relative_to(ROOT).as_posix()]=hashlib.sha256(item.read_bytes()).hexdigest()
(ROOT/'portal-manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode('utf-8'))
print('Copied public notebook sources:',revision,'— no models or private data.')
