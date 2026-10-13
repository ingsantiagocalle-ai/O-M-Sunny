import sys, json; sys.path.insert(0,'.')
import metrum
ATTRS=['mettype','gateway','spcus','zone','city','dept','invbrand','invmodel','invcap','invarray','invtype','model','BattSn','active','spgwserie','latch_state','latch_output','IU','VU']
rows=[]; page=0
while True:
    body={"entityFilter":{"type":"entityType","entityType":"DEVICE"},
          "pageLink":{"pageSize":100,"page":page},
          "entityFields":[{"type":"ENTITY_FIELD","key":"name"},{"type":"ENTITY_FIELD","key":"type"},{"type":"ENTITY_FIELD","key":"createdTime"}],
          "latestValues":[{"type":"ATTRIBUTE","key":k} for k in ATTRS]}
    r=metrum.post('/api/entitiesQuery/find',body)
    for d in r['data']:
        rec={'id':d['entityId']['id']}
        for grp in d['latest'].values():
            for k,v in grp.items():
                rec[k]=v.get('value')
        rows.append(rec)
    if not r.get('hasNext'): break
    page+=1
json.dump(rows,open('inventory.json','w'),ensure_ascii=False,indent=1)
print(len(rows))
