<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Einkaufsliste</h1>
      <button v-if="erledigte.length" class="btn btn-secondary btn-sm" @click="clearDone">
        Erledigt löschen
      </button>
    </div>

    <!-- Neuen Eintrag hinzufügen -->
    <div class="card add-card">
      <div class="form-group">
        <label>Was kaufen?</label>
        <input v-model="newForm.name" placeholder="z.B. Schrauben M6, Klebeband ..." @keyup.enter="addItem" />
      </div>
      <div class="qty-row">
        <div class="form-group" style="flex:1">
          <label>Menge</label>
          <input v-model.number="newForm.quantity" type="number" min="0.5" step="0.5" />
        </div>
        <div class="form-group" style="flex:1">
          <label>Einheit</label>
          <select v-model="newForm.unit">
            <option>Stück</option>
            <option>Meter</option>
            <option>Liter</option>
            <option>kg</option>
            <option>Rolle</option>
            <option>Paar</option>
            <option>Satz</option>
            <option>Packung</option>
          </select>
        </div>
      </div>
      <div class="form-group" style="margin-bottom:0">
        <label>Dringlichkeit</label>
        <div class="urgency-row">
          <button
            v-for="u in urgencies" :key="u.value"
            type="button"
            class="urgency-btn"
            :class="[u.value, { active: newForm.urgency === u.value }]"
            @click="newForm.urgency = u.value"
          >{{ u.label }}</button>
        </div>
      </div>
      <button class="btn btn-primary" style="margin-top:14px; width:100%" @click="addItem" :disabled="!newForm.name.trim()">
        + Hinzufügen
      </button>
    </div>

    <div v-if="loading" class="loading">Laden ...</div>

    <template v-else>
      <!-- Offene Einträge -->
      <div v-if="offene.length" style="margin-top: 14px;">
        <div
          v-for="item in offene" :key="item.id"
          class="shopping-item card"
          :class="item.urgency"
        >
          <div class="item-main">
            <button class="check-btn" @click="toggleDone(item)">
              <span>{{ item.erledigt ? '✓' : '' }}</span>
            </button>
            <div class="item-info">
              <div class="item-name">{{ item.name }}</div>
              <div class="item-meta">
                {{ item.quantity }} {{ item.unit }}
                <span class="urgency-tag" :class="item.urgency">{{ urgencyLabel(item.urgency) }}</span>
              </div>
              <div v-if="item.notes" class="item-notes">{{ item.notes }}</div>
            </div>
            <button class="delete-btn" @click="remove(item)">✕</button>
          </div>
        </div>
      </div>

      <div v-if="!offene.length && !erledigte.length" class="empty">
        <div style="font-size: 40px; margin-bottom: 8px;">🛒</div>
        <div>Die Einkaufsliste ist leer.</div>
      </div>

      <!-- Erledigte -->
      <div v-if="erledigte.length" style="margin-top: 20px;">
        <div class="section-title">Erledigt</div>
        <div
          v-for="item in erledigte" :key="item.id"
          class="shopping-item card done"
        >
          <div class="item-main">
            <button class="check-btn done" @click="toggleDone(item)">
              <span>✓</span>
            </button>
            <div class="item-info">
              <div class="item-name done-text">{{ item.name }}</div>
              <div class="item-meta">{{ item.quantity }} {{ item.unit }}</div>
            </div>
            <button class="delete-btn" @click="remove(item)">✕</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getShoppingItems, createShoppingItem, updateShoppingItem, deleteShoppingItem, clearErledigte } from '../api/index.js'

const items = ref([])
const loading = ref(false)

const urgencies = [
  { value: 'niedrig', label: 'Niedrig' },
  { value: 'mittel', label: 'Mittel' },
  { value: 'hoch', label: 'Hoch' },
  { value: 'dringend', label: 'Dringend!' },
]

const newForm = ref({ name: '', quantity: 1, unit: 'Stück', urgency: 'mittel' })

