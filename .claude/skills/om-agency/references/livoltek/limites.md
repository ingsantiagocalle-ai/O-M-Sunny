# Límites de uso de la API Livoltek (doc v1.6.0)

> Cifras tomadas **literalmente** de la sección «Usage Limitations» y de las reglas por endpoint de la doc
> (`api-doc.md`, sección 12 y cada endpoint). Nada de esto se ha medido en vivo: todo está **sin verificar**
> hasta la prueba del Paso 8. La doc advierte que los límites «pueden cambiar en el futuro sin aviso».
> Este archivo es curado a mano; `update_livoltek_api.py` solo vigila si cambia el texto de la sección
> (campo `section_sha256.usageLimitations` de `sources.json`).

## 1. Resumen

| Límite | Valor (doc) | Si se excede | Cómo lo trata el adaptador |
|---|---|---|---|
| Llamadas por hora, por **IP de origen o Security ID** | **300** | HTTP **429** «too many requests» | presupuesto por hora, contador compartido |
| Todas las interfaces sumadas (misma IP o Security ID) | 300 / hora | 429 | ídem |
| **Cada interfaz** por separado | 300 / hora | 429 | contador por ruta |
| Todos los tokens de cuenta sumados | 300 / hora | 429 | ídem |
| **Cada token de cuenta** (`userToken`) | **100 / hora** | 429 | **límite efectivo: 100 llamadas/h** |
| Por minuto, «usuarios especiales» | 300 / minuto con el mismo Security ID | 429 | no aplica salvo cuenta especial |
| **Concurrencia** | **3** llamadas simultáneas desde la misma IP | 429 | **una llamada a la vez** |
| Un token de cuenta desde **IP o Security ID distintos** | máximo **3** | HTTP **428** «token occupied» | no se reintenta; mensaje claro |

Todo lo que pase de estos topes es responsabilidad del cliente: la doc dice que hay que implementar la regulación
(«throttling») en el lado del cliente. Si se insiste mucho, el sistema puede quedar temporalmente inoperante o
**bloquear el acceso a la API**.

## 2. Consecuencias prácticas

- **El tope que manda es 100 llamadas/hora por `userToken`**, no las 300 de la IP. Con una sola cuenta de agente
  (`userType=1`) y un solo `userToken`, ese es el presupuesto real de todo el skill por hora.
- **El login también gasta cupo** de IP/Security ID (300/h). Reutilizar el token del login; no repetirlo en cada llamada.
- **428 «token occupied»**: el token de cuenta ya se usa desde 3 IP (o Security ID) distintas y esta no es una de ellas.
  No se reintenta: se avisa al usuario. *Inferencia:* un contenedor en la nube que sale con una IP distinta en cada
  sesión **puede consumir uno de esos 3 cupos cada vez**; conviene usar siempre el mismo origen cuando sea posible.
- **429**: backoff exponencial (2, 4, 8, 16 s, máximo 4 intentos) y, si se agota, parar y avisar. No existe cabecera
  `Retry-After` documentada (sin verificar si la envían).
- **Una llamada a la vez**, siempre (la doc permite 3, pero además hay presupuestos por hora tan bajos que no hace falta).
- **Cachear lo histórico**: un dato de ayer no cambia; pedirlo dos veces solo gasta presupuesto.

## 3. Ventanas de fechas (por endpoint)

| Ventana | Endpoints (id) | Detalle (doc) |
|---|---|---|
| **7 días** | `siteHistoricalPowerFlow` (`HisPowerflow`), `siteHistoricalActivePower` (`power`), `deviceHistoricalAlarm` (`alarm`), `deviceTechnical` (`realTime`), `storageInformation` (`ESS`, historial) | `startTime` debe caer en los últimos 7 días. `realTime`: muestras cada 5 min. `alarm`: fechas `yyyy-MM-dd`. |
| **2 años** | `siteHistoricalSolar` (`solarEnergy`), `siteHistoricalGrid` (`utilityEnergy`) | Con `timeType` 0 (día) o 1 (semana): inicio **y** fin dentro de los últimos 2 años. Día: intervalo **≤ 31 días**. Semana: **≤ 180 días**. Mes (2) y año (3): la doc **no** fija límite (sin verificar). |
| 24 horas | `devicePowerReportQuery` (`sample/energy`) | El intervalo consultado no puede superar 24 h. |
| 1 día | `deviceOneDayFaultAlarm` | Un solo día (`dateTime`). |
| 1 mes | `siteDayEnergyQuery` (`sample/energy/site/day`) | `date = yyyy-MM`, un mes por consulta. |
| 3 días | `siteHistoricalSolarGeneration`, `siteHistoricalGridImport` | **No están en el árbol lateral de la doc**; sin parámetros de fecha. |

El adaptador parte cualquier rango más largo en tramos que respeten estas ventanas y rechaza (sin llamar a la red)
un inicio fuera de ventana, en vez de enviarlo y recibir un error.

## 4. Reglas de frecuencia propias de cada endpoint

| Endpoint (id) | Regla (doc) |
|---|---|
| `devicePowerReportQuery` | Cada dispositivo puede consultar el endpoint **una vez por hora**. |
| `siteDayEnergyQuery` | Cada `id` (sitio) **una vez por hora**. |
| `sunspecRebootInverter`, `sunspecRebootBMS`, `sunspecSomeParamInfo`, `sunspecSomeParamSetting` | Cada `id` **una vez por hora** (no se ejecutan desde el skill). |
| `generateUserToken` | 5 llamadas cada 15 min por terminal con el mismo nombre; máximo 5 tokens válidos por usuario (no se ejecuta). |
| `userTokenQuery` | 5 llamadas cada 15 min por terminal con el mismo nombre (no se ejecuta). |

## 5. Lo que la doc NO dice (sin verificar)

- Si la ventana horaria es **deslizante** o se reinicia en punto, y si las llamadas fallidas cuentan.
- Si «IP de origen **o** Security ID» significa que se aplica el que primero se agote, o ambos a la vez.
- Qué es un «usuario especial» para el límite por minuto, y si una cuenta de agente lo es.
- Si los límites son iguales en el servidor Internacional y en el de Europa.
- Tamaños máximos de página: solo se documentan 5, 10 (por defecto) y 30.
- Qué cuenta contra «cada interfaz»: la ruta con parámetros distintos, o la ruta completa.

## 6. Bloqueo de red observado (no es un límite de la doc)

El 2026-10-05, desde el contenedor de la sesión, `api.livoltek-portal.com:8081` cerró la conexión en el apretón
de manos TLS (0 bytes de respuesta; reset), mientras que el mismo enlace abría bien en un navegador del usuario.
Dos orígenes distintos (el contenedor y el servicio de lectura web) recibieron rechazo. Es coherente con un filtro
por IP de origen en el lado de Livoltek, pero **no está demostrado**. Hasta que se resuelva, las llamadas en vivo
deben hacerse desde un origen aceptado por Livoltek.
