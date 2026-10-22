# Prompt estándar: reporte mensual de curtailment (solar + BESS con zero export)

Copia todo lo que sigue en una sesión nueva y cambia solo los dos parámetros.

---

## Parámetros (lo único que se cambia)

- **ZONA:** `RESERVAS DE PANCE` (valor exacto del atributo `zone` en Metrum; no incluir zonas con nombre parecido)
- **MES:** `2026-09` (del día 1 al último día, hora `America/Bogota`, UTC−5)

## Rol y objetivo

Actúa como el especialista de O&M de la skill `om-agency`. Calcula el **curtailment** de todas las casas de la ZONA durante el MES y entrega un **reporte HTML gráfico que sea solo de curtailment** (sin otros KPIs ni recomendaciones), con el **ranking de mayor a menor**.

**Definición de curtailment:** momentos en que la batería llega al 100 % (SOC) y la exportación a red está limitada a cero (zero export), de modo que el solar baja hasta entregar solo lo que consume la casa, aunque el arreglo tenía mucho más potencial. Curtailment = energía solar potencial − energía solar entregada, medida solo en esos momentos.

## Datos y credenciales

- Fuente: telemetría cruda de Metrum (ThingsBoard). Credenciales **solo desde variables de entorno** (`METRUM_API_URL`, `METRUM_USERNAME`, `METRUM_PASSWORD`). Para validar Deye, `DEYE_*` con `scripts/deye_adapter.py` en **solo lectura** (nivel 0). Nunca imprimas, guardes ni incluyas en archivos o en el HTML credenciales, tokens, URLs del servidor ni seriales de equipos. El token vive solo en memoria.
- Trabaja en el scratchpad; los scripts van separados de los datos descargados.

## Procedimiento

1. **Inventario.** `POST /api/entitiesQuery/find` paginando hasta `hasNext=false`, con `latestValues` de tipo `ATTRIBUTE`: `zone, spcus, gateway, mettype, invbrand, invmodel, invcap, invarray, invtype, BattSn`. Filtra por igualdad exacta de `zone == ZONA` y agrupa por `spcus` (Casa N). El id está en `entityId.id` y el nombre en `latest.ENTITY_FIELD.name`.
2. **Equipos fantasma.** Si una casa tiene más de un inversor, usa el que tenga telemetría en el mes. Un equipo sin ningún punto en el mes se excluye y se reporta. Nunca reincorpores un equipo excluido sin avisar al usuario con los datos concretos.
3. **Descarga.** `values/timeseries` con `agg=NONE`, `limit=50000`, trozos de 10 días, `endTs` exclusivo (+1 h de margen), hora local con UTC explícito. Los valores llegan como string: conviértelos y ordena por `ts` (pueden venir en orden descendente). Keys comunes de inversor: `BattSOC, BattPower, BattCur, BattVolt, powerAEg, powerAPg, powerAE, energyPD, energyLD, energyID, energyED, invrun, invstate, voltGridA/B/C`. Deye: `LoadPower_DY`. Livoltek: `LoadPower_LV, ExportGrid_LV, powerAEgdc_LV, BattStateOp_LV`. Confirma las keys con `keys/timeseries` antes de depender de ellas. **Si aparece otra marca o modelo, detente y pregunta**: hay que verificar keys y signos.
4. **Signos de batería (verificados, confírmalos de nuevo con noche vs. mediodía):** en Deye `BattPower` + = descarga; en Livoltek + = carga. No uses `ExportGrid_DY` como exportación (es la lectura de un CT externo, ~4 W fijos).
5. **PV entregada (Metrum no expone potencia PV; se deriva por balance cada 15 min, ventana solar 06:00–18:00):**
   - Livoltek: `powerAEgdc_LV`.
   - Deye: `powerAEg − BattPower − max(LoadPower_DY, 0) + offset diurno`. El offset se **recalibra cada mes** con una regresión horaria entre el delta del contador `energyPD` y el balance, usando las casas con contador sano (en sept-2026: pendiente 1,007 e intercepto +255 W).
   - **No uses `energyPD` para calcular la pérdida:** arrastra el día anterior y puede estar congelado. Solo sirve para validar.
6. **Estado saturado:** intervalo de 06:30 a 17:30 con `SOC ≥ 99 %`, batería sin descarga (flujo ≥ −100 W) e importación de red < 100 W.
7. **PV potencial (no hay piranómetro; la flota es el sensor de sol):**
   - Sensores válidos en cada instante: casas con `SOC ≤ 95 %`, cargando ≥ 150 W y con corriente de carga por debajo del 92 % de su P99 (si está en su tope, la PV está limitada por la batería); o casas con consumo mayor que la PV (batería descargando ≥ 100 W o importando ≥ 100 W).
   - Ajusta el modelo `PV_casa(t) = k_casa × S(t)` por mínimos cuadrados alternados (30 iteraciones, mínimo 3 sensores por instante). Limita el potencial a 1,3 × la potencia nominal del inversor.
   - Valida dejando una casa fuera cada vez (leave-one-out) y reporta razón real/predicho (mediana y rango intercuartil) y error relativo mediano. **Si el error mediano supera 20 % o el potencial cubre menos del 90 % de los intervalos saturados, avisa antes de seguir.**
