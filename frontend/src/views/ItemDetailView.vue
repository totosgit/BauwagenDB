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

      <button class="btn btn-danger" style="margin-top: 16px; width: 100%;" @click="doDelete">Löschen</button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItem, deleteItem, uploadImage } from '../api/index.js'
import { useMode } from '../composables/useMode.js'

const { mode } = useMode()

const route = useRoute()
const router = useRouter()
const id = route.params.id
const item = ref(null)
const loading = ref(false)
const fileInput = ref(null)

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
</style>
