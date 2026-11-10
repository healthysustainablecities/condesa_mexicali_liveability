# Espacio público abierto y grandes espacios verdes públicos

[← Volver al contenido](../README.md)

GHSCI identifica las áreas de espacio abierto a partir de polígonos de OpenStreetMap (reglas de `configuration/osm_open_space.yml`), las agrupa en áreas contiguas y retiene las de acceso público. El agua se excluye del espacio público abierto, de modo que un canal no encadena parques contiguos en un área enorme. El acceso se mide hasta puntos cada 20 m del perímetro del área a los que pasa una calle a menos de 30 m (`aos_public_any_nodes_30m_line`).

Un **gran espacio verde público** (LPUGS) es un espacio público abierto de al menos 1 ha con NDVI medio anual ≥ 0.2 (Sentinel-2), identificado en Google Earth Engine; sus entradas son el subconjunto de puntos de acceso de esas áreas.

| Variable en puntos de muestra | Variable de área (valor medido) | Descripción | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|---|---|
| `sp_walk_nearest_node_public_open_space_any` | `avg_walk_dist_public_open_space_any` | Distancia media por la red hasta lo más cercano: Espacio público abierto — red: Caminando | 469 m | 849 m |
| `sp_access_large_public_green_space_score` | `pct_access_500m_large_public_green_space_score` | Gran espacio verde público (500 m) | 8.2% | 0.0% |

## Método: práctica

**Recetas:** [R2. Distancia por la red al destino más cercano, censurada](../03_recipes.md#r2), [R3. Acceso por bandas y lejanía de una desamenidad](../03_recipes.md#r3), [R8. Earth Engine: vulnerabilidad al calor y grandes espacios verdes](../03_recipes.md#r8)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:475`](../../data/MX_Mexicali_2025_ULI.yml#L475)):

```yaml
- {name: public_open_space_any,   category: pos,  variant: lenient, layer: aos_public_any_nodes_30m_line}
```

**Código (GHSCI):**

- [`process/subprocesses/_06_open_space_areas_setup.py:43`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L43) `aos_setup_queries()`
- [`process/subprocesses/_earth_engine_indicators.py:282`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L282) `lpugs_analysis()`
- [`process/subprocesses/_earth_engine_indicators.py:664`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L664) `lpugs_indicators()`

## Lo usan

[Parques a menos de 300 m](parks.md), [Gran espacio verde público a menos de 500 m](lpugs.md)
