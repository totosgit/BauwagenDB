/**
 * Symbol und Beschriftung je Lagerort-Typ.
 * Die erlaubte Verschachtelung legt das Backend fest (VALID_CHILDREN in
 * routers/locations.py) -- hier steht nur, wie ein Typ aussieht und heißt.
 */
const TYPEN = {
  bauwagen:  { icon: 'bauwagen', label: 'Bauwagen' },
  schopf:    { icon: 'schopf',   label: 'Schopf' },
  regal:     { icon: 'regal',    label: 'Regal' },
  schrank:   { icon: 'schrank',  label: 'Schrank' },
  fach:      { icon: 'fach',     label: 'Fach' },
  boden:     { icon: 'boden',    label: 'Boden' },
  kiste:     { icon: 'orte',     label: 'Kiste' },
  wand:      { icon: 'wand',     label: 'Wand' },
  sonstiges: { icon: 'orte',     label: 'Sonstiges' },
}

export function typIcon(typ) {
  return TYPEN[typ]?.icon || 'orte'
}

export function typLabel(typ) {
  return TYPEN[typ]?.label || typ
}
