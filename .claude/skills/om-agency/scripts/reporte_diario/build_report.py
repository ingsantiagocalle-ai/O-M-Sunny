#!/usr/bin/env python3
"""Reporte operativo diario de la flota Sunny (tablero HTML oscuro), recalculado desde telemetría cruda de Metrum.

Credenciales únicamente desde el entorno (nunca se imprimen ni se escriben):
  METRUM_API_URL, METRUM_USERNAME, METRUM_PASSWORD
Solo lectura: no escribe nada en Metrum.

Uso:
  python3 build_report.py 2026-10-18                      # ventana 17 oct 07:00 -> 18 oct 07:00 (UTC-5)
  python3 build_report.py 2026-10-18 --out reportes/operacion-diaria-2026-10-18.html
  python3 build_report.py 2026-10-16 --now 2026-10-16T06:59:34   # como se habría visto a esa hora (energía hasta la última muestra)

La fecha es el día que CIERRA la ventana de 24 h (de ayer 07:00 a ese día 07:00, hora de Colombia). Sin --now, el
reporte se calcula al cierre de la ventana (o ahora, si la ventana aún no cierra).
OM_REPORT_CACHE=<dir> activa una caché de series en disco (solo para desarrollo).
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compute  # noqa: E402
import render  # noqa: E402
from data import fmt_local, local_ms  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('fecha', help='día que cierra la ventana, YYYY-MM-DD (hora de Colombia)')
    ap.add_argument('--out', help='archivo HTML de salida (por defecto operacion-diaria-<fecha>.html)')
    ap.add_argument('--now', help='instante del reporte en hora local, YYYY-MM-DDTHH:MM[:SS]')
    args = ap.parse_args()

    close = dt.date.fromisoformat(args.fecha)
    start = close - dt.timedelta(days=1)
    A = local_ms(start.year, start.month, start.day, 7)
    B = A + compute.DAY
    real_now = int(time.time() * 1000)
    if args.now:
        n = dt.datetime.fromisoformat(args.now)
        now = local_ms(n.year, n.month, n.day, n.hour, n.minute, n.second)
    else:
        now = min(real_now, B)

    t0 = time.time()
    R = compute.build(A, now=now)
    elapsed = time.time() - t0
    doc, O = render.render(R, elapsed=elapsed, generated=real_now)

    out = args.out or f'operacion-diaria-{args.fecha}.html'
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(doc)

    print(f'Ventana {fmt_local(A, "%d %b %H:%M")} -> {fmt_local(B, "%d %b %H:%M")} (UTC-5), calculada en {elapsed:.0f} s')
    print(f'  cortes: {O["n_cuts"]} en {len(O["houses_cut"])} casas, {len(O["events"])} eventos')
    print(f'  generación {O["gen"]:.0f} kWh ({O["n_valid"]} sistemas con cierre), yield {O["yield"]:.0f} kWh/kWp·año, cobertura {O["cov"]:.0f} %')
    print(f'  sin cierre diario: {", ".join(O["no_closing"]) or "ninguno"}')
    print(f'Escrito {out} ({len(doc) // 1024} KB)')


if __name__ == '__main__':
    main()
