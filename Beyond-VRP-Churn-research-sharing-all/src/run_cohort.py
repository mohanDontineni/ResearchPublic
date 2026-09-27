from pathlib import Path
import csv,datetime,hashlib,json,platform,resource,time
from semantic import *
ROOT=Path(__file__).resolve().parents[1]

def analyze_pair(old,new,label):
    started=time.perf_counter()
    auth=diff_authorizations(group(old),group(new));cov=diff_coverage(old,new)
    witnesses=verify_witnesses(auth,cov,old,new)
    (ROOT/'results'/f'witnesses-{label}.json').write_text(json.dumps(witnesses,indent=2))
    report={'pair':label,'old_unique':len(old),'new_unique':len(new),'added':len(new-old),'removed':len(old-new),'witnesses_checked':len(witnesses),'families':{}}
    for v in BITS:
        a=auth[str(v)];c=cov[str(v)];origins=a['origins']
        f={'tuple_added':sum(r[0]==v for r in new-old),'tuple_removed':sum(r[0]==v for r in old-new),'positive_origins_union':len({r[1] for r in old|new if r[0]==v and r[1]}),'changed_origins':len(origins),'A_unchanged_origins_full':sum(not any(o['gains']) and not any(o['losses']) for o in origins),'A_gains_by_length':a['gains'],'A_losses_by_length':a['losses'],'C_gains_by_length':c['gains'],'C_losses_by_length':c['losses'],'caps':{},'origins':origins}
        for cap in CAPS[v]:
            gain=sum(a['gains'][:cap+1]);loss=sum(a['losses'][:cap+1]);cg=sum(c['gains'][:cap+1]);cl=sum(c['losses'][:cap+1])
            f['caps'][str(cap)]={'A_gain':gain,'A_loss':loss,'A_net':gain-loss,'A_gross':gain+loss,'cancellation':1-abs(gain-loss)/(gain+loss) if gain+loss else None,'cancellation_fraction_numerator':gain+loss-abs(gain-loss),'cancellation_fraction_denominator':gain+loss,'C_gain':cg,'C_loss':cl,'A_unchanged_origins':sum(not any(o['gains'][:cap+1]) and not any(o['losses'][:cap+1]) for o in origins)}
        report['families'][str(v)]=f
    report['analysis_seconds']=time.perf_counter()-started
    report['peak_process_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return report

if __name__=='__main__':
    dates=[f'2026-09-{d:02}' for d in range(1,15)]
    report={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'platform':platform.platform(),'snapshots':[],'pairs':[]}
    old=None
    for date in dates:
        start=time.perf_counter();path=ROOT/'data'/f'ripe-{date}.json';new=read(path)
        report['snapshots'].append({'date':date,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'unique':len(new),'parse_seconds':time.perf_counter()-start})
        if old is not None:
            label=previous+'_'+date;r=analyze_pair(old,new,label);report['pairs'].append(r)
            (ROOT/'results/cohort.json').write_text(json.dumps(report,indent=2))
            print(label,r['added'],r['removed'],r['witnesses_checked'],round(r['analysis_seconds'],2),flush=True)
        old=new;previous=date
    with (ROOT/'results/cohort.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['pair','family','cap','tuple_added','tuple_removed','changed_origins','A_unchanged_origins_full','A_gain','A_loss','A_net','cancellation','C_gain','C_loss'])
        for r in report['pairs']:
            for v,fam in r['families'].items():
                for cap,c in fam['caps'].items():w.writerow([r['pair'],v,cap,fam['tuple_added'],fam['tuple_removed'],fam['changed_origins'],fam['A_unchanged_origins_full'],c['A_gain'],c['A_loss'],c['A_net'],c['cancellation'],c['C_gain'],c['C_loss']])
