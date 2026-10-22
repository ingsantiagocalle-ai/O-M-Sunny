# Pipeline de curtailment mensual

Genera el reporte HTML de curtailment (PV perdida por batería llena + zero export) de una zona de Metrum.
El cálculo, la plantilla y el texto de metodología son fijos: lo único que cambia entre corridas es la zona,
el mes y los datos. Por eso el reporte sale igual cada vez.

```
python3 reportes/curtailment/curtailment.py --zona "RESERVAS DE PANCE" --mes 2026-09
```

Requisitos: `python3` con `pandas`, `numpy` y `requests`; variables de entorno `METRUM_API_URL`,
`METRUM_USERNAME`, `METRUM_PASSWORD` (y `DEYE_*` para validar contra la nube de Deye, solo lectura).

Salidas: `reportes/curtailment-<zona>-<AAAA-MM>.html` (autocontenido) y, en `.curtailment-cache/`, el mismo
HTML sin envoltorio (`*.fragmento.html`) para publicarlo como artefacto. La telemetría descargada queda en
esa caché (no se versiona); `--refresh` la vuelve a bajar.

## Qué hace
1. Lista los inversores de la zona (`zone` exacto), agrupa por casa y excluye equipos sin datos en el mes.
2. Descarga la telemetría de 15 min y deriva la PV entregada por balance de potencias (Livoltek:
   `powerAEgdc_LV`; Deye: carga − batería − importación + residuo diurno, que calibra con el mes).
3. Marca los intervalos saturados (SOC ≥ 99 %, sin descarga ni importación), estima la PV potencial con la
   propia flota como sensor de sol y calcula la energía perdida.
4. Valida (contador `energyPD`, nube de Deye, leave-one-out, zero export, PV ÷ consumo, sensibilidad) y
   escribe el resultado de cada validación en la metodología del reporte, junto con las advertencias.

## Qué no se debe cambiar
- Los parámetros del diccionario `P` de `curtailment.py` y la plantilla: cambiarlos cambia los números o el
  formato y rompe la comparación entre meses. Si hay que ajustarlos, hacerlo en una confirmación aparte.
- Una marca o modelo de inversor distinto de Deye y Livoltek aborta la corrida: antes hay que verificar las
  keys de telemetría y el signo de `BattPower`.

## Cuándo detenerse y avisar
Error del potencial (leave-one-out) > 20 %, cobertura del potencial < 90 % de los intervalos saturados,
menos de 6 casas con datos, mes sin terminar, o una validación contra la nube de Deye muy desviada. El script
imprime estos casos como `ADVERTENCIA` y los incluye en la metodología del HTML.

## Lo que no se puede medir con Metrum
kWp instalados y capacidad de batería: sin ellos no se normaliza la pérdida. Pedirlos al usuario si los quiere.
