"""Cálculo del reporte operativo diario a partir de telemetría cruda de Metrum.

Todo se recalcula desde Metrum (eventos po/pr de medidores, contadores acumulados, SOC del inversor).
Las únicas entradas externas son kWp por sistema y el yield patrón por región (definidos por el equipo).
"""
from __future__ import annotations

import statistics

from data import inventory, local_ms, fmt_local, pmap, ts_query

H1 = 3600 * 1000
DAY = 24 * H1
YIELD_PATRON = {'Cali': 1188, 'Turbaco': 1323, 'Barranquilla': 1323, 'Cartagena': 1323}
CITY_ORDER = ['Cali', 'Turbaco', 'Barranquilla', 'Cartagena']
RESERVA = 20          # % SOC, igual para todos
ASSIGN_START = 75_000  # el hueco "empieza hasta 75 s del inicio" del corte
CLOCK_SKEW = 40_000    # los relojes de los medidores difieren hasta ~40 s
MAX_GAP_UNLINKED = 600_000  # un hueco sin corte de más de 10 min no se cuenta como "hueco de tensión"
LATE_MS = 10 * 60_000  # "el último que terminó hasta 10 min antes"
TRANSFER_MAX = 40_000  # transferencia aceptable: hasta ~40 s (el sesgo máximo de reloj entre medidores)
STALE = 2 * H1         # sin datos: más de 2 h


def pair_events(E):
    """[(ts, 'po'|'pr'|...)] -> ([(po, pr)], po_abierto)"""
    out, o = [], None
    for t, v in sorted(E):
        if v == 'po':
            o = t
        elif v == 'pr' and o is not None:
            out.append((o, t)); o = None
    return out, o


def nearest_at_or_before(P, t, maxage=None):
    c = [x for x in P if x[0] <= t]
    if not c: return None
    x = c[-1]
    if maxage is not None and t - x[0] > maxage: return None
    return x


def link_state(series):
    """('ok', ts_último_dato) | ('off', ts_inicio_de_la_caída) | ('none', None)."""
    if not series: return ('none', None)
    series = sorted(series)
    if series[-1][1] == 'succesful': return ('ok', series[-1][0])
    i = len(series) - 1
    while i >= 0 and series[i][1] != 'succesful': i -= 1
    run = series[i + 1:]                               # tramo final sin respuesta
    off = [t for t, v in run if v == 'offline']       # marcador de caída del enlace (si existe)
    return ('off', off[0] if off else run[0][0])


def closing(P, t, tol=H1):
    """Valor del contador acumulado en el cierre diario t (el punto más cercano a t, ±tol)."""
    c = [x for x in P if abs(x[0] - t) <= tol]
    if not c: return None
    x = min(c, key=lambda x: abs(x[0] - t))
    return float(x[1])


def delta(P, t0, t1):
    a, b = closing(P, t0), closing(P, t1)
    if a is None or b is None: return None
    return b - a


def day_energy(cl, d0):
    """Balance de medidores para el día calendario local que empieza en d0 (ms).
    cl = dict(solAI, redAI, redAE) -> series de cierres.  Devuelve kWh o None."""
    d1 = d0 + DAY
    sol = delta(cl['solAI'], d0, d1); imp = delta(cl['redAI'], d0, d1); exp = delta(cl['redAE'], d0, d1)
    if sol is None or imp is None or exp is None: return None
    if sol < 0 or imp < 0 or exp < 0: return None            # contador reiniciado / dato no confiable
    return {'cons': sol / 1000, 'imp': imp / 1000, 'exp': exp / 1000, 'gen': (sol - imp + exp) / 1000}