8. **Energía perdida:** intervalo con curtailment = saturado y potencial > 300 W y PV < 85 % del potencial. Pérdida = Σ (potencial − PV entregada) × 0,25 h. Reporta el rango con potencial ×0,88 y ×1,12.
9. **Validaciones obligatorias (reporta resultado y límites, nunca cites una validación inconclusa):**
   - Livoltek: razón ∫PV / `energyPD`.
   - Deye: producción diaria de la nube de Deye (`deye_adapter.py days SN inicio fin`), razón mensual y correlación diaria por casa.
   - Zero export activo: suma de exportación de la flota en el mes (debe ser ≈ 0).
   - Mediana de PV ÷ consumo en los intervalos de curtailment (debe ser ≈ 1,00).
   - Sensibilidad: potencial ±12 %, SOC = 100 % estricto, umbrales 70 % y 95 %. Reporta la correlación de rangos del ranking contra la base y el top 5 de cada variante.
10. **Métricas por casa:** energía perdida (kWh) y su rango; % de lo disponible = perdida ÷ (PV entregada + perdida); horas con curtailment; días con curtailment; horas saturadas; hora mediana a la que el SOC llega a 99 %; consumo medio durante el curtailment; consumo medio de 10 a 15 h como % de la PV disponible; máximo diario. También: matriz casa × día, matriz casa × hora, perfil horario promedio de la flota (entregada vs. disponible) y la serie de 15 min por casa y día (PV entregada, potencial, consumo, SOC, pérdida).

## Entregable: un HTML autocontenido

Antes de escribir el HTML carga las skills `dataviz` y `artifact-design`. Secciones en este orden:

1. **Encabezado:** título `Curtailment <Zona>`, periodo, el mecanismo en una línea (batería llena → zero export → PV limitada al consumo) y 4 tiles: total perdido con su rango y % del disponible; casas afectadas; concentración del top 4; franja horaria de mayor pérdida.
2. **Ranking** completo de mayor a menor, con barras, ordenable por kWh, % de lo disponible u horas. Clic en una fila abre su día de mayor pérdida.
3. **Cuándo ocurre:** perfil horario de la flota con el área perdida sombreada y mapa de calor casa × hora.
4. **Día a día:** barras de la pérdida de la flota por día y mapa de calor casa × día (fines de semana sombreados; clic abre el detalle).
5. **Un día en detalle:** selector de casa y día; PV entregada, PV potencial, consumo, panel de SOC y área de curtailment; estadísticas del día.
6. **Qué explica la diferencia entre casas:** dispersión de hora de llenado vs. % perdido y de consumo vs. % perdido, con su `r`. Sé honesto con lo que explican y lo que no.
7. **Metodología y calidad del dato:** definición, cómo se midió la PV entregada y la potencial, las validaciones con sus cifras, la tabla de sensibilidad, exclusiones y límites de lectura.

Reglas de diseño: un solo azul secuencial para la energía perdida y grises para el resto; valida la rampa con `validate_palette.js --ordinal` en claro y oscuro; tooltips por marca; cada gráfico con su vista de tabla; sin doble eje; tema claro y oscuro; legible a 390 px con scroll horizontal solo dentro de los contenedores anchos. Solo curtailment: ni recomendaciones ni otros indicadores.

## Calidad y entrega

- Renderiza una vez en escritorio claro, oscuro y teléfono, revisa errores de consola y que no haya scroll horizontal en la página, y corrige lo que falle.
- Verifica que el HTML no contenga credenciales, URLs del servidor ni seriales.
- Guarda como `reportes/curtailment-<zona-en-minusculas-con-guiones>-<AAAA-MM>.html`, publica como artefacto privado y haz commit y push en la rama de trabajo de la sesión.
- **Mensaje final al usuario:** total perdido con rango, top 5 del ranking, hallazgos clave, validaciones con cifras, equipos excluidos, lo que no se pudo medir (kWp y capacidad de batería no están en Metrum; pídelos si el usuario quiere normalizar), y el enlace del reporte.

## Reglas de honestidad

No inventes datos. El potencial es una estimación con incertidumbre y así se presenta. Si una validación sale inconclusa, dilo y no la uses como respaldo. Si un dato falta, pídelo.
