# Catálogo de endpoints Livoltek (API ESS v1.6.0)

> Generado por `scripts/update_livoltek_api.py` desde `js/app.9f56d8e5.js` (2026-10-05 21:09 UTC). **No editar a mano**: método, ruta y parámetros salen de la doc; la clasificación (lectura/control, nivel B.5, ventanas, incoherencias) sale de `clasificacion.json`.

## Acceso

- Solo HTTPS. Servidores: **International** `https://api.livoltek-portal.com:8081` y **Europa** `https://api-eu.livoltek-portal.com:8081`; prefijo común `/hess/api`.
- `POST /hess/api/login` con `{"secuid","key"}` → `data.data` = token. Ese token va en la cabecera `Authorization` (sin prefijo `Bearer`) en todo lo demás.
- Casi todas las consultas llevan además `userToken` en la URL (token de cuenta o de sitio generado en el portal) y `userType` (0 = usuario final, por defecto; **1 = agente/instalador**).
- Parámetros con espacios o caracteres especiales deben ir codificados en URL (`startTime=2025-01-18%2000:00:00`).

## Resumen

| # | Id | Método y ruta | Clase | Nivel B.5 | `userToken` | `account`+`pwd` | Ventana / regla | En árbol |
|---|---|---|---|---|---|---|---|---|
| 1 | `siteList` | `GET /hess/api/userSites/list` | **lectura** | 0 | sí |  |  | sí |
| 2 | `deviceList` | `GET /hess/api/device/{siteId}/list` | **lectura** | 0 | sí |  |  | sí |
| 3 | `currentPowerFlow` | `GET /hess/api/site/{siteId}/curPowerflow` | **lectura** | 0 | sí |  |  | sí |
| 4 | `deviceGenerationOrConsumption` | `GET /hess/api/device/{deviceId}/realElectricity` | **lectura** | 0 | sí |  |  | sí |
| 5 | `siteDetails` | `GET /hess/api/site/{siteId}/details` | **lectura** | 0 | sí |  |  | sí |
| 6 | `siteInstaller` | `GET /hess/api/site/{siteId}/siteInstaller` | **lectura** | 0 | sí |  |  | sí |
| 7 | `siteGenerationOverview` | `GET /hess/api/site/{siteId}/overview` | **lectura** | 0 | sí |  |  | sí |
| 8 | `siteHistoricalPowerFlow` | `GET /hess/api/site/{siteId}/HisPowerflow` | **lectura** | 0 | sí |  | startTime debe estar dentro de los últimos 7 días (doc). Marcas de tiempo en milisegundos (13 dígitos). | sí |
| 9 | `siteHistoricalActivePower` | `GET /hess/api/site/{siteId}/power` | **lectura** | 0 | sí |  | startTime debe estar dentro de los últimos 7 días (doc). | sí |
| 10 | `deviceHistoricalAlarm` | `GET /hess/api/device/{siteId}/{serialNumber}/alarm` | **lectura** | 0 | sí |  | Alarmas de los últimos 7 días; startTime y endTime con formato yyyy-MM-dd. | sí |
| 11 | `siteSocialContribution` | `GET /hess/api/site/{siteId}/socialContr` | **lectura** | 0 | sí |  |  | sí |
| 12 | `storageInformation` | `GET /hess/api/site/{siteId}/ESS` | **lectura** | 0 | sí |  | historyMap trae potencia, tensión y SOC de los últimos 7 días y la carga/descarga diaria de esos 7 días (doc). | sí |
| 13 | `deviceDetails` | `GET /hess/api/device/{siteId}/{serialNumber}/details` | **lectura** | 0 | sí |  |  | sí |
| 14 | `deviceTechnical` | `GET /hess/api/device/{siteId}/{serialNumber}/realTime` | **lectura** | 0 | sí |  | Últimos 7 días; muestras cada 5 minutos; startTime y endTime opcionales con formato yyyy-MM-dd HH:mm:ss (codificar el espacio). | sí |
| 15 | `siteHistoricalSolar` | `GET /hess/api/site/{siteId}/solarEnergy` | **lectura** | 0 | sí |  | timeType 0 (día) o 1 (semana): inicio y fin dentro de los últimos 2 años.; timeType 0: intervalo ≤ 31 días. timeType 1: intervalo ≤ 180 días.; timeType 2 (mes) y 3 (año): la doc no fija límite (SIN VERIFICAR). | sí |
| 16 | `siteHistoricalGrid` | `GET /hess/api/site/{siteId}/utilityEnergy` | **lectura** | 0 | sí |  | timeType 0 (día) o 1 (semana): inicio y fin dentro de los últimos 2 años.; timeType 0: intervalo ≤ 31 días. timeType 1: intervalo ≤ 180 días.; timeType 2 (mes) y 3 (año): la doc no fija límite (SIN VERIFICAR). | sí |
| 17 | `userLoginAndToken` | `POST /hess/api/login` | **lectura** | 0 |  |  |  | sí |
| 18 | `chargingStationCreation` | `POST /hess/api/chargeSite/create` | **control** | 2 | sí | sí |  | sí |
| 19 | `chargingStationQuery` | `POST /hess/api/chargeSite/querySite` | **control** | 2 | sí | sí |  | sí |
| 20 | `chargingStationUpdate` | `POST /hess/api/chargeSite/update` | **control** | 2 | sí | sí |  | sí |
| 21 | `chargingStationDeletion` | `POST /hess/api/chargeSite/disable` | **control** | 2 | sí | sí |  | sí |
| 22 | `chargingDeviceCreation` | `POST /hess/api/chargeDevice/create` | **control** | 2 | sí | sí |  | sí |
| 23 | `chargingDeviceQuery` | `POST /hess/api/chargeDevice/queryEv` | **control** | 2 | sí | sí |  | sí |
| 24 | `chargingDeviceDelete` | `POST /hess/api/chargeDevice/disable` | **control** | 2 | sí | sí |  | sí |
| 25 | `chargingRecordQuery` | `POST /hess/api/chargeRecord` | **control** | 2 | sí | sí |  | sí |
| 26 | `chargingStationStartOrStop` | `POST /hess/api/chargeCommandDown` | **control** | 2 | sí | sí |  | sí |
| 27 | `chargingScheduleSettings` | `POST /hess/api/chargeSchedule` | **control** | 2 | sí | sí |  | sí |
| 28 | `mqttPushDeviceAlarm` | MQTT (solo doc) | **lectura** | 0 |  |  |  | sí |
| 29 | `mqttPushDeviceWorkingStatus` | MQTT (solo doc) | **lectura** | 0 |  |  |  | sí |
| 30 | `queryPowerStationId` | `GET /hess/api/site/{serialNumber}` | **lectura** | 0 | sí |  |  | sí |
| 31 | `siteOwner` | `GET /hess/api/site/{siteId}/siteOwner` | **lectura** (sensible) | 0 | sí |  |  | sí |
| 32 | `deviceBasicData` | `GET /hess/api/device/basicData` | **lectura** | 0 | sí |  |  | sí |
| 33 | `deviceOneDayFaultAlarm` | `GET /hess/api/device/{siteId}/{serialNumber}/oneDayFaultAlarm` | **lectura** | 0 | sí |  | Un solo día por consulta (dateTime = yyyy-MM-dd). | sí |
| 34 | `generateUserToken` | `POST /hess/api/user/userToken` | **control** | 3 |  | sí | 5 llamadas cada 15 min por terminal con el mismo nombre; máx. 5 tokens válidos por usuario (doc). | sí |
| 35 | `userTokenQuery` | `POST /hess/api/user/userTokenList` | **lectura** (sensible) | 0 |  | sí | 5 llamadas cada 15 min por terminal con el mismo nombre (doc). | sí |
| 36 | `devicePowerReportQuery` | `POST /hess/api/sample/energy` | **lectura** | 0 | sí |  | El intervalo de consulta no puede superar 24 horas (doc).; Cada dispositivo solo puede consultar este endpoint una vez por hora (doc). | sí |
| 37 | `siteDayEnergyQuery` | `POST /hess/api/sample/energy/site/day` | **lectura** | 0 | sí |  | Un mes por consulta (date = yyyy-MM); devuelve el detalle día a día.; Cada id solo puede consultar este endpoint una vez por hora (doc). | sí |
| 38 | `sunspecRebootInverter` | `POST /hess/api/sunspec/command/rebootInverter` | **control** | 2 | sí | sí | Cada id solo puede llamar este endpoint una vez por hora (doc). | sí |
| 39 | `sunspecRebootBMS` | `POST /hess/api/sunspec/command/rebootBMS` | **control** | 2 | sí | sí | Cada id solo puede llamar este endpoint una vez por hora (doc). | sí |
| 40 | `sunspecSomeParamInfo` | `POST /hess/api/sunspec/command/info` | **control** | 2 | sí | sí | Cada id solo puede llamar este endpoint una vez por hora (doc). | sí |
| 41 | `sunspecSomeParamSetting` | `POST /hess/api/sunspec/command/send` | **control** | 2 o 3 según el registro | sí | sí | Cada id solo puede llamar este endpoint una vez por hora (doc). | sí |
| 42 | `queryStationStatistics` | `GET /hess/api/powerStationStatistics` | **lectura** | 0 |  |  |  | **no** |
| 43 | `siteHistoricalGridImport` | `GET /hess/api/site/{siteId}/reissueUtilityEnergy` | **lectura** | 0 | sí |  | Últimos 3 días (sin parámetros de fecha). | **no** |
| 44 | `siteHistoricalSolarGeneration` | `GET /hess/api/site/{siteId}/reissueSolarEnergy` | **lectura** | 0 | sí |  | Últimos 3 días (sin parámetros de fecha). | **no** |

