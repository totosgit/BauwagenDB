<template>
  <div class="page">
    <!-- Tabs -->
    <div class="drink-tabs">
      <button :class="{ active: tab === 'verkauf' }" @click="tab = 'verkauf'">🛒 Verkauf</button>
      <button :class="{ active: tab === 'strich' }" @click="tab = 'strich'">📋 Strichliste</button>
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

    <!-- ===== STRICHLISTE (Papier) ===== -->
    <div v-if="tab === 'strich'" class="strich-tab">
      <div class="page-header" style="margin-top: 16px;">
        <h2 class="page-title">Strichliste</h2>
        <button class="btn btn-secondary btn-sm" @click="exportPDF" :disabled="!allSummaries.length">📄 PDF</button>
      </div>

      <div v-if="loadingTally" class="loading">Laden ...</div>
      <div v-else-if="!drinks.length" class="empty">
        <div class="icon">🥤</div>
        <div>Keine Getränke angelegt. Bitte erst unter „Verwaltung" anlegen.</div>
      </div>

      <template v-else>
        <!-- Eigener Zettel: hier wird gestrichelt -->
        <div v-if="mySummary" class="paper paper-own">
          <div class="paper-head">
            <span class="paper-name">{{ mySummary.display_name }}</span>
            <span class="paper-you">das bin ich</span>
          </div>

          <div v-for="drink in drinks" :key="drink.id" class="paper-line">
            <span class="line-drink">{{ drink.emoji || '🥤' }} {{ drink.name }}</span>
            <span class="line-marks"><TallyMarks :count="countFor(mySummary, drink.id)" /></span>
            <span class="line-actions">
              <button
                class="ink-btn"
                :disabled="countFor(mySummary, drink.id) === 0 || busy"
                @click="minusOne(drink)"
                aria-label="Strich zurücknehmen"
              >−</button>
              <button class="ink-btn plus" :disabled="busy" @click="plusOne(drink)" aria-label="Strich setzen">＋</button>
            </span>
          </div>

          <div class="paper-total">
            <span>Zusammen</span>
            <span class="total-num">{{ mySummary.grand_total }}</span>
          </div>
        </div>

        <!-- Zettel der anderen: nur lesen -->
        <div v-if="others.length" class="others-label">Die anderen</div>
        <div v-for="s in others" :key="s.user_id" class="paper">
          <div class="paper-head">
            <router-link :to="'/users/' + s.user_id" class="paper-name link">{{ s.display_name }}</router-link>
            <button
              v-if="isAdmin && s.grand_total > 0"
              class="settle-btn"
              @click="settle(s)"
            >abrechnen</button>
          </div>

          <div v-if="!s.entries.length" class="paper-empty">noch nichts getrunken</div>
          <div v-for="e in s.entries" :key="e.drink_id" class="paper-line">
            <span class="line-drink">{{ e.drink_emoji || '🥤' }} {{ e.drink_name }}</span>
            <span class="line-marks"><TallyMarks :count="e.total" /></span>
          </div>

          <div v-if="s.entries.length" class="paper-total">
            <span>Zusammen</span>
            <span class="total-num">{{ s.grand_total }}</span>
          </div>
        </div>
      </template>
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

      <div class="hint-box">
        Wer auf der Strichliste auftaucht, ergibt sich jetzt aus den Benutzerkonten.
        Konten freigeben und verwalten kannst du unter
        <router-link to="/admin">Verwaltung</router-link>.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  getDrinks, createDrink, updateDrink, deleteDrink, deductDrink, restockDrink,
  getAllSummaries, addTally, removeLastTally, resetTallies
} from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import { useAuth } from '../composables/useAuth.js'
import { generateTallyPDF } from '../utils/tallyPDF.js'
import TallyMarks from '../components/TallyMarks.vue'

const { mode } = useMode()
const { isAdmin } = useAuth()

const tab = ref('strich')
const loading = ref(false)
const loadingTally = ref(false)
const busy = ref(false)

const drinks = ref([])
const allSummaries = ref([])

// Das Backend sortiert den eigenen Eintrag nach vorne (is_self).
const mySummary = computed(() => allSummaries.value.find(s => s.is_self) || null)
const others = computed(() => allSummaries.value.filter(s => !s.is_self))

// Restock
const restock = ref({ drinkId: null, amount: 1 })

// Drink form
const drinkForm = ref({
  open: false, id: null, error: '',
  data: { name: '', emoji: '', category: '', price: null, price_gl: null, stock_lager: 0 }
})

function countFor(summary, drinkId) {
  return summary?.entries?.find(e => e.drink_id === drinkId)?.total ?? 0
}

async function load() {
  loading.value = true
  try { drinks.value = await getDrinks() }
  finally { loading.value = false }
}

