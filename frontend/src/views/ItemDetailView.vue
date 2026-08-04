<template>
  <div class="page">
    <div class="page-header">
      <button class="btn btn-secondary btn-sm" @click="$router.back()">
        <Icon name="zurueck" class="icon" />Zurück
      </button>
      <button class="btn btn-secondary btn-sm" @click="$router.push('/items/' + id + '/edit')">
        <Icon name="stift" class="icon" />Bearbeiten
      </button>
    </div>

    <div v-if="loading" class="loading">Laden …</div>

    <template v-else-if="item">
      <!-- Das Polaroid trägt Name und Ort schon selbst -->
      <div class="polaroid-halter">
        <Polaroid
          class="gross"
          :item="item"
          :breadcrumb="activeBreadcrumb"
          :im-lager="mode !== 'jahr'"
        />
        <div class="foto-knoepfe">
          <button class="foto-knopf" @click="kameraEingabe?.click()">
            <Icon name="kamera" class="icon" />Aufnehmen
          </button>
          <button class="foto-knopf" @click="galerieEingabe?.click()">
            <Icon name="orte" class="icon" />Auswählen
          </button>
        </div>
        <!-- Getrennte Felder: mit "capture" lässt iOS nur die Kamera zu -->
        <input ref="kameraEingabe" type="file" accept="image/*" capture="environment" style="display:none" @change="onFileChange" />
        <input ref="galerieEingabe" type="file" accept="image/*" style="display:none" @change="onFileChange" />
      </div>

      <div class="card" style="margin-top: 14px;">
        <div v-if="item.category"><span class="tag">{{ item.category }}</span></div>

        <div v-if="item.aufgebaut && mode !== 'jahr'" class="aufgebaut">
          <Icon name="dinge" class="icon" />
          Aufgebaut<span v-if="item.aufgebaut_notiz"> · {{ item.aufgebaut_notiz }}</span>
        </div>

        <div class="divider"></div>
        <div class="detail-row">
          <span class="detail-label">Menge</span>
          <span class="menge">{{ item.quantity }} {{ item.unit }}</span>
        </div>

        <!-- Lagerorte -->
        <div v-if="item.breadcrumb_lager" class="detail-row">
          <span class="detail-label"><Icon name="zelt" class="icon" />Lager</span>
          <span class="breadcrumb">{{ item.breadcrumb_lager }}</span>
        </div>
        <div v-if="item.breadcrumb_jahr" class="detail-row">
          <span class="detail-label"><Icon name="haus" class="icon" />Jahr</span>
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
        <button class="btn btn-secondary" style="flex:1" @click="openShoppingForm">
          <Icon name="einkauf" class="icon" />Einkauf
        </button>
        <button class="btn btn-danger" style="flex:1" @click="doDelete">
          <Icon name="muell" class="icon" />Löschen
        </button>
      </div>
      <div v-if="showShoppingForm" style="margin-top:8px;">
        <button class="btn btn-danger" style="width:100%" @click="doDelete">
          <Icon name="muell" class="icon" />Löschen
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItem, deleteItem, uploadImage, createShoppingItem } from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import Icon from '../components/Icon.vue'
import Polaroid from '../components/Polaroid.vue'

const { mode } = useMode()

const route = useRoute()
const router = useRouter()
const id = route.params.id
const item = ref(null)
const loading = ref(false)
const kameraEingabe = ref(null)
const galerieEingabe = ref(null)
const showShoppingForm = ref(false)
const shopForm = ref({ quantity: 1, unit: 'Stück', urgency: 'mittel' })
const urgencies = [
  { value: 'niedrig', label: 'Niedrig' },
  { value: 'mittel', label: 'Mittel' },
  { value: 'hoch', label: 'Hoch' },
  { value: 'dringend', label: 'Dringend!' },
]

const activeBreadcrumb = computed(() =>
  mode.value === 'jahr' ? item.value?.breadcrumb_jahr : item.value?.breadcrumb_lager
)

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

async function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  item.value = await uploadImage(id, file)
  e.target.value = ''   // sonst löst dieselbe Datei kein change mehr aus
}

async function doDelete() {
  if (!confirm(`„${item.value.name}" wirklich löschen?`)) return
  await deleteItem(id)
  router.push('/items')
}

onMounted(load)
</script>

<style scoped>
/* Das große Polaroid sitzt zentriert, darunter der Foto-Knopf */
.polaroid-halter {
  display: flex; flex-direction: column; align-items: center;
  gap: 14px;
  padding-top: 8px;
}
.polaroid-halter > :first-child { width: 100%; max-width: 320px; }
.foto-knoepfe { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }

.foto-knopf {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 16px; min-height: 44px;
  border: 1.5px solid var(--linie-stark);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--tinte);
  font-family: var(--schrift-stempel);
  font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.1em;
  cursor: pointer;
}
.foto-knopf .icon { font-size: 16px; }

.detail-row { display: flex; gap: 12px; margin-top: 10px; align-items: baseline; }
.detail-label {
  font-family: var(--schrift-stempel);
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--tinte-blass);
  min-width: 92px; flex-shrink: 0;
  display: inline-flex; align-items: center; gap: 5px;
}
.detail-label .icon { font-size: 13px; }

.aufgebaut {
  display: inline-flex; align-items: center; gap: 6px;
  margin-top: 10px; padding: 5px 12px;
  border: 1.5px solid rgba(158, 58, 34, 0.5);
  border-radius: var(--radius-sm);
  color: var(--rot);
  font-family: var(--schrift-stempel);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
}

/* Dringlichkeit wie auf der Einkaufsliste: gestempelt, nicht bunt */
.urgency-row { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 4px; }
.urgency-btn {
  padding: 8px 12px; min-height: 40px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--linie);
  background: transparent; color: var(--tinte-blass);
  font-family: var(--schrift-stempel);
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.1em;
  cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.urgency-btn.active {
  color: var(--gebrannt); border-color: var(--gebrannt);
  background: rgba(53, 29, 8, 0.07);
}
.urgency-btn.active.dringend {
  color: var(--rot); border-color: var(--rot); background: var(--rot-blass);
}
</style>
