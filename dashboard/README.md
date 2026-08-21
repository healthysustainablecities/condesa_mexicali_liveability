# Explorador de indicadores · Indicator explorer

Un tablero estático para explorar los indicadores GHSCI de Mexicali y Condesa,
lado a lado. / A static dashboard for exploring the GHSCI indicators for
Mexicali and Condesa, side by side.

---

## Qué hace / What it does

Dos paneles, **un indicador compartido**. Cada panel elige su propia región
(Mexicali o Condesa), su escala de agregación (cuadrícula de 100 m, AGEB,
manzanas, fraccionamientos, lotes) y sus capas de apoyo; el indicador, la
medida, la red y la clasificación son comunes a ambos, de modo que los colores
significan lo mismo en los dos lados.

Two panes, **one shared indicator**. Each pane picks its own region, its own
aggregation scale and its own supporting layers; the indicator, measure,
network and classification are shared, so a colour means the same thing on both
sides. Because both regions come from a single analysis — one network, one
population grid, one destination set — the differences shown are real rather
than artefacts of separate runs.

The same interface compares two *scales* of one region against each other
(manzanas against AGEBs), which is the honest way to show how much the choice of
aggregation drives a result.

## Primeros pasos / Getting started

```bash
bash build/fetch-vendor.sh     # once: MapLibre and PMTiles into vendor/
node build/smoke.mjs mexicali  # checks the exporter/viewer contract
```

Then double-click `launch.bat` (Windows) or `launch.command` (macOS), or:

```bash
bash serve.sh                  # http://localhost:8123/
```

**A server is required.** PMTiles reads its archives with HTTP range requests,
which `file://` does not support, so opening `index.html` directly will show an
empty map. Everything else is local.

Basemap tiles (CARTO, Esri) are the one thing that still needs the internet.
Choose **sin mapa base / no basemap** when there is none: the indicator layers
still render.

## Cómo se generan los datos / Regenerating the data

Three steps, in the analysis repo and then here:

```bash
# 1. in the ghsci container: layers, manifest, stats, vocabulary
/env/bin/python _export_dashboard.py "data/MX/MX_Mexicali_2025_ULI.yml"

# 2. here: build the PMTiles archives (needs docker image tippecanoe:local)
docker build -t tippecanoe:local build/
bash build/build_tiles.sh mexicali

# 3. here: copy into data/ and rebuild the dataset index
bash build/deploy.sh mexicali
```

The exporter is generic: it reads the region's own `accessibility`,
`cycling_indicators` and `custom_aggregations` configuration, enumerates every
indicator column those imply, keeps the ones the database actually has, and
writes the vocabulary out as data. Adding a destination or a distance band to
the region config and re-running the analysis is enough — nothing in this site
lists indicators.

What the dashboard offers is declared in a `dashboard:` block in the region
YAML — nothing in this site lists indicators, names them, or colours them:

| key | what it declares |
|---|---|
| `slug`, `label`, `scales`, `scale_labels` | identity, and which aggregation scales to export |
| `regions` | the regions a pane can show, each naming the custom aggregation that summarises it and the scales it may be shown at |
| `themes` | the workshop's typology: label, colour, and the families belonging to each. **The primary grouping in the picker.** |
| `labels` | Spanish and English names for every indicator family and standalone variable |
| `interventions` | path to the workshop's matching spreadsheet, which drives "¿Por qué importa?" |
| `style` | design tokens, applied as CSS variables |
| `crosswalk` | the ULI core measure crosswalk, driving the "por medida ULI" view |

Revising any of those costs only a re-export of the JSON — **not** a re-tile:

```bash
/env/bin/python _export_dashboard.py "data/MX/MX_Mexicali_2025_ULI.yml" --no-layers
```

Theme colours are used for identity only — picker, indicator title, info panel.
They are deliberately **not** used for the choropleth: eleven distinct hues are
not perceptually ordered, so as a data ramp they would stop colour meaning
magnitude and make the two panes incomparable across indicators.

## Cómo está dispuesto / How it is laid out

Todo lo que describe el **indicador** — su leyenda, sus resultados, su gráfica y
sus capas — vive en la barra lateral, porque el indicador es compartido entre
paneles. Cada panel lleva sólo lo que lo describe a sí mismo: su región, su
escala y su mapa base.

