"""Render saved theory tables without running any evaluator."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BLUE, RED, GREY, GREEN = '#2166ac', '#c75b32', '#30343b', '#26806a'

def _panel(ax, label, title):
    ax.set_box_aspect(1)
    ax.set_title(f'({label}) {title}',loc='left',pad=10)
    ax.grid(True,color='#dedede',linewidth=.5,alpha=.65)

def _save(fig, path):
    for ext in ('png','pdf'):
        metadata={'Creator':'Two Field Spread v0.2.0'}
        if ext=='pdf':metadata.update(CreationDate=None,ModDate=None)
        fig.savefig(Path(str(path)+'.'+ext),bbox_inches='tight',metadata=metadata)
    plt.close(fig)

def render(root):
    root=Path(root);out=root/'outputs';figs=root/'figures';figs.mkdir(exist_ok=True)
    read=lambda name: np.loadtxt(out/(name+'.csv'),delimiter=',',skiprows=1)
    info=json.loads((out/'theory-summary-v0.2.0.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,
        'axes.titlesize':11,'legend.fontsize':8.5,'lines.linewidth':1.8,
        'axes.spines.top':False,'axes.spines.right':False,'axes.axisbelow':True,
        'savefig.dpi':220,'pdf.fonttype':42,'ps.fonttype':42})
    x,b,a,phi,rho=read('reference-v0.2.0').T
    pb,pa,qb,qa,eps=[info[k] for k in ('p_b','p_a','q_b','q_a','threshold')]
    fig,axes=plt.subplots(1,2,figsize=(9.2,4.6),layout='constrained')
    ax=axes[0];_panel(ax,'a','Side densities and quote geometry')
    ax.axvspan(pb,pa,color='#e7ecf2',alpha=.8,label='Sub-threshold core')
    ax.plot(x,b,color=BLUE,label=r'Bid $\rho_B$');ax.plot(x,a,color=RED,ls='--',label=r'Ask $\rho_A$')
    ax.axhline(eps,color=GREY,ls=':',lw=1.2)
    for q,c,lab in [(qb,BLUE,r'$q_b$'),(qa,RED,r'$q_a$')]:
        ax.axvline(q,color=c,ls='--',lw=1,alpha=.65);ax.text(q,1.025,lab,ha='center',color=c)
    for p,c,lab in [(pb,BLUE,r'$p_b$'),(pa,RED,r'$p_a$')]:
        ax.plot(p,eps,'o',color=c,ms=5);ax.text(p,eps+.07,lab,ha='center',color=c)
    for lo,hi,y,lab in [(qb,qa,.38,r'$\Sigma=12$'),(pb,pa,.62,rf'$s={pa-pb:.3f}$')]:
        ax.annotate('',xy=(hi,y),xytext=(lo,y),arrowprops={'arrowstyle':'<->','color':GREY,'lw':1})
        ax.text(0,y+.025,lab,ha='center',color=GREY)
    ax.text(x[0]+.25,eps+.035,r'$\epsilon=0.1$',fontsize=9,color=GREY)
    ax.set(xlim=(x[0],x[-1]),ylim=(0,1.1),xlabel='Log-price coordinate $x$',ylabel='Standing density')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=3,frameon=False)
    ax=axes[1];_panel(ax,'b','Imbalance and total standing density')
    ax.plot(x,phi,color=BLUE,label=r'$\phi=\rho_B-\rho_A$')
    ax.plot(x,rho,color=GREY,ls='--',label=r'$\rho=\rho_B+\rho_A$')
    ax.axhline(0,color='#aaaaaa',lw=.8);ax.axvline(0,color='#aaaaaa',ls=':',lw=1)
    ax.plot(0,0,'o',color=BLUE,ms=4)
    ax.set(xlim=(x[0],x[-1]),ylim=(-1.1,1.1),xlabel='Log-price coordinate $x$',ylabel='Field value')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=2,frameon=False)
    _save(fig,figs/'figure-01-reference-v0.2.0')
    fig,axs=plt.subplots(2,3,figsize=(13.1,8.8),layout='constrained')
    ax=axs[0,0];_panel(ax,'a','Direct and displaced response')
    t,g0,g1,g2,kg=read('kernels-v0.2.0').T
    for y,c,ls,lab in [(g0,GREY,'-',r'$d=0$'),(g1,BLUE,'-',r'$d=1$'),(g2,RED,'--',r'$d=2$'),(kg,GREEN,':',r'$d=1,\ w=0.5$')]:
        ax.loglog(t,y,color=c,ls=ls,label=lab)
    ax.set(xlim=(t[0],t[-1]),ylim=(1e-5,5),xlabel=r'Operational lag $\tau$',ylabel='Density response / unit volume')
    ax.legend(frameon=False,loc='upper right')
    ax=axs[0,1];_panel(ax,'b','Peak lag for a point source')
    d,p0,p025,p1=read('peak-lag-v0.2.0').T
    for y,c,ls,lab in [(p0,GREY,':',r'$\nu=0$'),(p025,RED,'--',r'$\nu=0.25$'),(p1,BLUE,'-',r'$\nu=1$')]:
        ax.plot(d,y,color=c,ls=ls,label=lab)
    ax.set(xlim=(0,4),ylim=(0,8.3),xlabel='Offset $d$',ylabel=r'Peak lag $\tau^\star$');ax.legend(frameon=False)
    ax=axs[0,2];_panel(ax,'c','Integrated response attenuation')
    d,r0,r05,r1=read('attenuation-v0.2.0').T
    for y,c,ls,lab in [(r0,GREY,'-',r'Point source'),(r05,BLUE,'--',r'Uniform $w=0.5$'),(r1,RED,':',r'Uniform $w=1$')]:
        ax.semilogy(d,y,color=c,ls=ls,label=lab)
    ax.set(xlim=(0,4),ylim=(.009,1.2),xlabel=r'Offset $d/\ell_\nu$',ylabel='Integrated response ratio');ax.legend(frameon=False)
    ax=axs[1,0];_panel(ax,'d','Inward penetration')
    r,depth,spread=read('threshold-v0.2.0').T
    ax.semilogx(r,depth,color=BLUE);ax.plot(info['threshold_ratio'],info['penetration'],'o',color=BLUE,ms=5)
    ax.set(xlim=(r[0],r[-1]),ylim=(0,5),xlabel=r'Threshold ratio $\epsilon/\rho^q$',ylabel=r'Penetration $d^*/\ell_\nu$')
    ax=axs[1,1];_panel(ax,'e','Threshold sensitivity of spread')
    ax.semilogx(r,spread,color=BLUE,label='Observed spread');ax.axhline(12,color=GREY,ls='--',label=r'Placement width $\Sigma$')
    ax.plot(info['threshold_ratio'],info['spread'],'o',color=BLUE,ms=5)
    ax.set(xlim=(r[0],r[-1]),ylim=(0,13),xlabel=r'Common ratio $\epsilon/\rho^q$',ylabel=r'Spread $s/\ell_\nu$');ax.legend(frameon=False,loc='lower right')
    ax=axs[1,2];_panel(ax,'f','Finite-window capacity')
    T,C,L,Lweak,Lend=read('capacity-v0.2.0').T
    ax.loglog(T,L,color=BLUE,label=r'$L_{avg}$, $\nu=1$')
    ax.loglog(T,Lweak,color=GREY,ls='--',label=r'$L_{avg}$, $\nu=0$')
    ax.loglog(T,Lend,color=RED,ls=':',label=r'$L_{end}$, $\nu=0$')
    ax.set(xlim=(T[0],T[-1]),xlabel='Operational window $T$',ylabel=r'Capacity / $(\lambda\sqrt{D})$');ax.legend(frameon=False,loc='upper left')
    _save(fig,figs/'figure-s01-theory-v0.2.0')
