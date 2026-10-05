# Livoltek Gen 2 — registros Modbus (resumen propio del PDF V1.01)

Fuente: «Livoltek Gen 2 Energy Storage Inverter External Communication Protocol» **V1.01** (2025-12-23, 61 págs.). SHA-256 del PDF: `59cc138112aa6a5c9f76cfad2a4b33828835702c00bdeb027f4ebbdbe187fecb`.
El PDF **no** se incluye en el repo (mismo criterio que Deye): aquí hay un resumen propio de las direcciones, escalas, estados y de la política de escritura. Quien necesite el original debe pedírselo al usuario / a Livoltek. Aplica a los modelos de la lista de la página 1 del PDF (PV conectado a red, almacenamiento monofásico —HP1, HES1, AES1, GF1— y trifásico —HP3, AC3, PCS—).

> **Estado: leído y transcrito, NADA validado en un equipo real.** Toda correspondencia con el esquema normalizado (B.0) y todo signo es **sin verificar** hasta la prueba en vivo. Los registros RO/RW se transcribieron a mano y se cruzaron con el texto del PDF (dirección y tipo en la misma fila: 162/162; nombre: 126/162 automático, el resto —nombres partidos en varias líneas— revisados sobre la imagen de la página).

## 1. Transporte y convenciones

| Tema | Lo que dice el PDF |
|---|---|
| Enlace | RS485 2 hilos, Modbus RTU, 9600 8N1 por defecto (esclavo 1-247 configurable, difusión sí); Ethernet opcional: IP por defecto 192.168.1.100, puerto 8080 (el PDF escribe la máscara como «255.225.255.1», errata) |
| Funciones | `0x03` leer holding · `0x06` escribir 1 registro · `0x10` escribir varios. **No** define `0x04`: los «Input Register (RO)» también se leen con `0x03` *(sin verificar en vivo)* |
| Direccionamiento | La dirección de la tabla va **tal cual** en la PDU, sin desplazamiento +40001: los ejemplos del PDF usan `0xA415` = 42005 (lectura) y `0xA700` = 42752 con valor `0x07E9` = 2025 (escritura del año del sistema) |
| Enteros de 32 bits | **Palabra baja primero**, luego la alta; bytes alto-bajo dentro de cada palabra (`0x01020304` → `03 04 01 02`). Cuidado con librerías que asumen el orden contrario |
| Negativos | Complemento a dos (`0xFFFF` = −1) |
| Decimales | El valor se transmite como entero escalado (10,333 kW → 10333); aquí «escala» = multiplicador a la unidad física |
| No soportado | El equipo responde todo `F`: `0xFFFF` (16 bit), `0xFFFFFFFF` (32 bit) → el adaptador debe leerlo como «sin dato», no como −1 |
| CRC | CRC-16 Modbus (poly `0xA001`, init `0xFFFF`) |

## 2. Registros de entrada (solo lectura, «RO»)

| Dirección | Nombre (como en el PDF) | Tipo | Escala / unidad | Notas |
|---|---|---|---|---|
| 42002 | Product Model | uint16 | — | Código de modelo: Apéndice 1 |
| 42004 | device type | uint16 | — | 1 PV monofásico; 2 PV trifásico; 3 almacenamiento monofásico; 4 almacenamiento trifásico; 5 off-grid monofásico; 6 off-grid trifásico; 7 AC-couple monofásico; 8 AC-couple trifásico; 9 PCS |
| 42005 | Rated Reactive Power | uint32 | ×0.01 kvar |  |
| 42007 | Rated Active Power | uint32 | ×0.01 kW |  |
| 42014 | Grid standard code | uint16 | — | Código de país/norma: Apéndice 2 |
| 42021 | Device SN | string | — | Longitud no indicada en el PDF |
| 42102–42103 | Protocol Ver. | uint32 | — |  |
| 42106–42120 | ARM Ver. | string | — |  |
| 42121–42135 | MasterDSP Ver. | string | — |  |
| 42136–42136 | SlaverDSP Ver. | string | — | El PDF imprime 42136-42136 (1 registro); probable errata (las otras versiones ocupan 15) |
| 42151–42165 | BMS Version | string | — |  |
| 42504 | Load active power | int32 | ×1 W |  |
| 42506 | Oper. status | uint16 | — | Enumeración 0x10xx (ver tabla de estados) |
| 42507 | BUS Voltage | uint16 | ×0.1 V |  |
| 42509 | PV array Insulation Resistance | uint16 | ×1 kΩ |  |
| 42512 | SM_Activepowe | int32 | ×1 W | Smart meter, total (el PDF imprime el nombre truncado) |
| 42514 | SM_Activepower_L1 | int32 | ×1 W | Smart meter, fase 1 |
| 42516 | SM_Activepower_L2 | int32 | ×1 W | Smart meter, fase 2 |
| 42518 | SM_Activepower_L3 | int32 | ×1 W | Smart meter, fase 3 |
| 42520 | Device Temperature | int16 | ×0.1 °C |  |
| 42521 | Total active power | int32 | ×1 W |  |
| 42523 | Total Reactive Power | int32 | ×1 var |  |
| 42525 | Total apparent power | uint32 | ×1 VA |  |
| 42527 | Total DC Power | int32 | ×1 W |  |
| 42529 | Total Power Factor | int16 | ×0.001 |  |
| 42530 | grid frequency | uint16 | ×0.01 Hz |  |
| 42531 | phase L1 voltage | uint16 | ×0.1 V |  |
| 42532 | phase L2 voltage | uint16 | ×0.1 V |  |
| 42533 | phase L3 voltage | uint16 | ×0.1 V |  |
| 42534 | phase L1 current | int16 | ×0.01 A |  |
| 42535 | phase L2 current | int16 | ×0.01 A |  |
| 42536 | phase L3 current | int16 | ×0.01 A |  |
| 42537 | Solar Energy Daily | uint16 | ×0.1 kWh |  |
| 42538 | month_pvenergy | uint32 | ×0.1 kWh |  |
| 42542 | ETotal-Solar | uint32 | ×0.1 kWh |  |
| 42544 | EToday-ExporttoGrid | uint16 | ×0.1 kWh |  |
| 42545 | total_export_energy | uint32 | ×0.1 kWh |  |
| 42547 | EToday-ImportfromGrid | uint16 | ×0.1 kWh |  |
| 42548 | total_import_energy | uint32 | ×0.1 kWh |  |
| 42550 | EToday-Load | int16 | ×0.1 kWh |  |
| 42551 | ETotal-Load | int32 | ×0.1 kWh |  |
| 42568 | PID status | uint16 | — | 0 inactivo; 2 recuperación PID; 4 protección PID; 8 anomalía PID (el changelog V1.01 dice que se eliminó PID, pero la fila sigue) |
| 42569 | PID fault code | uint16 | — | 0 sin falla; 432; 433; 434 |
| 42573 | fault number | uint16 | — |  |
| 42587 | Total_togrid_time | uint32 | ×1 h |  |
| 44605 | battery Voltage platform | uint16 | ×1 V | Solo inversores de almacenamiento |
| 44606 | battery Total Capacity | uint16 | ×1 Ah | Solo inversores de almacenamiento |
| 42590 | Battery Active Power | int32 | ×1 W | Signo no documentado |
| 42574–42583 | fault 1 … fault 10 | uint16 | — | Código de falla → Apéndice 3 (el PDF no dice qué valor significa «sin falla») |
| 42652 + 2·(N−1) | string voltage N (N = 1…24) | uint16 | ×0.1 V | Confirmar soporte de hardware (Apéndice 1) |
| 42653 + 2·(N−1) | string current N (N = 1…24) | int16 | ×0.01 A | idem |
| 42700 + 2·(N−1) | MPPT N voltage (N = 1…12) | uint16 | ×0.1 V | |
| 42701 + 2·(N−1) | MPPT N current (N = 1…12) | int16 | ×0.1 A | |

