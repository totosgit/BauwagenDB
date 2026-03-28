<template>
  <div class="page">
    <!-- Tabs -->
    <div class="drink-tabs">
      <button :class="{ active: tab === 'verkauf' }" @click="tab = 'verkauf'">🛒 Verkauf</button>
      <button :class="{ active: tab === 'gl' }" @click="tab = 'gl'">📋 Gruppenleiter</button>
      <button :class="{ active: tab === 'verwaltung' }" @click="tab = 'verwaltung'">⚙️ Verwaltung</button>
    </div>

    <!-- ===== VERKAUF ===== -->
    <div v-if="tab === 'verkauf'">
      <div class="page-header" style="margin-top: 16px;">
        <h2 class="page-title">Getränkeverkauf</h2>
      </div>

      <div v-if="loading" class="loading">Laden ...</div>
      <div v-else-if="!drinks.length" class="empty">
        <div class="icon">🥤</div>
        <div>Keine Getränke angelegt. Bitte erst unter „Verwaltung" anlegen.</div>
      </div>

      <div v-else class="drink-grid">
        <button
          v-for="drink in drinks"
          :key="drink.id"
          class="drink-card"
          :class="{ 'out-of-stock': drink.stock_lager <= 0 }"
          @click="doDeduct(drink)"
        >
          <div class="drink-emoji">{{ drink.emoji || '🥤' }}</div>
          <div class="drink-name">{{ drink.name }}</div>
          <div class="drink-stock" :class="{ low: drink.stock_lager <= 3 }">
            {{ drink.stock_lager }} Stk.
          </div>
          <div v-if="drink.price" class="drink-price">{{ drink.price.toFixed(2) }} €</div>
        </button>
      </div>

      <!-- Restock panel -->
      <div class="restock-bar card" style="margin-top: 20px;">
        <div style="font-weight: 600; margin-bottom: 10px;">📦 Bestand auffüllen</div>
        <div class="restock-row">
          <select v-model="restock.drinkId">
            <option :value="null">Getränk wählen ...</option>
            <option v-for="d in drinks" :key="d.id" :value="d.id">{{ d.emoji || '🥤' }} {{ d.name }}</option>
          </select>
          <input v-model.number="restock.amount" type="number" min="1" style="width: 80px;" />
          <button class="btn btn-primary" @click="doRestock" :disabled="!restock.drinkId">+ Auffüllen</button>
        </div>
      </div>
    </div>

    <!-- ===== GRUPPENLEITER ===== -->
    <div v-if="tab === 'gl'">
      <div class="page-header" style="margin-top: 16px;">
        <h2 class="page-title">Strichliste</h2>
        <div style="display:flex; gap: 8px;">
          <button class="btn btn-secondary btn-sm" @click="exportPDF" :disabled="!allSummaries.length">📄 PDF</button>
          <button class="btn btn-primary btn-sm" @click="showAddGL = true">+ GL</button>
        </div>
      </div>

      <!-- Add GL modal inline -->
      <div v-if="showAddGL" class="inline-form card">
        <input v-model="newGLName" placeholder="Name des Gruppenleiters" @keyup.enter="createGL" />
        <div style="display:flex; gap: 8px; margin-top: 8px;">
          <button class="btn btn-primary" @click="createGL">Hinzufügen</button>
          <button class="btn btn-secondary" @click="showAddGL = false; newGLName = ''">Abbrechen</button>
        </div>
      </div>

      <div v-if="loadingGL" class="loading">Laden ...</div>
      <div v-else-if="!groupLeaders.length" class="empty">
        <div class="icon">👤</div>
        <div>Noch keine Gruppenleiter angelegt</div>
      </div>

      <div v-else>
        <!-- Überblick alle Gruppenleiter (immer oben) -->
        <div class="section-label">Überblick</div>
        <div v-for="s in allSummaries" :key="s.group_leader_id" class="card" style="margin-top: 8px; padding: 12px;">
          <div style="display:flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600;">{{ s.group_leader_name }}</span>
            <span class="tag">{{ s.grand_total }} Getränke</span>
          </div>
          <div v-if="s.entries.length" style="margin-top: 6px; font-size: 13px; color: var(--text-muted);">
            <span v-for="e in s.entries" :key="e.drink_id" style="margin-right: 10px;">
              {{ e.drink_emoji || '🥤' }} {{ e.drink_name }}: {{ e.total }}
            </span>
          </div>
        </div>

        <!-- GL selector -->
        <div class="section-label" style="margin-top: 20px;">Strichliste</div>
        <div class="gl-chips">
          <button
            v-for="gl in groupLeaders"
            :key="gl.id"
            class="gl-chip"
            :class="{ active: selectedGL?.id === gl.id }"
            @click="toggleGL(gl)"
          >{{ gl.name }}</button>
        </div>

        <!-- Tally board for selected GL -->
        <div v-if="selectedGL" class="tally-board card" style="margin-top: 12px;">
          <div class="tally-header">
            <span class="page-title" style="font-size: 18px;">{{ selectedGL.name }}</span>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary btn-sm" @click="loadSummary">↻</button>
              <button class="btn btn-sm" style="background:#2a1018; color:#f47070"
                @click="doResetGL">Abrechnen</button>
            </div>
          </div>

          <div class="divider"></div>

          <div v-if="!drinks.length" class="empty">Keine Getränke vorhanden</div>
          <div v-else>
            <div v-for="drink in drinks" :key="drink.id" class="tally-row">
              <span class="tally-drink">{{ drink.emoji || '🥤' }} {{ drink.name }}</span>
              <div class="tally-marks">
                <span class="tally-count">{{ tallyCount(drink.id) }}</span>
                <button class="tally-btn tally-minus" @click="doTallyMinus(drink)" :disabled="tallyCount(drink.id) === 0">−</button>
                <button class="tally-btn tally-plus" @click="doTallyPlus(drink)">＋</button>
              </div>
            </div>
          </div>

          <div class="divider"></div>
          <div style="text-align: right; font-weight: 700;">
            Gesamt: {{ summary?.grand_total ?? 0 }} Getränke
          </div>
        </div>
      </div>
    </div>

    <!-- ===== VERWALTUNG ===== -->
    <div v-if="tab === 'verwaltung'">
      <div class="page-header" style="margin-top: 16px;">
        <h2 class="page-title">Getränke verwalten</h2>
        <button class="btn btn-primary btn-sm" @click="openDrinkForm(null)">+ Getränk</button>
      </div>

      <!-- Inline drink form -->
      <div v-if="drinkForm.open" class="card" style="margin-bottom: 16px;">
        <div style="font-weight: 600; margin-bottom: 12px;">{{ drinkForm.id ? 'Bearbeiten' : 'Neues Getränk' }}</div>
        <div class="form-group">
          <label>Name *</label>
          <input v-model="drinkForm.data.name" required placeholder="z.B. Cola" />
        </div>
        <div style="display:flex; gap: 8px;">
          <div class="form-group" style="flex:1">
            <label>Emoji</label>
            <input v-model="drinkForm.data.emoji" placeholder="🥤" maxlength="4" />
          </div>
          <div class="form-group" style="flex:1">
            <label>Verkaufspreis (€)</label>
            <input v-model.number="drinkForm.data.price" type="number" step="0.10" min="0" placeholder="0.50" />
          </div>
          <div class="form-group" style="flex:1">
            <label>GL-Preis (€)</label>
            <input v-model.number="drinkForm.data.price_gl" type="number" step="0.10" min="0" placeholder="kostenlos" />
          </div>
        </div>
        <div class="form-group">
          <label>Kategorie</label>
          <select v-model="drinkForm.data.category">
            <option value="">— keine —</option>
            <option>Softdrink</option>
            <option>Wasser</option>
            <option>Saft</option>
            <option>Bier</option>
            <option>Sonstiges</option>
          </select>
        </div>
        <div class="form-group">
          <label>Bestand</label>
          <input v-model.number="drinkForm.data.stock_lager" type="number" min="0" />
        </div>
        <div v-if="drinkForm.error" style="color: #c62828; font-size: 14px; margin-bottom: 8px;">{{ drinkForm.error }}</div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" @click="saveDrink">Speichern</button>
          <button class="btn btn-secondary" @click="drinkForm.open = false">Abbrechen</button>
        </div>
      </div>

      <div v-for="drink in drinks" :key="drink.id" class="card" style="margin-top: 8px; padding: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 28px;">{{ drink.emoji || '🥤' }}</span>
          <div style="flex:1">
            <div style="font-weight: 600;">{{ drink.name }}</div>
            <div style="font-size: 13px; color: var(--text-muted);">
              <span v-if="drink.category">{{ drink.category }} · </span>
              <span v-if="drink.price">VK {{ drink.price.toFixed(2) }} € · </span>
              <span v-if="drink.price_gl != null">GL {{ drink.price_gl.toFixed(2) }} € · </span>
              <span v-else style="color:#e65100">GL kostenlos · </span>
              {{ drink.stock_lager }} Stk.
            </div>
          </div>
          <button class="btn btn-secondary btn-sm" @click="openDrinkForm(drink)">✏️</button>
          <button class="btn btn-sm" style="background:#2a1018; color:#f47070" @click="doDeleteDrink(drink)">🗑️</button>
        </div>
      </div>

      <!-- Gruppenleiter management -->
      <div style="margin-top: 24px;">
        <div class="section-label">Gruppenleiter verwalten</div>
        <div v-for="gl in groupLeaders" :key="gl.id" class="card" style="margin-top: 8px; padding: 12px; display: flex; align-items: center; gap: 10px;">
          <span style="flex:1; font-weight: 600;">{{ gl.name }}</span>
          <button class="btn btn-sm" style="background:#2a1018; color:#f47070" @click="doDeleteGL(gl)">🗑️</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  getDrinks, createDrink, updateDrink, deleteDrink, deductDrink, restockDrink,
  getGroupLeaders, createGroupLeader, deleteGroupLeader,
  getTallySummary, getAllSummaries, addTally, resetTallies
} from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import { generateTallyPDF } from '../utils/tallyPDF.js'

