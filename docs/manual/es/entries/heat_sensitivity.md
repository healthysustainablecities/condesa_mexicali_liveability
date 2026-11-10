# Sensibilidad al calor (GUHVI)

[← Volver al contenido](../README.md)

> Subíndice de sensibilidad al calor del GUHVI (0-100), a partir del albedo, la vegetación, las zonas climáticas locales, la densidad de población y la población vulnerable; menor es mejor.

## Identificación

| | |
|---|---|
| Identificador | `heat_sensitivity` |
| Medida central (hoja de variables) | Índice Global de Vulnerabilidad Urbana al Calor (GUHVI) |
| ID de la hoja / registro | – |
| Variable en puntos de muestra | `sp_urban_heat_sensitivity_index` |
| Variable de área (valor medido) | `urban_heat_sensitivity_index` (0–100) |
| Puntuación normalizada | `index_uli__heat_sensitivity` |
| Dominios (parte del peso) | [Entorno medioambiental](domain_ambient_environment.md) |
| Subdominio | Riesgos climáticos |
| Enfoque | Calidad |
| Mejor si es | menor |
| Peso efectivo en el índice | `uli` 2.8% · `uli_plain` 2.4% |
| Estado | Se puntúa en el índice publicado |

## Justificación e interpretación

*Pendiente: No consta en el registro del proyecto.*

**Cómo leerlo.** Índice de sensibilidad al calor de … (0-100; menor es mejor).

**Heat sensitivity** (Global Urban Heat Vulnerability Index (GUHVI); ID –) (en inglés en la hoja)
- *Cómo calcular (hoja de variables):* USE GHSCI CALCULATION HERE (Land Surface Albedo, Normalised Difference Vegetation Index, Local Climate Zones, Population Density, Vulnerable Population Percentage)

## Fuentes de datos

**Fuentes declaradas en la configuración:**

- Turner et al. (2025) Urban Climate 64, 102716; computed in Google Earth Engine by GHSCI.

**Insumos:** [Índice Global de Vulnerabilidad Urbana al Calor (GUHVI) y sus insumos](guhvi.md)

## Método: teoría

1. Subíndice del Índice Global de Vulnerabilidad Urbana al Calor (GUHVI; Turner et al. 2025) calculado en Google Earth Engine sobre una cuadrícula de análisis, normalizado mín.–máx. a 0–100 dentro de la región (R8).
2. Cada punto de muestra toma el valor de la celda que lo contiene.
3. Normalización AMPI (R11) con metas fijas de 0 y 100 (la propia escala del subíndice), agregación (R12) y áreas (R13).

## Método: práctica

**Recetas:** [R1. Puntos de muestra y red peatonal](../03_recipes.md#r1), [R8. Earth Engine: vulnerabilidad al calor y grandes espacios verdes](../03_recipes.md#r8), [R11. Normalización: el Índice Ajustado de Mazziotta–Pareto (AMPI)](../03_recipes.md#r11), [R12. Agregación: dominios, indicadores compartidos e índice](../03_recipes.md#r12), [R13. De los puntos de muestra a las áreas](../03_recipes.md#r13), [R14. Metas congeladas y recálculo de un escenario](../03_recipes.md#r14)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:1232`](../../data/MX_Mexicali_2025_ULI.yml#L1232)):

```yaml
- variable: sp_urban_heat_sensitivity_index
  name: heat_sensitivity
  domains: [ambient_environment]
  polarity: negative
  goalposts: {min: 0, max: 100}
  lens: quality
  group: {es: 'Índice Global de Vulnerabilidad Urbana al Calor (GUHVI)', en: 'Global Urban Heat Vulnerability Index (GUHVI)'}
  label: {es: 'Sensibilidad al calor (GUHVI)', en: 'Heat sensitivity (GUHVI)'}
  reading: {es: 'Índice de sensibilidad al calor de {value} (0-100; menor es mejor)', en: 'Heat sensitivity index of {value} (0-100; lower is better)'}
  subdomain: {es: 'Riesgos climáticos', en: 'Climate risks'}
  about:
    es: Subíndice de sensibilidad al calor del GUHVI (0-100), a partir del albedo, la vegetación, las zonas climáticas locales, la densidad de población y la población vulnerable; menor es mejor.
    en: The GUHVI's heat sensitivity sub-index (0-100), from albedo, vegetation, local climate zones, population density and the vulnerable population; lower is better.
  sources:
    - 'Turner et al. (2025) Urban Climate 64, 102716; computed in Google Earth Engine by GHSCI.'
```

**Código (GHSCI):**

- [`process/subprocesses/_earth_engine_indicators.py:846`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L846) `guhvi_analysis()`
- [`process/subprocesses/_earth_engine_indicators.py:1105`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L1105) `normalise_band()`
- [`process/subprocesses/_composite_index.py:1819`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1819) `normalise()`
- [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`

|  | Variable en puntos de muestra | Transformación | Metas (escala puntuada) | inf – sup | asim. / curt. / empates | Alertas |
|---|---|---|---|---|---|---|
| `uli` | sp_urban_heat_sensitivity_index | tal cual | 0 · 58 · 100 | 0 – 81 | −0.79 / −0.15 / 2.6% | ninguna |
| `uli_plain` | sp_urban_heat_sensitivity_index | tal cual | 0 · 58 · 100 | 0 – 81 | −0.79 / −0.15 / 2.6% | ninguna |

## Recálculo (Reimagina Urbano)

Los subíndices GUHVI se normalizan dentro de la región con sus propios mínimos y máximos; un escenario debe usar los mismos mínimos y máximos de la línea base para no reescalar toda la ciudad.

Con las metas congeladas del archivo de parámetros (`Ref`, `Mín.`, `Máx.`, R14), una nueva puntuación es `r = 100 ± 60·(x − Ref)/(Máx. − Mín.)` sin volver a resolver metas; el dominio y el índice se recalculan con R12 y se resta 100. Así un escenario se compara con la línea base en la misma escala.

## Resultados

| Medida | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|
| Valor de la región | 59.7 | 33.8 |
| Puntuación de la región (`uli`) | −4.7 | +14.7 |
| Áreas con valor | 14,148 de 14,252 manzanas | 13,265 de 14,988 lotes |
| Mediana (P25–P75), ponderada | 67.3 (57.3 – 74.2) | 35.1 (30.3 – 39.1) |
| Rango | 4.2 – 81.2 | 10.5 – 48.5 |
| Puntuación: mediana (P25–P75) (`uli`) | −5.4 (−9.5 – +0.6) | +13.9 (+11.6 – +16.8) |

*Distribuciones: manzanas de la región de estudio ponderadas por su población censal (2020); lotes de Condesa con igual peso (3.2 residentes supuestos por lote). Los valores de la región son los que GHSCI reporta para cada región en conjunto.*

- Región de estudio: Índice de sensibilidad al calor de 59.7 (0-100; menor es mejor).
- Condesa: Índice de sensibilidad al calor de 33.8 (0-100; menor es mejor).
- Para la región de estudio en su conjunto, el valor es 59.7; en Condesa, 33.8. La puntuación de Condesa queda 14.7 puntos por encima del promedio de la región de estudio (−4.7 para la región de estudio).

## Mapa

![Sensibilidad al calor (GUHVI)](../../figures/es/heat_sensitivity.png)

*Mapa. Sensibilidad al calor (GUHVI): valor medido (0–100) por manzana en la región de estudio y por lote en Condesa (recuadro). Clases del tablero; los colores favorables son los claros (menor es mejor).*

## Advertencias y pendientes

- Normalizado mín.–máx. dentro de la región (véase exposición al calor).
