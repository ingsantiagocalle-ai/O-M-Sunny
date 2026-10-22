#!/usr/bin/env python3
"""Reporte mensual de curtailment (solar + BESS con zero export) para una zona de Metrum.

Curtailment = energía solar potencial - energía solar entregada, medida solo cuando la batería está
llena (SOC >= 99 %) y el zero export obliga a la PV a igualar el consumo de la casa.

Uso:
  python3 reportes/curtailment/curtailment.py --zona "RESERVAS DE PANCE" --mes 2026-09

Opciones:
  --out DIR           carpeta del HTML final (por defecto: <repo>/reportes)
  --cache DIR         telemetría descargada (por defecto: <repo>/.curtailment-cache; no se versiona)
  --refresh           vuelve a descargar aunque exista la caché
  --deye-offset W     fija el residuo diurno de las Deye en W en vez de calibrarlo con el mes
  --sin-deye          omite la validación contra la nube de Deye
  --titulo TXT        nombre de la zona para el título (por defecto se deriva de --zona)

Credenciales solo desde variables de entorno (nunca se imprimen ni se escriben):
  METRUM_API_URL, METRUM_USERNAME, METRUM_PASSWORD   (telemetría)
  DEYE_*                                              (validación opcional, solo lectura)

Salidas: <out>/curtailment-<zona>-<AAAA-MM>.html (autocontenido) y, en la caché, el mismo HTML sin
envoltorio (`.fragmento.html`) para publicarlo como artefacto.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html as htmllib
import json
import os
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

TZ = "America/Bogota"          # UTC-5 sin horario de verano
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# Parámetros del método. Cambiarlos cambia el resultado: no tocar sin dejarlo documentado.
P = dict(
    SOC_FULL=99,              # SOC (%) desde el que se considera batería llena
    SENSOR_SOC_MAX=95,        # sensor de sol: batería con espacio
    SENSOR_CHG_MIN_W=150,     # sensor de sol: carga mínima de la batería
    AT_LIMIT_FRAC=0.92,       # sensor de sol: se descarta si la corriente de carga está en su tope
    DEFICIT_W=100,            # consumo > PV: descarga de batería o importación >= este valor
    NO_DISCHARGE_W=-100,      # "sin descarga": flujo de batería >= este valor (W, + = carga)
    IMPORT_MAX_W=100,         # saturado exige importación de red por debajo de este valor
    FLAG_RATIO=0.85,          # curtailment si PV entregada < 85 % del potencial
    POT_MIN_W=300,            # potencial mínimo para contar un intervalo
    CAP_FACTOR=1.3,           # tope del potencial: 1,3 x potencia nominal del inversor
    SAT_FROM=6.5, SAT_TO=17.5,  # ventana horaria del estado saturado
    PV_FROM=6.0, PV_TO=18.0,    # ventana solar de la PV derivada
    MIN_PEERS=3, ALS_ITERS=30,
    POT_LOW=0.88, POT_HIGH=1.12,  # rango por la incertidumbre del potencial (error mediano 12 %)
    DEYE_OFFSET_DEFAULT=255.0,    # W, si no se puede calibrar
    DT_H=0.25,
)
KEYS_COMMON = ("BattSOC,BattPower,BattCur,BattVolt,powerAEg,powerAPg,powerAE,energyPD,energyLD,energyID,"
               "energyED,energyIT,energyET,invrun,invstate,voltGridA,voltGridB,voltGridC,frequency")
KEYS_DEYE = ",LoadPower_DY,ExportGrid_DY"
KEYS_LIVO = ",LoadPower_LV,ExportGrid_LV,powerAEgdc_LV,BattStateOp_LV"
TEXT_KEYS = ("invrun", "invstate", "BattStateOp_LV", "activityState")
ATTRS = ["zone", "spcus", "gateway", "mettype", "invbrand", "invmodel", "invcap", "invarray", "invtype", "BattSn"]
WARN: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    WARN.append(msg)
    print("ADVERTENCIA: " + msg, flush=True)


# ----------------------------------------------------------------------------- Metrum
class Metrum:
    def __init__(self) -> None:
        for k in ("METRUM_API_URL", "METRUM_USERNAME", "METRUM_PASSWORD"):
            if not os.environ.get(k):
                sys.exit(f"Falta la variable de entorno {k}.")
        self.base = os.environ["METRUM_API_URL"].rstrip("/")
        self._tok: dict = {}

    def _hdr(self) -> dict:
        if not self._tok or time.time() > self._tok["exp"]:
            r = requests.post(self.base + "/api/auth/login", timeout=30,
                              json={"username": os.environ["METRUM_USERNAME"], "password": os.environ["METRUM_PASSWORD"]})
            r.raise_for_status()
            self._tok = {"t": r.json()["token"], "exp": time.time() + 100 * 60}
        return {"Authorization": "Bearer " + self._tok["t"]}

    def _call(self, method: str, path: str, **kw):
        for i in range(5):
            r = requests.request(method, self.base + path, headers=self._hdr(), timeout=90, **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(2 ** i)
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()

    def get(self, path: str, **params):
        return self._call("GET", path, params=params)

    def post(self, path: str, body: dict):
        return self._call("POST", path, json=body)


def inventory(mt: Metrum) -> list[dict]:
    body = {"entityFilter": {"type": "entityType", "entityType": "DEVICE"},
            "pageLink": {"pageSize": 100, "page": 0},
            "entityFields": [{"type": "ENTITY_FIELD", "key": k} for k in ("name", "type", "createdTime")],
            "latestValues": [{"type": "ATTRIBUTE", "key": k} for k in ATTRS]}
    rows, page = [], 0
    while True:                                   # nunca asumir una sola página: iterar hasta hasNext=false
        body["pageLink"]["page"] = page
        j = mt.post("/api/entitiesQuery/find", body)
        rows += j["data"]
        if not j.get("hasNext"):
            break
        page += 1
    out = []
    for r in rows:
        f, a = r["latest"].get("ENTITY_FIELD", {}), r["latest"].get("ATTRIBUTE", {})
        g = lambda d, k: (d.get(k) or {}).get("value")
        out.append(dict(id=r["entityId"]["id"], name=g(f, "name"), type=g(f, "type"), **{k: g(a, k) for k in ATTRS}))
    return out


def download(mt: Metrum, devs: list[dict], first: dt.date, nxt: dt.date, cache: Path, refresh: bool) -> None:
    ms = lambda d, h: int(dt.datetime(d.year, d.month, d.day, h, tzinfo=dt.timezone.utc).timestamp() * 1000)
    start, end = ms(first, 5), ms(nxt, 6)          # 00:00 Bogotá = 05:00 UTC; endTs exclusivo -> +1 h de margen
    keys = KEYS_COMMON + KEYS_DEYE + KEYS_LIVO     # Metrum solo devuelve las que existen

    def job(d: dict):
        out = cache / "raw" / f"{d['name']}.json"
        if out.exists() and not refresh:
            return
        res: dict = {}
        t = start
        while t < end:
            t2 = min(t + 10 * 86400 * 1000, end)
            r = mt.get(f"/api/plugins/telemetry/DEVICE/{d['id']}/values/timeseries", keys=keys,
                       startTs=t, endTs=t2, agg="NONE", limit=50000)
            for k, pts in r.items():
                res.setdefault(k, []).extend(pts)
            t = t2
        out.write_text(json.dumps({"meta": d, "ts": res}), encoding="utf-8")

    (cache / "raw").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(job, devs))


def load_inverters(cache: Path, first: dt.date, nxt: dt.date, zona_devs: list[dict]):
    """Devuelve ({casa: (meta, df)}, [excluidos]). Los dispositivos sin datos en el mes se excluyen."""
    per_casa: dict[str, list] = {}
    excluded = []
    for d in zona_devs:
        j = json.loads((cache / "raw" / f"{d['name']}.json").read_text(encoding="utf-8"))
        cols = {}
        for k, pts in j["ts"].items():
            if not pts:
                continue
            s = pd.Series({int(p["ts"]): p["value"] for p in pts})
            cols[k] = s.astype(str) if k in TEXT_KEYS else pd.to_numeric(s, errors="coerce")
        df = None
        if cols:
            df = pd.DataFrame(cols).sort_index()          # las series pueden venir en orden descendente
            df.index = pd.to_datetime(df.index, unit="ms", utc=True).tz_convert(TZ)
            df = df[(df.index >= first.isoformat()) & (df.index < nxt.isoformat())]
            df = df[~df.index.duplicated()]
        if df is None or df.empty:
            excluded.append(dict(casa=d["spcus"], marca=(d["invbrand"] or "de marca no registrada").title() if d["invbrand"] else "de marca no registrada", motivo="sin datos en el mes"))
            continue
        per_casa.setdefault(d["spcus"], []).append((d, df))
    inv = {}
    for casa, cands in per_casa.items():
        if len(cands) > 1:                                # equipo viejo + actual: quedarse con el que se mueve
            cands.sort(key=lambda x: -float(x[1]["BattSOC"].std()) if "BattSOC" in x[1] else 0)   # el que se mueve de verdad
            for d, _ in cands[1:]:
                excluded.append(dict(casa=casa, marca=d["invbrand"].title() if d["invbrand"] else "de marca no registrada", motivo="duplicado de la misma casa"))
        meta, df = cands[0]
        brand = (meta.get("invbrand") or "").upper()
        inferred = "LIVOLTEK" if ("powerAEgdc_LV" in df or "LoadPower_LV" in df) else "DEYE" if "LoadPower_DY" in df else ""
        if brand not in ("DEYE", "LIVOLTEK"):
            brand = inferred
        if brand not in ("DEYE", "LIVOLTEK") or (inferred and brand != inferred):
            sys.exit(f"{casa}: marca/modelo no soportado o inconsistente (atributo={meta.get('invbrand')!r}, "
                     f"keys={inferred or 'ninguna reconocida'}). Hay que verificar keys y signos de batería antes de seguir.")
        meta = dict(meta, brand=brand)
        inv[casa] = (meta, df)
    return dict(sorted(inv.items(), key=lambda kv: kv[1][0]["name"])), excluded


# ----------------------------------------------------------------------------- PV derivada
def pv_actual(meta: dict, df: pd.DataFrame, deye_offset: float) -> pd.DataFrame:
    """PV entregada (W) por balance de potencias cada 15 min. Metrum no expone potencia PV."""
    o = pd.DataFrame(index=df.index)
    hr = df.index.hour + df.index.minute / 60
    day = (hr >= P["PV_FROM"]) & (hr <= P["PV_TO"])
    load = df["powerAEg"]
    if meta["brand"] == "DEYE":            # BattPower: + = descarga
        batt_chg = -df["BattPower"]
        grid_imp = df["LoadPower_DY"].clip(lower=0)
        pv = (load + batt_chg - grid_imp + np.where(day, deye_offset, 0.0)).clip(lower=0)
    else:                                  # Livoltek, BattPower: + = carga; powerAEgdc_LV = batería + carga
        batt_chg = df["BattPower"]
        grid_imp = pd.Series(np.nan, index=df.index)
        pv = df["powerAEgdc_LV"].clip(lower=0)
    o["pv"] = pv.where(day, 0.0)
    o["load"], o["batt_chg"], o["grid_imp"] = load, batt_chg, grid_imp
    o["soc"], o["battcur"] = df["BattSOC"], df["BattCur"].abs()
    return o


def counter_ratio(df: pd.DataFrame, pv: pd.Series):
    """Razón mediana diaria entre la integral de PV y el delta del contador diario energyPD."""
    if "energyPD" not in df:
        return float("nan"), 0
    pdv = df["energyPD"]
    dk = pd.Series(pdv.index.date, index=pdv.index)
    d = pdv.diff()
    d = d.where(dk.eq(dk.shift(1)) & (d >= 0) & (d < 3000))           # descarta resets y saltos
    h = pd.DataFrame({"cnt": d, "pv": pv * P["DT_H"]}).dropna()
    day = h.groupby(h.index.date).sum()
    day = day[day.cnt > 3000]
    return (float((day.pv / day.cnt).median()) if len(day) else float("nan")), len(day)


def calibrate_deye_offset(deye: list[tuple[dict, pd.DataFrame]]):
    """Residuo diurno de las Deye: mediana horaria de (contador - balance) en casas con contador sano."""
    rows, used = [], []
    for meta, df in deye:
        o0 = pv_actual(meta, df, 0.0)
        r, n = counter_ratio(df, o0.pv)
        if n < 15 or not (0.5 <= r <= 1.5):
            continue                                                   # contador no confiable
        pdv = df["energyPD"]
        dk = pd.Series(pdv.index.date, index=pdv.index)
        d = pdv.diff()
        d = d.where(dk.eq(dk.shift(1)) & (d >= 0) & (d < 3000))
        hh = pd.DataFrame({"cnt": d, "pv": o0.pv * P["DT_H"]}).dropna().resample("1h").sum(min_count=3)
        hh = hh[(hh.index.hour >= 7) & (hh.index.hour <= 17)].dropna()
        hh = hh[hh.pv > 0]
        rows.append(hh.cnt - hh.pv)
        used.append(meta["spcus"])
    if len(used) < 2:
        return None
    allr = pd.concat(rows)
    return dict(w=float(allr.median()), casas=used, horas=int(len(allr)))


# ----------------------------------------------------------------------------- modelo
def build_panel(inv: dict, first: dt.date, nxt: dt.date, offset: float):
    idx = pd.date_range(first.isoformat(), pd.Timestamp(nxt) - pd.Timedelta(minutes=15), freq="15min", tz=TZ)
    fr = {c: pv_actual(m, df, offset) for c, (m, df) in inv.items()}
    Pn = {k: pd.DataFrame({c: o[k].reindex(idx) for c, o in fr.items()}) for k in ["pv", "load", "batt_chg", "grid_imp", "soc", "battcur"]}
    return idx, Pn


def flags(idx, Pn, socfull=None):
    socfull = P["SOC_FULL"] if socfull is None else socfull
    hr = idx.hour + idx.minute / 60
    day = pd.Series((hr >= P["SAT_FROM"]) & (hr <= P["SAT_TO"]), index=idx)
    soc, chg, imp, pv, cur = Pn["soc"], Pn["batt_chg"], Pn["grid_imp"].fillna(0), Pn["pv"], Pn["battcur"]
    p99 = cur.where((soc <= P["SENSOR_SOC_MAX"]) & (chg >= P["SENSOR_CHG_MIN_W"])).quantile(0.99)
    at_limit = cur.ge(P["AT_LIMIT_FRAC"] * p99, axis=1)
    absorbing = (soc <= P["SENSOR_SOC_MAX"]) & (chg >= P["SENSOR_CHG_MIN_W"]) & ~at_limit
    deficit = (chg <= -P["DEFICIT_W"]) | (imp >= P["DEFICIT_W"])
    U = ((absorbing | deficit) & pv.notna()).mul(day, axis=0).astype(bool)
    C = ((soc >= socfull) & (chg >= P["NO_DISCHARGE_W"]) & (imp < P["IMPORT_MAX_W"]) & pv.notna()).mul(day, axis=0).astype(bool)
    return U, C


def fit_rank1(pv, U):
    cas = pv.columns
    k = pd.Series(1.0, index=cas)
    for c in cas:
        v = pv[c][U[c]]
        k[c] = v.quantile(0.9) if len(v) > 20 else np.nan
    k = k / k.mean()
    for _ in range(P["ALS_ITERS"]):
        W = U.astype(float)
        S = ((pv * W * k).sum(axis=1) / (W * k ** 2).sum(axis=1)).where(U.sum(axis=1) >= P["MIN_PEERS"])
        k = (pv * U).mul(S, axis=0).sum() / U.mul(S ** 2, axis=0).sum()
        k = k / k.mean()
    return k, S


def lost_power(Pn, meta, C, k, S, scale=1.0, ratio=None):
    ratio = P["FLAG_RATIO"] if ratio is None else ratio
    pv = Pn["pv"]
    pot = pd.DataFrame({c: k[c] * S for c in pv.columns}) * scale
    for c in pv.columns:
        try:
            cap = float(meta[c]["invcap"]) * 1000 * P["CAP_FACTOR"]
            pot[c] = pot[c].clip(upper=cap)
        except (TypeError, ValueError):
            pass
    flag = C & pot.notna() & (pot > P["POT_MIN_W"]) & (pv < ratio * pot)
    lost = (pot - pv).where(flag, 0.0).clip(lower=0)
    return pot, flag, lost


def loo_validation(pv, U, k):
    ratios, rel = [], []
    for c in pv.columns:
        oth = [x for x in pv.columns if x != c]
        W = U[oth].astype(float)
        S_loo = ((pv[oth] * W * k[oth]).sum(axis=1) / (W * k[oth] ** 2).sum(axis=1)).where(U[oth].sum(axis=1) >= P["MIN_PEERS"])
        pred = k[c] * S_loo
        m = U[c] & pred.notna() & (pred > 300)
        a, p = pv[c][m], pred[m]
        ratios.append(a / p)
        rel.append((a - p).abs() / p)
    r, e = pd.concat(ratios), pd.concat(rel)
    return dict(n=int(len(r)), med=float(r.median()), p25=float(r.quantile(.25)), p75=float(r.quantile(.75)), mae=float(e.median()))


# ----------------------------------------------------------------------------- validaciones y datos del reporte
def deye_cloud_check(deye, first, last):
    sys.path.insert(0, str(REPO / ".claude/skills/om-agency/scripts"))
    import deye_adapter as da                                           # solo lectura (nivel 0)
    ad = da.DeyeAdapter()
    ad.login()
    rows = []
    for meta, df, pvs in deye:
        days = ad.history_days(meta["name"], first.isoformat(), last.isoformat())
        cd = pd.DataFrame(days).set_index("date")["Production"]
        cd.index = pd.to_datetime(cd.index).date
        mine = (pvs * P["DT_H"]).groupby(pvs.index.date).sum() / 1000
        d = pd.DataFrame({"cloud": cd, "mine": mine}).dropna()
        d = d[d.cloud > 1]
        if d.empty:
            continue
        rr = d.mine / d.cloud
        rows.append(dict(casa=meta["spcus"], dias=int(len(d)), mes=float(d.mine.sum() / d.cloud.sum()), dia_med=float(rr.median()),
                         p10=float(rr.quantile(.1)), p90=float(rr.quantile(.9)), r=float(d.cloud.corr(d.mine))))
    return rows


def titulo_zona(zona: str) -> str:
    small = {"de", "del", "la", "las", "los", "y", "el", "en"}
    return " ".join(w.lower() if w.lower() in small and i else w.capitalize() for i, w in enumerate(zona.split()))


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


MES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zona", required=True)
    ap.add_argument("--mes", required=True, help="AAAA-MM")
    ap.add_argument("--out", default=str(REPO / "reportes"))
    ap.add_argument("--cache", default=str(REPO / ".curtailment-cache"))
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--deye-offset", type=float)
    ap.add_argument("--sin-deye", action="store_true")
    ap.add_argument("--titulo")
    a = ap.parse_args()
    y, m = map(int, a.mes.split("-"))
    first = dt.date(y, m, 1)
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    last = nxt - dt.timedelta(days=1)
    if nxt > dt.date.today():
        warn(f"El mes {a.mes} no ha terminado: el reporte es parcial.")
    zona = a.zona.strip()
    titulo = a.titulo or titulo_zona(zona)
    cache = Path(a.cache) / f"{slug(zona)}-{a.mes}"

    log(f"[1/7] Inventario de Metrum para {zona}")
    mt = Metrum()
    allinv = inventory(mt)
    zdevs = [d for d in allinv if (d["zone"] or "").upper().strip() == zona.upper().strip() and d["type"] == "inverter" and d["spcus"]]
    if not zdevs:
        sys.exit(f"No hay inversores con zone == {zona!r}. Zonas disponibles: {sorted({d['zone'] for d in allinv if d['zone']})}")
    words = {w for w in re.split(r"\W+", zona.upper()) if len(w) >= 4}
    parecidas = sorted({d["zone"] for d in allinv if d["zone"] and d["zone"].upper().strip() != zona.upper().strip()
                        and words & {w for w in re.split(r"\W+", d["zone"].upper()) if len(w) >= 4}})
    log(f"      {len(zdevs)} inversores en la zona")

    log("[2/7] Descarga de telemetría (15 min)")
    download(mt, zdevs, first, nxt, cache, a.refresh)
    inv, excluded = load_inverters(cache, first, nxt, zdevs)
    if len(inv) < 6:
        warn(f"Solo {len(inv)} casas con datos: el índice solar de la flota es poco confiable.")
    log(f"      {len(inv)} casas con datos; {len(excluded)} equipos excluidos")

    log("[3/7] PV entregada por balance de potencias")
    deye_items = [(m_, df) for m_, df in inv.values() if m_["brand"] == "DEYE"]
    cal = calibrate_deye_offset(deye_items) if deye_items else None
    if a.deye_offset is not None:
        offset, off_src = a.deye_offset, "fijado por parámetro"
    elif cal:
        offset, off_src = cal["w"], "calibrado con el mes"
    else:
        offset, off_src = P["DEYE_OFFSET_DEFAULT"], "valor por defecto (no hubo casas Deye con contador sano para calibrar)"
        if deye_items:
            warn("No se pudo calibrar el residuo de las Deye con el mes; se usa el valor por defecto.")
    log(f"      residuo diurno Deye: {offset:.0f} W ({off_src})")
    idx, Pn = build_panel(inv, first, nxt, offset)
    meta = {c: m_ for c, (m_, _) in inv.items()}
    cas = list(Pn["pv"].columns)
    pv, load, soc = Pn["pv"], Pn["load"], Pn["soc"]

    log("[4/7] Estado saturado, PV potencial y energía perdida")
    U, C = flags(idx, Pn)
    k, S = fit_rank1(pv, U)
    pot, flag, lost = lost_power(Pn, meta, C, k, S)
    DT = P["DT_H"]
    lost_kwh = lost.sum() * DT / 1000
    lo_kwh = lost_power(Pn, meta, C, k, S, scale=P["POT_LOW"])[2].sum() * DT / 1000
    hi_kwh = lost_power(Pn, meta, C, k, S, scale=P["POT_HIGH"])[2].sum() * DT / 1000
    cn = lambda c: int(c.split()[1])
    hr = idx.hour + idx.minute / 60
    inday = (hr >= 6) & (hr < 18)
    days = sorted(set(idx.date))
    D_ = len(days)
    deliv = pv.where(pd.DataFrame({c: inday for c in cas}, index=idx), 0).fillna(0).sum() * DT / 1000

    log("[5/7] Validaciones")
    val: dict = dict(params={kk: P[kk] for kk in ("SOC_FULL", "FLAG_RATIO", "SAT_FROM", "SAT_TO", "POT_LOW", "POT_HIGH")})
    # a) PV vs contador diario de Metrum
    liv, deye_ok, deye_bad = [], [], []
    for c in cas:
        r, n = counter_ratio(inv[c][1], Pn["pv"][c].reindex(inv[c][1].index))
        if meta[c]["brand"] == "LIVOLTEK":
            if n >= 15 and np.isfinite(r):
                liv.append(r)
        elif n >= 15 and 0.7 <= r <= 1.4:
            deye_ok.append(dict(casa=c, ratio=r, dias=n))
        else:
            deye_bad.append(c)
    val["liv"] = dict(n=len(liv), mean=float(np.mean(liv)), std=float(np.std(liv))) if liv else None
    val["deye_counter"] = dict(ok=deye_ok, bad=deye_bad,
                               ratio_med=float(np.median([x["ratio"] for x in deye_ok])) if deye_ok else None)
    val["deye_offset"] = dict(w=offset, fuente=off_src, casas=(cal or {}).get("casas", []), horas=(cal or {}).get("horas", 0))
    # b) nube de Deye
    val["deye_cloud"] = None
    if deye_items and not a.sin_deye:
        try:
            items = [(m_, df, Pn["pv"][m_["spcus"]].reindex(df.index)) for m_, df in deye_items]
            val["deye_cloud"] = deye_cloud_check(items, first, last)
        except Exception as e:                                                     # noqa: BLE001
            warn(f"No se pudo validar contra la nube de Deye: {str(e)[:120]}")
    # c) leave-one-out del potencial
    val["loo"] = loo_validation(pv, U, k)
    if val["loo"]["mae"] > 0.20:
        warn(f"El error mediano del potencial (leave-one-out) es {val['loo']['mae']*100:.0f} %: el resultado es poco confiable.")
    cov_w = C.sum(axis=1)
    val["cobertura_pct"] = float((cov_w * S.notna()).sum() / cov_w.sum() * 100) if cov_w.sum() else 0.0
    if val["cobertura_pct"] < 90:
        warn(f"El potencial solo cubre {val['cobertura_pct']:.0f} % de los intervalos saturados.")
    # d) zero export y PV/consumo
    exp = 0.0
    for c in cas:
        s = inv[c][1]["energyED"] if "energyED" in inv[c][1] else None
        if s is not None:
            exp += float(s.groupby(s.index.date).apply(lambda x: x.iloc[-2] if len(x) > 2 else 0).sum() / 1000)
    val["export_kwh"] = exp
    rr_ = (pv.where(flag) / load.where(flag)).to_numpy().ravel()
    val["pv_load_med"] = float(np.nanmedian(rr_)) if np.isfinite(rr_).any() else None
    # e) sensibilidad
    sens = []
    for name, kw in [("Potencial −12 %", dict(scale=P["POT_LOW"])), ("Potencial +12 %", dict(scale=P["POT_HIGH"])),
                     ("SOC = 100 % estricto", dict(socfull=100)), ("Umbral PV < 70 % del potencial", dict(ratio=0.70)),
                     ("Umbral PV < 95 % del potencial", dict(ratio=0.95))]:
        Cv = flags(idx, Pn, kw.get("socfull"))[1] if "socfull" in kw else C
        kk = lost_power(Pn, meta, Cv, k, S, scale=kw.get("scale", 1.0), ratio=kw.get("ratio"))[2].sum() * DT / 1000
        sens.append(dict(name=name, fleet=round(float(kk.sum())), rho=round(float(lost_kwh.rank().corr(kk.rank())), 3),
                         top5=[cn(x) for x in kk.sort_values(ascending=False).index[:5]]))
    val["sens"] = sens
    val["excluded"] = excluded
    val["zonas_parecidas"] = parecidas
    val["n_inv"] = len(inv)
    val["warnings"] = WARN

    log("[6/7] Métricas por casa, matrices y series")
    res_c = []
    for c in cas:
        f, mt_ = flag[c], meta[c]
        s99 = (soc[c] >= 99) & inday
        fills = []
        for d in days:
            sel = s99[(idx.date == d)]
            if sel.any():
                fills.append(float(hr[(idx.date == d)][sel.values][0]))
        mid = (hr >= 10) & (hr < 15)
        avail_mid = (pv[c] + lost[c])[mid]
        r = dict(id=c, n=cn(c), marca=mt_["brand"].title(), modelo=(mt_["invmodel"] or "").strip(), kw=int(float(mt_["invcap"] or 0)),
                 lost=round(float(lost_kwh[c]), 1), lost_lo=round(float(lo_kwh[c]), 1), lost_hi=round(float(hi_kwh[c]), 1),
                 deliv=round(float(deliv[c]), 1), pct=round(float(lost_kwh[c] / (lost_kwh[c] + deliv[c]) * 100), 1),
                 horas=round(float(f.sum() * DT), 1), dias=int(f.groupby(idx.date).any().sum()),
                 horas_sat=round(float(C[c].sum() * DT), 1),
                 fill_med=round(float(np.median(fills)), 2) if fills else None, fill_dias=len(fills),
                 load_rec=round(float(load[c][f].mean())) if f.any() else None,
                 avail_rec=round(float((pv[c] + lost[c])[f].mean())) if f.any() else None,
                 peak_lost=round(float(lost[c].max())),
                 load_mid=round(float(load[c][mid].mean())), avail_mid=round(float(avail_mid.mean())),
                 kwh_dia_max=round(float(lost[c].groupby(idx.date).sum().max() * DT / 1000), 1))
        r["cons_pct"] = round(r["load_mid"] / r["avail_mid"] * 100, 1) if r["avail_mid"] else None
        res_c.append(r)
    casa_day = [[round(float(lost[c][idx.date == d].sum() * DT / 1000), 2) for d in days] for c in cas]
    hours = list(range(6, 18))
    casa_hour = [[round(float(lost[c][idx.hour == h].sum() * DT / 1000), 2) for h in hours] for c in cas]
    fleet_day = [round(sum(casa_day[i][j] for i in range(len(cas))), 1) for j in range(D_)]
    fleet_day_n = [int(sum(1 for i in range(len(cas)) if casa_day[i][j] > 0.05)) for j in range(D_)]
    Sd = S.groupby(idx.date).sum(min_count=1)
    sun = (Sd / Sd.max() * 100).round(0)
    sun_idx = [None if pd.isna(sun.get(d, np.nan)) else int(sun.get(d)) for d in days]
    slot = idx.hour * 4 + idx.minute // 15
    slots = list(range(24, 72))
    curve = dict(slots=slots, deliv=[round(float(pv.loc[slot == s_].mean().mean())) for s_ in slots],
                 avail=[round(float((pv + lost).loc[slot == s_].mean().mean())) for s_ in slots])
    ser = []
    for c in cas:
        per_day = []
        for d in days:
            msk = (idx.date == d) & inday
            sl = lambda s: [None if pd.isna(v) else int(round(v)) for v in s[msk].values]
            per_day.append([sl(pv[c]), sl(pot[c]), sl(load[c]), sl(soc[c]), sl(lost[c])])
        ser.append(per_day)
    tot, totd = float(lost_kwh.sum()), float(deliv.sum())
    periodo = f"{first.day}–{last.day} {MES_ES[m - 1]} {y}"
    out = dict(zona=zona, zona_titulo=titulo, periodo=periodo, mes=a.mes, fecha_gen=dt.date.today().isoformat(),
               total=dict(lost=round(tot), lost_lo=round(float(lo_kwh.sum())), lost_hi=round(float(hi_kwh.sum())),
                          deliv=round(totd), pct=round(tot / (tot + totd) * 100, 1), n_casas=len(cas)),
               casas=res_c, order=[r["id"] for r in sorted(res_c, key=lambda r: -r["lost"])],
               dates=[d.isoformat() for d in days], casa_day=casa_day, hours=hours, casa_hour=casa_hour,
               fleet_day=fleet_day, fleet_day_n=fleet_day_n, sun_idx=sun_idx,
               curve=curve, cas=cas, series=ser, val=val)

    log("[7/7] HTML")
    tpl = (HERE / "template.html").read_text(encoding="utf-8")
    full_title = htmllib.escape(f"Curtailment {titulo}")
    frag = tpl.replace("__TITLE__", full_title).replace("__DATA__", json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    head = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n')
    full = head + frag.replace("</style>", "</style>\n</head>\n<body>", 1) + "\n</body>\n</html>\n"
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    name = f"curtailment-{slug(zona)}-{a.mes}"
    (outdir / f"{name}.html").write_text(full, encoding="utf-8")
    (cache / f"{name}.fragmento.html").write_text(frag, encoding="utf-8")

    top = sorted(res_c, key=lambda r: -r["lost"])
    log("\n==== RESUMEN ====")
    log(f"Total perdido: {tot:,.0f} kWh (rango {out['total']['lost_lo']:,}–{out['total']['lost_hi']:,}) · {out['total']['pct']} % de lo disponible")
    log("Top 5: " + " · ".join(f"{r['id']} {r['lost']:.0f} kWh ({r['pct']} %)" for r in top[:5]))
    if val["liv"]:
        log(f"PV vs contador (Livoltek): {val['liv']['mean']:.3f} ± {val['liv']['std']:.3f} en {val['liv']['n']} casas")
    if val["deye_cloud"]:
        rr = [x["mes"] for x in val["deye_cloud"]]
        log(f"PV vs nube Deye: razón mensual {min(rr):.2f}–{max(rr):.2f} en {len(rr)} casas")
    log(f"Potencial leave-one-out: razón {val['loo']['med']:.2f} (IQR {val['loo']['p25']:.2f}–{val['loo']['p75']:.2f}), error mediano {val['loo']['mae']*100:.0f} %")
    log(f"Exportación de la flota: {exp:.1f} kWh · PV/consumo en curtailment: {val['pv_load_med']:.2f} · cobertura del potencial: {val['cobertura_pct']:.0f} %")
    log("Sensibilidad: " + " | ".join(f"{s['name']}: {s['fleet']} kWh (ρ {s['rho']})" for s in sens))
    if excluded:
        log("Excluidos: " + "; ".join(f"{e['casa']} {e['marca']} ({e['motivo']})" for e in excluded))
    log(f"HTML: {outdir / (name + '.html')}\nFragmento para artefacto: {cache / (name + '.fragmento.html')}")
    if WARN:
        log("\nADVERTENCIAS:\n - " + "\n - ".join(WARN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
