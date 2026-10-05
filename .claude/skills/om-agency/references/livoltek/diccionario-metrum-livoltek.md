# Diccionario Metrum → API Livoltek → registro Modbus

> **Estado: todo SIN VERIFICAR en vivo.** Todavía no hay ningún inversor Livoltek validado con esta cuenta. Lo único
> comprobado es lo que *dicen* los documentos: API v1.6.0 (`api-doc.md`, `endpoints.md`) y el PDF Modbus V1.01
> (`modbus-gen2-registros.md`). La primera validación será el cruce **API Livoltek vs Metrum** (sección 6); hasta
> entonces ninguna fila pasa de «sin verificar».
>
> Leyenda: **D** = lo dice la doc/PDF · **S/V** = sin verificar en vivo · **H** = hipótesis mía · «—» = no existe ese dato en esa fuente.

## 0. Cómo leerlo

- **Metrum**: las claves salen de `../deye-cloud/diccionario-metrum-deye.md` (la única marca validada hasta hoy). Para un
  inversor Livoltek, Metrum puede entregar otras claves o las mismas con otro significado: **confirmar en la primera casa**.
  Las claves con sufijo `_DY` son del driver de Deye y **no se extrapolan** a Livoltek.
- **API**: `endpoint.campo`, tal como lo documenta Livoltek. Los nombres de endpoint son los `id` de `endpoints.json`.
- **Modbus**: dirección del PDF (se usa tal cual en la PDU), tipo y escala. Un `uint32` ocupa dos registros, palabra baja primero.
  `0xFFFF` / `0xFFFFFFFF` = el equipo no soporta el registro: el adaptador lo devuelve como `None`.
- **Esquema normalizado (B.0)**: `bat_power_w` + = carga · `grid_power_w` + = importación · `grid_up` · `energy_day_kwh{…}`.
- Las **unidades** de la API están en discusión (sección 7): el adaptador las toma de parámetros explícitos
  (`power_unit`, `energy_unit`), no las asume en silencio.

## 1. Convención de signo (lo más delicado)

| Magnitud normalizada | Metrum (validado en Deye) | API Livoltek (doc) | Modbus (PDF) | Qué hacer |
|---|---|---|---|---|
| `bat_power_w` **+ = carga** | `BattPower`: **+ = descarga** (Deye) → invertir | `curPowerflow.energyPower`: el ejemplo trae **−0.156** con `energyStatus = disCharging` → sugiere **+ = carga, − = descarga** (**H**, S/V) | `42590` Battery Active Power: **signo no documentado** | Con una carga conocida (SOC subiendo), comparar el signo en las tres fuentes y fijarlo |
| `bat_current_a` **+ = carga** | `BattCur`: **+ = carga**, opuesto a `BattPower` (Deye) | `realTime.batteryCurrent`: signo no documentado | — | Medir igual que la potencia |
| `grid_power_w` **+ = importación** | en Deye, `LoadPower_DY` (+ = importación) pero **no extrapolable** | `curPowerflow.powerGridPower` + `powerGridStatus` (`importing`/`exporting`): **signo no documentado**; ver el hallazgo siguiente | `42512` SM_Activepower (total) y `42514/42516/42518` (L1-L3): **signo no documentado** | Medir con importación y con exportación conocidas |

**Hallazgo que impide fiarse de la etiqueta de red.** En el ejemplo de `HisPowerflow`: `pvPower` = 2.953, `loadPower` = 0.061,
`energyPower` = 0.0 y `powerGridStatus` = «Importing» con `powerGridPower` = 2.743. Con esa generación y casi sin consumo,
el balance físico indica **exportación** (≈ 2.9 kW), no importación. O la etiqueta está dada desde el punto de vista de la
red, o el ejemplo es sintético. **No usar `powerGridStatus` para fijar el signo**: decidirlo cruzando con Metrum y con
un consumo conocido. `grid_power_w` queda `None` en el adaptador si no hay medidor (la doc dice que sin medidor interno o
externo no hay datos de red).

## 2. Energía (contadores) — escala Metrum Wh = valor del equipo en kWh × 1000 (como en Deye; S/V para Livoltek)

