// The workshop's themes, and the design tokens that go with them.
//
// Themes are the typology the workshop itself uses — its printed intervention
// cards are grouped and colour-coded by them — so they are the dashboard's
// primary grouping too. They arrive from the exporter, declared in the region
// config rather than derived from the analysis, which knows only its own
// English reporting domains.

import { label } from './strings.js';

export class Themes {
  constructor(indicators) {
    // a theme with no indicators is kept in the config so the vocabulary is
    // complete and documented, but there is nothing to navigate to, so it is
    // not offered (Vivienda is not a GHSCI output here)
    this.all = (indicators.themes || []).filter((t) => t.families.length);
    this.byId = new Map(this.all.map((t) => [t.id, t]));
    this.byFamily = new Map();
    for (const theme of this.all) {
      for (const family of theme.families) this.byFamily.set(family, theme);
    }
    this.interventions = indicators.interventions || [];
  }

  get(id) {
    return this.byId.get(id) || null;
  }

  /** The theme an indicator belongs to, or null. */
  forFamily(familyId) {
    return this.byFamily.get(familyId) || null;
  }

  /**
   * Interventions that could move indicators in a theme.
   *
   * `themes` is a *mapping* of theme id to the impacts the source sheet states
   * for that pairing, not a list of ids: an intervention tagged to a theme with
   * nothing said about what it would do there is not offered. Reading it as a
   * list threw, which left the whole info panel empty.
   */
  interventionsFor(themeId) {
    if (!themeId) return [];
    return this.interventions.filter(
      (i) => ((i.themes || {})[themeId] || []).length,
    );
  }

  options(lang) {
    return this.all.map((t) => [t.id, label(t.label, t.id)]);
  }
}

/**
 * Apply the region's design tokens as CSS variables.
 *
 * The stylesheet defines every colour as a variable with a sensible default,
 * so a region that declares no `style:` block looks exactly as before. Only
 * the keys actually supplied are overridden.
 */
export function applyStyle(style) {
  if (!style) return;
  const root = document.documentElement;
  for (const [key, value] of Object.entries(style)) {
    if (typeof value === 'string' && value) {
      root.style.setProperty(`--${key}`, value);
    }
  }
}

/**
 * A readable text colour for a theme swatch.
 *
 * The palette runs from a very pale cream to a strong blue, so a fixed text
 * colour is illegible on one end or the other. Relative luminance decides.
 */
export function contrastInk(hex) {
  const value = String(hex || '').replace('#', '');
  if (value.length !== 6) return '#1b1b1b';
  const channel = (i) => {
    const c = parseInt(value.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  const luminance =
    0.2126 * channel(0) + 0.7152 * channel(2) + 0.0722 * channel(4);
  return luminance > 0.5 ? '#1b1b1b' : '#ffffff';
}