Everything describing the **indicator** — its legend, its results, its chart and
its layers — lives in the sidebar, because the indicator is shared between
panes. Each pane carries only what describes itself: its region, its scale and
its basemap. Duplicating a legend per pane costs space, covers the scale bar,
and invites the reader to think the two might differ.

## Cambiar los textos / Changing the wording

**Todo lo que se lee en pantalla se edita en `data/mexicali/text.json`.** Se
edita, se recarga el navegador y ya está: no hay que reconstruir nada, ni volver
a exportar, ni tocar el código.

```bash
# regenerar el archivo con cualquier texto nuevo, conservando lo ya editado
node build/make_text.mjs mexicali
```

El archivo tiene seis secciones:

| Sección | Qué contiene |
|---|---|
| `showing` | La frase en lenguaje llano bajo el nombre del indicador, por medida |
| `notes` | El párrafo «cómo leer este indicador» del panel de información |
| `scale_note` | La advertencia sobre las escalas de agregación |
| `measures` | El nombre de cada medida, en el menú y en el título de la leyenda |
| `networks` | La red tal como la nombra una *frase* («peatonal»), distinta de su etiqueta en el menú («Caminando») |
| `strings` | Cualquier etiqueta de la interfaz: botones, encabezados, notas |

En `showing` y `notes` se pueden usar estos marcadores, que se sustituyen según
lo seleccionado: `{network}` `{networkLabel}` `{distance}` `{bands}`
`{indicator}` `{description}`. Un marcador mal escrito se muestra como un hueco,
no como `{texto}`.

Borrar una clave hace que vuelva a usarse el valor por defecto del exportador.
`build/make_text.mjs` conserva lo editado y sólo añade lo nuevo — y elimina las
claves que la aplicación ya no lee, para que nadie edite algo que no se muestra.

**Everything on screen is edited in `data/mexicali/text.json`** — edit, refresh,
done. Placeholders in `showing` and `notes` are substituted from the current
selection; delete a key to fall back to the exporter's default.

### Lo demás / Everything else

Estos viven en la configuración de la región
(`process/configuration/regions/…` o `process/data/MX/MX_Mexicali_2025_ULI.yml`)
y necesitan volver a exportar (`--no-layers`) y redesplegar — unos minutos:

| Qué | Dónde |
|---|---|
| Nombres de indicadores y variables | `dashboard.labels.families` / `.variables` |
| Temas, colores, escalas, regiones, título | `dashboard.themes` / `scale_labels` / `regions` / `title` |
| Clases de color y metas | `dashboard.breaks` / `dashboard.thresholds` |
| Qué salidas aparecen | `dashboard.hide` |
| Notas por indicador | `dashboard.notes` |
| Fuente, licencia, cita, códigos SCIAN | `points_of_interest` de la región |
| Intervenciones e impactos | `Match intervenciones-A911-REIMAGINA-LIV.xlsx` |

## Cosas que conviene saber / Things worth knowing

**Las escalas no cubren el mismo terreno.** Sólo la cuadrícula y la región
cubren toda el área de estudio: las manzanas cubren el 46 % de la superficie y
el 77 % de la población, los AGEB el 63 % y el 99 %. Por eso el resumen bajo
cada mapa distingue el *valor de la región* (autoritativo) de los percentiles
*de las áreas mostradas*, y nunca presenta un promedio de manzanas como cifra
de la ciudad.

**Condesa apenas tiene población registrada**, así que los promedios ponderados
por población son inestables allí; donde el cálculo recurrió a un promedio sin
ponderar, el panel lo dice.

**El acceso es un porcentaje, a una distancia elegida.** El mapa se dibujaba
antes por la banda más cercana en la que al menos la mitad de los puntos de
muestreo de un área alcanzaban el destino — una regla que costaba un párrafo
explicar y que dejaba inerte el selector de distancia. Ahora se dibuja el
porcentaje que ya se calcula para cada área a cada distancia, y el selector
elige cuál. La tabla sigue mostrando las tres distancias: la que está en el mapa
va recuadrada, y las otras dos son las que le dan sentido.

**Access is the percentage, at a chosen distance** — the statistic that already
exists per area, rather than the nested-band rule that needed explaining. The
results table still shows every distance, with the mapped one outlined.

**La clasificación la calcula el exportador, no el visor.** Las clases de color
y la proporción de población en cada una salen del mismo cálculo, y por eso la
leyenda puede dibujarse justo debajo de la gráfica como su eje: ambas tienen el
mismo número de celdas, del mismo ancho y en el mismo orden. Un corte que cae
dentro de un intervalo del histograma no se puede recuperar después, así que
ninguno de los dos se calcula por separado.

