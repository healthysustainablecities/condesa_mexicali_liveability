// The data dictionary viewer.
//
// The generate step already produces {codename}_data_dictionary.csv/.xlsx/.pdf
// for every region; the exporter copies them in.  This shows the CSV as a
// searchable table and offers all three for download, so the definitions travel
// with the map rather than living in a file somebody has to be sent.

import { getLang, label, t } from './strings.js';

/**
 * A real CSV parse, not a split on commas: the generated dictionary's
 * descriptions contain commas and quoted fields, and some wrap across lines.
 */
export function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 1; } else { quoted = false; }
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ',') {
      row.push(field); field = '';
    } else if (char === '\n') {
      row.push(field); field = '';
      if (row.length > 1 || row[0] !== '') rows.push(row);
      row = [];
    } else if (char !== '\r') {
      field += char;
    }
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  if (!rows.length) return [];
  const header = rows.shift().map((h) => h.trim());
  return rows.map((values) =>
    Object.fromEntries(header.map((key, i) => [key, (values[i] || '').trim()])));
}

export class Dictionary {
  constructor(panel) {
    this.panel = panel;
    this.rows = [];
    this.exposed = new Set();
    this.showAll = false;
  }

  async load(dataset) {
    const files = dataset.manifest.data_dictionary || {};
    this.files = files;
    this.slug = dataset.slug;
    if (!files.csv) {
      this.rows = [];
      return;
    }
    const response = await fetch(`data/${dataset.slug}/${files.csv}`);
    this.rows = parseCSV(await response.text());
  }

  /** The variables the dashboard actually offers, for the default filter. */
  setExposed(columns) {
    this.exposed = new Set(columns);
  }

  /**
   * The exporter's own descriptions, which carry Spanish.
   *
   * The region's generated dictionary is English only — translating its
   * thousand-odd sentences is not something to invent — but the columns this
   * dashboard exposes have a Spanish description composed from parts that were
   * already translated. Where one exists it wins; otherwise the English
   * definition stands, and the panel says so.
   */
  setDescriptions(descriptions) {
    this.descriptions = descriptions || {};
  }

  /** The row's indicator text in the active language. */
  describe(row) {
    const entry = this.descriptions[row.Variable];
    if (entry) {
      const translated = label(entry, '');
      if (translated) return translated;
    }
    return row.Indicator || '';
  }

  render(query = '') {
    const body = this.panel.querySelector('.dict-body');
    const needle = query.trim().toLowerCase();
    const rows = this.rows.filter((row) => {
      if (!this.showAll && !this.exposed.has(row.Variable)) return false;
      if (!needle) return true;
      return Object.values(row).some((value) =>
        String(value).toLowerCase().includes(needle));
    });
    const downloads = Object.entries(this.files || {}).map(([extension, file]) =>
      `<a class="btn small" href="data/${this.slug}/${file}" download>${
        t('download')} .${extension}</a>`).join(' ')
      // the CSV as shown, in the active language, built from what is on screen
      + ` <button class="btn small" id="dictCsv">${t('download')} .csv (${
        getLang()})</button>`;
    body.innerHTML = `
      <div class="dict-tools">
        <label><input type="checkbox" class="dict-all" ${
  this.showAll ? 'checked' : ''}> ${
  t('dictionary')} — ${this.rows.length}</label>
        <span class="dict-count">${rows.length}</span>
        ${downloads}
      </div>
      <div class="dict-scroll"><table class="dict-table">
        <thead><tr><th>Variable</th><th>${t('indicator')}</th>
          <th>${t('measure')}</th><th>${t('scale')}</th></tr></thead>
        <tbody>${rows.map((row) => `<tr>
          <td><code>${row.Variable || ''}</code></td>
          <td>${this.describe(row)}</td>
          <td>${[row.Units, row.Statistic].filter(Boolean).join(' · ')}</td>
          <td class="muted">${row.Scale || ''}</td>
        </tr>`).join('')}</tbody>
      </table></div>`;
    const all = body.querySelector('.dict-all');
    if (all) {
      all.addEventListener('change', () => {
        this.showAll = all.checked;
        this.render(query);
      });
    }
    const download = body.querySelector('#dictCsv');
    if (download) {
      download.addEventListener('click', () => this.downloadCSV(rows));
    }
  }

  /** Download exactly what is on screen, in the active language. */
  downloadCSV(rows) {
    const quote = (value) => `"${String(value == null ? '' : value).replace(/"/g, '""')}"`;
    const header = ['Variable', t('indicator'), 'Units', 'Statistic', 'Scale'];
    const lines = [header.map(quote).join(',')].concat(
      rows.map((row) => [
        row.Variable, this.describe(row), row.Units, row.Statistic, row.Scale,
      ].map(quote).join(',')),
    );
    // CRLF and a byte-order mark: between them they are what makes Excel open
    // a UTF-8 CSV with its accents intact rather than as mojibake
    const bom = String.fromCharCode(0xFEFF);
    const blob = new Blob(
      [bom + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' },
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${this.slug}_data_dictionary_${getLang()}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }
}
