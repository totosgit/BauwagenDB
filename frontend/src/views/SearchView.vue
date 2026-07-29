<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Suche</h1>
    </div>

    <div class="suchzeile">
      <Icon name="suche" class="icon lupe" />
      <input
        ref="inputEl"
        v-model="query"
        type="search"
        placeholder="Werkzeug, Material, Ort …"
        autocomplete="off"
        autocorrect="off"
        @input="onInput"
      />
      <button
        v-if="speechSupported"
        class="sprechen"
        :class="{ hoert: listening }"
        @click="toggleVoice"
        :title="listening ? 'Aufnahme stoppen' : 'Spracheingabe'"
      >
        <Icon name="mikro" class="icon" />
      </button>
    </div>
    <div v-if="listening" class="hoert-hinweis">Sprich jetzt …</div>

    <div v-if="loading" class="loading">Suche läuft …</div>

    <template v-else-if="searched">
      <!-- Items -->
      <div v-if="results.items.length">
        <div class="section-label">Gegenstände ({{ results.items.length }})</div>
        <div
          v-for="item in results.items"
          :key="'i' + item.id"
          class="item-row"
          @click="$router.push('/items/' + item.id)"
        >
          <div class="item-thumb">
            <img v-if="item.image_path" :src="'/images/' + item.image_path" :alt="item.name" />
            <Icon v-else :name="categoryIcon(item.category)" class="icon" />
          </div>
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-meta">
              <span v-if="item.quantity" class="menge">{{ item.quantity }} {{ item.unit }}</span>
              <span v-if="activeBreadcrumb(item)" class="ort">{{ activeBreadcrumb(item) }}</span>
              <span v-if="item.aufgebaut && mode !== 'jahr'" class="tag">Aufgebaut</span>
            </div>
          </div>
          <span v-if="item.category" class="tag">{{ item.category }}</span>
        </div>
      </div>

      <!-- Locations -->
      <div v-if="results.locations.length">
        <div class="section-label">Lagerorte ({{ results.locations.length }})</div>
        <div
          v-for="loc in results.locations"
          :key="'l' + loc.id"
          class="item-row"
          @click="$router.push('/locations')"
        >
          <div class="item-thumb"><Icon name="orte" class="icon" /></div>
          <div class="item-info">
            <div class="item-name">{{ loc.name }}</div>
            <div class="item-meta">
              <span class="type-badge">{{ loc.type }}</span>
              <span v-if="loc.breadcrumb" class="ort">{{ loc.breadcrumb }}</span>
            </div>
          </div>
          <span class="tag">{{ loc.item_count }} Dinge</span>
        </div>
      </div>

      <div v-if="!results.items.length && !results.locations.length" class="empty">
        <Icon name="suche" class="icon" />
        <div class="hinweis">Nichts gefunden für „{{ query }}"</div>
      </div>
    </template>

    <div v-else class="empty" style="margin-top: 40px;">
      <Icon name="suche" class="icon" />
      <div class="hinweis">Tippe oder sprich einen Suchbegriff</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchAll } from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import Icon from '../components/Icon.vue'
import { categoryIcon } from '../utils/kategorien.js'

const { mode } = useMode()

const query = ref('')
const results = ref({ items: [], locations: [] })
const loading = ref(false)
const searched = ref(false)
const listening = ref(false)
const inputEl = ref(null)

const speechSupported = !!(window.SpeechRecognition || window.webkitSpeechRecognition)

let debounceTimer = null
let recognition = null

function onInput() {
  clearTimeout(debounceTimer)
  if (!query.value.trim()) { searched.value = false; return }
  debounceTimer = setTimeout(doSearch, 350)
}

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  try {
    results.value = await searchAll(query.value)
    searched.value = true
  } finally {
    loading.value = false
  }
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
    const transcript = Array.from(e.results).map(r => r[0].transcript).join('')
    query.value = transcript
    if (e.results[e.results.length - 1].isFinal) doSearch()
  }
  recognition.onerror = () => { listening.value = false }
  recognition.onend = () => { listening.value = false }
  recognition.start()
}

function activeBreadcrumb(item) {
  if (mode.value === 'jahr') return item.breadcrumb_jahr
  return item.breadcrumb_lager
}
</script>

<style scoped>
/* Suchzeile: eine Linie auf dem Pergament, kein Kasten */
.suchzeile {
  display: flex; align-items: center; gap: 10px;
  border-bottom: 1.5px solid var(--linie-stark);
  padding: 4px 2px;
}
.suchzeile input {
  flex: 1; min-width: 0;
  border: none; padding: 10px 0; min-height: 46px;
}
.suchzeile input:focus { outline: none; }
.lupe { font-size: 20px; color: var(--tinte-blass); flex-shrink: 0; }

.sprechen {
  width: 42px; height: 42px; flex-shrink: 0;
  border: 1.5px solid var(--linie-stark);
  border-radius: 50%;
  background: transparent;
  color: var(--tinte);
  font-size: 19px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.sprechen.hoert {
  background: var(--holz); color: #f7e2c0;
  border-color: transparent;
  animation: pochen 1s infinite;
}
.hoert-hinweis {
  font-family: var(--schrift-hand);
  font-size: 18px; color: var(--rot);
  text-align: center; margin-top: 10px;
}
@keyframes pochen { 0%, 100% { opacity: 1 } 50% { opacity: 0.55 } }
</style>
