"""Genera el HTML del reporte operativo diario (tablero oscuro, una sola página, gráficos SVG inline).

Entrada: el diccionario de compute.build(); salida: HTML autocontenido (solo carga las fuentes de Google Fonts).
"""
from __future__ import annotations

import datetime
import html
import math
import os
import time

from aggregate import *
from data import ASSETS, TZ, UTC

CSS = open(os.path.join(ASSETS, 'report.css'), encoding='utf-8').read()
LOGO = open(os.path.join(ASSETS, 'logo.datauri.txt')).read().strip()
TAIL = open(os.path.join(ASSETS, 'tooltip.html'), encoding='utf-8').read()

MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
DIA3 = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
DIAF = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
VER = {'total': 'Respaldo total', 'transferencia': 'Respaldo total con transferencia',
       'retardo': 'Retardo de transferencia', 'caida': 'Caída durante el respaldo', 'sin': 'Sin respaldo'}
VER_PILL = {'total': 'okp', 'transferencia': 'okp', 'retardo': 'warn', 'caida': 'crit', 'sin': 'crit'}
esc = html.escape


# ---------------------------------------------------------------- formato
def dtm(t): return datetime.datetime.fromtimestamp((t + TZ) / 1000, UTC)
def d_short(t): d = dtm(t); return f"{d.day} {MES[d.month - 1]}"
def hm(t): return dtm(t).strftime('%H:%M')
def dh(t): return f"{d_short(t)} {hm(t)}"
def wd3(t): return DIA3[dtm(t).weekday()]
def wdf(t): return DIAF[dtm(t).weekday()]
def n1(x, d=1): return f"{x:.{d}f}".replace('.', ',')
def pct1(x): return n1(x, 1) + ' %'
def pct0(x): return f"{round(x)} %"

def fdur(s):
    s = int(round(s))
    if s < 60: return f"{s} s"
    m, ss = divmod(s, 60)
    if m < 60: return f"{m} min {ss:02d} s" if ss else f"{m} min"
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min"

