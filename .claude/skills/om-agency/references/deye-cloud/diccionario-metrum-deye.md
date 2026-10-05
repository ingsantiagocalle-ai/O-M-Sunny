# Diccionario Metrum → DeyeCloud → registro Modbus

Fuente de los registros: PDF "Deye SUN Inverter Modbus" (Modbus RTU trifásico, **v105**,
2023-10). El PDF **no** se incluye en el repo (su portada prohíbe la reproducción); aquí
solo hay un resumen propio de los registros usados. Quien lo necesite debe pedírselo al
usuario / a Deye.

Validado el 2026-10-05 en el inversor **2412240078** (Casa 10, Reservas de Pance;
DEYE SUN-15K-SG01HP3, productId `0_5412_1`, HV trifásico) alineando 189 muestras de
Metrum (≈15 min) con la trama de Deye más cercana (±3 min) y, para potencias/corrientes,
filtrando tramos estables. Estado: **C** = confirmado con datos; **H** = hipótesis.

Los valores de la API de Deye ya vienen escalados. En HV trifásico los registros de
potencia están en unidades de 10 W (la API devuelve W). Si algún día se leen registros
crudos por Modbus, aplicar ese factor.

## 1. Energía (acumuladores) — **C**: r = 1,000; Metrum Wh = Deye kWh × 1000

| Metrum | Punto Deye | Registro PDF | Nota |
|---|---|---|---|
| `energyPD` (Wh) | `DailyActiveProduction` | 501 (0,1 kWh) | **H** registro: `PVDailyPowerGenerationActive` (≈529) es idéntico en 511/511 tramas |
| `energyLD` / `energyLT` | `DailyConsumption` / `TotalConsumption` | 526 / 527-528 | |
| `energyID` / `energyIT` | `DailyEnergyPurchased` / `TotalEnergyBuy` | 520 / 522-523 | |
| `energyED` / `energyET` | `DailyGridFeedIn` / `TotalEnergySell` | 521 / 524-525 | `energyED` = 0 los dos días |
| `energyAE` (= `CenergyAE`) | `TotalActiveProduction` | 504-505 | en este inversor sí es la generación total acumulada |
| — (sin clave en Metrum) | `DailyChargingEnergy` / `DailyDischargingEnergy` | 514 / 515 | contador real de energía de batería |
| — | `TotalChargeEnergy` / `TotalDischargeEnergy` | 516-517 / 518-519 | |

- Los contadores diarios de Metrum no se reinician exactamente a 00:00 → para el cierre
  del día tomar el último valor < 24:00 local (no `max()` del día: arrastra el día previo).
- Resolución de Deye = 0,1 kWh: diferencias < 0,05 kWh no son medibles.
- Los contadores diarios del inversor en Metrum son idénticos a los de la nube de Deye.

## 2. Batería

| Metrum | Punto Deye | Registro | Escala / signo | Estado |
|---|---|---|---|---|
| `BattSOC` (%) | `SOC` / `BMSSOC` | 588 / BMS 10005 | 1:1 (r = 1,000) | **C** |
| `BattVolt` (V) | `BatteryVoltage` | 587 | 1:1 | **C** |
| `BattPower` (W) | `BatteryPower` | 590 | 1:1; **+ = descarga, − = carga** (SOC baja con P>0 en 46/46 pasos y sube con P<0 en 42/42); P ≈ V·I (±1,7 %) | **C** |
| `BattCur` (A) | `BatteryCurrent` | 591 | 1:1 en magnitud, **signo invertido** (ratio −0,987): en Metrum `BattCur` + = carga, opuesto a `BattPower` | **C** |
| `BattTemp` (°C) | `Temperature- Battery` | 586 | 1:1 (r = 0,998); Metrum la entrega en enteros | **C** |
| `BattSOH` (%) | — (la nube no expone el SOH de la batería 1) | BMS 10006 | constante 97 | **H** |
| `BattCapAH_DY` (Ah) | `BatteryRatedCapacity` = `config.battCapacity` = 40 | 102 (configurada) | constante 40 en ambas | **C** valor / **H** registro (102 vs 592 vs 10007) |
| `BattCharges_DY` | — | — | **No es un contador de cargas.** Rango 32,6–35,5; proporcional a la tensión de batería (÷12,78 ±1 %; se descartó ÷13 módulos). Sin identificar | **H** |

## 3. Red / AC / cargas

