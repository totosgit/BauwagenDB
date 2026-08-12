<template>
  <div class="wizard">

    <!-- Ausgewählter Pfad -->
    <div v-if="path.length || isDone" class="wizard-path">
      <button class="path-chip" @click="reset" aria-label="Von vorne"><Icon name="haus" class="icon" /></button>
      <template v-for="(loc, i) in path" :key="loc.id">
        <span class="path-sep">›</span>
        <button class="path-chip" @click="goTo(i)">{{ loc.name }}</button>
      </template>
      <template v-if="isDone && finalName">
        <span class="path-sep">›</span>
        <span class="path-chip path-chip-done">{{ finalName }}</span>
      </template>
    </div>

    <!-- Fertig-Ansicht -->
    <div v-if="isDone" class="wizard-done">
      <div class="wizard-done-label">{{ zweck === 'ziel' ? 'Neuer Platz' : 'Lagerort' }}</div>
      <div class="wizard-done-value">{{ breadcrumb }}</div>
      <button class="btn btn-secondary btn-sm" style="margin-top:10px" @click="reset">Ändern</button>
    </div>

    <!-- Aktuelle Frage -->
    <template v-else>
      <div class="wizard-question">{{ currentQuestion }}</div>

      <div v-if="noLocationsAtAll" class="wizard-empty">
        Noch keine Orte angelegt — bitte zuerst unter "Orte" Standorte anlegen.
      </div>

      <div v-else-if="!currentOptions.length && !hierAblegbar" class="wizard-empty">
        Kein passender Unterbereich vorhanden. Bitte erst unter "Orte" anlegen.
      </div>

      <div v-else-if="hierAblegbar || currentOptions.length">
        <!-- "Direkt auf dem Boden" Option -->
        <button v-if="canPickDirect" class="wizard-opt wizard-opt-direct" @click="pickDirect">
          <Icon name="haken" class="icon" />Direkt auf dem Boden (ohne Kiste)
        </button>

        <!-- Beim Verschieben: diese Ebene selbst nehmen -->
        <button v-if="hierAblegbar" class="wizard-opt wizard-opt-direct" @click="hierAblegen">
          <Icon name="haken" class="icon" />
          {{ currentParent ? `Hierher: ${currentParent.name}` : 'Auf die oberste Ebene' }}
        </button>

        <!-- Gruppierte Ansicht (Kinder eines Gebäudes) -->
        <template v-if="showGrouped">
          <div v-for="group in groupedOptions" :key="group.type" class="wizard-group">
            <div class="wizard-group-label">{{ group.label }}</div>
            <div class="wizard-opts">
              <button
                v-for="opt in group.options"
                :key="opt.id"
                class="wizard-opt"
                @click="pick(opt)"
              >
                <span class="opt-icon"><Icon :name="typIcon(opt.type)" class="icon" /></span>
                <span class="opt-name">{{ opt.name }}</span>
                <Icon v-if="childCount(opt.id)" name="weiter" class="icon opt-arrow" />
              </button>
            </div>
          </div>
        </template>

        <!-- Flache Ansicht -->
        <div v-else class="wizard-opts">
          <button
            v-for="opt in currentOptions"
            :key="opt.id"
            class="wizard-opt"
            @click="pick(opt)"
          >
            <span class="opt-icon"><Icon :name="typIcon(opt.type)" class="icon" /></span>
            <span class="opt-name">{{ opt.name }}</span>
            <Icon v-if="childCount(opt.id)" name="weiter" class="icon opt-arrow" />
          </button>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Icon from './Icon.vue'
import { typIcon } from '../utils/orttypen.js'