def fhace(ms):
    s = int(ms // 1000)
    if s < 3600:
        return f"{s // 60} min {s % 60:02d} s"
    h, m = divmod(s // 60, 60)
    if h >= 72:
        d, h = divmod(h, 24); return f"{d} d {h} h"
    return f"{h} h {m:02d} min"

def plural(n, s, p): return s if n == 1 else p
def join_es(xs): return ', '.join(xs)


# ---------------------------------------------------------------- gráficos
def svg_cortes(O, H):
    """Timeline de cortes por casa."""
    A, B = O['A'], O['B']
    X = lambda t: 96 + (t - A) / (B - A) * 880
    rows = []                       # (kind, y, payload)
    ynext = 28                      # primera fila libre (cada casa ocupa 17 px)
    first = True
    for city in CITY_ORDER:
        hs = [h for h in O['by_city'][city] if H[h]['cuts']]
        if not hs: continue
        ycity = (ynext + 21) if first else (ynext + 9)
        rows.append(('city', ycity, city))
        yt = ycity + 18
        for h in hs:
            rows.append(('house', yt, h)); yt += 17
        ynext = yt
        first = False
    last_text = max(r[1] for r in rows if r[0] == 'house')
    bottom = last_text + 5 + 3
    out = []
    # eje: marcas cada 3 h desde A+1 h
    k = 0
    while True:
        t = A + (1 + 3 * k) * H1
        if t >= B: break
        x = X(t)
        out.append(f'<line class="grid" x1="{x:.1f}" y1="28" x2="{x:.1f}" y2="{bottom}"/>')
        out.append(f'<text class="ax ax-f" x="{x:.1f}" y="11" text-anchor="middle">{wd3(t)} {d_short(t)}</text>')
        out.append(f'<text class="ax" x="{x:.1f}" y="24" text-anchor="middle">{hm(t)}</text>')
        k += 1
    for kind, yy, pl in rows:
        if kind == 'city':
            out.append(f'<text class="lbl" x="4" y="{yy}">{pl}</text>')
            continue
        h = pl
        out.append(f'<text class="sm" x="88" y="{yy}" text-anchor="end">{esc(h)}</text>')
        out.append(f'<line class="lane" x1="96" y1="{yy + 5}" x2="976" y2="{yy + 5}"/>')
        for c in H[h]['cuts']:
            title = (f"{h} · {hm(c['c0'])}–{hm(c['c1'])} · sin red {fdur(c['dur'])} · la casa vio {fdur(c['total'])}"
                     f" · respaldo {pct1(c['resp'])} · SOC al inicio {round(c['soc0']) if c['soc0'] is not None else '—'} % · {VER[c['verdict']]}")
            by = yy - 9
            bx = X(c['c0']); bw = max(4.0, X(c['c1']) - X(c['c0']))
            g = [f'<g class="tg"><title>{esc(title)}</title>',
                 f'<rect class="tl g" x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="12" rx="2"/>']
            for g0, g1 in c['gaps']:
                segs = []
                if g0 < c['c1']: segs.append((g0, min(g1, c['c1'])))
                if g1 > c['c1']: segs.append((max(g0, c['c1']), g1))
                for s0, s1 in segs:
                    g.append(f'<rect class="tl c" x="{X(s0):.1f}" y="{by}" width="{max(2.0, X(s1) - X(s0)):.1f}" height="12"/>')
            g.append('</g>')
            out.append(''.join(g))
    h_total = bottom + 20
    return (f'<svg viewBox="0 0 1008 {h_total}" role="img" aria-label="Cortes de red por casa en la ventana, coloreados por veredicto de respaldo" '
            f'style="min-width:760px">' + ''.join(out) + '</svg>')


def svg_heatmap(O, H):
    ev = O['events']; hs = O['houses_cut']
    W = 93 + 62 * len(ev) + 7; Ht = 55 + 19 * len(hs) + 5
    out = []
    for j, e in enumerate(ev):
        cx = 93 + 30 + 62 * j
        out.append(f'<text class="ax ax-f" x="{cx:.1f}" y="12" text-anchor="middle">{wd3(e["start"])} {d_short(e["start"])}</text>')
        out.append(f'<text class="ax" x="{cx:.1f}" y="27" text-anchor="middle">{e["city"]}</text>')
        out.append(f'<text class="ax" x="{cx:.1f}" y="40" text-anchor="middle">{hm(e["start"])}</text>')
    for i, h in enumerate(hs):
        y0 = 55 + 19 * i
        out.append(f'<text class="sm" x="84" y="{y0 + 13}" text-anchor="end">{esc(h)}</text>')
        for j, e in enumerate(ev):
            x0 = 93 + 62 * j
            if h not in e['per']:
                out.append(f'<rect class="hm n" x="{x0}" y="{y0}" width="60" height="17" rx="2"/>')
                continue
            p = e['per'][h]; r = e['resp'][h]
            cls = 'g' if r >= 99 else ('w' if r >= 90 else 'c')
            title = f"{h} · {e['city']} {dh(e['start'])} · respaldo {pct1(r)} · la casa vio {fdur(p['tot'])}"
            out.append(f'<g><title>{esc(title)}</title><rect class="hm {cls}" x="{x0}" y="{y0}" width="60" height="17" rx="2"/>'
                       f'<text class="hmt {cls}" x="{x0 + 30:.1f}" y="{y0 + 13}" text-anchor="middle">{round(r)}</text></g>')
    return (f'<svg viewBox="0 0 {W} {Ht}" role="img" aria-label="Porcentaje de respaldo de cada casa en cada evento de red" '
            f'style="width:{W}px;min-width:0;max-width:none">' + ''.join(out) + '</svg>')


BUCKETS = [('Sin hueco', lambda t: t == 0, 'g'), ('Menos de 30 s', lambda t: 0 < t < 30, 'a'),
           ('30 s a 2 min', lambda t: 30 <= t < 120, 'a'), ('2 a 5 min', lambda t: 120 <= t < 300, 'w'),
           ('5 min o más', lambda t: t >= 300, 'c')]

def svg_hueco(O, H):
    cuts = O['cuts']
    groups = []
    for name, fn, cls in BUCKETS:
        cs = [c for c in cuts if fn(c['total'])]
        groups.append((name, cls, cs))
    mx = max(1, max(len(g[2]) for g in groups))
    out = []
    for i, (name, cls, cs) in enumerate(groups):
        y0 = 6 + 28 * i
        w = max(2.0, len(cs) / mx * 640)
        names = []
        seen = {}
        for c in sorted(cs, key=lambda c: (nat_key(c['house']), c['c0'])): seen[c['house']] = seen.get(c['house'], 0) + 1
        for hname, n in seen.items(): names.append(hname + (f' ×{n}' if n > 1 else ''))
        title = f"{name}: {len(cs)} {plural(len(cs), 'corte', 'cortes')} · " + (join_es(names) if names else 'ninguna casa')
        out.append(f'<g class="hg"><title>{esc(title)}</title><rect class="hitb" x="0" y="{y0}" width="780" height="24"/>'
                   f'<text class="sm" x="4" y="{y0 + 15}">{name}</text>'
                   f'<rect class="hb {cls}" x="110" y="{y0 + 2}" width="{w:.1f}" height="18" rx="3"/>'
                   f'<text class="lbl" x="{110 + w + 8:.1f}" y="{y0 + 16}">{len(cs)}</text></g>')
    return ('<svg viewBox="0 0 800 152" role="img" aria-label="Cantidad de cortes según el tiempo que la casa vio la interrupción" '
            'style="min-width:560px">' + ''.join(out) + '</svg>')


def svg_bateria_corte(O, H):
    """Batería durante el corte más largo de cada casa (cortes de 5 min o más)."""
    rows = []
    for h in O['houses_cut']:
        long_ = [c for c in H[h]['cuts'] if c['dur'] >= 300]
        if long_:
            rows.append((h, max(long_, key=lambda c: c['dur'])))
    rows.sort(key=lambda r: (r[1]['soc0'] if r[1]['soc0'] is not None else 0, nat_key(r[0])))
    X = lambda v: 90 + v * 7.0
    ybot = 14 + 17 * len(rows)
    out = []
    for v in (0, 20, 40, 60, 80, 100):
        cls = 'lim' if v == 20 else 'grid'
        out.append(f'<line class="{cls}" x1="{X(v):.1f}" y1="14" x2="{X(v):.1f}" y2="{ybot}"/>')
        out.append(f'<text class="ax" x="{X(v):.1f}" y="{ybot + 14}" text-anchor="middle">{v} %</text>')
    for i, (h, c) in enumerate(rows):
        yy = 14 + 17 * i + 8
        s0, s1, sm = c['soc0'], c['soc1'], c['socmin']
        low = (sm if sm is not None else min(s0, s1)) <= RESERVA
        title = f"{h} · {hm(c['c0'])}–{hm(c['c1'])} · {fdur(c['dur'])} · SOC {round(s0)} → {'—' if sm is None else round(sm)} → {round(s1)} %"
        r = ' r' if low else ''
        parts = [f'<g class="dm"><title>{esc(title)}</title><rect class="hit" x="0" y="{yy - 8}" width="900" height="17"/>',
                 f'<text class="sm" x="84" y="{yy + 4}" text-anchor="end">{esc(h)}</text>',
                 f'<line class="dl2{r}" x1="{X(s0):.1f}" y1="{yy}" x2="{X(s1):.1f}" y2="{yy}"/>']
        if sm is not None:
            parts.append(f'<line class="mn{r}" x1="{X(sm):.1f}" y1="{yy - 6}" x2="{X(sm):.1f}" y2="{yy + 6}"/>')
        parts.append(f'<circle class="d0" cx="{X(s0):.1f}" cy="{yy}" r="5"/><circle class="d1{r}" cx="{X(s1):.1f}" cy="{yy}" r="4"/>')
        parts.append(f'<text class="soc-n" x="{max(X(s0), X(s1)) + 12:.1f}" y="{yy + 4}">{round(s0)} → {round(s1)} %</text></g>')
        out.append(''.join(parts))
    nlow = sum(1 for h, c in rows if (c['socmin'] if c['socmin'] is not None else min(c['soc0'], c['soc1'])) <= RESERVA)
    return (f'<svg viewBox="0 0 900 {ybot + 22}" role="img" aria-label="Carga de la batería al inicio y al final del corte más largo de cada casa" '
            f'style="min-width:720px">' + ''.join(out) + '</svg>'), len(rows), nlow


def svg_gen_cons(O):
    rows = [(c, O['cities'][c]) for c in CITY_ORDER] + [('Portafolio Sunny', {'gen': O['gen'], 'cons': O['cons'], 'cov': O['cov']})]
    mx = max(r[1]['cons'] for r in rows) or 1
    out = []
    for i, (name, v) in enumerate(rows):
        y0 = 12 + 50 * i
        wg = v['gen'] / mx * 600; wc = v['cons'] / mx * 600
        out.append(f'<text class="lbl" x="4" y="{y0 + 20}">{name}</text>')
        out.append(f'<rect class="gb gen" x="130" y="{y0}" width="{wg:.1f}" height="16" rx="3"><title>{name} · generación FV {round(v["gen"])} kWh</title></rect>')
        out.append(f'<text class="sm" x="{130 + wg + 6:.1f}" y="{y0 + 13}">{round(v["gen"])} kWh</text>')
        out.append(f'<rect class="gb con" x="130" y="{y0 + 20}" width="{wc:.1f}" height="16" rx="3"><title>{name} · consumo de los clientes {round(v["cons"])} kWh</title></rect>')
        out.append(f'<text class="sm" x="{130 + wc + 6:.1f}" y="{y0 + 33}">{round(v["cons"])} kWh</text>')
        out.append(f'<text class="lbl" x="880" y="{y0 + 24}" text-anchor="end">{round(v["cov"]) if v["cov"] is not None else "—"} %</text>')
    out.append('<text class="ax" x="880" y="6" text-anchor="end">cobertura</text>')
    return ('<svg viewBox="0 0 890 266" role="img" aria-label="Generación FV frente al consumo de los clientes por ciudad" '
            'style="min-width:720px">' + ''.join(out) + '</svg>')


def svg_ranking_export(O, H):
    rank = O['rank_exp']
    mx = max([H[h]['win']['exp'] for h in rank] + [0])
    dom = max(5, math.ceil(mx))
    sc = 620 / dom
    ybot = 10 + 17 * len(rank)
    out = []
    for v in range(0, dom + 1):
        x = 116 + v * sc
        out.append(f'<line class="grid" x1="{x:.1f}" y1="10" x2="{x:.1f}" y2="{ybot}"/>')
        out.append(f'<text class="ax" x="{x:.1f}" y="{ybot + 14}" text-anchor="middle">{v}{" kWh" if v == dom else ""}</text>')
    for i, h in enumerate(rank):
        v = H[h]; e = v['win']['exp']; imp = v['win']['imp'] or 0; gen = v['gen']
        y0 = 10 + 17 * i
        pexp = e / gen * 100 if gen else 0
        title = (f"#{i + 1} {h} · exportada {n1(e, 2)} kWh ({n1(e, 3)} kWh) · importada {n1(imp, 1)} kWh · generó {n1(gen, 1)} kWh"
                 f" · exportó el {n1(pexp, 1)} % de lo generado")
        parts = [f'<g class="dm"><title>{esc(title)}</title><rect class="hit" x="0" y="{y0}" width="816" height="17"/>',
                 f'<text class="sm" x="108" y="{y0 + 12}" text-anchor="end">{i + 1}. {esc(h)}</text>']
        if round(e, 3) > 0:
            w = max(2.0, e * sc)
            parts.append(f'<rect class="gb gen" x="116" y="{y0 + 2}" width="{w:.1f}" height="12" rx="2"/>')
            parts.append(f'<text class="soc-n" x="{116 + w + 6:.1f}" y="{y0 + 12}">{n1(e, 2)} kWh</text>')
        else:
            parts.append(f'<text class="soc-n" x="122.0" y="{y0 + 12}">{n1(e, 2)} kWh</text>')
        parts.append('</g>')
        out.append(''.join(parts))
    return (f'<svg viewBox="0 0 816 {ybot + 22}" role="img" aria-label="Ranking de las casas por energía exportada a la red" '
            f'style="min-width:720px">' + ''.join(out) + '</svg>')


def svg_yield(O, H):
    X = lambda p: 96 + p * 5.25
    out = []
    ticks = [(0, 'grid'), (25, 'grid'), (50, 'grid'), (75, 'grid'), (90, 'lim'), (100, 'pat'), (125, 'grid'), (150, 'grid')]
    n = len(CITY_ORDER)
    ybot = 14 + 40 * n
    for p, cls in ticks:
        out.append(f'<line class="{cls}" x1="{X(p):.1f}" y1="14" x2="{X(p):.1f}" y2="{ybot}"/>')
        out.append(f'<text class="ax" x="{X(p):.1f}" y="{ybot + 14}" text-anchor="middle">{p} %</text>')
    n_low = 0
    for i, city in enumerate(CITY_ORDER):
        base = 40 * i
        out.append(f'<text class="lbl" x="4" y="{base + 38}">{city}</text>')
        out.append(f'<line class="lane" x1="96" y1="{base + 54}" x2="936" y2="{base + 54}"/>')
        hs = [h for h in O['by_city'][city] if H[h]['pct'] is not None]
        hs.sort(key=lambda h: (H[h]['pct'], nat_key(h)))
        for k, h in enumerate(hs):
            v = H[h]; p = v['pct']
            cls = 'ok' if p >= 90 else 'w'
            if p < 90: n_low += 1
            title = f"{h} · yield {round(v['yield'])} kWh/kWp·año · {round(p)} % del patrón" + (f" · {v['alert']}" if v['alert'] else '')
            out.append(f'<circle class="yd {cls}" cx="{min(X(p), 936):.1f}" cy="{base + 28 + 8 * (k % 3)}" r="5"><title>{esc(title)}</title></circle>')
    return (f'<svg viewBox="0 0 956 {ybot + 22}" role="img" aria-label="Yield proyectado de cada casa frente al patrón de su región" '
            f'style="min-width:720px">' + ''.join(out) + '</svg>'), n_low


def svg_full(O, H):
    D0 = O['D0']
    X = lambda t: 92 + ((t - D0) / H1 - 6) * (760 / 12)
    full = O['full']
    n = len(full)
    ybot = 31.0 + 17 * (n - 1) if n else 14
    out = []
    for hh in range(6, 19, 2):
        x = 92 + (hh - 6) * (760 / 12)
        out.append(f'<line class="grid" x1="{x:.1f}" y1="14" x2="{x:.1f}" y2="{ybot:.0f}"/>')
        out.append(f'<text class="ax" x="{x:.1f}" y="{ybot + 14:.0f}" text-anchor="middle">{hh:02d}:00</text>')
    out.append(f'<line class="lim" x1="472.0" y1="14" x2="472.0" y2="{ybot:.0f}"/>')
    for i, (t, h) in enumerate(full):
        lane = 31.0 + 17 * i
        hh = (t - D0) / H1
        if hh < 12: cls, tag = 'w', ' · producción limitada'
        elif hh < 16: cls, tag = 't', ' · producción limitada en la tarde'
        else: cls, tag = 'ok', ''
        cx = min(max(X(t), 92), 852)
        out.append(f'<g class="dm"><title>{esc(h)} · batería a 99 % a las {hm(t)}{tag}</title>'
                   f'<text class="sm" x="84" y="{lane - 4.5}" text-anchor="end">{esc(h)}</text>'
                   f'<line class="lane" x1="92" y1="{lane:.1f}" x2="852" y2="{lane:.1f}"/>'
                   f'<circle class="yd {cls}" cx="{cx:.1f}" cy="{lane - 8.5}" r="5"/>'
                   f'<text class="soc-n" x="{cx + 9:.1f}" y="{lane - 4.5}">{hm(t)}</text></g>')
    return (f'<svg viewBox="0 0 862 {ybot + 22:.0f}" role="img" aria-label="Hora en que la batería de cada casa llegó a carga completa" '
            f'style="min-width:720px">' + ''.join(out) + '</svg>')


BAT_ICON = ('<svg class="bat-lg" width="12" height="8" viewBox="0 0 12 8" aria-hidden="true"><rect class="bat" x="0.5" y="0.5" width="9" height="7" rx="1.2"/>'
            '<rect class="bat-f" x="2" y="2" width="3.5" height="4"/><rect class="bat-f" x="9.5" y="2.5" width="1.5" height="3"/></svg>')


# ---------------------------------------------------------------- piezas HTML
def pill(cls, text): return f'<span class="pill {cls}">{esc(text)}</span>'

def names_or_count(hs):
    if not hs: return 'ninguna'
    return join_es(hs) if len(hs) <= 6 else f'{len(hs)} casas (ver tabla)'


def semaforo(O):
    spec = [('total', 'g', '✓'), ('transferencia', 'g', '✓'), ('retardo', 'w', '▲'), ('caida', 'c', '✕'), ('sin', 'c', '✕')]
    cards = []
    for k, cls, ic in spec:
        hs = O['sem'][k]
        cards.append(f'<div class="sm-card {cls}"><div class="t"><span class="ic" aria-hidden="true">{ic}</span>{VER[k]}</div>'
                     f'<div class="v">{len(hs)}</div><small>{esc(names_or_count(hs))}</small></div>')
    return '<div class="sema">' + ''.join(cards) + '</div>'


def city_cards(O, H):
    cards = []
    for c in CITY_ORDER:
        hs = O['by_city'][c]; v = O['cities'][c]
        cut_h = [h for h in hs if H[h]['cuts']]
        worst = [H[h]['cuts'][-1]['verdict'] for h in cut_h]
        if any(w in ('sin', 'caida') for w in worst): cls, ic = 'c', '✕'
        elif any(w == 'retardo' for w in worst): cls, ic = 'w', '▲'
        else: cls, ic = 'g', '✓'
        res = sum(1 for r in O['reserva'] if r['city'] == c)
        cards.append(
            f'<div class="sm-card {cls}"><div class="t"><span class="ic" aria-hidden="true">{ic}</span>{c}</div>'
            f'<div class="v">{len(cut_h)}<span class="de"> de {len(hs)}</span></div><small>sistemas con cortes</small>'
            f'<div class="kv"><span>Generación</span><b>{round(v["gen"])} kWh</b></div>'
            f'<div class="kv"><span>Cobertura solar</span><b>{pct0(v["cov"]) if v["cov"] is not None else "—"}</b></div>'
            f'<div class="kv"><span>Yield vs patrón</span><b>{pct0(v["vs_patron"]) if v["vs_patron"] is not None else "—"}</b></div>'
            f'<div class="kv"><span>Baterías en reserva</span><b>{res}</b></div></div>')
    return '<div class="sema">' + ''.join(cards) + '</div>'


def soc_grid(O):
    rows = []
    for r in O['bajo50']:
        cls = 'crit' if r['soc'] <= RESERVA else 'warn'
        rows.append(f'<div class="soc-row"><span class="sn">{esc(r["house"])}</span><div class="soc"><div class="track">'
                    f'<i class="{cls}" style="width:{round(r["soc"])}%"></i><b style="left:20%" title="reserva 20 %"></b></div>'
                    f'<span class="num">{round(r["soc"])} %</span></div></div>')
    return '<div class="soc-grid">' + ''.join(rows) + '</div>'


def table_ciudad(O):
    rows = ['<tr><th>Ciudad</th><th class="n">Sistemas</th><th class="n">Con<br>cortes</th><th class="n">Cortes</th><th class="n">Sin red<br>ahora</th>'
            '<th class="n">Generación<br>FV kWh</th><th class="n">Yield anual proyectado<br>kWh/kWp·año</th><th class="n">Cobertura<br>solar</th><th class="n">Exportada<br>kWh</th></tr>']
    H = O['_H']
    for c in CITY_ORDER:
        v = O['cities'][c]; hs = O['by_city'][c]
        con = sum(1 for h in hs if H[h]['cuts']); nc = sum(len(H[h]['cuts']) for h in hs)
        rows.append(f'<tr><td><b>{c}</b></td><td class="n">{len(hs)}</td><td class="n">{con}</td><td class="n">{nc}</td>'
                    f'<td class="n">{O["sin_red_ahora"][c]}</td><td class="n">{round(v["gen"])}</td>'
                    f'<td class="n">{round(v["yield"]) if v["yield"] is not None else "—"}</td>'
                    f'<td class="n">{pct0(v["cov"]) if v["cov"] is not None else "—"}</td><td class="n">{n1(v["exp"], 1)}</td></tr>')
    return '<table class="dt" style="min-width:760px"><thead>' + rows[0] + '</thead><tbody>' + ''.join(rows[1:]) + '</tbody></table>'


def table_eventos(O):
    rows = []
    for e in O['events']:
        mg = e['max_gap']
        mgc = f'{fdur(mg[0])}<small>{esc(mg[1])}</small>' if mg else '—<small></small>'
        rows.append(f'<tr><td>{e["city"]}</td><td>{dh(e["start"])}</td><td>{dh(e["end"])}</td><td class="n">{e["n"]} de {e["n_city"]}</td>'
                    f'<td class="n">{fdur(e["typ"])}</td><td class="n">{e["with_gap"]} de {e["n"]}</td><td class="n">{mgc}</td>'
                    f'<td class="n">{pct1(e["resp_med"])}</td></tr>')
    head = ('<tr><th>Ciudad</th><th>Inicio</th><th>Fin</th><th class="n">Sistemas<br>afectados</th><th class="n">Duración<br>típica</th>'
            '<th class="n">Casas con<br>hueco</th><th class="n">Mayor tiempo<br>sin tensión</th><th class="n">Respaldo<br>mediano</th></tr>')
    return '<table class="dt" style="min-width:900px"><thead>' + head + '</thead><tbody>' + ''.join(rows) + '</tbody></table>'


def table_sistema(O, H):
    hs = sorted(O['houses_cut'], key=lambda h: (-sum(c['dur'] for c in H[h]['cuts']), nat_key(h)))
    maxprev = max([len(H[h]['cuts']) - 1 for h in hs] + [0])
    head = ['<th>Sistema</th>', '<th class="n">Cortes</th>', '<th class="n">Tiempo<br>sin red</th>', '<th class="n">Tiempo que<br>vio la casa</th>',
            '<th>Último corte<br>inicio → fin · duración<br>SOC inicio → fin · respaldo</th>']
    for k in range(1, maxprev + 1):
        head.append(f'<th class="n">Anterior {k}<br>% respaldo<br>hora · sin red · vio</th>')
    head += ['<th>Ahora</th>', '<th>Veredicto de respaldo<br>(último corte)</th>']
    rows = []
    for h in hs:
        v = H[h]; cs = v['cuts']; last = cs[-1]
        tdur = sum(c['dur'] for c in cs); tvio = sum(c['total'] for c in cs)
        soc = f"SOC {round(last['soc0'])} → {round(last['soc1'])} %" if last['soc0'] is not None else 'SOC —'
        cells = [f'<td><b>{esc(h)}</b><small>{v["city"]} · {esc(v["equip"])}</small></td>',
                 f'<td class="n">{len(cs)}</td>', f'<td class="n">{fdur(tdur)}</td>',
                 f'<td class="n">{fdur(tvio) if tvio else "—"}</td>',
                 f'<td style="white-space:nowrap"><b>{dh(last["c0"])} → {hm(last["c1"])}</b><small>{fdur(last["dur"])}</small>'
                 f'<small>{soc}</small><small>respaldo {pct1(last["resp"])}</small></td>']
        prev = list(reversed(cs[:-1]))
        for k in range(maxprev):
            if k < len(prev):
                c = prev[k]
                cells.append(f'<td class="n"><small title="{dh(c["c0"])} · {fdur(c["dur"])}">{pct1(c["resp"])}</small><small>{dh(c["c0"])}</small>'
                             f'<small>sin red: {fdur(c["dur"])}</small><small>vio: {fdur(c["total"])}</small></td>')
            else:
                cells.append('<td></td>')
        cells.append(f'<td>{pill("crit", "sin red") if v["down_now"] else ""}</td>')
        sub = (f'tiempo que vio la casa: {fdur(last["total"])}' + (', sin hueco' if last['total'] == 0 else ''))
        cells.append(f'<td>{pill(VER_PILL[last["verdict"]], VER[last["verdict"]])}<small>{sub}</small></td>')
        rows.append('<tr class="">' + ''.join(cells) + '</tr>')
    return '<table class="dt" style="min-width:900px"><thead><tr>' + ''.join(head) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'


def table_detalle(O, H):
    cuts = sorted(O['cuts'], key=lambda c: (nat_key(c['house']), c['c0']))
    head = ('<tr><th>Sistema</th><th>Inicio</th><th>Fin</th><th class="n">Duración</th><th class="n">Hueco<br>al caer</th><th class="n">Hueco<br>durante</th>'
            '<th class="n">Hueco<br>al volver</th><th class="n">Total que<br>vio la casa</th><th class="n">Respaldo</th><th class="n">SOC inicio → mín → fin</th></tr>')
    rows = []
    d = lambda s: fdur(s) if s else '—'
    for c in cuts:
        soc = ('—' if c['soc0'] is None else f"{round(c['soc0'])} → {'—' if c['socmin'] is None else round(c['socmin'])} → {round(c['soc1'])} %")
        rows.append(f'<tr><td><b>{esc(c["house"])}</b><small>{c["city"]}</small></td><td>{dh(c["c0"])}</td><td>{dh(c["c1"])}</td>'
                    f'<td class="n">{fdur(c["dur"])}</td><td class="n">{d(c["caer"])}</td><td class="n">{d(c["durante"])}</td><td class="n">{d(c["volver"])}</td>'
                    f'<td class="n">{d(c["total"])}</td><td class="n">{pct1(c["resp"])}</td><td class="n">{soc}</td></tr>')
    return ('<table class="dt" style="min-width:900px"><thead>' + head + '</thead><tbody>' + ''.join(rows) + '</tbody></table>')


def table_rendimiento(O, H):
    d0 = O['D0']
    head = (f'<tr><th>Sistema</th><th class="n">{wd3(d0)} {d_short(d0)}<br>00:00–24:00<br>kWh</th><th class="n">Total<br>kWh</th>'
            '<th class="n">Yield anual<br>proyectado<br>kWh/kWp·año</th><th class="n">Frente al<br>yield patrón</th><th>Alerta</th></tr>')
    rows = []
    for c in CITY_ORDER:
        rows.append(f'<tr class="ciudad"><td colspan="6">{c} · yield patrón {YIELD_PATRON[c]} kWh/kWp·año</td></tr>')
        for h in O['by_city'][c]:
            v = H[h]
            first = f'<td><b>{esc(h)}</b><small>{esc(v["equip"])} · {n1(v["kwp"], 2)} kWp</small></td>'
            if v['gen'] is None:
                rows.append('<tr>' + first + '<td class="n">—</td><td class="n"><b>—</b></td><td class="n">—</td><td class="n">—</td>'
                            f'<td>{pill("off", "sin cierre diario del medidor")}</td></tr>')
            else:
                rows.append('<tr>' + first + f'<td class="n">{n1(v["gen"], 1)}</td><td class="n"><b>{n1(v["gen"], 1)}</b></td>'
                            f'<td class="n">{round(v["yield"])}</td><td class="n">{pct0(v["pct"])}</td>'
                            f'<td>{pill("warn", v["alert"]) if v["alert"] else ""}</td></tr>')
    return '<table class="dt" style="min-width:820px"><thead>' + head + '</thead><tbody>' + ''.join(rows) + '</tbody></table>'


def table_export(O, H):
    d0, d1 = O['D0'], O['D1']
    A, B = O['A'], O['B']
    head = (f'<tr><th>Sistema</th><th class="n">{wd3(d0)} {d_short(d0)}<br>07:00–24:00<br>kWh</th>'
            f'<th class="n">{wd3(d1)} {d_short(d1)}<br>00:00–07:00<br>kWh</th>'
            f'<th class="n">Exportada<br>{d_short(A)} 07:00 →<br>{d_short(B)} 07:00<br>kWh</th>'
            f'<th class="n">Importada<br>{d_short(A)} 07:00 →<br>{d_short(B)} 07:00<br>kWh</th>'
            f'<th class="n">Consumo lado respaldado<br>{d_short(A)} 07:00 →<br>{d_short(B)} 07:00<br>kWh</th>'
            f'<th class="n">Exportada / generada<br>(ventana ÷ generación<br>{wd3(d0)} {d_short(d0)}<br>00:00–24:00)</th>'
            f'<th class="n">Consumo del cliente<br>{wd3(d0)} {d_short(d0)}<br>00:00–24:00<br>kWh</th>'
            f'<th class="n">Cobertura solar<br>{wd3(d0)} {d_short(d0)}<br>00:00–24:00</th></tr>')
    rows = []
    for c in CITY_ORDER:
        rows.append(f'<tr class="ciudad"><td colspan="9">{c}</td></tr>')
        hs = sorted(O['by_city'][c], key=lambda h: (H[h]['win']['exp'] is None, -(H[h]['win']['exp'] or 0), nat_key(h)))
        for h in hs:
            v = H[h]; w = v['win']
            if w['exp'] is None or v['gen'] is None:
                a = n1(w['exp_a'], 2) if w['exp_a'] is not None else '—'
                rows.append(f'<tr><td><b>{esc(h)}</b></td><td class="n">{a}</td><td class="n">—</td><td class="n"><b>—</b></td><td class="n">—</td><td class="n">—</td>'
                            '<td class="n">—</td><td class="n">—</td><td class="n"><b>—</b></td></tr>')
                continue
            rows.append(f'<tr><td><b>{esc(h)}</b></td><td class="n">{n1(w["exp_a"], 2)}</td><td class="n">{n1(w["exp_b"], 2)}</td>'
                        f'<td class="n"><b>{n1(w["exp"], 2)}</b></td><td class="n">{n1(w["imp"], 1)}</td><td class="n">{n1(w["cons_resp"], 1)}</td>'
                        f'<td class="n">{pct1(w["exp"] / v["gen"] * 100) if v["gen"] else "—"}</td><td class="n">{n1(v["cons"], 1)}</td>'
                        f'<td class="n"><b>{pct0(v["gen"] / v["cons"] * 100) if v["cons"] else "—"}</b></td></tr>')
    return '<table class="dt" style="min-width:900px"><thead>' + head + '</thead><tbody>' + ''.join(rows) + '</tbody></table>'


def table_comm(O, H):
    now = O['now']
    rows = []
    for r in O['comm_rows']:
        t = r['t']
        rows.append(f'<tr><td><b>{esc(r["house"])}</b><small>{r["city"]}</small></td><td>{r["dev"]}</td>'
                    f'<td>{dh(t) if t else "sin dato"}</td><td class="n">{fhace(now - t) if t else "—"}</td></tr>')
    head = '<tr><th>Sistema</th><th>Dispositivo</th><th>Último dato / offline desde</th><th class="n">Hace</th></tr>'
    return '<table class="dt" style="min-width:640px"><thead>' + head + '</thead><tbody>' + ''.join(rows) + '</tbody></table>'


# ---------------------------------------------------------------- documento
def render(R, elapsed=None, generated=None):
    H = R['houses']
    O = aggregate(R)
    O['_H'] = H
    A, B, now = O['A'], O['B'], O['now']
    d0, d1 = O['D0'], O['D1']
    ncities = len(CITY_ORDER); nsys = len(H)
    n_hc = len(O['houses_cut']); n_cuts = O['n_cuts']; n_ev = len(O['events'])
    down = sum(O['sin_red_ahora'].values())

    # ---- KPIs
    k1cls = ' k-warn' if n_hc else ''
    bp = O['backup_pct']
    k2cls = '' if bp is None else (' k-ok' if bp >= 99 else (' k-warn' if bp < 90 else ''))
    gen_line = (f'(patrón {round(O["patron"])} kWh)' if O['patron'] else '')
    kpis = [
        f'<div class="kpi{k1cls}"><div class="v">{n_hc} <small>de {nsys}</small></div><div class="l">sistemas con cortes de red en la ventana '
        f'({n_cuts} {plural(n_cuts, "corte", "cortes")} en {n_ev} {plural(n_ev, "evento", "eventos")}).</div></div>',
        (f'<div class="kpi{k2cls}"><div class="v">{n1(bp, 1)} %</div><div class="l">del tiempo de corte con tensión en la casa (respaldo).</div></div>'
         if bp is not None else '<div class="kpi k-ok"><div class="v">—</div><div class="l">sin cortes de red en la ventana: no hay tiempo de respaldo que medir.</div></div>'),
        f'<div class="kpi"><div class="v">{round(O["gen"])} <small>kWh</small></div><div class="l">de generación FV del portafolio Sunny en 1 día {gen_line}.</div></div>',
        f'<div class="kpi"><div class="v">{round(O["yield"])} <small>kWh/kWp·año</small></div><div class="l">de yield proyectado a un año: generación diaria real de {O["n_valid"]} sistemas dividida entre su potencia pico instalada en DC (suma de kWp), por 365.</div></div>',
        f'<div class="kpi"><div class="v">{round(O["cov"])} <small>%</small></div><div class="l">de cobertura solar del portafolio Sunny: generación FV dividida entre el consumo de los clientes. La generación es el balance de medidores y el consumo es la demanda del medidor solar.</div></div>',
        f'<div class="kpi"><div class="v">{round(O["exp_total"])} <small>kWh</small></div><div class="l">de energía activa exportada a la red entre el {dh(A)} y el {dh(B)}; importada {round(O["imp_total"])} kWh en el mismo periodo.</div></div>',
    ]

    # ---- header
    status = ('<div class="status ok"><i></i>Sin cortes de red en curso</div>' if down == 0 else
              f'<div class="status"><i></i>{down} {plural(down, "sistema", "sistemas")} sin red ahora</div>')
    gen_ts = generated or int(time.time() * 1000)
    meta = (f'<span>{wdf(A)} {d_short(A)} 07:00 a {wdf(B)} {d_short(B)} 07:00 (UTC−5)</span><span>24 h de operación</span>'
            f'<span>Fuente: telemetría cruda de Metrum</span><span>Generado {dh(gen_ts)}</span>')
    header = ('<header>\n'
              f'  <img class="logo" src="{LOGO}" alt="Sunny, powered by Promigas" width="235" height="84">\n'
              f'  <div class="kick">24 horas · {ncities} ciudades · {nsys} sistemas</div>\n'
              f'  <h1>Operación diaria {d_short(A)} y {d_short(B)}</h1>\n  {status}\n  <div class="meta">{meta}</div>\n</header>')

    # ---- vista rápida
    parts = ['<h3>Semáforo del respaldo (último corte de cada casa)</h3>' + semaforo(O), '<h3>Por ciudad</h3>' + city_cards(O, H)]
    if n_cuts:
        parts.append('<h3>Cortes de red en la ventana, por casa</h3><div class="scroll">\n' + svg_cortes(O, H) + '\n</div>'
                     '<div class="legend"><span>' + BAT_ICON + 'SOC: carga de la batería al inicio del corte, no es el respaldo (cortes de 5 min o más; * = último dato registrado)</span>'
                     '<span><i class="lg g"></i>✓ Tiempo respaldado (la casa tuvo tensión)</span><span><i class="lg c"></i>✕ Tiempo que vio el cliente (sin tensión)</span>'
                     '<span>la barra completa es el tiempo total sin red</span></div>'
                     '<p class="note">Cada barra es un corte: su largo es el tiempo total sin red, en verde lo que la casa estuvo respaldada y en rojo los tramos en que el cliente vio la interrupción (huecos de tensión del medidor solar). Pasa el cursor para ver la duración, el tiempo que vio la casa, su % de respaldo y el veredicto. Los cortes y huecos de segundos se dibujan con un ancho mínimo para que se vean.</p>')
        parts.append('<h3>Respaldo de cada casa en los eventos de red</h3><div class="scroll">\n' + svg_heatmap(O, H) + '\n</div>'
                     '<div class="legend"><span><i class="lg g"></i>✓ 99 % o más</span><span><i class="lg w"></i>▲ 90 a 99 %</span><span><i class="lg c"></i>✕ menos de 90 %</span>'
                     '<span><i class="lg vacia"></i>la casa no tuvo ese corte</span><span>cada celda es el % de respaldo del corte; incluye todos los eventos de red de la ventana</span></div>')
        parts.append('<h3>Cuánto vio la casa en cada corte</h3><div class="scroll">\n' + svg_hueco(O, H) + '\n</div>'
                     f'<p class="note">Cada corte cuenta una vez ({n_cuts} en total); pasa el cursor sobre una barra para ver qué casas son. «Tiempo que vio la casa» = suma de los huecos de tensión del medidor solar en ese corte.</p>')
        svg5, n5, nlow5 = svg_bateria_corte(O, H)
        parts.append('<h3>Batería durante el corte más largo de cada casa</h3><div class="scroll">\n' + svg5 + '\n</div>'
                     '<div class="legend"><span><i class="dotl hueco"></i>SOC al inicio del corte</span><span><i class="dotl ok"></i>SOC al final</span>'
                     f'<span><i class="lg marca"></i>mínimo durante el corte</span><span><i class="lg c"></i>llegó a la reserva ({nlow5} {plural(nlow5, "casa", "casas")})</span><span>línea punteada: reserva 20 %</span></div>'
                     f'<p class="note">Se dibuja el corte más largo de cada casa entre los de 5 min o más ({n5} casas), ordenadas de menor a mayor carga al inicio. Pasa el cursor sobre una fila para ver el detalle.</p>')
    else:
        parts.append('<p class="note">No hubo cortes de red en la ventana.</p>')
    parts.append(f'<h3>Baterías por debajo de 50 % al corte del reporte, {dh(B)} ({len(O["reserva"])} en reserva)</h3>' + soc_grid(O) +
                 '<div class="legend"><span><i class="lg c"></i>en reserva (≤ 20 %)</span><span><i class="lg w"></i>entre 20 y 50 %</span><span>la marca vertical es la reserva</span>'
                 f'<span>{O["sobre50"]} {plural(O["sobre50"], "sistema por encima de 50 % no se dibuja", "sistemas por encima de 50 % no se dibujan")}</span></div>')
    parts.append('<h3>Generación frente a consumo de los clientes</h3>\n<div class="scroll">\n' + svg_gen_cons(O) + '\n</div>'
                 '<div class="legend"><span><i class="lg gen"></i>Generación FV (balance de medidores)</span><span><i class="lg con"></i>Consumo de los clientes</span><span>cobertura = generación ÷ consumo</span></div>')
    n_zero = sum(1 for h in O['rank_exp'] if round(H[h]['win']['exp'], 3) <= 0)
    parts.append('<h3>Ranking de las casas por energía exportada</h3><div class="scroll">\n' + svg_ranking_export(O, H) + '\n</div>'
                 f'<div class="legend"><span><i class="lg gen"></i>energía activa exportada a la red en la ventana (kWh)</span><span>{n_zero} {plural(n_zero, "casa", "casas")} con 0 kWh exportados</span>'
                 '<span>pasa el cursor para ver importada, generación y % exportado de cada casa</span></div>')
    svg8, n_low = svg_yield(O, H)
    parts.append('<h3>Yield frente al patrón de su región</h3>\n<div class="scroll">\n' + svg8 + '\n</div>'
                 f'<div class="legend"><span><i class="dotl ok"></i>≥ 90 % del patrón</span><span><i class="dotl w"></i>▲ por debajo de 90 % ({n_low} sistemas)</span>'
                 '<span>línea continua: 100 % del patrón de su región · punteada: 90 %</span></div>')
    nnf = len(O['no_full'])
    parts.append('<h3>Hora en que la batería llegó a carga completa</h3><div class="scroll">\n' + svg_full(O, H) + '\n</div>'
                 '<div class="legend"><span><i class="dotl w"></i>▲ antes de las 12:00 (pierde producción)</span><span><i class="dotl t"></i>entre las 12:00 y las 16:00</span>'
                 f'<span><i class="dotl ok"></i>después de las 16:00</span><span>línea punteada: las 12:00 · {nnf} {plural(nnf, "sistema no llegó", "sistemas no llegaron")} a 99 %</span></div>')
    vista = ('<section>\n  <h2>Vista rápida</h2>\n  <div class="card" style="display:flex;flex-direction:column;gap:18px">\n    '
             + '\n    '.join(parts) + '\n  </div>\n</section>')

    # ---- puntos relevantes
    pts = []
    if n_cuts:
        prim = [e for e in O['events'] if e['n'] >= 2 or e['typ'] >= 60]
        micro = [e for e in O['events'] if e not in prim]
        t = f'{n_hc} de {nsys} sistemas tuvieron cortes de red: {n_cuts} {plural(n_cuts, "corte", "cortes")} en {n_ev} {plural(n_ev, "evento", "eventos")}.'
        if prim:
            t += ' Principales: ' + '; '.join(f'{e["city"]} {dh(e["start"])} ({e["n"]} de {e["n_city"]} sistemas, {fdur(e["typ"])})' for e in prim) + '.'
        if micro:
            ms = len({h for e in micro for h in e['houses']})
            t += f' Además, {len(micro)} {plural(len(micro), "microcorte", "microcortes")} de menos de 1 min en {ms} {plural(ms, "sistema", "sistemas")}.'
        pts.append(('warn', 'Interrupciones', t))
    else:
        pts.append(('okp', 'Interrupciones', f'Ningún sistema tuvo cortes de red en la ventana (0 de {nsys}).'))
    if O['unlinked']:
        ug = O['unlinked']; uh = sorted({h for h, g in ug}, key=nat_key)
        big = max(ug, key=lambda x: x[1][1] - x[1][0])
        pts.append(('warn', 'Respaldo', f'{len(ug)} {plural(len(ug), "hueco", "huecos")} de tensión de 10 s o más en {len(uh)} {plural(len(uh), "casa", "casas")} sin un corte de red asociado en los medidores de red (el mayor, {fdur((big[1][1] - big[1][0]) / 1000)}).'))
    if O['reserva']:
        items = []
        for r in sorted(O['reserva'], key=lambda r: nat_key(r['house'])):
            lab = f'{round(r["soc"])} %' + (f', {hm(r["t"])}' if r['age'] > 30 * 60_000 else '')
            items.append(f'{r["house"]} ({lab})')
        pts.append(('warn', 'Baterías en reserva', f'Con batería en reserva al corte del reporte, {hm(B)} (SOC de 20 % o menos): ' + join_es(items) + '.'))
    low = sorted([(v['pct'], h) for h, v in H.items() if v['alert']])
    gv = O['gen_vs_patron']
    txt = f'Generación FV del portafolio Sunny: {round(O["gen"])} kWh en 1 día'
    if gv is not None: txt += f' ({"+" if gv >= 0 else "−"}{abs(round(gv))} % frente a la mediana de los días previos)'
    txt += f'. Yield proyectado a un año: {round(O["yield"])} kWh/kWp·año; cobertura solar: {round(O["cov"])} %.'
    if low:
        items = [f'{h} ({H[h]["alert"]})' for _, h in low]
        txt += f' {len(low)} sistemas con producción baja: ' + join_es(items[:8]) + ('…' if len(items) > 8 else '') + '.'
    pts.append(('warn' if low else 'okp', 'Rendimiento', txt))
    if O['comm_rows']:
        ih = sorted(O['inv_stale_houses'], key=lambda h: (CITY_ORDER.index(H[h]['city']), nat_key(h)))
        pts.append(('warn', 'Comunicación', f'{len(ih)} {plural(len(ih), "sistema sin datos del inversor", "sistemas sin datos del inversor")} en las últimas 2 h ({join_es(ih)}); {len(O["comm_rows"])} dispositivos con último dato de más de 2 h.'))
    if n_cuts:
        pts.append(('okp', 'Respaldo', f'La casa mantuvo tensión en {n1(bp, 1)} % del tiempo de corte; {O["cuts_no_gap"]} de {n_cuts} cortes no dejaron ningún hueco.'))
    lead = [h for h in O['rank_exp'] if H[h]['win']['exp'] >= 0.05][:3]
    ex = f'Energía activa exportada a la red: {n1(O["exp_total"], 1)} kWh en la ventana'
    if lead: ex += ' (' + '; '.join(f'{h} {n1(H[h]["win"]["exp"], 1)} kWh' for h in lead) + ' lideran)'
    ex += f'. {O["n_no_export"]} sistemas no exportaron.'
    pts.append(('okp', 'Exportación', ex))
    puntos = (f'<section>\n  <details><summary>Puntos más relevantes ({len(pts)})</summary><div style="margin-top:10px"><ul class="pts">'
              + ''.join(f'<li><span class="pill {c}">{esc(l)}</span><span>{esc(t)}</span></li>' for c, l, t in pts) + '</ul></div></details>\n</section>')

    por_ciudad = f'<section>\n  <details><summary>Por ciudad</summary><div style="margin-top:10px"><div class="scroll">\n{table_ciudad(O)}\n</div></div></details>\n</section>'

    # ---- interrupciones y respaldo
    if n_cuts:
        intr = ('<section>\n  <h2>Interrupciones y respaldo</h2>\n  <div class="card" style="display:flex;flex-direction:column;gap:14px">\n'
                f'    <details><summary>Eventos de red</summary><div style="margin-top:10px"><div class="scroll">\n{table_eventos(O)}\n</div></div></details>\n'
                f'    <details><summary>Por sistema</summary><div style="margin-top:10px"><div class="scroll">\n{table_sistema(O, H)}\n</div></div></details>\n    \n'
                f'    <details><summary>Detalle por corte ({n_cuts} {plural(n_cuts, "fila", "filas")})</summary><div style="margin-top:10px"><div class="scroll">\n{table_detalle(O, H)}\n</div></div></details>\n'
                '    <p class="note">Corte = intervalo entre los eventos <code>po</code> y <code>pr</code> del medidor de red. «Tiempo que vio la casa» = suma de los huecos de tensión del medidor solar (lado respaldado) asociados al corte, incluidos los del cambio al caer y al volver la red. «Respaldo» = (tiempo sin red del medidor de red − tiempo sin tensión del medidor solar) ÷ tiempo sin red del medidor de red; se calcula en todos los cortes, incluidos los de pocos segundos, y no baja de 0 %. Sin hueco, por criterio del equipo, el cliente no percibió el corte. En «Por sistema» se muestra completo el último corte registrado de cada casa, con su veredicto de respaldo; los anteriores (del más reciente al más antiguo) van solo con su % de respaldo y la hora de inicio, y la duración sale al pasar el cursor. El detalle de todos los cortes está en el desplegable. Veredicto: «Respaldo total» sin hueco; «con transferencia» si el hueco suma hasta 40 s (el desfase máximo entre relojes de medidores); «Retardo de transferencia» si es mayor y hubo respaldo; «Caída durante el respaldo» con un hueco de 10 s o más en mitad del corte; «Sin respaldo» si la casa vio todo el corte (respaldo 0 %).</p>\n'
                '  </div>\n</section>')
    else:
        intr = ''

    rend = (f'<section>\n  <details><summary>Rendimiento de los sistemas</summary><div style="margin-top:10px">\n    <div class="scroll">\n{table_rendimiento(O, H)}\n</div>\n'
            '    <p class="note" style="margin-top:10px">Generación = balance de medidores con los cierres diarios: demanda del medidor solar (<code>CenergyAI</code>) − importada + exportada del medidor de red. No se usa el contador del inversor. «Yield anual proyectado» es la generación real del día dividida entre la potencia instalada, por 365; en el portafolio Sunny y en cada ciudad, la suma de generación entre la suma de potencia. La potencia instalada es la potencia pico en DC (kWp) del archivo de sistemas, no la del inversor, y no se corrige estacionalidad ni clima. «Frente al yield patrón» es el yield anual proyectado del sistema dividido entre el yield patrón de su región, definido por el equipo: 1188 kWh/kWp·año en Cali y 1323 kWh/kWp·año en la costa (Turbaco, Barranquilla y Cartagena). La alerta «baja vs patrón» aparece por debajo del 90 % del patrón y se completa con «bajo consumo» cuando el consumo del cliente en el día evaluado (demanda del medidor solar) fue menor al 75 % del habitual de esa casa, medido como la mediana de sus 10 días previos; en ese caso la baja generación puede deberse a que la casa consumió menos. Se añade «producción limitada» cuando la batería llegó a 99 % antes de las 12:00, y «producción limitada en la tarde» cuando llegó entre las 12:00 y las 16:00, porque entonces solo se limita parte de la tarde (se indica la hora): en sistemas sin exportación, con la batería llena el inversor limita la producción FV al consumo de la casa, así que el yield mide la energía solar consumida y no la que el sistema podría producir.</p>\n'
            '  </div></details>\n</section>')
    expo = (f'<section>\n  <details><summary>Exportación de energía activa</summary><div style="margin-top:10px">\n    <div class="scroll">\n{table_export(O, H)}\n</div>\n'
            '    <p class="note" style="margin-top:10px">Exportada e importada, del medidor de red (<code>energyAE</code> y <code>energyAI</code>, contadores acumulados: diferencia entre el inicio y el fin de cada periodo). Consumo del cliente = demanda del día calendario en el medidor solar; cobertura solar = generación / consumo del cliente. La generación es el balance de medidores, así que incluye pérdidas y la energía que pasa por la batería. Cada encabezado indica el periodo de su dato: las columnas por día suman la ventana completa (exportada, importada y consumo del lado respaldado, que se miden entre la hora de inicio y la de corte del reporte), mientras que consumo del cliente, generación y cobertura son de días completos, de 00:00 a 24:00, porque dependen de los cierres diarios de los medidores.</p>\n'
            '  </div></details>\n</section>')
    comm = (f'<section>\n  <details><summary>Comunicación y equipos</summary><div style="margin-top:10px"><div class="scroll">\n{table_comm(O, H)}\n</div></div></details>\n</section>'
            if O['comm_rows'] else '')

    nc = O['no_closing']
    lim6 = ('Si a un medidor aún no le llegó el cierre diario de las 00:00 (' + join_es(nc) + '), su generación del día queda sin calcular y no se reemplaza por otro dato. '
            if nc else '') + 'La generación de todos los sistemas se calcula con el balance de medidores.'
    limites = ('<section>\n  <h2>Límites del análisis</h2>\n  <div class="limits">\n'
               '    <p>Los medidores de red sin tensión envían sus eventos guardados solo cuando vuelve la red. Un corte en curso al cierre de la ventana se cuenta en «Sin red ahora» (entrada de red del inversor por debajo de 5 V, o evento <code>po</code> sin <code>pr</code>), pero no se dibuja como corte hasta que vuelva la red.</p>\n'
               '    <p>Los relojes de los medidores difieren hasta unos 40 s entre sí. Cada hueco cuenta en un solo corte: el que empieza hasta 75 s de su inicio, si no el que lo contiene, si no el último que terminó hasta 10 min antes.</p>\n'
               '    <p>Los inversores se muestrean cada 15 min. El SOC de inicio y fin de cada corte es el de la muestra más cercana y la reserva se toma como 20 % para todos.</p>\n'
               '    <p>La ventana es siempre de 24 h (de 07:00 a 07:00); los lunes no se extiende hasta el viernes.</p>\n'
               '    <p>Cada sistema es una casa (medidor de red, medidor solar, inversor y gateway). Si una casa tiene dos inversores se usa el que reportó más recientemente.</p>\n'
               f'    <p>{lim6}</p>\n'
               f'    <p>El reporte se calculó el {dh(gen_ts)} sobre la ventana ya cerrada; los equipos que estuvieron sin conexión pueden haber sincronizado después datos atrasados, que sí se incluyen. El estado de comunicación y las baterías se evalúan al cierre de la ventana ({dh(B)}).</p>\n'
               '  </div>\n</section>')
    foot = f'<footer>Cálculo propio sobre telemetría cruda de Metrum.{(" Datos consultados en " + str(round(elapsed)) + " s.") if elapsed else ""}</footer>'

    body = '\n\n'.join(x for x in (
        '<div class="wrap">\n' + header, '<div class="kpis">\n  ' + '\n  '.join(kpis) + '\n</div>', vista, puntos, por_ciudad, intr, rend, expo, comm, limites, foot) if x)
    title = f'Operación diaria {d_short(B)}'
    return (f'<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{title}</title>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">\n'
            f'<style>body{{margin:0}}img{{max-width:100%}}[hidden]:not([hidden=until-found i]){{display:none!important}}</style><style>{CSS}</style></head>\n<body>\n{body}\n{TAIL}\n</div>\n</body></html>\n'), O
