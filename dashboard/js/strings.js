// User-facing text.  Spanish is the primary language: this dashboard is for a
// Mexicali audience, and English is the secondary.  Indicator descriptions are
// not here — they come from the region's own generated data dictionary, in
// English, and fall back to English when no Spanish string was supplied, so a
// translation gap stays visible rather than hidden behind an invented phrase.

export const LANGS = ['es', 'en'];
export const DEFAULT_LANG = 'es';

const S = {
  title: { es: 'Explorador de indicadores', en: 'Indicator explorer' },
  compare: { es: 'Comparar', en: 'Compare' },
  single: { es: 'Vista única', en: 'Single view' },
  dataset: { es: 'Conjunto de datos', en: 'Dataset' },
  region: { es: 'Región', en: 'Region' },
  scale: { es: 'Escala de agregación', en: 'Aggregation scale' },
  indicator: { es: 'Indicador', en: 'Indicator' },
  domain: { es: 'Ámbito', en: 'Domain' },
  measure: { es: 'Medida', en: 'Measure' },
  network: { es: 'Red', en: 'Network' },
  distance: { es: 'Distancia', en: 'Distance' },
  variable: { es: 'Variable', en: 'Variable' },
  group: { es: 'Subtipo', en: 'Sub-type' },
  basemap: { es: 'Mapa base', en: 'Basemap' },
  streets: { es: 'Calles', en: 'Streets' },
  satellite: { es: 'Satélite', en: 'Satellite' },
  none: { es: 'Ninguno', en: 'None' },
  overlays: { es: 'Capas de apoyo', en: 'Supporting layers' },
  destinations: { es: 'Destinos del indicador', en: 'Indicator destinations' },
  networkLayer: { es: 'Red vial', en: 'Street network' },
  population: { es: 'Población (cuadrícula 100 m)', en: 'Population (100 m grid)' },
  boundaries: { es: 'Límites', en: 'Boundaries' },
  legend: { es: 'Leyenda', en: 'Legend' },
  noData: { es: 'Sin datos', en: 'No data' },
  byPopulation: { es: 'Proporción de población', en: 'Share of population' },
  difference: { es: 'Diferencia', en: 'Difference' },
  higherBetter: { es: 'Más alto es mejor', en: 'Higher is better' },
  linkViews: { es: 'Vincular vistas', en: 'Link views' },
  lowerBetter: { es: 'Más bajo es mejor', en: 'Lower is better' },
  matchScale: { es: 'Igualar escala', en: 'Match scale' },
  measureHint: {
    es: 'Clic para añadir puntos · Esc para cancelar',
    en: 'Click to add points · Esc to cancel',
  },
  measureTool: { es: 'Medir', en: 'Measure' },
  onlyShownAreas: {
    es: 'Sólo la cuadrícula y la región cubren toda el área de estudio; los resúmenes de otras escalas describen únicamente las áreas mostradas.',
    en: 'Only the grid and region layers cover the whole study area; summaries at other scales describe only the areas shown.',
  },
  undo: { es: 'Deshacer', en: 'Undo' },
  clear: { es: 'Limpiar', en: 'Clear' },
  done: { es: 'Listo', en: 'Done' },
  total: { es: 'Total', en: 'Total' },
  dictionary: { es: 'Diccionario de datos', en: 'Data dictionary' },
  search: { es: 'Buscar', en: 'Search' },
  download: { es: 'Descargar', en: 'Download' },
  exportImage: { es: 'Exportar imagen', en: 'Export image' },
  info: { es: 'Cómo leer este indicador', en: 'How to read this indicator' },
  close: { es: 'Cerrar', en: 'Close' },
  notAvailable: {
    es: 'Este indicador no está disponible en esta escala.',
    en: 'This indicator is not available at this scale.',
  },
  sources: { es: 'Fuentes', en: 'Sources' },
  baseData: { es: 'Datos base', en: 'Base data' },
  uliMeasure: { es: 'Medida central ULI', en: 'ULI core measure' },
  facets: { es: 'Por tema', en: 'By theme' },
  uliView: { es: 'Por medida ULI', en: 'By ULI measure' },
  relation: { es: 'Relación', en: 'Relation' },
  loading: { es: 'Cargando…', en: 'Loading…' },

  // sidebar sections
  layers: { es: 'Capas', en: 'Layers' },
  settings: { es: 'Ajustes', en: 'Settings' },
  networkRetainsPrivate: {
    es: 'La red peatonal de esta región conserva deliberadamente las calles privadas y de acceso restringido, para incluir las vialidades internas del desarrollo Condesa y de los fraccionamientos cerrados de Mexicali.',
    en: 'This region’s pedestrian network deliberately retains private and gated streets, so the Condesa development’s internal roads and Mexicali’s gated communities are included.',
  },
  networkStandard: {
    es: 'Red peatonal estándar, excluyendo vías de acceso privado.',
    en: 'Standard pedestrian network, excluding private-access ways.',
  },
  ltsThresholds: {
    es: 'Nivel de estrés del tráfico (LTS) según infraestructura ciclista, jerarquía vial, límite de velocidad y tránsito diario asumido',
    en: 'Level of traffic stress (LTS) from cycling infrastructure, street class, speed limit and assumed daily traffic',
  },
  collapsePanel: {
    es: 'Ocultar los controles del indicador',
    en: 'Hide the indicator controls',
  },
  collapseFurther: {
    es: 'Ocultar el panel y dejar el mapa',
    en: 'Hide the panel and leave the map',
  },
  expandPanel: { es: 'Mostrar el panel', en: 'Show the panel' },
  assumedPopulation: {
    es: 'La población de cada lote es un supuesto de {n} personas, la ocupación media por vivienda en Mexicali (INEGI, 2020); no es una cifra observada.',
    en: 'Each lot’s population is an assumed {n} persons, the Mexicali average dwelling occupancy (INEGI, 2020); it is not an observed figure.',
  },
  results: { es: 'Resultados por región', en: 'Results by region' },
  shareWithAccess: {
    es: 'Proporción de población con acceso dentro de cada distancia',
    en: 'Share of population with access within each distance',
  },
  acrossAreasShown: {
    es: 'Centro y dispersión de las áreas mostradas',
    en: 'Middle and spread across the areas shown',
  },
  mean: { es: 'Media', en: 'Mean' },
  meanHelp: {
    es: 'Promedio ponderado por población de las áreas mostradas.',
    en: 'Population-weighted average across the areas shown.',
  },
  median: { es: 'Mediana', en: 'Median' },
  medianHelp: {
    es: 'El valor central: la mitad de la población está por debajo y la mitad por encima.',
    en: 'The middle value: half the population is below it and half above.',
  },
  iqr: { es: 'RIC', en: 'IQR' },
  iqrHelp: {
    es: 'Rango intercuartílico (del percentil 25 al percentil 75; el 50% central). Mide qué tan dispersos están los valores, no dónde están.',
    en: 'Interquartile range (25th percentile to 75th percentile; the middle 50%). It measures how spread out the values are, not where they sit.',
  },
  log2Scale: {
    es: 'escala logarítmica: cada clase duplica la anterior',
    en: 'log scale: each class doubles the one before it',
  },
  meetsTarget: {
    es: '{v}% de la población alcanza la meta ({t})',
    en: '{v}% of the population meets the target ({t})',
  },
  cycling: { es: 'Ciclismo', en: 'Cycling' },
  walking: { es: 'Caminando', en: 'Walking' },
  styleSlow: {
    es: 'El mapa está tardando en cargar…',
    en: 'The map is taking a while to load…',
  },

  // themes, the primary grouping
  theme: { es: 'Tema', en: 'Theme' },
  byTheme: { es: 'Por tema', en: 'By theme' },

  // the composite index profile
  profileTitle: { es: 'Perfil del índice', en: 'Index profile' },
  profileIndex: { es: 'Índice', en: 'Index' },
  profileAll: {
    es: 'Mostrar el índice en el mapa', en: 'Show the index on the map',
  },
  profileArea: { es: 'Área seleccionada', en: 'Selected area' },
  profileClear: { es: 'Volver a la región', en: 'Back to the region' },
  profileReference: {
    es: 'Puntos por encima o por debajo de la referencia, el promedio en los puntos de muestra del área de estudio (0; una puntuación de 100 en los datos)',
    en: 'Points above or below the reference, the average over the study area’s sample points (0; a score of 100 in the data)',
  },
  profileSelf: {
    es: 'La región es su propia referencia, así que su perfil queda cerca de 0. Seleccione un área en el mapa o compare con otra región para ver las diferencias.',
    en: 'The region is its own reference, so its profile sits close to 0. Select an area on the map, or compare another region, to see the differences.',
  },
  profileHint: {
    es: 'Cada pétalo es un indicador, del color de su dominio; haga clic en uno para mapearlo, en un dominio para ver sus indicadores, o en un área del mapa para ver su perfil.',
    en: 'Each petal is an indicator, in its domain’s colour; click one to map it, a domain to list its indicators, or an area on the map to see its own profile.',
  },
  profileDomains: { es: 'Dominios', en: 'Domains' },
  profileIndicator: { es: 'indicador', en: 'indicator' },
  profileIndicators: { es: 'indicadores', en: 'indicators' },
  profileLens: { es: 'Enfoque de cada indicador', en: 'Each indicator’s lens' },
  profileLensHelp: {
    es: 'El enfoque es la forma en que el indicador analiza el lugar o aspecto que mide (p. ej., el acceso a la salud desde el enfoque de la proximidad).',
    en: 'A lens is the way an indicator analyses the place or aspect it measures (e.g. healthcare access through a proximity lens).',
  },
  lenses: { es: 'Enfoques', en: 'Lenses' },
  conceptualModel: { es: 'Modelo conceptual', en: 'Conceptual model' },
  modelOpen: { es: 'Abrir en tamaño completo', en: 'Open full size' },
  modelZoom: { es: 'Haga clic para acercar o alejar', en: 'Click to zoom in or out' },
  methodsScore: { es: 'puntuación', en: 'score' },
  profileMean: { es: 'Nivel medio', en: 'Mean level' },
  profilePenalty: {
    es: 'penalización por desequilibrio', en: 'imbalance penalty',
  },
  profilePenaltyHelp: {
    es: 'Cuanto más desiguales son los ámbitos, mayor es la penalización: un perfil equilibrado puntúa más que uno desigual con el mismo promedio.',
    en: 'The more uneven the domains, the larger the penalty: a balanced profile scores higher than an uneven one with the same average.',
  },
  profileComponents: { es: 'Componentes', en: 'Components' },
  profileThreshold: { es: 'umbral suave de {d}', en: 'soft threshold of {d}' },
  profileWeight: { es: 'peso', en: 'weight' },
  profileExcluded: {
    es: 'excluido: no varía', en: 'left out: does not vary',
  },

  // guided tour
  tour: { es: 'Recorrido', en: 'Tour' },
  back: { es: 'Atrás', en: 'Back' },
  next: { es: 'Siguiente', en: 'Next' },
  skip: { es: 'Cerrar', en: 'Skip' },

  // supporting layers — sentence-length labels, as the validation site had
  overlayChoropleth: {
    es: 'Coropleta del indicador', en: 'Indicator choropleth',
  },
  overlayChoroplethHelp: {
    es: 'El mapa de color del indicador. Apáguela para ver las capas debajo.',
    en: 'The indicator colour map. Turn it off to see the layers beneath.',
  },
  overlayDestinations: {
    es: 'Destinos que mide el indicador', en: 'Destinations being measured',
  },
  overlayDestinationsHelp: {
    es: 'Los puntos exactos a los que se midió el acceso para el indicador seleccionado.',
    en: 'The exact points access was measured to for the selected indicator.',
  },
  overlayNetwork: {
    es: 'Red vial (nivel de estrés)', en: 'Street network (traffic stress)',
  },
  overlayNetworkHelp: {
    es: 'Las calles por las que se calculan los recorridos, coloreadas por nivel de estrés del tráfico (LTS 1 a 4).',
    en: 'The streets routes are calculated over, coloured by level of traffic stress (LTS 1 to 4).',
  },
  overlayPopulation: {
    es: 'Población (cuadrícula 100 m)', en: 'Population (100 m grid)',
  },
  overlayPopulationHelp: {
    es: 'De dónde viene la ponderación por población. Apague la coropleta para verla.',
    en: 'Where the population weighting comes from. Turn the choropleth off to see it.',
  },
  overlayBoundaries: {
    es: 'Límite de la región', en: 'Region boundary',
  },
  overlayBoundariesHelp: {
    es: 'El contorno de la región mostrada en este panel.',
    en: 'The outline of the region this pane is showing.',
  },
  peoplePerCell: { es: 'personas por celda', en: 'people per cell' },

  // info panel
  whyItMatters: { es: '¿Por qué importa?', en: 'Why it matters' },
  whatCouldChange: {
    es: 'Intervenciones que podrían cambiar este indicador, del catálogo del taller.',
    en: 'Interventions that could change this indicator, from the workshop catalogue.',
  },
  impact: { es: 'Impacto', en: 'Impact' },
  areaKm2: { es: 'Área (km²)', en: 'Area (km²)' },
  populationEstimate: { es: 'Población estimada', en: 'Estimated population' },
};

