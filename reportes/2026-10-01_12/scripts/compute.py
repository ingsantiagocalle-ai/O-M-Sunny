import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
from analysis import *
H=json.load(open('houses.json'))
CAP=json.load(open('battcap.json'))
CLOUD=json.load(open('deye_days.json')) if os.path.exists('deye_days.json') else {}
ALERTS=json.load(open('deye_alerts.json')) if os.path.exists('deye_alerts.json') else {}
GWA=json.load(open('gw_attrs.json')) if os.path.exists('gw_attrs.json') else {}
VNOM=120.0
def nominal_module_v(vmax):
    # LFP 16S modules of 51.2 V nominal; module count from max voltage (~56.5-57 V/module at full charge)
    if not vmax: return None
    n=max(1,round(vmax/56.5))
    return n*51.2, n

def house(h):
    R=dict(utility=GWA.get(h['gw'],{}).get('spdno'),casa=h['casa'],gw=h['gw'],zone=h['zone'],city=h['city'],brand=h['brand'],model=h['model'],invcap=h['invcap'],
           inv=h['inv'],red=h['red'],sol=h['sol'],inv_candidates=h['inv_candidates'],invarray=h['invarray'])
    inv,red,sol=h['inv'],h['red'],h['sol']
    has=lambda d: d and sum(len(v) for v in raw(d).values())>0
    R['has']=dict(inv=bool(has(inv)),red=bool(has(red)),sol=bool(has(sol)))
    if not any(R['has'].values()): return R
    # ---------- availability (15-min slots) ----------
    def avail(dev,key):
        s=ser(dev,key); slots=set((t-T0ms)//SLOT for t in s.t if T0ms<=t<TEND); return round(100*len(slots)/NSLOT,1)
    R['avail']=dict(inv=avail(inv,'BattSOC'),red=avail(red,'voltageA'),sol=avail(sol,'voltageA'))
    # ---------- daily energy from closings ----------
    cg=closings(inv,'CenergyAE'); ci=closings(red,'CenergyAI'); ce=closings(red,'CenergyAE'); cl=closings(sol,'CenergyAI'); cle=closings(sol,'CenergyAE')
    # fallback: cumulative interval series interpolated at midnight
    fb=dict(g=ser(inv,'energyAE'), i=ser(red,'energyAI'), e=ser(red,'energyAE'), l=ser(sol,'energyAI'))
    for c,f in ((cg,'g'),(ci,'i'),(ce,'e'),(cl,'l')):
        for k in c:
            if c[k] is None: c[k]=fb[f].at(T0ms+k*DAY, maxgap=3*HOUR)
    pd=ser(inv,'energyPD')
    # --- detección de escala x0.1 en contadores de energía del inversor (validada con DeyeCloud / balance de medidores)
    SCALE=1; R['scale_evidence']=None
    if h['brand']=='DEYE' and inv:
        gsum=sum((cg[k+1]-cg[k]) for k in range(DAYS) if cg.get(k) is not None and cg.get(k+1) is not None)/1000.0
        lsum=sum((cl[k+1]-cl[k]) for k in range(DAYS) if cl.get(k) is not None and cl.get(k+1) is not None)/1000.0
        isum=sum((ci[k+1]-ci[k]) for k in range(DAYS) if ci.get(k) is not None and ci.get(k+1) is not None)/1000.0
        csum=sum((x.get('Production') or 0) for x in (CLOUD.get(inv) or []) if isinstance(x,dict))
        meter_solar=lsum-isum
        if gsum>0 and csum>0 and 0.08<gsum/csum<0.13:
            SCALE=10; R['scale_evidence']=dict(tipo='Metrum x0,1 vs DeyeCloud', metrum=round(gsum,1), deyecloud=round(csum,1), ratio=round(gsum/csum,3), solar_medidores=round(meter_solar,1))
        elif gsum>0 and meter_solar/gsum>4:
            SCALE=10; R['scale_evidence']=dict(tipo='Contador del inversor x0,1 (Metrum = DeyeCloud) vs balance de medidores', metrum=round(gsum,1), deyecloud=round(csum,1), ratio=round(gsum/meter_solar,3), solar_medidores=round(meter_solar,1))
    R['scale']=SCALE
    daily=[]
    flags=[]
    for d in range(DAYS):
        def delta(c, floor=True, name=''):
            a,b=c.get(d),c.get(d+1)
            if a is None or b is None: return None
            x=b-a
            if x<0 and floor:
                flags.append(f'{name} delta negativo día {d+1}'); return None
            return x/1000.0
        g=delta(cg,name='gen'); i=delta(ci,name='imp'); e=delta(ce,floor=False); l=delta(cl,name='carga')
        # PV daily counter: last value before midnight (A.5)
        tmid=T0ms+(d+1)*DAY
        w=[x for t,x in pd.window(T0ms+d*DAY+3*HOUR, tmid)]
        pvd=(w[-1]/1000.0) if w else None
        src='metrum'
        if g is None and pvd is not None: g=pvd; src='metrum-energyPD'
        cloud=None
        for x in (CLOUD.get(inv) or []):
            if isinstance(x,dict) and x.get('date')==f'2026-10-{d+1:02d}': cloud=x.get('Production')
        if (g is None or src=='metrum-energyPD') and cloud is not None and SCALE==1: g=cloud; src='deyecloud'
        if g is not None: g*=SCALE
        if pvd is not None: pvd*=SCALE
        dem=(g+i-(e or 0)) if (g is not None and i is not None) else None
        daily.append(dict(day=d+1,gen=g,gen_src=src,cloud=cloud,pv_counter=pvd,imp=i,exp=e,load=l,dem=dem,
                          cov=(100*g/dem if (g is not None and dem and dem>0) else None),
                          selfsuf=(100*(l-i)/l if (l and i is not None and l>0) else None)))
    R['daily']=daily; R['flags']=flags
    # ---------- hourly profiles (288 h) ----------
    sl=ser(sol,'energyAI'); si=ser(red,'energyAI'); se=ser(red,'energyAE'); sg=ser(inv,'energyAE')
    # battery: normalized + = charge; sign determined from SOC correlation
    bp=ser(inv,'BattPower'); soc=ser(inv,'BattSOC')
    agree=0; tot=0
    for k in range(len(bp.t)):
        t=bp.t[k]; p=bp.v[k]
        s1=soc.at(t,exact_tol=2*MIN,maxgap=0); s2=soc.after(t+10*MIN, maxage=25*MIN)
        if s1 is None or s2 is None or abs(p)<500 or s2==s1: continue
        tot+=1; agree+= (p>0)==(s2>s1)
    sign = 1 if (tot and agree/tot>=0.5) else -1
    R['batt_sign']=dict(sign=('+ = carga' if sign==1 else '+ = descarga'), agree=round(100*max(agree,tot-agree)/tot,1) if tot else None, n=tot)
    hourly=[]
    for hh in range(DAYS*24):
        a=T0ms+hh*HOUR; b=a+HOUR
        def dE(s,mg=2*HOUR):
            x1=s.at(a,maxgap=mg); x2=s.at(b,maxgap=mg)
            if x1 is None or x2 is None: return None
            x=(x2-x1)/1000.0
            return x if x>-0.05 else None
        load=dE(sl); imp=dE(si); exp=dE(se); gen=dE(sg,3*HOUR)
        if gen is not None: gen*=SCALE
        # battery integration
        ch=dc=0.0; n=0
        for t,p in bp.window(a,b):
            p*=sign; n+=1
            e=p*0.25/1000.0
            if e>0: ch+=e
            else: dc+=-e
        socw=[x for t,x in soc.window(a,b)]
        hourly.append(dict(load=load,imp=imp,exp=exp,gen=gen,bch=ch if n else None,bdc=dc if n else None,soc=(sum(socw)/len(socw) if socw else None)))
    R['hourly']=hourly
    pl=[x for t,x in ser(sol,'powerAI').window(T0ms,TEND)]; pg=[x for t,x in ser(red,'powerAI').window(T0ms,TEND)]
    R['peak_load_kw']=(max(pl)/1000.0 if pl else None); R['peak_grid_kw']=(max(pg)/1000.0 if pg else None)
    R['p95_load_kw']=(pct(pl,95)/1000.0 if pl else None)
    gch=0.0; full=0; dayh=0
    for k,x in enumerate(hourly):
        hr=k%24
        if x['imp'] is not None and x['bch'] is not None and (x['gen'] or 0)<0.05:
            gch+=min(x['imp'],x['bch'])
        if 8<=hr<16 and x['soc'] is not None:
            dayh+=1
            if x['soc']>=98 and (x['exp'] or 0)<0.05: full+=1
    R['grid_charge_kwh']=gch; R['full_batt_daylight_pct']=(100*full/dayh if dayh else None)
    # ---------- battery ----------
    socv=[x for t,x in soc.window(T0ms,TEND)]
    drops=sum(max(0,a-b) for (a,b) in zip(socv,socv[1:]))
    bv=[x for t,x in ser(inv,'BattVolt').window(T0ms,TEND) if x>0]
    bt=[x for t,x in ser(inv,'BattTemp').window(T0ms,TEND) if -10<x<80]
    soh=[x for t,x in ser(inv,'BattSOH').window(T0ms,TEND)]
    capah=None
    cc=CAP.get(h['casa'],{})
    for k in ('BattCapAH_DY','BattCapAH_LV'):
        if cc.get(k): capah=float(cc[k])
    vb=sorted(bv)
    vmed=statistics.median(bv) if bv else None
    nm=((max(1,round(vmed/51.5))*51.2, max(1,round(vmed/51.5))) if vmed else None)
    capkwh=(capah*nm[0]/1000.0) if (capah and nm) else None
    dsoc=[]
    for d in range(DAYS):
        w=[x for t,x in soc.window(T0ms+d*DAY,T0ms+(d+1)*DAY)]
        dsoc.append(dict(min=min(w) if w else None,max=max(w) if w else None,avg=(sum(w)/len(w) if w else None)))
    tot_ch=sum(x['bch'] or 0 for x in hourly); tot_dc=sum(x['bdc'] or 0 for x in hourly)
    floor_soc=min(socv) if socv else None
    R['battery']=dict(soc_avg=(sum(socv)/len(socv) if socv else None), soc_min=floor_soc, soc_max=max(socv) if socv else None,
        pct_time_low=(100*sum(1 for x in socv if x<=21)/len(socv) if socv else None),
        pct_time_full=(100*sum(1 for x in socv if x>=98)/len(socv) if socv else None),
        cycles_soc=drops/100.0, ch_kwh=tot_ch, dc_kwh=tot_dc, capah=capah, vnom=(nm[0] if nm else None), modules=(nm[1] if nm else None),
        cap_kwh=capkwh, vmin=min(bv) if bv else None, vmax=max(bv) if bv else None, tmax=max(bt) if bt else None, tavg=(sum(bt)/len(bt) if bt else None),
        soh=(statistics.median(soh) if soh else None), soh_min=min(soh) if soh else None, daily=dsoc)
    # ---------- phases ----------
    def phase_stats(dev, prefix='current'):
        out={}
        for ph in 'ABC':
            s=ser(dev,prefix+ph); w=s.window(T0ms,TEND)
            if not w: out[ph]=None; continue
            vals=[x for t,x in w]
            tm,vm=max(w,key=lambda p:p[1])
            out[ph]=dict(max=vm,t_max=hm(tm),p95=pct(vals,95),p99=pct(vals,99),avg=sum(vals)/len(vals))
        return out
    R['cur_load']=phase_stats(sol,'current'); R['cur_grid']=phase_stats(red,'current'); R['cur_inv']=phase_stats(inv,'current')
    # per-phase energy
    def ph_energy(dev,key):
        o={}
        for ph in 'ABC':
            c=closings(dev,key+'ph'+ph)
            o[ph]=((c[DAYS]-c[0])/1000.0) if (c.get(0) is not None and c.get(DAYS) is not None) else None
        return o
    R['e_ph_load']=ph_energy(sol,'CenergyAI'); R['e_ph_imp']=ph_energy(red,'CenergyAI'); R['e_ph_exp']=ph_energy(red,'CenergyAE')
    # imbalance on load currents
    ia,ib,ic=ser(sol,'currentA'),ser(sol,'currentB'),ser(sol,'currentC')
    imb=[]; inom=(h['invcap']*1000/(3*127.0)) if h['invcap'] else None; hi80=0; nall=0
    hourly_ph={ph:[0.0]*24 for ph in 'ABC'}; hourly_n=[0]*24
    for k,t in enumerate(ia.t):
        if not (T0ms<=t<TEND): continue
        a=ia.v[k]; b=ib.at(t,exact_tol=2*MIN,maxgap=0); c=ic.at(t,exact_tol=2*MIN,maxgap=0)
        if b is None or c is None: continue
        nall+=1
        hr=datetime.fromtimestamp(t/1000,COT).hour
        hourly_ph['A'][hr]+=a; hourly_ph['B'][hr]+=b; hourly_ph['C'][hr]+=c; hourly_n[hr]+=1
        m=max(a,b,c); avg=(a+b+c)/3
        if inom and m>=0.8*inom: hi80+=1
        if m>=3 and avg>0: imb.append(100*max(abs(a-avg),abs(b-avg),abs(c-avg))/avg)
    R['cur_profile']={ph:[(hourly_ph[ph][i]/hourly_n[i] if hourly_n[i] else None) for i in range(24)] for ph in 'ABC'}
    R['imbalance']=dict(avg=(sum(imb)/len(imb) if imb else None),p95=pct(imb,95),n=len(imb))
    R['inom_est']=inom; R['pct_time_hi80']=(100*hi80/nall if nall else None)
    # voltages
    def volt_stats(dev, excl=()):
        out={}
        for ph in 'ABC':
            w=[x for t,x in ser(dev,'voltage'+ph).window(T0ms,TEND) if x>=5 and not any(a-SLOT<=t<=b+SLOT for a,b in excl)]
            if not w: out[ph]=None; continue
            out[ph]=dict(min=min(w),max=max(w),avg=sum(w)/len(w),p1=pct(w,1),p99=pct(w,99),
                         lo10=100*sum(1 for x in w if x<108)/len(w), hi10=100*sum(1 for x in w if x>132)/len(w),
                         lo5=100*sum(1 for x in w if x<114)/len(w), hi5=100*sum(1 for x in w if x>126)/len(w), n=len(w))
        return out
    R['volt_grid']=volt_stats(red); R['volt_load']=volt_stats(sol)
    def volt_events(dev, thr_hi=150, thr_lo=90, excl=()):
        ev=[]
        for ph in 'ABC':
            for t,x in ser(dev,'voltage'+ph).window(T0ms,TEND):
                if any(a-SLOT<=t<=b+SLOT for a,b in excl): continue
                if x>=thr_hi or (5<=x<thr_lo): ev.append(dict(t=hm(t),ph=ph,v=x))
        return ev
    # ---------- interruptions ----------
    ev_red=[(t,x) for t,x in raw(red).get('event',[]) if isinstance(x,str)] if red else []
    ev_sol=[(t,x) for t,x in raw(sol).get('event',[]) if isinstance(x,str)] if sol else []
    R['events_red']=collections.Counter(x for t,x in ev_red if T0ms<=t<TEND)
    R['events_sol']=collections.Counter(x for t,x in ev_sol if T0ms<=t<TEND)
    R['events_inv']=collections.Counter(x for t,x in raw(inv).get('event',[]) if isinstance(x,str) and T0ms<=t<TEND) if inv else {}
    # grid down from events
    giv=intervals_from_events([(t,x) for t,x in ev_red if T0ms-DAY<=t<TEND+DAY])
    # complete open intervals with voltage samples
    va,vb_,vc=ser(red,'voltageA'),ser(red,'voltageB'),ser(red,'voltageC')
    def grid_up(t):
        a=va.at(t,exact_tol=2*MIN,maxgap=0); b=vb_.at(t,exact_tol=2*MIN,maxgap=0); c=vc.at(t,exact_tol=2*MIN,maxgap=0)
        if a is None: return None
        return max(a,b or 0,c or 0)>=5
    fixed=[]
    for a,b in giv:
        if b is None:
            # find first up sample after a
            bb=None
            for t in va.t:
                if t>a and grid_up(t): bb=t; break
            b=bb or TEND
        fixed.append([a,b])
    # slots down without event coverage
    for t in va.t:
        if T0ms<=t<TEND and grid_up(t) is False and not any(a-2*MIN<=t<=b+2*MIN for a,b in fixed):
            fixed.append([t-SLOT//2,t+SLOT//2])
    fixed=[[max(a,T0ms),min(b,TEND)] for a,b in fixed if b>T0ms and a<TEND]
    raw_iv=sorted(fixed)
    R['grid_raw_events']=len(raw_iv)
    cons=merge([list(x) for x in raw_iv],10*MIN)
    # load-side interruptions (sol meter po/pr + voltage)
    liv=intervals_from_events([(t,x) for t,x in ev_sol if T0ms-DAY<=t<TEND+DAY])
    la,lb,lc=ser(sol,'voltageA'),ser(sol,'voltageB'),ser(sol,'voltageC')
    def load_up(t):
        a=la.at(t,exact_tol=2*MIN,maxgap=0); b=lb.at(t,exact_tol=2*MIN,maxgap=0); c=lc.at(t,exact_tol=2*MIN,maxgap=0)
        if a is None: return None
        return max(a,b or 0,c or 0)>=5
    lfix=[]
    for a,b in liv:
        if b is None:
            bb=None
            for t in la.t:
                if t>a and load_up(t): bb=t; break
            b=bb or TEND
        lfix.append([a,b])
    for t in la.t:
        if T0ms<=t<TEND and load_up(t) is False and not any(a-2*MIN<=t<=b+2*MIN for a,b in lfix):
            lfix.append([t-SLOT//2,t+SLOT//2])
    lfix=sorted([[max(a,T0ms),min(b,TEND)] for a,b in lfix if b>T0ms and a<TEND])
    outages=[]
    cur_l=[ser(sol,'current'+p) for p in 'ABC']
    for a,b in cons:
        dur=(b-a)/MIN
        ov=[(x,y) for x,y in lfix if overlap(a-2*MIN,b+5*MIN,x,y)>0]
        transfer=[(x,y) for x,y in ov if a-2*MIN<=x<=a+3*MIN]
        reconn=[(x,y) for x,y in ov if b-3*MIN<=x<=b+5*MIN and (x,y) not in transfer]
        mid=[(x,y) for x,y in ov if (x,y) not in transfer and (x,y) not in reconn]
        unserved=sum(overlap(a,b,x,y) for x,y in ov)/MIN
        tr_min=sum(y-x for x,y in transfer)/MIN
        rc_min=sum(y-x for x,y in reconn)/MIN
        mid_long=[(x,y) for x,y in mid if (y-x)>2*MIN]
        s0=soc.before(a,maxage=45*MIN); s1=soc.after(b,maxage=45*MIN)
        sw=[x for t,x in soc.window(a,b+1)]
        cand=[x for x in [s0,s1]+sw if x is not None]
        smin=min(cand) if cand else None
        e_load=None
        x1=sl.at(a,maxgap=40*MIN); x2=sl.at(b,maxgap=40*MIN)
        if x1 is not None and x2 is not None: e_load=(x2-x1)/1000.0
        inv_cov=len([t for t in bp.t if a<=t<=b])
        exp_slots=max(1,int((b-a)//SLOT))
        imax=None
        for p,s in zip('ABC',cur_l):
            for t,x in s.window(a,b):
                if imax is None or x>imax[1]: imax=(p,x)
        cov=100*max(0,dur-unserved)/dur if dur>0 else None
        if dur<=3: status='transitoria'
        elif unserved<=2: status='respaldo total'
        elif unserved<0.5*dur: status='respaldo con interrupciones'
        else: status='sin respaldo'
        cause=None
        if unserved>2:
            if s0==0 and (s1 in (0,None)): cause='batería fuera de servicio (SOC 0 %)'
            elif s0 is not None and s0<=25 and smin is not None and smin<=16: cause='batería en límite de descarga'
            elif tr_min>2 and not mid_long: cause='transferencia lenta'
            elif mid_long: cause='cortes/reinicios durante respaldo'
            else: cause='indeterminada'
        outages.append(dict(start=iso(a),end=iso(b),ts=a,te=b,dur=round(dur,1),unserved=round(unserved,1),transfer_min=round(tr_min,1),
            reconnect_min=round(rc_min,1),mid_events=len(mid),mid_long=len(mid_long),coverage=cov,status=status,cause=cause,
            soc0=s0,soc1=s1,socmin=smin,e_load=e_load,p_avg=(e_load/(dur/60) if (e_load is not None and dur>=10) else None),
            imax_backup=imax, inv_samples=inv_cov, inv_expected=exp_slots))
    R['outages']=outages
    EX=[(o['ts'],o['te']) for o in outages]
    R['volt_grid']=volt_stats(red,EX); R['volt_load']=volt_stats(sol,EX)
    R['volt_extreme_grid']=volt_events(red,excl=EX); R['volt_extreme_load']=volt_events(sol,excl=EX)
    # load interruptions without grid outage (system-side)
    sysint=[]
    for x,y in lfix:
        if any(overlap(x,y,a-3*MIN,b+3*MIN)>0 for a,b in cons): continue
        sysint.append(dict(start=iso(x),end=iso(y),dur=round((y-x)/MIN,1)))
    R['sys_interruptions']=sysint
    # inverter grid-port loss while grid meter has voltage (possible breaker trip / inverter-side isolation)
    vg=[ser(inv,'voltGrid'+p) for p in 'ABC']
    iso_slots=0; iso_list=[]
    for k,t in enumerate(vg[0].t):
        if not(T0ms<=t<TEND): continue
        vals=[vg[0].v[k]]+[s.at(t,exact_tol=2*MIN,maxgap=0) for s in vg[1:]]
        if any(v is None for v in vals): continue
        if max(vals)<5 and grid_up(t):
            iso_slots+=1; iso_list.append(t)
    R['inv_isolated_with_grid']=dict(slots=iso_slots, first=(hm(iso_list[0]) if iso_list else None), last=(hm(iso_list[-1]) if iso_list else None))
    # inverter faults
    runs=[(t,x) for t,x in raw(inv).get('invrun',[]) if T0ms<=t<TEND] if inv else []
    R['inv_states']=collections.Counter(x for t,x in runs)
    R['inv_faults']=[dict(t=hm(t),state=x) for t,x in runs if x in ('fault','alarm')]
    return R

if __name__=='__main__':
    out=[]
    for h in H:
        r=house(h); out.append(r)
        if r['has'].get('inv') or r['has'].get('red'):
            g=sum(x['gen'] or 0 for x in r['daily']); i=sum(x['imp'] or 0 for x in r['daily']); l=sum(x['load'] or 0 for x in r['daily'])
            print(f"{r['casa']:16s} gen={g:7.1f} imp={i:7.1f} load={l:7.1f} outages={len(r['outages'])} sysint={len(r['sys_interruptions'])} sign={r['batt_sign']} flags={r['flags'][:3]}")
        else:
            print(r['casa'],'SIN DATOS')
    json.dump(out,open('houses_result.json','w'),ensure_ascii=False,default=str)