const { mode } = useMode()

const tab = ref('gl')
const loading = ref(false)
const loadingGL = ref(false)

const drinks = ref([])
const groupLeaders = ref([])
const selectedGL = ref(null)
const summary = ref(null)
const allSummaries = ref([])

// Strichlisten-Tally-Zwischenspeicher
const pendingTallies = ref({})  // { drink_id: delta }

// Restock
const restock = ref({ drinkId: null, amount: 1 })

// GL form
const showAddGL = ref(false)
const newGLName = ref('')

// Drink form
const drinkForm = ref({
  open: false, id: null, error: '',
  data: { name: '', emoji: '', category: '', price: null, price_gl: null, stock_lager: 0 }
})

function tallyCount(drinkId) {
  const entry = summary.value?.entries?.find(e => e.drink_id === drinkId)
  const base = entry?.total ?? 0
  return base + (pendingTallies.value[drinkId] ?? 0)
}

async function load() {
  loading.value = true
  try { drinks.value = await getDrinks() }
  finally { loading.value = false }
}

async function loadGLData() {
  loadingGL.value = true
  try {
    [groupLeaders.value, allSummaries.value] = await Promise.all([getGroupLeaders(), getAllSummaries()])
  } finally { loadingGL.value = false }
}

async function toggleGL(gl) {
  if (selectedGL.value?.id === gl.id) {
    selectedGL.value = null
    return
  }
  selectedGL.value = gl
  pendingTallies.value = {}
  await loadSummary()
}

