"""Capa de datos Metrum para el reporte diario: inventario, series temporales y concurrencia.

El inventario (dispositivos y casas) se refresca desde Metrum en cada corrida; solo se guardan los
seriales de los medidores de cada gateway (el atributo `meter` trae claves de acceso: nunca se
conserva ni se imprime). La caché de series en disco es opcional (OM_REPORT_CACHE=<dir>) y solo
sirve para desarrollo: un reporte final debe consultar datos frescos.
"""
from __future__ import annotations

import ast
import concurrent.futures as cf
import datetime
import hashlib
import json
import os

import metrum

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'assets')
CACHE = os.environ.get('OM_REPORT_CACHE')
if CACHE:
    os.makedirs(CACHE, exist_ok=True)

UTC = datetime.timezone.utc
TZ = -5 * 3600 * 1000          # UTC-5 (Colombia)

# Atributos que se leen de cada dispositivo (lista blanca; no incluye claves de acceso)
ATTRS = ['spcus', 'mettype', 'gateway', 'city', 'zone', 'invbrand', 'invmodel', 'invcap', 'invarray', 'invtype',
         'active', 'meter']
# Sistemas excluidos: pilotos que no son casas de la flota
EXCLUIDOS = {'Piloto Promigas', 'Piloto HUAWEI'}

# kWp, equipo y ciudad por casa: dato externo a Metrum (archivo de sistemas del equipo)
SYSTEMS = json.load(open(os.path.join(ASSETS, 'systems.json'), encoding='utf-8'))

DEVS: list[dict] = []
BY: dict[str, dict] = {}


def utc_ms(y, mo, d, h=0, mi=0, s=0):
    return int(datetime.datetime(y, mo, d, h, mi, s, tzinfo=UTC).timestamp() * 1000)


def local_ms(y, mo, d, h=0, mi=0, s=0):
    """Instante dado en hora local (UTC-5) -> epoch ms."""
    return utc_ms(y, mo, d, h, mi, s) - TZ


def fmt_local(t, f='%d %H:%M:%S'):
    return datetime.datetime.fromtimestamp((t + TZ) / 1000, UTC).strftime(f)


def refresh_inventory():
    """Lee todos los dispositivos de Metrum (paginando hasta hasNext=false) y llena DEVS/BY."""
    devs, page = [], 0
    while True:
        r = metrum.post('/api/entitiesQuery/find', {
            'entityFilter': {'type': 'entityType', 'entityType': 'DEVICE'},
            'pageLink': {'pageSize': 100, 'page': page},
            'entityFields': [{'type': 'ENTITY_FIELD', 'key': 'name'}, {'type': 'ENTITY_FIELD', 'key': 'type'}],
            'latestValues': [{'type': 'ATTRIBUTE', 'key': k} for k in ATTRS]})
        for row in r['data']:
            L = row['latest']
            f = L['ENTITY_FIELD']
            d = {'id': row['entityId']['id'], 'name': f['name']['value'], 'type': f['type']['value']}
            for k in ATTRS:
                v = L.get('ATTRIBUTE', {}).get(k)
                if v is not None and v.get('value') not in (None, ''):
                    d[k] = v['value']
            if 'meter' in d:                              # solo seriales; el resto trae claves de acceso
                try:
                    d['meter_serials'] = sorted(ast.literal_eval(d['meter']).keys())
                except (ValueError, SyntaxError):
                    d['meter_serials'] = []
                del d['meter']
            devs.append(d)
        if not r['hasNext']:
            break
        page += 1
    DEVS[:] = devs
    BY.clear()
    BY.update({d['name']: d for d in devs})


def _ensure():
    if not DEVS:
        refresh_inventory()


def inventory():
    """48 sistemas = gateways con casa conocida en el archivo de sistemas. Medidores desde el atributo del gateway."""
    _ensure()
    pul = {d['spcus']: d for d in DEVS if d['type'] == 'pulsar' and d.get('spcus') in SYSTEMS}
    out = {}
    for h, p in pul.items():
        ser = p.get('meter_serials', [])
        red = [s for s in ser if BY[s].get('mettype') == 'red']
        sol = [s for s in ser if BY[s].get('mettype') == 'solar']
        if len(red) != 1 or len(sol) != 1:
            raise RuntimeError(f'{h}: se esperaba 1 medidor de red y 1 solar en el gateway, hay {len(red)} y {len(sol)}')
        invs = [d['name'] for d in DEVS if d['type'] == 'inverter' and d.get('spcus') == h]
        out[h] = {'house': h, 'city': SYSTEMS[h]['city'], 'kwp': SYSTEMS[h]['kwp'], 'equip': SYSTEMS[h]['equip'],
                  'gw': p['name'], 'red': red[0], 'sol': sol[0], 'invs': invs}
    sin_gw = sorted(set(SYSTEMS) - set(out))
    if sin_gw:
        print(f'AVISO: casas del archivo de sistemas sin gateway en Metrum: {", ".join(sin_gw)}')
    nuevas = sorted(d['spcus'] for d in DEVS if d['type'] == 'pulsar' and d.get('spcus') not in SYSTEMS
                    and d.get('spcus') not in EXCLUIDOS)
    if nuevas:
        print(f'AVISO: gateways en Metrum que no están en el archivo de sistemas (agrégalos con su kWp): {", ".join(nuevas)}')
    return out


def ts_query(dev, keys, start, end, limit=5000, desc=False):
    """Serie sin agregar. Devuelve {key: [(ts, valor_str)] ascendente}. `dev` es el nombre (serial) o el id."""
    _ensure()
    keys = ','.join(keys) if not isinstance(keys, str) else keys
    did = BY[dev]['id'] if dev in BY else dev
    fp = None
    if CACHE:
        k = hashlib.md5(f'{did}|{keys}|{start}|{end}|{limit}|{desc}'.encode()).hexdigest()
        fp = os.path.join(CACHE, k + '.json')
        if os.path.exists(fp):
            return {kk: [tuple(x) for x in v] for kk, v in json.load(open(fp)).items()}
    order = 'DESC' if desc else 'ASC'
    r = metrum.get(f'/api/plugins/telemetry/DEVICE/{did}/values/timeseries?keys={keys}&startTs={start}&endTs={end}'
                   f'&limit={limit}&agg=NONE&orderBy={order}')
    out = {kk: sorted([(p['ts'], p['value']) for p in v]) for kk, v in r.items()}
    if fp:
        json.dump(out, open(fp, 'w'))
    return out


def pmap(fn, items, workers=8):
    with cf.ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))