## Incoherencias detectadas en la propia doc

La doc se contradice a sí misma en estos puntos. Se anotan, **no se corrigen**; hay que confirmarlas en vivo.

- `siteList`: active se pide con 0/1 pero la respuesta lo describe como 2/3.
- `siteList`: El ejemplo mezcla espacios en los parámetros (sortField= pvCapacity): codificar la URL.
- `currentPowerFlow`: La descripción dice «parameter unit (W)» pero el ejemplo trae 0.006 y -0.156, que parecen kW. Unidad SIN VERIFICAR.
- `currentPowerFlow`: En el ejemplo energyPower = -0.156 con energyStatus = disCharging: sugiere + = carga y − = descarga. Signo SIN VERIFICAR.
- `currentPowerFlow`: pvStatus, powerGridStatus y loadStatus figuran como «Under developing» y llegan null en el ejemplo; sin medidor no hay datos de red.
- `siteDetails`: powerStationType se documenta con códigos 1-4 pero el ejemplo devuelve texto localizado (chino).
- `siteDetails`: powerStationStatus es entero en la tabla y cadena en el ejemplo.
- `siteGenerationOverview`: El ejemplo escribe etotalToGrid y la tabla eTotalToGrid.
- `siteHistoricalPowerFlow`: La prosa dice «unit (W)» pero la tabla de campos dice «Unit: kW». Unidad SIN VERIFICAR.
- `siteHistoricalPowerFlow`: userToken es obligatorio en la tabla pero el ejemplo no lo incluye; el ejemplo también escribe «pointInterval =1» con espacio.
- `siteHistoricalPowerFlow`: pointInterval 1 y 2 llevan una marca «(No)» sin explicar (¿no soportados?).
- `siteHistoricalActivePower`: La prosa dice «unit (W)» y la tabla «Unit: kW».
- `siteHistoricalActivePower`: El ejemplo omite userToken, que la tabla da como obligatorio.
- `deviceHistoricalAlarm`: La línea URL dice /hess/api/device/{siteId}/{serialNumber}/alarm pero el ejemplo usa /hess/api/site/123/SN10203/alarm. El adaptador usa la ruta de la línea URL; CONFIRMAR EN VIVO.
- `deviceHistoricalAlarm`: serialNumber figura como Integer en la tabla (es el SN, texto). page tiene valor por defecto 0 en la tabla y 1 en el ejemplo.
- `deviceHistoricalAlarm`: alarmType se documenta como Notice/fault pero el ejemplo devuelve «0»; alarmStatus llega null («Under developing»).
- `siteSocialContribution`: siteId no está en la tabla de parámetros y el ejemplo deja {siteId} sin sustituir.
- `storageInformation`: Erratas: energyVolage; el ejemplo muestra currentSoc que la tabla no lista; el JSON de ejemplo está mal formado.
- `storageInformation`: batterySn y cycleCount figuran como «underdeveloping».
- `deviceDetails`: device/basicData devuelve runningStatus como texto («Offline») y aquí se documenta como código numérico.
- `deviceDetails`: El ejemplo anida runningStatusVoMap, que la tabla no describe.
- `deviceTechnical`: Las descripciones de rCurrent, sVoltage, sCurrent, tVoltage y tCurrent están desplazadas (p. ej. rCurrent = «PhaseB voltage»). No fiarse de la descripción: confirmar fase por fase en vivo.
- `deviceTechnical`: El ejemplo de respuesta usa claves en minúscula (rvoltage, rcurrent…) y la tabla en camelCase; leer sin distinguir mayúsculas.
- `deviceTechnical`: Los ejemplos de URL contienen espacios sin codificar y la errata girdFrequency.
- `siteHistoricalSolar`: El ejemplo de URL está mal formado (/site/527/SN123456？userToken…) y no coincide con /site/{siteId}/solarEnergy.
- `siteHistoricalSolar`: La unidad de powerGeneration no está documentada.
- `siteHistoricalGrid`: La descripción habla de Wh pero los ejemplos (47.2) parecen kWh. Unidad SIN VERIFICAR.
- `siteHistoricalGrid`: El ejemplo escribe «negetive» y la tabla «negative»; el ejemplo de URL termina en «&userType» sin valor.
- `siteHistoricalGrid`: endTime figura como obligatorio y a la vez «option, default (current day)».
- `userLoginAndToken`: La URL se escribe «hess/api /login» (espacio y sin barra inicial).
- `userLoginAndToken`: La tabla de respuesta tiene erratas (mssage, messgae, tring) y repite data.
- `chargingDeviceQuery`: La tabla usa pageSize/start y el ejemplo page/size; el ejemplo de cuerpo tiene una coma final (JSON inválido).
- `chargingRecordQuery`: La línea URL dice /hess/api/chargeRecord y el ejemplo /hess/api/chargeDevice/chargeRecord.
- `queryPowerStationId`: La doc no indica el método ni la cabecera Authorization: el método se infiere GET (el enlace de la doc apunta a la operación querySiteIdUsingGET).
- `siteOwner`: La línea URL dice /hess/api/site/{siteId}/siteOwner y los ejemplos /hess/api/site/991/customer.
- `deviceBasicData`: La tabla escribe el parámetro «Sn» y el ejemplo «sn».
- `deviceBasicData`: Los ejemplos de fecha llevan espacios (codificar la URL).
- `deviceBasicData`: runningStatus llega como texto («Offline»), no como código.
- `deviceOneDayFaultAlarm`: Igual que deviceHistoricalAlarm: la línea URL usa device/{siteId}/{sn}/oneDayFaultAlarm y el ejemplo site/123/SN10203/ oneDayFaultAlarm (con un espacio).
- `devicePowerReportQuery`: El ejemplo de Europa usa /hess/api/user/sample/energy y el International /hess/api/sample/energy.
- `siteDayEnergyQuery`: El ejemplo de cuerpo está mal formado («date2025-04» sin dos puntos).
- `siteDayEnergyQuery`: El ejemplo de Europa usa /hess/api/user/sample/energy/site/day.
- `sunspecSomeParamInfo`: El ejemplo de respuesta está truncado con «………».
- `siteHistoricalGridImport`: El ejemplo escribe «negetive»; las URL de ejemplo llevan espacios.