# ---------------------------------------------------------------- carga cruda
def load_house(h, I, A, B, now, D0, nprev):
    M = 30 * 60_000
    out = {}
    out['red_ev'] = ts_query(I['red'], 'event', A - M, B + M).get('event', [])
    out['sol_ev'] = ts_query(I['sol'], 'event', A - M, B + M).get('event', [])
    # inversor: el que reportó más recientemente
    best, bt = None, -1
    for iv in I['invs']:
        r = ts_query(iv, 'activityState', now - 14 * DAY, now, limit=1, desc=True).get('activityState', [])
        t = r[-1][0] if r else -1
        if t > bt: best, bt = iv, t
    out['inv'] = best or I['invs'][0]
    out['inv_last'] = bt if bt > 0 else None
    iv = out['inv']
    out['soc'] = ts_query(iv, 'BattSOC', D0 - 2 * H1, B + 2 * H1).get('BattSOC', [])
    out['volt'] = {k: ts_query(iv, k, now - 3 * H1, now + H1).get(k, []) for k in ('voltGridA', 'voltGridB', 'voltGridC')}
    # contadores de la ventana
    out['redAI'] = ts_query(I['red'], 'energyAI', A - 2 * H1, B + 2 * H1).get('energyAI', [])
    out['redAE'] = ts_query(I['red'], 'energyAE', A - 2 * H1, B + 2 * H1).get('energyAE', [])
    out['solAI'] = ts_query(I['sol'], 'energyAI', A - 2 * H1, B + 2 * H1).get('energyAI', [])
    # cierres diarios
    c0, c1 = D0 - (nprev + 1) * DAY - H1, D0 + DAY + H1 + DAY   # hasta D1 00:00 (y un margen)
    r = ts_query(I['red'], 'CenergyAI,CenergyAE', c0, c1, limit=200)
    s = ts_query(I['sol'], 'CenergyAI', c0, c1, limit=200)
    out['cl'] = {'redAI': r.get('CenergyAI', []), 'redAE': r.get('CenergyAE', []), 'solAI': s.get('CenergyAI', [])}
    # comunicación: estado de enlace al cierre (activityState: succesful / noResponse / offline)
    def link(dev):
        r = ts_query(dev, 'activityState', now - 14 * DAY, now, limit=3000).get('activityState', [])
        return link_state(r)
    out['link'] = {'inv': link(iv), 'red': link(I['red']), 'sol': link(I['sol'])}
    gw = ts_query(I['gw'], 'activityState', now - 90 * DAY, now, limit=1, desc=True).get('activityState', [])
    out['gw'] = (gw[-1][0], gw[-1][1]) if gw else (None, None)
    return out


# ---------------------------------------------------------------- cortes y respaldo
def assign_gaps(cuts, gaps):
    """Cada hueco cuenta en un solo corte: (1) el que empieza hasta 75 s de su inicio,
    (2) si no el que lo contiene, (3) si no el último que terminó hasta 10 min antes."""
    asg = {i: [] for i in range(len(cuts))}
    unlinked = []
    for g0, g1 in gaps:
        cand = [(abs(g0 - c0), i) for i, (c0, c1) in enumerate(cuts) if c0 - CLOCK_SKEW <= g0 <= c0 + ASSIGN_START]
        if cand:
            asg[min(cand)[1]].append((g0, g1)); continue
        cont = [i for i, (c0, c1) in enumerate(cuts) if c0 <= g0 <= c1]
        if cont:
            asg[cont[0]].append((g0, g1)); continue
        late = [i for i, (c0, c1) in enumerate(cuts) if c1 <= g0 <= c1 + LATE_MS]
        if late:
            asg[late[-1]].append((g0, g1)); continue
        unlinked.append((g0, g1))
    return asg, unlinked


def split_gap(c0, c1, g0, g1):
    """Reparte un hueco en 'al caer' / 'durante' / 'al volver' (segundos)."""
    caer = durante = volver = 0
    if g0 < c1:                                  # empieza dentro del corte
        inside = (min(g1, c1) - g0) / 1000
        after = max(0, g1 - c1) / 1000
        if g0 - c0 <= ASSIGN_START: caer += inside
        else: durante += inside
        volver += after
    else:                                        # empieza después de que volvió la red
        if g0 - c0 <= ASSIGN_START: caer += (g1 - g0) / 1000
        else: volver += (g1 - g0) / 1000
    return caer, durante, volver


def soc_at(P, t, side):
    """SOC (muestra del inversor, ~15 min). side='before': última muestra <= t; 'after': primera >= t."""
    if not P: return None
    if side == 'before':
        c = [x for x in P if x[0] <= t]
        x = c[-1] if c else P[0]
    else:
        c = [x for x in P if x[0] >= t]
        x = c[0] if c else P[-1]
    return float(x[1])


def verdict(dur, total, caer, durante, volver):
    if total <= 0: return 'total'
    resp = max(0.0, (dur - total) / dur) if dur > 0 else 0.0
    if resp <= 0: return 'sin'
    if durante >= 10: return 'caida'
    if caer + volver > TRANSFER_MAX / 1000: return 'retardo'
    return 'transferencia'