**Huecos importantes (no están en este PDF):** SOC, tensión/corriente/temperatura de batería, energías diarias y totales de carga/descarga de batería, `Battery Active Power` sin convención de signo. Esos datos solo se pueden obtener por la API de nube (ver `diccionario-metrum-livoltek.md`).

### Estados de operación (registro 42506)

| Valor | Estado | Valor | Estado |
|---|---|---|---|
| `0x1000` | on grid | `0x100D` | fault |
| `0x1001` | off grid | `0x100E` | AFCI self-test |
| `0x1002` | open loop | `0x100F` | not initial |
| `0x1003` | scheduling | `0x1010` | initial standby |
| `0x1004` | charging | `0x1012` | forced charging and discharging |
| `0x1005` | shutdown | `0x1013` | external ems dispatch |
| `0x1006` | switch off | `0x1014` | on grid emergency charging |
| `0x1007` | emergency stop | `0x1015` | off grid emergency charging |
| `0x1008` | standby | `0x1017` | diesel generator |
| `0x100A` | starting | `0x1018` | Battery activation charging |
| `0x100B` | alarm | `0x1019` | In arrear |
| `0x100C` | derating | `` |  |

El PDF no lista `0x1009`, `0x1011` ni `0x1016`: tratarlos como «desconocido».

## 3. Registros de retención (lectura/escritura, «RW») y nivel de política B.5

El PDF **no clasifica riesgo**; la columna «Nivel» la asigna este skill según B.5. Nivel 3 = **prohibido siempre** (`Refused`). Cualquier dirección que no esté en esta tabla (incluidos todos los RO) es **no escribible** (`classify_register()` → `None`).

| Dirección | Nombre | Tipo | Rango / enumeración | Escala / unidad | Nivel | Motivo |
|---|---|---|---|---|---|---|
| 42752 | system time: year | uint16 | 2000..2099 | año | **1** | Reloj del sistema (reversible; afecta el sello horario de eventos) |
| 42753 | system time: month | uint16 | 1..12 | mes | **1** | Reloj del sistema (reversible; afecta el sello horario de eventos) |
| 42754 | system time: day | uint16 | 1..31 | día | **1** | Reloj del sistema (reversible; afecta el sello horario de eventos) |
| 42755 | system time: hour | uint16 | 0..23 | h | **1** | Reloj del sistema (reversible; afecta el sello horario de eventos) |
| 42756 | system time: minute | uint16 | 0..59 | min | **1** | Reloj del sistema (reversible; afecta el sello horario de eventos) |
| 42757 | system time: second | uint16 | 0..59 | s | **1** | Reloj del sistema (reversible; afecta el sello horario de eventos) |
| 42758 | turn on /shutdown | uint16 | 0xCE apagar; 0xCF encender | — | **3** | Apagado/encendido remoto: mismo criterio que Deye reg 80 (B.5, nivel 3) |
| 42759 | enable emergency shutdown control | uint16 | 0xAA habilitar; 0x55 deshabilitar | — | **3** | Función de seguridad (parada de emergencia): nivel 3 |
| 42762 | reboot | uint16 | 0xAA | — | **2** | Reinicio del inversor: nivel 2 (política) |
| 42763 | reboot BMS | uint16 | 0xAA | — | **2** | Reinicio del BMS: nivel 2 (política) |
| 43714 | enable power limit | uint16 | 0xAA habilitar; 0x55 deshabilitar | — | **2** | Límite de potencia (red) |
| 43715 | limit power percent | uint16 | 0..(registro 42011) | ×0.1 % | **2** | Límite de potencia (red) |
| 43718 | Export to grid (Feed-in) limit mode | uint16 | 0xA0 sistema; 0xA1 potencia individual | — | **2** | Límite de exportación (equivalente a Deye 143/340) |
| 43719 | Export to grid (Feed-in) limit | uint16 | 0xAA habilitar; 0x55 deshabilitar | — | **2** | Límite de exportación |
| 43720 | Max.export power limit | uint16 | 0..1000 | ×0.1 % | **2** | Límite de exportación |
| 43736 | Limit by % or Value | uint16 | 0xA1 % de potencia nominal; 0xA2 valor de venta | ×1 | **2** | Límite de exportación |
| 43737 | Max.export power limi | int32 | 0..(registro 42007) | ×0.01 kW | **2** | Límite de exportación (nombre truncado en el PDF) |
| 43742 | PV Active Power Setpoint Feedback | uint16 | 0..(registro 42007) | ×0.01 kW | **2** | Consigna de potencia activa FV; listada como RW pese a llamarse 'Feedback' |
| 43607 | PF | int16 | -1000..-800 y 800..1000 | ×0.001 | **2** | Factor de potencia (red) |
| 43602 | SVG | uint16 | 0xAA habilitar; 0x55 deshabilitar | — | **2** | Compensación reactiva (red) |
| 43605 | Reactive control mode | uint16 | 0x55 cerrado; 0xA1 PF; 0xA2 Qt; 0xA3 Cos φ(P); 0xA4 Q(U) | — | **2** | Control reactivo (red) |
| 43606 | QT | int16 | -1000..1000 | ×0.1 % | **2** | Consigna reactiva (red) |
| 44002 | PID reqair enable | enum16 | 0xAA habilitar; 0x55 deshabilitar | — | **1** | Recuperación PID (nombre 'reqair' como en el PDF). El PDF no imprime el tipo (muestra 'enum16' en la columna de límite inferior): se trata como uint16. El changelog V1.01 dice que PID se eliminó |
| 43610 | qu_curve | uint16 | 0 curva A; 1 curva B; 2 curva C | — | **2** | Curva Q(U) (red) |
| 43624 | qp_curve | uint16 | 0 curva A; 1 curva B; 2 curva C (reserva) | — | **2** | Curva Q(P) (red) |
| 43721 | Control method(meter) | uint16 | 0 sin medidor; 0xA0 medidor monofásico; 0xA1 trifásico; 0xA4 CT externo; 0xA5 trifásico doble CT | — | **2** | Método de control por medidor/CT (determina el límite de exportación) |
| 43727 | Meter/CT flow self-test | uint16 | 0xAA habilitar; 0x55 deshabilitar | — | **1** | Autodiagnóstico de sentido de flujo; efecto no documentado |
| 43745 | watchdog time | uint16 | 0xAA habilitar; 0x55 deshabilitar | — | **2** | Solo inversores de almacenamiento. Nombre dice 'time' pero el rango es habilitar/deshabilitar (inconsistencia del PDF); control remoto con vigilancia |
| 43744 | charge /discharge commands | uint16 | (sin enumeración) | ×1 s | **2** | Solo almacenamiento. Despacho remoto de carga/descarga |
| 45004 | charge /discharge max.power | uint16 | 0xAA cargar; 0xBB descargar; 0xCC detener | — | **2** | Solo almacenamiento. Despacho remoto |
| 45005 | target endup SOC | uint16 | 0..(registro 42031) | ×0.01 kW | **2** | Solo almacenamiento. El PDF alinea el nombre 'target endup SOC' con 45005 pero la unidad 0,01 kW; 45006 no tiene nombre y su unidad es 1 %. Probable desalineación de la tabla: SIN VERIFICAR |
| 45006 | (sin nombre) | uint16 | (registro 44904)..(registro 44903) | ×1 % | **2** | Solo almacenamiento. Probable SOC objetivo final (ver nota en 45005): SIN VERIFICAR |