## Detalle por endpoint

### 1. Site List — `siteList`

- **GET** `/hess/api/userSites/list`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: size solo admite 5, 10 (por defecto) o 30; page empieza en 1.
- Nota: Con userType=1 (agente) se espera ver los sitios de los clientes de la cuenta de agente: sin verificar.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0 - end-user（default)<br>1 - agent |
| `powerStationType` | query | no | String | Site type<br>1-Grid-tied solar system<br>2-Solar storage system<br>3-EV charging hub<br>4-EV charging hub with solar storage; Parameter:<br>1-Grid-tied solar system<br>2-Solar storage system<br>3-EV charging hub<br>4-EV charging hub with solar storage |
| `createTime` | query | no | Long | The time when this site is being added to the system; Search text for this site |
| `active` | query | no | Integer | If the site is active<br>0-not active<br>1-active |
| `country` | query | no | String | The region where this site located; Search text for this site |
| `sortField` | query | no | String | A sorting option for this site list:<br>- pvCapacity<br>- updateTime |
| `sortType` | query | no | String | Sort order for the sort property. Allowed values ar ASC (ascending) and DESC (descending). |
| `page` | query | sí | Int | The first site index to be returned in the results, default=1 |
| `size` | query | sí | Int | Pagesize of each page:<br>-5<br>-10 (default)<br>-30 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/userSites/list?userToken=1&createTime=1659705100000&active=1&sortType=asc&page=10&size=10&userType=1& powerStationType=1& country=CN& sortField= pvCapacity

### 2. Device List — `deviceList`

- **GET** `/hess/api/device/{siteId}/list`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: Devuelve id (número de equipo), inverterSn (SN de cualquier equipo: inversor, cargador, colector), productType y deviceManufacturer. size solo 5, 10 o 30.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `page` | query | sí | Int | The first site index to be returned in the results, default=1 |
| `size` | query | sí | Int | Pagesize of each page:<br>-5<br>-10 (default)<br>-30 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/device/527/list?userToken=1&page=1&size=10&userType=1

### 3. Current power flow — `currentPowerFlow`

- **GET** `/hess/api/site/{siteId}/curPowerflow`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: Fuente de bat_power_w, pv_power_w, load_power_w, grid_power_w y soc_pct del adaptador.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/527/curPowerflow?userToken=1&userType=1

### 4. Device generation or consumption — `deviceGenerationOrConsumption`

