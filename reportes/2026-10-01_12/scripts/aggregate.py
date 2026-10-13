import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
from analysis import *
R=json.load(open('houses_result.json'))
ALERTS=json.load(open('deye_alerts.json'))
GWA=json.load(open('gw_attrs.json'))
HD=[r for r in R if r['has'].get('inv') or r['has'].get('red')]
NODATA=[r for r in R if r not in HD]
def S_(xs): return sum(x for x in xs if x is not None)
def nz(x,d=0): return d if x is None else x
out={}
# ---------------- per-house KPIs ----------------
houses=[]
for r in HD:
    D=r['daily']
    gen=S_(x['gen'] for x in D); imp=S_(x['imp'] for x in D); exp=S_(x['exp'] for x in D); load=S_(x['load'] for x in D)
    dem=gen+imp-exp
    ndays=len([x for x in D if x['gen'] is not None])
    b=r['battery']
    cl=r['cur_load']; 
    imax=max(((p,cl[p]['max'],cl[p]['t_max'],cl[p]['p99']) for p in 'ABC' if cl.get(p)), key=lambda x:x[1], default=None)
    p99max=max((cl[p]['p99'] for p in 'ABC' if cl.get(p)), default=None)
    inom=r['inom_est']
    e=r['e_ph_load']; et=sum(v or 0 for v in e.values())
    shares={p:(100*(e[p] or 0)/et if et else None) for p in 'ABC'}
    dom=max(shares,key=lambda p:shares[p] or 0) if et else None
    vg=r['volt_grid']; vl=r['volt_load']
    vg_hi10=max((vg[p]['hi10'] for p in 'ABC' if vg.get(p)),default=None)
    vg_lo10=max((vg[p]['lo10'] for p in 'ABC' if vg.get(p)),default=None)
    vg_max=max((vg[p]['max'] for p in 'ABC' if vg.get(p)),default=None)
    vg_min=min((vg[p]['min'] for p in 'ABC' if vg.get(p)),default=None)
    vg_avg=(sum(vg[p]['avg'] for p in 'ABC' if vg.get(p))/len([p for p in 'ABC' if vg.get(p)])) if any(vg.get(p) for p in 'ABC') else None
    # backup voltage (load side during outages)
    bvs=[]
    for o in r['outages']:
        if o['dur']<10: continue
        for p in 'ABC':
            bvs+= [x for t,x in ser(r['sol'],'voltage'+p).window(o['ts']+SLOT,o['te']) if x>=90]
    vext=r.get('volt_extreme_grid',[])+r.get('volt_extreme_load',[])
    vext_hi=[x for x in vext if x['v']>=150]
    # current risk
    ratio=(imax[1]/inom) if (imax and inom) else None
    p99r=(p99max/inom) if (p99max and inom) else None
    hi80=nz(r['pct_time_hi80'])
    if ratio is None: cr='Sin dato'
    elif (ratio>=1.0 and hi80>=1) or (p99r or 0)>=0.8: cr='Crítico'
    elif ratio>=0.8 or hi80>=0.5: cr='Alerta'
    elif ratio>=0.6 or ((shares.get(dom) or 0)>=50 and ratio>=0.4): cr='Vigilancia'
    else: cr='Normal'
    if vext_hi: vr='Crítico'
    elif (vg_hi10 or 0)>=5 or (vg_lo10 or 0)>=1: vr='Alerta'
    elif bvs and statistics.median(bvs)>132: vr='Vigilancia'
    else: vr='Normal'
    # outages
    O=r['outages']; sus=[o for o in O if o['dur']>3]
    dur_s=sum(o['dur'] for o in sus); uns=sum(o['unserved'] for o in sus)
    cov=(100*(dur_s-uns)/dur_s) if dur_s else None
    if not sus: br='Sin cortes'
    elif (cov or 0)>=98: br='Normal'
    elif (cov or 0)>=85: br='Vigilancia'
    elif (cov or 0)>=60: br='Alerta'
    else: br='Crítico'
    rank={'Crítico':3,'Alerta':2,'Vigilancia':1,'Normal':0,'Sin dato':0,'Sin cortes':0}
    overall=max([cr,vr,br],key=lambda x:rank[x])
    inv_cov_out=[o for o in sus if o['dur']>=30]
    inv_gap=(100*sum(min(o['inv_samples'],o['inv_expected']) for o in inv_cov_out)/sum(o['inv_expected'] for o in inv_cov_out)) if inv_cov_out else None
    al=[a for a in (ALERTS.get(r['inv']) or []) if isinstance(a,dict)]
    houses.append(dict(
        casa=r['casa'], zone=r['zone'], city=r['city'], utility=r.get('utility'), brand=r['brand'], model=r['model'], invcap=r['invcap'], inv=r['inv'],
        scale=r.get('scale',1), scale_evidence=r.get('scale_evidence'), gen_src=sorted(set(x.get('gen_src') for x in D if x.get('gen_src')!='metrum')),
        gen=gen, imp=imp, exp=exp, load=load, dem=dem, cov=(100*gen/dem if dem>0 else None), selfsuf=(100*(load-imp)/load if load>0 else None),
        gen_day=gen/12, load_day=load/12, imp_day=imp/12, kwh_kw_day=(gen/12/r['invcap'] if r['invcap'] else None),
        losses=dem-load, losses_w=(dem-load)/(12*24)*1000, exp_pct=(100*exp/gen if gen else None),
        peak_load_kw=r['peak_load_kw'], p95_load_kw=r['p95_load_kw'], peak_grid_kw=r['peak_grid_kw'],
        daily=[dict(day=x['day'],gen=x['gen'],imp=x['imp'],exp=x['exp'],load=x['load'],dem=x['dem'],cov=x['cov']) for x in D],
        soc_avg=b['soc_avg'], soc_min=b['soc_min'], soc_max=b['soc_max'], pct_low=b['pct_time_low'], pct_full=b['pct_time_full'],
        cycles=b['cycles_soc'], cycles_day=b['cycles_soc']/12, bch=b['ch_kwh'], bdc=b['dc_kwh'], cap_kwh=b['cap_kwh'], capah=b['capah'], modules=b['modules'],
        vbat=[b['vmin'],b['vmax']], tbat_max=b['tmax'], tbat_avg=b['tavg'], soh=b['soh'], batt_sign=r['batt_sign'],
        grid_charge=r['grid_charge_kwh'], full_daylight=r['full_batt_daylight_pct'],
        imax=imax, inom=inom, imax_ratio=ratio, p99_ratio=p99r, hi80=r['pct_time_hi80'], cur_load=cl, cur_grid=r['cur_grid'], cur_inv=r['cur_inv'],
        shares=shares, dom=dom, e_ph=e, e_ph_imp=r['e_ph_imp'], imb=r['imbalance'],
        vg=vg, vl=vl, vg_hi10=vg_hi10, vg_lo10=vg_lo10, vg_max=vg_max, vg_min=vg_min, vg_avg=vg_avg,
        v_backup=(statistics.median(bvs) if bvs else None), v_backup_max=(max(bvs) if bvs else None), vext=vext,
        risk_current=cr, risk_voltage=vr, risk_backup=br, risk=overall,
        n_out=len(sus), n_trans=len([o for o in O if o['dur']<=3]), out_hours=dur_s/60, unserved_min=uns, backup_cov=cov,
        outages=[{k:o[k] for k in ('start','end','dur','unserved','transfer_min','reconnect_min','mid_events','coverage','status','cause','soc0','soc1','socmin','e_load','p_avg','imax_backup')} for o in O],
        sys_int=r['sys_interruptions'], inv_iso=r['inv_isolated_with_grid'], inv_states=r['inv_states'], inv_faults=r['inv_faults'],
        ev_red=r['events_red'], ev_sol=r['events_sol'], ev_inv=r['events_inv'], deye_alerts=al,
        avail=r['avail'], inv_cov_outage=inv_gap,
        cur_profile=r['cur_profile'],
    ))
