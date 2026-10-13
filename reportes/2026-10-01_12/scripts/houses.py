import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import json, collections, os
from util import load
rows=json.load(open('inventory.json'))
gws={r['name']:r for r in rows if r['type']=='pulsar'}
def nonzero(name):
    fn=f'raw/{name}.json'
    if not os.path.exists(fn): return 0
    d=json.load(open(fn)); return sum(len(v) for v in d.values())
def build():
    by=collections.defaultdict(list)
    for r in rows:
        if r['type']!='pulsar': by[r.get('gateway')].append(r)
    H=[]
    for g,G in gws.items():
        devs=by.get(g,[])
        invs=[d for d in devs if d['type']=='inverter']
        # A.9: choose inverter with moving CenergyAE in range
        best=None
        for d in invs:
            fn=f"raw/{d['name']}.json"
            if not os.path.exists(fn): continue
            dd=load(d['name'])
            ce=[x for _,x in dd.get('CenergyAE',[]) if isinstance(x,float)]
            if len(ce)>=2 and ce[-1]-ce[0]>0:
                best=d; break
        if best is None and invs: best=invs[0]
        red=[d for d in devs if d.get('mettype')=='red']
        sol=[d for d in devs if d.get('mettype')=='solar']
        H.append(dict(gw=g, casa=G.get('spcus'), zone=G.get('zone'), city=G.get('city'), dept=G.get('dept'),
            inv=best['name'] if best else None, inv_id=best['id'] if best else None,
            brand=(best or {}).get('invbrand') or ('LIVOLTEK' if (best or {}).get('name','').startswith('HP') else 'DEYE'),
            model=((best or {}).get('invmodel') or '').strip(), invcap=float((best or {}).get('invcap') or 0) or None,
            invarray=(best or {}).get('invarray'),
            inv_candidates=[d['name'] for d in invs],
            red=red[0]['name'] if red else None, sol=sol[0]['name'] if sol else None))
    return H
if __name__=='__main__':
    H=build()
    json.dump(H,open('houses.json','w'),ensure_ascii=False,indent=1)
    for h in sorted(H,key=lambda h:(h['zone'] or '',h['casa'] or '')):
        print(h['gw'],h['casa'],h['zone'],h['inv'],h['brand'],h['model'],h['invcap'],h['red'],nonzero(h['red']) if h['red'] else '-',h['sol'],nonzero(h['sol']) if h['sol'] else '-', nonzero(h['inv']) if h['inv'] else '-', h['inv_candidates'] if len(h['inv_candidates'])>1 else '')