- **GET** `/hess/api/device/{deviceId}/realElectricity`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: Se llama con deviceId (el id numérico de device/{siteId}/list), NO con el SN. Contadores acumulados (kWh).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `deviceId` | ruta | sí | String | Device ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/device/22018/realElectricity?userToken=1&userType=1

### 5. Site Details — `siteDetails`

- **GET** `/hess/api/site/{siteId}/details`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `siteId` | ruta | sí | String | Site ID |
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/details?userToken=1&userType=1

### 6. Site Installer — `siteInstaller`

- **GET** `/hess/api/site/{siteId}/siteInstaller`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/siteInstaller?userToken=1&userType=1

### 7. Site generation overview — `siteGenerationOverview`

- **GET** `/hess/api/site/{siteId}/overview`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: Fuente de las energías diaria, mensual, anual y de vida del sitio (kWh según la tabla).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/overview?userToken=1&userType=1

### 8. Site Historical Power Flow — `siteHistoricalPowerFlow`

- **GET** `/hess/api/site/{siteId}/HisPowerflow`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: startTime debe estar dentro de los últimos 7 días (doc). Marcas de tiempo en milisegundos (13 dígitos).
- Nota: pointInterval: 0 = cada 5 min, 1 = cada 10 min (por defecto), 2 = cada 15 min.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `pointInterval` | query | sí | Integer | Sampling accuracy<br>0- Every 5 minutes<br>1- Every 10 minutes(default)（No）<br>2- Every 15 minutes（No） |
| `startTime` | query | sí | Long | Start time for query, which should be in recent 7 days; Timestamp:13 |
| `endTime` | query | sí | Long | End up time for query |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/HisPowerflow?pointInterval =1&startTime=1659710500000&endTime=1659750500000&userType=1

### 9. Site Historical Active Power — `siteHistoricalActivePower`

- **GET** `/hess/api/site/{siteId}/power`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: startTime debe estar dentro de los últimos 7 días (doc).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `pointInterval` | query | sí | Integer | Sampling accuracy<br>0- Every 5 minutes<br>1- Every 10 minutes（No）<br>2- Every 15 minutes（No） |
| `startTime` | query | sí | Long | Start time for query, which should be in recent 7 days |
| `endTime` | query | sí | Long | End up time for query |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/power?pointInterval =1&startTime=1659102500000&endTime=1659202500000&userType=1

### 10. Device Historical Alarm — `deviceHistoricalAlarm`

- **GET** `/hess/api/device/{siteId}/{serialNumber}/alarm`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: Alarmas de los últimos 7 días; startTime y endTime con formato yyyy-MM-dd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `serialNumber` | ruta | sí | Integer | Device SN |
| `size` | query | sí | Integer | Pagesize of each page,<br>-5<br>-10 (default)<br>-30 |
| `page` | query | sí | Integer | The first site index to be returned in the results, default=0 |
| `startTime` | query | sí | String | Start time for query, which should be in recent 7 days; e.g. 2022-01-01 |
| `endTime` | query | sí | String | End up time for query; e.g. 2022-01-07 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/SN10203/alarm?startTime=2022-01-01&endTime=2022-01-07&page=1&size=10&userToken=*****&userType=1

### 11. Site Social Contribution — `siteSocialContribution`

- **GET** `/hess/api/site/{siteId}/socialContr`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/{siteId}/socialContr?userToken=1&userType=1

### 12. Storage Information — `storageInformation`

- **GET** `/hess/api/site/{siteId}/ESS`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: historyMap trae potencia, tensión y SOC de los últimos 7 días y la carga/descarga diaria de esos 7 días (doc).
- Nota: Ruta ESS en mayúsculas: /hess/api/site/{siteId}/ESS. Capacidad BMS en Ah.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/527/ESS?userToken=1&userType=1

### 13. Device Details — `deviceDetails`

- **GET** `/hess/api/device/{siteId}/{serialNumber}/details`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: runningStatus: 0 Normal, 1 Standby, 2 Fault, 3 Offline, 4 Self-test, 5 Upgrading. Es el endpoint del ejemplo device/527/SN123456/details.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `serialNumber` | ruta | sí | String | Device serial number |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/device/527/SN123456/details?userToken=1&userType=1

### 14. Device technical parameters in recent 7 days — `deviceTechnical`

- **GET** `/hess/api/device/{siteId}/{serialNumber}/realTime`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: Últimos 7 días; muestras cada 5 minutos; startTime y endTime opcionales con formato yyyy-MM-dd HH:mm:ss (codificar el espacio).
- Nota: La respuesta viene agrupada por día: data = {marca_de_tiempo_del_día: [muestras]}.
- Nota: Unidades de las magnitudes NO documentadas: SIN VERIFICAR.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `serialNumber` | ruta | sí | String | Device serial number |
| `startTime` | query | no | String | Start time; 2025-01-18 00:00:00 |
| `endTime` | query | no | String | End time; 2025-01-18 23:59:59 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/device/527/SN123456/realTime?userToken=1&userType=1 &startTime=2025-01-18 00:00:00&endTime=2025-01-18 23:59:59
    https://api-eu.livoltek-portal.com:8081/hess/api/device/527/SN123456/realTime?userToken=1&userType=1 &startTime=2025-01-18 00:00:00&endTime=2025-01-18 23:59:59

### 15. Site historical solar generation in recent 2 years — `siteHistoricalSolar`

- **GET** `/hess/api/site/{siteId}/solarEnergy`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: timeType 0 (día) o 1 (semana): inicio y fin dentro de los últimos 2 años.
- Ventana: timeType 0: intervalo ≤ 31 días. timeType 1: intervalo ≤ 180 días.
- Ventana: timeType 2 (mes) y 3 (año): la doc no fija límite (SIN VERIFICAR).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `startTime` | query | sí | String | Start time; e.g.20220726 |
| `endTime` | query | sí | String | End time; e.g.20220726 |
| `timeType` | query | sí | String | Time interval type<br>0：day<br>1: week<br>2: month<br>3: year |
| `page` | query | sí | Int | The first site index to be returned in the results, default=1 |
| `size` | query | sí | Int | Pagesize of each page,<br>- 5<br>-10 (default)<br>-30 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/527/SN123456？userToken=1&startTime=20220726&endTime=20220726&timeType=3&userType=1&page=1&size=10

