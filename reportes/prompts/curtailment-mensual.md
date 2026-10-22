# Prompt estándar: reporte de curtailment

Pega esto en una sesión nueva y cambia solo `ZONA` y `MES`.

---

Genera el reporte de curtailment de la zona **{ZONA}** para el mes **{AAAA-MM}** (ejemplo: `RESERVAS DE PANCE`, `2026-09`) con el pipeline del repo, sin modificar el cálculo ni la plantilla:

`python3 reportes/curtailment/curtailment.py --zona "{ZONA}" --mes {AAAA-MM}`

1. Lee la salida: validaciones, equipos excluidos y advertencias. Si el script falla, aparece una marca o modelo de inversor nuevo, o hay una advertencia grave (error del potencial > 20 %, cobertura < 90 %), detente y avísame; no improvises.
2. Abre el HTML generado y confirma que no hay errores de consola ni scroll horizontal a 390 px.
3. Publica el fragmento (`*.fragmento.html`, la ruta la imprime el script) como artefacto privado, y haz commit y push en la rama de la sesión.
4. Respóndeme corto: total perdido con su rango, top 5 del ranking, hallazgos clave, validaciones con cifras, equipos excluidos y límites (kWp y capacidad de batería no están en Metrum).

Credenciales solo desde variables de entorno; nunca en archivos ni en el HTML.
