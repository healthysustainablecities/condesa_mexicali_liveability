// The indicator vocabulary, and the resolution of a selection to the physical
// columns that carry it.
//
// The cycling validation site rebuilt column names in JavaScript from hardcoded
// naming conventions (pctCol / avgCol and a fixed list of families).  That made
// the viewer a second, silent copy of the analysis code's naming rules, which
// drifted.  Here the exporter emits every column name it produced, and this
// module only ever looks names up.  Nothing below constructs a column name.

import { label } from './strings.js';

export const CONTINUOUS = 'continuous';

/**
 * Measures whose columns are keyed by network, then by distance band.
 *
 * All of a family's bands are resolved together, because the popup reads out
 * every one of them for the area under the pointer and the results table
 * compares all of them at region level. The *map*, though, is drawn from a
 * single one — the selected distance — because "percentage of the population
 * with access within 500 m" is a statement anybody can read, where "the closest
 * band at which at least half its sample points have access" is a method.
 */
const BANDED_MEASURES = new Set(['access', 'beyond']);

export class Vocabulary {
  constructor(data) {
    this.raw = data;
    this.families = data.families;
    this.byId = new Map(data.families.map((f) => [f.id, f]));
    this.domains = data.domains;
    this.networks = data.networks;
    this.measureMeta = data.measures;
    this.descriptions = data.descriptions;
    // colour classes and targets, both computed by the exporter: see
    // choropleth.js for why they are not derived here
    this.breaks = data.breaks || {};
    this.targets = data.targets || {};
  }

  /** The exported class definition for a resolved selection's column. */
  breaksFor(resolved) {
    return (resolved && this.breaks[resolved.column]) || null;
  }

  /** The target that column is measured against, if it has one. */
  targetFor(resolved) {
    return (resolved && this.targets[resolved.column]) || null;
  }

  family(id) {
    return this.byId.get(id);
  }

  description(column) {
    return this.descriptions[column] || null;
  }

  familiesInDomain(domain) {
    return this.families.filter((f) => f.domain === domain);
  }

  /**
   * Every column a family/measure/network/... combination would use.
   * Returns [] for a combination the region never produced.
   */
  columnsFor({ family, measure, network, distance, variable, group }) {
    const f = this.byId.get(family);
    const m = f && f.measures[measure];
    if (!m) return [];
    if (m.variables) {
      const entry = m.variables[variable];
      return entry ? [entry.walk] : [];
    }
    if (m.groups) {
      const byNetwork = m.groups[group];
      const bands = byNetwork && byNetwork[network || 'walk'];
      if (!bands) return [];
      return distance && bands[distance] ? [bands[distance]] : [];
    }
    const value = m.networks && m.networks[network];
    if (!value) return [];
    if (typeof value === 'string') return [value];
    // banded: every distance at once, ascending -- the choropleth colours by
    // the smallest band an area reaches, so it needs the whole ladder
    const keys = Object.keys(value).sort((a, b) => Number(a) - Number(b));
    if (BANDED_MEASURES.has(measure)) return keys.map((k) => value[k]);
    return distance && value[distance] ? [value[distance]] : [];
  }

  /** Options for each control, given what the region produced. */
  measuresOf(familyId) {
    const f = this.byId.get(familyId);
    return f ? Object.keys(f.measures) : [];
  }

  networksOf(familyId, measure) {
    const f = this.byId.get(familyId);
    const m = f && f.measures[measure];
    if (!m) return [];
    if (m.variables) return ['walk'];
    if (m.groups) {
      const first = Object.values(m.groups)[0] || {};
      return Object.keys(first);
    }
    return Object.keys(m.networks || {});
  }

  distancesOf(familyId, measure, network) {
    const f = this.byId.get(familyId);
    const m = f && f.measures[measure];
    if (!m || m.variables) return [];
    const value = m.groups
      ? (Object.values(m.groups)[0] || {})[network]
      : (m.networks || {})[network];
    if (!value || typeof value === 'string') return [];
    return Object.keys(value).sort((a, b) => Number(a) - Number(b));
  }

  variablesOf(familyId) {
    const m = (this.byId.get(familyId) || { measures: {} }).measures.value;
    return m && m.variables ? Object.keys(m.variables) : [];
  }

  groupsOf(familyId) {
    const m = (this.byId.get(familyId) || { measures: {} }).measures.count;
    return m && m.groups ? Object.keys(m.groups) : [];
  }