# hourly per house (24h avg)
H24={}
for r in HD:
    hp={k:[None]*24 for k in ('load','imp','exp','gen','bch','bdc','soc')}
    for k in hp:
        for hr in range(24):
            vals=[r['hourly'][d*24+hr][k] for d in range(DAYS) if r['hourly'][d*24+hr][k] is not None]
            hp[k][hr]=(sum(vals)/len(vals)) if vals else None
    H24[r['casa']]=hp
# fleet hourly (avg per house, kW) & fleet heatmap (sum, kWh)
fleet24={k:[0.0]*24 for k in ('load','imp','exp','gen','bch','bdc','soc')}
for k in fleet24:
    for hr in range(24):
        vals=[H24[c][k][hr] for c in H24 if H24[c][k][hr] is not None]
        fleet24[k][hr]=sum(vals)/len(vals) if vals else None
heat={k:[[0.0]*24 for _ in range(DAYS)] for k in ('load','imp','gen')}
for r in HD:
    for i,x in enumerate(r['hourly']):
        d,hr=divmod(i,24)
        for k in heat:
            if x[k] is not None: heat[k][d][hr]+=x[k]
# daily fleet
daily=[]
for d in range(DAYS):
    row=dict(day=d+1)
    for k in ('gen','imp','exp','load','dem'):
        row[k]=S_(h['daily'][d][k] for h in houses)
        row['n_'+k]=len([1 for h in houses if h['daily'][d][k] is not None])
    row['cov']=100*row['gen']/row['dem'] if row['dem'] else None
    row['selfsuf']=100*(row['load']-row['imp'])/row['load'] if row['load'] else None
    daily.append(row)