### 16. Site historical grid import&export in recent 2 years — `siteHistoricalGrid`

- **GET** `/hess/api/site/{siteId}/utilityEnergy`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: timeType 0 (día) o 1 (semana): inicio y fin dentro de los últimos 2 años.
- Ventana: timeType 0: intervalo ≤ 31 días. timeType 1: intervalo ≤ 180 días.
- Ventana: timeType 2 (mes) y 3 (año): la doc no fija límite (SIN VERIFICAR).
- Nota: Ruta utilityEnergy: positive = importación de la red, negative = exportación; powerGeneration en etotalToGrid.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `timeType` | query | sí | Integer | Time Type; 0：day；1：week；2：month：3:year |
| `startTime` | query | sí | String | Start Time; format：yyyyMMdd |
| `endTime` | query | sí | String | End Time; format：yyyyMMdd<br>option，default(current day) |
| `size` | query | sí | Integer | Size of one page |
| `page` | query | sí | Integer | Current page |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/utilityEnergy?timeType=1&startTime=20220701&endTime=20220731&size=10&page=1&userType

### 17. API user login and get token — `userLoginAndToken`

- **POST** `/hess/api/login`
- Autenticación: cuerpo: secuid + key (devuelve el token)
- Clase: **lectura** · nivel B.5: **0**
- Nota: Autenticación: no cambia nada en los equipos. Es el único endpoint sin cabecera Authorization ni userToken; el token devuelto (data.data) se usa en la cabecera Authorization del resto.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `secuid` | cuerpo | sí | String | Security ID |
| `key` | cuerpo | sí | String | Securiity Key |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/login

### 18. Charging station creation — `chargingStationCreation`

- **POST** `/hess/api/chargeSite/create`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Familia de cargadores EV: nivel 2 por decisión del usuario. Exige account + pwd (MD5) en el cuerpo, que NO están en las variables de entorno.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `adress` | cuerpo | sí | String | Address of charging station |
| `countryValue` | cuerpo | sí | String | Country code; e.g: CN |
| `currencyUnitValue` | cuerpo | sí | String | Currency code; e.g: $ |
| `customer` | cuerpo | sí | Long | Consumer ID of the user |
| `downPrice` | cuerpo | sí | Object | Off grid electricity price |
| `price` | cuerpo | sí | Double | Off grid electricity price |
| `startTime` | cuerpo | sí | Long | time-on; e.g: 0 |
| `endTime` | cuerpo | sí | Long | End Time; e.g: 86400 |
| `gridTiedType` | cuerpo | sí | Integer | Grid connection type; 1:100% feed-in<br> 2:self-use first<br> 3:0 feed-in<br> 4:Off-grid |
| `isShown` | cuerpo | sí | Integer | Is the charging station visible to the consumer's user; 0: invisible<br> 1: visible |
| `latitude` | cuerpo | sí | Double | latitude |
| `longitude` | cuerpo | sí | Double | longitude |
| `name` | cuerpo | sí | String | Charging station name |
| `timezoneValue` | cuerpo | sí | String | Time zone where the charging station is located; e.g: Asia/Shanghai |
| `upPrice` | cuerpo | sí | Object | feed-in tariff |
| `price` | cuerpo | sí | Double | feed-in tariff |
| `startTime` | cuerpo | sí | Long | time-on; e.g: 0 |
| `endTime` | cuerpo | sí | Long | End Time; e.g: 86400 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeSite/create? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/create? userToken=xxx&userType=1

### 19. Charging station query — `chargingStationQuery`

- **POST** `/hess/api/chargeSite/querySite`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Solo consulta, pero se clasifica con la familia EV (control, nivel 2) por decisión del usuario y porque exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `filterName` | cuerpo | no | String | Charging station name |
| `filterTime` | cuerpo | no | List | Query by time list |
| `page` | cuerpo | sí | Int | The first site index to be returned in the results, default=1 |
| `size` | cuerpo | sí | Int | Pagesize of each page, -5 -10 (default) -30 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeSite/querySite? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/querySite? userToken=xxx&userType=1

### 20. Charging station update — `chargingStationUpdate`

- **POST** `/hess/api/chargeSite/update`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Familia de cargadores EV: nivel 2. Exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `id` | cuerpo | sí | Integer | Charging station ID |
| `adress` | cuerpo | sí | String | Address of charging station |
| `countryValue` | cuerpo | sí | String | Country code; e.g: CN |
| `currencyUnitValue` | cuerpo | sí | String | Currency code; e.g: $ |
| `customer` | cuerpo | sí | Long | Consumer ID of the user |
| `downPrice` | cuerpo | sí | Object | Purchase electricity price |
| `price` | cuerpo | sí | Double | Purchase electricity price |
| `startTime` | cuerpo | sí | Long | time-on; e.g: 0 |
| `endTime` | cuerpo | sí | Long | End Time; e.g: 86400 |
| `isShown` | cuerpo | sí | Integer | Is the charging station visible to the consumer's user; 0: invisible<br> 1: visible |
| `latitude` | cuerpo | sí | Double | latitude |
| `longitude` | cuerpo | sí | Double | longitude |
| `name` | cuerpo | sí | String | Charging station name |
| `timezoneValue` | cuerpo | sí | String | Time zone where the charging station is located; e.g: Asia/Shanghai |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeSite/update? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/update? userToken=xxx&userType=1

### 21. Charging station deletion — `chargingStationDeletion`

- **POST** `/hess/api/chargeSite/disable`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Familia de cargadores EV: nivel 2; destructivo (disable). Exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `id` | cuerpo | sí | Integer | Charging station ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeSite/disable? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/disable? userToken=xxx&userType=1

### 22. Charging device creation — `chargingDeviceCreation`

- **POST** `/hess/api/chargeDevice/create`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Familia de cargadores EV: nivel 2. Exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `inverterSn` | cuerpo | sí | String | Device serial number |
| `powerStation` | cuerpo | sí | Long | ID of the power station to which the equipment belongs |
| `productType` | cuerpo | sí | String | Product type of equipment |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeDevice/create? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/create? userToken=xxx&userType=1