Resumen: 
- **Nivel 3 (prohibido):** 42758, 42759.
- **Nivel 2 (aprobación explícita y específica):** 42762, 42763, 43714, 43715, 43718, 43719, 43720, 43736, 43737, 43742, 43607, 43602, 43605, 43606, 43610, 43624, 43721, 43745, 43744, 45004, 45005, 45006.
- **Nivel 1 (confirmación + equipo piloto):** 42752, 42753, 42754, 42755, 42756, 42757, 44002, 43727.

**Peligrosos (fábrica, seguridad, firmware).** La V1.01 **no documenta** ningún registro de reseteo de fábrica, inicialización, bloqueo, calibración ni actualización de firmware (solo hay 32 registros RW). Por eso la regla es *lista blanca*: lo no documentado no se escribe jamás. Decisiones de diseño que el usuario puede revisar: 42758 (encender/apagar) y 42759 (parada de emergencia) se tratan como **nivel 3**, igual que el reg 80 de Deye (apagado/encendido remoto) y por ser función de seguridad; el reinicio del inversor (42762) y del BMS (42763) es nivel 2 (pedido del usuario). Los registros de despacho remoto (43744, 43745, 45004-45006) son nivel 2 por analogía con el modo remoto con *watchdog* de Deye (reg 1000-1121).

## 4. Correspondencia con el esquema normalizado (B.0) — **sin verificar**

| Campo normalizado | Registro | Conversión propuesta | Estado |
|---|---|---|---|
| `pv_power_w` | 42527 Total DC Power | ×1 W | sin verificar (¿incluye solo FV?) |
| `load_power_w` | 42504 Load active power | ×1 W | sin verificar |
| `grid_power_w` (+ = importación) | 42512 SM_Activepower (L1-L3: 42514/42516/42518) | ×1 W; **signo no documentado** | sin verificar: medir con importación conocida |
| `bat_power_w` (+ = carga) | 42590 Battery Active Power | ×1 W; **signo no documentado** | sin verificar |
| `soc_pct`, `bat_voltage_v`, `bat_current_a`, `bat_temp_c` | — | **no hay registro en el PDF** (solo 44605 tensión de plataforma y 44606 capacidad total) | solo API |
| `grid_voltage_v[3]` | 42531-42533 phase L1-L3 voltage | ×0.1 V | sin verificar (¿red o salida del inversor?) |
| `grid_freq_hz` | 42530 grid frequency | ×0.01 Hz | sin verificar |
| `energy_day_kwh.pv` / `.load` | 42537 / 42550 | ×0.1 kWh (42550 es int16 con signo) | sin verificar |
| `energy_day_kwh.import` / `.export` | 42547 / 42544 | ×0.1 kWh | sin verificar |
| `energy_total_kwh.pv/load/import/export` | 42542 / 42551 / 42548 / 42545 | ×0.1 kWh (uint32, palabra baja primero) | sin verificar |
| `energy_*.bat_charge/discharge` | — | **no hay registro en el PDF** | solo API |
| `grid_up` | 42531-42533 y 42530 | `min(tensiones) ≥ 20 V` (umbral heredado de Deye) | sin verificar |
| estado / alarmas | 42506, 42573-42583 | enumeración y Apéndice 3 | sin verificar |

## 5. Inconsistencias del PDF (anotadas, no corregidas)

- `SlaverDSP Ver.` figura como 42136-42136 (1 registro); las demás versiones ocupan 15: probable errata.
- `PID`: el historial de cambios de V1.01 dice «eliminar PID y modo de tres partes», pero siguen las filas 42568, 42569 y 44002 (esta última sin tipo impreso; muestra `enum16` en la columna de límite inferior).
- `watchdog time` (43745) tiene enumeración 0xAA/0x55 (habilitar/deshabilitar), no un tiempo.
- 45005 «target endup SOC» tiene unidad 0,01 kW y límite superior «dirección 42031», mientras 45006 (sin nombre) tiene unidad 1 % y límites «dirección 44904 / 44903»: la tabla parece desalineada una fila. **No escribir nunca sin confirmar con Livoltek.**
- `PF` (43607) lista límites inferior «−1000, 800» y superior «−800, 1000» (rangos [−1000, −800] y [800, 1000]).
- `Max.export power limi` (43737) y `SM_Activepowe` (42512) tienen el nombre truncado en el PDF.
- El texto genérico de §3.2 habla de «registro 40108» y de «dirección desde cero», pero los ejemplos usan la dirección de la tabla directamente.
- Apéndice 2: a partir del código 41 el PDF combina celdas; las filas siguientes (Hungría, Suecia, Genset, Polonia, Eslovaquia) no traen código impreso. «Sovakia» es errata de Eslovaquia.

## Apéndice 1 — Tipos de equipo (`Product Model`, registro 42002)

Código, número de MPPT y máximo de strings por MPPT. Categoría según la lista de modelos de la página 1 del PDF («sin categoría» = el nombre exacto no aparece en esa lista).

