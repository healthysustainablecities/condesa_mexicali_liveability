// A guided tour of the dashboard.
//
// Hand-rolled rather than vendored, for one reason that matters: the steps
// **drive real state**. The tour does not describe the comparison view, it
// turns it on, picks the second region, and leaves it on at the end — which is
// the hand-over a workshop needs. A generic tour library can only point at
// things.
//
// The spotlight is a transparent, absolutely positioned element with a very
// large box-shadow, so the "hole" is just the element's own rectangle. No
// canvas, no SVG clip path, and it follows a resized or scrolled target.

import { getLang, t } from './strings.js';

const SEEN = 'dashboardTourSeen';
const PAD = 6;

/**
 * The steps.
 *
 * `element` is a selector to spotlight; omit it for a centred step. `before`
 * runs prior to showing the step and may change application state — that is
 * what makes this a demonstration rather than a description.
 */
function steps(app) {
  return [
    {
      title: { es: 'Explorador de indicadores', en: 'Indicator explorer' },
      text: {
        es: 'Este recorrido muestra cómo leer y comparar los indicadores de '
          + 'Mexicali y del Distrito Condesa. Puede volver a abrirlo cuando '
          + 'quiera con el botón <b>Recorrido</b>.',
        en: 'This tour shows how to read and compare the indicators for '
          + 'Mexicali and the Condesa district. Reopen it whenever you like '
          + 'with the <b>Tour</b> button.',
      },
    },
    {
      element: '#profile',
      title: {
        es: 'El Índice de entornos vivibles',
        en: 'The Urban Liveability Index',
      },
      text: {
        es: 'El explorador abre con el índice compuesto (provisional). Cada '
          + 'pétalo es un indicador, del color de su dominio: crece hacia '
          + 'fuera del anillo punteado (0, la referencia) donde el indicador '
          + 'supera su promedio, y hacia dentro donde queda por debajo. Haga '
          + 'clic en un pétalo para mapearlo, en un dominio para ver sus '
          + 'componentes, o en un área del mapa para ver su propio perfil. La '
          + 'franja inferior muestra por qué el índice no es un simple '
          + 'promedio: se resta una penalización cuando los dominios están '
          + 'desequilibrados. El engranaje de la esquina abre la configuración: '
          + 'la caminabilidad ajustada por el calor, y la importancia que usted '
          + 'da a cada dominio.',
        en: 'The explorer opens on the (provisional) composite index. Each '
          + 'petal is an indicator, in its domain’s colour: it grows outward '
          + 'from the dashed ring (0, the reference) where the indicator does '
          + 'better than its average, and inward where it falls short. Click '
          + 'a petal to map it, a domain to see its components, or an area on '
          + 'the map to see its own profile. The strip below shows why the '
          + 'index is not a simple average: a penalty is subtracted when the '
          + 'domains are out of balance. The cog in the corner opens the '
          + 'settings: walkability adjusted for heat, and the importance you '
          + 'give each domain.',
      },
      before: () => app.showFeatured(),
    },
    {
      element: '#showing',
      title: { es: 'Qué muestra el mapa', en: 'What the map shows' },
      text: {
        es: 'Siempre en lenguaje llano: el indicador, y qué significan los '
          + 'colores. El punto de color indica el tema del taller al que '
          + 'pertenece.',
        en: 'Always in plain language: the indicator, and what the colours '
          + 'mean. The coloured dot marks the workshop theme it belongs to.',
      },
    },
    {
      element: '#themeSel',
      title: { es: 'Empiece por el tema', en: 'Start with the theme' },
      text: {
        es: 'Los mismos temas que usan las tarjetas de intervención del '
          + 'taller. Cada indicador pertenece a uno.',
        en: 'The same themes the workshop intervention cards use. Every '
          + 'indicator belongs to one.',
      },
    },
    {
      element: '#measureSel',
      title: { es: 'Medida y red', en: 'Measure and network' },
      text: {
        es: '<b>Acceso (%)</b> colorea cada área por la banda de distancia '
          + 'más cercana que alcanza. <b>Distancia media</b> muestra un valor '
          + 'continuo. La <b>red</b> elige si el recorrido es caminando o en '
          + 'bicicleta, y con qué nivel de estrés del tráfico.',
        en: '<b>Access (%)</b> colours each area by the closest distance band '
          + 'it reaches. <b>Mean distance</b> shows a continuous value. The '
          + '<b>network</b> chooses whether the route is walked or cycled, and '
          + 'at what level of traffic stress.',
      },
    },
    {
      element: '.pane[data-pane="0"] .scaleSel',
      title: { es: 'La escala cambia la respuesta', en: 'Scale changes the answer' },
      text: {
        es: 'Manzanas, AGEB, lotes, cuadrícula: no cubren el mismo terreno. '
          + 'Sólo la cuadrícula y la región cubren toda el área de estudio, '
          + 'así que los resúmenes de otras escalas describen únicamente las '
          + 'áreas mostradas.',
        en: 'Manzanas, AGEBs, lots, grid: these do not cover the same ground. '
          + 'Only the grid and the region cover the whole study area, so '
          + 'summaries at other scales describe only the areas shown.',
      },
    },
    {
      element: '#settingsBtn',
      title: { es: 'Ajustes y capas', en: 'Settings and layers' },
      text: {
        es: 'El engrane abre las <b>capas</b>, el <b>mapa base</b> y cómo se '
          + 'relacionan las dos vistas. Las capas se aplican a ambos paneles: '
          + 'los <b>destinos</b> son exactamente los puntos que midió el '
          + 'indicador — pase el cursor sobre uno. Apague la <b>coropleta</b> '
          + 'para ver debajo la población.',
        en: 'The cog opens <b>layers</b>, the <b>basemap</b>, and how the two '
          + 'views relate. Layers apply to both panes: the <b>destinations</b> '
          + 'are exactly the points the indicator measured — hover one. Turn '
          + 'the <b>choropleth</b> off to see the population beneath it.',
      },
      before: () => app.setOverlay(0, 'destinations', true),
    },
    {
      element: '#legend',
      title: { es: 'La leyenda es un filtro', en: 'The legend is a filter' },
      text: {
        es: 'Haga clic en una banda de color para aislarla en el mapa; el '
          + 'resto se atenúa y el histograma la resalta. Clic de nuevo para '
          + 'volver.',
        en: 'Click a colour band to isolate it on the map; everything else '
          + 'dims and the histogram highlights it. Click again to restore.',
      },
    },
    {
      element: '#compareBtn',
      title: { es: 'Comparar dos regiones', en: 'Compare two regions' },
      text: {
        es: 'Se abre un segundo panel. El indicador es compartido, de modo '
          + 'que ambos lados responden la misma pregunta con la misma escala '
          + 'de color; la región y la escala se eligen por panel.',
        en: 'A second pane opens. The indicator is shared, so both sides '
          + 'answer the same question on the same colour scale; region and '
          + 'scale are chosen per pane.',
      },
      // the point of the tour: turn comparison on and leave it on
      before: () => app.setCompare(true),
    },
    {
      element: '#results',
      title: { es: 'La tabla de resultados', en: 'The results table' },
      text: {
        es: 'Una fila por región, una columna por banda de distancia, y la '
          + 'diferencia entre ambas al pie — en puntos porcentuales para los '
          + 'porcentajes, en metros para las distancias.',
        en: 'A row per region, a column per distance band, and the difference '
          + 'between them at the foot — in percentage points for percentages, '
          + 'in metres for distances.',
      },
    },
    {
      element: '#showing',
      title: { es: '¿Por qué importa?', en: 'Why it matters' },
      text: {
        es: 'El botón <b>i</b>, junto al nombre del indicador, explica cómo se '
          + 'calcula, de qué fuentes proviene y —cuando el catálogo del taller '
          + 'lo registra— qué intervenciones podrían cambiarlo.',
        en: 'The <b>i</b> beside the indicator name explains how it is '
          + 'calculated, which sources it came from and — where the workshop '
          + 'catalogue records one — what could change it.',
      },
    },
    {
      element: '#exportBtn',
      title: { es: 'Llevarse el mapa', en: 'Taking the map with you' },
      text: {
        es: '<b>Exportar imagen</b> descarga la vista con su leyenda, escala '
          + 'y fuentes. <b>Diccionario</b> define cada variable. <b>Medir</b> '
          + 'da una regla sobre el mapa. La dirección del navegador guarda la '
          + 'vista exacta: cópiela para compartirla.',
        en: '<b>Export image</b> downloads the view with its legend, scale bar '
          + 'and sources. <b>Dictionary</b> defines every variable. '
          + '<b>Measure</b> gives a ruler. The browser address holds the exact '
          + 'view: copy it to share.',
      },
    },
  ];
}

