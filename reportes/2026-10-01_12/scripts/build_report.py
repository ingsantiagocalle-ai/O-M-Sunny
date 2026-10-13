import sys, os, json, statistics, collections, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))

D = json.load(open('report_data.json'))
F = D['F']; HS = D['houses']; HB = {h['casa']: h for h in HS}
OUT = sys.argv[1] if len(sys.argv) > 1 else 'reporte_sunny.html'

# ---------------------------------------------------------------- formato
def n(x, d=0, dash='—'):
    if x is None: return dash
    s = f"{x:,.{d}f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')
def pct(x, d=1): return dash_or(x, lambda v: n(v, d) + ' %')
def dash_or(x, f): return '—' if x is None else f(x)
def e(s): return html.escape(str(s))
RISK = {'Crítico': ('crit', '▲'), 'Alerta': ('serious', '◆'), 'Vigilancia': ('warn', '●'), 'Normal': ('ok', '✓'),
        'Sin dato': ('none', '–'), 'Sin cortes': ('ok', '✓')}
RANK = {'Crítico': 3, 'Alerta': 2, 'Vigilancia': 1, 'Normal': 0, 'Sin dato': -1, 'Sin cortes': 0}
def chip(level, text=None):
    c, i = RISK.get(level, ('none', '–'))
    return f'<span class="chip {c}"><i aria-hidden="true">{i}</i>{e(text or level)}</span>'
def zone_short(z):
    return {'RESERVAS DE PANCE': 'Reservas de Pance', 'PRADO VERDE PRIMAVERA': 'Prado Verde Primavera', 'TERRA BY KAIA': 'Terra by Kaia',
            'CASTELLANA REAL': 'Castellana Real', 'PANCE CAMPESTRE': 'Pance Campestre', 'LLANOS DE PANCE': 'Llanos de Pance',
            'PORTON DE LA RIVERA': 'Portón de la Rivera', 'GERONA CLUB HOUSE': 'Gerona Club House', 'CONDOMINIO LOS ABEDULES': 'Cond. Los Abedules',
            'CONDOMINIO TERRANOVA': 'Cond. Terranova', 'OFICINA PROMIGAS': 'Oficina Promigas'}.get(z, (z or '').title())
CITY = {'CALI': 'Cali', 'TURBACO': 'Turbaco', 'BARRANQUILLA': 'Barranquilla', 'CARTAGENA': 'Cartagena'}
def casa_sort_key(c):
    import re
    m = re.search(r'(\d+)', c); return (int(m.group(1)) if m else 0, c)

# ---------------------------------------------------------------- derivados
for h in HS:
    H24 = D['H24'][h['casa']]
    cap = h['cap_kwh']
    night = [H24['load'][i] for i in list(range(18, 24)) + list(range(0, 6)) if H24['load'][i] is not None]
    morn = [H24['load'][i] for i in range(6, 9) if H24['load'][i] is not None]
    s18, s6 = H24['soc'][18], H24['soc'][6]
    h['aut18'] = (max(0, (s18 - 15) / 100 * cap) / (sum(night) / len(night))) if (cap and s18 is not None and night and sum(night) > 0) else None
    h['aut6'] = (max(0, (s6 - 15) / 100 * cap) / (sum(morn) / len(morn))) if (cap and s6 is not None and morn and sum(morn) > 0) else None
    h['soc6'] = s6; h['soc18'] = s18
    h['zero_days'] = [x['day'] for x in h['daily'] if x['gen'] is not None and x['gen'] < 0.5]

sectors = sorted(D['sectors'], key=lambda s: -s['n'])
events_s = [ev for ev in D['events'] if ev['sustained']]
events_t = [ev for ev in D['events'] if not ev['sustained']]
reconnect_grid = [h['casa'] for h in HS if any(v['t'] == '03-oct 19:15' and v['v'] < 30 for v in h['vext'][:len(h['vext'])])]
# separar fase ausente en red vs en cargas
rec_grid, rec_load = [], []
for h in HS:
    vg = [v for v in h['vext'] if v['t'] == '03-oct 19:15' and v['v'] < 30]
    if vg: rec_grid.append(h['casa'])
res_pance = [h for h in HS if h['zone'] == 'RESERVAS DE PANCE']

# alarmas DEYE
deye_alerts = []
for h in HS:
    for a in h['deye_alerts']:
        from datetime import datetime, timezone, timedelta
        C = timezone(timedelta(hours=-5))
        f = lambda x: datetime.fromtimestamp(int(x), C).strftime('%d-oct %H:%M') if x else '—'
        deye_alerts.append(dict(casa=h['casa'], name=a.get('alertName', '').replace(' ', ' '), level=a.get('level'),
                                start=f(a.get('alertStartTime')), end=f(a.get('alertEndTime'))))
