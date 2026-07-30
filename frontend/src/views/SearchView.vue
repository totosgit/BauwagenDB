<template>
  <div class="page">
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
      <template v-if="items.length">
        <div class="section-label">{{ items.length }} {{ items.length === 1 ? 'Treffer' : 'Treffer' }}</div>
        <div class="polaroids">
          <Polaroid
            v-for="item in items"
            :key="item.id"
            :item="item"
            :breadcrumb="activeBreadcrumb(item)"
            @oeffnen="$router.push('/items/' + item.id)"
          />
        </div>
      </template>

      <div v-else class="empty">
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
import Polaroid from '../components/Polaroid.vue'

const { mode } = useMode()

const query = ref('')
const items = ref([])
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
    const daten = await searchAll(query.value, mode.value)
    items.value = daten.items || []
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
  return mode.value === 'jahr' ? item.breadcrumb_jahr : item.breadcrumb_lager
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
.lupe { font-size: 21px; color: var(--tinte-blass); flex-shrink: 0; }

.sprechen {
  width: 42px; height: 42px; flex-shrink: 0;
  border: 1.5px solid var(--linie-stark);
  border-radius: 50%;
  background: transparent;
  color: var(--tinte);
  font-size: 19px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.sprechen.hoert {
  background: var(--holz); color: var(--gebrannt);
  border-color: transparent;
  animation: pochen 1s infinite;
}
.hoert-hinweis {
  font-family: var(--schrift-hand);
  font-size: 18px; color: var(--rot);
  text-align: center; margin-top: 10px;
}
@keyframes pochen { 0%, 100% { opacity: 1 } 50% { opacity: 0.55 } }

/* Pinnwand: zwei Spalten, mit Luft für die Klebestreifen */
.polaroids {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px 15px;
  margin-top: 10px;
  padding-top: 6px;
}
</style>
