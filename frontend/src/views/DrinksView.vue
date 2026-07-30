<template>
  <div class="page">
    <!-- Tabs -->
    <div class="drink-tabs">
      <button :class="{ active: tab === 'verkauf' }" @click="tab = 'verkauf'"><Icon name="einkauf" class="icon" />Verkauf</button>
      <button :class="{ active: tab === 'strich' }" @click="tab = 'strich'"><Icon name="notizen" class="icon" />Strichliste</button>
      <button :class="{ active: tab === 'verwaltung' }" @click="tab = 'verwaltung'"><Icon name="verwaltung" class="icon" />Verwaltung</button>
    </div>

    <!-- ===== VERKAUF ===== -->
    <div v-if="tab === 'verkauf'">
      <div class="page-header" style="margin-top: 16px;">
        <h2 class="page-title">Getränkeverkauf</h2>
      </div>

      <div v-if="loading" class="loading">Laden ...</div>
      <div v-else-if="!drinks.length" class="empty">
        <Icon name="getraenke" class="icon" />
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
          <div class="drink-emoji"><span v-if="drink.emoji">{{ drink.emoji }}</span><Icon v-else name="getraenke" class="icon" /></div>
          <div class="drink-name">{{ drink.name }}</div>
          <div class="drink-stock" :class="{ low: drink.stock_lager <= 3 }">
            {{ drink.stock_lager }} Stk.
          </div>
          <div v-if="drink.price" class="drink-price">{{ drink.price.toFixed(2) }} €</div>
        </button>
      </div>

      <!-- Restock panel -->
      <div class="restock-bar card" style="margin-top: 20px;">
        <div class="section-label" style="margin-top:0"><Icon name="auffuellen" class="icon" />Bestand auffüllen</div>
        <div class="restock-row">
          <select v-model="restock.drinkId">
            <option :value="null">Getränk wählen ...</option>
            <option v-for="d in drinks" :key="d.id" :value="d.id">{{ d.emoji ? d.emoji + ' ' : '' }}{{ d.name }}</option>
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
        <button class="btn btn-secondary btn-sm" @click="exportPDF" :disabled="!allSummaries.length"><Icon name="pdf" class="icon" />PDF</button>
      </div>

      <div v-if="loadingTally" class="loading">Laden …</div>
      <div v-else-if="!drinks.length" class="empty">
        <Icon name="getraenke" class="icon" />
        <div class="hinweis">Keine Getränke angelegt. Bitte erst unter „Verwaltung" anlegen.</div>
      </div>

      <template v-else>
        <div v-if="strichFehler" class="strich-fehler">{{ strichFehler }}</div>
        <!-- Eigener Zettel: hier wird gestrichelt -->
        <div v-if="mySummary" class="zettel zettel-schief">
          <div class="zettel-kopf">
            <span class="wer">{{ mySummary.display_name }}</span>
            <span class="dazu">das bin ich</span>
          </div>

          <div v-for="drink in drinks" :key="drink.id" class="zettel-zeile">
            <span class="line-drink"><span v-if="drink.emoji">{{ drink.emoji }}</span><Icon v-else name="getraenke" class="icon" />{{ drink.name }}</span>
            <span class="line-marks"><TallyMarks :count="countFor(mySummary, drink.id)" /></span>
            <span class="line-actions">
              <button
                class="ink-btn"
                :disabled="countFor(mySummary, drink.id) === 0"
                @click="minusOne(drink)"
                aria-label="Strich zurücknehmen"
              ><Icon name="minus" class="icon" /></button>
              <button class="ink-btn plus" @click="plusOne(drink)" aria-label="Strich setzen"><Icon name="plus" class="icon" /></button>
            </span>
          </div>

          <div class="zettel-summe">
            <span>Zusammen</span>
            <b>{{ mySummary.grand_total }}</b>
          </div>
        </div>

        <!-- Zettel der anderen: nur lesen -->
        <div v-if="others.length" class="others-label">Die anderen</div>
        <div v-for="s in others" :key="s.user_id" class="zettel">
          <div class="zettel-kopf">
            <router-link :to="'/users/' + s.user_id" class="wer link">{{ s.display_name }}</router-link>
            <button
              v-if="isAdmin && s.grand_total > 0"
              class="settle-btn"
              @click="settle(s)"
            >abrechnen</button>
          </div>

          <div v-if="!s.entries.length" class="paper-empty">noch nichts getrunken</div>
          <div v-for="e in s.entries" :key="e.drink_id" class="zettel-zeile">
            <span class="line-drink"><span v-if="e.drink_emoji">{{ e.drink_emoji }}</span><Icon v-else name="getraenke" class="icon" />{{ e.drink_name }}</span>
            <span class="line-marks"><TallyMarks :count="e.total" /></span>
          </div>

          <div v-if="s.entries.length" class="zettel-summe">
            <span>Zusammen</span>
            <b>{{ s.grand_total }}</b>
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
        <div v-if="drinkForm.error" style="color: var(--rot); font-size: 14px; margin-bottom: 8px;">{{ drinkForm.error }}</div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" @click="saveDrink">Speichern</button>
          <button class="btn btn-secondary" @click="drinkForm.open = false">Abbrechen</button>
        </div>
      </div>

      <div v-for="drink in drinks" :key="drink.id" class="card" style="margin-top: 8px; padding: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="verw-emoji"><span v-if="drink.emoji">{{ drink.emoji }}</span><Icon v-else name="getraenke" class="icon" /></span>
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
          <button class="btn btn-secondary btn-sm" @click="openDrinkForm(drink)" aria-label="Bearbeiten"><Icon name="stift" class="icon" /></button>
          <button class="btn btn-sm btn-danger" @click="doDeleteDrink(drink)" aria-label="Löschen"><Icon name="muell" class="icon" /></button>
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
import Icon from '../components/Icon.vue'

