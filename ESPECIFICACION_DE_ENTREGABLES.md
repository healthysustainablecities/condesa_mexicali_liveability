# Índice de Habitabilidad de Mexicali — especificación de entregables

**Versión 1.0 · agosto de 2026.** Este documento describe el *formato* en el que
deben entregarse los resultados de los indicadores. Qué se debe calcular se
aborda en el informe técnico por separado.

*Traducción de [`OUTPUT_SPECIFICATION.md`](OUTPUT_SPECIFICATION.md); en caso de
discrepancia, la versión en inglés es la de referencia.*

---

## 1. Qué entregar

Para cada conjunto de indicadores que se le asigne:

| | |
|---|---|
| **Resultados** | Una tabla por escala espacial — GeoPackage (`.gpkg`) o CSV (`.csv`) |
| **Diccionario de datos** | Una tabla que describa cada variable generada (`.csv` o `.xlsx`) |

No se requiere nada más. Si alguna escala no aplica a sus datos, indíquelo en el
diccionario de datos en lugar de omitirla sin explicación.

## 2. Sistema de referencia de coordenadas

**Mexico ITRF2008 / UTM zona 11N — EPSG:6366**, para todos los productos
espaciales.

Las geometrías de referencia de cada escala se proporcionan en
`mexicali_reference_areas.gpkg`, ya en esta proyección. Utilícelas tal como se
entregan: no vuelva a trazar los límites ni genere su propia cuadrícula, pues los
resultados no coincidirían con los de las demás personas.

## 3. Escalas espaciales

Entregue resultados en cada escala que sus datos realmente permitan, para **ambas**
áreas de estudio: la mancha urbana de Mexicali y el desarrollo Condesa.

| Escala | Capa en el geopaquete de referencia | Áreas | Identificador del área |
|---|---|---|---|
| Cuadrícula de población de 100 m | `grid_100m` | 33,451 | `area_id` (celda) |
| Manzana | `manzanas` | 13,656 | `area_id` = `CVEGEO` del INEGI |
| AGEB | `agebs` | 436 | `area_id` = `CVEGEO` del INEGI |
| Región | `region` | 2 | `area_id` = `mexicali` o `condesa` |
| Fraccionamientos de Condesa | `condesa_fraccionamientos` | 40 | `area_id` |
| Lotes de Condesa | `condesa_lotes` | 14,989 | `area_id` |

Se incluyen todas las áreas, incluso aquellas para las que no puede calcularse
ningún valor, de modo que la cobertura parcial sea visible y no quede oculta.
Cada capa incluye además `area_sqm` y `pop_2025` (GHS-POP 2025, repartida por
superficie a partir de la cuadrícula).

**Las escalas no cubren la misma superficie.** Solo la cuadrícula y las capas de
región abarcan la totalidad del área de estudio. Las manzanas son bloques y
excluyen las calles que las separan: cubren el 46% de la superficie y el 77% de
la población; las AGEB cubren el 63% de la superficie y el 99% de la población.
Por ello, **no calcule una cifra para toda la ciudad sumando o promediando
manzanas**, pues omitiría cerca de una cuarta parte de la población. Utilice la
capa `region` para los valores de ciudad.

La cuadrícula de 100 m corresponde a la cuadrícula de población GHS-POP 2025,
transformada de Mollweide a EPSG:6366 y vectorizada. Las celdas miden exactamente
100 m × 100 m, y la transformación conserva los conteos de población.

## 4. Estructura de las tablas

**Una fila por área y una columna por indicador.** No una fila por combinación de
indicador y área.

| `area_id` | `pct_pop_500m_open_space` | `dist_m_nearest_school` |
|---|---|---|
| `020020001661A041` | 42.6 | 385.2 |
| `020020001661A056` | 0.0 | 1204.7 |

- La primera columna es **`area_id`** y debe coincidir exactamente con la
  geometría de referencia. En las tablas de región basta con el nombre
  (`mexicali`, `condesa`).
