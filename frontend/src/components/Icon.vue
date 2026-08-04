<template>
  <svg class="icon" viewBox="0 0 24 24" aria-hidden="true" v-html="pfad" />
</template>

<script setup>
import { computed } from 'vue'

/**
 * Schlichte Strichzeichnungen im selben Duktus wie die Striche der
 * Strichliste. Bewusst als Sprite im Code statt als Emojis: Emojis sehen
 * auf jedem Gerät anders aus und lassen sich nicht einfärben.
 *
 * Die Pfade sind fest im Code -- v-html ist hier unkritisch, es kommt
 * kein Benutzerinhalt hinein.
 */
const PFADE = {
  suche:      '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/>',
  dinge:      '<rect x="2.5" y="7.5" width="19" height="12" rx="2"/><path d="M9 7.5V5.5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M2.5 12.5h19"/><path d="M10 12.5v2h4v-2"/>',
  orte:       '<path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5 12 12l9-4.5"/><path d="M12 12v9"/>',
  getraenke:  '<path d="M6.5 6.5h11l-1.1 12.7a2 2 0 0 1-2 1.8H9.6a2 2 0 0 1-2-1.8z"/><path d="M7.3 12h9.4"/>',
  einkauf:    '<circle cx="10" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2.5 3.5h2.6l2.6 11.4h11.2l2.1-8.4H6.4"/>',
  notizen:    '<rect x="4.5" y="4" width="15" height="17" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1.2"/><path d="M8.5 11h7"/><path d="M8.5 15h4.5"/>',
  profil:     '<circle cx="12" cy="8.5" r="3.6"/><path d="M5 20.5a7 7 0 0 1 14 0"/>',
  plus:       '<path d="M12 6v12"/><path d="M6 12h12"/>',
  minus:      '<path d="M6 12h12"/>',
  mikro:      '<rect x="9.2" y="2.5" width="5.6" height="11" rx="2.8"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0"/><path d="M12 18v3.5"/>',
  zelt:       '<path d="M12 3.5 2.5 20.5h19z"/><path d="M12 3.5v17"/><path d="M9.4 20.5c0-3.2 1.1-5.4 2.6-5.4s2.6 2.2 2.6 5.4"/>',
  haus:       '<path d="M3.5 10.5 12 3.5l8.5 7"/><path d="M5.5 9.6V20.5h13V9.6"/><path d="M10 20.5V15h4v5.5"/>',
  material:   '<path d="M3 8.5 12 4l9 4.5-9 4.5z"/><path d="m3 13.5 9 4.5 9-4.5"/>',
  verbrauch:  '<circle cx="8" cy="8" r="1.7"/><circle cx="16" cy="8" r="1.7"/><circle cx="12" cy="12" r="1.7"/><circle cx="8" cy="16" r="1.7"/><circle cx="16" cy="16" r="1.7"/>',
  haken:      '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  anheften:   '<path d="M9 3.5h6l-.8 5.2 3.3 3.3H6.5l3.3-3.3z"/><path d="M12 12v8.5"/>',
  stift:      '<path d="M4.5 19.5h4L19 9a2.12 2.12 0 0 0-3-3L5.5 16.5z"/><path d="m14.5 7.5 3 3"/>',
  muell:      '<path d="M4 6.5h16"/><path d="M9 6.5V4.5h6v2"/><path d="M6 6.5 7 20a1.6 1.6 0 0 0 1.6 1.5h6.8A1.6 1.6 0 0 0 17 20l1-13.5"/><path d="M10.5 10.5v7"/><path d="M13.5 10.5v7"/>',
  kamera:     '<rect x="2.5" y="7" width="19" height="13" rx="2.5"/><path d="M8.5 7 10 4.5h4L15.5 7"/><circle cx="12" cy="13.5" r="3.6"/>',
  zurueck:    '<path d="M14.5 5 8 12l6.5 7"/>',
  weiter:     '<path d="M9.5 5 16 12l-6.5 7"/>',
  auf:        '<path d="M5 14.5 12 8l7 6.5"/>',
  ab:         '<path d="M5 9.5 12 16l7-6.5"/>',
  schliessen: '<path d="M6 6l12 12"/><path d="M18 6 6 18"/>',
  verwaltung: '<path d="M3.5 7h9"/><path d="M18.5 7h2"/><path d="M3.5 17h4"/><path d="M13.5 17h7"/><circle cx="15.5" cy="7" r="2.4"/><circle cx="10.5" cy="17" r="2.4"/>',
  abmelden:   '<path d="M9.5 4.5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h3.5"/><path d="M14 8.5 17.5 12 14 15.5"/><path d="M17.5 12H9"/>',
  pdf:        '<path d="M6 3.5h8L18.5 8v12.5H6z"/><path d="M14 3.5V8h4.5"/><path d="M9 13h6"/><path d="M9 16.5h4"/>',
  auffuellen: '<path d="M12 20V6"/><path d="M6.5 11.5 12 6l5.5 5.5"/><path d="M4.5 20h15"/>',
  speichern:  '<path d="M4.5 4.5h11l4 4v11h-15z"/><path d="M8.5 4.5v5h5.5v-5"/><rect x="8" y="13" width="8" height="6.5"/>',
  warten:     '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.2V12l3.2 2.2"/>',
  griff:      '<circle cx="9" cy="6" r="1.3"/><circle cx="15" cy="6" r="1.3"/><circle cx="9" cy="12" r="1.3"/><circle cx="15" cy="12" r="1.3"/><circle cx="9" cy="18" r="1.3"/><circle cx="15" cy="18" r="1.3"/>',

  // ── Lagerort-Typen ──
  bauwagen:   '<rect x="2.5" y="6.5" width="14" height="9" rx="1.5"/><path d="M16.5 9.5h3l2 3.5v2.5h-2"/><circle cx="7" cy="18" r="2.1"/><circle cx="16" cy="18" r="2.1"/>',
  schopf:     '<path d="M2.8 11 12 4.8 21.2 11"/><path d="M5 10.3V20h14v-9.7"/><path d="M9.5 20v-5.5h5V20"/>',
  regal:      '<rect x="4" y="3.5" width="16" height="17" rx="1.5"/><path d="M4 9.2h16"/><path d="M4 14.8h16"/>',
  fach:       '<rect x="3.5" y="7" width="17" height="10" rx="1.5"/><path d="M12 7v10"/>',
  boden:      '<rect x="3.5" y="9" width="17" height="6" rx="1.5"/>',
  schrank:    '<rect x="4.5" y="3" width="15" height="18" rx="1.5"/><path d="M12 3v18"/><path d="M9.6 11.5h-1.4"/><path d="M14.4 11.5h1.4"/>',
  umziehen:   '<path d="M9 4.5H5.5a1.5 1.5 0 0 0-1.5 1.5v12a1.5 1.5 0 0 0 1.5 1.5H9"/><path d="M14.5 8 19 12l-4.5 4"/><path d="M19 12H9"/>',

  wand:       '<rect x="3" y="5.5" width="18" height="13" rx="1"/><path d="M3 9.8h18"/><path d="M3 14.2h18"/><path d="M9 5.5v4.3"/><path d="M15 9.8v4.4"/><path d="M9 14.2v4.3"/>',
}

const props = defineProps({
  name: { type: String, required: true },
})

const pfad = computed(() => PFADE[props.name] || '')
</script>

<style scoped>
.icon {
  width: 1em;
  height: 1em;
  fill: none;
  stroke: currentColor;
  /* 1,7 war zu zart -- dünne Linien verschwinden bei Sonne als Erstes */
  stroke-width: 1.95;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
  /* verhindert, dass das Symbol die Zeilenhöhe verschiebt */
  vertical-align: -0.125em;
}
</style>