  /**
   * Resolve a selection into everything the map, legend and info panel need.
   * Returns null when the combination produced no columns.
   */
  resolve(selection) {
    const f = this.byId.get(selection.family);
    if (!f) return null;
    const m = f.measures[selection.measure];
    if (!m) return null;
    const columns = this.columnsFor(selection);
    if (!columns.length) return null;
    const banded = BANDED_MEASURES.has(selection.measure) && columns.length > 1;
    const distances = banded
      ? this.distancesOf(selection.family, selection.measure, selection.network)
      : [];
    const bands = distances.map(Number);
    // the band the map is drawn from: the selection's own, or the shortest,
    // which is the one a reader reaches for first
    const chosen = banded
      ? (distances.includes(String(selection.distance))
        ? String(selection.distance) : distances[0])
      : null;
    // a network may invert a measure's polarity: dismount dependence is an
    // access measure, but more of it is worse
    const direction =
      (m.network_direction || {})[selection.network] ||
      (m.variable_direction || {})[selection.variable] ||
      m.direction ||
      f.direction;
    const column = banded
      ? (m.networks[selection.network] || {})[chosen] : columns[0];
    const described = this.descriptions[column] || {};
    return {
      selection,
      family: f,
      measure: m,
      measureKey: selection.measure,
      kind: CONTINUOUS,
      direction,
      units: described.units || m.units || '',
      statistic: described.statistic || '',
      columns,
      bands,
      // the distance the map is showing, whatever the selection said
      distance: chosen || selection.distance || null,
      column,
      description: described.en || '',
      category: described.category || '',
      overlay: f.overlay || null,
      uli: f.uli || null,
      title: this.title(selection),
    };
  }

  /** A one-line description of the current selection, for headers and exports. */
  title(selection) {
    const f = this.byId.get(selection.family);
    if (!f) return '';
    const m = f.measures[selection.measure] || {};
    const parts = [label(f.label, f.id)];
    if (selection.variable) parts.push(this.variableLabel(selection.variable));
    if (selection.group) parts.push(selection.group.replace(/_/g, ' '));
    parts.push(label(m.label, selection.measure));
    const network = this.networks[selection.network];
    if (network && selection.network !== 'walk') {
      parts.push(label(network.label, selection.network));
    } else if (network) {
      parts.push(label(network.label, 'walk'));
    }
    if (selection.distance) parts.push(`${selection.distance} m`);
    return parts.join(' · ');
  }

  variableLabel(variable) {
    const described = this.descriptions[variable] || {};
    // a configured label wins over the dictionary's own sentence, which is
    // English only and often a full definition rather than a name
    if (described.label) return label(described.label, variable);
    return described.en || variable.replace(/_/g, ' ');
  }

  /**
   * Walk a selection to the nearest combination the given columns support.
   *
   * Ported from the validation site's autofix(): when a pane is switched to a
   * scale that lacks the shared indicator, the alternative to moving is showing
   * an empty map, and an empty map reads as "no access here" rather than "not
   * measured here".
   */
  coerce(selection, available) {
    const has = (sel) => {
      const columns = this.columnsFor(sel);
      return columns.length > 0 && columns.every((c) => available.has(c));
    };
    let sel = { ...selection };
    if (has(sel)) return sel;

    const candidates = [
      ...this.familiesInDomain((this.byId.get(sel.family) || {}).domain),
      ...this.families,
    ];
    for (const f of candidates) {
      for (const measure of Object.keys(f.measures)) {
        for (const network of this.networksOf(f.id, measure)) {
          const distances = this.distancesOf(f.id, measure, network);
          const variables = this.variablesOf(f.id);
          const groups = this.groupsOf(f.id);
          const trial = {
            ...sel,
            family: f.id,
            measure,
            network,
            distance: distances.length
              ? distances.includes(sel.distance)
                ? sel.distance
                : distances[0]
              : null,
            variable: variables.length
              ? variables.includes(sel.variable)
                ? sel.variable
                : variables[0]
              : null,
            group: groups.length
              ? groups.includes(sel.group)
                ? sel.group
                : groups[0]
              : null,
          };
          if (has(trial)) return trial;
        }
      }
    }
    return sel;
  }

  /** The first selection worth showing when the app opens. */
  firstSelection(available) {
    const preferred = ['denue_fresh_food', 'fresh_food_market', 'blue_space'];
    for (const id of preferred) {
      if (!this.byId.has(id)) continue;
      const sel = this.coerce(
        { family: id, measure: 'access', network: 'walk' },
        available,
      );
      if (this.columnsFor(sel).length) return sel;
    }
    const f = this.families[0];
    return this.coerce(
      { family: f.id, measure: Object.keys(f.measures)[0], network: 'walk' },
      available,
    );
  }
}
