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

  // a distance beyond the distance searched: measured, and not found within it
  censoredBeyond: { es: '> {d}', en: '> {d}' },
  censoredNote: {
    es: '> {d}: ningún destino a menos de {d}; el acceso sólo se evaluó hasta {d}',
    en: '> {d}: none within {d}; access was only evaluated up to {d}',
  },

  // a regular grid drawn as a smooth surface (js/smooth.js)
  smooth: { es: 'Suavizar', en: 'Smooth' },
  smoothHelp: {
    es: 'Dibuja la cuadrícula como una superficie continua: los valores de las celdas vecinas se suavizan y se colorean con las mismas clases de la leyenda.',
    en: 'Draws the grid as a continuous surface: neighbouring cells’ values are smoothed, and coloured by the same classes as the legend.',
  },
  smoothGridOnly: {
    es: 'Sólo para la cuadrícula de 100 m: las demás escalas no son una cuadrícula regular.',
    en: 'Only for the 100 m grid: the other scales are not a regular grid.',
  },

  // the composite index profile
  profileTitle: { es: 'Perfil del índice', en: 'Index profile' },
  profileIndex: { es: 'Índice', en: 'Index' },
  profileAll: {
    es: 'Mostrar el índice en el mapa', en: 'Show the index on the map',
  },
  profileArea: { es: 'Área seleccionada', en: 'Selected area' },
  profileClear: { es: 'Volver a la región', en: 'Back to the region' },
  profileIndexWhole: { es: 'Índice (todos los dominios)', en: 'Index (all domains)' },
  profileReference: {
    es: 'Puntos por encima o por debajo de la referencia (0): el promedio de cada indicador en los puntos de muestra de la región de estudio. El valor de una celda de la cuadrícula es el promedio de sus puntos; el de un área mayor o una región, el promedio ponderado por población',
    en: 'Points above or below the reference (0): each indicator’s average over the study region’s sample points. A grid cell’s value is the average of its points; a larger area’s or a region’s, the population-weighted average',
  },
  profileSelf: {
    es: 'La región es su propia referencia, así que su perfil queda cerca de 0. Seleccione un área en el mapa o compare con otra región para ver las diferencias.',
    en: 'The region is its own reference, so its profile sits close to 0. Select an area on the map, or compare another region, to see the differences.',
  },
  profileHint: {
    es: 'Cada pétalo es un indicador, del color de su puntuación; los anillos de color debajo marcan los dominios a los que cuenta (pase el cursor para ver su valor). Haga clic en un pétalo para mapearlo, en un dominio para ver sus indicadores, o en un área del mapa para ver su perfil.',
    en: 'Each petal is an indicator, coloured by its score; the coloured rings beneath mark the domains it counts towards (hover to see its value). Click a petal to map it, a domain to list its indicators, or an area on the map to see its own profile.',
  },
  profileCountsTowards: { es: 'cuenta para', en: 'counts towards' },
  profileEffective: {
    es: 'peso efectivo en el índice', en: 'effective weight in the index',
  },
  profileShare: {
    es: 'Un indicador que atañe a varios dominios cuenta en cada uno con una parte de su peso.',
    en: 'An indicator bearing on several domains counts a share of its weight in each.',
  },
  profileUnscored: {
    es: 'aún sin indicadores', en: 'no indicators yet',
  },
  profileDomains: { es: 'Dominios', en: 'Domains' },
  profileByDomain: { es: 'Indicadores por dominio', en: 'Indicators by domain' },
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
  profileMean: { es: 'Nivel medio', en: 'Mean level' },
  profilePenalty: {
    es: 'penalización por desequilibrio', en: 'imbalance penalty',
  },
  profilePenaltyHelp: {
    es: 'Cuanto más desiguales son los dominios, mayor es la penalización: un perfil equilibrado puntúa más que uno desigual con el mismo promedio.',
    en: 'The more uneven the domains, the larger the penalty: a balanced profile scores higher than an uneven one with the same average.',
  },
  profileComponents: { es: 'Componentes', en: 'Components' },
  profileThreshold: { es: 'umbral suave de {d}', en: 'soft threshold of {d}' },
  profileWeight: { es: 'peso', en: 'weight' },
  profileExcluded: {
    es: 'excluido: no varía', en: 'left out: does not vary',
  },
  profileInactive: {
    es: 'no se cuenta con esta configuración',
    en: 'not counted with these settings',
  },

  // describing an item of the profile, in the conceptual model
  describeMethod: { es: 'Cómo se mide', en: 'How it is measured' },
  describeHint: {
    es: 'Haga clic en un dominio o un indicador del gráfico para ver cómo se mide y con qué datos.',
    en: 'Click a domain or an indicator on the chart to see how it is measured, and from what data.',
  },
  describeSoft: {
    es: 'La distancia se puntúa con un umbral suave de {d}: 0,5 a {d}, cerca de 1 bien dentro y cerca de 0 bien más allá.',
    en: 'The distance is scored with a soft threshold of {d}: 0.5 at {d}, close to 1 well within it and close to 0 well beyond it.',
  },
  describeWithin: { es: 'a', en: 'within' },
  describeBeyond: { es: 'más allá', en: 'beyond' },
  technicalReport: {
    es: 'Documento técnico: cómo se calcula el índice (PDF)',
    en: 'Technical report: how the index is calculated (PDF)',
  },
  describeSteps: {
    es: 'La distancia se puntúa por escalones: {steps}; {beyond} más allá.',
    en: 'The distance is scored in steps: {steps}; {beyond} beyond.',
  },
  describeHigher: { es: 'Más alto es mejor.', en: 'Higher is better.' },
  describeLower: { es: 'Más bajo es mejor.', en: 'Lower is better.' },
  describeGoalposts: {
    es: 'Se reescala con las metas {min} y {max}; la referencia, el promedio de la región de estudio ({ref}), puntúa {centre}.',
    en: 'Re-scaled against goalposts of {min} and {max}; the reference, the study region average ({ref}), scores {centre}.',
  },
  describeWalkVariant: {
    es: 'Por defecto se atenúa por el confort térmico diurno; puede elegirse sin atenuación, y entonces el confort térmico cuenta en el entorno medioambiental.',
    en: 'By default it is attenuated by daytime thermal comfort; it can be chosen without attenuation, and thermal comfort then counts in the ambient environment instead.',
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

  // the composite index's settings (the cog on the profile)
  uliSettings: { es: 'Configuración del índice', en: 'Index settings' },
  uliSettingsHelp: {
    es: 'La caminabilidad con o sin atenuación por confort térmico, las regiones lado a lado y la importancia relativa de cada dominio',
    en: 'Walkability with or without thermal comfort attenuation, the regions side by side, and the relative importance of each domain',
  },
  uliExploratory: { es: 'exploratorio', en: 'exploratory' },
  uliResetWeights: { es: 'Pesos iguales', en: 'Equal weights' },
  uliCustomWeights: { es: 'pesos personalizados', en: 'custom weights' },
  uliShowing: { es: 'Se muestra', en: 'Showing' },
  uliExact: { es: 'Puntuaciones publicadas', en: 'Published scores' },
  uliExactHelp: {
    es: 'Calculadas en cada punto de muestra y promediadas, como en el análisis.',
    en: 'Calculated at each sample point and averaged, as in the analysis.',
  },
  uliExploratoryHelp: {
    es: 'Con pesos personalizados, el índice se recalcula en el navegador a partir de las puntuaciones promedio de cada área: es una aproximación exploratoria, que no coincide exactamente con las puntuaciones publicadas.',
    en: 'With custom weights, the index is recalculated in the browser from each area’s average scores: an exploratory approximation, which does not exactly match the published scores.',
  },
  // walkability, attenuated by thermal comfort (the default) or not
  uliDefault: { es: 'Predeterminado', en: 'Default' },
  uliDefaultHelp: {
    es: 'El índice como se publica: la caminabilidad atenuada por el confort térmico diurno.',
    en: 'The index as published: walkability attenuated by daytime thermal comfort.',
  },
  uliWalkability: {
    es: 'Caminabilidad incluida en el índice', en: 'Walkability included in the index',
  },
  uliAttenuationInfo: {
    es: 'Qué hace la atenuación por confort térmico',
    en: 'What thermal comfort attenuation does',
  },
  uliAttenuationPlot: {
    es: 'La caminabilidad atenuada a medida que aumenta el calor diurno',
    en: 'Walkability attenuated as daytime heat increases',
  },
  uliAttenuationX: {
    es: 'Confort térmico diurno, UTCI medio (°C)',
    en: 'Daytime thermal comfort, mean UTCI (°C)',
  },
  uliAttenuationY: { es: 'Caminabilidad atenuada', en: 'Attenuated walkability' },
  // the regions side by side, and their distributions
  uliRegionsTitle: { es: 'Las regiones, lado a lado', en: 'The regions side by side' },
  uliRegionsIntro: {
    es: 'Cada región frente a la referencia, en la misma escala. Haga clic en el índice, un dominio o un indicador para comparar cómo se distribuyen los resultados de las regiones.',
    en: 'Each region against the reference, on one scale. Click the index, a domain or an indicator to compare how the regions’ results are distributed.',
  },
  uliDistributionMean: { es: 'media', en: 'mean' },
  uliDistributionAreas: { es: 'áreas', en: 'areas' },
  uliDistributionNote: {
    es: 'Histogramas suavizados de los resultados de {scale} en cada región, ponderados por la población que representa cada área (en Condesa, 3,2 personas por lote). La línea vertical de cada región marca su media.',
    en: 'Smoothed histograms of the {scale} results in each region, weighted by the population each area represents (in Condesa, 3.2 people per lot). Each region’s vertical line marks its mean.',
  },
  uliDistributionPoints: {
    es: 'En puntos respecto a la referencia (0, la línea punteada).',
    en: 'In points from the reference (0, the dashed line).',
  },
  uliDistributionPublished: {
    es: 'Con pesos personalizados se muestran las puntuaciones publicadas, con pesos iguales.',
    en: 'With custom weights, the published scores, with equal weights, are shown.',
  },
  uliDistributionMissing: {
    es: 'No se exportó la distribución de este resultado.',
    en: 'No distribution of this result was exported.',
  },
  uliWeightsTitle: { es: 'Importancia relativa', en: 'Relative importance' },
  uliWeightsIntro: {
    es: 'Por diseño, el índice premia un perfil equilibrado: todos los dominios pesan lo mismo. Aquí puede dar más o menos peso a lo que le importa. Esto expresa una preferencia personal, no la evidencia de salud pública, y las puntuaciones resultantes son exploratorias.',
    en: 'By design, the index rewards a balanced profile: every domain carries the same weight. Here you can give more or less weight to what matters to you. This expresses personal preference, not public health evidence, and the resulting scores are exploratory.',
  },
  uliWeightsIndicators: { es: 'Pesos de los indicadores', en: 'Indicator weights' },
  uliWeightExcluded: { es: 'excluido', en: 'excluded' },

  // the access chart, by distance band
  bandChartTitle: {
    es: 'Población con acceso, por distancia',
    en: 'Population with access, by distance',
  },
  bandChartHelp: {
    es: 'Porcentaje de la población con acceso dentro de cada distancia. La barra resaltada es la distancia del mapa; haga clic en otra para cambiarla.',
    en: 'Percentage of the population with access within each distance. The highlighted bar is the distance mapped; click another to change it.',
  },
  bandChartArea: { es: 'Área seleccionada', en: 'Selected area' },

  // the liveability report
  report: { es: 'Informe PDF', en: 'PDF report' },
  reportHelp: {
    es: 'Un informe de entornos vivibles con lo que se muestra, para guardar como PDF desde el diálogo de impresión',
    en: 'A liveability report of what is shown, to save as a PDF from the print dialogue',
  },
  reportTitle: { es: 'Informe de entornos vivibles', en: 'Liveability report' },
  reportGenerated: { es: 'Generado', en: 'Generated' },
  reportSubject: { es: 'Área del informe', en: 'Area reported' },
  reportIndex: { es: 'Índice', en: 'Index' },
  reportDomains: { es: 'Dominios e indicadores', en: 'Domains and indicators' },
  reportScore: { es: 'Puntos respecto a la referencia', en: 'Points from the reference' },
  reportMaps: { es: 'Mapa', en: 'Map' },
  reportMethods: { es: 'Método', en: 'Method' },
  reportSources: { es: 'Fuentes', en: 'Sources' },
  reportSettings: { es: 'Configuración del índice', en: 'Index settings' },
  reportPublished: {
    es: 'Índice publicado, con pesos iguales',
    en: 'Published index, with equal weights',
  },
  reportNoIndex: {
    es: 'Seleccione el índice de entornos vivibles para generar el informe.',
    en: 'Select the liveability index to produce the report.',
  },
  reportMapFailed: {
    es: 'El mapa no pudo incluirse (el mapa base no permite exportarlo); el resto del informe está completo.',
    en: 'The map could not be included (the basemap does not allow it to be exported); the rest of the report is complete.',
  },
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
  'points from the reference (0 = study region average)': {
    es: 'puntos respecto de la referencia (0 = promedio de la región de estudio)',
    en: 'points from the reference (0 = study region average)',
  },
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

// a true minus sign: a hyphen is too slight to read at legend sizes, and
// these are for display only
const minus = (text) => text.replace(/^-/, '−');

export function number(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return '–';
  return minus(new Intl.NumberFormat(locale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value));
}

export function integer(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '–';
  return minus(new Intl.NumberFormat(locale()).format(Math.round(value)));
}
