# Anexo G. Indicadores excluidos y pendientes

El ULI incluye toda subvariable de la hoja de variables del proyecto (`excel_work_sheet_key.xlsx`, revisada el 25 de septiembre de 2026) cuyos datos se han entregado y varían en la ciudad. La configuración registra por qué las demás no se puntúan ({{cfg:## Deliberately not included}}):

| Subvariable o medida central | Razón por la que no se puntúa |
|---|---|
| Inundaciones: población expuesta; área inundada en vialidades principales | Los valores entregados faltan en casi todas las áreas (ninguno en la cuadrícula), en espera de que el paquete de trabajo confirme si un valor faltante significa sin exposición. Se vinculan tomando lo faltante como cero (`null_as`), solo como referencia. |
| Cobertura arbórea | Solo 210 manzanas, sin valores en la cuadrícula: demasiado escasa para variar. |
| Cobertura de ciclovías protegidas | Casi toda en cero. INVI 2020 no distingue los carriles protegidos y OpenStreetMap no estuvo disponible para el paquete de trabajo (nota de la hoja). |
| Exposición al calor (medida central 3): temperatura de la superficie, frecuencia de calor extremo, retención nocturna de calor | Pendiente de entrega. |
| Cobertura de banquetas, alumbrado público, cobertura de ciclovías, empleos alcanzables, acceso a servicios básicos (Vivienda) | Pendientes de entrega. |
| Exposición al delito | Una sola tasa municipal para todos los lugares, por lo que no los distingue. |
| *Disponibilidad* de grandes espacios públicos abiertos: la parte del suelo de un área que es gran espacio verde público | El acceso a grandes espacios verdes públicos se calcula en el flujo central de GHSCI y **sí se puntúa** en el índice ([Gran espacio verde público a menos de 500 m](entries/lpugs.md)); también se calcula el acceso a pie y en bicicleta a grandes espacios públicos abiertos (más de 1.5 ha) en cada banda de distancia, que se muestra en el tablero general. La disponibilidad es una subvariable aparte de la hoja. Describe el suelo de un área, no el entorno de un punto de muestra, por lo que el índice, que puntúa puntos de muestra, no la incluye por ahora. |
| Densidad residencial neta, uso de suelo comercial, mezcla de usos | Componentes de la medida central de caminabilidad, que la caminabilidad misma representa: puntuarlos también contaría dos veces la densidad. Se mantienen en el tablero general. |
| Confort térmico nocturno | Varía muy poco en la ciudad (30.3–30.6 °C). |
| Cobertura de estaciones de bomberos a 75 km | Cobertura universal: se registra por completitud; se puntúa en su lugar el umbral suave de 3 km. |

Dos dominios, **Vivienda** y **Características sociodemográficas**, aún no tienen indicadores. Se describen pero no se puntúan, por lo que el índice es el compuesto de seis dominios.

## Preguntas abiertas registradas con el análisis

- Si un valor de inundación faltante significa sin exposición (paquete de trabajo 5).
- La medida central 3 de exposición al calor (paquete de trabajo 2).
- El destino y el umbral del indicador de nivel de estrés del tráfico (una elección provisional dentro de un conjunto).
- Los nombres en español de las medidas centrales (`group`) y el texto `about` y `sources` de cada indicador, redactados el 25 de septiembre de 2026, están pendientes de revisión.
