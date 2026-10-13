import sys, json, subprocess, os
H=json.load(open('houses.json'))
S='/home/user/O-M-Sunny/.claude/skills/om-agency/scripts/deye_adapter.py'
out={}
for h in H:
    if h['brand']!='DEYE' or not h['inv']: continue
    r=subprocess.run([sys.executable,'-I',S,'days',h['inv'],'2026-10-01','2026-10-12'],capture_output=True,text=True,timeout=120)
    try: out[h['inv']]=json.loads(r.stdout)
    except Exception: out[h['inv']]={'error':(r.stdout+r.stderr)[-300:]}
    print(h['casa'],h['inv'], 'ok' if isinstance(out[h['inv']],list) else out[h['inv']])
json.dump(out,open('deye_days.json','w'))
