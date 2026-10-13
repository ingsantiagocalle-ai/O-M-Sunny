import sys, json, os, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'.')
import metrum
from datetime import datetime, timezone, timedelta
START = int(datetime(2026,9,30,5,0,tzinfo=timezone.utc).timestamp()*1000)   # 30-sep 00:00 COT
END   = int(datetime(2026,10,13,7,0,tzinfo=timezone.utc).timestamp()*1000)  # 13-oct 02:00 COT (endTs exclusivo + margen)
INV_KEYS = ['CenergyAE','energyAE','energyPD','energyLD','energyID','energyED','energyET','energyIT','energyLT',
            'BattSOC','BattPower','BattCur','BattVolt','BattTemp','BattSOH','voltGridA','voltGridB','voltGridC',
            'voltageA','voltageB','voltageC','currentA','currentB','currentC','curGridA','curGridB','curGridC',
            'voltEpsA','voltEpsB','voltEpsC','curEpsA_LV','curEpsB_LV','curEpsC_LV','invrun','invstate','powerAEg','powerAPg','powerAE',
            'frequency','freqEps','event','activityState','LoadPower_DY','LoadPower_LV','ExportGrid_LV','BattStateOp_LV','powerPFg_LV','powerREg_LV','powerAEgdc_LV']
MET_KEYS = ['CenergyAI','CenergyAE','CenergyRI','CenergyRE','energyAI','energyAE','energyRI','currentA','currentB','currentC',
            'voltageA','voltageB','voltageC','powerAI','powerAE','powerRI','powerRE','FlagStaProf','event','activityState',
            'energyAIphA','energyAIphB','energyAIphC','energyAEphA','energyAEphB','energyAEphC','CenergyAIphA','CenergyAIphB','CenergyAIphC',
            'CenergyAEphA','CenergyAEphB','CenergyAEphC']
os.makedirs('raw',exist_ok=True)
def fetch(dev):
    fn=f"raw/{dev['name']}.json"
    if os.path.exists(fn): return dev['name'],'cached'
    keys = INV_KEYS if dev['type']=='inverter' else MET_KEYS
    out={}
    # split keys in chunks to keep responses moderate
    for i in range(0,len(keys),12):
        ks=','.join(keys[i:i+12])
        r=metrum.get(f"/api/plugins/telemetry/DEVICE/{dev['id']}/values/timeseries?keys={ks}&startTs={START}&endTs={END}&agg=NONE&limit=20000&orderBy=ASC")
        out.update(r or {})
    json.dump(out,open(fn,'w'))
    return dev['name'], sum(len(v) for v in out.values())
if __name__=='__main__':
    rows=json.load(open('inventory.json'))
    devs=[r for r in rows if r['type'] in ('inverter','meter')]
    metrum.login()
    with ThreadPoolExecutor(4) as ex:
        for name,n in ex.map(fetch,devs):
            print(name,n,flush=True)
