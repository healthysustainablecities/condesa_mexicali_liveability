# Escuelas primarias a menos de 300 m

[← Volver al contenido](../README.md)

> Distancia a pie a la escuela primaria más cercana, puntuada con un umbral suave de 300 m.

## Identificación

| | |
|---|---|
| Identificador | `primary_school` |
| Medida central (hoja de variables) | Acceso a salud, educación y cuidados |
| ID de la hoja / registro | 180, 246, 379 · #180 |
| Variable en puntos de muestra | `sp_walk_nearest_node_denue_primary_school` |
| Variable de área (valor medido) | `avg_walk_dist_denue_primary_school` (m) |
| Puntuación normalizada | `index_uli__primary_school` |
| Dominios (parte del peso) | [Infraestructura social](domain_social_infrastructure.md) |
| Subdominio | Educación |
| Enfoque | Proximidad |
| Mejor si es | valor medido menor (puntuación transformada mayor) |
| Peso efectivo en el índice | `uli` 1.7% · `uli_plain` 1.7% |
| Estado | Se puntúa en el índice publicado |

## Justificación e interpretación

> La cercanía a escuelas primarias favorece la habitabilidad para las familias al facilitar el acceso cómodo a la educación básica de los residentes más jóvenes. (traducción preliminar del inglés)
>
> — *Registro de indicadores #180: Access to schools: primary (Social Infrastructure / Education)*

- Cita del libro de trabajo: Onnom et al., 2018, 'Development of a Liveable City Index (LCI) Using Multi Criteria Geospatial Modelling for Medium Class Cities in Developing Countries'; Fu et al., 2019, 'The Livable Urban Landscape: GIS and Remote Sensing Extracted Land Use Assessment for Urban Livability in Changchun Proper, China'; Liu et al., 2020, 'Using Multi-Source Data to Assess Livability in Hong Kong at the Community-Based Level: A Combined Subjective-Objective Approach'
- Lista de artículos: #18: Jodder (2024), ‘Urban Livability in a Rapidly Urbanizing Mid-Size City: Lessons for Planning in the Global South’
- ⚠ la cita del libro de trabajo no nombra a un autor del artículo de la lista; verifique antes de citar (citation_audit.csv)

**Cómo leerlo.** … de la población vive a menos de 300 m de una escuela primaria; en promedio, la más cercana está a … (menor es mejor).

**Access to educational services** (Health, education and care access; ID 180, 246, 379) (en inglés en la hoja)
- *Cómo calcular (hoja de variables):* Walking distance access to preeschols, primary, secondary and tertiary educaitonal centers
- *Notas (hoja):* Using DENUE data

## Fuentes de datos

**Fuentes declaradas en la configuración:**

- INEGI (2026) Directorio Estadístico Nacional de Unidades Económicas (DENUE), May 2026.

**Fuente registrada por GHSCI (diccionario de datos)** (`avg_walk_dist_denue_primary_school`):

- OpenStreetMap: Geofabrik GmbH, 20260815, ODbL, https://download.geofabrik.de/north-america/mexico-latest.osm.pbf, OpenStreetMap Contributors.  Geofabrik GmbH (2026). https://download.geofabrik.de/north-america/mexico-latest.osm.pbf; INEGI, Directorio Estadistico Nacional de Unidades Economicas (DENUE): 2026-05, Terminos de Libre Uso de la Informacion del INEGI, https://www.inegi.org.mx/app/mapa/denue/, INEGI (2026). Directorio Estadistico Nacional de Unidades Economicas (DENUE), mayo 2026. Instituto Nacional de Estadistica y Geografia, Mexico.

**Filtro de destinos:**

- `denue_primary_school` (Primary schools (DENUE)): `MX/INEGI/DENUE_2026/denue_inegi_02_.shp` — Filtro de destinos: `"codigo_act IN ('611121','611122','611171','611172')"`

**Insumos:** [Destinos del DENUE por código SCIAN](denue_destinations.md)

## Método: teoría

1. Distancia por la red peatonal desde cada punto de muestra al destino más cercano, `d` (R2), censurada en la banda mayor buscada (1,500 m): un punto sin destino a esa distancia queda sin valor.
2. Puntuación de acceso suave (R10): `s(d) = 1 / (1 + exp(k·(d − t)/t))`, con `t = 300 m` y `k = 5`; `s = 0.5` en el umbral, ≈ 0.99 junto al destino, ≈ 0.007 a `2t`; sin valor → `s = 0`.
3. Normalización AMPI (R11) de `s` con las metas de la región de estudio, luego agregación por dominio e índice (R12) y a áreas (R13).

## Método: práctica

