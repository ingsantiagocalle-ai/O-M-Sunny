#!/usr/bin/env python3
"""Actualiza el Apéndice B (Livoltek) del skill om-agency desde la doc pública de la API.

Fuente única: references/livoltek/sources.json, cuyo `docs_url` es
https://api.livoltek-portal.com:8081/ess-api/index.html (servidor Internacional; Europa usa
https://api-eu.livoltek-portal.com:8081/ess-api/). La doc es una app Vue (no hay Swagger:
/v2/api-docs y /v3/api-docs dan 404): todo el texto vive dentro de `js/app.<hash>.js` como
funciones de render precompiladas. Este script descarga `index.html` y el bundle, y recorre el
bundle con un mini intérprete de JavaScript (solo biblioteca estándar, sin Node ni navegador)
para reconstruir las 54 secciones del árbol lateral tal como se ven en pantalla.

No usa ni necesita credenciales de Livoltek (solo descarga archivos estáticos públicos).

Uso:
  python3 scripts/update_livoltek_api.py            # sincroniza y reescribe references/livoltek/
  python3 scripts/update_livoltek_api.py --check    # solo informa (exit 0 sin cambios, 1 con cambios, 2 error)
  python3 scripts/update_livoltek_api.py --from-files APP.js [--index INDEX.html]
        # sin red: usa archivos que el usuario guardó desde su navegador (combinable con --check)

Lo que NO viene de la doc (clasificación lectura/control, nivel B.5, ventanas, incoherencias
detectadas) vive en references/livoltek/clasificacion.json y se conserva al regenerar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

SKILL_DIR = Path(__file__).resolve().parent.parent
REF_DIR = SKILL_DIR / "references" / "livoltek"
SOURCES_FILE = REF_DIR / "sources.json"
CLASS_FILE = REF_DIR / "clasificacion.json"
TIMEOUT = 60
UA = "om-agency-livoltek-updater/1.0"
API_PREFIX = "/hess/api"
GENERATED_BY = "scripts/update_livoltek_api.py"


# --------------------------------------------------------------------------- #
# HTTP (solo archivos estáticos públicos; sin credenciales)
# --------------------------------------------------------------------------- #
def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- #
# Mini intérprete de JavaScript (subconjunto ES5 que emite webpack + vue-loader)
# --------------------------------------------------------------------------- #
class JSError(Exception):
    pass


_TOKEN = re.compile(
    r"""
    (?P<ws>\s+)
   |(?P<num>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
   |(?P<id>[A-Za-z_$][\w$]*)
   |(?P<str>"(?:[^"\\\n]|\\.|\\\n)*"|'(?:[^'\\\n]|\\.|\\\n)*')
   |(?P<op>===|!==|\|\||&&|==|!=|[{}()\[\],.:;=!+\-*/?<>])
    """,
    re.X | re.S,
)
_SIMPLE_ESC = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def js_unescape(body: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        i += 1
        c = body[i]
        if c in _SIMPLE_ESC:
            out.append(_SIMPLE_ESC[c])
        elif c == "x":
            out.append(chr(int(body[i + 1:i + 3], 16)))
            i += 2
        elif c == "u":
            if body[i + 1] == "{":
                j = body.index("}", i)
                out.append(chr(int(body[i + 2:j], 16)))
                i = j
            else:
                out.append(chr(int(body[i + 1:i + 5], 16)))
                i += 4
        elif c == "\n":
            pass  # continuación de línea
        else:
            out.append(c)
        i += 1
    # une pares sustitutos (\uD83D\uDE00) en un solo carácter
    return "".join(out).encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def tokenize(src: str) -> list[tuple[str, object]]:
    toks: list[tuple[str, object]] = []
    pos = 0
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if not m:
            raise JSError(f"carácter no reconocido en {pos}: {src[pos:pos + 30]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        text = m.group()
        if kind == "num":
            toks.append(("num", float(text) if "." in text or "e" in text.lower() else int(text)))
        elif kind == "str":
            toks.append(("str", js_unescape(text[1:-1])))
        else:
            toks.append((kind, text))
    toks.append(("eof", None))
    return toks


class Parser:
    """Parser descendente recursivo -> AST en tuplas."""

    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self):
        return self.t[self.i]

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def accept(self, kind, val=None):
        k, v = self.peek()
        if k == kind and (val is None or v == val):
            self.i += 1
            return True
        return False

    def expect(self, kind, val=None):
        k, v = self.next()
        if k != kind or (val is not None and v != val):
            raise JSError(f"se esperaba {val or kind}, llegó {v!r} (token {self.i})")
        return v

    # --- expresiones -----------------------------------------------------
    def expr(self):
        first = self.assign()
        if self.peek() == ("op", ","):
            items = [first]
            while self.accept("op", ","):
                items.append(self.assign())
            return ("seq", items)
        return first

    def assign(self):
        left = self.cond()
        if self.peek() == ("op", "=") and left[0] in ("id", "mem"):
            self.next()
            return ("assign", left, self.assign())
        return left

    def cond(self):
        test = self.or_()
        if self.accept("op", "?"):
            a = self.assign()
            self.expect("op", ":")
            b = self.assign()
            return ("cond", test, a, b)
        return test

    def or_(self):
        left = self.and_()
        while self.accept("op", "||"):
            left = ("or", left, self.and_())
        return left

    def and_(self):
        left = self.eq()
        while self.accept("op", "&&"):
            left = ("and", left, self.eq())
        return left

    def eq(self):
        left = self.add()
        while self.peek()[0] == "op" and self.peek()[1] in ("===", "!==", "==", "!="):
            op = self.next()[1]
            left = ("eq", op, left, self.add())
        return left

    def add(self):
        left = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            left = ("bin", op, left, self.unary())
        return left

    def unary(self):
        k, v = self.peek()
        if k == "op" and v == "!":
            self.next()
            return ("not", self.unary())
        if k == "op" and v == "-":
            self.next()
            return ("neg", self.unary())
        if k == "id" and v in ("void", "typeof"):
            self.next()
            return (v, self.unary())
        if k == "id" and v == "new":
            self.next()
            callee = self.member_only()
            args = self.args() if self.peek() == ("op", "(") else []
            return ("new", callee, args)
        return self.postfix()

    def member_only(self):
        node = self.primary()
        while True:
            if self.accept("op", "."):
                node = ("mem", node, ("lit", self.expect("id")))
            elif self.accept("op", "["):
                prop = self.expr()
                self.expect("op", "]")
                node = ("mem", node, prop)
            else:
                return node

    def postfix(self):
        node = self.primary()
        while True:
            if self.accept("op", "."):
                node = ("mem", node, ("lit", self.expect("id")))
            elif self.accept("op", "["):
                prop = self.expr()
                self.expect("op", "]")
                node = ("mem", node, prop)
            elif self.peek() == ("op", "("):
                node = ("call", node, self.args())
            else:
                return node

    def args(self):
        self.expect("op", "(")
        out = []
        if not self.accept("op", ")"):
            out.append(self.assign())
            while self.accept("op", ","):
                out.append(self.assign())
            self.expect("op", ")")
        return out

    def primary(self):
        k, v = self.next()
        if k == "num":
            return ("lit", v)
        if k == "str":
            return ("lit", v)
        if k == "id":
            if v == "function":
                return self.function()
            if v == "this":
                return ("this",)
            if v == "null":
                return ("lit", None)
            if v == "true":
                return ("lit", True)
            if v == "false":
                return ("lit", False)
            return ("id", v)
        if k == "op":
            if v == "(":
                e = self.expr()
                self.expect("op", ")")
                return e
            if v == "[":
                items = []
                while not self.accept("op", "]"):
                    items.append(self.assign())
                    if not self.accept("op", ","):
                        self.expect("op", "]")
                        break
                return ("arr", items)
            if v == "{":
                props = []
                while not self.accept("op", "}"):
                    kk, key = self.next()
                    if kk not in ("id", "str", "num"):
                        raise JSError(f"clave de objeto inválida: {key!r}")
                    self.expect("op", ":")
                    props.append((str(key), self.assign()))
                    if not self.accept("op", ","):
                        self.expect("op", "}")
                        break
                return ("obj", props)
        raise JSError(f"token inesperado {v!r} (posición {self.i})")

    # --- funciones y sentencias -----------------------------------------
    def function(self):
        if self.peek()[0] == "id":
            self.next()  # nombre opcional
        self.expect("op", "(")
        params = []
        if not self.accept("op", ")"):
            params.append(self.expect("id"))
            while self.accept("op", ","):
                params.append(self.expect("id"))
            self.expect("op", ")")
        self.expect("op", "{")
        body = []
        while not self.accept("op", "}"):
            body.append(self.statement())
        return ("fn", params, body)

    def statement(self):
        k, v = self.peek()
        if k == "id" and v == "var":
            self.next()
            decls = []
            while True:
                name = self.expect("id")
                init = self.assign() if self.accept("op", "=") else None
                decls.append((name, init))
                if not self.accept("op", ","):
                    break
            self.accept("op", ";")
            return ("var", decls)
        if k == "id" and v == "return":
            self.next()
            if self.peek() in (("op", ";"), ("op", "}")):
                self.accept("op", ";")
                return ("ret", None)
            e = self.expr()
            self.accept("op", ";")
            return ("ret", e)
        e = self.expr()
        self.accept("op", ";")
        return ("expr", e)


class JSFunction:
    def __init__(self, params, body, scope):
        self.params, self.body, self.scope = params, body, scope


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class Scope:
    def __init__(self, parent=None):
        self.vars: dict = {}
        self.parent = parent

    def lookup(self, name):
        s = self
        while s:
            if name in s.vars:
                return s
            s = s.parent
        return None


class Req:
    """Stub del `require` de webpack: a("2877") devuelve el normalizador de vue-loader."""

    def __init__(self, calls):
        self.calls = calls
        self.props = {"r": lambda *a: None, "d": lambda *a: None, "n": lambda m: (lambda: m),
                      "o": lambda *a: False, "p": ""}

    def __call__(self, ident):
        if ident == "2877":
            def normalizer(comp, render, static_fns=None, *rest):
                self.calls.append({"options": comp, "render": render, "static": static_fns or []})
                return {"exports": {"render": render, "staticRenderFns": static_fns or [],
                                    "name": (comp or {}).get("name") if isinstance(comp, dict) else None}}
            return {"a": normalizer}
        return {}  # cualquier otro módulo: inerte


class Interp:
    def __init__(self):
        self.globals = Scope()
        self.globals.vars["Object"] = lambda x=None, *a: x
        self.globals.vars["undefined"] = None

    def call(self, fn, this, args):
        if isinstance(fn, JSFunction):
            scope = Scope(fn.scope)
            scope.vars["this"] = this
            for i, p in enumerate(fn.params):
                scope.vars[p] = args[i] if i < len(args) else None
            try:
                for st in fn.body:
                    self.stmt(st, scope)
            except _Return as r:
                return r.value
            return None
        if callable(fn):
            return fn(*args)
        raise JSError(f"valor no invocable: {fn!r}")

    def stmt(self, st, scope):
        kind = st[0]
        if kind == "var":
            for name, init in st[1]:
                scope.vars[name] = self.ev(init, scope) if init is not None else None
        elif kind == "ret":
            raise _Return(self.ev(st[1], scope) if st[1] is not None else None)
        else:
            self.ev(st[1], scope)

    def get(self, obj, key):
        if isinstance(obj, Req):
            return obj.props.get(key)
        if isinstance(obj, dict):
            return obj.get(key)
        if isinstance(obj, list):
            if key == "length":
                return len(obj)
            return obj[int(key)] if str(key).lstrip("-").isdigit() and int(key) < len(obj) else None
        if isinstance(obj, str) and key == "length":
            return len(obj)
        return None

    def ev(self, n, scope):
        kind = n[0]
        if kind == "lit":
            return n[1]
        if kind == "id":
            s = scope.lookup(n[1]) or self.globals.lookup(n[1])
            return s.vars[n[1]] if s else None
        if kind == "this":
            s = scope.lookup("this")
            return s.vars["this"] if s else None
        if kind == "arr":
            return [self.ev(x, scope) for x in n[1]]
        if kind == "obj":
            return {k: self.ev(v, scope) for k, v in n[1]}
        if kind == "fn":
            return JSFunction(n[1], n[2], scope)
        if kind == "mem":
            return self.get(self.ev(n[1], scope), self.ev(n[2], scope))
        if kind == "call":
            callee = n[1]
            this = None
            if callee[0] == "mem":
                this = self.ev(callee[1], scope)
                fn = self.get(this, self.ev(callee[2], scope))
            else:
                fn = self.ev(callee, scope)
            return self.call(fn, this, [self.ev(a, scope) for a in n[2]])
        if kind == "not":
            return not self.ev(n[1], scope)
        if kind == "neg":
            return -self.ev(n[1], scope)
        if kind == "void":
            self.ev(n[1], scope)
            return None
        if kind == "typeof":
            return type(self.ev(n[1], scope)).__name__
        if kind == "or":
            left = self.ev(n[1], scope)
            return left if left else self.ev(n[2], scope)
        if kind == "and":
            left = self.ev(n[1], scope)
            return self.ev(n[2], scope) if left else left
        if kind == "cond":
            return self.ev(n[2], scope) if self.ev(n[1], scope) else self.ev(n[3], scope)
        if kind == "eq":
            a, b = self.ev(n[2], scope), self.ev(n[3], scope)
            return (a == b) if n[1] in ("===", "==") else (a != b)
        if kind == "bin":
            a, b = self.ev(n[2], scope), self.ev(n[3], scope)
            if n[1] == "+":
                return (a + b) if not (isinstance(a, str) or isinstance(b, str)) else f"{a}{b}"
            return a - b
        if kind == "seq":
            result = None
            for x in n[1]:
                result = self.ev(x, scope)
            return result
        if kind == "assign":
            target, value = n[1], self.ev(n[2], scope)
            if target[0] == "id":
                s = scope.lookup(target[1]) or self.globals
                s.vars[target[1]] = value
            else:
                obj = self.ev(target[1], scope)
                key = self.ev(target[2], scope)
                if isinstance(obj, dict):
                    obj[key] = value
                elif isinstance(obj, list):
                    obj[int(key)] = value
            return value
        if kind == "new":
            return {}
        raise JSError(f"nodo no soportado: {kind}")


def parse_function(src: str):
    p = Parser(tokenize(src))
    p.expect("id", "function")
    node = p.function()
    return node


def parse_expression(src: str):
    p = Parser(tokenize(src))
    node = p.expr()
    p.expect("eof")
    return node


# --------------------------------------------------------------------------- #
# Localización de piezas dentro del bundle webpack
# --------------------------------------------------------------------------- #
# El minificador deja sin comillas las claves que son identificadores válidos (fbb0:function…) y
# con comillas las que empiezan por dígito ("0153":function…); las puramente numéricas van desnudas.
_MODULE_START = re.compile(r'(?<=[{,])(?:"([0-9a-z]+)"|([0-9a-z]{1,8})):function\(t,e,a\)\{')


def split_modules(js: str) -> dict[str, str]:
    """Divide el mapa de módulos final `})({0:function(t,e,a){...},"0153":function...})`."""
    start = js.find("})({")
    if start < 0:
        raise JSError("no se encontró el mapa de módulos del bundle")
    body_start = start + 3  # apunta a '{'
    body_end = js.rfind("})")
    region = js[body_start:body_end + 1]
    starts = [(m.start(), m.group(1) or m.group(2)) for m in _MODULE_START.finditer(region)]
    mods: dict[str, str] = {}
    for idx, (pos, key) in enumerate(starts):
        end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(region) - 1
        text = region[pos:end]
        mods[key] = text[text.index(":function(") + 1:]
    return mods


def balanced(text: str, start: int) -> int:
    """Índice del cierre que empareja el '[' o '{' en `start` (respeta cadenas)."""
    pairs = {"[": "]", "{": "}", "(": ")"}
    stack = [pairs[text[start]]]
    i = start + 1
    while i < len(text) and stack:
        c = text[i]
        if c in "\"'":
            q = c
            i += 1
            while text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif c in pairs:
            stack.append(pairs[c])
        elif c == stack[-1]:
            stack.pop()
        i += 1
    if stack:
        raise JSError("corchetes sin cerrar")
    return i - 1


def find_menu(js: str) -> list[dict]:
    """Árbol lateral en inglés: la lista cuyo grupo de endpoints se llama 'API'."""
    marker = '{id:"basic",label:"API"'
    k = js.find(marker)
    if k < 0:
        raise JSError("no se encontró el árbol lateral (label 'API')")
    start = js.rfind('[{id:"purpose"', 0, k)
    end = balanced(js, start)
    return Interp().ev(parse_expression(js[start:end + 1]), Scope())


def find_context_map(modules: dict[str, str]) -> dict[str, str]:
    """Módulo require.context: './<id>.vue' -> id de módulo."""
    for text in modules.values():
        if '"./acronyms.vue"' in text:
            return {m.group(1): m.group(2) for m in re.finditer(r'"\./([A-Za-z0-9_-]+)\.vue":"([0-9a-z]+)"', text)}
    raise JSError("no se encontró el mapa './<id>.vue' -> módulo")


# --------------------------------------------------------------------------- #
# Render: función de render de Vue -> árbol -> Markdown
# --------------------------------------------------------------------------- #
def vnode(tag, data=None, children=None, _norm=None):
    if isinstance(data, list):
        children, data = data, None
    flat: list = []

    def add(x):
        if isinstance(x, list):
            for y in x:
                add(y)
        elif x is not None:
            flat.append(x)

    add(children or [])
    return {"tag": tag, "data": data if isinstance(data, dict) else None, "children": flat}


def render_ctx(static_fns, interp):
    ctx: dict = {}
    ctx["_c"] = vnode
    ctx["$createElement"] = vnode
    ctx["_v"] = lambda text: {"text": str(text)}
    ctx["_s"] = lambda v: "" if v is None else str(v)
    ctx["_e"] = lambda: {"text": ""}
    ctx["_m"] = lambda i, *a: interp.call(static_fns[i], ctx, [])
    ctx["_self"] = {"_c": vnode}
    return ctx


def load_section_tree(module_src: str, interp: Interp):
    """Ejecuta un módulo de sección y devuelve (nombre, árbol de nodos) o (None, None)."""
    if 'a("2877")' not in module_src:
        return None, None
    calls: list = []
    fn = interp.ev(parse_function(module_src), Scope(interp.globals))
    exports: dict = {}
    interp.call(fn, None, [{"exports": {}}, exports, Req(calls)])
    content = next((c for c in calls if c["static"]), None)
    comp = exports.get("default") or {}
    name = comp.get("name") if isinstance(comp, dict) else None
    if not content:
        return name, None
    tree = interp.call(content["render"], render_ctx(content["static"], interp), [])
    return name, tree


def txt(n) -> str:
    if n is None:
        return ""
    if "text" in n:
        return n["text"]
    return "".join(txt(c) for c in n["children"])


def attrs(n) -> dict:
    return ((n.get("data") or {}).get("attrs")) or {}


def _str(v, default="") -> str:
    return v if isinstance(v, str) else default


def inline(n) -> str:
    if n is None:
        return ""
    if "text" in n:
        return n["text"]
    c = "".join(inline(k) for k in n["children"])
    tag = n["tag"]
    if tag == "br":
        return "<br>"
    if tag == "code":
        return f"`{c}`"
    if tag in ("strong", "b"):
        return f"**{c}**"
    if tag in ("em", "i"):
        return f"*{c}*"
    if tag == "a":
        return f"[{c}]({_str(attrs(n).get('href'))})"
    if tag == "img":
        at = attrs(n)
        src = at.get("src") if isinstance(at.get("src"), str) else "(imagen empaquetada en el bundle; no incluida)"
        return f"![{_str(at.get('alt'))}]({src})"
    return c


def md_table(n) -> str:
    rows: list[list[str]] = []

    def walk(x):
        if not x or "text" in x:
            return
        if x["tag"] == "tr":
            rows.append([
                re.sub(r"\n+", "<br>", inline(k).replace("|", "\\|")).strip()
                for k in x["children"] if k.get("tag") in ("th", "td")
            ])
        else:
            for k in x["children"]:
                walk(k)

    walk(n)
    if not rows:
        return ""
    w = max(len(r) for r in rows)
    pad = lambda r: r + [""] * (w - len(r))  # noqa: E731
    out = ["| " + " | ".join(pad(rows[0])) + " |", "|" + "|".join([" --- "] * w) + "|"]
    out += ["| " + " | ".join(pad(r)) + " |" for r in rows[1:]]
    return "\n".join(out)


def block(n) -> str:
    if n is None:
        return ""
    if "text" in n:
        return n["text"].strip()
    tag = n["tag"]
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "#" * int(tag[1]) + " " + inline(n).strip()
    if tag == "p":
        return inline(n).strip()
    if tag == "pre":
        return "```\n" + re.sub(r"\s+$", "", txt(n)) + "\n```"
    if tag == "table":
        return md_table(n)
    if tag in ("ul", "ol"):
        lines = []
        for i, li in enumerate((k for k in n["children"] if k.get("tag") == "li"), 1):
            lines.append((f"{i}. " if tag == "ol" else "- ") + inline(li).strip())
        return "\n".join(lines)
    if tag == "blockquote":
        return "\n".join("> " + ln for ln in inline(n).strip().split("\n"))
    if tag == "hr":
        return "---"
    return "\n\n".join(filter(None, (block(k) for k in n["children"])))


def tree_to_markdown(tree) -> str:
    return re.sub(r"\n{3,}", "\n\n", block(tree)) + "\n"


# --------------------------------------------------------------------------- #
# Extracción completa del bundle
# --------------------------------------------------------------------------- #
def parse_bundle(js: str) -> dict:
    modules = split_modules(js)
    menu = find_menu(js)
    ctx_map = find_context_map(modules)
    interp = Interp()

    version_m = re.search(r'_v\("(v\d+\.\d+(?:\.\d+)?)"\)', js)
    sections: dict[str, dict] = {}
    for sec_id, mod_id in ctx_map.items():
        name, tree = load_section_tree(modules[mod_id], interp) if mod_id in modules else (None, None)
        if tree is None:
            continue
        md = tree_to_markdown(tree)
        title_m = re.match(r"# (.+)", md)
        sections[sec_id] = {
            "id": sec_id, "module": mod_id, "component": name,
            "title": title_m.group(1).strip() if title_m else sec_id,
            "markdown": md, "sha256": sha256(md),
        }

    order: list[dict] = []   # nodos del árbol lateral, en orden, con grupo
    for node in menu:
        if node.get("children"):
            order.append({"id": node["id"], "label": node["label"], "group": True})
            for ch in node["children"]:
                order.append({"id": ch["id"], "label": ch["label"], "group": False, "parent": node["id"]})
        else:
            order.append({"id": node["id"], "label": node["label"], "group": False})
    in_menu = {o["id"] for o in order}
    trivial = {sid for sid, s in sections.items() if len([ln for ln in s["markdown"].splitlines() if ln.strip()]) <= 1}
    revision_md = sections.get("revision", {}).get("markdown", "")
    rev_m = re.search(r"([A-Z][a-z]+) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})", revision_md)
    last_rev = None
    if rev_m:
        try:
            last_rev = datetime.strptime(f"{rev_m.group(1)} {rev_m.group(2)} {rev_m.group(3)}", "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            last_rev = rev_m.group(0)
    return {
        "doc_version": version_m.group(1) if version_m else None,
        "last_revision_in_history": last_rev,
        "menu": order,
        "sections": sections,
        "not_in_menu": sorted(set(sections) - in_menu - trivial),
        "empty_modules": sorted(trivial - in_menu),
        "missing_in_bundle": sorted(i for i in in_menu if i not in sections and not any(o["id"] == i and o["group"] for o in order)),
        "modules_in_bundle": len(modules),
    }


# --------------------------------------------------------------------------- #
# Redacción de ejemplos de la doc (tokens/contraseñas de muestra)
# --------------------------------------------------------------------------- #
_JWT = re.compile(r"eyJ[A-Za-z0-9_\-.]*(?:[ \t]*\n[ \t]*[A-Za-z0-9_\-.]+)*")
_PWD = re.compile(r'("pwd"\s*:\s*")[0-9a-fA-F]{20,32}(")')


def redact_examples(md: str) -> str:
    md = _JWT.sub("<token-de-ejemplo-omitido>", md)
    return _PWD.sub(r"\1<md5-de-ejemplo-omitido>\2", md)


# --------------------------------------------------------------------------- #
# Endpoints: método, ruta y parámetros salen de cada sección (no se asumen)
# --------------------------------------------------------------------------- #
def parse_md_tables(md: str) -> dict[str, list[list[str]]]:
    """Primera tabla tras cada encabezado '## X' -> filas (sin separador)."""
    out: dict[str, list[list[str]]] = {}
    parts = re.split(r"^## ", md, flags=re.M)[1:]
    for part in parts:
        head, _, rest = part.partition("\n")
        rows: list[list[str]] = []
        for line in rest.split("\n"):
            if line.startswith("|"):
                rows.append([c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]])
            elif rows:
                break  # fin de la primera tabla
        rows = [r for r in rows if not (r and re.fullmatch(r":?-{3,}:?", r[0].replace(" ", "")))]
        if len(rows) > 1:
            out.setdefault(head.strip(), rows[1:])  # sin la fila de encabezado
    return out


def endpoint_meta(sec: dict) -> dict:
    md = sec["markdown"]
    url_m = re.search(r"\*\*(?:Host-)?URL\*\*:\s*(?:<br>)?\s*(.*?)(?=\*\*Method\*\*|\n|$)", md)
    raw_url = url_m.group(1) if url_m else ""
    raw_url = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw_url)
    mqtt = re.findall(r"mqtt://[^\s)]+", raw_url)
    method_m = re.search(r"\*\*Method\*\*:\s*([A-Za-z]+)", md)
    rules_m = re.search(r"\*\*Request Rules\*\*:\s*(.*?)(?=\n|$)", md)
    header_m = re.search(r"\*\*Header\*\*:\s*(.*?)(?=\*\*Request Rules\*\*|\n|$)", md)
    path = None
    if not mqtt:
        path = re.sub(r"\s+", "", raw_url)
        if path and not path.startswith("/"):
            path = "/" + path
    ex_m = re.search(r"## Example\n\n```\n(.*?)\n```", md, flags=re.S)
    example_raw = redact_examples(ex_m.group(1)) if ex_m else ""
    tables = parse_md_tables(md)
    return {
        "path": path or None,
        "mqtt_hosts": mqtt,
        "method": method_m.group(1).upper() if method_m else None,
        "header_note": (header_m.group(1).strip() if header_m else ""),
        "request_rules": rules_m.group(1).strip() if rules_m else "",
        "request_table": tables.get("Request parameters", []),
        "response_table": tables.get("Response Parameters", []),
        "example_raw": example_raw,
        "example_urls": [ln.strip() for ln in example_raw.split("\n") if ln.strip().startswith("http")],
    }


def build_endpoint(sec: dict, label: str, index: int, in_sidebar: bool, classes: dict) -> dict:
    meta = endpoint_meta(sec)
    path, method = meta["path"], meta["method"]
    inferred = False
    if path and not method:
        method, inferred = "GET", True
    params = []
    for row in meta["request_table"]:
        name = row[0].strip() if row else ""
        if not name:
            continue
        cells = row + [""] * (6 - len(row))
        required = {"yes": True, "no": False}.get(cells[4].strip().lower())
        if path and "{" + name + "}" in path:
            where = "ruta"
        elif method == "GET":
            where = "query"
        else:
            where = "query" if name in ("userToken", "userType") else "cuerpo"
        params.append({"name": name, "in": where, "type": cells[1], "length": cells[2],
                       "description": cells[3], "required": required, "constraint": cells[5]})
    names = {p["name"] for p in params}
    response = [{"name": r[0], "type": (r + [""] * 4)[1], "description": (r + [""] * 4)[3],
                 "constraint": (r + [""] * 6)[5]} for r in meta["response_table"] if r and r[0].strip()]
    cls = classes.get(sec["id"], {})
    transport = "mqtt" if meta["mqtt_hosts"] else "https"
    return {
        "id": sec["id"],
        "title": sec["title"],
        "menu_label": label,
        "order": index,
        "in_sidebar": in_sidebar,
        "transport": transport,
        "method": method,
        "method_inferred": inferred,
        "path": path,
        "mqtt_hosts": meta["mqtt_hosts"],
        "auth": ("cuerpo: secuid + key (devuelve el token)" if sec["id"] == "userLoginAndToken"
                 else "usuario/clave MQTT (se piden por correo a Livoltek)" if transport == "mqtt"
                 else "cabecera Authorization: <token del login>"),
        "uses_user_token": "userToken" in names,
        "uses_user_type": "userType" in names,
        "requires_account_pwd": {"account", "pwd"} <= names,
        "request_rules": meta["request_rules"],
        "params": params,
        "response_fields": response,
        "example_urls": meta["example_urls"],
        "kind": cls.get("kind", "sin_clasificar"),
        "nivel_b5": cls.get("nivel_b5"),
        "sensible": cls.get("sensible", False),
        "solo_manual": cls.get("solo_manual", False),
        "ejecutar_en_pruebas": cls.get("ejecutar_en_pruebas", cls.get("kind") == "lectura"),
        "implementado": cls.get("implementado", transport == "https"),
        "ventanas": cls.get("ventanas", []),
        "reglas_de_frecuencia": cls.get("reglas_de_frecuencia", []),
        "notas": cls.get("notas", []),
        "incoherencias_de_la_doc": cls.get("incoherencias_de_la_doc", []),
        "verificado_en_vivo": cls.get("verificado_en_vivo", False),
    }


# --------------------------------------------------------------------------- #
# Generación de archivos
# --------------------------------------------------------------------------- #
def demote(md: str, number: int | None) -> str:
    """Baja un nivel los encabezados (respeta bloques de código) y numera el H1."""
    out, fenced = [], False
    for line in md.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,5} ", line):
            line = "#" + line
            if number is not None and line.startswith("## ") and not out:
                line = f"## {number}. {line[3:]}"
        out.append(line)
    return "\n".join(out)


def render_api_doc(parsed: dict, meta: dict) -> str:
    out = [
        f"# Documentación de la API de Livoltek {parsed['doc_version']} (copia de trabajo)",
        "",
        f"> Generado por `{GENERATED_BY}` desde `{meta['bundle_name']}` (sha256 `{meta['bundle_sha256'][:16]}…`, "
        f"{meta['synced_at']}). **No editar a mano.** Última revisión del historial de la doc: "
        f"{parsed['last_revision_in_history']}. Texto reconstruido del bundle Vue de "
        "https://api.livoltek-portal.com:8081/ess-api/ (International) y https://api-eu.livoltek-portal.com:8081/ess-api/ (Europa).",
        ">",
        "> Los tokens y contraseñas de **ejemplo** de la doc se sustituyeron por marcadores "
        "(`<token-de-ejemplo-omitido>`, `<md5-de-ejemplo-omitido>`). Las incoherencias de la propia doc "
        "(rutas, unidades, erratas) se listan aparte en `endpoints.md`, no se corrigen aquí.",
        "",
        "## Índice",
        "",
    ]
    nodes = [o for o in parsed["menu"] if not o["group"]]
    for i, o in enumerate(nodes, 1):
        out.append(f"{i}. {o['label']}")
    out.append("")
    for i, o in enumerate(nodes, 1):
        sec = parsed["sections"].get(o["id"])
        if not sec:
            out += [f"## {i}. {o['label']}", "", "_Sección no encontrada en el bundle._", ""]
            continue
        out += [demote(redact_examples(sec["markdown"]), i).rstrip(), ""]
    hidden = parsed["not_in_menu"]
    if hidden:
        out += [
            "## Secciones presentes en el bundle pero fuera del árbol lateral",
            "",
            "Existen como módulos de la app y se alcanzan por id, pero no aparecen en el menú de la doc. "
            "No se usan por defecto en el adaptador.",
            "",
        ]
        for sid in hidden:
            sec = parsed["sections"][sid]
            if len(sec["markdown"].strip().splitlines()) <= 1:
                out += [f"### `{sid}` — «{sec['title']}» (sin contenido)", ""]
                continue
            out += [demote(demote(redact_examples(sec["markdown"]), None), None).rstrip(), ""]
    return "\n".join(out).rstrip() + "\n"


def cell(v) -> str:
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def render_endpoints_md(doc: dict, meta: dict) -> str:
    eps = doc["endpoints"]
    out = [
        "# Catálogo de endpoints Livoltek (API ESS v" + str(doc["doc_version"]).lstrip("v") + ")",
        "",
        f"> Generado por `{GENERATED_BY}` desde `{meta['bundle_name']}` ({meta['synced_at']}). "
        "**No editar a mano**: método, ruta y parámetros salen de la doc; la clasificación "
        "(lectura/control, nivel B.5, ventanas, incoherencias) sale de `clasificacion.json`.",
        "",
        "## Acceso",
        "",
        "- Solo HTTPS. Servidores: **International** `https://api.livoltek-portal.com:8081` y **Europa** "
        "`https://api-eu.livoltek-portal.com:8081`; prefijo común `" + API_PREFIX + "`.",
        "- `POST " + API_PREFIX + "/login` con `{\"secuid\",\"key\"}` → `data.data` = token. Ese token va en la cabecera "
        "`Authorization` (sin prefijo `Bearer`) en todo lo demás.",
        "- Casi todas las consultas llevan además `userToken` en la URL (token de cuenta o de sitio generado en el portal) "
        "y `userType` (0 = usuario final, por defecto; **1 = agente/instalador**).",
        "- Parámetros con espacios o caracteres especiales deben ir codificados en URL (`startTime=2025-01-18%2000:00:00`).",
        "",
        "## Resumen",
        "",
        "| # | Id | Método y ruta | Clase | Nivel B.5 | `userToken` | `account`+`pwd` | Ventana / regla | En árbol |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for ep in eps:
        where = f"`{ep['method']} {ep['path']}`" if ep["path"] else "MQTT (solo doc)"
        rules = "; ".join(ep["ventanas"] + ep["reglas_de_frecuencia"])
        out.append(
            f"| {ep['order']} | `{ep['id']}` | {where} | **{ep['kind']}**{' (sensible)' if ep['sensible'] else ''} "
            f"| {cell(ep['nivel_b5'])} | {'sí' if ep['uses_user_token'] else ''} | {'sí' if ep['requires_account_pwd'] else ''} "
            f"| {cell(rules)} | {'sí' if ep['in_sidebar'] else '**no**'} |"
        )
    out += ["", "## Incoherencias detectadas en la propia doc", "",
            "La doc se contradice a sí misma en estos puntos. Se anotan, **no se corrigen**; hay que confirmarlas en vivo.",
            ""]
    any_issue = False
    for ep in eps:
        for issue in ep["incoherencias_de_la_doc"]:
            any_issue = True
            out.append(f"- `{ep['id']}`: {issue}")
    if not any_issue:
        out.append("- (ninguna registrada)")
    out += ["", "## Detalle por endpoint", ""]
    for ep in eps:
        out += [f"### {ep['order']}. {ep['title']} — `{ep['id']}`", ""]
        if ep["path"]:
            out.append(f"- **{ep['method']}** `{ep['path']}`" + (" _(método inferido: la doc no lo indica)_" if ep["method_inferred"] else ""))
        else:
            out.append("- Transporte MQTT: " + ", ".join(f"`{h}`" for h in ep["mqtt_hosts"]) + " — **solo documentado; no implementado**.")
        out.append(f"- Autenticación: {ep['auth']}")
        out.append(f"- Clase: **{ep['kind']}**" + (f" · nivel B.5: **{ep['nivel_b5']}**" if ep["nivel_b5"] is not None else "")
                   + (" · contiene datos sensibles (credenciales o datos personales)" if ep["sensible"] else "")
                   + (" · **solo manual: el skill no lo ejecuta**" if ep["solo_manual"] else ""))
        if ep["request_rules"]:
            out.append(f"- Regla de frecuencia (doc): {ep['request_rules']}")
        for item in ep["ventanas"]:
            out.append(f"- Ventana: {item}")
        for item in ep["reglas_de_frecuencia"]:
            out.append(f"- Frecuencia: {item}")
        for item in ep["notas"]:
            out.append(f"- Nota: {item}")
        out.append("- Verificado en vivo: " + ("sí" if ep["verificado_en_vivo"] else "**no (sin verificar)**"))
        if ep["params"]:
            out += ["", "| Parámetro | En | Oblig. | Tipo | Descripción |", "|---|---|---|---|---|"]
            for p in ep["params"]:
                req = {True: "sí", False: "no", None: ""}[p["required"]]
                desc = "; ".join(x for x in (p["description"], p["constraint"]) if x)
                out.append(f"| `{p['name']}` | {p['in']} | {req} | {cell(p['type'])} | {cell(desc)} |")
        if ep["example_urls"]:
            out += ["", "Ejemplo(s) de la doc:", ""] + [f"    {u}" for u in ep["example_urls"]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def build_endpoints_doc(parsed: dict, classes: dict) -> dict:
    eps: list[dict] = []
    idx = 0
    nodes = [o for o in parsed["menu"] if not o["group"]]
    for o in nodes:
        sec = parsed["sections"].get(o["id"])
        if not sec:
            continue
        ep = build_endpoint(sec, o["label"], idx + 1, True, classes)
        if ep["path"] or ep["mqtt_hosts"]:
            idx += 1
            ep["order"] = idx
            eps.append(ep)
    for sid in parsed["not_in_menu"]:
        sec = parsed["sections"][sid]
        ep = build_endpoint(sec, sec["title"], idx + 1, False, classes)
        if ep["path"] or ep["mqtt_hosts"]:
            idx += 1
            ep["order"] = idx
            eps.append(ep)
    return {
        "generado_por": GENERATED_BY,
        "doc_version": parsed["doc_version"],
        "last_revision_in_history": parsed["last_revision_in_history"],
        "servidores": {"international": "https://api.livoltek-portal.com:8081",
                       "europe": "https://api-eu.livoltek-portal.com:8081"},
        "prefijo_api": API_PREFIX,
        "autenticacion": {
            "login": "POST /hess/api/login con {\"secuid\",\"key\"}; el token está en data.data",
            "cabecera": "Authorization: <token> (sin 'Bearer')",
            "userToken": "parámetro de URL; token de cuenta o de sitio generado en el portal",
            "userType": "0 = usuario final (por defecto), 1 = agente/instalador",
        },
        "endpoints": eps,
    }


def endpoint_keys(doc: dict) -> list[str]:
    return sorted(f"{e['method']} {e['path']}" if e["path"] else f"MQTT {e['id']}" for e in doc["endpoints"])


# --------------------------------------------------------------------------- #
# Estado (sources.json) y comparación
# --------------------------------------------------------------------------- #
ASSET_RE = re.compile(r"((?:app|chunk-[\w-]+)\.[0-9a-f]{8}\.(?:js|css))")


def index_assets(index_text: str) -> list[str]:
    return sorted(set(ASSET_RE.findall(index_text)))


def bundle_name_from_index(index_text: str) -> str | None:
    m = re.search(r"(?:src|href)=[\"']?([^\"' >]*?js/app\.[0-9a-f]+\.js)", index_text)
    return m.group(1) if m else None


def new_state(parsed: dict, doc: dict, bundle: bytes, bundle_name: str, index_text: str | None,
              index_sha: str | None, origin: str) -> dict:
    return {
        "status": "SINCRONIZADO",
        "origen": origin,
        "docs_version": parsed["doc_version"],
        "last_revision_in_history": parsed["last_revision_in_history"],
        "bundle_name": bundle_name,
        "bundle_sha256": sha256(bundle),
        "bundle_bytes": len(bundle),
        "index_html_sha256": index_sha,
        "assets_referenciados": index_assets(index_text) if index_text else [],
        "nodos_arbol_lateral": len([o for o in parsed["menu"] if not o["group"]]) + sum(1 for o in parsed["menu"] if o["group"]),
        "secciones_con_contenido": len(parsed["sections"]),
        "fuera_del_arbol": parsed["not_in_menu"],
        "endpoints": endpoint_keys(doc),
        "sin_clasificar": sorted(e["id"] for e in doc["endpoints"] if e["kind"] == "sin_clasificar"),
        "section_sha256": {sid: s["sha256"][:16] for sid, s in sorted(parsed["sections"].items())},
    }


def summarize_diff(old: dict, new: dict) -> list[str]:
    lines = []
    for key, label in (("endpoints", "endpoints"), ("fuera_del_arbol", "secciones fuera del árbol")):
        before, after = set(old.get(key) or []), set(new.get(key) or [])
        if added := sorted(after - before):
            lines.append(f"+ {label} nuevos: {', '.join(added)}")
        if removed := sorted(before - after):
            lines.append(f"- {label} eliminados: {', '.join(removed)}")
    for key in ("docs_version", "last_revision_in_history", "bundle_name", "bundle_sha256", "index_html_sha256"):
        if old.get(key) != new.get(key) and not (key == "index_html_sha256" and new.get(key) is None):
            lines.append(f"~ {key}: {old.get(key)} -> {new.get(key)}")
    changed = [s for s, h in (new.get("section_sha256") or {}).items() if (old.get("section_sha256") or {}).get(s) not in (None, h)]
    new_secs = [s for s in (new.get("section_sha256") or {}) if s not in (old.get("section_sha256") or {})]
    if changed:
        lines.append("~ secciones con texto distinto: " + ", ".join(changed))
    if new_secs and old.get("section_sha256"):
        lines.append("+ secciones nuevas: " + ", ".join(new_secs))
    if new.get("sin_clasificar"):
        lines.append("! endpoints sin clasificar (tratados como NO escribibles): " + ", ".join(new["sin_clasificar"]))
    if old.get("assets_referenciados") and new.get("assets_referenciados") and old["assets_referenciados"] != new["assets_referenciados"]:
        lines.append("~ assets del index: " + ", ".join(sorted(set(new["assets_referenciados"]) ^ set(old["assets_referenciados"]))))
    return lines


def comparable(state: dict) -> dict:
    keys = ("docs_version", "last_revision_in_history", "bundle_name", "bundle_sha256", "endpoints",
            "fuera_del_arbol", "section_sha256", "sin_clasificar")
    return {k: state.get(k) for k in keys}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def load_inputs(args, sources: dict) -> tuple[bytes, str | None, str | None, str, str]:
    """Devuelve (bundle, index_text, index_sha256, bundle_name, origen)."""
    if args.from_files:
        bundle = Path(args.from_files).read_bytes()
        index_text = index_sha = None
        if args.index:
            raw = Path(args.index).read_bytes()
            index_text = raw.decode("utf-8", "replace")
            # Un .html guardado desde el navegador es el DOM ya renderizado, no el index.html del servidor:
            # su hash NO es comparable. Solo se acepta como hash del servidor si contiene el shell original.
            index_sha = None
        found = re.search(r"app\.[0-9a-f]{8}\.js", (index_text or "") + " " + Path(args.from_files).name)
        name = "js/" + (found.group() if found else Path(args.from_files).name)
        return bundle, index_text, index_sha, name, "archivos guardados desde el navegador por el usuario (sin descarga por script)"
    base = args.base_url or sources.get("docs_url", "").rsplit("index.html", 1)[0]
    index_url = urljoin(base, "index.html")
    raw = http_get(index_url)
    index_text = raw.decode("utf-8", "replace")
    ref = bundle_name_from_index(index_text)
    if not ref:
        raise RuntimeError("index.html no referencia js/app.<hash>.js (¿cambió la estructura de la doc?)")
    bundle = http_get(urljoin(index_url, ref))
    return bundle, index_text, sha256(raw), "js/" + ref.rsplit("/", 1)[-1], f"descarga directa de {index_url}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--check", action="store_true", help="no escribe; exit 1 si hay cambios")
    ap.add_argument("--from-files", metavar="APP_JS", help="usa este bundle local en vez de descargar (sin red)")
    ap.add_argument("--index", metavar="INDEX_HTML", help="index.html local (solo con --from-files)")
    ap.add_argument("--base-url", help="base de la doc (por defecto, la de sources.json; p. ej. la de Europa)")
    ap.add_argument("--ref-dir", help=argparse.SUPPRESS)  # pruebas: escribir en otra carpeta
    args = ap.parse_args()

    ref_dir = Path(args.ref_dir) if args.ref_dir else REF_DIR
    sources_file = ref_dir / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8"))
    class_file = ref_dir / "clasificacion.json"
    classes = json.loads(class_file.read_text(encoding="utf-8")).get("endpoints", {}) if class_file.exists() else {}

    print(f"Fuente: {sources.get('docs_url')}" + (f"  [local: {args.from_files}]" if args.from_files else ""))
    bundle, index_text, index_sha, bundle_name, origin = load_inputs(args, sources)
    parsed = parse_bundle(bundle.decode("utf-8"))
    doc = build_endpoints_doc(parsed, classes)
    state = new_state(parsed, doc, bundle, bundle_name, index_text, index_sha, origin)

    old = sources.get("synced") or {}
    first = old.get("status") != "SINCRONIZADO"
    nodes = state["nodos_arbol_lateral"]
    print(f"Doc {state['docs_version']} (última revisión {state['last_revision_in_history']}) | bundle {bundle_name} "
          f"({len(bundle):,} B) | {nodes} nodos del árbol | {len(parsed['sections'])} secciones | {len(doc['endpoints'])} endpoints"
          + (f" | fuera del árbol: {', '.join(parsed['not_in_menu'])}" if parsed["not_in_menu"] else ""))
    if parsed["missing_in_bundle"]:
        print("AVISO: ids del árbol sin módulo en el bundle: " + ", ".join(parsed["missing_in_bundle"]))
    changed = first or comparable(old) != comparable(state)
    if not changed:
        print("Sin cambios desde la última sincronización.")
        return 0
    print("Primera sincronización:" if first else "Cambios detectados:")
    for line in summarize_diff(old, state) or ["(sin diferencias de contenido comparables)"]:
        print("  " + line)
    if args.check:
        print("Ejecuta sin --check para actualizar el skill.")
        return 1

    meta = {"bundle_name": bundle_name, "bundle_sha256": state["bundle_sha256"],
            "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "api-doc.md").write_text(render_api_doc(parsed, meta), encoding="utf-8")
    (ref_dir / "endpoints.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ref_dir / "endpoints.md").write_text(render_endpoints_md(doc, meta), encoding="utf-8")
    state["synced_at"] = meta["synced_at"]
    sources["synced"] = state
    sources_file.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Actualizado: {ref_dir.name}/{{api-doc.md,endpoints.json,endpoints.md,sources.json}}")
    if state["sin_clasificar"]:
        print("AVISO: hay endpoints sin clasificar; se tratan como NO escribibles hasta añadirlos a clasificacion.json.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - CLI: mensaje claro en vez de traceback
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