// Vocabularies that arrive from the data in English.
const TERMS = {
  direct: { es: 'directa', en: 'direct' },
  proxy: { es: 'aproximada', en: 'proxy' },
  component: { es: 'componente', en: 'component' },
  complementary: { es: 'complementaria', en: 'complementary' },
  not_covered: { es: 'no cubierta', en: 'not covered' },
  percent: { es: 'porcentaje', en: 'percent' },
  metres: { es: 'metros', en: 'metres' },
  count: { es: 'conteo', en: 'count' },
  percentage: { es: 'porcentaje', en: 'percentage' },
  mean: { es: 'promedio', en: 'mean' },
  median: { es: 'mediana', en: 'median' },
  sum: { es: 'suma', en: 'sum' },
  higher_is_better: { es: 'más alto es mejor', en: 'higher is better' },
  lower_is_better: { es: 'más bajo es mejor', en: 'lower is better' },
  // without brackets of its own: the legend title puts the units in brackets
  'index (100 = reference)': {
    es: 'índice, 100 = referencia', en: 'index, 100 = reference',
  },
};

/**
 * The whole table, for build/make_text.mjs.
 *
 * Exported so that the editable data/<slug>/text.json can be regenerated with
 * every current string in it, rather than maintained by hand and drifting out
 * of step with what the interface actually shows.
 */
