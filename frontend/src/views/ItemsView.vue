<template>
  <div class="page">
    <!-- Die Suche ist keine eigene Seite mehr, sondern der Filter dieser
         Liste: leer = alles, getippt = Treffer. -->
    <div class="suchzeile">
      <Icon name="suche" class="icon lupe" />
      <input
        ref="inputEl"
        v-model="query"
        type="search"
        placeholder="Werkzeug, Material …"
        autocomplete="off"
        autocorrect="off"
        @input="onInput"
      />
      <button v-if="query" class="leeren" @click="reset" aria-label="Suche zurücksetzen">
        <Icon name="schliessen" class="icon" />
      </button>
      <button
        v-else-if="speechSupported"
        class="sprechen"
        :class="{ hoert: listening }"
        @click="toggleVoice"
        :title="listening ? 'Aufnahme stoppen' : 'Spracheingabe'"
      >
        <Icon name="mikro" class="icon" />
      </button>
    </div>
    <div v-if="listening" class="hoert-hinweis">Sprich jetzt …</div>

    <!-- Kategorien nur beim Blättern, bei einer Suche wären sie doppelt -->
    <div v-if="!suchModus" class="filter-row">
      <button
        class="btn btn-sm"
        :class="activeCategory === null ? 'btn-primary' : 'btn-secondary'"
        @click="activeCategory = null; load()"
      >Alle</button>
      <button
        v-for="cat in categories"
        :key="cat"
        class="btn btn-sm"
        :class="activeCategory === cat ? 'btn-primary' : 'btn-secondary'"
        @click="activeCategory = cat; load()"
      >{{ cat }}</button>
    </div>

    <div v-if="loading" class="loading">{{ suchModus ? 'Suche läuft …' : 'Laden …' }}</div>

    <template v-else>
      <div v-if="!items.length && !orte.length" class="empty">
        <Icon :name="suchModus ? 'suche' : 'dinge'" class="icon" />
        <div class="hinweis">
          {{ suchModus ? `Nichts gefunden für „${query}"` : 'Noch nichts aufgenommen' }}
        </div>
        <button v-if="!suchModus" class="btn btn-primary" style="margin-top:16px" @click="$router.push('/items/new')">
          <Icon name="plus" class="icon" />Ersten Gegenstand aufnehmen
        </button>
      </div>

      <template v-else>
        <!-- Kisten zuerst: ganze Kisten werden ausgeliehen, und wer nach
             "Bastelkiste" sucht, meint meist die Kiste, nicht den Inhalt. -->
        <template v-if="orte.length">
          <div class="section-label">
            {{ orte.length }} {{ orte.length === 1 ? 'Lagerort' : 'Lagerorte' }}
          </div>
          <div class="ort-treffer">
            <button
              v-for="o in orte" :key="o.id"
              class="ort-karte"
              @click="ortOeffnen(o)"
            >
              <Icon :name="typIcon(o.type)" class="icon" />
              <span class="ort-text">
                <span class="ort-name">{{ o.name }}</span>
                <span v-if="o.breadcrumb" class="ort-pfad">{{ o.breadcrumb }}</span>
              </span>
              <span class="ort-anzahl">{{ o.item_count }}</span>
            </button>
          </div>
        </template>

        <div v-if="suchModus" class="section-label">
          {{ items.length }} {{ items.length === 1 ? 'Gegenstand' : 'Gegenstände' }}
        </div>
        <div class="polaroids">
          <Polaroid
            v-for="item in items"
            :key="item.id"
            :item="item"
            :breadcrumb="activeBreadcrumb(item)"
            :im-lager="mode !== 'jahr'"
            @oeffnen="$router.push('/items/' + item.id)"
          />
        </div>
      </template>
    </template>

    <button class="fab" @click="$router.push('/items/new')" aria-label="Gegenstand aufnehmen">
      <Icon name="plus" class="icon" />
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getItems, getCategories, searchAll } from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import Icon from '../components/Icon.vue'
import Polaroid from '../components/Polaroid.vue'
import { typIcon } from '../utils/orttypen.js'

const { mode } = useMode()

const items = ref([])
const orte = ref([])
const categories = ref([])
const activeCategory = ref(null)
const loading = ref(false)
const query = ref('')
const listening = ref(false)
const inputEl = ref(null)

const suchModus = computed(() => !!query.value.trim())
const speechSupported = !!(window.SpeechRecognition || window.webkitSpeechRecognition)

