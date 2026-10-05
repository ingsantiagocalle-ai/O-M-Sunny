#!/usr/bin/env python3
"""Adaptador Livoltek para om-agency (SOLO LECTURA).

Mismo contrato B.0 que `deye_adapter.py`: login, list_devices, latest, normalized, history,
alerts, config, write_order (+ classify_register). Solo biblioteca estándar.

Credenciales únicamente desde el entorno (nunca se imprimen ni se escriben):
  LIVOLTEK_API_URL     base del servidor (International https://api.livoltek-portal.com:8081 o
                       Europa https://api-eu.livoltek-portal.com:8081)
  LIVOLTEK_SECUID      Security ID  -> cuerpo del login
  LIVOLTEK_KEY         Security Key -> cuerpo del login
  LIVOLTEK_USER_TOKEN  token de cuenta o de sitio -> parámetro `userToken` de la URL
  LIVOLTEK_USER_TYPE   0 usuario final · 1 agente/instalador -> parámetro `userType`
Opcionales: LIVOLTEK_TZ_OFFSET (horas; Colombia = -5), LIVOLTEK_CACHE_DIR, LIVOLTEK_AUDIT_LOG,
LIVOLTEK_BUDGET_FILE. El token del login vive solo en memoria.

Flujo (doc v1.6.0):  POST {base}/hess/api/login {"secuid","key"} -> data.data = token
                     GET  {base}/hess/api/...?userToken=…&userType=…  con cabecera `Authorization: <token>`

Uso (todo es lectura; la salida es JSON y pasa por la redacción de secretos):
  python3 livoltek_adapter.py sites
  python3 livoltek_adapter.py site-of SN
  python3 livoltek_adapter.py devices SITE_ID
  python3 livoltek_adapter.py latest SN            # respuestas crudas (varias llamadas)
  python3 livoltek_adapter.py normalized SN        # esquema B.0
  python3 livoltek_adapter.py realtime SN [--start "AAAA-MM-DD HH:MM:SS"] [--end …] [--last 12]
  python3 livoltek_adapter.py ess SITE_ID [--history]
  python3 livoltek_adapter.py alarms SN [DESDE HASTA]        # por defecto, los últimos 7 días
  python3 livoltek_adapter.py powerflow SITE_ID DESDE HASTA [--interval 0]
  python3 livoltek_adapter.py energy SITE_ID DESDE HASTA day|week|month|year [--only grid|solar]
  python3 livoltek_adapter.py url ENDPOINT_ID [--site-id X] [--sn Y] [--device-id Z]
        # construye la consulta con las variables de entorno SIN red y con los secretos enmascarados

Escritura: NO hay comando de CLI. `LivoltekAdapter.write_order()` solo ensaya (dry-run) aplicando la
política de 4 niveles de SKILL.md (B.5) y **nunca contacta la red**; `execute=True` se rechaza porque los
endpoints de control exigen `account`+`pwd` de la cuenta (no están en el entorno) y no se han probado.

Límites de la doc (sin verificar en vivo; ver references/livoltek/limites.md): 300 llamadas/h por IP o
Security ID, 300/h por interfaz, **100/h por userToken**, 3 simultáneas (429; aquí siempre 1), token usado
desde ≤ 3 IP (428 «token occupied»), ventanas de 7 días y de 2 años.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REF_DIR = SKILL_DIR / "references" / "livoltek"
API_PREFIX = "/hess/api"
ENV_SECRETS = ("LIVOLTEK_API_URL", "LIVOLTEK_SECUID", "LIVOLTEK_KEY", "LIVOLTEK_USER_TOKEN")
ENV_ALL = ENV_SECRETS + ("LIVOLTEK_USER_TYPE",)
UA = "om-agency-livoltek-adapter/1.0"

LIMIT_PER_TOKEN = 100      # llamadas/hora por userToken (doc)
LIMIT_PER_IP = 300         # llamadas/hora por IP o Security ID (doc)
WINDOW_S = 3600.0
RECENT_DAYS = 7            # ventana de HisPowerflow, power, alarm, realTime (doc)
RECENT_YEARS = 2           # ventana de solarEnergy y utilityEnergy en día/semana (doc)
MAX_SPAN_DAY = 31          # días máximos por consulta con timeType 0 (doc)
MAX_SPAN_WEEK = 180        # días máximos por consulta con timeType 1 (doc)
PAGE_SIZE = 30             # la doc solo permite 5, 10 (defecto) o 30


class Refused(Exception):
    """Operación rechazada por política (no se envió nada a la nube)."""


class BudgetExceeded(RuntimeError):
    """Se agotó el presupuesto horario; no se llamó a la nube."""


class TokenOccupied(RuntimeError):
    """HTTP 428 «token occupied»: el userToken ya se usa desde 3 IP o Security ID distintos."""


# --------------------------------------------------------------------------- #
# Redacción de secretos (en toda salida y todo error)
# --------------------------------------------------------------------------- #
_RUNTIME_SECRETS: set[str] = set()


def redact(text) -> str:
    text = str(text)
    for v in sorted(_RUNTIME_SECRETS, key=len, reverse=True):
        if len(v) >= 4:
            text = text.replace(v, "<token>")
    for n in ENV_SECRETS:
        v = os.environ.get(n, "")
        if len(v) >= 4:
            text = text.replace(v, f"<{n}>")
    text = re.sub(r"(userToken=)[^&\s\"']+", r"\1<LIVOLTEK_USER_TOKEN>", text)
    text = re.sub(r'("(?:key|pwd|password|secuid|account)"\s*:\s*)"[^"]*"', r'\1"<redactado>"', text)
    return re.sub(r"eyJ[A-Za-z0-9_\-\.]{20,}", "<jwt>", text)


def _env(name: str) -> str:
    v = os.environ.get(name, "")
    if not v:
        raise SystemExit(f"Falta la variable de entorno {name}")
    return v


def check_env() -> dict:
    """Solo booleanos: definida / sin caracteres de control ni espacios en los bordes. Nunca valores."""
    out = {}
    for n in ENV_ALL:
        v = os.environ.get(n)
        out[n] = {
            "definida": bool(v),
            "sin_caracteres_de_control": bool(v) and not re.search(r"[\x00-\x1f\x7f]", v) and v == v.strip(),
        }
    out["LIVOLTEK_USER_TYPE"]["valor_valido_0_o_1"] = os.environ.get("LIVOLTEK_USER_TYPE") in ("0", "1")
    api = os.environ.get("LIVOLTEK_API_URL", "")
    sp = urllib.parse.urlsplit(api) if api else None
    out["LIVOLTEK_API_URL"]["es_https_con_host"] = bool(sp and sp.scheme == "https" and sp.hostname)
    return out


# --------------------------------------------------------------------------- #
# Catálogo de lectura (ids = nodos de la doc; rutas verificadas contra endpoints.json en las pruebas)
# --------------------------------------------------------------------------- #
READ: dict[str, tuple[str, str]] = {
    "siteList": ("GET", "/hess/api/userSites/list"),
    "deviceList": ("GET", "/hess/api/device/{siteId}/list"),
    "currentPowerFlow": ("GET", "/hess/api/site/{siteId}/curPowerflow"),
    "siteHistoricalPowerFlow": ("GET", "/hess/api/site/{siteId}/HisPowerflow"),
    "siteHistoricalActivePower": ("GET", "/hess/api/site/{siteId}/power"),
    "storageInformation": ("GET", "/hess/api/site/{siteId}/ESS"),
    "deviceTechnical": ("GET", "/hess/api/device/{siteId}/{serialNumber}/realTime"),
    "deviceDetails": ("GET", "/hess/api/device/{siteId}/{serialNumber}/details"),
    "deviceHistoricalAlarm": ("GET", "/hess/api/device/{siteId}/{serialNumber}/alarm"),
    "deviceOneDayFaultAlarm": ("GET", "/hess/api/device/{siteId}/{serialNumber}/oneDayFaultAlarm"),
    "queryPowerStationId": ("GET", "/hess/api/site/{serialNumber}"),
    "siteHistoricalGrid": ("GET", "/hess/api/site/{siteId}/utilityEnergy"),
    "siteHistoricalSolar": ("GET", "/hess/api/site/{siteId}/solarEnergy"),
    "siteDetails": ("GET", "/hess/api/site/{siteId}/details"),
    "siteGenerationOverview": ("GET", "/hess/api/site/{siteId}/overview"),
    "deviceBasicData": ("GET", "/hess/api/device/basicData"),
    "deviceGenerationOrConsumption": ("GET", "/hess/api/device/{deviceId}/realElectricity"),
    # POST que SOLO LEEN (el método HTTP no basta para clasificar); una consulta por hora por equipo/sitio
    "devicePowerReportQuery": ("POST", "/hess/api/sample/energy"),
    "siteDayEnergyQuery": ("POST", "/hess/api/sample/energy/site/day"),
}
ONCE_PER_HOUR = {"devicePowerReportQuery", "siteDayEnergyQuery"}
# No están (a propósito): siteOwner (datos personales), userTokenQuery (devuelve tokens en claro),
# generateUserToken, todo sunspec/command/* y los cargadores EV (control).
LOGIN_PATH = "/hess/api/login"
_SAFE_ID = re.compile(r"[A-Za-z0-9._\-]{1,64}")

# --------------------------------------------------------------------------- #
# Política de comandos B.5 (la misma de todas las marcas)
# --------------------------------------------------------------------------- #
# Nivel 2 = aprobación explícita y específica; None = según el registro; 3 = prohibido siempre.
_EV = ("/hess/api/chargeSite/create", "/hess/api/chargeSite/querySite", "/hess/api/chargeSite/update",
       "/hess/api/chargeSite/disable", "/hess/api/chargeDevice/create", "/hess/api/chargeDevice/queryEv",
       "/hess/api/chargeDevice/disable", "/hess/api/chargeRecord", "/hess/api/chargeCommandDown",
       "/hess/api/chargeSchedule")
ORDER_LEVELS: dict[str, int | None] = {
    "/hess/api/sunspec/command/rebootInverter": 2,
    "/hess/api/sunspec/command/rebootBMS": 2,
    "/hess/api/sunspec/command/info": 2,        # lee, pero exige account+pwd: conservador
    "/hess/api/sunspec/command/send": None,     # según el registro (classify_register)
    "/hess/api/user/userToken": 3,              # regla del usuario: nunca
    **{p: 2 for p in _EV},
}
HARD_LEVEL3 = frozenset({42758, 42759})   # apagado/encendido remoto y parada de emergencia (defensa en profundidad)
UNVERIFIED_TABLE = frozenset({45005, 45006})   # tabla del PDF desalineada: no escribir sin confirmar con Livoltek
_SENSITIVE_KEYS = {"pwd", "password", "account", "key", "secuid", "userToken"}


def _load_register_levels() -> dict[int, int]:
    f = REF_DIR / "modbus-gen2.json"
    try:
        regs = json.loads(f.read_text(encoding="utf-8"))["holding_registers"]
        return {int(r["address"]): int(r["level"]) for r in regs if r.get("level") in (1, 2, 3)}
    except (OSError, KeyError, ValueError):
        return {}      # sin mapa no se puede escribir nada: falla en modo seguro


REGISTER_LEVELS: dict[int, int] = _load_register_levels()


def classify_register(reg: int) -> int | None:
    """3 = prohibido, 2 = red/protecciones (aprobación explícita), 1 = operativo, None = no escribible.

    Lista blanca: solo los 32 registros RW del PDF Modbus Gen 2 V1.01 (modbus-gen2.json). Reseteo de
    fábrica, seguridad y firmware no están documentados en esa versión; lo no documentado = None.
    """
    reg = int(reg)
    if reg in HARD_LEVEL3:
        return 3
    return REGISTER_LEVELS.get(reg)


# --------------------------------------------------------------------------- #
# Fechas y ventanas (se validan SIN red)
# --------------------------------------------------------------------------- #
def _tz(hours: float) -> dt.timezone:
    return dt.timezone(dt.timedelta(hours=hours))


def parse_day(s: str) -> dt.date:
    try:
        return dt.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise Refused(f"fecha inválida «{s}»: usa AAAA-MM-DD") from None


def day_start_ms(day: dt.date, tz: dt.timezone) -> int:
    return int(dt.datetime.combine(day, dt.time.min, tzinfo=tz).timestamp() * 1000)


def check_recent(start: dt.date, today: dt.date, days: int, what: str) -> None:
    oldest = today - dt.timedelta(days=days)
    if start < oldest:
        raise Refused(f"{what}: el inicio {start} queda fuera de los últimos {days} días (mínimo {oldest}); la doc lo exige y no se envía")


def check_years(start: dt.date, today: dt.date, years: int, what: str) -> None:
    try:
        oldest = today.replace(year=today.year - years)
    except ValueError:                   # 29-feb
        oldest = today.replace(year=today.year - years, day=28)
    if start < oldest:
        raise Refused(f"{what}: el inicio {start} queda fuera de los últimos {years} años (mínimo {oldest}); la doc lo exige y no se envía")


def split_days(start: dt.date, end: dt.date, max_days: int) -> list[tuple[dt.date, dt.date]]:
    """Parte [start, end] en tramos de ≤ max_days días (inclusive)."""
    if end < start:
        raise Refused(f"rango inválido: {start} > {end}")
    out, cur = [], start
    while cur <= end:
        last = min(end, cur + dt.timedelta(days=max_days - 1))
        out.append((cur, last))
        cur = last + dt.timedelta(days=1)
    return out


TIME_TYPE = {"day": 0, "week": 1, "month": 2, "year": 3}


# --------------------------------------------------------------------------- #
# Presupuesto horario persistente (entre ejecuciones del CLI)
# --------------------------------------------------------------------------- #
class Budget:
    """Cuenta las llamadas de la última hora. Guarda solo marcas de tiempo, nunca el token."""

    def __init__(self, path: Path | None):
        self.path = path
        self.events: list[list] = []          # [epoch_s, usa_userToken]
        if path and path.exists():
            try:
                self.events = [[float(a), bool(b)] for a, b in json.loads(path.read_text())]
            except (OSError, ValueError, TypeError):
                self.events = []

    def _purge(self, now: float) -> None:
        self.events = [e for e in self.events if now - e[0] < WINDOW_S]

    def check(self, uses_token: bool, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self._purge(now)
        total = len(self.events)
        tokened = sum(1 for e in self.events if e[1])
        for count, limit, what in ((total, LIMIT_PER_IP, "por IP o Security ID"),
                                   (tokened if uses_token else 0, LIMIT_PER_TOKEN, "por userToken")):
            if count >= limit and (what != "por userToken" or uses_token):
                oldest = min(e[0] for e in self.events if (e[1] or what != "por userToken"))
                wait = int(oldest + WINDOW_S - now) + 1
                raise BudgetExceeded(f"presupuesto horario agotado ({limit} llamadas/h {what}); vuelve a intentar en ~{wait // 60} min. No se llamó a la nube.")

    def record(self, uses_token: bool, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self.events.append([now, uses_token])
        self._purge(now)
        if self.path:
            try:
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps(self.events))
                os.replace(tmp, self.path)
            except OSError:
                pass


# --------------------------------------------------------------------------- #
# Normalización (esquema común entre marcas) — convenciones del Apéndice B.0
#   bat_power_w  : + = CARGA        grid_power_w : + = IMPORTACIÓN
# Lo que la doc no permite fijar queda en parámetros explícitos (no se adivina).
# --------------------------------------------------------------------------- #
GRID_DOWN_V = 20.0     # umbral heredado de Deye (H: sin verificar para Livoltek)


@dataclass
class Conventions:
    power_unit: str = "kW"              # la prosa de la doc dice W y las tablas kW (SIN VERIFICAR)
    energy_unit: str = "kWh"            # utilityEnergy dice Wh; el resto no da unidad (SIN VERIFICAR)
    bat_power_sign: int | None = 1      # H: el ejemplo de curPowerflow trae -0.156 con «disCharging»
    bat_current_sign: int | None = None  # sin ninguna pista en la doc -> None
    grid_power_sign: int | None = None   # el ejemplo de HisPowerflow se contradice -> None hasta validar

    @property
    def power_to_w(self) -> float:
        return {"kW": 1000.0, "W": 1.0}[self.power_unit]

    @property
    def energy_to_kwh(self) -> float:
        return {"kWh": 1.0, "Wh": 0.001}[self.energy_unit]


def _num(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _scaled(v, factor, sign=1):
    x = _num(v)
    if x is None or sign is None:
        return None
    r = x * factor * sign
    return 0.0 if r == 0 else r


def latest_sample(realtime_data) -> dict:
    """`realTime` agrupa por día: {ts_día: [muestras]}. Devuelve la muestra más reciente con claves en minúscula."""
    best, best_ts = {}, None
    for day_key in sorted(realtime_data or {}):
        for s in realtime_data[day_key] or []:
            low = {str(k).lower(): v for k, v in s.items()}
            ts = _num(low.get("timestamp"))
            if best_ts is None or (ts is not None and ts >= best_ts) or not best:
                best, best_ts = low, ts if ts is not None else best_ts
    return best


def normalize(flow: dict | None, sample: dict | None, basic: dict | None, totals: dict | None,
              conv: Conventions) -> dict:
    flow, sample, basic, totals = flow or {}, sample or {}, basic or {}, totals or {}
    kw, ek = conv.power_to_w, conv.energy_to_kwh
    volts = [_num(sample.get(k)) for k in ("rvoltage", "svoltage", "tvoltage")]
    present = [v for v in volts if v is not None]
    day = lambda k: _scaled(basic.get(k), ek)          # noqa: E731
    out = {
        "soc_pct": _num(flow.get("energySoc")) if _num(flow.get("energySoc")) is not None else _num(sample.get("batterysoc")),
        "bat_power_w": _scaled(flow.get("energyPower"), kw, conv.bat_power_sign),
        "bat_voltage_v": _num(sample.get("batteryvoltage")),
        "bat_current_a": _scaled(sample.get("batterycurrent"), 1.0, conv.bat_current_sign),
        "bat_temp_c": None,                              # sin campo en la API ni registro en el PDF
        "pv_power_w": _scaled(flow.get("pvPower"), kw),
        "load_power_w": _scaled(flow.get("loadPower"), kw),
        "grid_power_w": _scaled(flow.get("powerGridPower"), kw, conv.grid_power_sign),
        "grid_voltage_v": volts,
        "grid_freq_hz": _num(sample.get("girdfrequency")),
        "ac_out_freq_hz": _num(sample.get("epsfrequency")),
        "energy_day_kwh": {
            "pv": day("powerGenerationDay"), "load": day("loadDay"),
            "import": day("positiveDay"), "export": day("negativeDay"),
            "bat_charge": day("chargeDay"), "bat_discharge": day("dischargeDay"),
        },
        "energy_total_kwh": {
            "pv": _scaled(totals.get("pvProduceElectric"), ek), "load": _scaled(totals.get("loadCustomerElectric"), ek),
            "import": None, "export": None, "bat_charge": None, "bat_discharge": None,   # sin fuente en la API
        },
        "grid_up": (min(present) >= GRID_DOWN_V) if present else None,
    }
    unverified = ["unidades de potencia y energía supuestas (parámetros power_unit / energy_unit)",
                  "bat_power_w: + = carga es una hipótesis tomada del ejemplo de la doc",
                  "grid_voltage_v y grid_up: la doc no dice si rVoltage… es tensión de red o de salida del inversor",
                  "energy_day_kwh.export: negativeDay se toma como exportación por analogía"]
    if conv.grid_power_sign is None:
        unverified.append("grid_power_w = None: signo sin validar (use grid_power_sign=+1/-1 tras cruzar con Metrum)")
    if conv.bat_current_sign is None:
        unverified.append("bat_current_a = None: signo sin validar")
    return {**out, "state": basic.get("runningStatus"), "communication": basic.get("communicationStatus"),
            "collected_at": _num(sample.get("timestamp")) or _num(flow.get("timestamp")),
            "raw": {"flow": flow, "sample": sample, "basic": basic, "totals": totals},
            "conventions": conv.__dict__, "unverified": unverified}


# --------------------------------------------------------------------------- #
# Adaptador
# --------------------------------------------------------------------------- #
class LivoltekAdapter:
    def __init__(self, min_interval: float = 1.0, max_retries: int = 4, net_retries: int = 1,
                 max_calls: int = 60, tz_hours: float | None = None):
        self._api_raw = os.environ.get("LIVOLTEK_API_URL", "")     # se valida en la primera llamada de red
        self.min_interval, self.max_retries, self.net_retries = min_interval, max_retries, net_retries
        self.max_calls = max_calls
        self.tz = _tz(float(os.environ.get("LIVOLTEK_TZ_OFFSET", "-5")) if tz_hours is None else tz_hours)
        self._token: str | None = None
        self._last = 0.0
        self.calls = 0
        self._budget: Budget | None = None
        self._site_cache: dict[str, str] = {}
        self._once: dict[str, float] = {}
        cd = os.environ.get("LIVOLTEK_CACHE_DIR")
        self.cache_dir = Path(cd) if cd else None

    # -- construcción de la consulta ----------------------------------------
    def _base(self) -> str:
        if not self._api_raw:
            raise SystemExit("Falta la variable de entorno LIVOLTEK_API_URL")
        base = self._api_raw.strip().rstrip("/")
        if base.endswith(API_PREFIX):
            base = base[: -len(API_PREFIX)]
        sp = urllib.parse.urlsplit(base)
        local = sp.hostname in ("127.0.0.1", "localhost", "::1")
        if not sp.hostname or sp.scheme not in ("https", "http") or (sp.scheme == "http" and not local):
            raise RuntimeError("LIVOLTEK_API_URL debe ser una URL https con host (la API solo admite HTTPS)")
        return base

    @staticmethod
    def _fill(template: str, ids: dict) -> str:
        def sub(m: re.Match) -> str:
            val = str(ids.get(m.group(1), ""))
            if not _SAFE_ID.fullmatch(val):
                raise Refused(f"valor inválido para {{{m.group(1)}}}: solo letras, números, punto, guion y guion bajo (máx. 64)")
            return urllib.parse.quote(val, safe="")
        return re.sub(r"\{(\w+)\}", sub, template)

    def build_request(self, endpoint_id: str, ids: dict | None = None, query: dict | None = None,
                      *, mask: bool = True) -> tuple[str, str]:
        """(método, URL). Con mask=True los secretos salen como <VARIABLE>; no toca la red."""
        if endpoint_id not in READ:
            raise Refused(f"{endpoint_id}: no está en la lista de lectura del adaptador")
        method, tpl = READ[endpoint_id]
        path = self._fill(tpl, ids or {})
        params = dict(query or {})
        if mask:
            params = {"userToken": "<LIVOLTEK_USER_TOKEN>", "userType": "<LIVOLTEK_USER_TYPE>", **params}
        else:
            params = {"userToken": _env("LIVOLTEK_USER_TOKEN"), "userType": self._user_type(), **params}
        qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="<>" if mask else "")
        base = "<LIVOLTEK_API_URL>" if mask else self._base()
        return method, f"{base}{path}?{qs}"

    @staticmethod
    def _user_type() -> str:
        v = _env("LIVOLTEK_USER_TYPE")
        if v not in ("0", "1"):
            raise SystemExit("LIVOLTEK_USER_TYPE debe ser 0 (usuario final) o 1 (agente/instalador)")
        return v

    # -- HTTP ---------------------------------------------------------------
    def _budget_obj(self) -> Budget:
        if self._budget is None:
            f = os.environ.get("LIVOLTEK_BUDGET_FILE")
            if f:
                path = Path(f)
            else:
                tag = hashlib.sha256((os.environ.get("LIVOLTEK_USER_TOKEN", "") + self._api_raw).encode()).hexdigest()[:8]
                path = Path(tempfile.gettempdir()) / f"om-agency-livoltek-budget-{tag}.json"
            self._budget = Budget(path)
        return self._budget

    def _http(self, method: str, url: str, *, body: dict | None, label: str, auth: bool, uses_token: bool):
        headers = {"Content-Type": "application/json", "User-Agent": UA, "Accept": "application/json"}
        if auth:
            headers["Authorization"] = self._token or ""
        data = json.dumps(body if body is not None else {}).encode() if method == "POST" else None
        relogged = False
        net_fail = 0
        for attempt in range(self.max_retries + 1):
            if self.calls >= self.max_calls:
                raise RuntimeError(f"tope de llamadas de esta ejecución alcanzado ({self.max_calls}); no se llamó a la nube")
            self._budget_obj().check(uses_token)
            time.sleep(max(0.0, self.min_interval - (time.time() - self._last)))
            self._last = time.time()
            self.calls += 1
            self._budget_obj().record(uses_token)
            req = urllib.request.Request(url, data=data, headers=headers if not auth else {**headers, "Authorization": self._token or ""}, method=method)
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                snippet = redact(e.read().decode("utf-8", "replace")[:300])
                if e.code == 428:
                    raise TokenOccupied("HTTP 428 «token occupied»: el userToken ya se usa desde 3 IP o Security ID distintos y esta no es una de ellas. "
                                        "No se reintenta: libera un cupo en el portal o genera otro token.") from None
                if e.code == 401 and auth and not relogged and label != "login":
                    relogged = True
                    self.login()
                    headers["Authorization"] = self._token or ""
                    continue
                if e.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(2 ** (attempt + 1))                   # 2, 4, 8, 16 s
                    continue
                if e.code == 429:
                    raise RuntimeError(f"HTTP 429 en {label}: demasiadas peticiones (reintentos agotados). {snippet}") from None
                raise RuntimeError(f"HTTP {e.code} en {label}: {snippet}") from None
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                net_fail += 1
                if net_fail <= self.net_retries and attempt < self.max_retries:
                    time.sleep(2 ** net_fail)
                    continue
                reason = getattr(e, "reason", e)
                raise RuntimeError(f"Red en {label}: {redact(reason)}") from None
            try:
                return json.loads(raw)
            except ValueError:
                raise RuntimeError(f"{label}: la respuesta no es JSON: {redact(raw[:200])}") from None
        raise RuntimeError(f"{label}: sin respuesta tras reintentos")

    @staticmethod
    def _check_ok(res: dict, label: str) -> dict:
        code = str(res.get("code", ""))
        if code not in ("200", "201", "operate.success"):
            raise RuntimeError(f"{label}: code={redact(code)} message={redact(res.get('message'))}")
        return res

    def login(self) -> None:
        base = self._base()
        body = {"secuid": _env("LIVOLTEK_SECUID"), "key": _env("LIVOLTEK_KEY")}
        res = self._http("POST", f"{base}{LOGIN_PATH}", body=body, label="login", auth=False, uses_token=False)
        self._check_ok(res, "login")
        tok = ((res.get("data") or {}).get("data"))
        if not tok or not isinstance(tok, str):
            raise RuntimeError(f"login: sin token en la respuesta (message={redact(res.get('message'))})")
        self._token = tok
        _RUNTIME_SECRETS.add(tok)

    def read(self, endpoint_id: str, ids: dict | None = None, query: dict | None = None,
             body: dict | None = None, *, cache: bool = False):
        """Lectura de un endpoint de la lista blanca. Devuelve `data` ya desenvuelto."""
        if endpoint_id not in READ:
            raise Refused(f"{endpoint_id}: no está en la lista de lectura del adaptador")
        if endpoint_id in ONCE_PER_HOUR:
            key = f"{endpoint_id}:{json.dumps(ids or {}, sort_keys=True)}:{json.dumps(body, sort_keys=True)}"
            if time.time() - self._once.get(key, 0.0) < WINDOW_S:
                raise Refused(f"{endpoint_id}: la doc permite una consulta por hora por equipo/sitio y ya se hizo en esta ejecución")
        ckey = None
        if cache and self.cache_dir:
            ident = json.dumps([endpoint_id, ids, query, body], sort_keys=True, default=str)
            ckey = self.cache_dir / f"{hashlib.sha256(ident.encode()).hexdigest()[:24]}.json"
            if ckey.exists():
                return json.loads(ckey.read_text(encoding="utf-8"))
        if self._token is None:
            self.login()
        method, url = self.build_request(endpoint_id, ids, query, mask=False)
        res = self._http(method, url, body=body, label=endpoint_id, auth=True, uses_token=True)
        self._check_ok(res, endpoint_id)
        if endpoint_id in ONCE_PER_HOUR:
            self._once[f"{endpoint_id}:{json.dumps(ids or {}, sort_keys=True)}:{json.dumps(body, sort_keys=True)}"] = time.time()
        data = res.get("data")
        if ckey is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            ckey.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    # -- lectura ------------------------------------------------------------
    def today(self) -> dt.date:
        return dt.datetime.now(self.tz).date()

    def _paged(self, endpoint_id, ids, query, first_page: int = 1, size: int = PAGE_SIZE):
        """Lista paginada {list, count}. Si falta contenido (índice base 0 vs 1 de la doc), pide también la página anterior."""
        out, page, count = [], first_page, None
        while True:
            d = self.read(endpoint_id, ids, {**query, "page": page, "size": size}) or {}
            batch = d.get("list") or []
            count = d.get("count", count)
            out += batch
            if not batch or (count is not None and len(out) >= int(count)) or len(batch) < size:
                break
            page += 1
        if count is not None and len(out) < int(count) and first_page >= 1:
            prev = self.read(endpoint_id, ids, {**query, "page": first_page - 1, "size": size}) or {}
            known = {json.dumps(x, sort_keys=True) for x in out}
            out += [x for x in (prev.get("list") or []) if json.dumps(x, sort_keys=True) not in known]
        return out

    def list_sites(self) -> list[dict]:
        return self._paged("siteList", {}, {})

    def site_of(self, sn: str) -> str:
        if sn not in self._site_cache:
            d = self.read("queryPowerStationId", {"serialNumber": sn})
            sid = (d or {}).get("powerStationId")
            if not sid:
                raise RuntimeError(f"{sn}: la API no devolvió powerStationId")
            self._site_cache[sn] = str(sid)
        return self._site_cache[sn]

    def list_devices(self, site_id: str) -> list[dict]:
        return self._paged("deviceList", {"siteId": site_id}, {})

    def basic_data(self, sn: str) -> dict | None:
        d = self.read("deviceBasicData", {}, {"sn": sn, "page": 1, "size": PAGE_SIZE})
        rows = d if isinstance(d, list) else (d or {}).get("list") or []
        return next((r for r in rows if str(r.get("sn", "")).lower() == sn.lower()), rows[0] if rows else None)

    def realtime(self, sn: str, start: str | None = None, end: str | None = None, site_id: str | None = None) -> dict:
        """Muestras de 5 min. La ventana por defecto es ayer 00:00 → mañana 00:00 locales (la zona de las cadenas es
        indocumentada: la ventana ancha evita perder la última muestra). La doc limita a los últimos 7 días."""
        site_id = site_id or self.site_of(sn)
        today = self.today()
        s = start or f"{today - dt.timedelta(days=1)} 00:00:00"
        e = end or f"{today + dt.timedelta(days=1)} 00:00:00"
        try:
            s_day = dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").date()
            dt.datetime.strptime(e, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise Refused('formato inválido: usa "AAAA-MM-DD HH:MM:SS"') from None
        check_recent(s_day, today, RECENT_DAYS, "realTime")
        return self.read("deviceTechnical", {"siteId": site_id, "serialNumber": sn}, {"startTime": s, "endTime": e}) or {}

    def latest(self, sn: str) -> dict:
        """Respuestas crudas: flujo del sitio, última muestra técnica y datos básicos del equipo."""
        site_id = self.site_of(sn)
        flow = self.read("currentPowerFlow", {"siteId": site_id})
        rt = self.realtime(sn, site_id=site_id)
        return {"sn": sn, "site_id": site_id, "flow": flow, "sample": latest_sample(rt),
                "samples_in_window": sum(len(v or []) for v in rt.values()), "basic": self.basic_data(sn)}

    def normalized(self, sn: str, conv: Conventions | None = None) -> dict:
        raw = self.latest(sn)
        totals = None
        dev_id = (raw["basic"] or {}).get("id")
        if dev_id is not None:
            totals = self.read("deviceGenerationOrConsumption", {"deviceId": str(dev_id)})
        return {"sn": sn, "site_id": raw["site_id"],
                **normalize(raw["flow"], raw["sample"], raw["basic"], totals, conv or Conventions())}

    def history(self, site_id: str, start: dt.date, end: dt.date, point_interval: int = 0,
                chunk_days: int = 1) -> list[dict]:
        """Flujo de potencia del sitio (HisPowerflow), un tramo por día. El inicio debe estar en los últimos 7 días."""
        check_recent(start, self.today(), RECENT_DAYS, "HisPowerflow")
        frames: list[dict] = []
        for a, b in split_days(start, end, chunk_days):
            d = self.read("siteHistoricalPowerFlow", {"siteId": site_id}, {
                "pointInterval": point_interval, "startTime": day_start_ms(a, self.tz),
                "endTime": day_start_ms(b + dt.timedelta(days=1), self.tz) - 1}, cache=b < self.today())
            for rows in (d or {}).values():
                frames += rows or []
        return sorted(frames, key=lambda f: _num(f.get("timestamp")) or 0)

    def energy(self, site_id: str, start: dt.date, end: dt.date, unit: str, only: str | None = None) -> dict:
        """Energía por periodo (utilityEnergy: importación/exportación; solarEnergy: generación)."""
        if unit not in TIME_TYPE:
            raise Refused("unidad inválida: day, week, month o year")
        today = self.today()
        if unit in ("day", "week"):
            check_years(start, today, RECENT_YEARS, "energía")
        span = {"day": MAX_SPAN_DAY, "week": MAX_SPAN_WEEK}.get(unit, 366)
        out: dict = {"grid": [], "solar": []}
        for a, b in split_days(start, end, span):
            q = {"timeType": TIME_TYPE[unit], "startTime": a.strftime("%Y%m%d"), "endTime": b.strftime("%Y%m%d")}
            for key, ep in (("grid", "siteHistoricalGrid"), ("solar", "siteHistoricalSolar")):
                if only and only != key:
                    continue
                page = 1
                while True:
                    d = self.read(ep, {"siteId": site_id}, {**q, "page": page, "size": PAGE_SIZE}, cache=b < today)
                    rows = (d.get("historyList") if isinstance(d, dict) else d) or []
                    out[key] += rows
                    if len(rows) < PAGE_SIZE:
                        break
                    page += 1
        return {k: v for k, v in out.items() if not only or k == only}

    def alerts(self, sn: str, start: dt.date | None = None, end: dt.date | None = None) -> list[dict]:
        """Alarmas del equipo. La doc las limita a los últimos 7 días (fechas AAAA-MM-DD)."""
        today = self.today()
        start = start or today - dt.timedelta(days=RECENT_DAYS - 1)
        end = end or today
        check_recent(start, today, RECENT_DAYS, "alarm")
        site_id = self.site_of(sn)
        return self._paged("deviceHistoricalAlarm", {"siteId": site_id, "serialNumber": sn},
                           {"startTime": start.isoformat(), "endTime": end.isoformat()})

    def storage(self, site_id: str) -> dict:
        return self.read("storageInformation", {"siteId": site_id}) or {}

    def config(self, sn: str) -> dict:
        """Configuración que la API pública SÍ expone: datos del equipo, del sitio y de la batería.
        Los parámetros operativos (TOU, límites) solo salen por sunspec/command/info (control: exige account+pwd,
        regla del usuario: no se ejecuta) o por Modbus función 03 con acceso local."""
        site_id = self.site_of(sn)
        ess = self.storage(site_id)
        return {"device": self.read("deviceDetails", {"siteId": site_id, "serialNumber": sn}),
                "site": self.read("siteDetails", {"siteId": site_id}),
                "battery": {k: v for k, v in ess.items() if k != "historyMap"},
                "not_available_via_api": "parámetros operativos (TOU, límites de exportación): solo sunspec/command/info o Modbus"}

    # -- escritura (ensayo; NUNCA contacta la red) --------------------------------
    def write_order(self, sn: str, path: str, body: dict, *, confirmed_by: str,
                    approval_ref: str | None = None, registers: list[int] | None = None,
                    execute: bool = False) -> dict:
        """Ensaya una orden de control aplicando la política de 4 niveles (SKILL.md B.5). No usa la red.

        - `confirmed_by`: quién confirmó SN + acción + valor (obligatorio).
        - `approval_ref`: aprobación explícita y específica (obligatoria en nivel 2).
        - `registers`: registros Modbus que tocará `sunspec/command/send`; se completan con el `address`
          de cada punto de `body['points']` (deben ser enteros).
        - `execute=True` se rechaza: los endpoints de control exigen account+pwd (no están en el entorno)
          y no están probados contra la API real.
        """
        if path not in ORDER_LEVELS:
            raise Refused(f"{path}: fuera de la política (solo órdenes de control documentadas)")
        level = ORDER_LEVELS[path]
        if level == 3:
            raise Refused(f"{path}: NIVEL 3 PROHIBIDO (regla del usuario: nunca se ejecuta desde el skill)")
        if not _SAFE_ID.fullmatch(str(sn or "")):
            raise Refused("SN inválido")
        regs = [int(r) for r in (registers or [])]
        if path.endswith("/sunspec/command/send"):
            for p in (body or {}).get("points") or []:
                try:
                    regs.append(int(str(p.get("address", "")).strip()))
                except (ValueError, AttributeError):
                    raise Refused(f"punto sin dirección Modbus entera ({redact(p.get('uiName') if isinstance(p, dict) else p)}): no se envía") from None
            if not regs:
                raise Refused("sunspec/command/send: declara los registros que tocará (points[].address o registers=[...])")
            level = 1
        for r in sorted(set(regs)):
            lv = classify_register(r)
            if lv == 3:
                raise Refused(f"registro {r}: NIVEL 3 PROHIBIDO (apagado remoto, parada de emergencia, fábrica, seguridad o firmware)")
            if lv is None:
                raise Refused(f"registro {r}: no está en la lista blanca de 32 registros RW del PDF V1.01 (no documentado = no se escribe)")
            if r in UNVERIFIED_TABLE:
                raise Refused(f"registro {r}: la tabla del PDF está desalineada en 45005/45006; no se escribe sin confirmar con Livoltek")
            level = max(level, lv)
        if not confirmed_by:
            raise Refused("falta confirmed_by (confirmación explícita de SN + acción + valor)")
        if level >= 2 and not approval_ref:
            raise Refused("nivel 2: falta approval_ref (aprobación explícita y específica)")
        if execute:
            raise Refused("escritura real no implementada: exige account+pwd de la cuenta (no están en el entorno) y la API de control no está probada")
        safe_body = {k: ("<redactado>" if k in _SENSITIVE_KEYS else v) for k, v in (body or {}).items()}
        would = {"method": "POST", "path": path, "query": {"userType": "<LIVOLTEK_USER_TYPE>", "userToken": "<LIVOLTEK_USER_TOKEN>"},
                 "body": {**safe_body, "sn": sn}}
        self._audit({"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "sn": sn, "path": path, "level": level,
                     "registers": sorted(set(regs)), "confirmed_by": confirmed_by, "approval_ref": approval_ref,
                     "mode": "dry-run", "would_send": would})
        return {"dry_run": True, "level": level, "calls": self.calls, "would_send": would}

    @staticmethod
    def _audit(rec: dict) -> None:
        log = os.environ.get("LIVOLTEK_AUDIT_LOG")
        if log:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(redact(json.dumps(rec, ensure_ascii=False)) + "\n")


# --------------------------------------------------------------------------- #
# CLI (solo lectura)
# --------------------------------------------------------------------------- #
def _print(obj) -> None:
    print(redact(json.dumps(obj, ensure_ascii=False, indent=2)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--tz-offset", type=float, default=None, help="huso horario local en horas (Colombia = -5)")
    ap.add_argument("--max-calls", type=int, default=60, help="tope de llamadas de esta ejecución (por defecto 60)")
    ap.add_argument("--power-unit", choices=("kW", "W"), default="kW", help="unidad de las potencias de la API (sin verificar)")
    ap.add_argument("--energy-unit", choices=("kWh", "Wh"), default="kWh", help="unidad de las energías de la API (sin verificar)")
    ap.add_argument("--bat-power-sign", choices=("+1", "-1", "none"), default="+1", help="+1 = el valor de la API ya es + = carga")
    ap.add_argument("--bat-current-sign", choices=("+1", "-1", "none"), default="none")
    ap.add_argument("--grid-sign", choices=("+1", "-1", "none"), default="none", help="+1 = el valor de la API ya es + = importación")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sites")
    for name in ("site-of", "latest", "normalized"):
        sub.add_parser(name).add_argument("sn")
    sub.add_parser("devices").add_argument("site_id")
    p = sub.add_parser("realtime"); p.add_argument("sn"); p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--last", type=int, default=12)
    p = sub.add_parser("ess"); p.add_argument("site_id"); p.add_argument("--history", action="store_true")
    p = sub.add_parser("alarms"); p.add_argument("sn"); p.add_argument("start", nargs="?"); p.add_argument("end", nargs="?")
    p = sub.add_parser("powerflow"); p.add_argument("site_id"); p.add_argument("start"); p.add_argument("end"); p.add_argument("--interval", type=int, default=0, choices=(0, 1, 2))
    p = sub.add_parser("energy"); p.add_argument("site_id"); p.add_argument("start"); p.add_argument("end"); p.add_argument("unit", choices=tuple(TIME_TYPE)); p.add_argument("--only", choices=("grid", "solar"))
    p = sub.add_parser("url"); p.add_argument("endpoint_id", choices=sorted(READ)); p.add_argument("--site-id"); p.add_argument("--sn"); p.add_argument("--device-id")
    a = ap.parse_args()

    sign = lambda s: None if s == "none" else int(s)       # noqa: E731
    conv = Conventions(a.power_unit, a.energy_unit, sign(a.bat_power_sign), sign(a.bat_current_sign), sign(a.grid_sign))
    d = LivoltekAdapter(max_calls=a.max_calls, tz_hours=a.tz_offset)

    if a.cmd == "url":                                           # sin red
        ids = {k: v for k, v in (("siteId", a.site_id), ("serialNumber", a.sn), ("deviceId", a.device_id)) if v}
        method, url = d.build_request(a.endpoint_id, ids, mask=True)
        real_ok = True
        try:
            d.build_request(a.endpoint_id, ids, mask=False)      # construye la real en memoria; no se imprime
        except (SystemExit, RuntimeError) as exc:
            real_ok = False
            url += f"   [no se pudo construir con el entorno: {redact(exc)}]"
        _print({"endpoint": a.endpoint_id, "method": method, "url": url, "construida_con_el_entorno": real_ok,
                "entorno": check_env(), "red": "no se usó"})
        return 0
    if a.cmd == "sites":
        out = d.list_sites()
    elif a.cmd == "site-of":
        out = {"sn": a.sn, "site_id": d.site_of(a.sn)}
    elif a.cmd == "devices":
        out = d.list_devices(a.site_id)
    elif a.cmd == "latest":
        out = d.latest(a.sn)
    elif a.cmd == "normalized":
        out = d.normalized(a.sn, conv)
    elif a.cmd == "realtime":
        rt = d.realtime(a.sn, a.start, a.end)
        rows = [s for k in sorted(rt) for s in (rt[k] or [])]
        out = {"sn": a.sn, "n_samples": len(rows), "last": rows[-a.last:] if a.last else []}
    elif a.cmd == "ess":
        ess = d.storage(a.site_id)
        out = ess if a.history else {**{k: v for k, v in ess.items() if k != "historyMap"},
                                     "historyMap_days": len(ess.get("historyMap") or {})}
    elif a.cmd == "alarms":
        out = d.alerts(a.sn, parse_day(a.start) if a.start else None, parse_day(a.end) if a.end else None)
    elif a.cmd == "powerflow":
        out = d.history(a.site_id, parse_day(a.start), parse_day(a.end), a.interval)
    else:  # energy
        out = d.energy(a.site_id, parse_day(a.start), parse_day(a.end), a.unit, a.only)
    _print(out)
    print(f"[llamadas a la API en esta ejecución: {d.calls}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refused as exc:
        print(f"RECHAZADO: {redact(exc)}", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:  # noqa: BLE001 - CLI: mensaje claro en vez de traceback
        print(f"ERROR: {redact(exc)}", file=sys.stderr)
        sys.exit(2)