| Metrum | Punto Deye | Registro | Escala / signo | Estado |
|---|---|---|---|---|
| `voltGridA/B/C` (V) | `GridVoltageL1/L2/L3` | 598-600 | 1:1 (r = 1,000) | **C** |
| `voltageA/B/C` (V) | `ACVoltageRUA/SVB/TWC` | 627-629 | 1:1 (≤ 0,3 %); fases A=R, B=S, C=T por nombre (las tres tensiones son casi idénticas) | **C** nivel / **H** fase |
| `voltEpsA/B/C` (V) | `LoadVoltageL1/L2/L3` | 644-646 | 1:1 (≤ 1 %) | **C** nivel / **H** fase |
| `curGridA/B/C` (A) | `GridCurrentL1/L2/L3` | 610-612 (interna) | ratio 1,00; MAE 0,03–0,06 A | **C** punto / **H** registro (610-612 vs 613-615) |
| `currentA/B/C` (A) | `ACCurrentRUA/SVB/TWC` | 630-632 | ratio 1,00; MAE 0,2–0,4 A | **C** |
| `frequency`, `freqEps` (Hz) | `ACOutputFrequencyR` ≈ `LoadFrequency` | 638 / 655 | dif 0,000; MAE 0,02 Hz. **No es la frecuencia de red** (`GridFrequency`, reg 609, vale 0 sin red; Metrum sigue en ~60) | **C** |
| `powerAEg` = `powerAPg` | ≈ `TotalConsumptionPower` (= `UPSLoadPower`) | 653 / 643 | ratio 1,00; MAE ≈ 15 W; idénticas entre sí 190/190. **No es generación PV** (`TotalSolarPower` da ratio 0,86) | **C** punto / **H** registro |
| `powerAE` | ídem; difiere de `powerAEg` en 133/190 muestras | — | | **H** |
| `LoadPower_DY` (W) | `TotalGridPower` | 625 (+690 alto) | **+ = importación**; MAE 3,5 W (7/8 positivos al importar; 2/2 negativos al exportar). **No es la carga** a pesar del nombre | **C** probable (≈) |
| `ExportGrid_DY` (W) | `TotalExternalCTPower` | 619 (+708) | ratio 1,000; MAE 0,3 W. **No es exportación**: lectura del CT externo, ≈ 4 W fijos por fase | **C** punto / **H** interpretación |
| `MeterState_DY` | — | 343 bit 0 (0 = CT, 1 = Meter) | siempre `ct` | **H** |
| `invrun` / `invstate` | alertas Deye / `deviceState` | 500 (0 standby, 1 autochequeo, 2 normal, 3 alarma, 4 fallo, 5 activando) | el único `fault` de Metrum (3-oct 19:15) coincide con la alarma Deye F18 y con el regreso de la red | **C** correlación / **H** registro |

## 4. Configuración (device/config/*) ↔ registros de escritura

| API Deye | Valor Casa 10 | Registro PDF | Estado |
|---|---|---|---|
| `system.systemWorkMode` | `ZERO_EXPORT_TO_LOAD` | 142 (0 vende, 1 interno, 2 externo) | **H** |
| `system.energyPattern` | `BATTERY_FIRST` | 141 bits 0-1 (10 = battery first, 11 = load first) | **C** |
| `system.maxSellPower` | 1000 W | 143 (1 W LV / 10 W HV) | **C** |
| `system.maxSolarPower` | 15000 W | 340 | **H** |
| `system.zeroExportPower` | 0 | 104 | **H** |
| `battery.battCapacity` | 40 Ah | 102 | **C** |
| `battery.maxCharge/DischargeCurrent` | 40 A / 40 A | 107 / 108 (0-185 A) | **C** |
| `battery.battLowCapacity` | 15 % | 117 | **C** |
| `battery.battShutDownCapacity` | 10 % | 115 | **C** |
| `tou.touAction` / `timeUseSettingItems` | `on` / 6 franjas | 146 (bit 0 + bits 1-7 días) · 148-153 hora (HHMM) · 154-159 potencia · 160-165 tensión objetivo · 166-171 SOC · 172-177 carga red/gen | **C** por nombre |

## 5. Registros Modbus — resumen propio (PDF v105)

Función 03 lectura / 10 escritura. Escribibles: 60–499 y 1000–1121. Solo lectura:
0–59, 500–999, 10000+ (batería Deye, protocolo del pack).

| Rango | Contenido |
|---|---|
| 500 | Estado de operación |
| 501-535 | Energías día/total: generación, batería, red compra/venta, carga, PV |
| 553-558 | Palabras de advertencia (553-554) y de fallo (555-558) |
| 586-592 | Batería 1: temperatura, tensión, SOC, potencia, corriente, capacidad corregida (Ah) |
| 598-625, 687-709 | Red: tensiones, corrientes, potencias (palabra baja/alta), frecuencia 609, CT externo 613-620 |
| 626-639 | Salida del inversor: tensiones, corrientes, potencias, frecuencia |
| 640-659 | Carga UPS / carga: potencias, tensiones 644-646, frecuencia 655 |
| 660-671 | Puerto del generador |
| 672-683 | PV: potencia (672-675), tensión/corriente (676-683) |
| 10000-10069 | BMS del pack Deye: SOC 10005, SOH 10006, capacidad restante 10007 |
| 60-125 | Parámetros generales y de batería (98 tipo, 102 capacidad, 104 exportación cero, 107/108 corrientes, 115-120 SOC/tensión) |
| 126-177 | Carga red/gen, energía 141, exportación 142-145, TOU 146-177 |
| 340-492 | Red/seguridad: venta máx. 340, CT 343-346, umbrales y curvas V/F, LVRT/HVRT |
| 1100-1121 | Modo remoto (1100 habilita, 1101 watchdog) y consigna de potencia ±120 % |

**Nunca escribir (nivel 3):** 81 (reseteo de fábrica; =3 bloquea el inversor), 91/92
(inicializa EEPROM; 92 =3 bloquea), 60/93/94/97 (solo fábrica), 80 (apagado/encendido),
559-583, 738-739, 800 y la banda 190-210 (ARC/calibración; banda conservadora). La
política completa y su aplicación en código están en `scripts/deye_adapter.py`
(`classify_register`) y en SKILL.md B.5.