| Modelo | Código | MPPT | Strings/MPPT | Categoría |
|---|---|---|---|---|
| GT3-30KT1 | `0x8001` | 3 | 6 | red (PV conectado a red) |
| GT3-33KT1 | `0x8002` | 3 | 6 | red (PV conectado a red) |
| GT3-36KQ1 | `0x8003` | 4 | 8 | red (PV conectado a red) |
| GT3-37K5Q1 | `0x8004` | 4 | 8 | red (PV conectado a red) |
| GT3-40KQ1 | `0x8005` | 4 | 8 | red (PV conectado a red) |
| GT3-50KQ1 | `0x8006` | 4 | 8 | red (PV conectado a red) |
| GT3-15KTL1 | `0x800D` | 3 | 6 | red (PV conectado a red) |
| GT3-20KTL1 | `0x800E` | 3 | 6 | red (PV conectado a red) |
| GT3-30KT1C | `0x800F` | 3 | 6 | red (PV conectado a red) |
| GT3-25KQL1 | `0x8010` | 4 | 8 | red (PV conectado a red) |
| GT3-30KQL1 | `0x8011` | 4 | 8 | red (PV conectado a red) |
| GT1-3KD2 | `0x8007` | 2 | 2 | red (PV conectado a red) |
| GT1-3K3D2 | `0x8012` | 2 | 2 | red (PV conectado a red) |
| GT1-3K6D2 | `0x8008` | 2 | 2 | red (PV conectado a red) |
| GT1-4KD2 | `0x8009` | 2 | 2 | red (PV conectado a red) |
| GT1-5KD2 | `0x800A` | 2 | 2 | red (PV conectado a red) |
| GT1-6KD2 | `0x800B` | 2 | 2 | red (PV conectado a red) |
| GT1-2K5D2 | `0x800C` | 2 | 2 | red (PV conectado a red) |
| GT1-7KT2 | `0x8013` | 3 | 3 | red (PV conectado a red) |
| GT1-8KT2 | `0x8014` | 3 | 3 | red (PV conectado a red) |
| GT1-9KT2 | `0x8015` | 3 | 3 | red (PV conectado a red) |
| GT1-10KT2 | `0x8016` | 3 | 3 | red (PV conectado a red) |
| GT3-60KQ1 | `0x8017` | 4 | 8 | red (PV conectado a red) |
| HP3-5KD2 | `0x8018` | 2 | 2 | almacenamiento trifásico |
| HP3-6KD2 | `0x8019` | 2 | 2 | almacenamiento trifásico |
| HP3-8KD2 | `0x8020` | 2 | 2 | almacenamiento trifásico |
| HP3-10KD2 | `0x8021` | 2 | 3 | almacenamiento trifásico |
| HP3-12KD2 | `0x8022` | 2 | 3 | almacenamiento trifásico |
| HP3-15KD2 | `0x8023` | 3 | 5 | almacenamiento trifásico |
| HP3-20KT2 | `0x8024` | 3 | 5 | almacenamiento trifásico |
| HP3-25KT2 | `0x8025` | 3 | 6 | almacenamiento trifásico |
| HP3-30KT2 | `0x8026` | 3 | 6 | almacenamiento trifásico |
| GT1-5KD2C | `0x8027` | 2 | 2 | red (PV conectado a red) |
| HP3-9.9KD2 | `0x8028` | 2 | 2 | almacenamiento trifásico |
| HP3-14.9KT2 | `0x8029` | 3 | 5 | almacenamiento trifásico |
| HP3-29.9KT2 | `0x802A` | 3 | 6 | almacenamiento trifásico |
| GT3-50KQM1 | `0x802B` | 4 | 8 | red (PV conectado a red) |
| GT3-60KQM1 | `0x802C` | 4 | 8 | red (PV conectado a red) |
| GT3-75K-1 | `0x802D` | 8 | 16 | red (PV conectado a red) |
| GT3-100K-1 | `0x802E` | 10 | 20 | red (PV conectado a red) |
| GT3-110K-1 | `0x802F` | 10 | 20 | red (PV conectado a red) |
| GT3-125K-1 | `0x8030` | 10 | 20 | red (PV conectado a red) |
| AES1-3KG1 | `0x8031` | 0 | 0 | almacenamiento monofásico |
| AES1-3K6G1 | `0x8032` | 0 | 0 | almacenamiento monofásico |
| AES1-4K6G1 | `0x8033` | 0 | 0 | almacenamiento monofásico |
| AES1-5KG1 | `0x8034` | 0 | 0 | almacenamiento monofásico |
| AES1-3KEG1 | `0x8035` | 0 | 0 | almacenamiento monofásico |
| AES1-3K6EG1 | `0x8036` | 0 | 0 | almacenamiento monofásico |
| AES1-4K6EG1 | `0x8037` | 0 | 0 | almacenamiento monofásico |
| AES1-5KEG1 | `0x8038` | 0 | 0 | almacenamiento monofásico |
| GT1-7K5T2 | `0x8039` | 3 | 3 | red (PV conectado a red) |
| GT3-10KTL1 | `0x803A` | 3 | 6 | red (PV conectado a red) |
| GT3-30KTM1 | `0x803B` | 3 | 6 | red (PV conectado a red) |
| GT3-36KQM1 | `0x803C` | 4 | 8 | red (PV conectado a red) |
| GT3-40KQM1 | `0x803D` | 4 | 8 | red (PV conectado a red) |
| HP1-3KS2 | `0x803E` | 2 | 2 | almacenamiento monofásico |
| HP1-3K6S2 | `0x803F` | 2 | 2 | almacenamiento monofásico |
| HP1-5KS2 | `0x8040` | 2 | 2 | almacenamiento monofásico |
| HP1-6KS2 | `0x8041` | 2 | 2 | almacenamiento monofásico |
| HP1-7K5S2 | `0x8042` | 2 | 2 | almacenamiento monofásico |
| HP1-8KS2 | `0x8043` | 2 | 2 | almacenamiento monofásico |
| HP1-10KS2 | `0x8044` | 3 | 6 | almacenamiento monofásico |
| HP1-12KS2 | `0x8045` | 3 | 6 | almacenamiento monofásico |
| HP3-5KL2 | `0x804B` | 2 | 3 | almacenamiento trifásico |
| HP3-6KL2 | `0x804C` | 2 | 3 | almacenamiento trifásico |
| HP3-8KL2 | `0x804D` | 3 | 5 | almacenamiento trifásico |
| HP3-9.9KL2 | `0x804E` | 3 | 5 | almacenamiento trifásico |
| HP3-10KL2 | `0x804F` | 3 | 5 | almacenamiento trifásico |
| HP3-12KL2 | `0x8050` | 3 | 6 | almacenamiento trifásico |
| HP3-14.9KL2 | `0x8051` | 3 | 6 | almacenamiento trifásico |
| HP3-15KL2 | `0x8052` | 3 | 6 | almacenamiento trifásico |
| GT3-110K-11 | `0x8053` | 8 | 16 | red (PV conectado a red) |
| GT3-125K-11 | `0x8054` | 8 | 16 | red (PV conectado a red) |
| GT3-36KL1 | `0x8055` | 4 | 8 | red (PV conectado a red) |
| GT3-40KL1 | `0x8056` | 4 | 8 | red (PV conectado a red) |
| GT3-50KL1 | `0x8057` | 6 | 12 | red (PV conectado a red) |
| GT3-60KL1 | `0x8058` | 8 | 16 | red (PV conectado a red) |
| GT3-75KL1 | `0x8059` | 8 | 16 | red (PV conectado a red) |
| GT3-100KM1 | `0x805A` | 10 | 20 | red (PV conectado a red) |
| GT3-124KM1 | `0x805B` | 10 | 20 | red (PV conectado a red) |
| GT3-125KM1 | `0x805C` | 10 | 20 | red (PV conectado a red) |
| GT3-150KM1 | `0x805D` | 10 | 20 | red (PV conectado a red) |
| AES1-3KEL1 | `0x805E` | 0 | 0 | sin categoría en la lista de la página 1 |
| PCS-75KG1 | `0x805F` | 0 | 0 | almacenamiento trifásico |
| PCS-100KG1 | `0x8060` | 0 | 0 | almacenamiento trifásico |
| PCS-110KG1 | `0x8061` | 0 | 0 | almacenamiento trifásico |
| PCS-125KG1 | `0x8062` | 0 | 0 | almacenamiento trifásico |
| PCS-75KMG1 | `0x8063` | 0 | 0 | almacenamiento trifásico |
| PCS-100KMG1 | `0x8064` | 0 | 0 | almacenamiento trifásico |
| PCS-110KMG1 | `0x8065` | 0 | 0 | almacenamiento trifásico |
| PCS-125KMG1 | `0x8066` | 0 | 0 | almacenamiento trifásico |
| PCS-150KMG1 | `0x8067` | 0 | 0 | almacenamiento trifásico |
| PCS-135KG1 | `0x8068` | 0 | 0 | almacenamiento trifásico |
| PCS-135KMG1 | `0x8069` | 0 | 0 | almacenamiento trifásico |
| HP1-1K5L2 | `0x806A` | 1 | 1 | almacenamiento monofásico |
| HP1-3KL2 | `0x806B` | 2 | 2 | almacenamiento monofásico |
| HP1-4KL2 | `0x806C` | 2 | 2 | almacenamiento monofásico |
| HP1-5KL2 | `0x806D` | 2 | 4 | almacenamiento monofásico |
| HP1-6KL2 | `0x806E` | 2 | 4 | almacenamiento monofásico |
| HP1-7K5L2 | `0x806F` | 2 | 4 | almacenamiento monofásico |
| HP1-8KL2 | `0x8070` | 2 | 4 | almacenamiento monofásico |
| HP1-1K5S2 | `0x8071` | 1 | 1 | almacenamiento monofásico |
| HP1-5KS2C | `0x8072` | 2 | 2 | almacenamiento monofásico |
| HP1-7K5S2M | `0x8073` | 2 | 4 | almacenamiento monofásico |
| HP1-8KS2M | `0x8074` | 2 | 4 | almacenamiento monofásico |
| HP1-14KS2 | `0x8075` | 3 | 6 | almacenamiento monofásico |
| HP1-16KS2 | `0x8076` | 3 | 6 | almacenamiento monofásico |
| GT3-30KD1 | `0x8077` | 2 | 4 | red (PV conectado a red) |
| GT3-37K5T1 | `0x8078` | 3 | 6 | red (PV conectado a red) |
| GT3-15KDL1 | `0x8079` | 2 | 4 | red (PV conectado a red) |
| GT3-20KDL1 | `0x807A` | 2 | 4 | red (PV conectado a red) |
| GT3-25KDL1 | `0x807B` | 2 | 4 | red (PV conectado a red) |
| GT3-30KTL1 | `0x807C` | 3 | 6 | red (PV conectado a red) |
| GT3-75K-12 | `0x807D` | 4 | 8 | sin categoría en la lista de la página 1 |
| GT3-75K-11 | `0x807E` | 6 | 12 | sin categoría en la lista de la página 1 |
| GT3-100K-12 | `0x807F` | 6 | 12 | sin categoría en la lista de la página 1 |
| GT3-100K-11 | `0x8080` | 8 | 16 | sin categoría en la lista de la página 1 |
| GT3-110K-12 | `0x8081` | 6 | 12 | sin categoría en la lista de la página 1 |
| GT3-50KL11 | `0x8082` | 4 | 8 | sin categoría en la lista de la página 1 |
| GT3-60KL12 | `0x8083` | 4 | 8 | sin categoría en la lista de la página 1 |
| GT3-60KL11 | `0x8084` | 6 | 12 | sin categoría en la lista de la página 1 |
| GT3-75KL11 | `0x8085` | 6 | 12 | sin categoría en la lista de la página 1 |
| GT3-100KM11 | `0x8086` | 8 | 16 | sin categoría en la lista de la página 1 |
| GT3-124KM11 | `0x8087` | 8 | 16 | sin categoría en la lista de la página 1 |
| GT3-125KM11 | `0x8088` | 8 | 16 | sin categoría en la lista de la página 1 |
| GT3-36KL11 | `0x8089` | 6 | 12 | sin categoría en la lista de la página 1 |
| GT3-40KL11 | `0x808A` | 6 | 12 | sin categoría en la lista de la página 1 |
| GF1-3K6S2 | `0x808B` | 2 | 2 | almacenamiento monofásico |
| GF1-6KS2 | `0x808C` | 2 | 2 | almacenamiento monofásico |
| GF1-8KS2 | `0x808D` | 2 | 2 | almacenamiento monofásico |
| GF1-11KS2 | `0x808E` | 3 | 6 | almacenamiento monofásico |
| GF1-12KS2 | `0x808F` | 3 | 6 | almacenamiento monofásico |
| GF1-16KS2 | `0x8090` | 3 | 6 | almacenamiento monofásico |
| AC3-8KD2 | `0x8091` | 2 | 2 | almacenamiento trifásico |
| AC3-10KD2 | `0x8092` | 2 | 3 | sin categoría en la lista de la página 1 |
| HP3-40KS1 | `0x8093` | 5 | 10 | sin categoría en la lista de la página 1 |
| HP3-50KS1 | `0x8094` | 5 | 10 | sin categoría en la lista de la página 1 |
| HP3-60KS1 | `0x8095` | 5 | 10 | sin categoría en la lista de la página 1 |
| HP3-8KS1LV | `0x8096` | 1 | 2 | almacenamiento trifásico |
| HP3-10KS1LV | `0x8097` | 1 | 2 | almacenamiento trifásico |
| HP3-12KS1LV | `0x8098` | 2 | 3 | almacenamiento trifásico |
| HP3-15KS1LV | `0x8099` | 2 | 3 | almacenamiento trifásico |
| GF1-7K5S2M | `0x809A` | 2 | 4 | almacenamiento monofásico |
| GF1-8KS2M | `0x809B` | 2 | 4 | almacenamiento monofásico |
| GT3-37K5QL1 | `0x809C` | 4 | 8 | red (PV conectado a red) |
| HES1-3KS2 | `0x809D` | 2 | 2 | almacenamiento monofásico |
| HES1-3K6S2 | `0x809E` | 2 | 2 | almacenamiento monofásico |
| HES1-5KS2 | `0x809F` | 2 | 2 | almacenamiento monofásico |
| HES1-6KS2 | `0x80A0` | 2 | 2 | almacenamiento monofásico |
| HP3-15KM2 | `0x80A1` | 3 | 5 | almacenamiento trifásico |
| HP3-20KM2158 | `0x80A2` | 3 | 5 | almacenamiento trifásico |
| HP3-25KM2159 | `0x80A3` | 3 | 5 | almacenamiento trifásico |
| HP3-30KM2160 | `0x80A4` | 3 | 6 | almacenamiento trifásico |
| HP3-36KM2 | `0x80A5` | 3 | 6 | almacenamiento trifásico |
| HES1-5K5S2 | `0x80A6` | 2 | 2 | almacenamiento monofásico |

