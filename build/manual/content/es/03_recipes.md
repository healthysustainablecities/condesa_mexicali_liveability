# 3. Recetas de método

Cada receta enuncia una sola vez un método compartido, en teoría (qué se calcula) y en práctica (dónde lo calcula GHSCI). Termina con lo que una nueva implementación necesita conservar para recalcularlo. Las entradas de indicadores citan estas recetas por número.

<a id="r1"></a>
## R1. Puntos de muestra y red peatonal

**Teoría.** El entorno vivible se mide en los lugares desde los que la gente vive y camina: puntos cada 30 m a lo largo de la red peatonal. Cada punto está sobre un tramo entre dos nodos `n1` y `n2`, a distancias `d1` y `d2` de ellos a lo largo del tramo. La distancia por la red desde un punto es la menor de las dos rutas por sus nodos extremos.

**Práctica.**

- La red se construye con OSMnx a partir de la consulta peatonal configurada, que en Mexicali conserva el acceso privado y cerrado, con `retain_all` para conservar los fraccionamientos cerrados desconectados. Se eliminan los ramales sin salida más cortos que la mitad del intervalo de muestreo ({{code:_03_create_network_resources.py:prune_short_dangles}}).
- Se generan puntos cada `point_sampling_interval` = 30 m a lo largo de cada tramo, desde su inicio, excluyendo vías troncales y vías con `foot = no` ({{code:_07_locate_origins_destinations.py:nearest_node_locations}}).
- Se eliminan los puntos duplicados en los cruces y los puntos dentro de espacios abiertos, y el conjunto se restringe a la región de estudio urbana.
- Como está activado `sampling.sample_unpopulated_areas`, se conservan puntos donde no hay población registrada (Condesa). Se agrega un punto por lote de Condesa, ajustado al tramo más cercano a menos de 100 m ({{cfg:custom_sample_points:}}). Los lotes a más de 100 m de una calle mapeada están en fraccionamientos cuyas calles no están en OpenStreetMap; se dejan sin valor en lugar de atribuirles un acceso que no tienen.

El análisis tiene {{fact:sample_points}} puntos de muestra.

**Recálculo.** Conserve los puntos con sus `n1`, `n2`, `d1`, `d2` y el grafo de la red (tramos con su longitud). Una edición de la red cambia el grafo y los puntos de los tramos nuevos.

<a id="r2"></a>
## R2. Distancia por la red al destino más cercano, censurada

**Teoría.** Para un conjunto de destinos `D`, unidos a la red en los nodos extremos de su tramo más cercano con sus desplazamientos, la distancia de un nodo es `D(n) = mín sobre destinos (distancia por la red(n, nodo) + desplazamiento)`. La distancia del punto es

```text
d(p) = mín( D(n1) + d1 ,  D(n2) + d2 )
```

Las distancias se buscan en bandas (300, 500, 1,000, 1,500 m) y se censuran en la mayor: un nodo sin destino a 1,500 m no tiene distancia, y tampoco el punto. El valor de un punto puede exceder 1,500 m hasta por su desplazamiento a lo largo del tramo.

**Práctica.**

- El ruteo es no dirigido sobre la longitud de los tramos: `pgr_drivingDistance` de pgRouting o, en memoria, un Dijkstra desde una superfuente por conjunto de destinos, limitado a la banda mayor ({{code:_accessibility_spec.py:_banded_distances}}, {{code:_accessibility_spec.py:_nearest_distances_inmemory}}). En cada banda mayor solo se vuelven a rutear los orígenes que aún no alcanzan todos los destinos.
- Las distancias de los puntos se toman de las distancias de los nodos ({{code:setup_sp.py:create_full_nodes}}, {{code:setup_sp.py:process_distant_nodes}}).
- Cada destino es una especificación configurada ({{cfg:    destinations:}}). Su distancia es `sp_walk_nearest_node_<nombre>` en los puntos y `avg_walk_dist_<nombre>` en las áreas.