| Metrum | API Livoltek | Modbus | Unidad / escala | Estado |
|---|---|---|---|---|
| `energyPD` | `deviceBasicData.powerGenerationDay` (equipo); `siteGenerationOverview.eoutDaily` (sitio, kWh **D**) | `42537` Solar Energy Daily (uint16) | Modbus ×0.1 kWh **D**; `basicData` sin unidad documentada | S/V |
| `energyLD` | `deviceBasicData.loadDay`; serie `devicePowerReportQuery.loadConsumption` | `42550` EToday-Load (**int16**, con signo) | ×0.1 kWh | S/V |
| `energyID` | `deviceBasicData.positiveDay` (la doc: «Daily purchase of online electricity», es decir, compra a la red); `siteHistoricalGrid.positive` («Energy import from grid» **D**) | `42547` EToday-ImportfromGrid (uint16) | ×0.1 kWh | S/V |
| `energyED` | `deviceBasicData.negativeDay` (**H**: la doc dice «Daily grid connected electricity consumption», ambiguo; se toma como exportación por analogía con `siteHistoricalGrid.negative` = «Energy export to grid» **D**) | `42544` EToday-ExporttoGrid (uint16) | ×0.1 kWh | S/V |
| `energyIT` | — (no hay total de importación en la API) | `42548` total_import_energy (uint32) | ×0.1 kWh | S/V |
| `energyET` | — | `42545` total_export_energy (uint32) | ×0.1 kWh | S/V |
| `energyLT` | `deviceGenerationOrConsumption.loadCustomerElectric` (**solo con medidor RS485**) | `42551` ETotal-Load (int32) | kWh | S/V |
| `energyAE` | `deviceGenerationOrConsumption.pvProduceElectric`; `siteGenerationOverview.eTotalToGrid` (la doc lo llama «Lifetime generation»; el nombre engaña) | `42542` ETotal-Solar (uint32) | ×0.1 kWh | S/V |
| — (sin clave Metrum) carga de batería, día | `deviceBasicData.chargeDay`; serie `chargingCapacity` | — | sin unidad documentada | S/V |
| — descarga de batería, día | `deviceBasicData.dischargeDay`; serie `dischargeCapacity` | — | ídem | S/V |

- El PDF **no** trae las energías de carga y descarga de la batería: solo la API.
- Resolución Modbus 0,1 kWh. La resolución de la API no está documentada.
- Como en Deye, el cierre del día de Metrum es el último valor antes de las 24:00 locales (no `max()` del día).
- `devicePowerReportQuery` y `siteDayEnergyQuery` son **POST de solo lectura** con tope de **una consulta por hora** por equipo o sitio:
  no sirven para sondeo frecuente.

## 3. Batería

| Metrum | API Livoltek | Modbus | Nota | Estado |
|---|---|---|---|---|
| `BattSOC` | `curPowerflow.energySoc`; `storageInformation.currentSoc`; `deviceTechnical.batterySoc` | **—** (el PDF no trae SOC) | solo API | S/V |
| `BattVolt` | `deviceTechnical.batteryVoltage` («BMS voltage»); `storageInformation…energyVolage` (sic) | **—** (`44605` es la tensión de **plataforma nominal**, no la medida) | solo API | S/V |
| `BattCur` | `deviceTechnical.batteryCurrent` | **—** | solo API; signo sin documentar | S/V |
| `BattPower` | `curPowerflow.energyPower`; `siteHistoricalPowerFlow.energyPower` | `42590` Battery Active Power (int32 ×1 W) | signo: sección 1 | S/V |
| `BattTemp` | **—** (ningún campo documentado) | **—** | **sin fuente** | — |
| `BattSOH` / ciclos | `storageInformation.cycleCount`, `batterySn` (**«underdeveloping»**) | **—** | no disponible hoy | — |
| `BattCapAH_DY` | `storageInformation.BMSCapacity` (Ah, «del BMS») | `44606` battery Total Capacity (uint16, Ah; nominal) | nominal, no medida | S/V |
| — BMS | `storageInformation.deviceSn` / `deviceId`; `batteryTypeList` | `42151-42165` BMS Version (texto) | | S/V |

## 4. Red / AC / PV / carga / estado

| Metrum | API Livoltek | Modbus | Nota | Estado |
|---|---|---|---|---|
| `voltGridA/B/C` | `deviceTechnical.rVoltage / sVoltage / tVoltage` («inverter AC interface») | `42531-42533` phase L1-L3 voltage (uint16 ×0.1 V) | ¿tensión de **red** o de **salida del inversor**? La doc no lo dice | S/V |
| `voltageA/B/C` | las mismas | las mismas | **H**: Livoltek no distingue las dos tensiones como Deye | S/V |
| `curGridA/B/C`, `currentA/B/C` | `deviceTechnical.rCurrent / sCurrent / tCurrent` | `42534-42536` phase L1-L3 current (int16 ×0.01 A) | **la descripción de la API está desplazada** (sección 7): confirmar fase por fase | S/V |
| `frequency` | `deviceTechnical.girdFrequency` (sic; «Grid frequency») | `42530` grid frequency (uint16 ×0.01 Hz) | en Deye `frequency` era la de **salida**: aquí la doc dice «grid»; no asumir | S/V |
| `freqEps`, `voltEpsA/B/C` | `deviceTechnical.epsFrequency / epsVoltage / epsCurrent` (solo híbridos) | — | | S/V |
| — PV total | `curPowerflow.pvPower`; `deviceTechnical.p1Voltage … p12Current` | `42527` Total DC Power (int32 ×1 W); MPPT N: `42700+2(N−1)` V (×0.1), `42701+2(N−1)` A (×0.1) | | S/V |
| — carga | `curPowerflow.loadPower` | `42504` Load active power (int32 ×1 W) | | S/V |
| — potencia de red | `curPowerflow.powerGridPower`; `deviceTechnical.dwActivePower` | `42512` SM_Activepower; `42521` Total active power (inversor) | signo: sección 1 | S/V |
| `powerAEg`, `powerAPg`, `powerAE`, `LoadPower_DY`, `ExportGrid_DY`, `MeterState_DY`, `BattCharges_DY` | — | — | claves del driver de Deye con significados engañosos: **no extrapolar** | — |
| `invrun` / `invstate` | `deviceDetails.runningStatus` (0 Normal, 1 Standby, 2 Fault, 3 Offline, 4 Self-test, 5 Upgrading); `deviceBasicData.runningStatus` (texto) | `42506` Oper. status (`0x1000` on grid, `0x1001` off grid, `0x100D` fault, … ver tabla de estados) | la API da el estado general; **solo Modbus** distingue «on grid / off grid» | S/V |
| **`grid_up`** (derivada) | `min(rVoltage, sVoltage, tVoltage) ≥ 20 V` si no son nulas (**H**, umbral heredado de Deye) | `42506` = `0x1000` (on grid) o `min(42531-42533) ≥ 20 V` | a validar con un corte real; si falta el dato, `None` (nunca `True` por defecto) | S/V |
| alarmas | `deviceHistoricalAlarm` / `deviceOneDayFaultAlarm`: `alarmCode`, `alarmName`, `alarmType`, `originTime` | `42573` fault number, `42574-42583` fault 1…10 → Apéndice 3 (277 códigos) | la API da ventana de 7 días; el PDF solo el estado actual | S/V |

