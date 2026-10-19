"""Cliente mínimo de la API REST de Metrum (ThingsBoard) para el reporte diario. SOLO LECTURA.

Credenciales únicamente desde el entorno (nunca se imprimen ni se escriben):
  METRUM_API_URL, METRUM_USERNAME, METRUM_PASSWORD
El JWT vive solo en memoria y se reutiliza (~100 min) para no disparar el rate-limit por logins repetidos.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request

BASE = os.environ.get('METRUM_API_URL', '').rstrip('/')
_tok = {'t': None, 'at': 0.0}
_lock = threading.Lock()


def _req(method, path, body=None, token=None, timeout=60):
    if not BASE:
        raise RuntimeError('Falta METRUM_API_URL en el entorno')
    data = json.dumps(body).encode() if body is not None else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['X-Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return json.loads(f.read().decode() or 'null')
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"HTTP {e.code} {method} {path.split('?')[0]}") from None
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise


def token():
    with _lock:
        if _tok['t'] and time.time() - _tok['at'] < 6000:
            return _tok['t']
        d = _req('POST', '/api/auth/login',
                 {'username': os.environ['METRUM_USERNAME'], 'password': os.environ['METRUM_PASSWORD']})
        _tok['t'], _tok['at'] = d['token'], time.time()
        return _tok['t']


def get(path):
    return _req('GET', path, token=token())


def post(path, body):
    return _req('POST', path, body, token=token())
