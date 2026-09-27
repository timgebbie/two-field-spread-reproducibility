"""Focused numerical figures and a video, all from stored trajectories."""
import csv
import io
import tempfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from matplotlib.lines import Line2D
from functions.experiments import VERSION,write_csv

BLUE='#2166ac';RED='#b2182b';GREEN='#238b45';GREY='#777777'
COLORS={'moving':BLUE,'immediate':RED,'fixed':GREEN}
LABELS={'moving':'Delayed / moving placement','immediate':'Next-update completion','fixed':'Delayed / fixed placement'}


def read_csv(path):
    with path.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    return {key:np.array([float(r[key]) if key!='phase' else r[key] for r in rows]) for key in rows[0]}


def curve(d,key,pre=None):
    """Insert an explicit pre-event point at each impulse timestamp."""
    u=[];y=[];v=d['executed_buy']+d['executed_sell']
    for j,t in enumerate(d['u_end']):
        if v[j]>0 and pre is not None:u.append(t);y.append(pre(j))
        u.append(t);y.append(d[key][j])
    return np.array(u),np.array(y)


def axis(ax,title,xlabel='Operational time u',ylabel=None,square=True):
    ax.set_title(title,loc='left',fontsize=10,pad=8);ax.set_xlabel(xlabel)
    if ylabel:ax.set_ylabel(ylabel)
    ax.grid(alpha=.16,lw=.6);ax.spines[['top','right']].set_visible(False)
    if square:ax.set_box_aspect(1)


def event_band(ax,c):
    times=[e['u'] for e in c['events']]
    ax.axvspan(min(times),max(times),color='#d9d9d9',alpha=.35,zorder=0);ax.set_xlim(0,c['horizon'])


def save(fig,folder,name):
    stem=folder/(name+'-'+VERSION)
    fig.savefig(str(stem)+'.png',dpi=160)
    target=folder/(name+'-'+VERSION+'.pdf');buffer=io.BytesIO()
    try:fig.savefig(buffer,format='pdf',metadata={'CreationDate':None,'ModDate':None})
    finally:plt.close(fig)
    content=buffer.getvalue()
    if not content.startswith(b'%PDF-') or not content.rstrip().endswith(b'%%EOF'):
        raise ValueError('Incomplete PDF export: '+str(target))
    # Stage complete bytes on the same filesystem; clean up on every exit.
    with tempfile.TemporaryDirectory(prefix='pdf-stage-',dir=folder) as directory:
        temporary=Path(directory)/'export'
        temporary.write_bytes(content);temporary.replace(target)


def draw_density(ax,x,rho,initial,row,m):
    for y in initial:ax.plot(x,y,color=GREY,lw=.8,ls='--',alpha=.6)
    lines=[ax.plot(x,rho[i],color=color,lw=1.5)[0] for i,color in enumerate((BLUE,RED))]
    ax.axhline(m.threshold,color=GREY,lw=.6,ls=':');quotes=[]
    for name,color,style in [('q_b',BLUE,':'),('q_a',RED,':'),('p_b',BLUE,'--'),('p_a',RED,'--')]:
        quotes.append(ax.axvline(row[name],color=color,ls=style,lw=.8,alpha=.75))
    ax.set_xlim(-8,8);ax.set_ylim(-.02,1.08)
    return lines,quotes


