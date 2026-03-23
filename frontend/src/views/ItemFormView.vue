<template>
  <div class="page">
    <div class="page-header">
      <button class="btn btn-secondary btn-sm" @click="$router.back()">← Zurück</button>
      <h1 class="page-title">{{ isEdit ? 'Bearbeiten' : 'Neu' }}</h1>
    </div>

    <div v-if="loading" class="loading">Laden ...</div>

    <form v-else @submit.prevent="save">

      <!-- Basis-Infos -->
      <div class="card">
        <div class="form-group">
          <label>Name *</label>
          <input v-model="form.name" required placeholder="z.B. Akkuschrauber" />
        </div>
        <div class="form-group">
          <label>Kategorie</label>
          <select v-model="form.category">
            <option value="">— keine —</option>
            <option>Werkzeug</option>
            <option>Material</option>
            <option>Verbrauchsmaterial</option>
            <option>Elektrik</option>
            <option>Sonstiges</option>
          </select>
        </div>
        <div class="qty-row">
          <div class="form-group" style="flex:1">
            <label>Menge</label>
            <input v-model.number="form.quantity" type="number" min="0" step="0.5" />
          </div>
          <div class="form-group" style="flex:1">
            <label>Einheit</label>
            <select v-model="form.unit">
              <option>Stück</option>
              <option>Meter</option>
              <option>Liter</option>
              <option>kg</option>
              <option>Rolle</option>
              <option>Paar</option>
              <option>Satz</option>
            </select>
          </div>
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>Lagerzustand</label>
          <select v-model="form.storage_mode">
            <option value="both">Immer (Lager &amp; Jahr)</option>
            <option value="lager">Nur Auf dem Lager</option>
            <option value="jahr">Nur Unter dem Jahr</option>
          </select>
        </div>
      </div>

      <!-- Lagerort Auf dem Lager -->
      <div class="card loc-card" style="margin-top: 14px;">
        <div class="loc-card-header">
          <span class="loc-card-title">🏕️ Auf dem Lager</span>
        </div>

        <!-- Aufgebaut-Toggle -->
        <div class="aufgebaut-row" @click="form.aufgebaut = !form.aufgebaut">
          <div class="aufgebaut-check" :class="{ active: form.aufgebaut }">
            <span v-if="form.aufgebaut">✓</span>
          </div>
          <div>
            <div class="aufgebaut-label">Aufgebaut während dem Lager</div>
            <div class="aufgebaut-hint">statt einem fixen Lagerort</div>
          </div>
        </div>

        <!-- Wenn aufgebaut: Notiz-Feld statt Wizard -->
        <div v-if="form.aufgebaut" style="margin-top: 12px;">
          <label>Wo aufgebaut / Notiz</label>
          <input v-model="form.aufgebaut_notiz" placeholder="z.B. Werkstattzelt, Zeltdorf ..." />
        </div>

        <!-- Wenn nicht aufgebaut: Wizard -->
        <div v-else style="margin-top: 12px;">
          <LocationWizard
            v-model="form.location_lager_id"
            :locations="allLocations"
          />
        </div>
      </div>

      <!-- Lagerort Unter dem Jahr -->
      <div class="card" style="margin-top: 14px;">
        <div class="loc-card-header">
          <span class="loc-card-title">🏠 Unter dem Jahr</span>
        </div>
        <div style="margin-top: 12px;">
          <LocationWizard
            v-model="form.location_jahr_id"
            :locations="allLocations"
          />
        </div>
      </div>

      <!-- Zusatz-Infos -->
      <div class="card" style="margin-top: 14px;">
        <div class="form-group">
          <label>Beschreibung</label>
          <textarea v-model="form.description" placeholder="Optionale Beschreibung ..."></textarea>
        </div>
        <div class="form-group">
          <label>Tags (kommagetrennt)</label>
          <input v-model="form.tags" placeholder="z.B. holz, schrauben, lager" />
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>Notizen</label>
          <textarea v-model="form.notes" placeholder="Weitere Hinweise ..."></textarea>
        </div>
      </div>

      <div v-if="error" class="error-msg" style="margin-top: 10px;">{{ error }}</div>

      <button type="submit" class="btn btn-primary btn-lg" style="width:100%; margin-top:14px" :disabled="saving">
        {{ saving ? 'Speichern ...' : '💾 Speichern' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItem, createItem, updateItem, getLocations } from '../api/index.js'
import LocationWizard from '../components/LocationWizard.vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id
const isEdit = !!id && route.path.includes('/edit')

const form = ref({
  name: '', category: '', quantity: 1, unit: 'Stück', storage_mode: 'both',
  location_lager_id: null, location_jahr_id: null,
  aufgebaut: false, aufgebaut_notiz: '',
  description: '', tags: '', notes: '',
})
const allLocations = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  try {
    allLocations.value = await getLocations()
    if (isEdit) {
      const item = await getItem(id)
      form.value = { ...item, aufgebaut_notiz: item.aufgebaut_notiz || '' }
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.category) payload.category = null
    if (!payload.tags) payload.tags = null
    if (!payload.aufgebaut_notiz) payload.aufgebaut_notiz = null
    // Wenn aufgebaut: keinen lager-Ort speichern
    if (payload.aufgebaut) payload.location_lager_id = null
    const saved = isEdit ? await updateItem(id, payload) : await createItem(payload)
    router.push('/items/' + saved.id)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Fehler beim Speichern'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.qty-row { display: flex; gap: 12px; }
.error-msg { color: #c62828; font-size: 15px; }

.loc-card-header { margin-bottom: 4px; }
.loc-card-title { font-size: 15px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; font-size: 13px; }

.aufgebaut-row {
  display: flex; align-items: center; gap: 14px;
  cursor: pointer; padding: 10px 0 6px;
  -webkit-tap-highlight-color: transparent;
}
.aufgebaut-check {
  width: 34px; height: 34px; border-radius: 8px;
  border: 2px solid var(--border); background: var(--white);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 700; color: var(--green);
  flex-shrink: 0; transition: all 0.15s;
}
.aufgebaut-check.active { background: var(--green-pale); border-color: var(--green); }
.aufgebaut-label { font-size: 17px; font-weight: 700; }
.aufgebaut-hint { font-size: 13px; color: var(--text-muted); margin-top: 2px; }
</style>
