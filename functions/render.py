"""Three numerical figures and a video from the stored experiment data."""
import csv
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
    fig.savefig(str(stem)+'.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)


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
    fig,axs=plt.subplots(1,3,figsize=(11,4.2))
    for name in c['cases']:
        d=data[name]
        # Only the smooth stationary no-event reference is interpolated to
        # event-neighbour samples; impulse trajectories are never smoothed.
        reference=np.interp(d['u_end'],data['no-event']['u_end'],data['no-event']['midpoint'])
        d['response']=d['midpoint']-reference;d['Q_sum']=d['Q_B_post']+d['Q_A_post']
        style={'color':COLORS[name],'ls':{'moving':'-','immediate':'--','fixed':':'}[name],'label':LABELS[name]}
        axs[0].plot(*curve(d,'spread',lambda j:d['pre_p_a'][j]-d['pre_p_b'][j]),**style)
        axs[1].plot(*curve(d,'response',lambda j:(d['pre_p_a'][j]+d['pre_p_b'][j])/2-reference[j]),**style)
        axs[2].plot(*curve(d,'Q_sum',lambda j:d['Q_B_quote'][j]+d['Q_A_quote'][j]),**style)
    for ax,title,unit in zip(axs,['(a) Observed spread','(b) Midpoint response','(c) Post-event pending exposure'],['Log-price width','Event minus no-event log price','Volume: P_B + P_A']):axis(ax,title,ylabel=unit);event_band(ax,c)
    fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=3,frameon=False)
    fig.suptitle('F4  Matched executed programme; completion and placement controls',fontsize=13,y=.995)
    fig.tight_layout(rect=(0,.10,1,.94));save(fig,folder,'controls')
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
    plt.close(fig);print('Rendered F2, F3, F4 and trajectory video from saved states.',flush=True)
