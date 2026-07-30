<template>
  <div
    class="polaroid"
    :style="{ transform: `rotate(${winkel}deg)`, boxShadow: schatten }"
    @click="$emit('oeffnen')"
  >
    <span class="klebe" :class="klebeArt" aria-hidden="true" />

    <div class="fenster" :class="{ leer: !item.image_path }">
      <img v-if="item.image_path" :src="'/images/' + item.image_path" :alt="item.name" />
      <Icon v-else :name="categoryIcon(item.category)" class="icon" />
    </div>

    <span v-if="item.quantity" class="menge">{{ mengeKurz }}</span>

    <div class="rand" :style="{ transform: `rotate(${randWinkel}deg)` }">
      <div class="name">{{ item.name }}</div>
      <div class="ort" :class="{ fehlt: !ort }">{{ ort || 'noch kein Ort' }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'
import { categoryIcon } from '../utils/kategorien.js'

const props = defineProps({
  item: { type: Object, required: true },
  /** Voller Pfad; im Polaroid zeigen wir nur die letzten Stationen. */
  breadcrumb: { type: String, default: '' },
  /** Wie viele Pfadstationen ins Polaroid passen. */
  ortTiefe: { type: Number, default: 2 },
})

defineEmits(['oeffnen'])

/**
 * Winkel, Klebestreifen und Schatten sollen je Abzug verschieden sein,
 * aber beim Neuzeichnen gleich bleiben -- echter Zufall würde die Bilder
 * bei jeder Aktualisierung zappeln lassen. Deshalb ein kleiner Hash
 * über die ID.
 */
function streu(id, salz) {
  let x = ((Number(id) || 0) * 2654435761 + salz * 40503) >>> 0
  x = (x ^ (x >>> 15)) >>> 0
  return (x % 1000) / 1000
}

const winkel = computed(() => (-2.4 + streu(props.item.id, 1) * 4.8).toFixed(2))
const randWinkel = computed(() => (-0.7 + streu(props.item.id, 4) * 1.4).toFixed(2))
const klebeArt = computed(
  () => ['mitte', 'ecken', 'eine'][Math.floor(streu(props.item.id, 2) * 3)]
)
const schatten = computed(() => {
  const v = Math.floor(streu(props.item.id, 3) * 3)
  return [
    '3px 4px 10px rgba(48,26,8,.30)',
    '-2px 5px 11px rgba(48,26,8,.28)',
    '2px 4px 9px rgba(48,26,8,.32)',
  ][v]
})

/** Nur die letzten Stationen -- der volle Pfad sprengt die schmale Zeile. */
const ort = computed(() => {
  if (!props.breadcrumb) return ''
  const teile = props.breadcrumb.split('›').map(t => t.trim()).filter(Boolean)
  return teile.slice(-props.ortTiefe).join(' › ')
})

const mengeKurz = computed(() => {
  const m = props.item.quantity
  const zahl = Number.isInteger(m) ? m : Number(m).toFixed(1)
  // "Stück" ist zu lang für den Stempel
  const einheit = props.item.unit === 'Stück' ? 'Stk' : props.item.unit
  return `${zahl} ${einheit}`
})
</script>

<style scoped>
.polaroid {
  position: relative;
  background: var(--foto-papier);
  /* leicht ungleichmäßiges Papier statt reinweiß */
  background-image:
    radial-gradient(60% 40% at 15% 8%, rgba(255, 255, 248, 0.7), transparent 60%),
    radial-gradient(70% 50% at 85% 95%, rgba(210, 190, 155, 0.25), transparent 65%);
  padding: 8px 8px 0;
  border-radius: 1px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.polaroid:active { filter: brightness(0.97); }

/* Klebestreifen in drei Varianten */
.klebe { position: absolute; inset: 0; pointer-events: none; }
.klebe::before, .klebe::after {
  content: '';
  position: absolute;
  background: rgba(222, 196, 152, 0.66);
  box-shadow: 0 1px 2px rgba(48, 26, 8, 0.22), inset 0 0 0 1px rgba(255, 250, 235, 0.28);
}
.klebe.mitte::before {
  top: -7px; left: 50%; width: 52px; height: 15px;
  transform: translateX(-50%) rotate(-1.6deg);
}
.klebe.ecken::before {
  top: -8px; left: -9px; width: 40px; height: 14px; transform: rotate(-42deg);
}
.klebe.ecken::after {
  top: -8px; right: -9px; width: 40px; height: 14px; transform: rotate(42deg);
}
.klebe.eine::before {
  top: -8px; left: -10px; width: 42px; height: 14px; transform: rotate(-40deg);
}

.fenster {
  position: relative;
  aspect-ratio: 1;
  background: #e9e3d4;
  overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.fenster img { width: 100%; height: 100%; object-fit: cover; display: block; }
/* Alterung: warme Tönung und dunklere Ecken wie bei einem echten Abzug */
.fenster::after {
  content: '';
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(120% 120% at 50% 45%, transparent 55%, rgba(70, 48, 20, 0.2) 100%),
    linear-gradient(160deg, rgba(255, 238, 205, 0.13), transparent 55%);
  box-shadow: inset 0 0 0 1px rgba(53, 29, 8, 0.14);
}
/* Ohne Foto: gestempeltes Kategoriesymbol auf unbelichtetem Feld */
.fenster.leer {
  background:
    repeating-linear-gradient(45deg, rgba(53, 29, 8, 0.035) 0 6px, transparent 6px 12px),
    #e6dfcd;
  color: var(--tinte-blass);
}
.fenster.leer .icon { font-size: 44px; stroke-width: 1.6; }

/* Von Hand auf den Rand geschrieben */
.rand {
  padding: 9px 4px 12px;
  display: flex; flex-direction: column;
  min-height: 62px;
}
.name {
  font-family: var(--schrift-hand);
  font-size: 19px; line-height: 1.12;
  color: #2f2a20;
  overflow: hidden;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}
.ort {
  font-family: var(--schrift-hand);
  font-size: 15.5px; color: #6a6252;
  line-height: 1.15; margin-top: 2px;
  overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.ort.fehlt { color: var(--rot); }

/* Menge als kleiner Stempel in der Fotoecke */
.menge {
  position: absolute; top: 15px; right: 15px;
  background: rgba(247, 241, 226, 0.92);
  color: var(--tinte);
  font-family: var(--schrift-stempel);
  font-size: 10.5px; letter-spacing: 0.06em;
  padding: 3px 6px; border-radius: 1px;
  box-shadow: 0 1px 3px rgba(48, 26, 8, 0.26);
  font-variant-numeric: tabular-nums;
  transform: rotate(1.4deg);
}

/* Große Ausführung für die Detailansicht */
.polaroid.gross { padding: 11px 11px 0; cursor: default; }
.polaroid.gross .rand { padding: 12px 5px 15px; }
.polaroid.gross .name { font-size: 24px; -webkit-line-clamp: 3; }
.polaroid.gross .ort { font-size: 19px; white-space: normal; }
.polaroid.gross .menge { top: 19px; right: 19px; font-size: 12px; }

@media (max-width: 390px) {
  .name { font-size: 17.5px; }
  .ort { font-size: 14.5px; }
  .rand { padding: 8px 3px 10px; min-height: 56px; }
}
</style>
