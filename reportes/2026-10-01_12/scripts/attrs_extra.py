# Lee capacidad de batería (Ah) por inversor y el operador de red de cada gateway. Solo lectura.
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
import metrum
H = json.load(open('houses.json')); cap = {}
for h in H:
    if not h['inv_id']: continue
    r = metrum.get(f"/api/plugins/telemetry/DEVICE/{h['inv_id']}/values/timeseries?keys=BattCapAH_DY,BattCapAH_LV")
    cap[h['casa']] = {k: v[0]['value'] for k, v in (r or {}).items() if v}
json.dump(cap, open('battcap.json', 'w'))
rows = json.load(open('inventory.json')); gw = {}
for r in rows:
    if r['type'] != 'pulsar': continue
    a = metrum.get(f"/api/plugins/telemetry/DEVICE/{r['id']}/values/attributes/SERVER_SCOPE?keys=spdno,spcom,spcus,zone,city")
    gw[r['name']] = {x['key']: x['value'] for x in a}
json.dump(gw, open('gw_attrs.json', 'w'), ensure_ascii=False)