let debounceTimer = null
let recognition = null

async function load() {
  loading.value = true
  try {
    if (suchModus.value) {
      const daten = await searchAll(query.value.trim(), mode.value)
      items.value = daten.items || []
      orte.value = daten.orte || []
    } else {
      orte.value = []
      const params = { mode: mode.value }
      if (activeCategory.value) params.category = activeCategory.value
      items.value = await getItems(params)
    }
  } finally {
    loading.value = false
  }
}

function onInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 350)
}

function reset() {
  query.value = ''
  clearTimeout(debounceTimer)
  load()
}

function toggleVoice() {
  if (listening.value) {
    recognition?.stop()
    return
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return
  recognition = new SR()
  recognition.lang = 'de-DE'
  recognition.continuous = false
  recognition.interimResults = true
  recognition.onstart = () => { listening.value = true }
  recognition.onresult = (e) => {
    query.value = Array.from(e.results).map(r => r[0].transcript).join('')
    if (e.results[e.results.length - 1].isFinal) load()
  }
  recognition.onerror = () => { listening.value = false }
  recognition.onend = () => { listening.value = false }
  recognition.start()
}

/** Zeigt, was in dieser Kiste liegt -- als Suche nach dem Ortsnamen. */
function ortOeffnen(o) {
  query.value = o.name
  load()
}

function activeBreadcrumb(item) {
  return mode.value === 'jahr' ? item.breadcrumb_jahr : item.breadcrumb_lager
}

onMounted(async () => {
  categories.value = await getCategories()
  await load()
})
</script>

<style scoped>
/* Suchzeile: eine Linie auf dem Pergament, kein Kasten */
.suchzeile {
  display: flex; align-items: center; gap: 10px;
  border-bottom: 1.5px solid var(--linie-stark);
  padding: 4px 2px;
  margin-bottom: 12px;
}
.suchzeile input {
  flex: 1; min-width: 0;
  border: none; padding: 10px 0; min-height: 46px;
  background: transparent;
}
.suchzeile input:focus { outline: none; }
.lupe { font-size: 21px; color: var(--tinte-blass); flex-shrink: 0; }

.sprechen, .leeren {
  width: 38px; height: 38px; flex-shrink: 0;
  border: 1.5px solid var(--linie-stark);
  border-radius: 50%;
  background: transparent;
  color: var(--tinte);
  font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.leeren { border-style: none; color: var(--tinte-blass); }
.sprechen.hoert {
  background: var(--gebrannt); color: #f7e2c0;
  border-color: transparent;
  animation: pochen 1s infinite;
}
.hoert-hinweis {
  font-family: var(--schrift-hand);
  font-size: 18px; color: var(--rot);
  text-align: center; margin-bottom: 10px;
}
@keyframes pochen { 0%, 100% { opacity: 1 } 50% { opacity: 0.55 } }

.filter-row { display: flex; gap: 7px; flex-wrap: wrap; margin-bottom: 6px; }

/* Gefundene Lagerorte: schlichte Zeilen, klar abgesetzt von den Abzügen */
.ort-treffer { display: flex; flex-direction: column; gap: 7px; }
.ort-karte {
  display: flex; align-items: center; gap: 11px;
  padding: 11px 13px; min-height: 54px; width: 100%;
  background: var(--blatt);
  border: none; border-radius: var(--radius-sm);
  box-shadow: var(--schatten);
  text-align: left; cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.ort-karte .icon { font-size: 22px; color: var(--gebrannt); flex-shrink: 0; }
.ort-text { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.ort-name { font-weight: 600; font-size: 16px; }
.ort-pfad {
  font-family: var(--schrift-hand); font-size: 14.5px;
  color: var(--tinte-blass); overflow-wrap: anywhere;
}
.ort-anzahl {
  font-family: var(--schrift-stempel); font-size: 11px;
  color: var(--tinte-blass); flex-shrink: 0;
  border: 1px solid var(--linie); border-radius: var(--radius-sm);
  padding: 3px 8px;
}

/* Pinnwand. auto-fill statt fester Spaltenzahl: auf dem Handy zwei, auf
   breiteren Geräten mehr, ohne dass die Abzüge riesig werden. */
.polaroids {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px 13px;
  margin-top: 12px;
  padding-top: 6px;
}
@media (max-width: 360px) {
  .polaroids { grid-template-columns: repeat(auto-fill, minmax(125px, 1fr)); gap: 16px 10px; }
}
</style>