export class Tour {
  constructor(app) {
    this.app = app;
    this.layer = document.getElementById('tourLayer');
    this.pop = document.getElementById('tourPop');
    this.index = 0;
    this.steps = [];
    this.spot = document.createElement('div');
    this.spot.id = 'tourSpot';
    this.wire();
  }

  wire() {
    document.getElementById('tourNext')
      .addEventListener('click', () => this.go(this.index + 1));
    document.getElementById('tourPrev')
      .addEventListener('click', () => this.go(this.index - 1));
    document.getElementById('tourSkip')
      .addEventListener('click', () => this.stop());
    document.getElementById('tourMask')
      .addEventListener('click', () => this.stop());
    window.addEventListener('keydown', (event) => {
      if (this.layer.hidden) return;
      if (event.key === 'Escape') this.stop();
      if (event.key === 'ArrowRight') this.go(this.index + 1);
      if (event.key === 'ArrowLeft') this.go(this.index - 1);
    });
  }

  start() {
    this.steps = steps(this.app);
    this.layer.hidden = false;
    this.layer.appendChild(this.spot);
    this.go(0);
  }

  stop() {
    this.layer.hidden = true;
    this.spot.remove();
    localStorage.setItem(SEEN, '1');
  }

  /** Run once on a first visit, and never again unless asked. */
  offerOnFirstVisit() {
    if (localStorage.getItem(SEEN)) return;
    setTimeout(() => this.start(), 900);
  }

