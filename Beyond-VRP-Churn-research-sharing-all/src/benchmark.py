from pathlib import Path
import gc,json,platform,resource,time
from semantic import *
ROOT=Path(__file__).resolve().parents[1]
out={'python':platform.python_version(),'platform':platform.platform(),'scope':'A differencing on already parsed and grouped sets; includes group comparison; excludes C and witnesses','repetitions':[]}
try:out['cpu']=next(x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name'))
except Exception:pass
for day in (1,7,13):
    label=f'2026-09-{day:02}_2026-09-{day+1:02}'
    t=time.perf_counter();a=group(read(ROOT/'data'/f'ripe-2026-09-{day:02}.json'));b=group(read(ROOT/'data'/f'ripe-2026-09-{day+1:02}.json'));parsing=time.perf_counter()-t
    for rep in range(3):
        outputs={};record={'pair':label,'rep':rep+1,'parse_and_group_seconds':parsing,'order':['full','incremental'] if rep%2==0 else ['incremental','full']}
        for mode in record['order']:
            gc.collect();t=time.perf_counter();outputs[mode]=diff_authorizations(a,b,mode=='incremental',False);record[mode+'_seconds']=time.perf_counter()-t
        assert outputs['full']==outputs['incremental']
        record['equal']=True;record['peak_process_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;out['repetitions'].append(record)
        (ROOT/'results/benchmark.json').write_text(json.dumps(out,indent=2));print(record,flush=True)
    del a,b,outputs;gc.collect()