const props = defineProps({
  modelValue: { type: Number, default: null },
  locations: { type: Array, default: () => [] },
  /**
   * "gegenstand" = wohin gehoert ein Ding (Standard).
   * "ziel"       = wohin gehoert ein ganzer Lagerort. Dann sind auch
   *                Zwischenebenen waehlbar, nicht nur Kisten und Waende.
   */
  zweck: { type: String, default: 'gegenstand' },
  /** Diese Orte sind nicht waehlbar (der Ort selbst und alles darunter). */
  gesperrt: { type: Array, default: () => [] },
  /** Nur diese Typen sind ein gueltiges Ziel. Leer = alle. */
  erlaubteTypen: { type: Array, default: () => [] },
  /** Im Jahr-Baum navigieren (parent_jahr_id statt parent_id). */
  jahrBaum: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])


const GROUP_LABELS = {
  regal: 'Regale', schrank: 'Schränke', kiste: 'Kisten', wand: 'Wände', sonstiges: 'Sonstiges',
}

// Leaf-Typen: Items landen direkt hier, kein weiteres Navigieren
const LEAF_TYPES = new Set(['kiste', 'wand'])

const path = ref([])       // Navigation-Pfad (ohne das finale Element)
const isDone = ref(false)
const finalName = ref('')

// Kinder eines Location-Knotens. Im Jahr-Baum zaehlt parent_jahr_id, wo
// gesetzt -- eine Kiste kann dort woanders haengen.
function elternVon(l) {
  return props.jahrBaum && l.parent_jahr_id ? l.parent_jahr_id : l.parent_id
}
function getChildren(parentId) {
  return props.locations
    .filter(l => elternVon(l) === parentId)
    .filter(l => !props.gesperrt.includes(l.id))
}
function childCount(id) {
  return getChildren(id).length
}

const currentParent = computed(() => path.value.at(-1) ?? null)
const currentParentType = computed(() => currentParent.value?.type ?? null)
const currentParentId = computed(() => currentParent.value?.id ?? null)
const currentOptions = computed(() => getChildren(currentParentId.value))

// Auf einem Boden kann direkt (ohne Kiste) platziert werden
const canPickDirect = computed(
  () => props.zweck === 'gegenstand' && currentParentType.value === 'boden'
)

/** Darf die aktuelle Ebene selbst gewaehlt werden? Beim Verschieben eines
    Ortes ja -- eine Kiste kommt auf einen Boden, nicht in eine andere Kiste. */
const hierAblegbar = computed(() => {
  if (props.zweck !== 'ziel') return false
  const typ = currentParentType.value
  if (typ === null) return props.erlaubteTypen.includes('__root__')
  return props.erlaubteTypen.length === 0 || props.erlaubteTypen.includes(typ)
})

// Kinder eines Gebäudes werden nach Typ gruppiert
const showGrouped = computed(() =>
  ['bauwagen', 'schopf', 'sonstiges'].includes(currentParentType.value)
)

const groupedOptions = computed(() => {
  if (!showGrouped.value) return []
  const map = new Map()
  for (const opt of currentOptions.value) {
    if (!map.has(opt.type)) map.set(opt.type, [])
    map.get(opt.type).push(opt)
  }
  return [...map.entries()].map(([type, options]) => ({
    type,
    label: GROUP_LABELS[type] || type,
    options,
  }))
})

const noLocationsAtAll = computed(() =>
  props.locations.length === 0
)

const currentQuestion = computed(() => {
  switch (currentParentType.value) {
    case null:        return props.zweck === 'ziel'
                        ? 'Wohin soll der Ort?'
                        : 'Wo befindet sich das Objekt?'
    case 'bauwagen':  return 'Wie ist es im Bauwagen gelagert?'
    case 'schopf':    return 'Wie ist es im Schopf gelagert?'
    case 'sonstiges': return 'Wie ist es dort gelagert?'
    case 'regal':     return 'In welchem Fach?'
    case 'fach':      return 'Auf welchem Boden?'
    case 'schrank':   return 'Auf welchem Boden?'
    case 'boden':     return 'In einer Kiste oder direkt auf dem Boden?'
    default:          return 'Auswählen:'
  }
})

const breadcrumb = computed(() => {
  const parts = path.value.map(l => l.name)
  if (finalName.value) parts.push(finalName.value)
  return parts.join(' › ')
})

