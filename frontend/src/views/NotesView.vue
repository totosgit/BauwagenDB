<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">Notizen</h2>
    </div>

    <!-- Neue Notiz -->
    <div class="card note-form">
      <input v-model="form.author" placeholder="Dein Name" class="author-input" maxlength="100" />
      <textarea v-model="form.text" placeholder="Notiz schreiben ..." rows="3" maxlength="2000" />
      <button class="btn btn-primary" @click="submit" :disabled="!form.author.trim() || !form.text.trim()">
        Notiz hinterlassen
      </button>
    </div>

    <!-- Notizen-Liste -->
    <div v-if="loading" class="loading">Laden ...</div>
    <div v-else-if="!notes.length" class="empty">
      <div class="icon">📝</div>
      <div>Noch keine Notizen</div>
    </div>

    <div v-else class="notes-list">
      <div v-for="note in notes" :key="note.id" class="card note-card">
        <div class="note-meta">
          <span class="note-author">{{ note.author }}</span>
          <span class="note-date">{{ formatDate(note.created_at) }}</span>
          <button class="delete-btn" @click="doDelete(note)" title="Löschen">✕</button>
        </div>
        <div class="note-text">{{ note.text }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNotes, createNote, deleteNote } from '../api/index.js'

const notes = ref([])
const loading = ref(false)
const form = ref({ author: '', text: '' })

async function load() {
  loading.value = true
  try { notes.value = await getNotes() }
  finally { loading.value = false }
}

async function submit() {
  if (!form.value.author.trim() || !form.value.text.trim()) return
  await createNote({ author: form.value.author.trim(), text: form.value.text.trim() })
  form.value.text = ''
  await load()
}

async function doDelete(note) {
  if (!confirm(`Notiz von „${note.author}" löschen?`)) return
  await deleteNote(note.id)
  await load()
}

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.note-form {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}
.author-input {
  font-weight: 600;
}
textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px;
  font-size: 15px;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.note-card {
  padding: 14px;
}
.note-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.note-author {
  font-weight: 700;
  font-size: 15px;
  flex: 1;
}
.note-date {
  font-size: 12px;
  color: var(--text-muted);
}
.delete-btn {
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 4px;
  -webkit-tap-highlight-color: transparent;
}
.delete-btn:active { background: #2a1018; color: #f47070; }
.note-text {
  font-size: 15px;
  line-height: 1.5;
  white-space: pre-wrap;
  color: var(--text);
}
</style>