**Recetas:** [R1. Puntos de muestra y red peatonal](../03_recipes.md#r1), [R2. Distancia por la red al destino más cercano, censurada](../03_recipes.md#r2), [R10. Transformaciones: umbrales suaves y escalas escalonadas](../03_recipes.md#r10), [R11. Normalización: el Índice Ajustado de Mazziotta–Pareto (AMPI)](../03_recipes.md#r11), [R12. Agregación: dominios, indicadores compartidos e índice](../03_recipes.md#r12), [R13. De los puntos de muestra a las áreas](../03_recipes.md#r13), [R14. Metas congeladas y recálculo de un escenario](../03_recipes.md#r14)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:1539`](../../data/MX_Mexicali_2025_ULI.yml#L1539)):

```yaml
- variable: sp_walk_nearest_node_denue_primary_school
  name: primary_school
  domains: [social_infrastructure]
  transform: {soft_threshold: 300}
  group: {es: 'Acceso a salud, educación y cuidados', en: 'Health, education and care access'}
  label: {es: 'Escuelas primarias a menos de 300 m', en: 'Primary schools within 300 m'}
  reading: {es: '{access} de la población vive a menos de 300 m de una escuela primaria; en promedio, la más cercana está a {value}', en: '{access} of the population live within 300 m of a primary school; on average the nearest is {value} away'}
  subdomain: {es: 'Educación', en: 'Education'}
  about:
    es: Distancia a pie a la escuela primaria más cercana, puntuada con un umbral suave de 300 m.
    en: Walking distance to the nearest primary school, scored with a 300 m soft threshold.
  sources:
    - 'INEGI (2026) Directorio Estadístico Nacional de Unidades Económicas (DENUE), May 2026.'
```

[`MX_Mexicali_2025_ULI.yml:502`](../../data/MX_Mexicali_2025_ULI.yml#L502):

```yaml
- {name: denue_primary_school, category: primary_school, variant: any, layer: destinations, where: "dest_name = 'denue_primary_school'"}
```

**Código (GHSCI):**

- [`process/subprocesses/_accessibility_spec.py:806`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L806) `_banded_distances()`
- [`process/subprocesses/setup_sp.py:888`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/setup_sp.py#L888) `create_full_nodes()`
- [`process/subprocesses/_composite_index.py:1457`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1457) `soft_threshold()`
- [`process/subprocesses/_composite_index.py:1819`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1819) `normalise()`
- [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`

|  | Variable en puntos de muestra | Transformación | Metas (escala puntuada) | inf – sup | asim. / curt. / empates | Alertas |
|---|---|---|---|---|---|---|
| `uli` | sp_walk_nearest_node_denue_primary_school | acceso suave, umbral de 300 m, k = 5 | −0.330 · 0.166 · 0.663 | 0.000 – 0.993 | 1.70 / 1.44 / 12.5% | ninguna |
| `uli_plain` | sp_walk_nearest_node_denue_primary_school | acceso suave, umbral de 300 m, k = 5 | −0.330 · 0.166 · 0.663 | 0.000 – 0.993 | 1.70 / 1.44 / 12.5% | ninguna |

## Recálculo (Reimagina Urbano)

Un destino nuevo o retirado, o un cambio en la red peatonal, cambia `d` solo en los puntos cuyo destino más cercano cambia: basta un Dijkstra multi-origen desde los destinos afectados, limitado a 1,500 m, tomando el mínimo con la distancia previa.

Con las metas congeladas del archivo de parámetros (`Ref`, `Mín.`, `Máx.`, R14), una nueva puntuación es `r = 100 ± 60·(x − Ref)/(Máx. − Mín.)` sin volver a resolver metas; el dominio y el índice se recalculan con R12 y se resta 100. Así un escenario se compara con la línea base en la misma escala.

## Resultados

| Medida | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|
| Valor de la región | 525 m | 1,013 m |
| Puntuación de la región (`uli`) | +4.6 | −8.6 |
| Áreas con valor | 13,765 de 14,252 manzanas | 4,084 de 14,988 lotes |
| Mediana (P25–P75), ponderada | 500 m (341 m – 730 m) | 1,039 m (518 m – 1,462 m) |
| Rango | 58 m – 2,777 m | 33 m – 3,051 m |
| Nada a la distancia buscada | 1.0% | 69.2% |
| Puntuación: mediana (P25–P75) (`uli`) | −6.0 (−9.9 – +13.0) | −10.1 (−10.1 – −10.1) |

*Distribuciones: manzanas de la región de estudio ponderadas por su población censal (2020); lotes de Condesa con igual peso (3.2 residentes supuestos por lote). Los valores de la región son los que GHSCI reporta para cada región en conjunto.*

*Una distancia media se calcula sobre los puntos que encontraron un destino dentro de la distancia buscada; la fila «Nada a la distancia buscada» da la parte de la población de las áreas sin ninguno.*

- Región de estudio: 22.9% de la población vive a menos de 300 m de una escuela primaria; en promedio, la más cercana está a 525 m.
- Condesa: 1.9% de la población vive a menos de 300 m de una escuela primaria; en promedio, la más cercana está a 1,013 m.
- Para la región de estudio en su conjunto, el valor es 525 m; en Condesa, 1,013 m. La puntuación de Condesa queda 8.6 puntos por debajo del promedio de la región de estudio (+4.6 para la región de estudio).

## Mapa

![Escuelas primarias a menos de 300 m](../../figures/es/primary_school.png)

*Mapa. Escuelas primarias a menos de 300 m: valor medido (m) por manzana en la región de estudio y por lote en Condesa (recuadro). Clases del tablero; los colores favorables son los claros (menor es mejor).*

## Advertencias y pendientes

- Las escuelas que combinan niveles (SCIAN 611171/611172) se cuentan en cada nivel que atienden (configuración).