const offene = computed(() => items.value.filter(i => !i.erledigt))
const erledigte = computed(() => items.value.filter(i => i.erledigt))

function urgencyLabel(u) {
  return urgencies.find(x => x.value === u)?.label ?? u
}

async function load() {
  loading.value = true
  try { items.value = await getShoppingItems() }
  finally { loading.value = false }
}

async function addItem() {
  if (!newForm.value.name.trim()) return
  const created = await createShoppingItem({ ...newForm.value })
  items.value.unshift(created)
  newForm.value.name = ''
  newForm.value.quantity = 1
  newForm.value.urgency = 'mittel'
  await load()
}

async function toggleDone(item) {
  const updated = await updateShoppingItem(item.id, { erledigt: !item.erledigt })
  const idx = items.value.findIndex(i => i.id === item.id)
  if (idx !== -1) items.value[idx] = updated
  await load()
}

async function remove(item) {
  await deleteShoppingItem(item.id)
  items.value = items.value.filter(i => i.id !== item.id)
}

async function clearDone() {
  if (!confirm('Alle erledigten Einträge löschen?')) return
  await clearErledigte()
  await load()
}

onMounted(load)
</script>

<style scoped>
.add-card { margin-bottom: 4px; }
.qty-row { display: flex; gap: 12px; }

.urgency-row { display: flex; gap: 8px; flex-wrap: wrap; }
.urgency-btn {
  padding: 7px 14px; border-radius: 8px; border: 2px solid var(--border);
  background: var(--white); color: var(--text-muted); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; -webkit-tap-highlight-color: transparent;
}
.urgency-btn.active.niedrig  { background: #1a3a1a; border-color: #4caf50; color: #4caf50; }
.urgency-btn.active.mittel   { background: #1a2e3a; border-color: #2196f3; color: #2196f3; }
.urgency-btn.active.hoch     { background: #3a2a1a; border-color: #ff9800; color: #ff9800; }
.urgency-btn.active.dringend { background: #3a1a1a; border-color: #f44336; color: #f44336; }

.shopping-item { margin-bottom: 8px; }
.shopping-item.hoch     { border-left: 3px solid #ff9800; }
.shopping-item.dringend { border-left: 3px solid #f44336; }
.shopping-item.mittel   { border-left: 3px solid #2196f3; }
.shopping-item.niedrig  { border-left: 3px solid #4caf50; }
.shopping-item.done     { border-left: 3px solid var(--border); opacity: 0.6; }

.item-main { display: flex; align-items: center; gap: 12px; }

.check-btn {
  width: 36px; height: 36px; flex-shrink: 0; border-radius: 8px;
  border: 2px solid var(--border); background: var(--white);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700; color: var(--green);
  cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.check-btn.done { background: #1a3a1a; border-color: #4caf50; }

.item-info { flex: 1; min-width: 0; }
.item-name { font-size: 17px; font-weight: 700; }
.item-name.done-text { text-decoration: line-through; color: var(--text-muted); }
.item-meta { font-size: 13px; color: var(--text-muted); margin-top: 3px; display: flex; align-items: center; gap: 8px; }
.item-notes { font-size: 13px; color: var(--text-muted); margin-top: 3px; }

.urgency-tag {
  font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 999px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.urgency-tag.niedrig  { background: #1a3a1a; color: #4caf50; }
.urgency-tag.mittel   { background: #1a2e3a; color: #2196f3; }
.urgency-tag.hoch     { background: #3a2a1a; color: #ff9800; }
.urgency-tag.dringend { background: #3a1a1a; color: #f44336; }

.delete-btn {
  width: 32px; height: 32px; flex-shrink: 0; border-radius: 6px;
  border: none; background: transparent; color: var(--text-muted);
  font-size: 16px; cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.delete-btn:active { background: rgba(255,255,255,0.08); }

.section-title {
  font-size: 13px; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
}

.empty { text-align: center; color: var(--text-muted); padding: 40px 20px; }
</style>