Las unidades declaradas pueden estar equivocadas: los índices GUHVI se
declaraban «index 0-1» pero contienen valores de 3 a 56, de modo que cualquier
corte de 0 a 1 dejaba cada área en la clase superior y dibujaba el mapa de un
solo color. Un rango declarado sólo se usa si los datos caben dentro y ocupan
una parte razonable de él; si no, los cortes salen de los datos.
`build/smoke.mjs` comprueba que ninguna columna quede fuera de su propia escala,
que las clases y las barras coincidan en número, y que recorriendo todo el
dominio de una columna el mapa pinte cada clase una vez y en orden.

**Los cortes y las metas se configuran por columna**, en el bloque `dashboard`
del YAML de la región — no en el código:

```yaml
dashboard:
  breaks:
    local_walkability: [-3, -2, -1, 0, 1, 2, 3]   # colas agrupadas: "< -3", "≥ 3"
    local_daily_living: {edges: [0, 1, 2, 3], closed: true}
    local_nh_population_density: {scale: log2, classes: 7}
    urban_heat_guhvi_class: {categories: [1, 2, 3, 4, 5]}
  thresholds:
    local_nh_population_density: {criteria: 5700, relationship: '>='}
  hide:
    - urban_heat_subnational_hdi     # constante en una sola ciudad
```

Una escala `log2` cuelga sus cortes de la meta de la columna, doblando hacia
arriba y hacia abajo: la meta siempre es un borde, y la clase superior significa
exactamente «la alcanza». Dibujadas como celdas del mismo ancho, esas
duplicaciones *son* el eje logarítmico, y la clase inferior abierta es lo que
permite mostrar en él los ceros reales que ambas densidades contienen.

Las metas se toman automáticamente del bloque `thresholds` de la configuración
de referencia de GHSCI (`configuration/indicators.yml`), así que las dos metas
de densidad ya están presentes sin configurar nada; el bloque de arriba sirve
para añadir o corregir una meta acordada después.

**The classification is computed by the exporter, not the viewer**, together
with the share of population in each class — which is what lets the legend be
drawn directly beneath the chart as its axis. The breaks and the targets for any
column are configured per column in the region YAML's `dashboard` block, as
above; a `log2` scale hangs its edges off the column's target so the target is
always an edge and the top class means exactly "meets it".

**Todas las áreas aparecen, incluso sin resultado.** La agregación borra las
áreas que no recibieron unidades de origen (38 de 40 fraccionamientos
sobreviven), así que la exportación une las geometrías por la izquierda y las
áreas sin dato se dibujan como «sin datos» en lugar de desaparecer.

## Estructura / Layout

| | |
|---|---|
| `index.html` | markup and the DOM contract |
| `js/app.js` | orchestration: loads the data, wires controls, repaints |
| `js/state.js` | the state object and its URL-hash serialisation |
| `js/vocab.js` | the indicator vocabulary; resolves a selection to columns |
| `js/choropleth.js` | classification and MapLibre paint expressions |
| `js/legend.js` | the legend, and the class isolation clicking it drives |
| `js/pane.js` | one map pane: style, layers, popups, camera |
| `js/results.js` | the region results table, and the difference between regions |
| `js/stats.js` | the distribution chart, and what it means in words |
| `js/showing.js` | the plain-language line: what the map is showing, and why |
| `js/theme.js` | the workshop themes and the design tokens |
| `js/tour.js` | the guided tour, which drives real state rather than describing it |
| `js/info.js` | "cómo leer este indicador" and "¿por qué importa?" |
| `js/measure.js` | the measure tool |
| `js/imageexport.js` | PNG export with legend, scale bar and attribution |
| `js/dictionary.js` | the data dictionary viewer |
| `js/strings.js` | every UI string, `es` first |
| `build/smoke.mjs` | headless checks of the exporter/viewer contract |
| `build/serve.py` | dev server with byte ranges (PMTiles needs them) and no caching |
| `data/<slug>/` | manifest, stats, vocabulary, dictionary, `.pmtiles` |

`data/**/*.pmtiles` is gitignored: the archives are large and are rebuilt from
the analysis, not versioned.

## Créditos / Credits

Built on the interaction patterns of the GHSCI cycling validation site —
the nested-band choropleth, the clickable legend that isolates a class, the
greying of permutations a region did not produce, and the measure tool.
