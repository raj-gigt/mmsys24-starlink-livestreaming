"""Compare the latest actual original/improved demo, not final test evidence."""
import gzip
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'reports/final/demo';chosen={}
    for policy in ['original','improved']:
        paths=sorted(folder.glob('leo-demo-'+policy+'-*.json'))
        if not paths:
            print('Comparison plot waits for both original and improved real demos.');return
        chosen[policy]=json.loads(paths[-1].read_text())
    assert len({r['case_id'] for r in chosen.values()})==1
    fig,axes=plt.subplots(5,1,figsize=(8.8,8.8),sharex=True)
    for policy,color,label in [('original','#7B8796','Original CMAB'),('improved','#128C86','Guarded CMAB')]:
        r=chosen[policy];d=json.loads(gzip.decompress((folder/r['raw_evidence']).read_bytes()))
        t=d['telemetry.json'];samples=t['samples'];start=t['started_at_ms']/1000
        times=[s['t_s'] for s in samples]
        if policy=='original':
            stages=d['applied-profile.json']['applied']
            ts=[max(0,s['at_unix_s']-start) for s in stages]
            values=[0 if s['loss_percent']==100 else s['rate_mbit'] for s in stages]
            axes[0].step(ts+[times[-1]],values+[values[-1]],where='post',color='#263B58')
        trace=t['cmab_decisions']
        axes[1].step([s['at_ms']/1000-start for s in trace],[s['bitrate_bps']/1e6 for s in trace],where='post',color=color,label=label,lw=1.3)
        for ax,key,scale in [(axes[2],'played_bitrate_bps',1e6),(axes[3],'buffer_s',1),(axes[4],'latency_s',1)]:
            ax.plot(times,[s[key]/scale if s.get(key) is not None else float('nan') for s in samples],color=color,lw=1.2,label=label)
    axes[1].legend(loc='upper right',ncol=2,frameon=False,fontsize=10)
    for ax,label in zip(axes,['Applied link\nrate (Mbps)','Logged selections\n(Mbps)','Actually played\nrate (Mbps)','Buffer (s)','Live delay (s)']):
        ax.set_ylabel(label);ax.grid(alpha=.18);ax.spines[['top','right']].set_visible(False)
    axes[-1].set_xlabel('Wall time after player Load (s)')
    axes[-1].axhline(3,color='#C17A18',ls='--',lw=.8)
    axes[-1].set_xlim(0,max(s['t_s'] for s in samples))
    fig.suptitle('Real recovery demonstration: identical case, two deployed policies',fontsize=13)
    fig.text(.13,.017,'Demonstration only; excluded from final results. Source run IDs and raw events: demo-comparison.json.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.97))
    for ext in ['svg','png']:fig.savefig(folder/('demo-comparison.'+ext),dpi=180)
    plt.close(fig)
    (folder/'demo-comparison.json').write_text(json.dumps({'scope':'Demo only, not final performance comparison','runs':chosen},indent=2))
    print('Created real-demo selected/played bitrate, buffer and delay comparison.')


if __name__=='__main__':main()
