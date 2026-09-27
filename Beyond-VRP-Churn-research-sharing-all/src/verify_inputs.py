from pathlib import Path
import datetime,hashlib,json,lzma
ROOT=Path(__file__).resolve().parents[1]
records=json.loads((ROOT/'data/daily-downloads.json').read_text())
assert len(records)==70 and not any('error' in r for r in records)
verified=[];timings={}
for r in records:
    p=ROOT/'data'/f"ripe-{r['date']}-{r['ta']}.json.xz";data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
    assert sha==r['sha256'] and sha in r['published_checksum']
    parsed=json.loads(lzma.decompress(data));t=datetime.datetime.fromtimestamp(parsed['metadata']['generated'],datetime.timezone.utc)
    assert t.date().isoformat()==r['date'] and len(parsed['roas'])==r['rows']
    timings.setdefault(r['date'],[]).append(t.timestamp())
    verified.append({'file':p.name,'sha256':sha,'rows':r['rows'],'generated_utc':t.isoformat()})
out={'verified':verified,'raw_rows':sum(r['rows'] for r in records),'within_date_spread_minutes':{d:(max(ts)-min(ts))/60 for d,ts in timings.items()}}
(ROOT/'results/input-verification.json').write_text(json.dumps(out,indent=2));print('Verified',len(verified),'raw rows',out['raw_rows'],'spread',min(out['within_date_spread_minutes'].values()),max(out['within_date_spread_minutes'].values()))