### 23. Charging device query — `chargingDeviceQuery`

- **POST** `/hess/api/chargeDevice/queryEv`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Solo consulta, pero se clasifica con la familia EV (control, nivel 2) y exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `filterSn` | cuerpo | no | String | Device serial number |
| `filterStationId` | cuerpo | no | List | ID of the power station to which the equipment belongs |
| `filterTime` | cuerpo | no | List | Time interval |
| `pageSize` | cuerpo | sí | Integer | Single page quantity |
| `start` | cuerpo | sí | Integer | Number of pages |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeDevice/queryEv?userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/queryEv?userToken=xxx&userType=1

### 24. Charging device delete — `chargingDeviceDelete`

- **POST** `/hess/api/chargeDevice/disable`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Familia de cargadores EV: nivel 2; destructivo (disable). Exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `id` | cuerpo | sí | Integer | Device ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeDevice/disable? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/disable? userToken=xxx&userType=1

### 25. Charging Record Query — `chargingRecordQuery`

- **POST** `/hess/api/chargeRecord`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: Solo consulta de historial de cargas, pero se clasifica con la familia EV (nivel 2) y exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `inverterId` | cuerpo | no | String | Charger Device ID |
| `siteId` | cuerpo | no | String | Power station ID |
| `filterTime` | cuerpo | no | List | Time interval |
| `pageSize` | cuerpo | sí | Integer | Single page quantity |
| `start` | cuerpo | sí | Integer | Number of pages |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeDevice/chargeRecord? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/chargeRecord? userToken=xxx&userType=1

### 26. Charging Station Start/Stop — `chargingStationStartOrStop`

- **POST** `/hess/api/chargeCommandDown`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: chargeCommandDown: inicia o detiene una carga. Acción física sobre el cargador. Exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user <br>1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `chargeStrategy` | cuerpo | sí | Integer | Charging strategy<br> -1: Stop charging<br> 0: Until fully charged<br> 1: Charge according to time<br> 2: Charge according to amount<br> 3: Charge according to battery level |
| `chargeStrategyPar` | cuerpo | sí | Integer | Charging strategy parameter:<br> When chargeStrategy is 0, fill in 0;<br> When chargeStrategy is 1, transfer the charging duration in seconds, such as 120;<br> When chargeStrategy is 2, transfer the charging amount, such as: 10;<br> When chargeStrategy is 3, transfer the charging charge, such as 100 |
| `chargeType` | cuerpo | sí | Integer | Charging effective type 0: Instant charging 2: Appointment charging |
| `startTime` | cuerpo | sí | String | Appointment start time, timestamp, in seconds, such as 1693468512 |
| `sn` | cuerpo | sí | String | Device SN number |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeCommandDown? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeCommandDown? userToken=xxx&userType=1

### 27. Charging schedule settings — `chargingScheduleSettings`

- **POST** `/hess/api/chargeSchedule`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Nota: chargeSchedule: un solo horario por día; uno repetido sobrescribe el anterior (doc). Exige account + pwd.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user<br> 1：agent |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `dayOfWeek` | cuerpo | sí | Integer | 1: Monday<br> 2:Tuesday<br> 3:Wednesday <br> 4：Thursday <br> 5：Friday <br> 6：Saturday<br> 7：Sunday |
| `deviceId` | cuerpo | sí | String | Device ID |
| `durationHour` | cuerpo | sí | Integer | Charging duration hours must be greater than -1 and less than 24 |
| `durationMin` | cuerpo | sí | Integer | Charging duration minutes, must be 0 or 30 |
| `startMin` | cuerpo | sí | Integer | Charging start time minutes, must be 0 or 30 |
| `startHour` | cuerpo | sí | Integer | Charging start time hours, must be greater than -1 and less than 24 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/chargeSchedule? userToken=xxx&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/chargeSchedule? userToken=xxx&userType=1

### 28. Mqtt push device alarm — `mqttPushDeviceAlarm`

- Transporte MQTT: `mqtt://api.livoltek-portal.com:1883`, `mqtt://api-eu.livoltek-portal.com:1883` — **solo documentado; no implementado**.
- Autenticación: usuario/clave MQTT (se piden por correo a Livoltek)
- Clase: **lectura** · nivel B.5: **0**
- Nota: Solo documentado. Suscripción MQTT: mqtt://api.livoltek-portal.com:1883 (International) o mqtt://api-eu.livoltek-portal.com:1883 (Europa). Usuario y clave se piden por correo a service@livoltek.com. Tema: ev_alarm_topic/{sn} (el ejemplo de la doc es de un cargador EV).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `username` | cuerpo | sí | String | user name |
| `password` | cuerpo | sí | String | password |
| `topic` | cuerpo | sí | String | Mqtt subscription theme; ev_alarm_topic/{sn} e.g: ev_alarm_topic/AC12456 |

### 29. Mqtt push device working status — `mqttPushDeviceWorkingStatus`

- Transporte MQTT: `mqtt://api.livoltek-portal.com:1883`, `mqtt://api-eu.livoltek-portal.com:1883` — **solo documentado; no implementado**.
- Autenticación: usuario/clave MQTT (se piden por correo a Livoltek)
- Clase: **lectura** · nivel B.5: **0**
- Nota: Solo documentado; mismas condiciones y servidores que la de alarmas.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `username` | cuerpo | sí | String | user name |
| `password` | cuerpo | sí | String | password |
| `topic` | cuerpo | sí | String | Mqtt subscription theme; ev_work_status_topic/{sn} e.g: ev_work_status_topic/AC12456 |

### 30. Query the power station ID based on device SN — `queryPowerStationId`

- **GET** `/hess/api/site/{serialNumber}` _(método inferido: la doc no lo indica)_
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: GET /hess/api/site/{serialNumber}: devuelve el powerStationId a partir del SN de un equipo.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0：end-user 1：agent |
| `serialNumber` | ruta | sí | String | The serial number of the device |

### 31. Site Owner — `siteOwner`