async function loadSummary() {
  if (!selectedGL.value) return
  summary.value = await getTallySummary(selectedGL.value.id)
  allSummaries.value = await getAllSummaries()
}

async function doDeduct(drink) {
  if (drink.stock_lager <= 0) return
  try {
    const updated = await deductDrink(drink.id)
    const idx = drinks.value.findIndex(d => d.id === drink.id)
    if (idx !== -1) drinks.value[idx] = updated
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Ausbuchen')
  }
}

async function doRestock() {
  if (!restock.value.drinkId || !restock.value.amount) return
  try {
    const updated = await restockDrink(restock.value.drinkId, restock.value.amount)
    const idx = drinks.value.findIndex(d => d.id === updated.id)
    if (idx !== -1) drinks.value[idx] = updated
    restock.value = { drinkId: null, amount: 1 }
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler')
  }
}

async function doTallyPlus(drink) {
  await addTally({ group_leader_id: selectedGL.value.id, drink_id: drink.id, count: 1 })
  await loadSummary()
}

async function doTallyMinus(drink) {
  // Letzten Strich löschen: wir suchen den neuesten Tally-Eintrag für diesen GL+Drink
  // Einfachster Ansatz: Summary neu laden und prüfen
  if (tallyCount(drink.id) <= 0) return
  // Wir speichern keinen tally_id direkt — stattdessen addTally mit count=-1
  // (Backend prüft das nicht, aber Summe wird korrekt)
  // Sauberer: eigener DELETE-Endpoint. Hier nutzen wir count=-1 als Korrektur.
  await addTally({ group_leader_id: selectedGL.value.id, drink_id: drink.id, count: -1 })
  await loadSummary()
}

async function doResetGL() {
  if (!confirm(`Alle Striche von „${selectedGL.value.name}" zurücksetzen (Abrechnung)?`)) return
  await resetTallies(selectedGL.value.id)
  await loadSummary()
}

async function createGL() {
  if (!newGLName.value.trim()) return
  await createGroupLeader(newGLName.value.trim())
  newGLName.value = ''
  showAddGL.value = false
  await loadGLData()
}

async function doDeleteGL(gl) {
  if (!confirm(`„${gl.name}" wirklich löschen?`)) return
  if (selectedGL.value?.id === gl.id) selectedGL.value = null
  await deleteGroupLeader(gl.id)
  await loadGLData()
}

