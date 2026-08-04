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
      <div v-if="!items.length" class="empty">
        <Icon :name="suchModus ? 'suche' : 'dinge'" class="icon" />
        <div class="hinweis">
          {{ suchModus ? `Nichts gefunden für „${query}"` : 'Noch nichts aufgenommen' }}
        </div>
        <button v-if="!suchModus" class="btn btn-primary" style="margin-top:16px" @click="$router.push('/items/new')">
          <Icon name="plus" class="icon" />Ersten Gegenstand aufnehmen
        </button>
      </div>

      <template v-else>
        <div v-if="suchModus" class="section-label">
          {{ items.length }} {{ items.length === 1 ? 'Treffer' : 'Treffer' }}
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

const { mode } = useMode()

const items = ref([])
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
    } else {
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