export function allStrings() {
  return S;
}

/**
 * Overlay the site's own wording onto the built-in strings.
 *
 * Applied once at boot from data/<slug>/text.json, so that any label on screen
 * can be revised for an audience without editing this file.
 */
export function applyOverrides(overrides) {
  for (const [key, value] of Object.entries(overrides || {})) {
    if (value && typeof value === 'object') {
      S[key] = { ...(S[key] || {}), ...value };
    }
  }
}

let lang = DEFAULT_LANG;

export function setLang(next) {
  lang = LANGS.includes(next) ? next : DEFAULT_LANG;
  return lang;
}

export function getLang() {
  return lang;
}

/** A UI string in the active language. */
export function t(key) {
  const entry = S[key];
  if (!entry) return key;
  return entry[lang] || entry.en || entry.es || key;
}

/** A data-supplied term, translated where a translation exists. */
export function term(value) {
  if (!value) return '';
  const entry = TERMS[value];
  return entry ? entry[lang] || entry.en : value;
}

/**
 * A label from the data.  Labels arrive as {es, en} maps (or a bare string);
 * a missing Spanish string falls back to English rather than to the key, so an
 * untranslated indicator still reads as itself.
 */
export function label(value, fallback = '') {
  if (!value) return fallback;
  if (typeof value === 'string') return value;
  return value[lang] || value.en || value.es || fallback;
}

/**
 * Append the units to a label, unless the label already names them.
 *
 * "Distancia media a la más cercana (m)" does not want "(metros)" after it.
 */
export function withUnits(text, units) {
  if (!units) return text;
  return /\([^)]*\)\s*$/.test(text) ? text : `${text} (${term(units)})`;
}

const locale = () => (lang === 'es' ? 'es-MX' : 'en-AU');

export function number(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return '–';
  return new Intl.NumberFormat(locale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function integer(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '–';
  return new Intl.NumberFormat(locale()).format(Math.round(value));
}