  async go(index) {
    if (index < 0) return;
    if (index >= this.steps.length) {
      this.stop();
      return;
    }
    this.index = index;
    const step = this.steps[index];
    if (step.before) await step.before();
    // the state change may have added or moved the element being pointed at.
    // Timed out as well as frame-based: a hidden tab never paints, and the tour
    // must not be able to stall there.
    await new Promise((resolve) => {
      let settled = false;
      const finish = () => { if (!settled) { settled = true; resolve(); } };
      requestAnimationFrame(finish);
      setTimeout(finish, 120);
    });

    const lang = getLang();
    document.getElementById('tourTitle').innerHTML =
      step.title[lang] || step.title.en;
    document.getElementById('tourText').innerHTML =
      step.text[lang] || step.text.en;
    document.getElementById('tourStep').textContent =
      `${index + 1} / ${this.steps.length}`;
    document.getElementById('tourPrev').textContent = t('back');
    document.getElementById('tourPrev').hidden = index === 0;
    document.getElementById('tourSkip').textContent = t('skip');
    document.getElementById('tourNext').textContent =
      index === this.steps.length - 1 ? t('done') : t('next');

    this.place(step.element ? document.querySelector(step.element) : null);
  }

  /** Put the spotlight over the target and the popover beside it. */
  place(target) {
    const pop = this.pop;
    if (!target || target.hidden || !target.getBoundingClientRect().width) {
      this.spot.style.display = 'none';
      pop.style.left = `${(window.innerWidth - pop.offsetWidth) / 2}px`;
      pop.style.top = `${(window.innerHeight - pop.offsetHeight) / 2}px`;
      return;
    }
    const box = target.getBoundingClientRect();
    this.spot.style.display = 'block';
    this.spot.style.left = `${box.left - PAD}px`;
    this.spot.style.top = `${box.top - PAD}px`;
    this.spot.style.width = `${box.width + PAD * 2}px`;
    this.spot.style.height = `${box.height + PAD * 2}px`;

    // prefer the right of the target, then below, then wherever it fits
    const width = pop.offsetWidth || 320;
    const height = pop.offsetHeight || 160;
    let left = box.right + 16;
    let top = box.top;
    if (left + width > window.innerWidth - 8) {
      left = Math.max(8, box.left);
      top = box.bottom + 16;
    }
    if (top + height > window.innerHeight - 8) {
      top = Math.max(8, box.top - height - 16);
    }
    pop.style.left = `${Math.min(left, window.innerWidth - width - 8)}px`;
    pop.style.top = `${Math.max(8, top)}px`;
  }
}