## 5. Escritura: API Sunspec ↔ registros del PDF (política B.5)

El endpoint `sunspec/command/send` usa `address` = **registro Modbus** y `functionCode` (6 = escribir un registro).
`classify_register()` decide por registro con `modbus-gen2.json`, que es una **lista blanca de 32 registros** (solo esos son escribibles):

| Concepto | Registros (nivel B.5) |
|---|---|
| Reloj del sistema | 42752-42757 (**1**) |
| Reinicio inversor / BMS | 42762 / 42763 (**2**) |
| Apagado/encendido; parada de emergencia | 42758 / 42759 (**3**, prohibido) |
| Límite de potencia / exportación | 43714, 43715, 43718, 43719, 43720, 43736, 43737, 43742 (**2**) |
| Reactiva y curvas | 43602, 43605, 43606, 43607, 43610, 43624 (**2**) |
| Método de control por medidor/CT | 43721 (**2**); autodiagnóstico de flujo 43727 (**1**) |
| Despacho remoto de batería | 43744, 43745, 45004, 45005, 45006 (**2**) |
| PID | 44002 (**1**) |

> **Hallazgo:** los ejemplos de la propia API usan `45093` (TOUEnable) y `45018` (Time2BatteryChargePower), que **no están**
> entre los 32 registros del PDF V1.01. Por la lista blanca son **no escribibles** (`classify_register()` → `None`, rechazado).
> Hay más puntos accesibles por la nube (TOU, etc.) que el PDF no documenta: tratarlos como no escribibles hasta tener su documentación.

## 6. Plan de la primera validación: cruce API Livoltek vs Metrum

Pendiente de que el usuario diga **qué casa o número de serie** usar. Con ~20 llamadas de solo lectura (login, `site/{sn}`, `device/{siteId}/list`,
`curPowerflow`, `realTime`, `basicData`, `details`, `alarm`):

1. Alinear la hora (la API usa marcas en ms; Metrum ≈ 15 min) y comparar **SOC, potencias y energías del día** con Metrum.
2. Fijar el **signo** de batería (1) y de red (1) con una carga/descarga o importación/exportación conocida.
3. Fijar las **unidades** (W o kW; Wh o kWh) y el **significado** de `rVoltage…tCurrent`.
4. Comprobar `grid_up` contra un corte conocido si lo hay; si no, dejarlo anotado como pendiente.
5. Guardar el resultado en `validacion-<casa>-AAAA-MM.md` y pasar las filas confirmadas de **S/V** a **C** (con su correlación).

## 7. Hallazgos de la doc que afectan la normalización

- **Unidades de potencia:** la prosa de `curPowerflow` y `HisPowerflow` dice «(W)», las tablas de campos dicen «kW» y los ejemplos (0.006, −0.156, 2.953) parecen kW.
- **Unidades de energía:** `utilityEnergy` habla de «Wh» y sus ejemplos parecen kWh; `deviceBasicData` y `solarEnergy` no dan unidad.
- **`realTime`:** las descripciones de `rCurrent`, `sVoltage`, `sCurrent`, `tVoltage` y `tCurrent` están corridas una posición; los ejemplos usan claves en minúscula; las unidades no se documentan.
- **Estados «Under developing»:** `pvStatus`, `powerGridStatus`, `loadStatus`, `batterySn`, `cycleCount`, `alarmStatus` llegan `null`.
- **Sin medidor** (interno o externo) no hay datos de red.
- **El estado del equipo** es numérico en `deviceDetails` y texto en `deviceBasicData`.
- **Metrum:** no hay clave de temperatura de batería ni de SOH con fuente en Livoltek.
