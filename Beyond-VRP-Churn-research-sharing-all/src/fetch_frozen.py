"""Acquire the exact study inputs from the distributable manifest, then assemble days."""
from pathlib import Path
import hashlib,json,lzma,urllib.request
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/input-manifest.json').read_text())
(ROOT/'data').mkdir(exist_ok=True)
for r in manifest:
    path=ROOT/'data'/r['file']
    if path.exists():data=path.read_bytes()
    else:data=urllib.request.urlopen(r['url'],timeout=120).read()
    if hashlib.sha256(data).hexdigest()!=r['sha256']:raise RuntimeError('Frozen hash mismatch: '+r['file'])
    if not path.exists():path.write_bytes(data)
    print('Verified',path.name,flush=True)
for day in range(1,15):
    date=f'2026-09-{day:02}';roas=[]
    for ta in ['afrinic','apnic','arin','lacnic','ripencc']:
        roas.extend(json.loads(lzma.decompress((ROOT/'data'/f'ripe-{date}-{ta}.json.xz').read_bytes()))['roas'])
    output=ROOT/'data'/f'ripe-{date}.json'
    data=json.dumps({'metadata':{'archive_date':date,'assembled_from':['afrinic','apnic','arin','lacnic','ripencc'],'assembly':'concatenation; canonical deduplication performed by analyze.py'},'roas':roas},separators=(',',':')).encode()
    if output.exists():assert output.read_bytes()==data
    else:output.write_bytes(data)