async function loadTallies() {
  loadingTally.value = true
  try { allSummaries.value = await getAllSummaries() }
  finally { loadingTally.value = false }
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

async function plusOne(drink) {
  busy.value = true
  try {
    await addTally(drink.id)
    await loadTallies()
  } finally { busy.value = false }
}

async function minusOne(drink) {
  busy.value = true
  try {
    await removeLastTally(drink.id)
    await loadTallies()
  } finally { busy.value = false }
}

async function settle(summary) {
  if (!confirm(`Alle Striche von „${summary.display_name}" zurücksetzen (Abrechnung)?`)) return
  await resetTallies(summary.user_id)
  await loadTallies()
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
  await Promise.all([load(), loadTallies()])
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

/* ── Strichliste: Papier & Handschrift ────────────────────────────
   Bewusst nur auf diese eine Ansicht begrenzt -- der Rest der App
   bleibt im gewohnten dunklen Theme.
   Die Schrift kommt vom Gerät (iOS: Bradley Hand / Noteworthy), damit
   nichts nachgeladen werden muss und es auch offline stimmt. */
.strich-tab {
  --ink:        #2c3e57;
  --ink-soft:   #6b7a90;
  --ink-red:    #b5443a;
  --paper:      #f6f0e2;
  --paper-line: #d9d0bb;

  font-family: 'Bradley Hand', 'Noteworthy', 'Segoe Print', 'Comic Sans MS', cursive;
}

.paper {
  position: relative;
  background: var(--paper);
  color: var(--ink);
  border-radius: 3px;
  padding: 18px 18px 14px 26px;
  margin-top: 14px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.45);
  /* feine Linien wie auf liniertem Papier */
  background-image: repeating-linear-gradient(
    to bottom,
    transparent 0 43px,
    var(--paper-line) 43px 44px
  );
  overflow: hidden;
}
/* roter Rand links wie im Schulheft */
.paper::before {
  content: '';
  position: absolute;
  top: 0; bottom: 0; left: 14px;
  width: 1.5px;
  background: var(--ink-red);
  opacity: 0.5;
}
.paper-own {
  box-shadow: 0 3px 14px rgba(0,0,0,0.5);
  transform: rotate(-0.35deg);
}

.paper-head {
  display: flex; align-items: baseline; gap: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 6px;
}
.paper-name { font-size: 26px; font-weight: 700; flex: 1; min-width: 0; }
.paper-name.link { color: var(--ink); text-decoration: none; }
.paper-you { font-size: 15px; color: var(--ink-soft); flex-shrink: 0; }
.settle-btn {
  background: none; border: none; cursor: pointer;
  font-family: inherit; font-size: 16px; color: var(--ink-red);
  text-decoration: underline; padding: 4px 2px; flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}

.paper-line {
  display: flex; align-items: center; gap: 10px;
  min-height: 44px;
  padding: 4px 0;
}
.line-drink { font-size: 19px; flex: 0 0 34%; min-width: 0; }
.line-marks { flex: 1; min-width: 0; color: var(--ink); }
.line-actions { display: flex; gap: 6px; flex-shrink: 0; }

.ink-btn {
  width: 38px; height: 38px; border-radius: 50%;
  border: 2px solid var(--ink); background: transparent;
  color: var(--ink); font-size: 20px; font-weight: 700;
  font-family: inherit; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  -webkit-tap-highlight-color: transparent;
}
.ink-btn:active { transform: scale(0.9); background: rgba(44,62,87,0.12); }
.ink-btn.plus { background: var(--ink); color: var(--paper); }
.ink-btn:disabled { opacity: 0.25; cursor: not-allowed; }

.paper-total {
  display: flex; justify-content: space-between; align-items: baseline;
  border-top: 2px solid var(--ink);
  margin-top: 8px; padding-top: 8px;
  font-size: 19px;
}
.total-num { font-size: 27px; font-weight: 700; }
.paper-empty { color: var(--ink-soft); font-size: 18px; padding: 8px 0; }

.others-label {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: var(--text-muted);
  margin: 26px 0 2px;
}

.hint-box {
  margin-top: 24px; padding: 14px;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius); font-size: 15px; line-height: 1.5;
  color: var(--text-muted);
}
.hint-box a { color: var(--green-light); font-weight: 700; }

.inline-form { margin-bottom: 12px; padding: 14px; }
.section-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 8px; }

@media (max-width: 390px) {
  .drink-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .drink-card { padding: 12px 6px; }
  .drink-emoji { font-size: 28px; }
  .drink-name { font-size: 13px; }
  .drink-tabs button { font-size: 12px; padding: 10px 4px; }
  .restock-row { flex-wrap: wrap; }

  .paper { padding: 14px 12px 12px 22px; }
  .paper-name { font-size: 22px; }
  .line-drink { flex: 0 0 30%; font-size: 17px; }
  .ink-btn { width: 34px; height: 34px; font-size: 18px; }
  .total-num { font-size: 24px; }
}
</style>
