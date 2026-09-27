from pathlib import Path
from collections import Counter
import gzip,hashlib,json,time
from semantic import *
ROOT=Path(__file__).resolve().parents[1]
t=time.perf_counter();old=read(ROOT/'data/ripe-2026-09-13.json');new=read(ROOT/'data/ripe-2026-09-14.json')
a,b=Validator(old),Validator(new)
report={'design':'Fixed 2026-09-14 route pairs evaluated under Sep13 and Sep14 RPKI views; not observed BGP transitions','families':{}}
changed=[]
for v,name in [(4,'routeviews-rv2-20260914-2000.pfx2as.gz'),(6,'routeviews-rv6-20260914-1200.pfx2as.gz')]:
    path=ROOT/'data'/name;matrix=Counter();excluded=Counter();seen=set();lines=0
    with gzip.open(path,'rt') as f:
        for line in f:
            lines+=1;address,length,origin=line.strip().split()
            if not origin.isdecimal():excluded['multi_origin_or_as_set']+=1;continue
            asn=int(origin)
            if not 0<asn<2**32:excluded['invalid_or_zero_asn']+=1;continue
            n=ipaddress.ip_network(address+'/'+length,strict=True)
            assert n.version==v
            key=str(n),asn
            if key in seen:excluded['duplicate']+=1;continue
            seen.add(key);x,y=a.classify(*key),b.classify(*key);matrix[x+'->'+y]+=1
            if x!=y:changed.append({'prefix':key[0],'asn':asn,'before':x,'after':y})
    report['families'][str(v)]={'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'lines':lines,'included_unique_pairs':len(seen),'excluded':dict(excluded),'matrix':dict(matrix),'changed':sum(n for k,n in matrix.items() if k.split('->')[0]!=k.split('->')[1])}
    print(v,report['families'][str(v)],flush=True)
report['seconds']=time.perf_counter()-t
(ROOT/'results/route-projection.json').write_text(json.dumps(report,indent=2))
(ROOT/'results/route-transitions.json').write_text(json.dumps(changed,indent=2))
