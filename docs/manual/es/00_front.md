# Presentación

**Índice de entornos vivibles para Mexicali** — Manual técnico: recetario de indicadores, dominios e índice

| | |
|---|---|
| Proyecto | Índice de entornos vivibles para Mexicali (*Mexicali Urban Liveability Index*), Mexicali y el distrito Condesa, Baja California, México |
| Equipo del proyecto | Carl Higgs (RMIT University), Eugen Resendiz, Juan Ernesto Díaz Noguez y el equipo del Tecnológico de Monterrey |
| Financiamiento | Tecnológico de Monterrey, 2026 |
| Software | Global Healthy and Sustainable City Indicators (GHSCI) 4.15.2 (entorno 4.15.0), rama `mexicali` ([`f039096`](https://github.com/healthysustainablecities/global-indicators/tree/f03909611dba336c2728fffab6d697779487d0b1)) |
| Ejecución del análisis | 2026-09-26; metas del índice resueltas el 2026-09-26 a partir de 154,239 puntos de muestra |
| Manual generado | 2026-11-11, a partir del repositorio del ULI en `c453d78` |
| Estado | Borrador para revisión del equipo del proyecto. El texto en español es un borrador para revisión de Eugen Resendiz y Juan Ernesto Díaz Noguez; donde el registro de indicadores da la justificación solo en inglés, esta edición marca su traducción como preliminar. |
| Licencia | Este manual (texto, mapas y tablas): [CC BY 4.0](../LICENSE.md). El código que lo genera y el resto del repositorio: MIT. Los conjuntos de datos de insumo conservan sus propias licencias ([Anexo D](D_datasets.md)), y los mapas y valores derivados de ellos siguen sujetos a esos términos cuando imponen condiciones (por ejemplo, el UTCI se modeló con el terreno FABDEM, CC BY-NC-SA 4.0). |

**Cita sugerida.** Higgs, C., Resendiz, E., Díaz Noguez, J. E. y equipo del Tecnológico de Monterrey (2026). *Índice de entornos vivibles para Mexicali: manual técnico.* Tecnológico de Monterrey y RMIT University. https://github.com/healthysustainablecities/condesa_mexicali_liveability

## Para qué sirve este manual

El Índice de entornos vivibles para Mexicali (ULI, por sus siglas en inglés) resume qué tan bien el entorno cotidiano de cada lugar de Mexicali y del distrito Condesa favorece una vida sana y vivible. Combina 28 indicadores de seis dominios del Marco Adaptado de Entornos Urbanos Vivibles en una sola medida compuesta. Se calcula en puntos de muestra a lo largo de la red peatonal y se resume para la cuadrícula de 100 m, las áreas censales (AGEB), las manzanas, y los lotes y fraccionamientos de Condesa.

Este manual es el **recetario** de ese trabajo. Está escrito para un equipo que vuelva a implementar los métodos, en particular en Reimagina Urbano, donde los indicadores se recalcularían al momento ante cambios en las condiciones del entorno. También es el registro técnico del proyecto. Para cada indicador, subindicador, puntuación de dominio y para el índice mismo, da:

- **identificación:** nombres, variables en cada escala, dominios y pesos;
- **justificación e interpretación:** por qué importa, según el registro del proyecto, y cómo leerlo;
- **fuentes de datos:** los registros configurados de cada conjunto de datos que usa, con referencias cruzadas a las entradas de insumos;
- **método:** la teoría (fórmulas) y la práctica (configuración, funciones de GHSCI, recálculo);
- **resultados:** un resumen breve de la distribución para la región de estudio (Mexicali, incluida Condesa) y para Condesa;
- **mapa:** manzanas de la región de estudio, con los lotes de Condesa, leyenda, escala gráfica y flecha de norte.

## Cómo leer una entrada

Las recetas (R1–R14, [sección 3](03_recipes.md)) describen una sola vez cada método compartido; las entradas las citan. Las referencias al código enlazan a la línea exacta en GitHub en la versión indicada arriba. Las referencias a la configuración apuntan a la copia de la configuración de la región publicada con este manual ([`data/MX_Mexicali_2025_ULI.yml`](../data/MX_Mexicali_2025_ULI.yml)), cuyos comentarios registran por qué se tomó cada decisión.

Las puntuaciones son puntos por encima o por debajo del promedio de la región de estudio (0). Cada indicador se reescala de modo que la media de la región de estudio, sobre todos los puntos de muestra, vale 0, y su rango observado abarca 30 puntos a cada lado ([R11](03_recipes.md#r11)). Las puntuaciones de dominio y del índice combinan esas puntuaciones, menos una penalización por desequilibrio ([R12](03_recipes.md#r12)).

Nada en este manual se estima a mano. Los nombres, descripciones y lecturas provienen de la configuración de la región. Las metas y los pesos provienen de los parámetros que escribió el análisis. Las clases y unidades provienen de la exportación del tablero, los valores del GeoPackage de resultados a precisión completa, y la justificación del registro de indicadores del proyecto. Donde ninguno de estos registra algo, el manual dice *Pendiente*.
