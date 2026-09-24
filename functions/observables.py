"""Execution prices and pairwise lag statistics on an explicit trade tape.

The primary execution log price is the fill-volume-weighted log coordinate,
as in correlation-emergence v2.0.0 records.py. Arithmetic price VWAP is
retained separately; it is not exp(mean log price). No prices are simulated
outside the density execution mechanism.
"""
import numpy as np


def trade_record(m, record, removed, event_index, parent_order_id):
    fills=np.asarray(removed,dtype=float)*m.dx
    if fills.shape!=(2,len(m.x)) or not np.all(np.isfinite(fills)) or np.any(fills<0):
        raise ValueError('Invalid execution fills')
    totals=fills.sum(axis=1);active=np.flatnonzero(totals>0)
    if len(active)!=1:raise ValueError('A trade observation requires exactly one executed aggressor side')
    side=int(active[0]);ids=np.flatnonzero(fills[side]>0)
    if np.any((ids==0)|(ids==len(m.x)-1)):raise ValueError('Reservoirs are not executable')
    volume=float(totals[side]);weights=fills[side,ids]/volume;x=m.x[ids]
    z=float(weights@x);vwap=float(weights@np.exp(x));sign=1 if side==1 else -1
    pre=(record['pre_p_b']+record['pre_p_a'])/2
    result={'event_index':event_index,'parent_order_id':parent_order_id,'operational_step':record['step']+1,
        'u':record['u_end'],'aggressor_sign':sign,'filled_quantity':volume,
        'execution_log_price':z,'execution_price_geometric':float(np.exp(z)),
        'execution_price_vwap':vwap,'pre_event_mid_log_price':pre,'post_event_mid_log_price':record['midpoint'],
        'pre_bid_log_price':record['pre_p_b'],'pre_ask_log_price':record['pre_p_a'],
        'post_bid_log_price':record['p_b'],'post_ask_log_price':record['p_a'],
        'pre_spread':record['pre_p_a']-record['pre_p_b'],'post_spread':record['spread'],
        'q_b_used':record['q_b'],'q_a_used':record['q_a'],'Sigma_used':record['Sigma'],'mu_used':record['mu'],
        'pending_bid_quote':record['Q_B_quote'],'pending_ask_quote':record['Q_A_quote'],
        'pending_bid_post':record['Q_B_post'],'pending_ask_post':record['Q_A_post'],
        'instant_mid_log_change':record['midpoint']-pre,
        'requested_quantity':record['requested_buy' if sign==1 else 'requested_sell'],
        'unfilled_quantity':record['unfilled_buy' if sign==1 else 'unfilled_sell'],
        'quote_midpoint_sign':int(np.sign(z-pre))}
    rows=[{'event_index':event_index,'parent_order_id':parent_order_id,'u':record['u_end'],
        'aggressor_sign':sign,'grid_index':int(j),'log_price':float(m.x[j]),'price':float(np.exp(m.x[j])),
        'filled_quantity':float(fills[side,j])} for j in (ids if sign==1 else ids[::-1])]
    return result,rows


def finish_tape(rows):
    """Add legacy tick labels and consecutive-trade increments in place.

    First increments are missing, not zero. A zero tick carries the preceding
    nonzero tick sign; the first tick label is zero, as in the prior code.
    """
    previous_tick=0
    for i,r in enumerate(rows):
        if i==0:
            r.update(tick_rule_sign=0,mid_log_increment=None,trade_log_increment=None,
                abs_mid_log_increment=None,abs_trade_log_increment=None,spread_increment=None)
            continue
        old=rows[i-1];rm=r['post_event_mid_log_price']-old['post_event_mid_log_price']
        rt=r['execution_log_price']-old['execution_log_price']
        if rt!=0:previous_tick=int(np.sign(rt))
        r.update(tick_rule_sign=previous_tick,mid_log_increment=rm,trade_log_increment=rt,
            abs_mid_log_increment=abs(rm),abs_trade_log_increment=abs(rt),spread_increment=r['post_spread']-old['post_spread'])


def lag_correlation(x,y,lags):
    """Pearson Corr(x_n,y_(n+lag)); positive lag means x leads y.

    Centre each overlapping slice by its own mean, matching the prior v2.0.0
    ACF estimator for x=y. Missing values are not silently compressed, and
    constant slices have undefined correlation rather than zero correlation.
    """
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float);lags=np.asarray(lags)
    if x.ndim!=1 or y.shape!=x.shape or len(x)<4 or not np.all(np.isfinite([x,y])):
        raise ValueError('Supply equal finite one-dimensional series with at least four observations')
    if lags.ndim!=1 or not np.issubdtype(lags.dtype,np.integer) or np.any(np.abs(lags)>len(x)-2):
        raise ValueError('Integer lags must retain at least two aligned pairs')
    values=[];pairs=[]
    for lag in lags:
        if lag>0:a,b=x[:-lag],y[lag:]
        elif lag<0:a,b=x[-lag:],y[:lag]
        else:a,b=x,y
        a=a-a.mean();b=b-b.mean();scale=np.sqrt((a@a)*(b@b))
        if scale==0:raise ValueError('Correlation is undefined for a constant overlapping slice')
        values.append(float((a@b)/scale));pairs.append(len(a))
    return np.array(values),np.array(pairs,dtype=int)