def render(root,c,m):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'legend.fontsize':8,'lines.linewidth':1.5,'savefig.facecolor':'white'})
    out=root/'outputs';folder=root/'figures';folder.mkdir(exist_ok=True)
    data={name:read_csv(out/(name+'-'+VERSION+'.csv')) for name in ['moving','immediate','fixed','no-event']}
    ix=read_csv(out/('density-index-'+VERSION+'.csv'))
    with np.load(out/('density-'+VERSION+'.npz')) as a:x=a['x'];rho=a['rho'];initial=a['initial']
    def row(i):return {k:v[i] for k,v in ix.items()}
    legend=[Line2D([],[],color=BLUE,label='Bid density'),Line2D([],[],color=RED,label='Ask density'),Line2D([],[],color=GREY,ls='--',label='Initial stationary field'),Line2D([],[],color=GREY,ls=':',label='Placement q'),Line2D([],[],color=GREY,ls='--',label='Threshold price p')]
    fig,axs=plt.subplots(3,3,figsize=(10,10))
    for n,(ax,s) in enumerate(zip(axs.flat,c['snapshots'])):
        hit=np.flatnonzero(np.isclose(ix['u'],s['u'],rtol=0,atol=1e-10)&(ix['phase']==s['phase']))
        if len(hit)!=1:raise ValueError('Snapshot is missing or ambiguous')
        i=int(hit[0]);draw_density(ax,x,rho[i],initial,row(i),m)
        axis(ax,f"({chr(97+n)}) {s['label']}\nu = {s['u']:g} ({s['phase']})",xlabel='Log price x',ylabel='Side density' if n%3==0 else None)
    fig.suptitle('F2  Density evolution through a finite buy programme',fontsize=14,y=.99)
    fig.legend(handles=legend,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.015))
    fig.tight_layout(rect=(0,.09,1,.96));save(fig,folder,'density')
    d=data['moving'];d['Q_sum']=d['Q_B_post']+d['Q_A_post']
    fig,axs=plt.subplots(2,3,figsize=(11,7.3));ax=axs.flat
    for key,label,color,pre in [('p_b','Bid',BLUE,lambda j:d['pre_p_b'][j]),('p_a','Ask',RED,lambda j:d['pre_p_a'][j]),('midpoint','Midpoint','black',lambda j:(d['pre_p_b'][j]+d['pre_p_a'][j])/2)]:ax[0].plot(*curve(d,key,pre),label=label,color=color)
    with (out/('moving-trades-'+VERSION+'.csv')).open(newline='') as f:trades=list(csv.DictReader(f))
    ax[0].plot([float(t['u']) for t in trades],[float(t['execution_log_price']) for t in trades],
               'o',ms=3,color='#d95f02',label='Executed log price',ls='none')
    ax[1].plot(*curve(d,'spread',lambda j:d['pre_p_a'][j]-d['pre_p_b'][j]),color=BLUE,label='Observed s')
    ax[1].plot(d['u_end'],d['Sigma'],color=GREY,ls='--',label='Placement Sigma')
    ax[2].plot(*curve(d,'Q_sum',lambda j:d['Q_B_quote'][j]+d['Q_A_quote'][j]),color=BLUE)
    ax[3].plot(*curve(d,'I_post',lambda j:d['I_quote'][j]),color=RED);ax[3].axhline(0,color=GREY,lw=.6)
    ax[4].plot(*curve(d,'cumulative_buy',lambda j:d['cumulative_buy'][j]-d['executed_buy'][j]),color=RED,label='Executed buy volume')
    ax[4].plot(d['u_end'],d['cumulative_completed_bid'],color=BLUE,label='Completed bid supply')
    ax[5].plot(d['u_end'],d['mu'],color=BLUE,label='Placement centre mu');ax[5].axhline(m.mu0,color=GREY,ls='--',label='Initial mu0')
    titles=['(a) Observed quotes','(b) Observed and placement widths','(c) Post-event pending exposure','(d) Post-event signed inventory','(e) Integrated initiation / completion','(f) Placement centre']
    units=['Log price','Log-price width','Volume: P_B + P_A','Volume: P_A - P_B','Cumulative volume','Log price']
    for i in range(6):
        axis(ax[i],titles[i],ylabel=units[i]);event_band(ax[i],c)
        if i in (0,1,4,5):ax[i].legend(frameon=False,loc='best')
    fig.suptitle('F3  Prices and market-maker state from the same simulation',fontsize=14,y=.995)
    fig.tight_layout(rect=(0,0,1,.96));save(fig,folder,'timeseries')
    video=c['video'];count=round(video['seconds']*video['fps']);nominal=np.linspace(0,c['horizon'],count)
    selected=np.searchsorted(ix['u'],nominal,side='right')-1
    # Hold stored states; each impulse gets consecutive pre/post frames.
    for e in c['events']:
        k=int(round(e['u']/c['horizon']*(count-1)))
        for offset,phase in [(-1,'pre'),(0,'post')]:selected[k+offset]=np.flatnonzero(np.isclose(ix['u'],e['u'],rtol=0,atol=1e-10)&(ix['phase']==phase))[0]
    frame_map=[{'video_frame':k,'video_seconds':k/video['fps'],'density_frame':int(i),'u':ix['u'][i],'phase':ix['phase'][i]} for k,i in enumerate(selected)]
    write_csv(out/('video-frames-'+VERSION+'.csv'),frame_map)
    fig=plt.figure(figsize=(8,6.5));gs=fig.add_gridspec(3,1,height_ratios=[4,1,1],hspace=.65)
    density=fig.add_subplot(gs[0]);spread=fig.add_subplot(gs[1]);pending=fig.add_subplot(gs[2])
    lines,quotes=draw_density(density,x,rho[0],initial,row(0),m)
    axis(density,'',xlabel='Log price x',ylabel='Side density',square=False)
    density.legend(handles=legend[:2]+legend[3:],loc='upper center',ncol=4,frameon=False)
    d=data['moving'];spread.plot(*curve(d,'spread',lambda j:d['pre_p_a'][j]-d['pre_p_b'][j]),color=BLUE,lw=1)
    pending.plot(*curve(d,'Q_sum',lambda j:d['Q_B_quote'][j]+d['Q_A_quote'][j]),color=BLUE,lw=1)
    cursors=[];dots=[]
    for ax,label in [(spread,'Spread'),(pending,'Pending volume')]:
        axis(ax,'',ylabel=label,square=False);event_band(ax,c)
        cursors.append(ax.axvline(0,color='black',lw=1));dots.append(ax.plot([],[],'o',color='black',ms=3)[0])
    title=fig.suptitle('',fontsize=12,y=.98);fig.subplots_adjust(left=.13,right=.97,bottom=.08,top=.90)
    writer=FFMpegWriter(fps=video['fps'],codec='libx264',metadata={'title':'Two-field spread numerical pilot '+VERSION},extra_args=['-crf','23','-pix_fmt','yuv420p','-threads','1'])
    with writer.saving(fig,str(folder/('density-'+VERSION+'.mp4')),dpi=video['dpi']):
        for k,i in enumerate(selected):
            r=row(i)
            for side,line in enumerate(lines):line.set_ydata(rho[i,side])
            for line,key in zip(quotes,['q_b','q_a','p_b','p_a']):line.set_xdata([r[key],r[key]])
            for line in cursors:line.set_xdata([r['u'],r['u']])
            dots[0].set_data([r['u']],[r['spread']]);dots[1].set_data([r['u']],[r['Q_sum']])
            phase='pre execution' if r['phase']=='pre' else ('post execution' if any(abs(r['u']-e['u'])<1e-10 for e in c['events']) else 'stored state')
            title.set_text(f"Numerical pilot {VERSION}   |   u = {r['u']:.3f}   |   {phase}");writer.grab_frame()
            if k==round(3/c['horizon']*(count-1)):fig.savefig(folder/('video-poster-'+VERSION+'.png'),dpi=video['dpi'])
    plt.close(fig);print('Rendered F2, F3 and trajectory video from saved states.',flush=True)


