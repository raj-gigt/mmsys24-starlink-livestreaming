"""Shared testbed and actual policy data path; vector figure for report/slides."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/final/figures';OUT.mkdir(parents=True,exist_ok=True)
NAVY='#263B58';TEAL='#128C86';GRAY='#64748B';AMBER='#C17A18'
fig,ax=plt.subplots(figsize=(10,5.1));ax.set(xlim=(0,10),ylim=(0,5.4));ax.axis('off')
def box(x,y,w,h,title,detail,color=NAVY):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04,rounding_size=.08',facecolor='#F6F8FA',edgecolor=color,lw=1.3))
 ax.text(x+w/2,y+h*.72,title,ha='center',va='center',fontsize=12,fontweight='bold',color=color)
 ax.text(x+w/2,y+h*.30,detail,ha='center',va='center',fontsize=10.5,color='#334155',linespacing=1.35)
def arrow(a,b,label=None,color=GRAY,style='-',rad=0):
 ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color=color,lw=1.1,linestyle=style,connectionstyle='arc3,rad='+str(rad)))
 if label:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.10,label,ha='center',va='bottom',fontsize=9.8,color=color,bbox={'facecolor':'white','edgecolor':'none','pad':1})
box(.2,2.65,2.05,.95,'livesim2 source','8 representations\n2 s segments / 60 s loop')
box(3.55,2.65,2.25,.95,'Nginx + tc/netem','Media proxy + common\ncapacity / delay / loss replay')
box(7.15,2.65,2.6,.95,'Chrome + dash.js','Selected synchronous ABR\nActual requested / played quality',TEAL)
arrow((2.3,3.22),(3.5,3.22),'media',NAVY);arrow((5.85,3.22),(7.1,3.22),'media',NAVY)
arrow((7.10,2.88),(5.85,2.88),'request',NAVY)
arrow((3.50,2.88),(2.30,2.88),'request',NAVY)
box(3.55,4.0,2.25,.8,'Scenario manifest','Measured RTT +\ngenerated capacity',AMBER)
arrow((4.68,3.95),(4.68,3.64),color=AMBER)
box(7.15,4.0,2.6,.8,'Offline PyTorch training','Train scenarios / media bytes\nSynchronous JS actor export',TEAL)
arrow((8.45,3.95),(8.45,3.64),color=TEAL,style='--')
box(.2,.72,2.4,1.0,'Identical controls','Media / target / catch-up\nLink replay and start phase')
box(4.05,.72,2.3,1.0,'Statistics sidecar','Timestamped RTT health\nPlayer event / metric ingestion')
arrow((5.15,1.78),(4.72,2.60),'probe',GRAY)
arrow((6.40,1.64),(7.60,2.60),'RTT input',TEAL,rad=-.08)
arrow((8.55,2.60),(6.40,1.22),'player telemetry',GRAY,rad=-.1)
box(7.65,.72,2.1,1.0,'MongoDB + exports','DB events + browser ledger\nAnalysis / plots / report')
arrow((6.4,1.15),(7.6,1.15),'records',GRAY)
arrow((9.35,2.60),(9.35,1.77),'Selenium\nexport',GRAY)
ax.text(.2,5.25,'Common testbed and policy interfaces',fontsize=14,fontweight='bold',color=NAVY,va='top')
ax.text(.2,.16,'The policy reads player observations and cached RTT health. MongoDB is for logging, not an inference dependency.',fontsize=9.5,color=GRAY)
fig.subplots_adjust(left=.02,right=.99,top=.98,bottom=.03)
for ext in ['svg','png']:fig.savefig(OUT/('F1-system.'+ext),dpi=180)
plt.close(fig);print('Created F1 system data-flow diagram')