def analyze_cuts(h, raw, A, B, now):
    red_pairs, red_open = pair_events(raw['red_ev'])
    sol_pairs, sol_open = pair_events(raw['sol_ev'])
    cuts = [c for c in red_pairs if A <= c[0] < B]
    gaps = [g for g in sol_pairs if A - LATE_MS <= g[0] <= B + LATE_MS]
    asg, unlinked = assign_gaps(cuts, gaps)
    res = []
    for i, (c0, c1) in enumerate(cuts):
        dur = round((c1 - c0) / 1000)
        caer = durante = volver = 0.0
        for g0, g1 in asg[i]:
            a, d, v = split_gap(c0, c1, g0, g1)
            caer += a; durante += d; volver += v
        caer, durante, volver = round(caer), round(durante), round(volver)
        total = sum(round((g1 - g0) / 1000) for g0, g1 in asg[i])
        resp = max(0.0, (dur - total) / dur * 100) if dur > 0 else 0.0
        s0 = soc_at(raw['soc'], c0, 'before'); s1 = soc_at(raw['soc'], c1, 'after')
        smin = None
        if dur >= 300:
            inside = [float(v) for t, v in raw['soc'] if c0 <= t <= c1]
            if inside: smin = min(inside)
        res.append({'gaps': [[g0, g1] for g0, g1 in asg[i]], 'c0': c0, 'c1': c1, 'dur': dur, 'caer': caer, 'durante': durante, 'volver': volver,
                    'total': total, 'resp': resp, 'soc0': s0, 'soc1': s1, 'socmin': smin,
                    'verdict': verdict(dur, total, caer, durante, volver)})
    unl = [round((g1 - g0) / 1000) for g0, g1 in unlinked if 10_000 <= g1 - g0 <= MAX_GAP_UNLINKED]
    return res, red_open, [g for g in unlinked if 10_000 <= g[1] - g[0] <= MAX_GAP_UNLINKED]


def grid_down_now(raw, now):
    """Sin red al cierre: tensión de red del inversor < 5 V en las 3 fases en la última muestra reciente."""
    last = []
    for k, S in raw['volt'].items():
        x = nearest_at_or_before(S, now, maxage=30 * 60_000)
        last.append(None if x is None else float(x[1]))
    return all(v is not None and v < 5 for v in last)


# ---------------------------------------------------------------- build
def build(A, now=None, nprev=14, energy_end=None):
    """A: inicio de ventana (ms, 07:00 local).  now: instante del reporte (por defecto el fin de ventana)."""
    B = A + DAY
    now = now or B
    D0 = A - 7 * H1                       # medianoche local del día D0
    D1 = D0 + DAY
    inv = inventory()
    H = list(inv)
    raws = dict(zip(H, pmap(lambda h: load_house(h, inv[h], A, B, now, D0, nprev), H)))
    R = {'A': A, 'B': B, 'now': now, 'D0': D0, 'D1': D1, 'houses': {}}
    e_end = energy_end if energy_end is not None else min(B, now)
    for h in H:
        I, raw = inv[h], raws[h]
        cuts, red_open, unlinked = analyze_cuts(h, raw, A, B, now)
        # energía de la ventana (contadores acumulados)
        def rd(P, t):
            x = nearest_at_or_before(P, t, maxage=2 * H1)
            return None if x is None else float(x[1])
        def dwin(P, t0, t1):
            a, b = rd(P, t0), rd(P, t1)
            return None if a is None or b is None else (b - a) / 1000
        w = {'imp': dwin(raw['redAI'], A, e_end), 'exp': dwin(raw['redAE'], A, e_end),
             'exp_a': dwin(raw['redAE'], A, D1), 'exp_b': dwin(raw['redAE'], D1, e_end),
             'cons_resp': dwin(raw['solAI'], A, e_end)}
        # día D0 y días previos
        day = day_energy(raw['cl'], D0)
        prev = [day_energy(raw['cl'], D0 - k * DAY) for k in range(1, nprev + 1)]
        # SOC
        socs = raw['soc']
        gw_t, gw_st = raw['gw']
        soc_until = min(now, gw_t) if gw_st == 'offline' and gw_t else now      # gateway caído: sin datos desde entonces
        lastsoc = nearest_at_or_before(socs, soc_until, maxage=48 * H1)
        full_t = None
        day_pts = [(t, float(v)) for t, v in socs if D0 + 6 * H1 <= t < D1]
        for t, v in day_pts:
            if v >= 99: full_t = t; break
        R['houses'][h] = {
            'house': h, 'city': I['city'], 'kwp': I['kwp'], 'equip': I['equip'], 'inv': raw['inv'],
            'cuts': cuts, 'red_open': red_open, 'unlinked': unlinked,
            'down_now': grid_down_now(raw, now) or (red_open is not None and red_open < now),
            'win': w, 'day': day, 'prev': prev,
            'soc_last': None if lastsoc is None else {'t': lastsoc[0], 'v': float(lastsoc[1])},
            'full_t': full_t, 'day_has_soc': bool(day_pts),
            'link': raw['link'], 'gw': raw['gw'],
            'soc_series': [(t, float(v)) for t, v in socs],
        }
    return R
