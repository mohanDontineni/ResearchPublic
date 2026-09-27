"""Post-analysis illustration: lowest IPv4 ASN with zero A delta in first pair."""
from pathlib import Path
import json
from semantic import *
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'results/cohort.json').read_text());f=d['pairs'][0]['families']['4']
asn=min(o['asn'] for o in f['origins'] if not any(o['gains']) and not any(o['losses']))
old=read(ROOT/'data/ripe-2026-09-01.json');new=read(ROOT/'data/ripe-2026-09-02.json')
a={r for r in old if r[0]==4 and r[1]==asn};b={r for r in new if r[0]==4 and r[1]==asn}
def show(r):
    v,asn,n,p,m=r
    return {'prefix':prefix(v,n>>(BITS[v]-p),p),'asn':asn,'maxLength':m}
out={'selection':'Post-analysis illustration, lowest IPv4 ASN with full-width A equality in first cohort pair; not a prespecified outcome','asn':asn,'old_tuples':len(a),'new_tuples':len(b),'added':[show(r) for r in sorted(b-a)],'removed':[show(r) for r in sorted(a-b)],'unchanged_context':[show(r) for r in sorted(a&b)],'A_equal_full':True,'global_C_equal_for_origin_edit':not any(sum(z['gains'])+sum(z['losses']) for z in diff_coverage(old,(old-a)|b,False).values())}
(ROOT/'results/illustrative-case.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
