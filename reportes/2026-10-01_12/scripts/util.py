import json
from datetime import datetime, timezone, timedelta
COT = timezone(timedelta(hours=-5))
def load(name):
    d=json.load(open(f'raw/{name}.json'))
    out={}
    for k,v in d.items():
        s=[]
        for p in v:
            try: s.append((p['ts'], float(p['value'])))
            except: s.append((p['ts'], p['value']))
        s.sort()
        out[k]=s
    return out
def lt(ts): return datetime.fromtimestamp(ts/1000, COT)