- Cada una de las demás columnas corresponde a un indicador.
- Entregue los valores en sus unidades naturales. No los normalice, reescale ni
  convierta en índices: eso se hace una sola vez, de forma centralizada, para que
  se realice de manera consistente.
- Deje la celda vacía cuando realmente no exista valor. No utilice `0`, `-999` ni
  el texto `NA` para indicar un dato faltante.

## 5. Nomenclatura de variables

- **Minúsculas y guiones bajos en lugar de espacios**: `pct_pop_500m_open_space`.
- Sin acentos, espacios, guiones ni signos de puntuación.
- **Es preferible la claridad a la brevedad.** Hasta unos 30 caracteres está bien:
  `mean_summer_temperature_c` es mejor que `mst`.
- Comience por lo que representa el número (`pct_`, `count_`, `dist_m_`, `mean_`)
  y después por aquello que describe.

## 6. Diccionario de datos

Una fila por variable, con estas columnas (los nombres de las columnas se
mantienen en inglés):

| Columna | Contenido |
|---|---|
| `variable` | El nombre de la columna tal como aparece en sus resultados |
| `description` | Lenguaje sencillo, **en español o en inglés**: qué significa el número |
| `units` | p. ej. `metros`, `porcentaje`, `conteo`, `personas por km2`, `adimensional` |
| `statistic` | uno de `value`, `mean`, `median`, `percentage`, `count`, `sum`, `rate`, `index`, `category` (valor, promedio, mediana, porcentaje, conteo, suma, tasa, índice, categoría) |
| `scale` | En qué escala o escalas se proporciona la variable |
| `source` | El conjunto de datos del que proviene el valor |

Ejemplo:

| variable | description | units | statistic | scale | source |
|---|---|---|---|---|---|
| `pct_pop_500m_open_space` | Porcentaje de residentes a 500 m o menos, caminando, de un espacio público abierto | porcentaje | porcentaje | grid_100m, manzanas, agebs, region | OpenStreetMap, abril de 2026 |
| `mean_summer_temperature_c` | Temperatura superficial promedio diurna, de junio a agosto | grados Celsius | promedio | grid_100m, agebs | Landsat 8/9, 2024–2025 |
| `count_pharmacies` | Número de farmacias ubicadas dentro del área | conteo | conteo | manzanas, agebs | DENUE 2025 |

Las columnas `units` y `statistic` son importantes: sin ellas, una columna de
números no puede interpretarse, combinarse ni cartografiarse correctamente.

Utilice `value` para una medición directa (no agregada) y `rate` para un conteo o
cantidad por unidad de superficie o de población.

Los indicadores generados con el programa GHSCI ya incluyen estas columnas en el
diccionario de datos que produce, de modo que pueden utilizarse tal cual.

## 7. Documentación de las fuentes

Para cada conjunto de datos utilizado, registre en el diccionario de datos o en
una nota adjunta: el nombre y la institución responsable, la cita, la URL, la
fecha de descarga y la licencia.

## 8. Dos cuestiones sobre Condesa

**Está en gran medida sin construir y sin habitantes.** Los productos de población
registran apenas unos cientos de residentes en todo el desarrollo. Los valores
ponderados por población serán inestables o vacíos: conviene preferir medidas
basadas en superficie o por lote, e indicar cuándo una fuente sencillamente no
cubre la zona.

**Se extiende más allá del límite de la mancha urbana.** Alrededor del 18% del
desarrollo queda fuera del área urbana cartografiada de Mexicali, por lo que las
geometrías de referencia abarcan la unión de ambas. Si las utiliza tal como se
entregan, Condesa queda cubierta por completo.

---

## Lista de verificación antes de enviar

- [ ] EPSG:6366
- [ ] Una fila por área, una columna por indicador
- [ ] `area_id` coincide exactamente con las geometrías de referencia
- [ ] Nombres de variables en minúsculas y con guiones bajos
- [ ] Todas las variables aparecen en el diccionario de datos, con `units` y `statistic`
- [ ] Valores en unidades naturales, sin normalizar
- [ ] Fuentes documentadas con fecha de descarga y licencia