## Apéndice 2 — Norma de red (`Grid standard code`, registro 42014)

**Colombia = código 35 (IEC61727, 230 V, 60 Hz).** Tabla completa:

| Código | País / norma | Regulación | V normal | V baja | Hz |
|---|---|---|---|---|---|
| 0 | China (CQC) | CQC | 230 | — | 50 |
| 1 | Germany (VDE-AR-N 4105) | VDE-AR-N 4105 | 230 | — | 50 |
| 2 | United Kingdom (G83/G59) | G83/G59 | 230 | — | 50 |
| 3 | Australia_A (AS/NZS 4777) | AS/NZS 4777 | 230 | — | 50 |
| 4 | NewZealand (AS/NZS 4777) | AS/NZS 4777 | 230 | — | 50 |
| 5 | France_50Hz (UTE C 15-712) | UTE C 15-712 | 230 | — | 50 |
| 6 | Spain (RD 1699/244 &UNE&NTS) | RD 1699/244 &UNE&NTS | 230 | — | 50 |
| 7 | Italy (CEI 0-21 & CEI 0-21-Bbis) | CEI 0-21 & CEI 0-21-Bbis | 230 | — | 50 |
| 8 | Netherlands (EN 50549) | EN 50549 | 230 | — | 50 |
| 9 | Belgium (C10/11) | C10/11 | 230 | — | 50 |
| 10 | Ireland (EN 50549-1) | EN 50549-1 | 230 | — | 50 |
| 11 | France_60Hz (UTE C 15-712-1) | UTE C 15-712- 1 | 230 | — | 60 |
| 12 | General (IEC 61727) | IEC 61727 | 230 | 127 | 50 |
| 13 | Czech (EN 50549) | EN 50549 | 230 | — | 50 |
| 14 | France_M50Hz (UTE C 15-712-1) | UTE C 15-712- 1 | 230 | — | 50 |
| 15 | Unitied Kingdom (G99) | G99 | 230 | — | 50 |
| 16 | South Africa (NRS 097-2-1) | NRS 097-2-1 | 230 | — | 50 |
| 17 | PAIOnly (R&D) | R&D | 230 | — | 50 |
| 18 | EN50549 (EN 50549-1) | EN 50549-1 | 230 | — | 50 |
| 19 | Unitied Kingdom (G100) | G100 | 230 | — | 50 |
| 20 | Brazil (ABNT NBR 16149/16150) | ABNT NBR 16149/16150 | 220 | 127 | 60 |
| 21 | Mexico (IEEE 1547) | IEEE 1547 | 220 | — | 60 |
| 22 | Poland (EN 50549) | EN 50549 | 230 | — | 50 |
| 23 | Luxembourg (EN 50549) | EN 50549 | 230 | — | 50 |
| 24 | Thailand (PEA) | PEA | 220 | — | 50 |
| 25 | Thailand (MEA) | MEA | 230 | — | 50 |
| 26 | Australia_B (AS/NZS 4777.2) | AS/NZS 4777.2 | 230 | — | 50 |
| 27 | Australia_C (AS/NZS 4777.2) | AS/NZS 4777.2 | 230 | — | 50 |
| 28 | Portugal (EN 50549) | EN 50549 | 230 | — | 50 |
| 29 | Romania (EN 50549) | EN 50549 | 230 | — | 50 |
| 30 | Austria (TOR Erzeuger OVE-Richtlinie R 25) | OVE-Richtlinie | 230 | — | 50 |
| 31 | General_60Hz (IEC61727) | IEC61727 | 230 | 127 | 60 |
| 32 | Unitied Kingdom (G98) | G98 | 230 | — | 50 |
| 33 | North Ireland (G98-NI) | G98-NI | 230 | — | 50 |
| 34 | North Ireland (G99-NI) | G99-NI | 230 | — | 50 |
| 35 | Colombia (IEC61727) | IEC61727 | 230 | — | 60 |
| 36 | Brazil (Ordinance No. 140) | Ordinance No. 140 | 220 | 127 | 60 |
| 37 | Chile(SEC 32427) | SEC 32427 | 220 | 127 | 50 |
| 38 | EN50549 (EN 50549-10) | EN 50549-10 | 230 | — | 50 |
| 39 | Other_50Hz | Other_50Hz | 230 | 127 | 50 |
| 40 | Other_60Hz | Other_60Hz | 230 | 127 | 60 |
| 41 | Ukraine (EN50549-1) | EN50549-1 | 230 | — | 50 |
| — | Hungary (EN50549-1) | EN50549-1 | 230 | — | 50 |
| — | Sweden (EN50549-1) | EN50549-1 | 230 | — | 50 |
| — | Genset_50Hz | Genset_50Hz | 230 | — | 50 |
| — | Genset_60Hz | Genset_60Hz | 230 | — | 50 |
| — | Poland (TypeB-sN) | PTPiREE 2024-10-01 (bn_2024-10-01) | 230 | — | 50 |
| — | Poland (TypeB-nN) | PTPiREE 2024-10-01 (bn_2024-10-01) | 230 | — | 50 |
| — | Poland (TypeA) | PTPiREE 2024-10-01 (bn_2024-10-01) | 230 | — | 50 |
| — | Sovakia (TypeA) *(El PDF escribe 'Sovakia' (Eslovaquia))* | Techinical codintions of the distribution system operator (texto tal cual del PDF) | 230 | — | 50 |
| — | Sovakia (TypeB) *(El PDF escribe 'Sovakia' (Eslovaquia))* | Techinical codintions of the distribution system operator (texto tal cual del PDF) | 230 | — | 50 |

