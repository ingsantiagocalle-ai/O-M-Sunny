"""Agregados del reporte (eventos, semáforos, KPIs, rankings) a partir de compute.build()."""
from __future__ import annotations

import re
import statistics

from compute import *
from data import fmt_local

EVENT_GAP = 10 * 60_000   # cortes de una misma ciudad separados menos de 10 min = mismo evento
PATRON_DAYS = 10          # mediana de los 10 días previos (validado contra el reporte de referencia)


def nat_key(name):
    m = re.match(r'Casa\s+(\d+)\s*(.*)$', name)
    return (int(m.group(1)), m.group(2).strip().lower()) if m else (10**9, name.lower())


def kwp_exact(k):
    """El kWp del archivo de sistemas viene redondeado a 2 decimales; el real es n módulos de 595 W."""
    n = round(k / 0.595)
    return n * 0.595 if abs(n * 0.595 - k) <= 0.01 else k


def median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def aggregate(R):
    H = R['houses']
    A, B, now, D0 = R['A'], R['B'], R['now'], R['D0']
    out = {'A': A, 'B': B, 'now': now, 'D0': D0, 'D1': R['D1']}
    names = sorted(H, key=nat_key)
    by_city = {c: [h for h in names if H[h]['city'] == c] for c in CITY_ORDER}
    out['by_city'] = by_city

    # ---------------- energía por casa
    for h, v in H.items():
        d = v['day']
        v['gen'] = d['gen'] if d else None
        v['cons'] = d['cons'] if d else None
        v['kwp_x'] = kwp_exact(v['kwp'])
        v['yield'] = (d['gen'] / v['kwp_x'] * 365) if d else None
        pat = YIELD_PATRON[v['city']]
        v['pct'] = (v['yield'] / pat * 100) if v['yield'] is not None else None
        # consumo habitual: mediana de sus días previos
        prevc = [p['cons'] for p in v['prev'][:PATRON_DAYS] if p]
        v['cons_med'] = median(prevc)
        # alerta de rendimiento
        al = None
        if v['pct'] is not None and v['pct'] < 90:
            parts = ['baja vs patrón']
            if v['cons_med'] and v['cons'] < 0.75 * v['cons_med']: parts.append('bajo consumo')
            if v['full_t'] is not None:
                hh = (v['full_t'] - D0) / H1                 # hora local del día D0
                tt = fmt_local(v['full_t'], '%H:%M')
                if hh < 12: parts.append(f'producción limitada (batería llena {tt})')
                elif hh < 16: parts.append(f'producción limitada en la tarde (batería llena {tt})')
            al = ', '.join(parts)
        v['alert'] = al

    valid = [v for v in H.values() if v['gen'] is not None]
    out['n_valid'] = len(valid)
    out['gen'] = sum(v['gen'] for v in valid)
    out['cons'] = sum(v['cons'] for v in valid)
    out['kwp_valid'] = sum(v['kwp_x'] for v in valid)
    out['yield'] = out['gen'] / out['kwp_valid'] * 365 if valid else None
    out['cov'] = out['gen'] / out['cons'] * 100 if out['cons'] else None
    # patrón de la flota = mediana de los totales diarios de los días previos
    tots = []
    for k in range(PATRON_DAYS):
        vals = [v['prev'][k]['gen'] for v in H.values() if v['prev'][k]]
        if vals: tots.append(sum(vals))
    out['patron'] = median(tots)
    out['gen_vs_patron'] = (out['gen'] / out['patron'] - 1) * 100 if out['patron'] else None

    cities = {}
    for c in CITY_ORDER:
        hs = [H[h] for h in by_city[c]]
        vs = [v for v in hs if v['gen'] is not None]
        g = sum(v['gen'] for v in vs); cs = sum(v['cons'] for v in vs); kp = sum(v['kwp_x'] for v in vs)
        cities[c] = {'n': len(hs), 'gen': g, 'cons': cs, 'cov': g / cs * 100 if cs else None,
                     'yield': g / kp * 365 if kp else None,
                     'vs_patron': (g / kp * 365) / YIELD_PATRON[c] * 100 if kp else None,
                     'exp': sum((v['win']['exp'] or 0) for v in hs),
                     'imp': sum((v['win']['imp'] or 0) for v in hs)}
    out['cities'] = cities
    out['exp_total'] = sum((v['win']['exp'] or 0) for v in H.values())
    out['imp_total'] = sum((v['win']['imp'] or 0) for v in H.values())

    # ---------------- cortes
    all_cuts = []
    for h in names:
        for c in H[h]['cuts']:
            all_cuts.append(dict(c, house=h, city=H[h]['city']))
    out['cuts'] = all_cuts
    out['n_cuts'] = len(all_cuts)
    houses_cut = [h for h in names if H[h]['cuts']]
    out['houses_cut'] = houses_cut
    tot_dur = sum(c['dur'] for c in all_cuts)
    tot_vio = sum(min(c['total'], c['dur']) for c in all_cuts)
    out['backup_pct'] = (1 - tot_vio / tot_dur) * 100 if tot_dur else None
    out['cuts_no_gap'] = sum(1 for c in all_cuts if c['total'] == 0)

    # eventos de red por ciudad (cortes cercanos en el tiempo)
    events = []
    for city in CITY_ORDER:
        cc = sorted([c for c in all_cuts if c['city'] == city], key=lambda c: c['c0'])
        cur = None
        for c in cc:
            if cur is None or c['c0'] > cur['end'] + EVENT_GAP:
                cur = {'city': city, 'start': c['c0'], 'end': c['c1'], 'cuts': []}
                events.append(cur)
            cur['end'] = max(cur['end'], c['c1']); cur['cuts'].append(c)
    for e in events:
        hs = sorted({c['house'] for c in e['cuts']}, key=nat_key)
        e['houses'] = hs
        e['n'] = len(hs); e['n_city'] = len(by_city[e['city']])
        e['typ'] = round(median([c['dur'] for c in e['cuts']]))
        per = {}
        for c in e['cuts']:
            p = per.setdefault(c['house'], {'dur': 0, 'tot': 0})
            p['dur'] += c['dur']; p['tot'] += c['total']
        e['per'] = per
        e['with_gap'] = sum(1 for p in per.values() if p['tot'] > 0)
        worst = max(per.items(), key=lambda kv: (kv[1]['tot'], -nat_key(kv[0])[0]))
        e['max_gap'] = (worst[1]['tot'], worst[0]) if worst[1]['tot'] > 0 else None
        e['resp'] = {h: (max(0.0, (p['dur'] - p['tot']) / p['dur'] * 100) if p['dur'] else 0.0) for h, p in per.items()}
        e['resp_med'] = median(list(e['resp'].values()))
    events.sort(key=lambda e: e['start'])
    out['events'] = events

    # semáforo: veredicto del último corte de cada casa
    sem = {'total': [], 'transferencia': [], 'retardo': [], 'caida': [], 'sin': []}
    for h in houses_cut:
        last = H[h]['cuts'][-1]
        sem[last['verdict']].append(h)
    out['sem'] = sem

    # huecos de tensión sin corte asociado
    unl = [(h, g) for h in names for g in H[h]['unlinked']]
    out['unlinked'] = unl

    # ---------------- baterías al corte del reporte
    soc_rows = []
    for h in names:
        v = H[h]; s = v['soc_last']
        if s is None: continue
        soc_rows.append({'house': h, 'soc': s['v'], 'age': now - s['t'], 't': s['t'], 'city': v['city']})
    out['soc_rows'] = soc_rows
    out['reserva'] = [r for r in soc_rows if r['soc'] <= RESERVA]
    out['bajo50'] = sorted([r for r in soc_rows if r['soc'] <= 50], key=lambda r: (round(r['soc']), CITY_ORDER.index(r['city']), nat_key(r['house'])))
    out['sobre50'] = sum(1 for r in soc_rows if r['soc'] > 50)

    # ---------------- comunicación
    rows = []
    for h in names:
        v = H[h]
        v['inv_stale'] = False
        for key, label in (('inv', 'inversor'), ('red', 'medidor de red'), ('sol', 'medidor solar')):
            st, t = v['link'][key]
            gt, gs = v['gw']
            if gs == 'offline' and gt:                  # los equipos cuelgan del gateway: sin datos desde que cayó
                t = gt if (st != 'off' or t is None) else min(gt, t); st = 'off'
            if st == 'none' or now - t > STALE:
                rows.append({'house': h, 'city': v['city'], 'dev': label, 't': t, 'st': st})
                if key == 'inv': v['inv_stale'] = True
        t, st = v['gw']
        if st == 'offline':
            rows.append({'house': h, 'city': v['city'], 'dev': 'gateway (offline)', 't': t, 'st': 'off'})
    rows.sort(key=lambda r: (r['t'] if r['t'] is not None else 0, nat_key(r['house'])))
    out['comm_rows'] = rows
    out['inv_stale_houses'] = [h for h in names if H[h].get('inv_stale')]
    out['sin_red_ahora'] = {c: sum(1 for h in by_city[c] if H[h]['down_now']) for c in CITY_ORDER}

    # ---------------- ranking de exportación
    rank = []
    for h in names:
        v = H[h]
        if v['gen'] is None or v['win']['exp'] is None: continue
        rank.append(h)
    rank.sort(key=lambda h: (-H[h]['win']['exp'], nat_key(h)))
    out['rank_exp'] = rank
    out['n_no_export'] = sum(1 for h in rank if H[h]['win']['exp'] < 0.05)

    # ---------------- baterías llenas
    full = [(H[h]['full_t'], h) for h in names if H[h]['full_t'] is not None]
    full.sort(key=lambda x: (x[0], CITY_ORDER.index(H[x[1]]['city']), nat_key(x[1])))
    out['full'] = full
    out['no_full'] = [h for h in names if H[h]['full_t'] is None and H[h]['day_has_soc']]
    out['no_closing'] = [h for h in names if H[h]['gen'] is None]
    return out
