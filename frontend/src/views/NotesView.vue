<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Notizen</h1>
    </div>

    <!-- Neue Notiz. Der Name kommt aus dem Konto, nicht aus einem Feld. -->
    <div class="card">
      <div class="form-group" style="margin-bottom: 10px">
        <label>Notiz von {{ user?.display_name || 'dir' }}</label>
        <textarea v-model="text" placeholder="Was soll die Runde wissen?" rows="3" maxlength="2000" />
      </div>
      <button class="btn btn-primary" style="width:100%" @click="submit" :disabled="!text.trim() || sending">
        <Icon name="anheften" class="icon" />Anheften
      </button>
    </div>

    <div v-if="loading" class="loading">Laden …</div>

    <div v-else-if="!notes.length" class="empty">
      <Icon name="notizen" class="icon" />
      <div class="hinweis">Noch keine Notizen</div>
    </div>

    <div v-else class="notizen">
      <div v-for="note in notes" :key="note.id" class="card geheftet notiz">
        <div class="notiz-kopf">
          <span class="notiz-wer">{{ note.author }}</span>
          <span class="notiz-wann">{{ formatDate(note.created_at) }}</span>
          <button class="loeschen" @click="doDelete(note)" :title="'Notiz von ' + note.author + ' löschen'">
            <Icon name="schliessen" class="icon" />
          </button>
        </div>
        <div class="notiz-text">{{ note.text }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNotes, createNote, deleteNote } from '../api/index.js'
import { useAuth } from '../composables/useAuth.js'
import Icon from '../components/Icon.vue'

const { user } = useAuth()

const notes = ref([])
const loading = ref(false)
const sending = ref(false)
const text = ref('')

async function load() {
  loading.value = true
  try { notes.value = await getNotes() }
  finally { loading.value = false }
}

async function submit() {
  if (!text.value.trim()) return
  sending.value = true
  try {
    await createNote({ text: text.value.trim() })
    text.value = ''
    await load()
  } finally {
    sending.value = false
  }
}

async function doDelete(note) {
  if (!confirm(`Notiz von „${note.author}" löschen?`)) return
  await deleteNote(note.id)
  await load()
}

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' })
    + ' · ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.notizen { display: flex; flex-direction: column; gap: 18px; margin-top: 22px; }

.notiz-kopf {
  display: flex; align-items: baseline; gap: 8px;
  margin-bottom: 5px;
}
.notiz-wer {
  font-family: var(--schrift-hand);
  font-size: 20px;
  color: var(--tinte);
  flex: 1; min-width: 0;
}
.notiz-wann { font-size: 12px; color: var(--tinte-blass); flex-shrink: 0; }
.notiz-text {
  font-family: var(--schrift-hand);
  font-size: 20px;
  line-height: 1.45;
  white-space: pre-wrap;
}

.loeschen {
  border: none; background: none; cursor: pointer;
  color: var(--tinte-blass);
  font-size: 15px; padding: 4px;
  display: flex; align-items: center;
  flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}
.loeschen:active { color: var(--rot); }
</style>