const { mode } = useMode()
const { isAdmin } = useAuth()

const tab = ref('strich')
const loading = ref(false)
const loadingTally = ref(false)
const strichFehler = ref('')

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

/**
 * still = ohne Ladeanzeige. Beim Strichmachen darf die Liste nicht
 * verschwinden und neu aufgebaut werden -- das war beim Tippen störend.
 */
async function loadTallies({ still = false } = {}) {
  if (!still) loadingTally.value = true
  try { allSummaries.value = await getAllSummaries() }
  finally { if (!still) loadingTally.value = false }
}

/** Zählt lokal hoch oder runter, damit der Strich sofort dasteht. */
function zaehleLokal(drink, delta) {
  const s = mySummary.value
  if (!s) return
  let e = s.entries.find(x => x.drink_id === drink.id)
  if (!e) {
    if (delta < 0) return
    e = { drink_id: drink.id, drink_name: drink.name, drink_emoji: drink.emoji, total: 0 }
    s.entries.push(e)
    s.entries.sort((a, b) => a.drink_name.localeCompare(b.drink_name, 'de'))
  }
  e.total += delta
  if (e.total <= 0) s.entries = s.entries.filter(x => x !== e)
  s.grand_total = Math.max(0, s.grand_total + delta)
}

// Nach dem Tippen einmal still nachladen -- so tauchen auch die Striche
// der anderen auf, ohne dass es beim Tippen ruckelt.
let abgleichTimer = null
function spaeterAbgleichen() {
  clearTimeout(abgleichTimer)
  abgleichTimer = setTimeout(() => loadTallies({ still: true }), 2000)
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
  zaehleLokal(drink, +1)
  try {
    await addTally(drink.id)
    spaeterAbgleichen()
  } catch {
    zaehleLokal(drink, -1)   // zurücknehmen, der Strich ging nicht durch
    strichFehler.value = 'Strich konnte nicht gespeichert werden'
  }
}

async function minusOne(drink) {
  zaehleLokal(drink, -1)
  try {
    await removeLastTally(drink.id)
    spaeterAbgleichen()
  } catch {
    zaehleLokal(drink, +1)
    strichFehler.value = 'Konnte nicht zurückgenommen werden'
  }
}

async function settle(summary) {
  if (!confirm(`Alle Striche von „${summary.display_name}" zurücksetzen (Abrechnung)?`)) return
  await resetTallies(summary.user_id)
  await loadTallies({ still: true })
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

/* ── Strichliste ──────────────────────────────────────────────────
   Nutzt jetzt die globalen Materialien -- die eigenen Farbvariablen
   von früher wären doppelt, seit die ganze App auf Pergament liegt.
   Die Zettel bleiben eigene Blätter, weil es inhaltlich welche sind. */
.strich-tab {
  --ink:        var(--tinte);
  --ink-soft:   var(--tinte-blass);
  --ink-red:    var(--rot);
  --paper:      var(--blatt);
  --paper-line: var(--linie);

  font-family: var(--schrift-hand);
}



/* Aufteilung einer Strichzeile: Getränk | Striche | Knöpfe.
   Der Zettel selbst (Papier, Linien, Kopf, Summe) kommt aus style.css. */
.line-drink {
  font-family: var(--schrift-hand);
  font-size: 19px;
  flex: 0 0 31%;
  min-width: 0;
  display: inline-flex; align-items: center; gap: 6px;
}
.line-drink .icon { font-size: 17px; }
.line-marks { flex: 1; min-width: 0; color: var(--tinte); }
.line-actions { display: flex; gap: 6px; flex-shrink: 0; }

.ink-btn {
  width: 38px; height: 38px; border-radius: 50%;
  border: 2px solid var(--tinte); background: transparent;
  color: var(--tinte); font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  padding: 0; cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.ink-btn:active { transform: scale(0.9); background: rgba(53, 29, 8, 0.1); }
.ink-btn.plus { background: var(--tinte); color: var(--blatt); }
.ink-btn:disabled { opacity: 0.25; cursor: not-allowed; }

.paper-empty {
  font-family: var(--schrift-hand);
  font-size: 18px; color: var(--tinte-blass);
  padding: 8px 0;
}

.others-label {
  font-family: var(--schrift-stempel);
  font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--tinte-blass);
  margin: 26px 0 2px;
  display: flex; align-items: center; gap: 9px;
}
.others-label::after { content: ''; flex: 1; height: 1px; background: var(--linie); }

.settle-btn {
  background: none; border: none; cursor: pointer;
  font-family: var(--schrift-hand); font-size: 16px;
  color: var(--rot); text-decoration: underline;
  padding: 4px 2px; flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}

.wer.link { color: var(--tinte); text-decoration: none; }

/* Wenn ein Strich nicht gespeichert werden konnte */
.strich-fehler {
  font-family: var(--schrift-hand);
  font-size: 17px; color: var(--rot);
  text-align: center; padding: 8px 0;
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

  .line-drink { flex: 0 0 29%; font-size: 17px; }
  .line-drink .icon { font-size: 15px; }
  .ink-btn { width: 34px; height: 34px; font-size: 15px; }
}

  </style>
