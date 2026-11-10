# 1. Diseño del estudio

## Región de estudio

La región de estudio es la unión del área urbana de Mexicali (la localidad `NOMGEO = 'Mexicali'` del Marco Geoestadístico 2025 del INEGI) y el desarrollo Condesa, disuelta en un solo elemento. Solo 82% de Condesa cae dentro del límite urbano administrativo, que por sí solo habría recortado 2,419 de sus 14,989 lotes ([`MX_Mexicali_2025_ULI.yml:43`](../data/MX_Mexicali_2025_ULI.yml#L43)). La región de estudio abarca 211.2 km², de los cuales Condesa ocupa 3.12 km².

Las áreas se resumen solo donde están dentro de la región de estudio (un punto de su superficie dentro de ella). La red se extrae para la región de estudio misma y no para su zona de amortiguamiento de 1,600 m, de modo que las calles y destinos al otro lado de la frontera con Estados Unidos no entren en los cálculos de accesibilidad ([`MX_Mexicali_2025_ULI.yml:55`](../data/MX_Mexicali_2025_ULI.yml#L55); issue #610 de GHSCI).

## Sistema de referencia de coordenadas

EPSG:6366, Mexico ITRF2008 / UTM zona 11N, en metros ([`MX_Mexicali_2025_ULI.yml:42`](../data/MX_Mexicali_2025_ULI.yml#L42)).

## Escalas

| Escala | Unidades | Fuente | Cómo llegan los valores |
|---|---|---|---|
| Puntos de muestra | 154,239 | Cada 30 m a lo largo de la red peatonal, más uno por lote de Condesa ([R1](03_recipes.md#r1)) | Se calculan aquí |
| Cuadrícula de 100 m | 21,076 celdas | GHS-POP 2025, reproyectado a EPSG:6366 con remuestreo por suma | Media de los puntos de muestra de la celda |
| AGEB | 436 | Áreas censales del INEGI 2020 | De la cuadrícula, ponderado por su población |
| Manzanas | 14,252 | Manzanas censales del INEGI 2020 con geometrías actualizadas por el CFC | Media de los puntos de muestra a menos de 30 m |
| Lotes de Condesa | 14,988 | Lotes del CFC de 400 m² o menos | Media de los puntos de muestra a menos de 15 m |
| Fraccionamientos de Condesa | 40 | Fraccionamientos del CFC | De los lotes, con 3.2 residentes supuestos por lote |
| Región: región de estudio | 1 | Límite de la región de estudio | De la cuadrícula, ponderado por población |
| Región: Condesa | 1 | Límite de Condesa | De los lotes |

Las manzanas se resumen desde los puntos de muestra y no desde la cuadrícula porque una manzana (mediana de 0.71 ha) es más pequeña que una celda de 100 m; agregar desde la cuadrícula solo copiaría la celda que la contiene ([`MX_Mexicali_2025_ULI.yml:121`](../data/MX_Mexicali_2025_ULI.yml#L121)). Los lotes se resumen a 15 m para que un lote dentro de un fraccionamiento cerrado no reciba crédito de acceso a través de una puerta que no puede usar ([`MX_Mexicali_2025_ULI.yml:81`](../data/MX_Mexicali_2025_ULI.yml#L81)).

## Población

- **Cuadrícula de 100 m:** GHS-POP R2023A para 2025 (Schiavina et al. 2023), en Mollweide, reproyectado con remuestreo por suma para conservar los conteos ([`MX_Mexicali_2025_ULI.yml:61`](../data/MX_Mexicali_2025_ULI.yml#L61)). La cuadrícula no se redirige a conteos censales a propósito, para que exista como resultado.
- **Manzanas y AGEB:** Censo 2020 del INEGI (`POBTOT`). 3,497 manzanas no tienen población registrada y se excluyen de los resúmenes ponderados por población.
- **Condesa:** el desarrollo es demasiado reciente para el censo, así que se supone que cada lote aloja a 3.2 residentes (el tamaño medio de hogar de Mexicali en 2020, INEGI). También se colocan puntos de muestra en áreas sin población (`sampling.sample_unpopulated_areas`), para que Condesa se mida.

## Red

La red peatonal se obtiene con OSMnx de OpenStreetMap, en la marca de tiempo de replicación del extracto de México de Geofabrik del 15 de agosto de 2026, que contiene las calles de Condesa aportadas ese día ([`MX_Mexicali_2025_ULI.yml:396`](../data/MX_Mexicali_2025_ULI.yml#L396)). La definición conserva el acceso privado y cerrado, que GHSCI excluye por defecto, porque las calles internas de Condesa y de los fraccionamientos cerrados de Mexicali son justamente las áreas de interés ([`MX_Mexicali_2025_ULI.yml:414`](../data/MX_Mexicali_2025_ULI.yml#L414)). Las intersecciones son las intersecciones consolidadas de OSMnx con una tolerancia de 12 m.

## Distancias y bandas

El acceso a pie se juzga a 300 m, la caminata de cinco minutos que busca la política de caminabilidad de vialidades colectoras de Mexicali, en lugar de los 500 m de los indicadores comparables a nivel mundial de GHSCI, que también se producen sin cambios. Las distancias se miden en bandas de 300, 500, 1,000 y 1,500 m y se censuran en 1,500 m: un punto de muestra sin nada a 1,500 m no tiene distancia y cuenta como sin acceso ([`MX_Mexicali_2025_ULI.yml:461`](../data/MX_Mexicali_2025_ULI.yml#L461)).

## Dos regiones, un análisis

Mexicali y Condesa se analizan en una sola ejecución, con la misma red, cuadrícula de población y destinos, de modo que las diferencias entre ellas son reales y no artefactos de análisis separados. La referencia de la región de estudio, la media sobre todos los puntos de muestra contra la que se mide cada puntuación, incluye a Condesa.