**Recálculo.** Agregar o quitar un destino cambia `d` solo donde pasa a ser, o deja de ser, el más cercano. Ejecute un Dijkstra desde los destinos modificados, limitado a 1,500 m, y tome el mínimo con la distancia almacenada; una eliminación requiere el siguiente más cercano, así que almacene el segundo más cercano o vuelva a rutear localmente.

<a id="r3"></a>
## R3. Acceso por bandas y lejanía de una desamenidad

**Teoría.** Acceso binario a una distancia `D`: `a = 1` si `d ≤ D`, si no 0; una distancia faltante (nada a 1,500 m) vale 0. Para una desamenidad (`direction: avoid`), el indicador es la lejanía: `b = 1 − a`, de modo que no encontrar nada vale 1. Para un área, el porcentaje de sus puntos de muestra con acceso, `pct_access_walk_<nombre>_<D>m` (o `pct_beyond_…`).

**Práctica.** {{code:_accessibility_spec.py:sample_point_access}}, {{code:setup_sp.py:binary_access_score}}. Una especificación puede fijar sus propias distancias, como la gasolinera (250 m).

<a id="r4"></a>
## R4. Diversidad de lo alcanzable

**Teoría.** Para un conjunto de `k` subtipos configurados, `c_g` es el número de destinos distintos del subtipo `g` alcanzables a la distancia `D`. Entonces

```text
p_g = c_g / Σ c          H = − Σ_{p_g > 0} p_g · ln p_g  /  ln k          (0 … 1)
R   = #{g : c_g > 0} / k                                                  (riqueza)
```

`k` es el número de subtipos configurados, no el de los presentes, de modo que la puntuación es comparable entre lugares. No alcanzar nada, o un solo subtipo, vale 0. Los conteos de un punto se interpolan desde sus nodos extremos, `c(p) = Σ_i (1 − d_i/(d1 + d2)) · c(n_i)`, por lo que pueden ser fraccionarios.

**Práctica.** {{code:_accessibility_spec.py:diversity_sets}}, {{code:_accessibility_spec.py:_banded_counts}}, {{code:_accessibility_spec.py:normalised_entropy}}, {{code:_accessibility_spec.py:richness}}. Los conjuntos se configuran en {{cfg:    diversity:}}. El ULI usa `sp_walk_diversity_<conjunto>_500m`.

**Recálculo.** Un destino agregado a menos de `D` de un punto suma 1 al conteo de su subtipo; recalcule `H` en los puntos afectados.

<a id="r5"></a>
## R5. Áreas de servicio en línea recta

**Teoría.** `d(p)` es la distancia en línea recta a la estación más cercana, buscada hasta `max_distance`. Más allá no hay valor.

**Práctica.**

- Cada especificación lee su propio archivo y filtro, recortado a la región de estudio ampliada por `max_distance` y fuera de la región de exclusión ({{code:_euclidean_accessibility.py:resolve_spec}}, {{code:_euclidean_accessibility.py:import_destinations}}).
- La estación más cercana se encuentra con una búsqueda KNN ({{code:_euclidean_accessibility.py:nearest_distances}}).
- Los resultados son `sp_euclid_dist_<nombre>` y `avg_euclid_dist_<nombre>` ({{cfg:  euclidean:}}).

<a id="r6"></a>
## R6. Nivel de estrés del tráfico y red ciclista de bajo estrés

**Teoría.** Cada tramo recibe un nivel de estrés del tráfico (LTS) de 1 (apto para todos) a 4, según su infraestructura ciclista, velocidad y tránsito supuesto. La red de bajo estrés son los tramos con LTS ≤ 2 donde se permite circular en bicicleta (o empujarla). La distancia al destino más cercano por ella sigue R2, con bandas de 500, 1,000, 2,000 y 5,000 m. Las reglas están en la entrada [Red ciclista por nivel de estrés del tráfico](entries/lts_network.md).

**Práctica.** {{code:_cycling_lts_network.py:assign_lts}}, {{code:_cycling_lts_network.py:add_impedance}}, {{code:_cycling_accessibility.py:cycling_poi_distance}}. Resultado: `sp_cycle_safe_nearest_node_<destino>`.