function pick(loc) {
  const children = getChildren(loc.id)
  const isLeaf = LEAF_TYPES.has(loc.type)

  if (props.zweck === 'ziel') {
    // Beim Verschieben immer erst hineinnavigieren, wenn es weitergeht --
    // gewaehlt wird ueber "Hierher", nicht durch bloßes Antippen.
    if (children.length) {
      path.value = [...path.value, loc]
    } else if (props.erlaubteTypen.length === 0 || props.erlaubteTypen.includes(loc.type)) {
      finalize(loc)
    }
    return
  }

  if (isLeaf || children.length === 0) {
    // Blatt oder kein weiterer Unterbereich → direkt auswählen
    finalize(loc)
  } else {
    // Tiefer navigieren
    path.value = [...path.value, loc]
  }
}

/** Beim Verschieben: die Ebene nehmen, in der man gerade steht. */
function hierAblegen() {
  const hier = currentParent.value
  if (!hier) {
    finalName.value = ''
    isDone.value = true
    emit('update:modelValue', 0)      // 0 = oberste Ebene
    return
  }
  finalize(hier)
}

function pickDirect() {
  // Boden direkt auswählen (ohne Kiste)
  finalize(currentParent.value)
}

function finalize(loc) {
  finalName.value = loc.name
  isDone.value = true
  emit('update:modelValue', loc.id)
}

function goTo(index) {
  path.value = path.value.slice(0, index + 1)
  isDone.value = false
  finalName.value = ''
  emit('update:modelValue', null)
}

function reset() {
  path.value = []
  isDone.value = false
  finalName.value = ''
  emit('update:modelValue', null)
}

// Pfad rekonstruieren wenn ein Item bereits einen Lagerort hat (beim Bearbeiten)
watch(
  () => [props.modelValue, props.locations.length],
  ([newId]) => {
    if (!newId || isDone.value || props.locations.length === 0) return
    const chain = []
    let cur = props.locations.find(l => l.id === newId)
    while (cur) {
      chain.unshift(cur)
      cur = cur.parent_id ? props.locations.find(l => l.id === cur.parent_id) : null
    }
    if (chain.length) {
      path.value = chain.slice(0, -1)
      finalName.value = chain.at(-1).name
      isDone.value = true
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.wizard {
  background: var(--cream);
  border-radius: var(--radius);
  padding: 16px;
  border: 1.5px solid var(--border);
}

/* Breadcrumb-Pfad */
.wizard-path {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 14px;
}
.path-chip {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-muted);
  -webkit-tap-highlight-color: transparent;
  transition: all 0.12s;
}
.path-chip:active { opacity: 0.7; }
.path-chip-done {
  background: var(--green-pale);
  color: var(--green);
  border-color: var(--green);
  cursor: default;
}
.path-sep { color: var(--text-muted); font-size: 16px; }

/* Frage */
.wizard-question {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--text);
}

/* Gruppen */
.wizard-group { margin-bottom: 12px; }
.wizard-group-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

/* Optionen */
.wizard-opts {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.wizard-opt {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--border);
  background: var(--white);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  min-height: 54px;
  -webkit-tap-highlight-color: transparent;
  transition: border-color 0.12s, background 0.12s;
}
.wizard-opt:active { border-color: var(--green); background: var(--green-pale); transform: scale(0.97); }
.wizard-opt-direct {
  width: 100%;
  justify-content: center;
  border-color: var(--green);
  background: var(--green-pale);
  color: var(--green);
  margin-bottom: 6px;
}
.opt-icon { font-size: 22px; }
.opt-name { flex: 1; }
.opt-arrow { font-size: 16px; color: var(--text-muted); }

/* Fertig */
.wizard-done { text-align: center; padding: 8px 0; }
.wizard-done-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); }
.wizard-done-value { font-size: 18px; font-weight: 700; color: var(--green); margin-top: 4px; }

/* Leer */
.wizard-empty { font-size: 15px; color: var(--text-muted); padding: 12px 0; }
</style>
