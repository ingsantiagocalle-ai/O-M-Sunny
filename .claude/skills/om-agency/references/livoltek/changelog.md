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

## 2026-10-05 — Documentación de la API v1.6.0 (desde archivos del usuario)

- **Contexto:** `api.livoltek-portal.com:8081` no respondía desde el contenedor (reset tras el ClientHello, también para la
  herramienta de lectura web; el mismo enlace abre en el navegador del usuario). El usuario guardó `js/app.9f56d8e5.js` e
  `index.html` desde su navegador y los subió a la sesión. `sources.json → network_sync` sigue **PENDIENTE**.
- **Añadido** `scripts/update_livoltek_api.py`: reconstruye la doc leyendo el bundle con un mini intérprete de JavaScript
  (solo biblioteca estándar). Comprobado contra Node: las **57 secciones** salen idénticas. Modos `--check` y `--from-files`.
- **Añadido** `api-doc.md` (los 54 nodos del árbol lateral + 3 secciones del bundle que no están en el árbol), con los tokens y
  contraseñas de ejemplo de la doc sustituidos por marcadores.
- **Añadido** `endpoints.json` y `endpoints.md` (44 endpoints; método, ruta y parámetros salen de la doc) y
  `clasificacion.json` (lectura/control, nivel B.5, ventanas, reglas de frecuencia e incoherencias de la doc; curado a mano).
- **Añadido** `limites.md`: 300/h por IP o Security ID, 300/h por interfaz, 100/h por token de cuenta, 3 simultáneas (429),
  token desde máximo 3 IP (428), ventanas de 7 días y de 2 años, y el límite por minuto de «usuarios especiales» que la
  petición original no mencionaba.
- **Verificado contra la doc** (y no asumido): login `POST /hess/api/login` con `{secuid,key}` y token en la cabecera
  `Authorization`; `userToken` y `userType` en la URL (`userType` 0 = usuario final, 1 = agente); los 14 endpoints de lectura de la lista;
  los de control (Sunspec y cargadores EV); MQTT en `mqtt://api.livoltek-portal.com:1883` (Europa: `api-eu`).
- **Hallazgos:** `sample/energy` y `sample/energy/site/day` son POST pero solo leen; `sunspec/command/info` lee pero exige
  `account`+`pwd`; `user/userTokenList` devuelve tokens en claro; el ejemplo `device/527/SN123456/details` del usuario es el de la
  página «Device Details»; la doc se contradice en rutas (alarm, oneDayFaultAlarm, siteOwner, chargeRecord) y en unidades (W frente a kW).
- **Modificado:** `sources.json` (versión y revisión declaradas ahora verificadas; servidores; `network_sync` conserva el aviso anterior).
- No se tocó SKILL.md, Deye ni sus scripts.

## 2026-10-05 — Diccionario Metrum → API → Modbus

- **Añadido** `diccionario-metrum-livoltek.md`: cada clave de Metrum con su campo de la API y su registro Modbus (escala, tipo, signo).
  **Todo marcado «sin verificar»**: no hay inversor Livoltek validado en vivo.
- **Hallazgos:** el PDF no trae SOC, tensión, corriente ni temperatura de batería ni energías de carga/descarga (solo la API);
  el ejemplo de `HisPowerflow` no cuadra físicamente (PV 2.953 kW, carga 0.061 kW y «Importing» 2.743 kW), así que `powerGridStatus` no sirve para
  fijar el signo de la red; los ejemplos de Sunspec usan los registros 45093 y 45018, que **no están** entre los 32 escribibles del PDF V1.01
  (por la lista blanca serían no escribibles).