<a id="r7"></a>
## R7. Vinculación de indicadores preparados externamente

**Teoría.** Un valor preparado fuera de GHSCI para un conjunto de áreas se une a las áreas de referencia que le corresponden y luego se replica a los puntos de muestra que contienen esas áreas, para puntuarlo como cualquier otro indicador.

**Práctica.**

- **Emparejamiento por identificador** (`match: id`, UTCI) o **por geometría** (`match: geometry`, el archivo de los paquetes de trabajo, que no trae identificadores) ({{code:_linkage_indicators.py:match_by_geometry}}). Por geometría se intenta primero una coincidencia exacta normalizada; si no la hay, el área de referencia que contiene la mayor parte, si es al menos la mitad.
- Las partes emparejadas con una misma área se combinan como media ponderada por área ({{code:_linkage_indicators.py:combine_matched}}).
- `null_as` rellena los valores faltantes y después `mask` anula los poco confiables ({{code:_linkage_indicators.py:apply_rules}}).
- **A los puntos de muestra:** desde la primera capa configurada que tenga un valor, por contención o a una distancia ({{code:_linkage_indicators.py:sample_point_values}}), lo que da `sp_<prefijo><columna>`. Son valores replicados: todos los puntos de un área tienen el valor de esa área.

<a id="r8"></a>
## R8. Earth Engine: vulnerabilidad al calor y grandes espacios verdes

**Teoría.**

- **GUHVI** (Turner et al. 2025) combina exposición, sensibilidad y capacidad de adaptación, cada una media de insumos normalizados mín.–máx. a 0–100 dentro de la región. Los detalles están en la entrada [GUHVI y sus insumos](entries/guhvi.md).
- **Gran espacio verde público urbano** es el espacio público abierto de al menos 1 ha con NDVI medio anual ≥ 0.2.

**Práctica.** {{code:_earth_engine_indicators.py:guhvi_analysis}}, {{code:_earth_engine_indicators.py:normalise_band}}. Los puntos de muestra toman el valor de la celda GUHVI que los contiene. El acceso a grandes espacios verdes sigue R2 y R3 a 500 m. Requieren el contenedor de Earth Engine y `gee: true`.

<a id="r9"></a>
## R9. Caminabilidad y su atenuación por confort térmico

**Teoría.**

```text
DL   = a_mercado_alimentos_frescos(300) + a_conveniencia(300) + a_transporte(300)   (0 … 3)
W    = z(DL) + z(densidad de población) + z(densidad de intersecciones)
         z(x) = (x − media(x)) / de(x), sobre todos los puntos de muestra urbanos (de muestral)
h′   = recortar( (UTCI − 30) / (50 − 30), 0, 1 )
W_tm = rango_percentil(W) · (1 − λ · h′),   λ = 0.5
```

Las densidades son promedios del vecindario a 1,000 m por la red. El rango percentil promedia los empates y está en (0, 1]. Atenuar por multiplicación significa que la sombra no compensa no tener a dónde caminar: un lugar sin nada al alcance puntúa bajo por fresco que sea.

**Práctica.** {{code:_11_neighbourhood_analysis.py:compute_nodes_pop_intersect_density}}, {{code:_walkability_variants.py:compute_variants}}, {{code:_walkability_variants.py:percentile_rank}}, {{code:_walkability_variants.py:rescale}} ({{cfg:walkability_variants:}}). Los límites con que se reescaló cada medida de calor se registran en el comentario de la tabla `sample_points_walkability`. Los percentiles 5 y 95 observados del UTCI diurno fueron {{fact:utci_p5}} y {{fact:utci_p95}} °C.

<a id="r10"></a>
## R10. Transformaciones: umbrales suaves y escalas escalonadas

**Teoría.** Una distancia entra en el índice a través de una transformación, de modo que estar más cerca cuenta, pero cada vez menos más allá de un umbral:

```text
umbral suave:     s(d) = 1 / (1 + exp( k · (d − t) / t )),   k = 5
                  s(0) ≈ 0.993,  s(t) = 0.5,  s(2t) ≈ 0.007;  d faltante → 0
escala escalonada: s(d) = puntuación del primer escalón con d ≤ distancia;  más allá o faltante → puntuación «más allá»
```

Por ejemplo, con un umbral de 300 m, 150 m vale 0.92, 300 m vale 0.50 y 450 m vale 0.08. GHSCI advierte si la distancia de censura es menor que `2t`. Por eso las distancias se buscan hasta 1,500 m (cinco veces 300 m) y las estaciones de policía hasta 45 km.

**Práctica.** {{code:_composite_index.py:soft_threshold}}, {{code:_composite_index.py:stepped_score}}, {{code:_composite_index.py:prepare}}. La `transform` de cada indicador está en {{cfg:composite_indices:}}.

<a id="r11"></a>
## R11. Normalización: el Índice Ajustado de Mazziotta–Pareto (AMPI)

**Teoría.** Cada indicador preparado `x` (transformado cuando tiene transformación) se reescala contra metas:

```text
r = 100 ± 60 · (x − Ref) / (Máx − Mín)        + si mayor es mejor, − si menor es mejor
Ref = media de x sobre todos los puntos de muestra de la región de estudio
Mín, Máx = Ref ∓ (sup − inf) / 2              inf, sup = mínimo y máximo observados
```

Así `Máx − Mín` es el rango observado, y `r` abarca de 70 a 130 alrededor de la referencia en 100. Un indicador con metas configuradas (los subíndices GUHVI: 0 y 100) usa esas. Un indicador que no varía se descarta con una advertencia. La polaridad se configura o se infiere del nombre de la variable.

**Práctica.** {{code:_composite_index.py:resolve_parameters}}, {{code:_composite_index.py:normalise}}, {{code:_composite_index.py:infer_polarity}}. Las metas usadas se escriben en `MX_Mexicali_2025_ULI_composite_<índice>_parameters.yml`, publicado con este manual ([`data/`](../data/)) y tabulado en el [Anexo C](C_goalposts.md). Ahí se registran también la asimetría, la curtosis y la proporción de empates de cada indicador (`distribution`).

<a id="r12"></a>
## R12. Agregación: dominios, indicadores compartidos e índice

**Teoría.** La puntuación de un dominio es el compuesto ponderado de Mazziotta–Pareto de las puntuaciones `r_i` de sus indicadores. Un indicador listado en `k` dominios cuenta `1/k` de su peso en cada uno (`share`), de modo que en total no pesa más que un indicador de un solo dominio:

```text
w_i = weight_i · share_{i,d} / Σ_j weight_j · share_{j,d}       (sobre los indicadores con valor)
M   = Σ w_i r_i        S = √( Σ w_i (r_i − M)² )        cv = S / M
dominio = M − S · cv                       (penalización S·cv: el desequilibrio baja la puntuación)
índice  = lo mismo sobre los seis dominios puntuados, cada uno con peso 1
puntuación reportada = puntuación − 100    (centre: 0; la penalización se reporta tal cual)
```

La penalización divide entre la media, por lo que las puntuaciones se calculan en 100 y se reportan menos 100. Un punto se puntúa solo donde todos los indicadores de un dominio y todos los dominios tienen valor (`min_valid`: todos). El **peso efectivo** de un indicador es su parte del nivel medio del índice:

```text
e_i = Σ_d (W_d / Σ W) · (weight_i · share_{i,d} / Σ_j weight_j · share_{j,d})
```

En Mexicali van de {{fact:eff_min}} a {{fact:eff_max}}.

**Práctica.** {{code:_composite_index.py:mpi_aggregate}}, {{code:_composite_index.py:score}}, {{code:_composite_index.py:share_of}}, {{code:_composite_index.py:effective_weights}}.

**Variantes.** `uli_plain` sustituye la caminabilidad atenuada por la caminabilidad sola y activa el confort térmico como indicador del entorno medioambiental, contra sus propias metas ({{code:_composite_index.py:expand_variants}}).