# sectors
sect={}
for h in houses:
    s=sect.setdefault(h['zone'],dict(zone=h['zone'],city=h['city'],utility=h['utility'],n=0,gen=0,imp=0,exp=0,load=0,dem=0,out_h=0,n_out=0,uns=0,dur=0,brands=collections.Counter(),kwkw=[]))
    s['n']+=1
    for k in ('gen','imp','exp','load','dem'): s[k]+=h[k]
    s['n_out']+=h['n_out']; s['out_h']+=h['out_hours']; s['uns']+=h['unserved_min']; s['dur']+=h['out_hours']*60
    s['brands'][h['brand']]+=1
    if h['kwh_kw_day']: s['kwkw'].append(h['kwh_kw_day'])
for s in sect.values():
    s['cov']=100*s['gen']/s['dem'] if s['dem'] else None
    s['selfsuf']=100*(s['load']-s['imp'])/s['load'] if s['load'] else None
    s['gen_house_day']=s['gen']/s['n']/12; s['load_house_day']=s['load']/s['n']/12
    s['backup_cov']=100*(s['dur']-s['uns'])/s['dur'] if s['dur'] else None
    s['saifi']=s['n_out']/s['n']; s['saidi']=s['out_h']/s['n']
    s['kwkw']=sum(s['kwkw'])/len(s['kwkw']) if s['kwkw'] else None
    s['brands']=dict(s['brands'])
# grid events clustered by zone (sustained >3 min)
events=[]
byz=collections.defaultdict(list)
for h in houses:
    for o in h['outages']:
        byz[h['zone']].append((o,h))
for z,lst in byz.items():
    lst.sort(key=lambda x:x[0]['start'])
    cl=[]
    for o,h in lst:
        t=datetime.strptime(o['start'],'%Y-%m-%d %H:%M')
        if cl and (t-cl[-1]['t0']).total_seconds()<=10*60: cl[-1]['items'].append((o,h))
        else: cl.append(dict(t0=t,items=[(o,h)]))
    nz_=len([h for h in houses if h['zone']==z])
    for c in cl:
        its=c['items']; durs=[o['dur'] for o,h in its]
        md=statistics.median(durs)
        unserved_h=[h['casa'] for o,h in its if o['unserved']>2]
        covs=[o['coverage'] for o,h in its if o['coverage'] is not None and o['dur']>3]
        events.append(dict(zone=z,utility=its[0][1]['utility'],start=min(o['start'] for o,h in its),end=max(o['end'] for o,h in its),
            dur_med=md,dur_max=max(durs),n=len(set(h['casa'] for o,h in its)),n_zone=nz_,sustained=md>3,
            unserved_houses=sorted(set(unserved_h)), cov_avg=(sum(covs)/len(covs) if covs else None),
            e_load=S_(o['e_load'] for o,h in its), soc_min=min((o['socmin'] for o,h in its if o['socmin'] is not None),default=None)))
events.sort(key=lambda e:e['start'])
# fleet KPIs
F=dict(n_houses=len(houses), n_nodata=len(NODATA), nodata=[(r['casa'],r['zone']) for r in NODATA])
for k in ('gen','imp','exp','load','dem','bch','bdc','grid_charge'):
    F[k]=sum(h[k] for h in houses)