livo_faults = [(h['casa'], h['brand'], [x['t'] + ' (' + x['state'] + ')' for x in h['inv_faults']]) for h in HS if h['inv_faults']]
igf = sorted([(h['ev_inv'].get('igf', 0), h['casa']) for h in HS if h['ev_inv'].get('igf')], reverse=True)
code_count = collections.Counter()
for h in HS:
    for k, v in h['ev_red'].items(): code_count[('Red', k)] += v
    for k, v in h['ev_sol'].items(): code_count[('Cargas', k)] += v
CODES = {'po': 'Pérdida de alimentación del medidor (power off)', 'pr': 'Retorno de alimentación (power restore)',
         'rps': 'Secuencia de fases invertida', 'mn': 'Neutro ausente', 'drf': 'Sin identificar',
         'uv': 'Subtensión en la fase indicada', 'ov': 'Sobretensión en la fase indicada', 'mv': 'Tensión ausente en la fase indicada',
         'nv': 'Tensión normalizada en la fase indicada', 'cs': 'Sin identificar (posible ajuste de reloj)', 'rc': 'Sin identificar',
         'tmp': 'Tapa del medidor abierta', 'tmc': 'Tapa del medidor cerrada'}
def code_meaning(c):
    base = c.rstrip('0123456789'); ph = c[len(base):]
    m = CODES.get(base, 'Sin identificar')
    return m + (f' ({ "ABC"[int(ph)-1] if ph in "123" else ph})' if ph else '')

# ---------------------------------------------------------------- datos para JS
def r3(v, d=3): return None if v is None else round(v, d)
fleet_cur = {p: [] for p in 'ABC'}
for p in 'ABC':
    for i in range(24):
        vals = [h['cur_profile'][p][i] for h in HS if h['cur_profile'] and h['cur_profile'].get(p) and h['cur_profile'][p][i] is not None]
        fleet_cur[p].append(sum(vals) / len(vals) if vals else None)
JS = dict(
    daily=[{k: r3(x[k], 4) for k in ('day', 'gen', 'imp', 'exp', 'load', 'dem', 'cov', 'selfsuf')} for x in D['daily']],
    prof={'__flota__': {k: [r3(v) for v in D['fleet24'][k]] for k in D['fleet24']}},
    cur={'__flota__': {p: [r3(v, 2) for v in fleet_cur[p]] for p in 'ABC'}},
    heat={k: [[r3(v, 2) for v in row] for row in D['heat'][k]] for k in ('imp', 'load')},
    ratio=sorted([dict(casa=h['casa'], brand=h['brand'], r=r3(h['imax_ratio']), p99=r3(h['p99_ratio']), imax=r3(h['imax'][1], 1) if h['imax'] else None,
                       ph=h['imax'][0] if h['imax'] else None, inom=r3(h['inom'], 1), risk=h['risk_current']) for h in HS if h['imax_ratio'] is not None],
                 key=lambda x: -x['r']),
    events=[dict(zone=zone_short(ev['zone']), start=ev['start'], end=ev['end'], dur=r3(ev['dur_med'], 1), n=ev['n'], nz=ev['n_zone'],
                 s=ev['sustained'], u=len(ev['unserved_houses'])) for ev in D['events']],
    zones=[zone_short(s['zone']) for s in sectors],
)
for h in HS:
    JS['prof'][h['casa']] = {k: [r3(v) for v in D['H24'][h['casa']][k]] for k in D['H24'][h['casa']]}
    JS['cur'][h['casa']] = {p: [r3(v, 2) for v in (h['cur_profile'] or {}).get(p, [None] * 24)] for p in 'ABC'}