<a id="r13"></a>
## R13. De los puntos de muestra a las áreas

**Teoría.** Las puntuaciones se calculan en los puntos de muestra y luego se promedian. La puntuación del índice de un área es la media de las puntuaciones del índice de sus puntos, no un compuesto de las puntuaciones medias de dominio del área.

| Área | Valor |
|---|---|
| Cuadrícula de 100 m | media no ponderada de los puntos de muestra de la celda |
| AGEB, región (región de estudio) | media de las celdas ponderada por `pop_est × parte del área` |
| Manzanas | media no ponderada de los puntos de muestra a menos de 30 m |
| Lotes de Condesa | media no ponderada de los puntos de muestra a menos de 15 m |
| Fraccionamientos, región (Condesa) | media de los lotes (3.2 residentes cada uno) por parte del área |

Las columnas de acceso (`pct_*`) se multiplican por 100 al agregarse.

**Práctica.** {{code:_12_aggregation.py:_propagate_sample_point_columns}}, {{code:_12_aggregation.py:custom_aggregation}}, {{code:_12_aggregation.py:_custom_area_query}}, {{code:_composite_index.py:propagate}}. Los planes de agregación se registran en la tabla `aggregation_plans` de la base de datos.

<a id="r14"></a>
## R14. Metas congeladas y recálculo de un escenario

Las metas hacen comparables las puntuaciones: un escenario puntuado contra las metas de la línea base está en la misma escala, y sus puntuaciones pueden salir del rango 70–130 si mejora lo mejor observado. Para recalcular un punto de muestra después de un cambio, por ejemplo un parque nuevo, una calle sombreada o una escuela nueva:

```python
params = yaml.safe_load(open('MX_Mexicali_2025_ULI_composite_uli_parameters.yml'))

def indicator_score(i, raw):                    # raw: el valor medido del punto
    spec = params['indicators'][i]
    x = transform(spec['transform'], raw)        # R10: umbral suave, escalones o tal cual
    sign = 1 if spec['polarity'] == 'positive' else -1
    return 100 + sign * 60 * (x - spec['reference']) / (spec['max'] - spec['min'])

def mpi(scores, weights):                        # R12
    w = {i: weights[i] / sum(weights[j] for j in scores) for i in scores}
    M = sum(w[i] * scores[i] for i in scores)
    S = (sum(w[i] * (scores[i] - M) ** 2 for i in scores)) ** 0.5
    return M - S * S / M

r = {i: indicator_score(i, raw[i]) for i in params['indicators']}
domains = {d: mpi({i: r[i] for i in r if d in params['indicators'][i]['domains']},
                  {i: params['indicators'][i]['weight'] * params['indicators'][i]['domains'][d]
                   for i in r if d in params['indicators'][i]['domains']})
           for d in params['domains']}
uli = mpi(domains, params['domains']) - 100     # se reporta en puntos respecto al promedio
```

Después se promedia a las áreas como en R13. Una comprobación útil de una nueva implementación: volver a puntuar los valores medidos de la línea base contra estas metas debería reproducir el `sp_index_uli` publicado (este manual no ha hecho esa comprobación, que requiere las tablas de puntos de muestra de la base de datos). GHSCI lo hace con `r.composite_index(goalposts=…)` ({{code:_composite_index.py:load_goalposts}}).

Qué cambia en cada caso:

- **Un destino** (comercio, escuela, parada): recalcule sus distancias (R2), los conteos de diversidad (R4) y el puntaje de vida cotidiana de la caminabilidad (R9) a su alrededor.
- **Sombra, vegetación o materiales:** el UTCI y el NDVI vinculados de las áreas afectadas (R7), y luego la atenuación de la caminabilidad (R9).
- **Calles o cruces:** la red y, por tanto, toda distancia cerca del cambio (R2), la densidad de intersecciones (R9) y, para la bicicleta, el LTS (R6).
- **Nuevos residentes:** la densidad de población (R9) y los pesos de población en las áreas (R13).
