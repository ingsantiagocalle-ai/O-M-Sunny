#!/usr/bin/env python3
"""Pruebas SIN credenciales reales y SIN internet del adaptador Livoltek.

  python3 scripts/test_livoltek_adapter.py -v

- Política B.5: se ejecuta con `LIVOLTEK_API_URL` inválida y con `urllib.request.urlopen` bloqueado
  (cualquier intento de red falla la prueba); además se comprueba `calls == 0`.
- Comportamiento HTTP (login, 429, 428, 401, presupuesto): contra un servidor local falso en 127.0.0.1.
- Todas las credenciales de estas pruebas son inventadas; no se lee ninguna variable real.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import livoltek_adapter as la  # noqa: E402

FAKE = {"LIVOLTEK_SECUID": "SECUID-FAKE-1234", "LIVOLTEK_KEY": "KEY-FAKE-5678",
        "LIVOLTEK_USER_TOKEN": "UTOKEN-FAKE-9012", "LIVOLTEK_USER_TYPE": "1"}
REF = la.REF_DIR


def no_network(*a, **k):
    raise AssertionError("se intentó usar la red")


class PolicyOffline(unittest.TestCase):
    """B.5 sin red: API inválida + urlopen bloqueado."""

    def setUp(self):
        self.env = mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": "esto-no-es-una-url"})
        self.env.start()
        self.net = mock.patch.object(urllib.request, "urlopen", no_network)
        self.net.start()
        self.a = la.LivoltekAdapter(min_interval=0)

    def tearDown(self):
        self.net.stop()
        self.env.stop()

    REBOOT = "/hess/api/sunspec/command/rebootInverter"
    SEND = "/hess/api/sunspec/command/send"

    def test_nivel3_user_token_rechazado(self):
        with self.assertRaises(la.Refused):
            self.a.write_order("SN1", "/hess/api/user/userToken", {}, confirmed_by="ana", approval_ref="X")
        self.assertEqual(self.a.calls, 0)

    def test_nivel3_registros_rechazados_aun_confirmados(self):
        for reg in (42758, 42759):
            with self.assertRaises(la.Refused):
                self.a.write_order("SN1", self.SEND, {"points": [{"address": str(reg), "value": "1"}]},
                                   confirmed_by="ana", approval_ref="OK-1")
        self.assertEqual(self.a.calls, 0)

    def test_nivel2_sin_confirmar_rechazado(self):
        with self.assertRaises(la.Refused):
            self.a.write_order("SN1", self.REBOOT, {}, confirmed_by="")
        with self.assertRaises(la.Refused):          # confirmado pero sin aprobación nombrada
            self.a.write_order("SN1", self.REBOOT, {}, confirmed_by="ana")
        self.assertEqual(self.a.calls, 0)

    def test_nivel2_confirmado_es_dry_run(self):
        r = self.a.write_order("SN1", self.REBOOT, {"account": "x", "pwd": "y"}, confirmed_by="ana", approval_ref="OK-1")
        self.assertTrue(r["dry_run"])
        self.assertEqual(r["level"], 2)
        self.assertEqual(r["calls"], 0)
        self.assertEqual(self.a.calls, 0)
        self.assertEqual(r["would_send"]["body"]["pwd"], "<redactado>")        # nunca eco de credenciales
        self.assertEqual(r["would_send"]["body"]["account"], "<redactado>")

    def test_ev_es_nivel2(self):
        for p in ("/hess/api/chargeCommandDown", "/hess/api/chargeSchedule", "/hess/api/chargeSite/create",
                  "/hess/api/chargeDevice/queryEv"):
            r = self.a.write_order("SN1", p, {}, confirmed_by="ana", approval_ref="OK-1")
            self.assertEqual(r["level"], 2, p)

    def test_send_segun_el_registro(self):
        r = self.a.write_order("SN1", self.SEND, {"points": [{"address": "42752", "value": "2026"}]}, confirmed_by="ana")
        self.assertEqual(r["level"], 1)                                          # reloj: nivel 1, sin approval_ref
        with self.assertRaises(la.Refused):                                      # 43720 es nivel 2: exige aprobación
            self.a.write_order("SN1", self.SEND, {"points": [{"address": "43720", "value": "100"}]}, confirmed_by="ana")
        r = self.a.write_order("SN1", self.SEND, {"points": [{"address": "43720", "value": "100"}]}, confirmed_by="ana", approval_ref="OK-2")
        self.assertEqual(r["level"], 2)

    def test_send_sin_registros_o_no_documentado_rechazado(self):
        with self.assertRaises(la.Refused):
            self.a.write_order("SN1", self.SEND, {"points": []}, confirmed_by="ana", approval_ref="OK")
        for addr in ("45093", "45018", "XXXXX", "0"):        # ejemplos de la doc: fuera de la lista blanca
            with self.assertRaises(la.Refused, msg=addr):
                self.a.write_order("SN1", self.SEND, {"points": [{"address": addr, "value": "1"}]}, confirmed_by="ana", approval_ref="OK")
        for reg in (45005, 45006):                           # tabla del PDF desalineada
            with self.assertRaises(la.Refused, msg=str(reg)):
                self.a.write_order("SN1", self.SEND, {"points": [{"address": str(reg), "value": "1"}]}, confirmed_by="ana", approval_ref="OK")
        self.assertEqual(self.a.calls, 0)

    def test_execute_y_rutas_desconocidas_rechazadas(self):
        with self.assertRaises(la.Refused):
            self.a.write_order("SN1", self.REBOOT, {}, confirmed_by="ana", approval_ref="OK", execute=True)
        with self.assertRaises(la.Refused):
            self.a.write_order("SN1", "/hess/api/lo/que/sea", {}, confirmed_by="ana", approval_ref="OK")
        with self.assertRaises(la.Refused):
            self.a.write_order("SN 1;DROP", self.REBOOT, {}, confirmed_by="ana", approval_ref="OK")
        self.assertEqual(self.a.calls, 0)

    def test_read_rechaza_lo_que_no_es_lectura(self):
        for ep in ("sunspecRebootInverter", "chargingScheduleSettings", "generateUserToken", "userTokenQuery", "siteOwner"):
            with self.assertRaises(la.Refused, msg=ep):
                self.a.read(ep, {})
        self.assertEqual(self.a.calls, 0)

    def test_classify_register(self):
        self.assertEqual(la.classify_register(42758), 3)
        self.assertEqual(la.classify_register(42759), 3)
        self.assertEqual(la.classify_register(42762), 2)
        self.assertEqual(la.classify_register(42752), 1)
        self.assertIsNone(la.classify_register(42506))     # registro de solo lectura
        self.assertIsNone(la.classify_register(99999))
        levels = la.REGISTER_LEVELS
        self.assertEqual(len(levels), 32)                  # lista blanca = los 32 RW del PDF V1.01


class Catalog(unittest.TestCase):
    """La lista blanca del adaptador debe coincidir con el catálogo generado desde la doc."""

    def test_read_coincide_con_endpoints_json(self):
        eps = {e["id"]: e for e in json.loads((REF / "endpoints.json").read_text(encoding="utf-8"))["endpoints"]}
        for ep_id, (method, path) in la.READ.items():
            self.assertIn(ep_id, eps, ep_id)
            e = eps[ep_id]
            self.assertEqual((e["method"], e["path"]), (method, path), ep_id)
            self.assertEqual(e["kind"], "lectura", ep_id)
            self.assertFalse(e["sensible"], ep_id)
            self.assertFalse(e["solo_manual"], ep_id)
            self.assertFalse(e["requires_account_pwd"], ep_id)

    def test_control_del_catalogo_esta_en_la_politica(self):
        eps = json.loads((REF / "endpoints.json").read_text(encoding="utf-8"))["endpoints"]
        for e in eps:
            if e["kind"] == "control" and e["path"]:
                self.assertIn(e["path"], la.ORDER_LEVELS, e["id"])
        for e in eps:
            if e["kind"] == "sin_clasificar":
                self.fail(f"endpoint sin clasificar: {e['id']}")

    def test_modbus_json_coincide_con_clasificacion(self):
        raw = json.loads((REF / "modbus-gen2.json").read_text(encoding="utf-8"))["holding_registers"]
        self.assertEqual({int(r["address"]) for r in raw}, set(la.REGISTER_LEVELS))


class Ventanas(unittest.TestCase):
    def test_recent_y_years(self):
        today = dt.date(2026, 10, 5)
        la.check_recent(dt.date(2026, 9, 28), today, 7, "t")            # 7 días atrás: ok
        with self.assertRaises(la.Refused):
            la.check_recent(dt.date(2026, 9, 27), today, 7, "t")
        la.check_years(dt.date(2024, 10, 5), today, 2, "t")
        with self.assertRaises(la.Refused):
            la.check_years(dt.date(2024, 10, 4), today, 2, "t")

    def test_split_days(self):
        parts = la.split_days(dt.date(2026, 1, 1), dt.date(2026, 3, 1), 31)
        self.assertEqual(parts[0], (dt.date(2026, 1, 1), dt.date(2026, 1, 31)))
        self.assertEqual(parts[-1][1], dt.date(2026, 3, 1))
        self.assertTrue(all((b - a).days + 1 <= 31 for a, b in parts))
        with self.assertRaises(la.Refused):
            la.split_days(dt.date(2026, 2, 1), dt.date(2026, 1, 1), 31)

    def test_ventana_rechaza_sin_red(self):
        with mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": "https://invalida.invalid"}), \
             mock.patch.object(urllib.request, "urlopen", no_network):
            a = la.LivoltekAdapter(min_interval=0)
            old = a.today() - dt.timedelta(days=30)
            with self.assertRaises(la.Refused):
                a.history("1", old, old)
            with self.assertRaises(la.Refused):
                a.energy("1", a.today() - dt.timedelta(days=900), a.today(), "day")
            with self.assertRaises(la.Refused):
                a.realtime("SN1", start=f"{old} 00:00:00", site_id="1")
            self.assertEqual(a.calls, 0)


class Normalizacion(unittest.TestCase):
    FLOW = {"energyStatus": "disCharging", "energyPower": -0.156, "energySoc": 100.0, "pvPower": 0.006,
            "powerGridPower": 0.0, "loadPower": 0.0, "timestamp": 1655789700000}
    SAMPLE = {"rVoltage": "231.5", "sVoltage": None, "tVoltage": None, "girdFrequency": "60.0",
              "batteryVoltage": "52.1", "batteryCurrent": "3.0", "batterySoc": "99", "epsFrequency": "60.0", "timestamp": 10}
    BASIC = {"id": "8", "powerGenerationDay": "12", "loadDay": "15", "positiveDay": "50", "negativeDay": "51",
             "chargeDay": "52", "dischargeDay": "53", "runningStatus": "Offline", "communicationStatus": "offline"}

    def run_norm(self, conv=None):
        sample = la.latest_sample({"1": [self.SAMPLE]})
        return la.normalize(self.FLOW, sample, self.BASIC, {"pvProduceElectric": "137.5", "loadCustomerElectric": "3.1"}, conv or la.Conventions())

    def test_unidades_y_signos_por_defecto(self):
        n = self.run_norm()
        self.assertAlmostEqual(n["bat_power_w"], -156.0)       # kW -> W, + = carga (hipótesis): descarga = negativo
        self.assertAlmostEqual(n["pv_power_w"], 6.0)
        self.assertEqual(n["soc_pct"], 100.0)
        self.assertIsNone(n["grid_power_w"])                   # signo sin validar: no se adivina
        self.assertIsNone(n["bat_current_a"])
        self.assertIsNone(n["bat_temp_c"])
        self.assertEqual(n["grid_voltage_v"], [231.5, None, None])
        self.assertTrue(n["grid_up"])
        self.assertEqual(n["energy_day_kwh"]["pv"], 12.0)
        self.assertEqual(n["energy_day_kwh"]["import"], 50.0)
        self.assertEqual(n["energy_total_kwh"]["pv"], 137.5)
        self.assertTrue(any("grid_power_w" in u for u in n["unverified"]))

    def test_convenciones_explicitas(self):
        n = self.run_norm(la.Conventions(power_unit="W", energy_unit="Wh", bat_power_sign=-1, grid_power_sign=1, bat_current_sign=-1))
        self.assertAlmostEqual(n["bat_power_w"], 0.156)
        self.assertEqual(n["grid_power_w"], 0.0)
        self.assertAlmostEqual(n["bat_current_a"], -3.0)
        self.assertAlmostEqual(n["energy_day_kwh"]["pv"], 0.012)

    def test_grid_up(self):
        down = la.normalize({}, {"rvoltage": "0", "svoltage": "0", "tvoltage": "0"}, {}, {}, la.Conventions())
        self.assertFalse(down["grid_up"])
        none = la.normalize({}, {}, {}, {}, la.Conventions())
        self.assertIsNone(none["grid_up"])                     # sin dato nunca es True

    def test_latest_sample_toma_la_mas_reciente(self):
        data = {"1": [{"timestamp": 5, "batterySoc": "1"}, {"timestamp": 9, "batterySoc": "2"}], "2": [{"timestamp": 7, "batterySoc": "3"}]}
        self.assertEqual(la.latest_sample(data)["batterysoc"], "2")


class Redaccion(unittest.TestCase):
    def test_redact(self):
        with mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": "https://api.ejemplo.test:8081"}):
            la._RUNTIME_SECRETS.add("TOKEN-DEL-LOGIN-XYZ")
            try:
                txt = ("GET https://api.ejemplo.test:8081/x?userToken=OTRO-VALOR&a=1 SECUID-FAKE-1234 KEY-FAKE-5678 "
                       'UTOKEN-FAKE-9012 TOKEN-DEL-LOGIN-XYZ {"pwd":"abc","key":"zzzz"} eyJabcdefghijklmnopqrstuvwxyz0123')
                out = la.redact(txt)
            finally:
                la._RUNTIME_SECRETS.discard("TOKEN-DEL-LOGIN-XYZ")
        for secret in ("SECUID-FAKE-1234", "KEY-FAKE-5678", "UTOKEN-FAKE-9012", "TOKEN-DEL-LOGIN-XYZ", "OTRO-VALOR",
                       "api.ejemplo.test", "eyJabcdef", '"abc"', '"zzzz"'):
            self.assertNotIn(secret, out)

    def test_build_request_enmascarado(self):
        with mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": "https://api.ejemplo.test:8081"}):
            a = la.LivoltekAdapter(min_interval=0)
            m, url = a.build_request("deviceDetails", {"siteId": "527", "serialNumber": "SN123456"})
            self.assertEqual(m, "GET")
            self.assertEqual(url, "<LIVOLTEK_API_URL>/hess/api/device/527/SN123456/details?userToken=<LIVOLTEK_USER_TOKEN>&userType=<LIVOLTEK_USER_TYPE>")
            real = a.build_request("deviceDetails", {"siteId": "527", "serialNumber": "SN123456"}, mask=False)[1]
            self.assertEqual(real, "https://api.ejemplo.test:8081/hess/api/device/527/SN123456/details?userToken=UTOKEN-FAKE-9012&userType=1")
            with self.assertRaises(la.Refused):
                a.build_request("deviceDetails", {"siteId": "../x", "serialNumber": "SN1"})

    def test_base_con_prefijo_o_barra_final(self):
        for raw in ("https://h.test:8081", "https://h.test:8081/", "https://h.test:8081/hess/api", "https://h.test:8081/hess/api/"):
            with mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": raw}):
                self.assertEqual(la.LivoltekAdapter()._base(), "https://h.test:8081")
        with mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": "http://api.remoto.test"}):
            with self.assertRaises(RuntimeError):
                la.LivoltekAdapter()._base()                     # la API solo admite HTTPS (salvo localhost para pruebas)


# --------------------------------------------------------------------------- #
# Servidor falso local
# --------------------------------------------------------------------------- #
class Fake(BaseHTTPRequestHandler):
    script: list = []
    seen: list = []

    def _go(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode() if n else ""
        Fake.seen.append({"method": self.command, "path": self.path, "auth": self.headers.get("Authorization"), "body": body})
        status, payload = Fake.script.pop(0) if Fake.script else (200, {"code": "200", "message": "SUCCESS", "data": {}})
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = do_POST = _go

    def log_message(self, *a):
        pass


def ok(data):
    return 200, {"code": "200", "message": "SUCCESS", "data": data}


LOGIN_OK = ok({"msgCode": "operate.success", "message": None, "data": "TOKEN-DE-PRUEBA-LOGIN-0001", "msg_code": "operate.success"})


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Fake.script, Fake.seen = [], []
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {**FAKE, "LIVOLTEK_API_URL": f"http://127.0.0.1:{self.port}",
                                                "LIVOLTEK_BUDGET_FILE": str(Path(self.tmp.name) / "b.json")})
        self.env.start()
        self._all_sleeps: list = []
        self.sl = mock.patch.object(la.time, "sleep", lambda s: self._all_sleeps.append(s))
        self.sl.start()
        self.a = la.LivoltekAdapter(min_interval=0)

    @property
    def sleeps(self):
        return [s for s in self._all_sleeps if s > 0]       # ignora las pausas nulas del ritmo entre llamadas

    def tearDown(self):
        self.sl.stop()
        self.env.stop()
        self.tmp.cleanup()
        la._RUNTIME_SECRETS.discard("TOKEN-DE-PRUEBA-LOGIN-0001")

    def test_login_y_lectura(self):
        Fake.script = [LOGIN_OK, ok({"list": [{"powerStationId": "527"}], "count": 1})]
        sites = self.a.list_sites()
        self.assertEqual(sites[0]["powerStationId"], "527")
        login, call = Fake.seen
        self.assertEqual(login["method"], "POST")
        self.assertEqual(json.loads(login["body"]), {"secuid": FAKE["LIVOLTEK_SECUID"], "key": FAKE["LIVOLTEK_KEY"]})
        self.assertIn("/hess/api/login", login["path"])
        self.assertEqual(call["auth"], "TOKEN-DE-PRUEBA-LOGIN-0001")          # sin prefijo Bearer
        self.assertIn("userToken=UTOKEN-FAKE-9012", call["path"])
        self.assertIn("userType=1", call["path"])
        self.assertEqual(self.a.calls, 2)
        self.assertIn("TOKEN-DE-PRUEBA-LOGIN-0001", la._RUNTIME_SECRETS)
        self.assertNotIn("TOKEN-DE-PRUEBA-LOGIN-0001", la.redact("x TOKEN-DE-PRUEBA-LOGIN-0001 y"))

    def test_429_backoff_exponencial(self):
        Fake.script = [LOGIN_OK, (429, {"code": "429"}), (429, {"code": "429"}), ok({"powerStationId": "527"})]
        self.assertEqual(self.a.site_of("SN1"), "527")
        self.assertEqual(self.sleeps, [2, 4])
        self.assertEqual(self.a.calls, 4)

    def test_429_agotado(self):
        Fake.script = [LOGIN_OK] + [(429, {"code": "429"})] * 6
        with self.assertRaises(RuntimeError) as cm:
            self.a.site_of("SN1")
        self.assertIn("429", str(cm.exception))
        self.assertEqual(self.sleeps, [2, 4, 8, 16])

    def test_428_token_ocupado_sin_reintento(self):
        Fake.script = [LOGIN_OK, (428, {"code": "428", "message": "token occupied"})]
        with self.assertRaises(la.TokenOccupied) as cm:
            self.a.site_of("SN1")
        self.assertIn("3 IP", str(cm.exception))
        self.assertEqual(self.a.calls, 2)                                     # login + una sola llamada
        self.assertEqual(self.sleeps, [])

    def test_401_relogin_una_vez(self):
        Fake.script = [LOGIN_OK, (401, {"code": "401"}), LOGIN_OK, ok({"powerStationId": "9"})]
        self.assertEqual(self.a.site_of("SN1"), "9")
        self.assertEqual([s["path"].split("?")[0] for s in Fake.seen].count("/hess/api/login"), 2)

    def test_presupuesto_por_token(self):
        with mock.patch.object(la, "LIMIT_PER_TOKEN", 2):
            Fake.script = [LOGIN_OK, ok({"powerStationId": "1"}), ok({"powerStationId": "2"})]
            self.a.site_of("A")
            self.a.site_of("B")
            n_before = len(Fake.seen)
            with self.assertRaises(la.BudgetExceeded):
                self.a.site_of("C")
            self.assertEqual(len(Fake.seen), n_before)                        # no se llamó a la nube
            # el presupuesto sobrevive entre ejecuciones (archivo): un adaptador nuevo también se detiene
            b = la.LivoltekAdapter(min_interval=0)
            b._token = "TOKEN-DE-PRUEBA-LOGIN-0001"
            with self.assertRaises(la.BudgetExceeded):
                b.site_of("D")

    def test_tope_de_llamadas_de_la_ejecucion(self):
        a = la.LivoltekAdapter(min_interval=0, max_calls=1)
        Fake.script = [LOGIN_OK]
        with self.assertRaises(RuntimeError) as cm:
            a.site_of("SN1")
        self.assertIn("tope de llamadas", str(cm.exception))

    def test_una_consulta_por_hora(self):
        Fake.script = [LOGIN_OK, ok({"pvYield": []})]
        self.a.read("devicePowerReportQuery", {}, {}, {"id": 1, "startTime": "2026-10-05 00:00:00", "endTime": "2026-10-05 23:59:59"})
        n = len(Fake.seen)
        with self.assertRaises(la.Refused):
            self.a.read("devicePowerReportQuery", {}, {}, {"id": 1, "startTime": "2026-10-05 00:00:00", "endTime": "2026-10-05 23:59:59"})
        self.assertEqual(len(Fake.seen), n)

    def test_paginacion_base_cero(self):
        page1 = [{"alarmCode": str(i)} for i in range(30)]
        Fake.script = [LOGIN_OK, ok({"list": page1, "count": 33}), ok({"list": [{"alarmCode": "x"}], "count": 33}),
                       ok({"list": [{"alarmCode": "p0-a"}, {"alarmCode": "p0-b"}, {"alarmCode": "p0-c"}], "count": 33})]
        out = self.a._paged("deviceHistoricalAlarm", {"siteId": "1", "serialNumber": "S"}, {"startTime": "2026-10-01", "endTime": "2026-10-05"})
        self.assertEqual(len(out), 34)           # 30 + 1 + 3 de la página 0 (faltaban 2 según `count`; se pidió la página anterior)
        pages = [s["path"].split("page=")[1].split("&")[0] for s in Fake.seen[1:]]
        self.assertEqual(pages, ["1", "2", "0"])

    def test_errores_redactados(self):
        Fake.script = [LOGIN_OK, (500, {"detail": "boom UTOKEN-FAKE-9012 userToken=ZZZ TOKEN-DE-PRUEBA-LOGIN-0001"})] * 6
        with self.assertRaises(RuntimeError) as cm:
            self.a.site_of("SN1")
        msg = la.redact(cm.exception)
        for s in ("UTOKEN-FAKE-9012", "TOKEN-DE-PRUEBA-LOGIN-0001", "ZZZ"):
            self.assertNotIn(s, msg)

    def test_normalized_extremo_a_extremo(self):
        today = self.a.today()
        Fake.script = [
            LOGIN_OK,
            ok({"powerStationId": "527"}),                                                    # site_of
            ok({"energyStatus": "disCharging", "energyPower": -0.156, "energySoc": 100.0, "pvPower": 0.006,
                "powerGridPower": 0.0, "loadPower": 0.0, "timestamp": 1655789700000}),        # curPowerflow
            ok({"1": [{"rVoltage": "230", "batteryVoltage": "52", "timestamp": 5}]}),         # realTime
            ok([{"id": "8", "sn": "SN1", "powerGenerationDay": "12", "loadDay": "15", "positiveDay": "1",
                 "negativeDay": "2", "chargeDay": "3", "dischargeDay": "4", "runningStatus": "Normal"}]),   # basicData
            ok({"pvProduceElectric": "137.5", "loadCustomerElectric": "3.1"}),                # realElectricity
        ]
        n = self.a.normalized("SN1")
        self.assertEqual(n["site_id"], "527")
        self.assertAlmostEqual(n["bat_power_w"], -156.0)
        self.assertEqual(n["energy_total_kwh"]["pv"], 137.5)
        self.assertEqual(n["state"], "Normal")
        self.assertEqual(self.a.calls, 6)                      # login + 5 lecturas
        paths = [s["path"].split("?")[0] for s in Fake.seen]
        self.assertEqual(paths[1:], ["/hess/api/site/SN1", "/hess/api/site/527/curPowerflow", "/hess/api/device/527/SN1/realTime",
                                     "/hess/api/device/basicData", "/hess/api/device/8/realElectricity"])
        rt = Fake.seen[3]["path"]
        self.assertIn(f"startTime={(today - dt.timedelta(days=1)).isoformat()}%2000%3A00%3A00", rt)   # espacio y ':' codificados


if __name__ == "__main__":
    unittest.main()
