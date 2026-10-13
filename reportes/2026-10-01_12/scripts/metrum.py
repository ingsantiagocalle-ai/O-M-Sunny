import os, json, time, urllib.request, urllib.error
BASE = os.environ["METRUM_API_URL"].rstrip("/")
_TOK = None
def _req(method, path, body=None, auth=True, retries=4):
    global _TOK
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    for i in range(retries):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if auth:
            req.add_header("X-Authorization", "Bearer " + login())
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt else None
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(2 ** (i + 1)); continue
            if e.code == 401 and auth and i < retries - 1:
                _TOK = None; time.sleep(2); continue
            raise RuntimeError(f"{e.code} {path}: {e.read()[:300]!r}")
        except urllib.error.URLError as e:
            if i < retries - 1: time.sleep(2 ** (i + 1)); continue
            raise
def login():
    global _TOK
    if _TOK: return _TOK
    r = _req("POST", "/api/auth/login", {"username": os.environ["METRUM_USERNAME"], "password": os.environ["METRUM_PASSWORD"]}, auth=False)
    _TOK = r["token"]
    return _TOK
def get(path): return _req("GET", path)
def post(path, body): return _req("POST", path, body)
