# Validación — Casa 10 (Reservas de Pance), inversor 2412240078, 3–5 oct 2026

Solo lectura. DEYE SUN-15K-SG01HP3 (HV trifásico), zona America/Bogota. Cuenta de empresa
(companyId en `DEYE_COMPANY_ID`): 67 equipos = 16 inversores, 16 recolectores, 35 baterías (60 en línea,
7 fuera de línea; 15 inversores `0_5412_1` y 1 `0_5411_1`).

## 1. Deye frente a la referencia de Metrum

| kWh | Sáb 3-oct Deye | Referencia Metrum | Δ | Dom 4-oct Deye | Referencia Metrum | Δ |
|---|---|---|---|---|---|---|
| Generación | 21,60 | 21,6 | 0,0 % | 5,70 | 5,8 | −1,7 % |
| Consumo | 12,50 | ~12,4 | +0,8 % | 1,30 | ~1,3 | 0 % |
| Importación | 0,40 | 0,41 | −2,4 % | 0,00 | 0,03 | −0,03 kWh |
| Excedentes | 0,00 | 0,03 | −0,03 kWh | 0,00 | 0,12 | −0,12 kWh |
| SOC mín→máx | 14→100 | 14→100 | igual | 77→100 | 77→100 | igual |
| Carga batería | 11,9 | 10,1 | +17,8 % | 3,0 | 3,2 | −6,3 % |
| Descarga batería | 7,4 | 7,3 | +1,4 % | 3,2 | 3,3 | −3,0 % |
| Cortes de red | 08:59–09:47 · 10:09–19:04 | 08:59–09:42 · 10:08–18:59 | inicio igual, fin +5 min | 17:56–19:41 | 17:56–19:42 | igual |

- Los contadores diarios del **inversor** en Metrum son idénticos a los de Deye (0 %).
  Las cifras de importación/excedentes de la referencia no salen del inversor
  (probable medidor de red; no leído). Solo el excedente del domingo (0,12) supera la
  resolución de 0,1 kWh de Deye.
- **Carga de batería:** la diferencia no es de escala sino de **muestreo**. Metrum es una
  foto cada 15 min y la rampa de 08–12 h cambia rápido (11:15: Metrum −1550 W vs Deye
  −4790 W; 12:00: 0 vs −2680 W). Para energía de batería usar los contadores 514/515.
- Los cortes de Deye terminan hasta 5 min después por la resolución de trama (~5 min).

## 2. Configuración y salud (Fase 3)

Configuración leída: `systemWorkMode = ZERO_EXPORT_TO_LOAD`, `energyPattern =
BATTERY_FIRST`, `zeroExportPower = 0`, `maxSellPower = 1000 W`, `maxSolarPower = 15000 W`;
batería 40 Ah, 40 A carga/descarga, SOC bajo 15 %, apagado 10 %; TOU `on` con 6 franjas
cíclicas (09:00, 13:00, 15:00, 16:00, 18:00, 22:30), todas SOC 15 %, 15000 W, 290 V, sin
carga desde red ni generador.

1. **Exportación cero: sí está configurada.** Coherente con `energyED = 0` y
   `DailyGridFeedIn = 0,00`. `maxSellPower` queda inactivo en este modo (**H**).
2. **La generación limitada del domingo es recorte, no falla** (**C**). SOC 100 % a las
   08:42, carga ~35–45 W, red ~0. Desde las 09:00 la PV cae a ~250 W y el string queda a
   ~370–380 V con ~0,4 A (con poca irradiancia la tensión baja a ~280–290 V, como a las
   06:00). El sábado ocurrió igual tras llenarse (12:03): 325 V/10 A → 370 V/1–3 A. El
   domingo arrancó con 77 % de SOC y consumió solo 1,3 kWh. Parte del déficit podría ser
   nubosidad (**H**): no se puede cuantificar la irradiancia.
3. **Piso de descarga 15 %** (**C**): SOC mín 14 % a las 06:28 del 3-oct y ~0,4 kWh
   importados al amanecer (05:15–06:45, 100–184 W).
4. **Alarma única en 5 días:** `F18 Tz_Ac_OverCurr_Fault` (ERR4, nivel 2), 3-oct
   19:04:22 → 19:19:14, justo al volver la red tras el corte de 10:09–19:04. Metrum:
   `invrun = fault` y `powerAE = 0` a las 19:15. La nube no devolvió descripción, causa ni
   solución y el código F18 no está en el PDF → causa **H**; vigilar recurrencia.
5. **Residuo de potencia ≈ 180 W constante** en `PV + batería + red − carga` (mediana
   173–196 W de noche y con PV bajo; 278–314 W con PV > 1500 W) ≈ 4,3 kWh/día: es lo que
   no cierra del balance diario (sáb. +5,0 kWh, dom. +4,6 kWh). Origen **H**: autoconsumo
   del inversor/BMS, cargas fuera del puerto medido o sesgo de sensores.
6. **CT externo:** `TotalExternalCTPower` fijo ≈ 12 W (4 W/fase) sin seguir la carga → no
   aporta medida real; el modo ZERO_EXPORT_TO_LOAD no lo usa (**H**).

## 3. Pendiente de confirmar

- Identidad de `BattCharges_DY`; registro exacto de `DailyActiveProduction` (501 vs 529) y
  de `GridCurrentL*`.
- Significado de F18 y si el corte de ~15 min de salida AC al reconectar afectó cargas.
- Origen del residuo de ~180 W y del CT plano.
- De dónde salen las cifras de importación/excedentes de la referencia (medidor de red no leído).
- Validar en 2–3 casas más (otro modelo `0_5411_1`, un equipo fuera de línea, una normal).
