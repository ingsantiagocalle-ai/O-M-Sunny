import sys, os, json, math, bisect, collections, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from util import COT
from datetime import datetime, timedelta, timezone

T0 = datetime(2026,10,1,tzinfo=COT); T0ms = int(T0.timestamp()*1000)
DAYS=12; MIN=60000; SLOT=15*MIN; HOUR=60*MIN; DAY=24*HOUR
TEND = T0ms + DAYS*DAY
NSLOT = DAYS*96
def iso(t): return datetime.fromtimestamp(t/1000,COT).strftime('%Y-%m-%d %H:%M')
def hm(t): return datetime.fromtimestamp(t/1000,COT).strftime('%d-oct %H:%M')

_cache={}
def raw(name):
    if name in _cache: return _cache[name]
    fn=f'raw/{name}.json'
    d=json.load(open(fn)) if os.path.exists(fn) else {}
    out={}
    for k,v in d.items():
        s=[]
        for p in v:
            val=p['value']
            try:
                f=float(val)
                if math.isfinite(f): val=f
            except: pass
            s.append((p['ts'],val))
        s.sort(key=lambda x:x[0])
        out[k]=s
    _cache[name]=out
    return out

class S:
    """numeric series helper"""
    def __init__(self, pts):
        pts=[(t,x) for t,x in pts if isinstance(x,float)]
        self.t=[p[0] for p in pts]; self.v=[p[1] for p in pts]
    def __len__(self): return len(self.t)
    def at(self, t, maxgap=2*HOUR, exact_tol=0):
        i=bisect.bisect_left(self.t,t)
        if i<len(self.t) and abs(self.t[i]-t)<=exact_tol: return self.v[i]
        if i>0 and abs(self.t[i-1]-t)<=exact_tol: return self.v[i-1]
        if i==0 or i==len(self.t): return None
        t1,t2=self.t[i-1],self.t[i]
        if t2-t1>maxgap: return None
        v1,v2=self.v[i-1],self.v[i]
        return v1+(v2-v1)*(t-t1)/(t2-t1)
    def before(self, t, maxage=2*HOUR):
        i=bisect.bisect_right(self.t,t)-1
        if i<0 or t-self.t[i]>maxage: return None
        return self.v[i]
    def after(self, t, maxage=2*HOUR):
        i=bisect.bisect_left(self.t,t)
        if i>=len(self.t) or self.t[i]-t>maxage: return None
        return self.v[i]
    def window(self, a, b):
        i=bisect.bisect_left(self.t,a); j=bisect.bisect_left(self.t,b)
        return list(zip(self.t[i:j],self.v[i:j]))

def ser(dev,key): return S(raw(dev).get(key,[])) if dev else S([])

def closings(dev,key):
    """closing values at T0 + k days, k=0..DAYS (snapshot 00:00 COT). Falls back to cumulative interval key."""
    s=ser(dev,key)
    out={}
    for k in range(0,DAYS+1):
        t=T0ms+k*DAY
        v=s.at(t, exact_tol=20*MIN, maxgap=0)
        out[k]=v
    return out

def pct(xs,p):
    xs=sorted(xs)
    if not xs: return None
    i=(len(xs)-1)*p/100; lo=math.floor(i); hi=math.ceil(i)
    return xs[lo]+(xs[hi]-xs[lo])*(i-lo)

def intervals_from_events(evs, start_code='po', end_code='pr', t_end=TEND):
    """pairs po->pr into intervals (ms)"""
    out=[]; cur=None
    for t,x in evs:
        if x==start_code:
            if cur is None: cur=t
        elif x==end_code:
            if cur is not None:
                out.append([cur,t]); cur=None
    if cur is not None: out.append([cur,None])
    return out

def merge(iv, gap):
    iv=sorted(iv)
    out=[]
    for a,b in iv:
        if out and a-out[-1][1]<=gap: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return out

def overlap(a,b,c,d): return max(0,min(b,d)-max(a,c))