## Apéndice 3 — Códigos de falla y alerta (registros 42574-42583)

277 códigos (193 `fault`, 84 `warn`). Columnas de soporte: PV monofásico / PV trifásico / almacenamiento (√ = el equipo soporta ese código). Muchos códigos se llaman solo «System fault»: el código, no el nombre, identifica la falla.

| Código | Tipo | Nombre | PV 1F | PV 3F | ESS |
|---|---|---|---|---|---|
| 1 | warn | Grid Overvoltage | √ | √ | √ |
| 2 | warn | Grid Overvoltage | √ | √ | √ |
| 3 | warn | Grid Undervolt | √ | √ | √ |
| 4 | warn | Grid Undervolt | × | √ | √ |
| 5 | fault | reverse connection fault | √ | √ | √ |
| 6 | fault | System fault | √ | × | √ |
| 7 | warn | Grid Overfrequency | √ | √ | √ |
| 8 | warn | Grid Underfrequency | √ | √ | √ |
| 9 | warn | Grid Power Loss | √ | √ | √ |
| 10 | fault | System fault | √ | √ | √ |
| 11 | fault | Exceeds | √ | √ | √ |
| 12 | warn | Grid Abnormal | √ | √ | √ |
| 13 | warn | Grid Overvoltage | √ | √ | √ |
| 14 | warn | Grid Overvoltage | × | √ | × |
| 15 | fault | System fault | × | × | √ |
| 16 | warn | Grid Volt Imbalance | × | √ | √ |
| 17 | fault | System fault | √ | √ | √ |
| 18 | warn | System fault | × | × | × |
| 21 | fault | System fault | × | × | × |
| 22 | warn | System fault | √ | × | √ |
| 23 | fault | PE Abnormal | √ | √ | √ |
| 24 | fault | System fault | × | × | √ |
| 25 | fault | System fault | × | × | × |
| 26 | fault | System fault | × | × | × |
| 27 | fault | System fault | × | × | × |
| 28 | fault | System fault | × | × | × |
| 29 | fault | System fault | × | × | × |
| 30 | fault | System fault | × | × | √ |
| 33 | fault | System fault | √ | √ | √ |
| 34 | fault | System fault | √ | √ | √ |
| 35 | fault | System fault | √ | × | × |
| 36 | fault | System fault | √ | × | × |
| 37 | fault | System fault | × | × | × |
| 38 | fault | System fault | × | √ | √ |
| 39 | fault | System fault | × | √ | √ |
| 40 | fault | System fault | × | × | √ |
| 41 | fault | System fault | × | × | √ |
| 42 | fault | MPPT reverse connection fault | √ | × | √ |
| 43 | fault | MPPT reverse connection fault | √ | × | √ |
| 44 | fault | System fault | × | × | × |
| 45 | fault | System fault | × | × | × |
| 46 | fault | System fault | × | × | × |
| 47 | fault | System fault | × | × | × |
| 48 | fault | System fault | × | × | × |
| 49 | fault | System fault | √ | √ | √ |
| 50 | fault | System fault | × | × | √ |
| 51 | fault | System fault | √ | √ | √ |
| 52 | fault | System fault | × | × | × |
| 53 | fault | System fault | × | √ | √ |
| 54 | fault | System fault | × | √ | √ |
| 55 | fault | System fault | × | × | × |
| 56 | fault | System fault | √ | × | × |
| 57 | fault | MPPT reverse connection fault | √ | √ | √ |
| 58 | fault | System fault | × | × | √ |
| 59 | fault | System fault | × | √ | √ |
| 60 | fault | System fault | × | × | √ |
| 61 | fault | System fault | × | √ | × |
| 62 | fault | System fault | × | √ | × |
| 63 | fault | System fault | × | √ | × |
| 64 | fault | System fault | × | √ | × |
| 65 | fault | System fault | × | √ | √ |
| 66 | fault | System fault | × | √ | × |
| 67 | fault | System fault | × | √ | × |
| 68 | fault | System fault | × | × | √ |
| 69 | fault | System fault | × | × | √ |
| 71 | fault | System fault | √ | × | √ |
| 72 | fault | System fault | × | × | × |
| 73 | fault | System fault | × | × | × |
| 74 | fault | System fault | √ | × | √ |
| 75 | fault | System fault | × | × | √ |
| 76 | fault | System fault | × | × | √ |
| 77 | fault | System fault | √ | × | √ |
| 78 | fault | System fault | × | × | √ |
| 79 | fault | System fault | × | × | √ |
| 80 | fault | System fault | √ | × | √ |
| 81 | fault | System fault | √ | × | √ |
| 82 | fault | System fault | × | × | × |
| 83 | fault | System fault | × | × | × |
| 84 | fault | System fault | × | √ | × |
| 85 | fault | System fault | × | √ | √ |
| 86 | fault | System fault | × | × | √ |
| 89 | fault | System fault | √ | × | √ |
| 90 | fault | System fault | × | × | × |
| 91 | fault | System fault | × | × | × |
| 92 | fault | System fault | × | × | × |
| 97 | fault | System fault | √ | √ | √ |
| 98 | fault | Environmental Temp Too High | √ | √ | √ |
| 99 | fault | System fault | √ | √ | √ |
| 100 | fault | Insulation | √ | × | √ |
| 101 | fault | System fault | × | √ | √ |
| 102 | fault | System fault | √ | × | √ |
| 103 | fault | System fault | × | √ | √ |
| 104 | warn | Environmental Temp Too Low | √ | √ | √ |
| 105 | fault | System fault | √ | × | √ |
| 106 | fault | System fault | × | × | √ |
| 107 | fault | System fault | × | × | √ |
| 108 | fault | System fault | × | × | √ |
| 109 | fault | System fault | √ | √ | √ |
| 110 | fault | System fault | × | √ | √ |
| 111 | fault | System fault | × | √ | √ |
| 112 | fault | System fault | × | × | √ |
| 113 | fault | System fault | × | × | √ |
| 114 | fault | System fault | × | × | √ |
| 115 | fault | System fault | × | × | √ |
| 116 | fault | System fault | × | × | √ |
| 117 | fault | System fault | × | × | × |
| 118 | fault | System fault | × | × | × |
| 119 | fault | System fault | × | × | √ |
| 120 | fault | System fault | × | × | √ |
| 121 | fault | System fault | × | × | √ |
| 122 | fault | System fault | × | × | √ |
| 123 | fault | System fault | × | × | √ |
| 124 | fault | System fault | × | × | √ |
| 125 | fault | System fault | × | × | √ |
| 126 | fault | System fault | × | × | √ |
| 127 | fault | System fault | × | × | √ |
| 128 | fault | System fault | × | × | √ |
| 129 | fault | System fault | √ | × | √ |
| 130 | fault | System fault | √ | × | √ |
| 131 | fault | System fault | √ | × | √ |
| 132 | fault | System fault | √ | × | √ |
| 133 | fault | System fault | × | × | √ |
| 134 | fault | System fault | × | × | √ |
| 135 | warn | Sstem warm | × | × | √ |
| 136 | fault | System fault | × | × | √ |
| 137 | fault | System fault | × | × | √ |
| 138 | fault | System fault | × | × | √ |
| 139 | fault | System fault | × | × | √ |
| 140 | fault | System fault | × | × | √ |
| 141 | fault | System fault | × | × | √ |
| 142 | fault | System fault | × | × | √ |
| 143 | fault | System fault | × | × | √ |
| 147 | fault | System fault | × | × | √ |
| 161 | warn | Sstem warm | √ | √ | √ |
| 162 | warn | Sstem warm | × | √ | √ |
| 163 | warn | Sstem warm | √ | √ | √ |
| 165 | warn | Sstem warm | × | × | √ |
| 167 | warn | Sstem warm | × | × | × |
| 168 | warn | Sstem warm | × | × | × |
| 169 | warn | Sstem warm | × | √ | × |
| 170 | warn | Sstem warm | × | √ | × |
| 171 | warn | Sstem warm | × | √ | × |
| 172 | warn | Sstem warm | × | √ | × |
| 173 | warn | Sstem warm | × | × | × |
| 174 | warn | Sstem warm | × | √ | √ |
| 175 | warn | Sstem warm | × | × | √ |
| 176 | warn | Sstem warm | × | × | √ |
| 177 | warn | Sstem warm | × | × | × |
| 178 | warn | Sstem warm | × | × | × |
| 179 | warn | Sstem warm | × | × | × |
| 180 | warn | Sstem warm | √ | × | √ |
| 181 | warn | Sstem warm | √ | × | √ |
| 182 | warn | Sstem warm | √ | × | √ |
| 183 | warn | Sstem warm | √ | × | √ |
| 184 | warn | Sstem warm | × | × | √ |
| 185 | warn | Sstem warm | × | × | √ |
| 186 | warn | Sstem warm | × | × | × |
| 187 | warn | Sstem warm | × | × | × |
| 188 | warn | Sstem warm | × | × | × |
| 189 | warn | Sstem warm | × | × | × |
| 190 | warn | Sstem warm | × | × | × |
| 192 | warn | Sstem warm | × | × | × |
| 194 | warn | Sstem warm | × | × | √ |
| 195 | warn | Sstem warm | × | × | × |
| 197 | warn | Sstem warm | × | × | × |
| 198 | warn | Sstem warm | × | × | × |
| 199 | warn | Sstem warm | × | × | × |
| 200 | warn | Sstem warm | × | × | × |
| 201 | warn | Sstem warm | × | × | × |
| 202 | warn | Sstem warm | × | × | × |
| 203 | warn | Sstem warm | × | × | × |
| 204 | warn | Sstem warm | × | × | × |
| 205 | warn | Sstem warm | × | × | × |
| 206 | warn | Sstem warm | × | × | × |
| 207 | warn | Sstem warm | × | × | × |
| 208 | warn | Sstem warm | × | × | × |
| 209 | warn | Sstem warm | × | × | √ |
| 210 | warn | Sstem warm | × | × | √ |
| 211 | warn | Sstem warm | × | × | √ |
| 212 | warn | Sstem warm | × | × | √ |
| 213 | warn | Sstem warm | × | × | √ |
| 214 | warn | Sstem warm | × | × | √ |
| 215 | warn | Sstem warm | × | × | √ |
| 226 | fault | System fault | × | × | × |
| 227 | fault | System fault | × | × | × |
| 228 | fault | System fault | × | × | × |
| 229 | fault | System fault | × | × | × |
| 230 | fault | System fault | × | × | × |
| 231 | fault | System fault | × | × | × |
| 232 | fault | System fault | × | × | × |
| 233 | fault | System fault | × | × | × |
| 234 | fault | System fault | × | × | × |
| 235 | fault | System fault | × | × | × |
| 236 | fault | System fault | × | × | × |
| 257 | fault | System fault | × | × | √ |
| 258 | fault | System fault | × | × | √ |
| 261 | fault | System fault | × | × | √ |
| 262 | fault | System fault | × | × | √ |
| 263 | fault | System fault | × | × | √ |
| 265 | fault | System fault | × | × | √ |
| 269 | fault | System fault | × | × | √ |
| 273 | fault | System fault | × | × | √ |
| 277 | fault | System fault | × | × | √ |
| 281 | fault | System fault | × | × | √ |
| 321 | fault | Battery fault | × | × | √ |
| 324 | fault | Battery fault | × | × | √ |
| 332 | fault | Battery fault | × | × | √ |
| 333 | fault | Battery fault | × | × | √ |
| 335 | warn | Communication | × | × | √ |
| 336 | fault | Battery fault | × | × | √ |
| 337 | fault | Battery Reverse Polarity Fault | × | × | √ |
| 353 | warn | Sstem warm | × | × | √ |
| 354 | warn | Sstem warm | × | × | √ |
| 419 | warn | Sstem warm | × | × | × |
| 422 | fault | System fault | × | × | × |
| 423 | fault | System fault | × | × | × |
| 424 | warn | Sstem warm | × | √ | × |
| 425 | warn | Sstem warm | × | √ | × |
| 426 | warn | Sstem warm | × | √ | × |
| 427 | warn | Sstem warm | × | √ | × |
| 428 | warn | Sstem warm | × | √ | × |
| 429 | warn | Sstem warm | × | √ | × |
| 430 | warn | Sstem warm | × | √ | × |
| 449 | fault | MPPT reverse connection fault | √ | × | × |
| 450 | fault | MPPT reverse connection fault | √ | × | × |
| 451 | fault | MPPT reverse connection fault | √ | × | × |
| 452 | fault | MPPT reverse connection fault | √ | × | × |
| 453 | fault | MPPT reverse connection fault | √ | × | × |
| 454 | fault | MPPT reverse connection fault | √ | × | × |
| 455 | fault | MPPT reverse connection fault | √ | × | × |
| 513 | warn | Sstem warm | × | √ | × |
| 514 | warn | Sstem warm | × | √ | × |
| 515 | warn | Sstem warm | × | × | × |
| 516 | fault | AFCI fault | √ | √ | × |
| 517 | fault | System fault | × | × | × |
| 518 | warn | Communication | √ | × | × |
| 519 | fault | System fault | × | × | × |
| 520 | warn | Fan warn | × | √ | × |
| 521 | warn | Fan warn | × | √ | × |
| 522 | warn | Fan warn | × | × | × |
| 523 | warn | Electricity Meter Reversed | × | × | √ |
| 524 | fault | System fault | × | × | √ |
| 525 | fault | System fault | × | × | √ |
| 526 | fault | Fire alarm | × | × | √ |
| 527 | fault | Fire alarm | × | × | √ |
| 528 | fault | Fire alarm | × | × | √ |
| 529 | fault | Fire alarm | × | × | √ |
| 530 | fault | Fire alarm | × | × | √ |
| 531 | fault | Fire alarm | × | × | √ |
| 532 | fault | Fire alarm | × | × | √ |
| 533 | fault | Fire alarm | × | × | √ |
| 545 | fault | Battery warn | × | × | √ |
| 546 | fault | Battery warn | × | × | √ |
| 547 | fault | Battery warn | × | × | √ |
| 548 | fault | Battery warn | × | × | √ |
| 549 | fault | Battery warn | × | × | √ |
| 550 | fault | Battery warn | × | × | √ |
| 551 | fault | Battery warn | × | × | √ |
| 552 | fault | Battery warn | × | × | √ |
| 553 | fault | Battery warn | × | × | √ |
| 577 | fault | Battery fault | × | × | √ |
| 578 | fault | Battery fault | × | × | √ |
| 579 | fault | Battery fault | × | × | √ |
| 580 | fault | Battery fault | × | × | √ |
| 581 | fault | Battery fault | × | × | √ |
| 582 | fault | Battery fault | × | × | √ |
| 583 | fault | Battery fault | × | × | √ |
| 584 | fault | Battery fault | × | × | √ |
| 585 | fault | Battery fault | × | × | √ |
| 586 | fault | Battery fault | × | × | √ |
| 587 | fault | Battery fault | × | × | √ |
| 588 | fault | Battery fault | × | × | √ |
| 589 | fault | Battery fault | × | × | √ |
| 590 | fault | Battery fault | × | × | √ |
| 591 | fault | Battery fault | × | × | √ |
| 592 | fault | Battery fault | × | × | √ |
| 593 | fault | Battery fault | × | × | √ |

