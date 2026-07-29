<template>
  <div class="page">
    <div class="page-header">
      <button class="btn btn-secondary btn-sm" @click="$router.back()">← Zurück</button>
      <button class="btn btn-secondary btn-sm" @click="$router.push('/items/' + id + '/edit')">Bearbeiten</button>
    </div>

    <div v-if="loading" class="loading">Laden ...</div>

    <template v-else-if="item">
      <!-- Image -->
      <div class="image-area card" @click="triggerImageUpload">
        <img v-if="item.image_path" :src="'/images/' + item.image_path" :alt="item.name" class="item-image" />
        <div v-else class="image-placeholder">
          <span style="font-size:48px">📷</span>
          <div>Foto hinzufügen</div>
        </div>
        <input ref="fileInput" type="file" accept="image/*" capture="environment" style="display:none" @change="onFileChange" />
      </div>

      <div class="card" style="margin-top: 12px;">
        <div class="detail-name">{{ item.name }}</div>
        <div v-if="item.category" style="margin-top: 6px;"><span class="tag">{{ item.category }}</span></div>

        <!-- Aufgebaut-Badge -->
        <div v-if="item.aufgebaut && mode !== 'jahr'" class="aufgebaut-badge">
          🔧 Aufgebaut<span v-if="item.aufgebaut_notiz"> · {{ item.aufgebaut_notiz }}</span>
        </div>

        <div class="divider"></div>
        <div class="detail-row"><span class="detail-label">Menge</span><span>{{ item.quantity }} {{ item.unit }}</span></div>

        <!-- Lagerorte -->
        <div v-if="item.breadcrumb_lager" class="detail-row">
          <span class="detail-label">🏕️ Lager</span>
          <span class="breadcrumb">{{ item.breadcrumb_lager }}</span>
        </div>
        <div v-if="item.breadcrumb_jahr" class="detail-row">
          <span class="detail-label">🏠 Jahr</span>
          <span class="breadcrumb">{{ item.breadcrumb_jahr }}</span>
        </div>

        <div v-if="item.description" class="detail-row"><span class="detail-label">Beschreibung</span><span>{{ item.description }}</span></div>
        <div v-if="item.notes" class="detail-row"><span class="detail-label">Notizen</span><span>{{ item.notes }}</span></div>
        <div v-if="item.tags" class="detail-row">
          <span class="detail-label">Tags</span>
          <span>
            <span v-for="tag in item.tags.split(',')" :key="tag" class="tag" style="margin-right:4px">{{ tag.trim() }}</span>
          </span>
        </div>
      </div>

      <!-- Einkaufsliste -->
      <div v-if="showShoppingForm" class="card" style="margin-top: 14px;">
        <div style="font-size:15px; font-weight:700; margin-bottom:10px;">Auf Einkaufsliste</div>
        <div class="form-group">
          <label>Menge</label>
          <input v-model.number="shopForm.quantity" type="number" min="0.5" step="0.5" />
        </div>
        <div class="form-group">
          <label>Einheit</label>
          <select v-model="shopForm.unit">
            <option>Stück</option><option>Meter</option><option>Liter</option>
            <option>kg</option><option>Rolle</option><option>Paar</option>
            <option>Satz</option><option>Packung</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>Dringlichkeit</label>
          <div class="urgency-row">
            <button v-for="u in urgencies" :key="u.value" type="button"
              class="urgency-btn" :class="[u.value, { active: shopForm.urgency === u.value }]"
              @click="shopForm.urgency = u.value">{{ u.label }}</button>
          </div>
        </div>
        <div style="display:flex; gap:8px; margin-top:12px;">
          <button class="btn btn-primary" style="flex:1" @click="addToShopping">Hinzufügen</button>
          <button class="btn btn-secondary" @click="showShoppingForm = false">Abbrechen</button>
        </div>
      </div>

      <div style="display:flex; gap:8px; margin-top: 16px;" v-if="!showShoppingForm">
        <button class="btn btn-secondary" style="flex:1" @click="openShoppingForm">🛒 Einkaufsliste</button>
        <button class="btn btn-danger" style="flex:1" @click="doDelete">Löschen</button>
      </div>
      <div v-if="showShoppingForm" style="margin-top:8px;">
        <button class="btn btn-danger" style="width:100%" @click="doDelete">Löschen</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItem, deleteItem, uploadImage, createShoppingItem } from '../api/index.js'
import { useMode } from '../composables/useMode.js'

const { mode } = useMode()

const route = useRoute()
const router = useRouter()
const id = route.params.id
const item = ref(null)
const loading = ref(false)
const fileInput = ref(null)
const showShoppingForm = ref(false)
const shopForm = ref({ quantity: 1, unit: 'Stück', urgency: 'mittel' })
const urgencies = [
  { value: 'niedrig', label: 'Niedrig' },
  { value: 'mittel', label: 'Mittel' },
  { value: 'hoch', label: 'Hoch' },
  { value: 'dringend', label: 'Dringend!' },
]

function openShoppingForm() {
  shopForm.value = { quantity: item.value?.quantity ?? 1, unit: item.value?.unit ?? 'Stück', urgency: 'mittel' }
  showShoppingForm.value = true
}

async function addToShopping() {
  await createShoppingItem({
    name: item.value.name,
    quantity: shopForm.value.quantity,
    unit: shopForm.value.unit,
    urgency: shopForm.value.urgency,
    item_id: item.value.id,
  })
  showShoppingForm.value = false
  router.push('/shopping')
}

async function load() {
  loading.value = true
  try { item.value = await getItem(id) }
  finally { loading.value = false }
}

function triggerImageUpload() { fileInput.value?.click() }

async function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  item.value = await uploadImage(id, file)
}

async function doDelete() {
  if (!confirm(`„${item.value.name}" wirklich löschen?`)) return
  await deleteItem(id)
  router.push('/items')
}

onMounted(load)
</script>

<style scoped>
.image-area { cursor: pointer; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 8px; }
.item-image { max-width: 100%; max-height: 220px; width: auto; object-fit: contain; border-radius: var(--radius); }
.image-placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-muted); padding: 32px; }
.detail-name { font-size: 24px; font-weight: 700; }
.detail-row { display: flex; gap: 12px; margin-top: 10px; }
.detail-label { font-size: 13px; font-weight: 700; color: var(--text-muted); min-width: 100px; text-transform: uppercase; letter-spacing: 0.4px; flex-shrink: 0; }
.aufgebaut-badge {
  display: inline-flex; align-items: center; gap: 6px;
  margin-top: 10px; padding: 6px 14px; border-radius: 999px;
  background: #2a1800; color: #ffa040; font-size: 14px; font-weight: 700;
}

.urgency-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.urgency-btn {
  padding: 6px 12px; border-radius: 8px; border: 2px solid var(--border);
  background: var(--white); color: var(--text-muted); font-size: 13px; font-weight: 600;
  cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.urgency-btn.active.niedrig  { background: #1a3a1a; border-color: #4caf50; color: #4caf50; }
.urgency-btn.active.mittel   { background: #1a2e3a; border-color: #2196f3; color: #2196f3; }
.urgency-btn.active.hoch     { background: #3a2a1a; border-color: #ff9800; color: #ff9800; }
.urgency-btn.active.dringend { background: #3a1a1a; border-color: #f44336; color: #f44336; }
</style>