F['cov']=100*F['gen']/F['dem']; F['selfsuf']=100*(F['load']-F['imp'])/F['load']; F['losses']=F['dem']-F['load']; F['losses_pct']=100*F['losses']/F['gen']
F['exp_pct']=100*F['exp']/F['gen']
F['gen_house_day']=F['gen']/len(houses)/12; F['load_house_day']=F['load']/len(houses)/12
F['kwh_kw_day']=sum(h['kwh_kw_day'] for h in houses if h['kwh_kw_day'])/len([h for h in houses if h['kwh_kw_day']])
F['cap_inv_kw']=sum(h['invcap'] or 0 for h in houses)
F['soc_avg']=sum(h['soc_avg'] for h in houses if h['soc_avg'] is not None)/len([h for h in houses if h['soc_avg'] is not None])
F['cycles_day']=sum(h['cycles_day'] for h in houses)/len(houses)
sus_all=[o for h in houses for o in h['outages'] if o['dur']>3]
F['n_out_house']=len(sus_all); F['n_trans_house']=sum(h['n_trans'] for h in houses)
F['out_hours_house']=sum(o['dur'] for o in sus_all)/60
F['unserved_h']=sum(o['unserved'] for o in sus_all)/60
F['backup_cov']=100*(1-F['unserved_h']/F['out_hours_house']) if F['out_hours_house'] else None
F['saifi']=F['n_out_house']/len(houses); F['saidi']=F['out_hours_house']/len(houses)
F['houses_with_out']=len([h for h in houses if h['n_out']>0])
F['grid_events']=len([e for e in events if e['sustained']]); F['grid_events_trans']=len([e for e in events if not e['sustained']])
F['e_backup']=S_(o['e_load'] for o in sus_all)
for br in ('DEYE','LIVOLTEK'):
    oo=[o for h in houses if h['brand']==br for o in h['outages'] if o['dur']>3]
    d=sum(o['dur'] for o in oo); u=sum(o['unserved'] for o in oo)
    F['backup_cov_'+br]=100*(1-u/d) if d else None; F['n_out_'+br]=len(oo)
    tr=[o['transfer_min'] for o in oo if o['transfer_min']>0]
    F['transfer_med_'+br]=statistics.median(tr) if tr else None
F['risk_counts']={lvl:len([h for h in houses if h['risk']==lvl]) for lvl in ('Crítico','Alerta','Vigilancia','Normal')}
F['avail_inv']=sum(h['avail']['inv'] for h in houses)/len(houses); F['avail_red']=sum(h['avail']['red'] for h in houses)/len(houses); F['avail_sol']=sum(h['avail']['sol'] for h in houses)/len(houses)
F['scaled']=[(h['casa'],h['scale_evidence']) for h in houses if h['scale']!=1]
F['peak_hour_load']=max(range(24),key=lambda i:fleet24['load'][i]); F['peak_hour_imp']=max(range(24),key=lambda i:fleet24['imp'][i])
out=dict(F=F,houses=houses,H24=H24,fleet24=fleet24,heat=heat,daily=daily,sectors=list(sect.values()),events=events)
json.dump(out,open('report_data.json','w'),ensure_ascii=False,default=str)
# print summary
for k,v in F.items():
    if k not in ('nodata','scaled'): print(k, round(v,2) if isinstance(v,float) else v)
print('sectors:'); [print('  ',s['zone'],s['n'],round(s['gen']),round(s['load']),round(s['cov'] or 0,1),s['n_out'],round(s['saidi'],1),round(s['backup_cov'] or 0,1)) for s in sect.values()]
print('events sustained:'); [print('  ',e['zone'],e['start'],e['end'],round(e['dur_med']),e['n'],'/',e['n_zone'],e['unserved_houses'],round(e['cov_avg'] or 0,1)) for e in events if e['sustained']]
print('risk:'); [print('  ',h['casa'],h['risk'],'| I',h['risk_current'],round(h['imax_ratio'] or 0,2),'| V',h['risk_voltage'],'| B',h['risk_backup'],round(h['backup_cov'] or 0,1)) for h in sorted(houses,key=lambda h:h['risk'])]
