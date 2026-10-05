#!/usr/bin/env python3
"""Adaptador DeyeCloud para om-agency (SOLO LECTURA por defecto).

Credenciales únicamente desde el entorno (nunca se imprimen ni se escriben):
  DEYE_API_URL, DEYE_APP_ID, DEYE_APP_SECRET, DEYE_USERNAME, DEYE_PASSWORD, DEYE_COMPANY_ID
El password se envía como SHA-256 en minúsculas, calculado dentro del proceso.
El token vive solo en memoria.

Uso (todo es lectura; la salida es JSON):
  python3 deye_adapter.py devices
  python3 deye_adapter.py latest SN [SN ...]
  python3 deye_adapter.py normalized SN
  python3 deye_adapter.py frames SN 2026-10-03 [--points SOC,BatteryPower,...]
  python3 deye_adapter.py days SN 2026-10-03 2026-10-04
  python3 deye_adapter.py alerts SN 2026-10-01 2026-10-05
  python3 deye_adapter.py config SN

Escritura: NO hay comando de CLI. Solo existe `DeyeAdapter.write_order()` (Python), que por
defecto es un ensayo (dry-run) y exige confirmación; ver la política de 4 niveles en
SKILL.md (Apéndice B.5). El nivel 3 (reseteo de fábrica, bloqueo, EEPROM, registros de
fábrica) se rechaza siempre. `write_order(execute=True)` NO está probado contra la API real.

Límites verificados en la Casa 10 (oct-2026): device/latest ≤ 10 SN; device/list ≤ 200 por
página; history granularity 1 exige endAt y ≤ 5 measurePoints por consulta (se pide en lotes
de 5 y se fusiona por `time`); alertList ≤ 30 días; historyRaw ≤ 5 días.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV_SECRETS = ("DEYE_API_URL", "DEYE_APP_ID", "DEYE_APP_SECRET", "DEYE_USERNAME",
               "DEYE_PASSWORD", "DEYE_COMPANY_ID")

# --------------------------------------------------------------------------- #
# Políticas
# --------------------------------------------------------------------------- #
READ_POST = {
    "/v1.0/account/info", "/v1.0/station/list", "/v1.0/station/listWithDevice",
    "/v1.0/station/device", "/v1.0/station/latest", "/v1.0/station/history",
    "/v1.0/station/history/power", "/v1.0/station/alertList", "/v1.0/device/list",
    "/v1.0/device/latest", "/v1.0/device/history", "/v1.0/device/historyRaw",
    "/v1.0/device/measurePoints", "/v1.0/device/alertList", "/v1.0/config/battery",
    "/v1.0/config/system", "/v1.0/config/tou",
}
READ_GET_PREFIX = "/v1.0/order/"   # consulta del resultado de una orden

# Órdenes de control -> nivel de política (SKILL.md B.5). Cualquier otra ruta se rechaza.
ORDER_LEVELS = {
    "/v1.0/order/sys/workMode/update": 1, "/v1.0/order/sys/energyPattern/update": 1,
    "/v1.0/order/sys/limitControl": 1, "/v1.0/order/sys/solarSell/control": 1,
    "/v1.0/order/sys/tou/switch": 1, "/v1.0/order/sys/tou/update": 1,
    "/v1.0/order/battery/modeControl": 1, "/v1.0/order/battery/parameter/update": 1,
    "/v1.0/order/gridPeakShaving/control": 1, "/v1.0/order/smartload/update": 1,
    "/v1.0/order/sys/power/update": 2, "/v1.0/strategy/dynamicControl": 2,
    "/v1.0/order/customControl": 2, "/v1.0/order/battery/type/update": 2,
}

# Registros Modbus (PDF "Deye SUN Inverter Modbus" v105). Solo 60-499 y 1000-1121 son escribibles.
PROHIBITED = (set(range(190, 211)) | {60, 80, 81, 91, 92, 93, 94, 97}
              | set(range(559, 584)) | {738, 739, 800})
LEVEL2 = (set(range(74, 80)) | set(range(82, 89)) | {143, 179, 340}
          | set(range(346, 493)) | set(range(1000, 1122)))


def classify_register(reg: int) -> int | None:
    """3 = prohibido, 2 = red/protecciones (aprobación explícita), 1 = operativo, None = no escribible."""
    if reg in PROHIBITED:
        return 3
    if not (60 <= reg <= 499 or 1000 <= reg <= 1121):
        return None            # solo-lectura o no documentado: nunca escribir
    return 2 if reg in LEVEL2 else 1


class Refused(Exception):
    """Operación rechazada por política (no se envió nada a la nube)."""


def redact(text: str) -> str:
    for n in ENV_SECRETS:
        v = os.environ.get(n, "")
        if len(v) >= 4:
            text = text.replace(v, f"<{n}>")
    return re.sub(r"eyJ[A-Za-z0-9_\-\.]{20,}", "<jwt>", text)


def _env(name: str) -> str:
    v = os.environ.get(name, "")
    if not v:
        raise SystemExit(f"Falta la variable de entorno {name}")
    return v


# --------------------------------------------------------------------------- #
# Normalización (esquema común entre marcas) — convenciones del Apéndice B.0
#   bat_power_w  : + = CARGA   (Deye/Metrum nativo es + = descarga → se invierte)
#   bat_current_a: + = CARGA   (coherente con bat_power_w)
#   grid_power_w : + = IMPORTACIÓN
# --------------------------------------------------------------------------- #
GRID_DOWN_V = 20.0   # umbral usado en la validación (cortes coinciden con Metrum ±5 min)


def _f(points: dict, key: str):
    v = points.get(key)
    if v is None:
        return None
    try:
        return float(v[0] if isinstance(v, tuple) else v)
    except (TypeError, ValueError):
        return None


def normalize_latest(points: dict) -> dict:
    neg = lambda x: None if x is None else (0.0 if x == 0 else -x)  # noqa: E731
    gv = [_f(points, k) for k in ("GridVoltageL1", "GridVoltageL2", "GridVoltageL3")]
    grid_up = None if None in gv else min(gv) >= GRID_DOWN_V
    return {
        "soc_pct": _f(points, "SOC") if _f(points, "SOC") is not None else _f(points, "BMSSOC"),
        "bat_power_w": neg(_f(points, "BatteryPower")),
        "bat_voltage_v": _f(points, "BatteryVoltage"),
        "bat_current_a": neg(_f(points, "BatteryCurrent")),
        "bat_temp_c": _f(points, "Temperature- Battery"),
        "pv_power_w": _f(points, "TotalSolarPower"),
        "load_power_w": _f(points, "TotalConsumptionPower"),
        "grid_power_w": _f(points, "TotalGridPower"),
        "grid_voltage_v": gv,
        "grid_freq_hz": _f(points, "GridFrequency"),
        "ac_out_freq_hz": _f(points, "ACOutputFrequencyR") if _f(points, "ACOutputFrequencyR") is not None
        else _f(points, "LoadFrequency"),
        "energy_day_kwh": {
            "pv": _f(points, "DailyActiveProduction"), "load": _f(points, "DailyConsumption"),
            "import": _f(points, "DailyEnergyPurchased"), "export": _f(points, "DailyGridFeedIn"),
            "bat_charge": _f(points, "DailyChargingEnergy"),
            "bat_discharge": _f(points, "DailyDischargingEnergy"),
        },
        "energy_total_kwh": {
            "pv": _f(points, "TotalActiveProduction"), "load": _f(points, "TotalConsumption"),
            "import": _f(points, "TotalEnergyBuy"), "export": _f(points, "TotalEnergySell"),
            "bat_charge": _f(points, "TotalChargeEnergy"),
            "bat_discharge": _f(points, "TotalDischargeEnergy"),
        },
        "grid_up": grid_up,
    }


# --------------------------------------------------------------------------- #
# Adaptador
# --------------------------------------------------------------------------- #
class DeyeAdapter:
    def __init__(self, min_interval: float = 0.4, max_retries: int = 4):
        self.base = _env("DEYE_API_URL").rstrip("/")
        self.min_interval, self.max_retries = min_interval, max_retries
        self._token: str | None = None
        self._last = 0.0
        self.calls = 0
        cd = os.environ.get("DEYE_CACHE_DIR")
        self.cache_dir = Path(cd) if cd else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- HTTP ---------------------------------------------------------------
    def _http(self, method: str, path: str, body: dict | None = None, query: str = "", auth=True):
        headers = {"Content-Type": "application/json", "User-Agent": "om-agency-deye-adapter/1.0"}
        if auth:
            headers["Authorization"] = self._token or ""
        data = None if method == "GET" else json.dumps(body or {}).encode()
        req = urllib.request.Request(f"{self.base}{path}{query}", data=data, headers=headers, method=method)
        for attempt in range(self.max_retries + 1):
            time.sleep(max(0.0, self.min_interval - (time.time() - self._last)))
            self._last = time.time()
            self.calls += 1
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                snippet = redact(e.read().decode("utf-8", "replace")[:300])
                if e.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise RuntimeError(f"HTTP {e.code} en {path}: {snippet}") from None
            except urllib.error.URLError as e:
                if attempt < self.max_retries:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise RuntimeError(f"Red en {path}: {redact(str(e.reason))}") from None

    def login(self) -> None:
        user = _env("DEYE_USERNAME")
        body = {
            "appSecret": _env("DEYE_APP_SECRET"),
            "password": hashlib.sha256(_env("DEYE_PASSWORD").encode()).hexdigest(),
            "companyId": int(_env("DEYE_COMPANY_ID")),
            ("email" if "@" in user else "username"): user,
        }
        res = self._http("POST", "/v1.0/account/token", body, f"?appId={_env('DEYE_APP_ID')}", auth=False)
        if not res.get("success") or not res.get("accessToken"):
            raise RuntimeError(f"Login falló: code={res.get('code')} msg={redact(str(res.get('msg')))}")
        tok = res["accessToken"]
        self._token = tok if tok.lower().startswith("bearer ") else f"Bearer {tok}"

    def read(self, path: str, body: dict | None = None, *, cache: bool = False):
        if path not in READ_POST:
            raise Refused(f"{path} no está en la lista de lectura")
        key = hashlib.sha256(f"{path}{json.dumps(body, sort_keys=True)}".encode()).hexdigest()[:24]
        f = self.cache_dir / f"{key}.json" if (cache and self.cache_dir) else None
        if f and f.exists():
            return json.loads(f.read_text())
        if self._token is None:
            self.login()
        res = self._http("POST", path, body)
        if res.get("success") is False or res.get("code") not in (None, 1000000, "1000000"):
            raise RuntimeError(f"{path}: code={res.get('code')} msg={redact(str(res.get('msg')))}")
        if f:
            f.write_text(json.dumps(res, ensure_ascii=False))
        return res

    # -- lectura ------------------------------------------------------------
    def list_devices(self, page_size: int = 200) -> list[dict]:
        out, page = [], 1
        while True:
            r = self.read("/v1.0/device/list", {"page": page, "size": page_size})
            batch = r.get("deviceList") or []
            out += batch
            if not batch or len(out) >= int(r.get("total", 0)):
                return out
            page += 1

    def latest(self, sns: list[str]) -> dict[str, dict]:
        out = {}
        for i in range(0, len(sns), 10):                     # ≤ 10 SN por llamada
            r = self.read("/v1.0/device/latest", {"deviceList": sns[i:i + 10]})
            for d in r.get("deviceDataList") or []:
                out[d["deviceSn"]] = {
                    "state": d.get("deviceState"), "collected_at": d.get("collectionTime"),
                    "points": {p["key"]: (p["value"], p.get("unit")) for p in d.get("dataList", [])},
                }
        return out

    def normalized(self, sn: str) -> dict:
        d = self.latest([sn]).get(sn)
        if not d:
            raise RuntimeError(f"{sn}: sin datos en device/latest")
        return {"sn": sn, "state": d["state"], "collected_at": d["collected_at"],
                **normalize_latest(d["points"])}

    def history_frames(self, sn: str, day: str, points: list[str], *, closed_day: bool = True) -> dict:
        """Tramas (~5 min) de un día. Lotes de 5 puntos, `endAt = startAt`, fusión por `time`."""
        merged: dict[int, dict] = {}
        for i in range(0, len(points), 5):
            r = self.read("/v1.0/device/history", {
                "deviceSn": sn, "granularity": 1, "startAt": day, "endAt": day,
                "measurePoints": points[i:i + 5]}, cache=closed_day)
            for fr in r.get("dataList") or []:
                row = merged.setdefault(int(fr["time"]), {})
                for it in fr.get("itemList", []):
                    row[it["key"]] = float(it["value"])
        return dict(sorted(merged.items()))

    def history_days(self, sn: str, start: str, end: str) -> list[dict]:
        """Estadísticas diarias (granularity 2, hasta 31 días)."""
        r = self.read("/v1.0/device/history", {
            "deviceSn": sn, "granularity": 2, "startAt": start, "endAt": end})
        return [{"date": d["time"], **{(i.get("key") or i.get("name")): float(i["value"])
                                      for i in d.get("itemList", [])}} for d in r.get("dataList", [])]

    def alerts(self, sn: str, start_ts: int, end_ts: int, page_size: int = 100) -> list[dict]:
        out, page = [], 1
        while True:
            r = self.read("/v1.0/device/alertList", {
                "deviceSn": sn, "startTimestamp": start_ts, "endTimestamp": end_ts,
                "page": page, "size": page_size})
            batch = r.get("alertList") or []
            out += batch
            if not batch or len(out) >= int(r.get("total", 0)):
                return out
            page += 1

    def config(self, sn: str) -> dict:
        strip = lambda r: {k: v for k, v in r.items() if k not in ("code", "msg", "success", "requestId")}  # noqa: E731
        return {n: strip(self.read(f"/v1.0/config/{n}", {"deviceSn": sn}))
                for n in ("battery", "system", "tou")}

    def order_result(self, order_id: str):
        if self._token is None:
            self.login()
        return self._http("GET", f"{READ_GET_PREFIX}{order_id}")

    # -- escritura (ensayo por defecto; nunca desde la CLI) ----------------------
    def write_order(self, sn: str, path: str, body: dict, *, confirmed_by: str,
                    approval_ref: str | None = None, registers: list[int] | None = None,
                    execute: bool = False) -> dict:
        """Ensaya (o ejecuta) una orden de control aplicando la política de 4 niveles.

        - `confirmed_by`: quién confirmó SN + acción + valor (obligatorio).
        - `approval_ref`: referencia de la aprobación explícita (obligatoria en nivel 2).
        - `registers`: registros Modbus que el comando tocará (obligatorio en customControl).
        - `execute=False` → solo ensayo: NO se contacta la nube.
        - `execute=True` exige además DEYE_ALLOW_WRITE=1 y DEYE_AUDIT_LOG (archivo JSONL).
        """
        level = ORDER_LEVELS.get(path)
        if level is None:
            raise Refused(f"{path}: fuera de la política (solo órdenes documentadas de nivel 1-2)")
        regs = list(registers or [])
        if path == "/v1.0/order/customControl" and not regs:
            raise Refused("customControl (Modbus crudo): declara los registros que tocará (registers=[...])")
        for r in regs:
            lv = classify_register(r)
            if lv == 3:
                raise Refused(f"registro {r}: NIVEL 3 PROHIBIDO (reseteo/bloqueo/EEPROM/fábrica)")
            if lv is None:
                raise Refused(f"registro {r}: solo-lectura o no documentado; no se escribe")
            level = max(level, lv)
        if not confirmed_by:
            raise Refused("falta confirmed_by (confirmación explícita de SN + acción + valor)")
        if level >= 2 and not approval_ref:
            raise Refused("nivel 2: falta approval_ref (aprobación explícita y específica)")
        payload = {**body, "deviceSn": sn}
        audit = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "sn": sn, "path": path,
                 "level": level, "body": payload, "registers": regs,
                 "confirmed_by": confirmed_by, "approval_ref": approval_ref,
                 "mode": "execute" if execute else "dry-run"}
        if not execute:
            self._audit(audit)
            return {"dry_run": True, "level": level, "would_send": {"path": path, "body": payload}}
        if os.environ.get("DEYE_ALLOW_WRITE") != "1":
            raise Refused("escritura real deshabilitada: define DEYE_ALLOW_WRITE=1 (decisión humana)")
        if not os.environ.get("DEYE_AUDIT_LOG"):
            raise Refused("escritura real exige DEYE_AUDIT_LOG (auditoría propia obligatoria)")
        self._audit(audit)
        if self._token is None:
            self.login()
        res = self._http("POST", path, payload)
        self._audit({**audit, "mode": "response", "response": {k: res.get(k) for k in ("code", "success", "orderId")}})
        return res

    @staticmethod
    def _audit(rec: dict) -> None:
        log = os.environ.get("DEYE_AUDIT_LOG")
        if log:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- #
# CLI (solo lectura)
# --------------------------------------------------------------------------- #
DEFAULT_FRAME_POINTS = ["SOC", "BatteryPower", "BatteryVoltage", "BatteryCurrent", "TotalGridPower",
                        "GridVoltageL1", "TotalConsumptionPower", "TotalSolarPower", "DailyActiveProduction",
                        "DailyChargingEnergy"]


def _ts(day: str, tz_hours: float, end_of_day: bool = False) -> int:
    d = dt.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=dt.timezone(dt.timedelta(hours=tz_hours)))
    return int((d + dt.timedelta(days=1 if end_of_day else 0)).timestamp())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--tz-offset", type=float, default=float(os.environ.get("DEYE_TZ_OFFSET", "-5")),
                    help="huso horario local en horas (Colombia = -5)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("devices")
    for name in ("latest",):
        sub.add_parser(name).add_argument("sn", nargs="+")
    for name in ("normalized", "config"):
        sub.add_parser(name).add_argument("sn")
    p = sub.add_parser("frames"); p.add_argument("sn"); p.add_argument("day"); p.add_argument("--points")
    p = sub.add_parser("days"); p.add_argument("sn"); p.add_argument("start"); p.add_argument("end")
    p = sub.add_parser("alerts"); p.add_argument("sn"); p.add_argument("start"); p.add_argument("end")
    a = ap.parse_args()

    d = DeyeAdapter()
    if a.cmd == "devices":
        out = d.list_devices()
    elif a.cmd == "latest":
        out = d.latest(a.sn)
    elif a.cmd == "normalized":
        out = d.normalized(a.sn)
    elif a.cmd == "config":
        out = d.config(a.sn)
    elif a.cmd == "frames":
        pts = a.points.split(",") if a.points else DEFAULT_FRAME_POINTS
        closed = a.day < dt.date.today().isoformat()
        out = {str(k): v for k, v in d.history_frames(a.sn, a.day, pts, closed_day=closed).items()}
    elif a.cmd == "days":
        out = d.history_days(a.sn, a.start, a.end)
    else:  # alerts
        out = d.alerts(a.sn, _ts(a.start, a.tz_offset), _ts(a.end, a.tz_offset, end_of_day=True))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refused as exc:
        print(f"RECHAZADO: {exc}", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:  # noqa: BLE001 - CLI: mensaje claro en vez de traceback
        print(f"ERROR: {redact(str(exc))}", file=sys.stderr)
        sys.exit(2)
