#!/usr/bin/env python3
"""Actualiza el Apéndice B (DeyeCloud) del skill om-agency desde la doc pública de Deye.

Fuente única: references/deye-cloud/sources.json, cuyo `docs_url` es
https://developer.deyecloud.com/api. La página /api es una SPA sin contenido
estático, así que se leen las fuentes publicadas bajo el mismo origen:

  * Servidor MCP público (Streamable HTTP): catálogo OpenAPI completo
    (list_deye_endpoints), lista de tools, centros de datos, versión.
  * Páginas /openmcp/docs/*.html: historial de cambios.
  * /openmcp/dist/deye-open-mcp-skill.zip: skill oficial de Deye.

No usa ni necesita credenciales de Deye (solo llamadas públicas).

Uso:
  python3 scripts/update_deye_api.py     # sincroniza y reescribe references/
  python3 scripts/update_deye_api.py --check  # solo informa si hay cambios (exit 1 si los hay)
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

SKILL_DIR = Path(__file__).resolve().parent.parent
REF_DIR = SKILL_DIR / "references" / "deye-cloud"
SOURCES_FILE = REF_DIR / "sources.json"
OFFICIAL_DIR = REF_DIR / "official-skill"
TIMEOUT = 60
UA = "om-agency-deye-updater/1.0"


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


class McpClient:
    """Cliente mínimo MCP Streamable HTTP (initialize + tools/call)."""

    def __init__(self, url: str):
        self.url = url
        self.session: str | None = None
        self._id = 0

    def _post(self, payload: dict) -> dict | None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": UA,
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            self.session = resp.headers.get("Mcp-Session-Id") or self.session
            body = resp.read().decode("utf-8")
        if "id" not in payload:  # notificación: sin respuesta útil
            return None
        for line in body.splitlines():
            if line.startswith("data:"):
                msg = json.loads(line[5:].strip())
                if msg.get("id") == payload["id"]:
                    return msg
        return json.loads(body) if body.strip().startswith("{") else None

    def request(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        msg = self._post(
            {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        )
        if not msg or "error" in msg:
            raise RuntimeError(f"MCP {method} falló: {msg}")
        return msg["result"]

    def initialize(self) -> dict:
        res = self.request(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "deye-skill-updater", "version": "1.0"},
            },
        )
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return res

    def call(self, name: str, arguments: dict | None = None):
        res = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        if res.get("isError"):
            raise RuntimeError(f"tool {name} devolvió error: {res}")
        return res

    def call_json(self, name: str, arguments: dict | None = None):
        """Devuelve el contenido de la tool como JSON (uno por bloque de texto)."""
        res = self.call(name, arguments)
        blocks = [json.loads(c["text"]) for c in res.get("content", []) if c.get("text")]
        return blocks[0] if len(blocks) == 1 else blocks


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def html_to_text(raw: str) -> str:
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S)
    raw = re.sub(r"</(p|div|h\d|li|tr|section|ul)>|<br\s*/?>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def md_cell(value) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def type_of(prop: dict) -> str:
    if "$ref" in prop:
        return prop["$ref"].rsplit("/", 1)[-1]
    typ = prop.get("type", "")
    if typ == "array":
        return f"array[{type_of(prop.get('items', {}))}]"
    return typ


def schema_rows(schema: dict) -> list[str]:
    required = set(schema.get("required", []))
    rows = []
    for name, prop in schema.get("properties", {}).items():
        notes = []
        if prop.get("description"):
            notes.append(prop["description"])
        if prop.get("enum"):
            notes.append("valores: " + ", ".join(map(str, prop["enum"])))
        if "example" in prop:
            notes.append(f"ej: {prop['example']}")
        rows.append(
            f"| `{name}` | {md_cell(type_of(prop))} | {'sí' if name in required else ''} "
            f"| {md_cell('; '.join(notes))} |"
        )
    return rows


def render_endpoints_md(endpoints: list[dict], meta: dict) -> str:
    out = [
        "# Catálogo de endpoints DeyeCloud OpenAPI",
        "",
        f"> Generado por `scripts/update_deye_api.py` desde {meta['docs_url']} "
        f"(servidor MCP v{meta['server_version']}, sync {meta['synced_at']}). **No editar a mano.**",
        "",
        "Todos los endpoints requieren el header `Authorization: Bearer <token>` salvo "
        "`/v1.0/account/token` (que usa `appId` por query). Base URL por región: ver SKILL.md.",
        "",
    ]
    by_tag: dict[str, list[dict]] = {}
    for ep in endpoints:
        by_tag.setdefault((ep.get("tags") or ["Otros"])[0], []).append(ep)
    for tag in sorted(by_tag):
        out += [f"## {tag}", ""]
        for ep in sorted(by_tag[tag], key=lambda e: e["path"]):
            out += [f"### `{ep['method']} {ep['path']}`", "", ep.get("summary", "").strip(), ""]
            non_body = [
                p for p in ep.get("parameters", [])
                if p.get("in") != "body" and p.get("name", "").lower() != "authorization"
            ]
            if non_body:
                out += ["| Param | En | Req. | Tipo | Descripción |", "|---|---|---|---|---|"]
                for p in non_body:
                    out.append(
                        f"| `{p['name']}` | {p['in']} | {'sí' if p.get('required') else ''} "
                        f"| {md_cell(p.get('type'))} | {md_cell(p.get('description'))} |"
                    )
                out.append("")
            for p in ep.get("parameters", []):
                if p.get("in") == "body":
                    schema = p.get("resolvedSchema") or {}
                    title = schema.get("title") or type_of(p.get("schema", {}))
                    out += [f"Body (`{title}`):", ""]
                    rows = schema_rows(schema)
                    if rows:
                        out += ["| Campo | Tipo | Req. | Notas |", "|---|---|---|---|", *rows]
                    else:
                        out.append("_Sin campos documentados (JSON libre)._")
                    out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_tools_md(tools: list[dict], meta: dict) -> str:
    out = [
        "# Herramientas del servidor Deye Open MCP",
        "",
        f"> Generado por `scripts/update_deye_api.py` (servidor v{meta['server_version']}, "
        f"{len(tools)} tools, sync {meta['synced_at']}). **No editar a mano.**",
        "",
        "| Tool | Argumentos | Descripción |",
        "|---|---|---|",
    ]
    for t in tools:
        props = t.get("inputSchema", {}).get("properties", {})
        required = set(t.get("inputSchema", {}).get("required", []))
        args = ", ".join(f"`{k}`{'*' if k in required else ''}" for k in props) or "—"
        desc = (t.get("description") or "").strip().splitlines()[0] if t.get("description") else ""
        out.append(f"| `{t['name']}` | {args} | {md_cell(desc)} |")
    out += ["", "`*` = obligatorio."]
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# Swagger (/v2/api-docs): trae los límites y la semántica (granularity, ventanas)
# que NO están en el catálogo MCP. Deye lo publica con un typo que rompe el JSON
# (p. ej. "example":[12583SS] sin comillas), así que se reintenta con reparación.
# --------------------------------------------------------------------------- #
def parse_swagger(raw: str) -> tuple[dict, bool]:
    try:
        return json.loads(raw), False
    except json.JSONDecodeError:
        def quote_bare(m: re.Match) -> str:
            tok = m.group(1)
            if tok in ("true", "false", "null") or re.fullmatch(r"-?\d+(\.\d+)?([eE][+-]?\d+)?", tok):
                return m.group(0)  # literal JSON válido: no tocar
            return f'["{tok}"]'

        fixed = re.sub(r'\[\s*([^\[\]"{},:\s]+)\s*\]', quote_bare, raw)
        return json.loads(fixed), True


def swagger_endpoints(spec: dict) -> list[str]:
    return sorted(
        f"{m.upper()} {p}"
        for p, ops in spec.get("paths", {}).items()
        for m in ops
        if m in ("get", "post", "put", "delete", "patch")
    )


def render_swagger_md(spec: dict, meta: dict, repaired: bool) -> str:
    out = [
        "# Notas por endpoint (Swagger /v2/api-docs)",
        "",
        f"> Generado por `scripts/update_deye_api.py` desde {meta['swagger_url']} "
        f"(sync {meta['synced_at']}{'; JSON reparado por typo de Deye' if repaired else ''}). "
        "**No editar a mano.** Aquí viven los límites y la semántica que el catálogo MCP no trae "
        "(significado de `granularity`, ventanas máximas, etc.).",
        "",
    ]
    for path in sorted(spec.get("paths", {})):
        for method, op in spec["paths"][path].items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue
            out += [f"### `{method.upper()} {path}`", "", (op.get("summary") or "").strip(), ""]
            desc = (op.get("description") or "").replace("<br/>", "\n").strip()
            if desc:
                out += [desc, ""]
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# Official skill zip
# --------------------------------------------------------------------------- #
def extract_official_skill(zip_bytes: bytes) -> list[str]:
    written = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            target = (OFFICIAL_DIR / info.filename).resolve()
            if OFFICIAL_DIR.resolve() not in target.parents:  # zip-slip
                raise RuntimeError(f"Ruta insegura en zip: {info.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(info))
            target.chmod(0o644)
            written.append(str(target.relative_to(SKILL_DIR)))
    return sorted(written)


def parse_official_version(skill_md: str) -> str:
    m = re.search(r"^version:\s*(\S+)", skill_md, flags=re.M)
    return m.group(1) if m else "desconocida"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()[:16]


def summarize_diff(old: dict, new: dict) -> list[str]:
    lines = []
    for key, label in (
        ("endpoints", "endpoints"), ("tools", "tools MCP"), ("swagger_endpoints", "endpoints Swagger")
    ):
        before, after = set(old.get(key, [])), set(new.get(key, []))
        if added := sorted(after - before):
            lines.append(f"+ {label} nuevos: {', '.join(added)}")
        if removed := sorted(before - after):
            lines.append(f"- {label} eliminados: {', '.join(removed)}")
    for key in (
        "server_version", "official_skill_version", "catalog_hash", "changelog_hash", "swagger_hash"
    ):
        if old.get(key) != new.get(key):
            lines.append(f"~ {key}: {old.get(key)} -> {new.get(key)}")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--check", action="store_true", help="no escribe; exit 1 si hay cambios")
    args = ap.parse_args()

    sources = json.loads(SOURCES_FILE.read_text())
    docs_url = sources["docs_url"]
    origin = "{0.scheme}://{0.netloc}".format(urlsplit(docs_url))

    print(f"Fuente: {docs_url}")
    http_get(docs_url)  # verifica que el link siga vivo
    mcp = McpClient(urljoin(origin, sources["mcp_path"]))
    init = mcp.initialize()
    endpoints = mcp.call_json("list_deye_endpoints")
    data_centers = mcp.call_json("list_data_centers")
    server_info = mcp.call_json("get_server_info")
    tools = mcp.request("tools/list")["tools"]
    changelog_txt = html_to_text(
        http_get(urljoin(origin, sources["changelog_path"])).decode("utf-8")
    )
    zip_bytes = http_get(urljoin(origin, sources["skill_zip_path"]))
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        official_md = zf.read("deye-open-mcp/SKILL.md").decode("utf-8")

    if not isinstance(endpoints, list) or not endpoints:
        raise RuntimeError("Catálogo de endpoints vacío o con formato inesperado")

    swagger_url = (
        sources["data_centers"][sources.get("swagger_data_center", "am")] + sources["swagger_path"]
    )
    swagger, swagger_repaired = parse_swagger(http_get(swagger_url).decode("utf-8"))
    sw_eps = swagger_endpoints(swagger)
    catalog_eps = {f"{e['method']} {e['path']}" for e in endpoints}

    new_state = {
        "swagger_endpoints": sw_eps,
        "swagger_only": sorted(set(sw_eps) - catalog_eps),   # en Swagger pero no en el catálogo MCP
        "swagger_hash": sha(json.dumps(swagger, sort_keys=True)),
        "server_version": server_info.get("server_version"),
        "recommended_skill_version": server_info.get("recommended_skill_version"),
        "official_skill_version": parse_official_version(official_md),
        "endpoints": sorted(f"{e['method']} {e['path']}" for e in endpoints),
        "tools": sorted(t["name"] for t in tools),
        "catalog_hash": sha(json.dumps(endpoints, sort_keys=True)),
        "changelog_hash": sha(changelog_txt),
        "skill_zip_hash": sha(zip_bytes),
        "data_centers": data_centers,
    }
    old_state = sources.get("synced", {})
    diff = summarize_diff(old_state, new_state)
    changed = any(old_state.get(k) != new_state[k] for k in new_state)

    print(
        f"MCP {init['serverInfo']['name']} v{new_state['server_version']} | "
        f"{len(endpoints)} endpoints | {len(tools)} tools | "
        f"skill oficial v{new_state['official_skill_version']} | "
        f"Swagger {len(sw_eps)} endpoints"
        + (f" (solo en Swagger: {', '.join(new_state['swagger_only'])})" if new_state["swagger_only"] else "")
        + (" [JSON reparado]" if swagger_repaired else "")
    )
    if not changed:
        print("Sin cambios desde la última sincronización.")
        return 0
    print("Cambios detectados:" if old_state else "Primera sincronización:")
    for line in diff or ["(solo cambió contenido interno del catálogo)"]:
        print("  " + line)
    if args.check:
        print("Ejecuta sin --check para actualizar el skill.")
        return 1

    meta = {
        "docs_url": docs_url,
        "server_version": new_state["server_version"],
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "swagger_url": swagger_url,
    }
    REF_DIR.mkdir(exist_ok=True)
    (REF_DIR / "swagger-notes.md").write_text(render_swagger_md(swagger, meta, swagger_repaired))
    (REF_DIR / "endpoints.json").write_text(
        json.dumps(endpoints, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    (REF_DIR / "endpoints.md").write_text(render_endpoints_md(endpoints, meta))
    (REF_DIR / "mcp-tools.md").write_text(render_tools_md(tools, meta))
    (REF_DIR / "changelog.md").write_text(
        "# Historial de cambios de Deye Open MCP\n\n"
        f"> Copia de {urljoin(origin, sources['changelog_path'])} (sync {meta['synced_at']}).\n\n"
        + changelog_txt + "\n"
    )
    for stale in OFFICIAL_DIR.rglob("*") if OFFICIAL_DIR.exists() else []:
        if stale.is_file():
            stale.unlink()
    written = extract_official_skill(zip_bytes)

    sources["synced"] = {**new_state, "synced_at": meta["synced_at"]}
    SOURCES_FILE.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n")
    print(f"Actualizado: references/deye-cloud/{{endpoints.md,endpoints.json,swagger-notes.md,mcp-tools.md,changelog.md}} y {len(written)} archivos oficiales.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - CLI: mensaje claro en vez de traceback
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
