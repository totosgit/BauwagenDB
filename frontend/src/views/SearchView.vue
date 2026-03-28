<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Suche</h1>
    </div>

    <div class="search-bar card">
      <div class="search-input-row">
        <input
          ref="inputEl"
          v-model="query"
          type="search"
          placeholder="Werkzeug, Material, Ort ..."
          autocomplete="off"
          autocorrect="off"
          @input="onInput"
        />
        <button
          v-if="speechSupported"
          class="btn btn-icon"
          :class="{ 'btn-primary': listening }"
          @click="toggleVoice"
          :title="listening ? 'Aufnahme stoppen' : 'Spracheingabe'"
        >
          🎤
        </button>
      </div>
      <div v-if="listening" class="voice-hint">Sprechen Sie jetzt ...</div>
    </div>

    <div v-if="loading" class="loading">Suche läuft ...</div>

    <template v-else-if="searched">
      <!-- Items -->
      <div v-if="results.items.length" style="margin-top: 20px;">
        <div class="section-label">Gegenstände ({{ results.items.length }})</div>
        <div
          v-for="item in results.items"
          :key="'i' + item.id"
          class="item-row"
          @click="$router.push('/items/' + item.id)"
        >
          <div class="item-thumb">
            <img v-if="item.image_path" :src="'/images/' + item.image_path" :alt="item.name" />
            <span v-else>{{ categoryIcon(item.category) }}</span>
          </div>
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-meta">
              <span v-if="item.quantity">{{ item.quantity }} {{ item.unit }}</span>
              <span v-if="activeBreadcrumb(item)"> · 📍 {{ activeBreadcrumb(item) }}</span>
              <span v-if="item.aufgebaut && mode !== 'jahr'" class="aufgebaut-pill">🔧 Aufgebaut</span>
            </div>
          </div>
          <span v-if="item.category" class="tag">{{ item.category }}</span>
        </div>
      </div>

      <!-- Locations -->
      <div v-if="results.locations.length" style="margin-top: 20px;">
        <div class="section-label">Lagerorte ({{ results.locations.length }})</div>
        <div
          v-for="loc in results.locations"
          :key="'l' + loc.id"
          class="item-row"
          @click="$router.push('/locations')"
        >
          <div class="item-thumb">📦</div>
          <div class="item-info">
            <div class="item-name">{{ loc.name }}</div>
            <div class="item-meta">
              <span class="type-badge">{{ loc.type }}</span>
              <span v-if="loc.breadcrumb"> · {{ loc.breadcrumb }}</span>
            </div>
          </div>
          <span class="tag">{{ loc.item_count }} Dinge</span>
        </div>
      </div>

      <div v-if="!results.items.length && !results.locations.length" class="empty">
        <div class="icon">🔎</div>
        <div>Nichts gefunden für „{{ query }}"</div>
      </div>
    </template>

    <div v-else class="empty" style="margin-top: 48px;">
      <div class="icon">🔍</div>
      <div>Tippen oder sprechen Sie einen Suchbegriff ein</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchAll } from '../api/index.js'
import { useMode } from '../composables/useMode.js'

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

function categoryIcon(cat) {
  const map = { 'Werkzeug': '🔧', 'Material': '🪵', 'Verbrauchsmaterial': '🔩', 'Elektrik': '⚡', 'Sonstiges': '📦' }
  return map[cat] || '📦'
}

function activeBreadcrumb(item) {
  if (mode.value === 'jahr') return item.breadcrumb_jahr
  return item.breadcrumb_lager
}
</script>

<style scoped>
.search-input-row { display: flex; gap: 10px; align-items: center; }
.search-input-row input { flex: 1; }
.voice-hint { margin-top: 10px; font-size: 14px; color: var(--green); font-weight: 600; text-align: center; animation: pulse 1s infinite; }
.section-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 10px; }
.item-thumb { width: 48px; height: 48px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 28px; border-radius: var(--radius); overflow: hidden; background: var(--surface-2); }
.item-thumb img { width: 100%; height: 100%; object-fit: cover; }
.aufgebaut-pill { display: inline-block; padding: 1px 8px; border-radius: 999px; background: #2a1800; color: #ffa040; font-size: 12px; font-weight: 700; margin-left: 4px; }
@keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.5 } }
</style>
