from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'results/cohort.json').read_text());assert len(d['pairs'])==13
out={'families':{},'witnesses_checked':sum(r['witnesses_checked'] for r in d['pairs']),'tuple_additions':sum(r['added'] for r in d['pairs']),'tuple_removals':sum(r['removed'] for r in d['pairs']),'parse_seconds_range':[min(r['parse_seconds'] for r in d['snapshots']),max(r['parse_seconds'] for r in d['snapshots'])],'analysis_seconds_range':[min(r['analysis_seconds'] for r in d['pairs']),max(r['analysis_seconds'] for r in d['pairs'])]}
for v,cap in [('4','24'),('6','48')]:
    ff=[r['families'][v] for r in d['pairs']];changed=sum(f['changed_origins'] for f in ff);noop=sum(f['A_unchanged_origins_full'] for f in ff)
    out['families'][v]={'changed_groups':changed,'unchanged_A_groups':noop,'unchanged_A_percent':100*noop/changed,'daily_noop_percent_range':[min(100*f['A_unchanged_origins_full']/f['changed_origins'] for f in ff),max(100*f['A_unchanged_origins_full']/f['changed_origins'] for f in ff)],'caps':{},'changed_origin_fraction_range':[min(f['changed_origins']/f['positive_origins_union'] for f in ff),max(f['changed_origins']/f['positive_origins_union'] for f in ff)]}
    for k in ff[0]['caps']:
        cc=[f['caps'][k] for f in ff];gain=sum(c['A_gain'] for c in cc);loss=sum(c['A_loss'] for c in cc)
        out['families'][v]['caps'][k]={'gain':gain,'loss':loss,'gross':gain+loss,'net':gain-loss,'sum_daily_absolute_net':sum(abs(c['A_net']) for c in cc),'daily_cancellation_range':[min(c['cancellation'] for c in cc),max(c['cancellation'] for c in cc)],'C_gain':sum(c['C_gain'] for c in cc),'C_loss':sum(c['C_loss'] for c in cc)}
out['benchmark']={}
b=json.loads((ROOT/'results/benchmark.json').read_text());assert len(b['repetitions'])==9
for pair in sorted({r['pair'] for r in b['repetitions']}):
    rr=[r for r in b['repetitions'] if r['pair']==pair];f=[r['full_seconds'] for r in rr];i=[r['incremental_seconds'] for r in rr]
    out['benchmark'][pair]={'full_median':statistics.median(f),'incremental_median':statistics.median(i),'ratio_of_medians':statistics.median(f)/statistics.median(i),'full_range':[min(f),max(f)],'incremental_range':[min(i),max(i)]}
(ROOT/'results/summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
