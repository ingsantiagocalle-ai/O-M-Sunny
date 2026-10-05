# Historial de cambios de la integración Livoltek (skill om-agency)

Este archivo registra cambios **de este skill** (no el historial de Livoltek; ese vive en la documentación oficial y
lo comparará `update_livoltek_api.py --check`).

## 2026-10-05 — Arranque parcial (solo Modbus)

- Respaldo previo de la carpeta del skill (commit `fad374a`, 15 archivos, idéntica a la original).
- **Añadido** `modbus-gen2-registros.md` y `modbus-gen2.json`: resumen propio del PDF «Gen 2 Energy Storage Inverter External
  Communication Protocol» **V1.01** (2025-12-23): transporte, 130 registros RO, 32 RW con nivel de política B.5, estados
  de operación, 155 tipos de equipo, 51 normas de red (Colombia = código 35) y 277 códigos de falla. Nada validado en vivo.
- **Añadido** `sources.json` parcial (PDF registrado con su SHA-256; la parte de la API queda en `PENDIENTE`).
- **Bloqueado:** la documentación de la API (`https://api.livoltek-portal.com:8081/ess-api/index.html`) no se pudo leer desde el
  contenedor de la sesión: el proxy de salida cerró el túnel hacia `api.livoltek-portal.com:8081` (`www.livoltek-portal.com`
  por 443 y DeyeCloud sí responden). Por tanto **faltan** `api-doc.md`, `endpoints.json/md`, `limites.md`,
  `diccionario-metrum-livoltek.md`, `scripts/livoltek_adapter.py`, `scripts/update_livoltek_api.py` y la fusión en `SKILL.md`.
- No se tocó ningún archivo existente (SKILL.md, Deye, scripts de Deye).
