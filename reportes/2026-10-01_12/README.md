# Reporte operativo Sunny · 1–12 oct 2026

`reporte-operativo-sunny-2026-10-01_12.html` es el reporte completo (abre en cualquier navegador).

Todo se recalcula desde telemetría cruda de Metrum (15 min) y DeyeCloud (solo lectura).
Credenciales solo por variables de entorno (`METRUM_*`, `DEYE_*`); ningún script las imprime ni las guarda.

## Regenerar

```bash
cd scripts
python3 -I inventory.py      # dispositivos + atributos (entitiesQuery/find)
python3 -I fetch.py          # series crudas 30-sep → 13-oct en raw/ (no se versionan)
python3 -I houses.py         # mapa vivienda → inversor / medidor de red / medidor de cargas
python3 -I attrs_extra.py    # capacidad de batería (Ah) y operador de red
python3 -I deye_days.py      # energía diaria DeyeCloud (validación de escala)
python3 -I deye_alerts.py    # alarmas DeyeCloud
python3 -I compute.py        # KPIs por vivienda, fases, tensiones, cortes, respaldo
python3 -I aggregate.py      # flota, sectores, eventos, riesgo
python3 -I build_report.py reporte_sunny.html   # HTML (contenido de la página)
```

Las fórmulas, correcciones (escala ×0,1 en 8 inversores DEYE) y limitaciones están en la sección 10 del reporte.
