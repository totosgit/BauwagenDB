/**
 * Welches Symbol steht für welche Kategorie.
 * Wird von Suche, Bestandsliste und Detailansicht gemeinsam benutzt --
 * vorher stand dieselbe Zuordnung dreimal im Code.
 */
const SYMBOLE = {
  'Werkzeug': 'dinge',
  'Material': 'material',
  'Verbrauchsmaterial': 'verbrauch',
  'Elektrik': 'verbrauch',
  'Sonstiges': 'orte',
}

export function categoryIcon(kategorie) {
  return SYMBOLE[kategorie] || 'orte'
}