- **GET** `/hess/api/site/{siteId}/siteOwner`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0** · contiene datos sensibles (credenciales o datos personales)
- Nota: Devuelve datos personales del cliente final (nombre, correo, cuenta de acceso). No incluirlo en reportes ni en el CLI por defecto.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | Long | Unique identifier of the power station |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/991/customer?userToken=ehnu2NQ&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/site/991/customer?userToken=eyhnu2NQ&userType=1

### 32. Device Basic Data — `deviceBasicData`

- **GET** `/hess/api/device/basicData`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: Trae las energías del día del equipo: powerGenerationDay, positiveDay (compra a la red), negativeDay (venta), chargeDay, dischargeDay, loadDay. Unidad NO documentada (SIN VERIFICAR).
- Nota: size solo 5, 10 o 30.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `size` | query | sí | Integer | Pagesize of each page:<br>-5<br>-10 (default)<br>-30 |
| `page` | query | sí | Integer | The first site index to be returned in the results, default=1 |
| `startTime` | query | no | String | Start time for query; 2021-03-15 05:47:15 |
| `endTime` | query | no | String | End time for query; 2024-03-15 05:47:15 |
| `Sn` | query | no | String | Device serial number |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/device/basicData?userType=1&userToken=<token-de-ejemplo-omitido>&sn=GT32501H22520024&startTime=2021-03-15 05:47:15&endTime=2024-03-15 05:47:15

### 33. Device One Day Fault Alarm — `deviceOneDayFaultAlarm`

- **GET** `/hess/api/device/{siteId}/{serialNumber}/oneDayFaultAlarm`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: Un solo día por consulta (dateTime = yyyy-MM-dd).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |
| `serialNumber` | ruta | sí | Integer | Device SN |
| `size` | query | sí | Integer | Pagesize of each page,<br>-5<br>-10 (default)<br>-30 |
| `page` | query | sí | Integer | The first site index to be returned in the results, default=0 |
| `dateTime` | query | sí | String | Datetime for query, which should be in one day; e.g. 2022-01-01 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/SN10203/ oneDayFaultAlarm? dateTime=2022-01-01&page=1&size=10&userToken=*****&userType=1
    https://api-eu.livoltek-portal.com:8081/hess/api/site/123/SN10203/ oneDayFaultAlarm? dateTime=2022-01-01&page=1&size=10&userToken=*****&userType=1

### 34. Generate UserToken — `generateUserToken`

- **POST** `/hess/api/user/userToken`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **3** · **solo manual: el skill no lo ejecuta**
- Regla de frecuencia (doc): Each terminal with the same name can only call the interface 5 times in 15 minutes, and each terminal user with the same name can only generate 5 valid tokens.
- Frecuencia: 5 llamadas cada 15 min por terminal con el mismo nombre; máx. 5 tokens válidos por usuario (doc).
- Nota: user/userToken crea una credencial de la cuenta (exige account + pwd en MD5). Regla del usuario: NUNCA se ejecuta desde el skill. Se anota como nivel 3 por esa decisión.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `account` | cuerpo | sí | String | User account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `expiryTime` | cuerpo | sí | Long | UserToken expiration time |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/user/userToken?userType=1
    https://api-eu.livoltek-portal.com:8081 /hess/api/user/userToken?userType=1

### 35. UserToken query — `userTokenQuery`

- **POST** `/hess/api/user/userTokenList`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0** · contiene datos sensibles (credenciales o datos personales) · **solo manual: el skill no lo ejecuta**
- Regla de frecuencia (doc): Each terminal with the same name can only call the interface 5 times in 15 minutes. Only valid tokens can be queried.
- Frecuencia: 5 llamadas cada 15 min por terminal con el mismo nombre (doc).
- Nota: user/userTokenList es de solo lectura pero DEVUELVE TOKENS EN CLARO y exige account + pwd: el skill no lo ejecuta (precaución propia, no regla del usuario; confirmar).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `account` | cuerpo | sí | String | User account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/user/userTokenList?userType=1
    https://api-eu.livoltek-portal.com:8081 /hess/api/user/userTokenList?userType=1

### 36. Device power report query — `devicePowerReportQuery`

- **POST** `/hess/api/sample/energy`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Regla de frecuencia (doc): Each device can only request an interface once per hour The query time interval cannot exceed 24 hours
- Ventana: El intervalo de consulta no puede superar 24 horas (doc).
- Frecuencia: Cada dispositivo solo puede consultar este endpoint una vez por hora (doc).
- Nota: Es POST pero SOLO LEE: el método HTTP no basta para clasificar. userToken y userType van en la URL; id, startTime, endTime e interval (300/900/1800/3600 s) en el cuerpo JSON.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `userToken` | query | sí | String | userToken |
| `id` | cuerpo | sí | Long | Device ID |
| `startTime` | cuerpo | sí | String | Start time |
| `endTime` | cuerpo | sí | String | End Time |
| `interval` | cuerpo | no | Integer | Time interval in seconds; Default: 3600 (1h)<br>Options: 300 (5min) / 900 (15min) / 1800 (30min) / 3600 (1h) |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/sample/energy?userType=1 & userToken=qwrqwrq
    https://api-eu.livoltek-portal.com:8081 /hess/api/user/sample/energy?userType=1 & userToken=qwrqwrq

### 37. Site day energy query — `siteDayEnergyQuery`

- **POST** `/hess/api/sample/energy/site/day`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Regla de frecuencia (doc): Each id can only request an interface once per hour
- Ventana: Un mes por consulta (date = yyyy-MM); devuelve el detalle día a día.
- Frecuencia: Cada id solo puede consultar este endpoint una vez por hora (doc).
- Nota: Es POST pero SOLO LEE. Incluye evConsumption (consumo de cargadores EV).
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `userToken` | query | sí | String | userToken |
| `id` | cuerpo | sí | Long | Site ID |
| `date` | cuerpo | sí | String | Month date; 2025-07 |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/sample/energy/site/day?userType=1&userToken=qwrqwrq
    https://api-eu.livoltek-portal.com:8081 /hess/api/user/sample/energy/site/day?userType=1&userToken=qwrqwrq

### 38. Sunspec reboot inverter — `sunspecRebootInverter`