function openDrinkForm(drink) {
  if (drink) {
    drinkForm.value = { open: true, id: drink.id, error: '',
      data: { name: drink.name, emoji: drink.emoji || '', category: drink.category || '', price: drink.price, price_gl: drink.price_gl, stock_lager: drink.stock_lager } }
  } else {
    drinkForm.value = { open: true, id: null, error: '',
      data: { name: '', emoji: '', category: '', price: null, price_gl: null, stock_lager: 0 } }
  }
}

async function saveDrink() {
  drinkForm.value.error = ''
  try {
    const payload = { ...drinkForm.value.data }
    if (!payload.category) payload.category = null
    if (!payload.emoji) payload.emoji = null
    // Leere Zahlenfelder → null (v-model.number gibt '' zurück bei leerem Input)
    if (payload.price === '' || isNaN(payload.price)) payload.price = null
    if (payload.price_gl === '' || isNaN(payload.price_gl)) payload.price_gl = null
    if (drinkForm.value.id) await updateDrink(drinkForm.value.id, payload)
    else await createDrink(payload)
    drinkForm.value.open = false
    await load()
  } catch (e) {
    drinkForm.value.error = e.response?.data?.detail || 'Fehler beim Speichern'
  }
}

function exportPDF() {
  generateTallyPDF(allSummaries.value, drinks.value)
}

async function doDeleteDrink(drink) {
  if (!confirm(`„${drink.name}" wirklich löschen?`)) return
  await deleteDrink(drink.id)
  await load()
}

onMounted(async () => {
  await Promise.all([load(), loadGLData()])
})
</script>

<style scoped>
.drink-tabs { display: flex; gap: 0; border-bottom: 2px solid var(--border); margin-bottom: 4px; }
.drink-tabs button { flex: 1; padding: 12px 8px; border: none; background: none; font-size: 14px; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px; -webkit-tap-highlight-color: transparent; }
.drink-tabs button.active { color: var(--green); border-bottom-color: var(--green); }

.stock-mode-label { font-size: 13px; font-weight: 600; color: var(--text-muted); }

.drink-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; margin-top: 4px; }
.drink-card { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 16px 8px; background: var(--white); border-radius: var(--radius); box-shadow: var(--shadow); border: 2px solid transparent; cursor: pointer; -webkit-tap-highlight-color: transparent; transition: transform 0.1s, border-color 0.1s; }
.drink-card:active { transform: scale(0.95); border-color: var(--green); }
.drink-card.out-of-stock { opacity: 0.45; cursor: not-allowed; }
.drink-emoji { font-size: 36px; }
.drink-name { font-size: 14px; font-weight: 600; text-align: center; }
.drink-stock { font-size: 13px; font-weight: 700; color: var(--green); }
.drink-stock.low { color: #e65100; }
.drink-price { font-size: 12px; color: var(--text-muted); }

.restock-bar { padding: 14px; }
.restock-row { display: flex; gap: 8px; align-items: center; }
.restock-row select { flex: 1; }

.gl-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
.gl-chip { padding: 8px 16px; border-radius: 999px; border: 2px solid var(--border); background: var(--white); font-size: 14px; font-weight: 600; cursor: pointer; -webkit-tap-highlight-color: transparent; transition: all 0.15s; }
.gl-chip.active { background: var(--green); color: white; border-color: var(--green); }

.tally-board { padding: 16px; }
.tally-header { display: flex; justify-content: space-between; align-items: center; }
.tally-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border); }
.tally-drink { font-size: 15px; font-weight: 500; }
.tally-marks { display: flex; align-items: center; gap: 10px; }
.tally-count { font-size: 20px; font-weight: 700; min-width: 32px; text-align: center; color: var(--green); }
.tally-btn { width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--border); background: var(--white); font-size: 20px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; -webkit-tap-highlight-color: transparent; }
.tally-btn:active { transform: scale(0.9); }
.tally-btn.tally-plus { background: var(--green); color: white; border-color: var(--green); font-size: 18px; }
.tally-btn.tally-minus { color: #c62828; border-color: #c62828; }
.tally-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.inline-form { margin-bottom: 12px; padding: 14px; }
.section-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 8px; }

@media (max-width: 390px) {
  .drink-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .drink-card { padding: 12px 6px; }
  .drink-emoji { font-size: 28px; }
  .drink-name { font-size: 13px; }
  .drink-tabs button { font-size: 12px; padding: 10px 4px; }
  .tally-btn { width: 36px; height: 36px; font-size: 18px; }
  .gl-chip { padding: 6px 12px; font-size: 13px; }
  .restock-row { flex-wrap: wrap; }
}
</style>
