# Reporte operativo diario (tablero HTML)

Genera el tablero oscuro «Operación diaria» de la flota Sunny (48 sistemas, 4 ciudades) para una ventana de
24 h (07:00 → 07:00, UTC−5), **recalculado desde telemetría cruda de Metrum**. Solo lectura.

```bash
export METRUM_API_URL=... METRUM_USERNAME=... METRUM_PASSWORD=...   # solo desde el entorno
python3 build_report.py 2026-10-18 --out reportes/operacion-diaria-2026-10-18.html
```

La fecha es el día que **cierra** la ventana (`2026-10-18` = 17 oct 07:00 → 18 oct 07:00). `--now` reproduce el
reporte como se habría visto a una hora (energía hasta la última muestra anterior). Tarda ~15 s.

## Qué sale de dónde

| Dato | Fuente |
|---|---|
| Cortes de red | eventos `po`/`pr` del medidor de red |
| Huecos de tensión («lo que vio la casa») | eventos `po`/`pr` del medidor solar (lado respaldado) |
| SOC, hora de batería llena, comunicación | inversor (`BattSOC`) y `activityState` de gateway/medidores/inversor |
| Generación, consumo, importada, exportada | contadores acumulados de los medidores (`CenergyAI/AE` al cierre diario; `energyAI/AE` en la ventana). Generación = demanda del medidor solar − importada + exportada; **no** se usa el contador del inversor |
| kWp, equipo, ciudad por casa | `assets/systems.json` (archivo de sistemas; **no sale de Metrum**) |
| Yield patrón | definido por el equipo: Cali 1188, costa 1323 kWh/kWp·año (`compute.YIELD_PATRON`) |

## Validación contra «Operación diaria 16 oct»

Se corrió la misma ventana (15 oct 07:00 → 16 oct 07:00) y se comparó con el reporte publicado:

- **Cortes**: 27 de 27 filas idénticas (duración, hueco al caer/durante/volver, total, % respaldo, SOC inicio → mín → fin); 25 casas, 3 eventos, respaldo 69,6 %, semáforo 6/16/0/0/3.
- **Energía**: generación por casa y yield idénticos en las 42 casas que la referencia calculó (730 kWh, 1145 kWh/kWp·año, cobertura 78 %); patrón de 657 kWh = mediana de los 10 días previos.
- **Gráficos**: cortes por casa, respaldo por evento, batería durante el corte y hora de batería llena salen **idénticos byte a byte**.
- Lo que difiere hoy es solo porque Metrum recibió después datos atrasados (casas que estaban offline cuando se generó la referencia).

## Reglas inferidas (no documentadas por el equipo)

Se dedujeron de los datos de la referencia; confírmalas o corrígelas:

- Un hueco cuenta en un solo corte: el que empieza hasta 75 s de su inicio (±40 s de desfase de relojes), si no el que lo contiene, si no el último que terminó hasta 10 min antes.
- «Al caer»: hueco que empieza hasta 75 s después del inicio del corte; «al volver»: el resto (o el que empieza después). Un hueco de más de 75 s dentro del corte es «durante».
- Evento = cortes de una misma ciudad separados menos de 10 min.
- Veredicto (**umbrales supuestos**; la referencia no tuvo casos de retardo ni de caída): sin hueco = respaldo total; hueco total ≤ 40 s = con transferencia; mayor y con respaldo = retardo de transferencia; hueco ≥ 10 s «durante» = caída durante el respaldo; respaldo 0 % = sin respaldo.
- Hueco de tensión sin corte asociado: se cuenta si dura entre 10 s y 10 min.
- «Bajo consumo»: consumo del día < 75 % de la mediana de los 10 días previos de esa casa.
- kWp: el archivo trae 2 decimales; el real es un múltiplo de 0,595 kWp (módulo de 595 W). Se corrige al múltiplo más cercano si está a ≤ 0,01 kWp (así el yield coincide con la referencia).
- Equipos detrás de un gateway caído: sin datos desde que cayó el gateway.

## Límites

- Un corte **en curso** al cierre se cuenta en «Sin red ahora», pero no se dibuja como corte (sin hora aproximada «≈») hasta que vuelva la red. No hubo casos en las ventanas probadas.
- La ventana es siempre de 24 h (el lunes no se extiende hasta el viernes).
- El gráfico «batería durante el corte más largo» y los veredictos de retardo/caída no se han visto con datos reales (no hubo cortes ≥ 5 min ni casos de esos tipos).
- Si Metrum no tiene el cierre diario de un medidor, la casa queda como «sin cierre diario del medidor» (no se inventa).
- Si aparece un gateway nuevo, agrégalo a `assets/systems.json` con su kWp; el generador avisa de los que faltan.