data_json = json.dumps(JS, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

# ---------------------------------------------------------------- tablas
def table(head, rows, cls='', sortable=False, tid=''):
    th = ''.join(f'<th{(" data-k=%d" % i) if sortable else ""} scope="col"{(" class=" + chr(34) + c + chr(34)) if c else ""}>{t}</th>' for i, (t, c) in enumerate(head))
    body = '\n'.join(rows)
    return f'<div class="tw"><table class="{cls}{" sortable" if sortable else ""}"{(" id=" + chr(34) + tid + chr(34)) if tid else ""}><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
def td(v, sortv=None, cls='num'):
    sv = '' if sortv is None else f' data-v="{sortv}"'
    return f'<td class="{cls}"{sv}>{v}</td>'

# Diario
daily_rows = []
for x in D['daily']:
    daily_rows.append('<tr>' + td(f'{x["day"]:02d}-oct', x['day'], 'txt') + td(n(x['gen'])) + td(n(x['load'])) + td(n(x['imp'])) + td(n(x['exp'], 1)) +
                      td(n(x['dem'])) + td(pct(x['cov'])) + td(pct(x['selfsuf'])) + '</tr>')
tot = D['daily']
daily_rows.append('<tr class="tot">' + td('Total', None, 'txt') + td(n(F['gen'])) + td(n(F['load'])) + td(n(F['imp'])) + td(n(F['exp'], 1)) + td(n(F['dem'])) + td(pct(F['cov'])) + td(pct(F['selfsuf'])) + '</tr>')
T_DAILY = table([('Día', 'txt'), ('Generación FV<br><small>kWh</small>', ''), ('Consumo medido<br><small>kWh</small>', ''), ('Importación<br><small>kWh</small>', ''),
                 ('Exportación<br><small>kWh</small>', ''), ('Demanda del sistema<br><small>kWh</small>', ''), ('Cobertura solar', ''), ('Autosuficiencia en cargas', '')], daily_rows)

# Sectores
sec_rows = []
for s in sectors:
    sec_rows.append('<tr>' + td(e(zone_short(s['zone'])), None, 'txt') + td(e(CITY.get(s['city'], s['city'])), None, 'txt') + td(e(s['utility'] or '—'), None, 'txt') + td(s['n']) +
                    td(' · '.join(f'{k.title()} {v}' for k, v in sorted(s['brands'].items())), None, 'txt') +
                    td(n(s['gen'])) + td(n(s['gen_house_day'], 1)) + td(n(s['load_house_day'], 1)) + td(n(s['imp'])) + td(pct(s['cov'])) +
                    td(n(s['n_out'])) + td(n(s['saidi'], 1)) + td(pct(s['backup_cov']) if s['n_out'] else '—') + '</tr>')
T_SECT = table([('Sector', 'txt'), ('Ciudad', 'txt'), ('Operador de red', 'txt'), ('Viviendas', ''), ('Inversores', 'txt'), ('Generación<br><small>kWh</small>', ''),
                ('Gen./vivienda·día<br><small>kWh</small>', ''), ('Consumo/vivienda·día<br><small>kWh</small>', ''), ('Importación<br><small>kWh</small>', ''),
                ('Cobertura', ''), ('Cortes &gt;3 min<br><small>vivienda-evento</small>', ''), ('Horas de corte<br><small>por vivienda</small>', ''), ('Respaldo efectivo', '')], sec_rows)

# Ranking por vivienda
rk_rows = []
for h in sorted(HS, key=lambda h: -(h['cov'] or 0)):
    note = ''
    if h['scale'] != 1: note = ' <sup title="Generación corregida ×10 (ver Calidad de datos)">×10</sup>'
    elif h['gen_src']: note = ' <sup title="Días completados con DeyeCloud o contador diario del inversor">*</sup>'
    rk_rows.append(f'<tr data-zone="{e(zone_short(h["zone"]))}" data-casa="{e(h["casa"].lower())}">' + td(e(h['casa']), casa_sort_key(h['casa'])[0], 'txt') + td(e(zone_short(h['zone'])), e(h['zone']), 'txt') +
                   td(e(h['brand'].title()) + f' {n(h["invcap"])} kW', h['invcap'], 'txt') +
                   td(n(h['gen'], 1) + note, h['gen']) + td(n(h['gen_day'], 1), h['gen_day']) + td(n(h['kwh_kw_day'], 2), h['kwh_kw_day']) +
                   td(n(h['load'], 1), h['load']) + td(n(h['load_day'], 1), h['load_day']) + td(n(h['imp'], 1), h['imp']) + td(n(h['exp'], 2), h['exp']) +
                   td(pct(h['cov']), h['cov']) + td(pct(h['selfsuf']), h['selfsuf']) + td(n(h['losses_w']), h['losses_w']) +
                   td(n(h['peak_load_kw'], 1), h['peak_load_kw']) + td(chip(h['risk']), RANK[h['risk']], 'txt') + '</tr>')
T_RANK = table([('Vivienda', 'txt'), ('Sector', 'txt'), ('Inversor', 'txt'), ('Generación<br><small>kWh</small>', ''), ('kWh/día', ''), ('kWh/kW·día<br><small>por kW nominal</small>', ''),
                ('Consumo<br><small>kWh</small>', ''), ('Consumo/día<br><small>kWh</small>', ''), ('Importación<br><small>kWh</small>', ''), ('Exportación<br><small>kWh</small>', ''),
                ('Cobertura', ''), ('Autosuf.', ''), ('Pérdidas<br><small>W promedio</small>', ''), ('Pico de carga<br><small>kW</small>', ''), ('Riesgo global', 'txt')],
               rk_rows, sortable=True, tid='t-rank')

# Fases
ph_rows = []
for h in sorted(HS, key=lambda h: (-RANK[h['risk_current']], -(h['imax_ratio'] or 0))):
    cl = h['cur_load']
    def cell(p):
        c = cl.get(p)
        if not c: return td('—')
        hot = ' hot' if h['inom'] and c['max'] >= 0.8 * h['inom'] else ''
        return f'<td class="num{hot}" data-v="{c["max"]}">{n(c["max"], 1)}<small> / {n(c["p99"], 1)}</small></td>'
    sh = h['shares']
    dom = f'{h["dom"]} {n(sh[h["dom"]], 0)} %' if h['dom'] else '—'
    vg = h['vg']
    ph_rows.append('<tr>' + td(e(h['casa']), casa_sort_key(h['casa'])[0], 'txt') + td(e(h['brand'].title()) + f' {n(h["invcap"])} kW', h['invcap'], 'txt') + td(n(h['inom'], 1), h['inom']) +
                   cell('A') + cell('B') + cell('C') + td(pct(100 * h['imax_ratio'] if h['imax_ratio'] else None, 0), h['imax_ratio']) +
                   td(pct(h['hi80'], 1), h['hi80']) + td(dom, sh.get(h['dom']) if h['dom'] else None, 'txt') +
                   td(f'{n(h["vg_min"], 0)}–{n(h["vg_max"], 0)}', h['vg_max']) + td(n(h['vg_avg'], 1), h['vg_avg']) + td(pct(h['vg_hi10'], 1), h['vg_hi10']) +
                   td(n(h['v_backup'], 1), h['v_backup']) + td(chip(h['risk_current']), RANK[h['risk_current']], 'txt') + td(chip(h['risk_voltage']), RANK[h['risk_voltage']], 'txt') + '</tr>')
T_PH = table([('Vivienda', 'txt'), ('Inversor', 'txt'), ('I nominal<br><small>A/fase (est.)</small>', ''), ('Fase A<br><small>máx / p99 A</small>', ''), ('Fase B<br><small>máx / p99 A</small>', ''),
              ('Fase C<br><small>máx / p99 A</small>', ''), ('I máx / I nom', ''), ('Tiempo &gt;80 % I nom', ''), ('Fase dominante<br><small>% energía</small>', 'txt'),
              ('Red mín–máx<br><small>V, sin cortes</small>', ''), ('Red promedio<br><small>V</small>', ''), ('Red &gt;132 V<br><small>% tiempo</small>', ''), ('Cargas en respaldo<br><small>V mediana</small>', ''),
              ('Riesgo corriente', 'txt'), ('Riesgo tensión', 'txt')], ph_rows, sortable=True, tid='t-ph')

# Eventos de red
ev_rows = []
for ev in events_s:
    ev_rows.append('<tr>' + td(e(ev['start'][8:10] + '-oct ' + ev['start'][11:]), ev['start'], 'txt') + td(e(ev['end'][8:10] + '-oct ' + ev['end'][11:]), ev['end'], 'txt') +
                   td(e(zone_short(ev['zone'])), None, 'txt') + td(e(ev['utility'] or '—'), None, 'txt') + td(n(ev['dur_med'], 0), ev['dur_med']) +
                   td(f'{ev["n"]} / {ev["n_zone"]}', ev['n']) + td(pct(ev['cov_avg'], 1), ev['cov_avg']) + td(n(ev['e_load'], 1), ev['e_load']) +
                   td(e(', '.join(ev['unserved_houses'])) if ev['unserved_houses'] else '<span class="muted">Ninguna</span>', len(ev['unserved_houses']), 'txt wrap') + '</tr>')
T_EV = table([('Inicio', 'txt'), ('Fin', 'txt'), ('Sector', 'txt'), ('Operador', 'txt'), ('Duración<br><small>min (mediana)</small>', ''), ('Viviendas afectadas', ''),
              ('Respaldo efectivo<br><small>promedio</small>', ''), ('Energía servida en respaldo<br><small>kWh</small>', ''), ('Viviendas con &gt;2 min sin tensión', 'txt')], ev_rows, sortable=True, tid='t-ev')

# Respaldo por vivienda
bk_rows = []
for h in sorted(HS, key=lambda h: (h['backup_cov'] if h['backup_cov'] is not None else 101)):
    if not h['n_out']: continue
    sus = [o for o in h['outages'] if o['dur'] > 3]
    causes = collections.Counter(o['cause'] for o in sus if o['cause'])
    tr = [o['transfer_min'] for o in sus if o['transfer_min'] > 0]
    longest = max(sus, key=lambda o: o['dur'])
    bk_rows.append('<tr>' + td(e(h['casa']), casa_sort_key(h['casa'])[0], 'txt') + td(e(h['brand'].title()), None, 'txt') + td(h['n_out']) + td(n(h['out_hours'], 1), h['out_hours']) +
                   td(n(longest['dur'] / 60, 1), longest['dur']) + td(n(h['unserved_min'], 0), h['unserved_min']) + td(pct(h['backup_cov'], 1), h['backup_cov']) +
                   td(n(statistics.median(tr), 1) if tr else '—', statistics.median(tr) if tr else 0) +
                   td(n(min([o['socmin'] for o in sus if o['socmin'] is not None], default=None), 0), None) +
                   td(e('; '.join(f'{k} ({v})' for k, v in causes.most_common())) or '<span class="muted">—</span>', None, 'txt wrap') +
                   td(chip(h['risk_backup']), RANK[h['risk_backup']], 'txt') + '</tr>')
T_BK = table([('Vivienda', 'txt'), ('Marca', 'txt'), ('Cortes &gt;3 min', ''), ('Horas de corte', ''), ('Corte más largo<br><small>h</small>', ''), ('Sin tensión en cargas<br><small>min</small>', ''),
              ('Respaldo efectivo', ''), ('Transferencia<br><small>min mediana</small>', ''), ('SOC mín en cortes<br><small>%</small>', ''), ('Causa de minutos sin respaldo', 'txt'), ('Estado', 'txt')], bk_rows, sortable=True, tid='t-bk')

# Batería
bt_rows = []
for h in sorted(HS, key=lambda h: -(h['cycles_day'] or 0)):
    bt_rows.append('<tr>' + td(e(h['casa']), casa_sort_key(h['casa'])[0], 'txt') + td(e(h['brand'].title()), None, 'txt') +
                   td(n(h['cap_kwh'], 1) + f'<small> ({n(h["capah"])} Ah · {h["modules"]} mód.)</small>' if h['cap_kwh'] else '—', h['cap_kwh']) +
                   td(n(h['soc_avg'], 0), h['soc_avg']) + td(n(h['soc6'], 0), h['soc6']) + td(n(h['soc18'], 0), h['soc18']) +
                   td(pct(h['pct_low'], 0), h['pct_low']) + td(pct(h['pct_full'], 0), h['pct_full']) + td(n(h['cycles_day'], 2), h['cycles_day']) +
                   td(n(h['bch'], 0), h['bch']) + td(n(h['bdc'], 0), h['bdc']) + td(n(h['grid_charge'], 1), h['grid_charge']) +
                   td(n(h['aut18'], 1), h['aut18'] or 0) + td(n(h['aut6'], 1), h['aut6'] or 0) +
                   td(n(h['tbat_max'], 0), h['tbat_max']) + td(n(h['soh'], 0), h['soh']) + '</tr>')
T_BT = table([('Vivienda', 'txt'), ('Marca', 'txt'), ('Capacidad est.<br><small>kWh</small>', ''), ('SOC prom.<br><small>%</small>', ''), ('SOC 06:00<br><small>% prom.</small>', ''),
              ('SOC 18:00<br><small>% prom.</small>', ''), ('Tiempo SOC ≤21 %', ''), ('Tiempo SOC ≥98 %', ''), ('Ciclos eq./día', ''), ('Carga<br><small>kWh est.</small>', ''),
              ('Descarga<br><small>kWh est.</small>', ''), ('Carga desde red<br><small>kWh est.</small>', ''), ('Autonomía 18:00<br><small>h est.</small>', ''),
              ('Autonomía 06:00<br><small>h est.</small>', ''), ('T máx<br><small>°C</small>', ''), ('SOH<br><small>% (reportado)</small>', '')], bt_rows, sortable=True, tid='t-bt')

# Exportación
ex_rows = []
for h in sorted(HS, key=lambda h: -h['exp'])[:10]:
    ex_rows.append('<tr>' + td(e(h['casa']), None, 'txt') + td(e(h['brand'].title()), None, 'txt') + td(n(h['exp'], 2)) + td(pct(h['exp_pct'], 2)) + td(pct(h['full_daylight'], 0)) + '</tr>')
T_EX = table([('Vivienda', 'txt'), ('Marca', 'txt'), ('Exportación<br><small>kWh, 12 días</small>', ''), ('% de su generación', ''), ('Horas de luz con batería llena', '')], ex_rows)

# Alarmas
al_rows = []
for a in deye_alerts:
    al_rows.append('<tr>' + td(e(a['casa']), None, 'txt') + td('DeyeCloud', None, 'txt') + td(f'<code>{e(a["name"])}</code>', None, 'txt') + td(e(a['start']), None, 'txt') + td(e(a['end']), None, 'txt') + '</tr>')
for casa, brand, lst in livo_faults:
    al_rows.append('<tr>' + td(e(casa), None, 'txt') + td('Metrum · estado del inversor', None, 'txt') + td(f'<code>invrun = fault/alarm</code> ({brand.title()})', None, 'txt') + td(e(', '.join(lst)), None, 'txt wrap') + td('—', None, 'txt') + '</tr>')
T_AL = table([('Vivienda', 'txt'), ('Fuente', 'txt'), ('Código', 'txt'), ('Inicio / registros', 'txt'), ('Fin', 'txt')], al_rows)
code_rows = []
for (where, code), cnt in sorted(code_count.items(), key=lambda x: -x[1]):
    code_rows.append('<tr>' + td(f'<code>{e(code)}</code>', None, 'txt') + td(where, None, 'txt') + td(n(cnt)) + td(e(code_meaning(code)), None, 'txt') + '</tr>')
T_CODES = table([('Código', 'txt'), ('Medidor', 'txt'), ('Registros', ''), ('Interpretación probable', 'txt')], code_rows)

# Calidad de datos: escala
sc_rows = []
for h in HS:
    if h['scale'] != 1:
        ev = h['scale_evidence']
        sc_rows.append('<tr>' + td(e(h['casa']), None, 'txt') + td(f'<code>{e(h["inv"])}</code>', None, 'txt') + td(n(ev['metrum'], 1)) + td(n(ev['deyecloud'], 1)) +
                       td(n(ev['solar_medidores'], 1)) + td(n(h['gen'], 1)) + td(e('DeyeCloud ×10 respecto a Metrum' if 'DeyeCloud' in ev['tipo'] and 'Metrum = DeyeCloud' not in ev['tipo'] else 'Metrum = DeyeCloud; balance de medidores y batería ×10'), None, 'txt wrap') + '</tr>')
T_SC = table([('Vivienda', 'txt'), ('Inversor', 'txt'), ('Metrum<br><small>kWh</small>', ''), ('DeyeCloud<br><small>kWh</small>', ''), ('Solar a cargas por medidores<br><small>kWh</small>', ''),
              ('Usado en el reporte<br><small>kWh</small>', ''), ('Evidencia', 'txt')], sc_rows)

# ---------------------------------------------------------------- textos con cifras
rp = next(s for s in D['sectors'] if s['zone'] == 'RESERVAS DE PANCE')
c121 = HB['Casa 121 CR']; c447 = HB['Casa 447p']; c9g = HB['Casa 9G']; c104 = HB['Casa 104']; c74 = HB['Casa 74']; c18pr = HB['Casa 18PR']
c10 = HB['Casa 10']; c99 = HB['Casa 99']; c23 = HB['Casa 23']; c63 = HB['Casa 63']; c76 = HB['Casa 76']
crit_cur = [h for h in HS if h['risk_current'] == 'Crítico']
alert_cur = [h for h in HS if h['risk_current'] == 'Alerta']
livo_rp = [h for h in res_pance if h['brand'] == 'LIVOLTEK']
oct4_bad = [h['casa'] for h in res_pance if any(o['start'].startswith('2026-10-04 17:5') and o['unserved'] > 20 for o in h['outages'])]
lv_eps = [h['v_backup'] for h in HS if h['brand'] == 'LIVOLTEK' and h['v_backup']]
dy_eps = [h['v_backup'] for h in HS if h['brand'] == 'DEYE' and h['v_backup']]
gen_houses_day = F['gen_house_day']
inv_gap_houses = [h['casa'] for h in HS if h['inv_cov_outage'] is not None and h['inv_cov_outage'] < 50]
fleet24 = D['fleet24']
pv_peak_h = max(range(24), key=lambda i: fleet24['gen'][i] or 0)
soc_min_h = min(range(24), key=lambda i: fleet24['soc'][i] or 100)
rps_houses = [h['casa'] for h in HS if h['ev_red'].get('rps') or h['ev_sol'].get('rps')]
zero_gen = [(h['casa'], h['zero_days']) for h in HS if h['zero_days']]
top_full = sorted(HS, key=lambda h: -(h['full_daylight'] or 0))[:5]

def fmt_days(ds):
    if not ds: return ''
    if len(ds) > 1 and ds == list(range(ds[0], ds[-1] + 1)): return f'{ds[0]}–{ds[-1]} oct'
    return ', '.join(str(d) for d in ds) + ' oct'


cov_sorted = sorted(D['daily'], key=lambda x: x['cov'])
oct4_soc = [o['soc0'] for h in res_pance for o in h['outages'] if o['start'].startswith('2026-10-04 17:5') and o['unserved'] > 20 and o['soc0'] is not None]
RR = {r['casa']: r for r in json.load(open('houses_result.json'))}
rec_load = [c for c, r in RR.items() if any(v['t'] == '03-oct 19:15' and v['v'] < 30 for v in (r.get('volt_extreme_load') or []))]
rec_grid = [c for c, r in RR.items() if any(v['t'] == '03-oct 19:15' and v['v'] < 30 for v in (r.get('volt_extreme_grid') or []))]
REC_LOAD_N = len(rec_load)
a6 = [h['aut6'] for h in HS if h['aut6'] is not None]
ratios = [h['imax_ratio'] for h in crit_cur]

TPL = open('report_template.html', encoding='utf-8').read()
REPL = {
    '{{DATA}}': data_json,
    '{{CHIP_CRIT}}': chip('Crítico'), '{{CHIP_ALERT}}': chip('Alerta'), '{{CHIP_VIG}}': chip('Vigilancia'),
    '{{COV_MIN}}': n(cov_sorted[0]['cov'], 1), '{{COV_MIN_D}}': f"{cov_sorted[0]['day']}-oct", '{{COV_MAX}}': n(cov_sorted[-1]['cov'], 1), '{{COV_MAX_D}}': f"{cov_sorted[-1]['day']}-oct",
    '{{OCT4_SOCMIN}}': n(min(oct4_soc), 0), '{{OCT4_SOCMAX}}': n(max(oct4_soc), 0), '{{REC_LOAD_N}}': str(REC_LOAD_N),
    '{{AUT6_LT2}}': str(sum(1 for x in a6 if x < 2)), '{{AUT6_ZERO}}': str(sum(1 for x in a6 if x < 0.05)),
    '{{P99_LIST}}': ', '.join(f"{h['casa']} {n(100*h['p99_ratio'],0)} %" for h in sorted(crit_cur, key=lambda h: -h['p99_ratio'])),
    '{{RATIO_MIN}}': n(100 * min(ratios), 0), '{{RATIO_MAX}}': n(100 * max(ratios), 0),
    '{{N_HOUSES}}': str(F['n_houses']), '{{GEN}}': n(F['gen']), '{{LOAD}}': n(F['load']), '{{IMP}}': n(F['imp']), '{{EXP}}': n(F['exp'], 1),
    '{{DEM}}': n(F['dem']), '{{COV}}': n(F['cov'], 1), '{{SELFSUF}}': n(F['selfsuf'], 1), '{{LOSSES}}': n(F['losses']), '{{LOSSES_PCT}}': n(F['losses_pct'], 1),
    '{{EXP_PCT}}': n(F['exp_pct'], 2), '{{GEN_HD}}': n(F['gen_house_day'], 1), '{{LOAD_HD}}': n(F['load_house_day'], 1), '{{KWKW}}': n(F['kwh_kw_day'], 2),
    '{{CAP_INV}}': n(F['cap_inv_kw']), '{{SOC_AVG}}': n(F['soc_avg'], 0), '{{CYC}}': n(F['cycles_day'], 2), '{{BCH}}': n(F['bch']), '{{BDC}}': n(F['bdc']),
    '{{GRID_CH}}': n(F['grid_charge']), '{{N_OUT}}': n(F['n_out_house']), '{{N_TRANS}}': n(F['n_trans_house']), '{{OUT_H}}': n(F['out_hours_house']),
    '{{UNS_H}}': n(F['unserved_h'], 1), '{{BK_COV}}': n(F['backup_cov'], 1), '{{SAIFI}}': n(F['saifi'], 1), '{{SAIDI}}': n(F['saidi'], 1),
    '{{HOUSES_OUT}}': str(F['houses_with_out']), '{{GRID_EV}}': str(F['grid_events']), '{{GRID_EV_T}}': str(F['grid_events_trans']), '{{E_BK}}': n(F['e_backup']),
    '{{BK_DEYE}}': n(F['backup_cov_DEYE'], 1), '{{BK_LIVO}}': n(F['backup_cov_LIVOLTEK'], 1), '{{TR_DEYE}}': n(F['transfer_med_DEYE'], 1), '{{TR_LIVO}}': n(F['transfer_med_LIVOLTEK'], 1),
    '{{N_OUT_DEYE}}': str(F['n_out_DEYE']), '{{N_OUT_LIVO}}': str(F['n_out_LIVOLTEK']),
    '{{R_CRIT}}': str(F['risk_counts']['Crítico']), '{{R_ALERT}}': str(F['risk_counts']['Alerta']), '{{R_VIG}}': str(F['risk_counts']['Vigilancia']), '{{R_OK}}': str(F['risk_counts']['Normal']),
    '{{AV_INV}}': n(F['avail_inv'], 1), '{{AV_RED}}': n(F['avail_red'], 1), '{{AV_SOL}}': n(F['avail_sol'], 1),
    '{{PEAK_H_LOAD}}': f'{F["peak_hour_load"]:02d}:00', '{{PEAK_H_IMP}}': f'{F["peak_hour_imp"]:02d}:00', '{{PV_PEAK_H}}': f'{pv_peak_h:02d}:00',
    '{{SOC_MIN_H}}': f'{soc_min_h:02d}:00', '{{SOC_MIN_V}}': n(fleet24['soc'][soc_min_h], 0), '{{SOC_MAX_V}}': n(max(fleet24['soc']), 0),
    '{{PV_PEAK_V}}': n(fleet24['gen'][pv_peak_h], 2), '{{LOAD_PEAK_V}}': n(max(fleet24['load']), 2),
    '{{RP_SAIDI}}': n(rp['saidi'], 1), '{{RP_N}}': str(rp['n']), '{{RP_BK}}': n(rp['backup_cov'], 1), '{{RP_EVENTS}}': str(len([ev for ev in events_s if ev['zone'] == 'RESERVAS DE PANCE'])),
    '{{C121_VMAX}}': n(max(v['v'] for v in c121['vext']), 1), '{{C121_BK}}': n(c121['backup_cov'], 1), '{{C121_MN}}': str(c121['ev_red'].get('mn', 0) + c121['ev_sol'].get('mn', 0)),
    '{{C121_SYS}}': str(len([s for s in c121['sys_int'] if s['dur'] > 2])), '{{C121_VLOAD}}': n(max([v['v'] for v in c121['vext'] if v['v'] >= 140 and v['t'] == '02-oct 12:30'] + [0]), 1),
    '{{C447_GEN}}': n(c447['gen'], 1), '{{C447_KWKW}}': n(c447['kwh_kw_day'], 2), '{{C447_IGF}}': str(c447['ev_inv'].get('igf', 0)), '{{C447_COV}}': n(c447['cov'], 0),
    '{{C9G_VMIN}}': n(c9g['vg_min'], 1), '{{C9G_VMAX}}': n(c9g['vg_max'], 1), '{{C9G_VAVG}}': n(c9g['vg_avg'], 1), '{{C9G_HI}}': n(c9g['vg_hi10'], 0),
    '{{C104_SLOTS}}': n(c104['inv_iso']['slots'] * 15 / 60, 0), '{{C104_FIRST}}': c104['inv_iso']['first'] or '', '{{C104_LAST}}': c104['inv_iso']['last'] or '',
    '{{C74_P99}}': n(max(c74['cur_load'][p]['p99'] for p in 'ABC'), 1), '{{C74_MAX}}': n(c74['imax'][1], 1), '{{C74_COV}}': n(c74['cov'], 0), '{{C74_PEAK}}': n(c74['peak_load_kw'], 1),
    '{{C18PR_MAX}}': n(c18pr['imax'][1], 1), '{{C18PR_R}}': n(100 * c18pr['imax_ratio'], 0), '{{C10_MAX}}': n(c10['imax'][1], 1), '{{C10_P99}}': n(max(c10['cur_load'][p]['p99'] for p in 'ABC'), 1),
    '{{C99_MAX}}': n(c99['imax'][1], 1), '{{C99_P99}}': n(max(c99['cur_load'][p]['p99'] for p in 'ABC'), 1), '{{C23_MAX}}': n(c23['imax'][1], 1), '{{C63_MAX}}': n(c63['imax'][1], 1),
    '{{C76_LW}}': n(c76['losses_w'], 0), '{{N_CRIT_CUR}}': str(len(crit_cur)), '{{CRIT_CUR}}': ', '.join(h['casa'] for h in sorted(crit_cur, key=lambda h: -h['imax_ratio'])),
    '{{N_ALERT_CUR}}': str(len(alert_cur)), '{{ALERT_CUR}}': ', '.join(h['casa'] for h in alert_cur),
    '{{OCT4_N}}': str(len(oct4_bad)), '{{OCT4_LIST}}': ', '.join(oct4_bad), '{{LIVO_RP_N}}': str(len(livo_rp)),
    '{{LV_EPS}}': n(statistics.median(lv_eps), 1), '{{DY_EPS}}': n(statistics.median(dy_eps), 1), '{{REC_GRID_N}}': str(len(rec_grid)),
    '{{INV_GAP}}': ', '.join(inv_gap_houses), '{{RPS_N}}': str(len(rps_houses)),
    '{{ZERO_GEN}}': '; '.join(f'{c} ({fmt_days(ds)})' for c, ds in zero_gen),
    '{{TOP_FULL}}': ', '.join(f'{h["casa"]} ({n(h["full_daylight"], 0)} %)' for h in top_full),
    '{{N_SCALED}}': str(len(F['scaled'])),
    '{{T_DAILY}}': T_DAILY, '{{T_SECT}}': T_SECT, '{{T_RANK}}': T_RANK, '{{T_PH}}': T_PH, '{{T_EV}}': T_EV, '{{T_BK}}': T_BK, '{{T_BT}}': T_BT, '{{T_EX}}': T_EX,
    '{{T_AL}}': T_AL, '{{T_CODES}}': T_CODES, '{{T_SC}}': T_SC,
    '{{ZONE_OPTS}}': ''.join(f'<option value="{e(zone_short(s["zone"]))}">{e(zone_short(s["zone"]))}</option>' for s in sectors),
    '{{HOUSE_OPTS}}': ''.join(f'<optgroup label="{e(zone_short(s["zone"]))}">' + ''.join(f'<option value="{e(h["casa"])}">{e(h["casa"])} · {e(h["brand"].title())}</option>' for h in sorted([h for h in HS if h['zone'] == s['zone']], key=lambda h: casa_sort_key(h['casa']))) + '</optgroup>' for s in sectors),
}
for k, v in REPL.items():
    TPL = TPL.replace(k, v)
import re
left = re.findall(r'\{\{[A-Z0-9_]+\}\}', TPL)
if left: print('UNREPLACED', set(left))
open(OUT, 'w', encoding='utf-8').write(TPL)
print('wrote', OUT, len(TPL) // 1024, 'KB')