def render_assessment(root,c):
    out=root/'outputs';folder=root/'figures'
    mm=np.load(out/('market-maker-'+VERSION+'.npz'))
    styles={'moving':(BLUE,'-','Moving placement'),'immediate':(RED,'--','Next-update completion'),
      'fixed':(GREY,':','Both feedbacks off'),'width-fixed':('#762a83','--','Width feedback off'),
      'centre-fixed':(GREEN,'-.','Centre feedback off')}
    event_times=np.array([e['u'] for e in c['events']])
    fig,axs=plt.subplots(2,3,figsize=(11,7.6))
    for row,flow in enumerate(('directional','balanced')):
        for mode,(color,ls,label) in styles.items():
            d=mm[flow+'-'+mode];u=[];spread=[];mid=[]
            for r in d:
                if np.any(np.isclose(r[0],event_times,rtol=0,atol=1e-10)):
                    u.append(r[0]);spread.append(r[12]-r[11]-d[0,4]);mid.append((r[11]+r[12])/2-d[0,3])
                u.append(r[0]);spread.append(r[4]-d[0,4]);mid.append(r[3]-d[0,3])
            axs[row,0].plot(u,spread,color=color,ls=ls,label=label)
            axs[row,1].plot(u,mid,color=color,ls=ls,label=label)
        d=mm[flow+'-moving'];u=[];total=[];signed=[]
        for r in d:
            if np.any(np.isclose(r[0],event_times,rtol=0,atol=1e-10)):
                u.append(r[0]);total.append(r[9]+r[10]);signed.append(r[10]-r[9])
            u.append(r[0]);total.append(r[7]+r[8]);signed.append(r[8]-r[7])
        axs[row,2].plot(u,total,color=BLUE,label='Total pending')
        axs[row,2].plot(u,signed,color=RED,ls='--',label='Signed inventory')
        axs[row,2].legend(frameon=False,fontsize=7)
        for col,(title,unit) in enumerate([('Spread response','Change in log-price spread'),('Midpoint response','Change in log midpoint'),('Moving case: pending modes','Volume')]):
            ax=axs[row,col];axis(ax,f'({chr(97+row*3+col)}) {flow.capitalize()}\n{title}',ylabel=unit)
            event_band(ax,c);ax.axhline(0,color=GREY,lw=.5)
    fig.legend(*axs[0,0].get_legend_handles_labels(),loc='lower center',ncol=3,frameon=False,fontsize=8)
    fig.suptitle('F4  Market-maker response to one-sided and balanced programmes',fontsize=13,y=.995)
    fig.tight_layout(rect=(0,.085,1,.95));save(fig,folder,'controls')
    corr=np.load(out/('correlations-'+VERSION+'.npz'));paths=np.load(out/('statistics-paths-'+VERSION+'.npz'))
    s=c['statistics'];b=s['burn_events'];sample=paths['lmf-moving-0-values'][b:b+512]
    signs=paths['lmf-moving-0-signs'][b:b+512];n=np.arange(1,len(sample)+1)
    groups=[('lmf-moving',BLUE,'Order splitting / moving'),('iid-moving',RED,'Independent signs / moving'),
            ('lmf-fixed',GREEN,'Order splitting / fixed')]
    refinement=np.load(out/('resolution-correlations-'+VERSION+'.npz'))
    def paired(ax,kind,k,lags):
        for dx,style in [(0.025,':'),(0.0125,'--')]:
            a=np.mean([refinement[f'resolution-{dx}-{j}-{kind}'][k] for j in c['resolution']['replicates']],axis=0)
            if kind=='acf':a=a[1:]
            ax.plot(lags,a,color='black',ls=style,lw=.9,label=f'Paired 2 paths / dx={dx}')
    fig,axs=plt.subplots(3,3,figsize=(11,11))
    axs[0,0].plot(n,sample[:,6],color='#d95f02',lw=.7,label='Execution log price')
    axs[0,0].plot(n,sample[:,2],color='black',lw=1,label='Log midpoint');axs[0,0].legend(frameon=False,fontsize=7)
    axs[0,1].plot(n,sample[:,3],color=BLUE,lw=1)
    axs[0,2].step(n,signs,where='post',color=BLUE,lw=.6);axs[0,2].set_yticks([-1,1]);axs[0,2].set_ylim(-1.2,1.2)
    for ax,title,unit in zip(axs[0],['(a) Executed prices: one path','(b) Observed spread: same path','(c) Input trade signs: same path'],['Log price','Log-price width','Aggressor sign']):
        axis(ax,title,xlabel='Retained trade index',ylabel=unit)
    labels=[r'Trade signs $\epsilon$',r'Midpoint increments $r_m$',r'Trade-price increments $r_T$',
            r'Absolute midpoint increments $|r_m|$',r'Absolute trade increments $|r_T|$',r'Spread $s$']
    lag=corr['lags'][1:]
    for k,ax in enumerate(axs.flat[3:]):
        for group,color,label in groups:
            values=corr[group+'-acf'][:,k,1:];mean=values.mean(axis=0);se=values.std(axis=0,ddof=1)/np.sqrt(len(values))
            ax.plot(lag,mean,color=color,label=label,lw=1.2);ax.fill_between(lag,mean-2*se,mean+2*se,color=color,alpha=.10,lw=0)
        if k==0:ax.plot(lag,corr['renewal_reference'][1:],color='black',ls='--',lw=1,label='Truncated renewal reference')
        if k in (1,5):paired(ax,'acf',k,lag)
        ax.axhline(0,color=GREY,lw=.6);ax.set_xscale('log');ax.set_xlim(1,s['maximum_lag'])
        axis(ax,f'({chr(100+k)}) '+labels[k],xlabel='Lag in executed trades',ylabel='Pearson ACF')
    handles,labels=axs[1,0].get_legend_handles_labels()
    hh,ll=axs[1,1].get_legend_handles_labels();handles+=hh[-2:];labels+=ll[-2:]
    fig.legend(handles,labels,loc='lower center',ncol=2,frameon=False,fontsize=8)
    fig.suptitle('F5  Event-time paths and correlations from DTRW executions',fontsize=14,y=.995)
    fig.tight_layout(rect=(0,.085,1,.96));save(fig,folder,'autocorrelations')
    fig,axs=plt.subplots(2,3,figsize=(11,7.5));lag=corr['ccf_lags']
    labels=[r'Signs $\rightarrow r_m$',r'Signs $\rightarrow\Delta s$',r'$r_m\rightarrow r_T$',
            r'$r_m\rightarrow\Delta s$',r'$|r_m|\rightarrow s$',r'$|r_T|\rightarrow s$']
    for k,ax in enumerate(axs.flat):
        for group,color,label in groups:
            values=corr[group+'-ccf'][:,k];mean=values.mean(axis=0);se=values.std(axis=0,ddof=1)/np.sqrt(len(values))
            ax.plot(lag,mean,color=color,label=label,lw=1.2);ax.fill_between(lag,mean-2*se,mean+2*se,color=color,alpha=.10,lw=0)
        paired(ax,'ccf',k,lag)
        ax.axhline(0,color=GREY,lw=.6);ax.axvline(0,color=GREY,lw=.6,ls=':');ax.set_xlim(lag[0],lag[-1])
        axis(ax,f'({chr(97+k)}) '+labels[k],xlabel='Trade lag: positive = first leads',ylabel='Pearson CCF')
    fig.legend(*axs[0,0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False,fontsize=8)
    fig.suptitle('F6  Signed and magnitude cross-correlations',fontsize=14,y=.995)
    fig.tight_layout(rect=(0,.085,1,.95));save(fig,folder,'cross-correlations')
    print('Rendered F4 market-maker controls, F5 ACFs and F6 CCFs.',flush=True)
