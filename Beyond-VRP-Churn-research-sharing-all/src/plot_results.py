from pathlib import Path
import json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
data=json.loads((ROOT/'results/cohort.json').read_text())['pairs']
assert len(data)==13
days=np.arange(2,15)
fig,axes=plt.subplots(2,2,figsize=(7.1,4.6),sharex=True)
for j,(v,cap,name) in enumerate([('4','24','IPv4, lengths ≤24'),('6','48','IPv6, lengths ≤48')]):
    caps=[x['families'][v]['caps'][cap] for x in data]
    ax=axes[0,j];ax.plot(days,[c['A_gain'] for c in caps],'-o',color='#0072B2',label='Gains',markersize=3)
    ax.plot(days,[c['A_loss'] for c in caps],'--s',color='#D55E00',label='Losses',markersize=3)
    ax.set_yscale('log');ax.set_title(name);ax.set_ylabel('Prefix–origin pairs');ax.legend(frameon=False,ncol=2,fontsize=8)
    ax=axes[1,j];ax.bar(days,[100*c['cancellation'] for c in caps],color='#009E73',width=.7)
    ax.set_ylim(0,105);ax.set_ylabel('Cancellation (%)');ax.set_xlabel('September 2026: ending day')
    ax.set_xticks([2,4,6,8,10,12,14])
for ax in axes.flat:ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(ROOT/'figures/daily.pdf',bbox_inches='tight');fig.savefig(ROOT/'figures/daily.png',dpi=220,bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(7.1,2.7),sharey=True)
for ax,v,name in zip(axes,['4','6'],['IPv4','IPv6']):
    f=[r['families'][v] for r in data];ax.bar(days,[100*x['A_unchanged_origins_full']/x['changed_origins'] for x in f],color='#0072B2')
    ax.set_title(name);ax.set_xlabel('September 2026: ending day');ax.set_xticks([2,4,6,8,10,12,14]);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Changed-origin groups with\nidentical full-width A (%)')
fig.tight_layout();fig.savefig(ROOT/'figures/noops.pdf',bbox_inches='tight');fig.savefig(ROOT/'figures/noops.png',dpi=220,bbox_inches='tight');plt.close(fig)

projection=json.loads((ROOT/'results/route-projection.json').read_text())
states=['Valid','Invalid','NotFound'];fig,axes=plt.subplots(1,2,figsize=(7.1,3))
for ax,v in zip(axes,['4','6']):
    f=projection['families'][v];m=np.array([[f['matrix'].get(a+'->'+b,0) for b in states] for a in states])
    ax.imshow(np.log10(m+1),cmap='Blues',vmin=0,vmax=6)
    for i in range(3):
        for j in range(3):ax.text(j,i,f'{m[i,j]:,}',ha='center',va='center',color='white' if m[i,j]>5000 else 'black',fontsize=8)
    ax.set_xticks(range(3),states);ax.set_yticks(range(3),states);ax.set_xlabel('September 14 view');ax.set_title('IPv'+v)
axes[0].set_ylabel('September 13 view');fig.tight_layout();fig.savefig(ROOT/'figures/projection.pdf',bbox_inches='tight');fig.savefig(ROOT/'figures/projection.png',dpi=220,bbox_inches='tight');plt.close(fig)

b=json.loads((ROOT/'results/benchmark.json').read_text())['repetitions'];pairs=sorted({r['pair'] for r in b});fig,ax=plt.subplots(figsize=(3.45,2.55));x=np.arange(3)
for offset,mode,color in [(-.18,'full','#0072B2'),(.18,'incremental','#E69F00')]:
    vals=[[r[mode+'_seconds'] for r in b if r['pair']==p] for p in pairs];med=[statistics.median(a) for a in vals]
    ax.bar(x+offset,med,width=.34,label=mode.capitalize(),color=color)
    ax.errorbar(x+offset,med,yerr=[[m-min(a) for m,a in zip(med,vals)],[max(a)-m for m,a in zip(med,vals)]],fmt='none',ecolor='black',capsize=3,lw=.8)
ax.set_xticks(x,['Sep 1–2','Sep 7–8','Sep 13–14']);ax.set_ylabel('Authorization kernel (s)');ax.legend(frameon=False,fontsize=8);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(ROOT/'figures/benchmark.pdf',bbox_inches='tight');fig.savefig(ROOT/'figures/benchmark.png',dpi=220,bbox_inches='tight')
print('Rendered four figure sets')