- **POST** `/hess/api/sunspec/command/rebootInverter`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Regla de frecuencia (doc): Each id can only request an interface once per hour
- Frecuencia: Cada id solo puede llamar este endpoint una vez por hora (doc).
- Nota: Reinicia el inversor. Exige account + pwd. Regla del usuario: ningún sunspec/command/* se ejecuta.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `userToken` | query | sí | String | userToken |
| `account` | cuerpo | sí | String | account |
| `pwd` | cuerpo | sí | String | password |
| `sn` | cuerpo | sí | String | device sn |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/sunspec/command/rebootInverter?userType=1 & userToken=qwrqwrq
    https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/rebootInverter?userType=1 & userToken=qwrqwrq

### 39. Sunspec reboot BMS — `sunspecRebootBMS`

- **POST** `/hess/api/sunspec/command/rebootBMS`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Regla de frecuencia (doc): Each id can only request an interface once per hour
- Frecuencia: Cada id solo puede llamar este endpoint una vez por hora (doc).
- Nota: Reinicia el BMS. Exige account + pwd. No se ejecuta.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `userToken` | query | sí | String | userToken |
| `account` | cuerpo | sí | String | account |
| `pwd` | cuerpo | sí | String | password |
| `sn` | cuerpo | sí | String | device sn |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/sunspec/command/rebootBMS?userType=1 & userToken=qwrqwrq
    https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/rebootBMS?userType=1 & userToken=qwrqwrq

### 40. Sunspec some param info — `sunspecSomeParamInfo`

- **POST** `/hess/api/sunspec/command/info`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2**
- Regla de frecuencia (doc): Each id can only request an interface once per hour
- Frecuencia: Cada id solo puede llamar este endpoint una vez por hora (doc).
- Nota: Lee parámetros (devuelve address, factor, functionCode y value de cada punto) pero exige account + pwd. Se agrupa con control por decisión del usuario y por la regla de no ejecutar sunspec/command/*. Conservador: nivel 2 aunque semánticamente sea lectura (CONFIRMAR con el usuario).
- Nota: El campo address es un registro Modbus (p. ej. 45093 TOUEnable, 45018 Time2BatteryChargePower): cruza con modbus-gen2.json.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `userToken` | query | sí | String | userToken |
| `account` | cuerpo | sí | String | account |
| `pwd` | cuerpo | sí | String | password |
| `sn` | cuerpo | sí | String | device sn |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/sunspec/command/info?userType=1 & userToken=qwrqwrq
    https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/info?userType=1 & userToken=qwrqwrq

### 41. Sunspec some param setting — `sunspecSomeParamSetting`

- **POST** `/hess/api/sunspec/command/send`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **control** · nivel B.5: **2 o 3 según el registro**
- Regla de frecuencia (doc): Each id can only request an interface once per hour
- Frecuencia: Cada id solo puede llamar este endpoint una vez por hora (doc).
- Nota: Escribe parámetros: la doc dice que hay que usar el resultado de info y modificar value. Cada punto lleva address (registro Modbus) y functionCode (6 = escribir un registro).
- Nota: classify_register() decide por registro con modbus-gen2.json: fábrica, seguridad y firmware = nivel 3 (rechazado); lo no documentado = no escribible. Exige account + pwd. No se ejecuta.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `userToken` | query | sí | String | userToken |
| `account` | cuerpo | sí | String | user account |
| `pwd` | cuerpo | sí | String | User password encrypted using MD5 |
| `sn` | cuerpo | sí | String | Device SN |
| `points` | cuerpo | sí | Array | Collection of the following data objects |
| `pointDesc` | cuerpo |  | String | Control point description |
| `pointName` | cuerpo |  | String | Control Point Name |
| `uiName` | cuerpo |  | String | UI Name of Control Point |
| `address` | cuerpo |  | String | address |
| `factor` | cuerpo |  | String | factor |
| `template` | cuerpo |  | long | template |
| `value` | cuerpo |  | String | Value, display on query, issue on setting |
| `pointOrder` | cuerpo |  | String | Point Order |
| `pointLen` | cuerpo |  | String | Point Length |
| `pointGroupId` | cuerpo |  | String | Point Group Id |
| `controlType` | cuerpo |  | long | template |
| `functionCode` | cuerpo |  | String | Function Code |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/sunspec/command/send?userType=1 & userToken=qwrqwrq
    https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/send?userType=1 & userToken=qwrqwrq

### 42. Query station statistics — `queryStationStatistics`

- **GET** `/hess/api/powerStationStatistics`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Nota: NO aparece en el árbol lateral de la doc: GET /hess/api/powerStationStatistics (número de sitios, capacidad instalada, generación actual y acumulada). La doc no lista parámetros. No se usa por defecto.
- Verificado en vivo: **no (sin verificar)**

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/powerStationStatistics

### 43. Site historical grid import&export in recent 3 days — `siteHistoricalGridImport`

- **GET** `/hess/api/site/{siteId}/reissueUtilityEnergy`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: Últimos 3 días (sin parámetros de fecha).
- Nota: NO aparece en el árbol lateral de la doc: ruta reissueUtilityEnergy. No se usa por defecto; unidad SIN VERIFICAR.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/ reissueUtilityEnergy? userToken =1& siteId =1123& userType =1

### 44. Site historical solar generation in recent 3 days — `siteHistoricalSolarGeneration`

- **GET** `/hess/api/site/{siteId}/reissueSolarEnergy`
- Autenticación: cabecera Authorization: <token del login>
- Clase: **lectura** · nivel B.5: **0**
- Ventana: Últimos 3 días (sin parámetros de fecha).
- Nota: NO aparece en el árbol lateral de la doc (existe como módulo del bundle): ruta reissueSolarEnergy. No se usa por defecto; unidad (Wh según el texto) SIN VERIFICAR.
- Verificado en vivo: **no (sin verificar)**

| Parámetro | En | Oblig. | Tipo | Descripción |
|---|---|---|---|---|
| `userToken` | query | sí | String | User token |
| `userType` | query | no | String | User Type; 0- end-user<br>1- agent |
| `siteId` | ruta | sí | String | Site ID |

Ejemplo(s) de la doc:

    https://api.livoltek-portal.com:8081/hess/api/site/123/reissueSolarEnergy? userToken =1& siteId =1123& userType =1
