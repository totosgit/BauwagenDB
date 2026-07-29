<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Einkauf</h1>
      <button v-if="erledigte.length" class="btn btn-secondary btn-sm" @click="clearDone">
        Erledigt weg
      </button>
    </div>

    <!-- Neuen Eintrag aufschreiben -->
    <div class="card">
      <div class="form-group">
        <label>Was besorgen?</label>
        <input v-model="newForm.name" placeholder="z.B. Schrauben M6, Klebeband …" @keyup.enter="addItem" />
      </div>
      <div class="menge-reihe">
        <div class="form-group" style="flex:1">
          <label>Menge</label>
          <input v-model.number="newForm.quantity" type="number" min="0.5" step="0.5" />
        </div>
        <div class="form-group" style="flex:1.3">
          <label>Einheit</label>
          <select v-model="newForm.unit">
            <option>Stück</option><option>Meter</option><option>Liter</option>
            <option>kg</option><option>Rolle</option><option>Paar</option>
            <option>Satz</option><option>Packung</option><option>Kasten</option>
          </select>
        </div>
      </div>
      <div class="form-group" style="margin-bottom:0">
        <label>Wie dringend?</label>
        <div class="stufen">
          <button
            v-for="u in urgencies" :key="u.value"
            type="button"
            class="stufe"
            :class="[u.value, { an: newForm.urgency === u.value }]"
            @click="newForm.urgency = u.value"
          >{{ u.label }}</button>
        </div>
      </div>
      <button class="btn btn-primary" style="margin-top:14px; width:100%" @click="addItem" :disabled="!newForm.name.trim()">
        <Icon name="plus" class="icon" />Auf die Liste setzen
      </button>
    </div>

    <div v-if="loading" class="loading">Laden …</div>

    <template v-else>
      <!-- Offene Einträge -->
      <template v-if="offene.length">
        <div class="section-label">Noch zu besorgen</div>
        <div
          v-for="item in offene" :key="item.id"
          class="item-row"
          :class="item.urgency"
        >
          <button class="kaestchen" @click="toggleDone(item)" aria-label="Als erledigt markieren" />
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-meta">
              <span class="menge">{{ item.quantity }} {{ item.unit }}</span>
              <span class="urheber"><Icon name="profil" class="icon" />{{ item.author }}</span>
            </div>
            <div v-if="item.notes" class="notiz-zusatz">{{ item.notes }}</div>
          </div>
          <span v-if="item.urgency === 'dringend' || item.urgency === 'hoch'"
                class="tag" :class="{ 'tag-rot': item.urgency === 'dringend' }">
            {{ urgencyLabel(item.urgency) }}
          </span>
          <button class="loeschen" @click="remove(item)" aria-label="Vom Zettel streichen">
            <Icon name="schliessen" class="icon" />
          </button>
        </div>
      </template>

      <div v-if="!offene.length && !erledigte.length" class="empty">
        <Icon name="einkauf" class="icon" />
        <div class="hinweis">Nichts zu besorgen</div>
      </div>

      <!-- Erledigte -->
      <template v-if="erledigte.length">
        <div class="section-label">Erledigt</div>
        <div v-for="item in erledigte" :key="item.id" class="item-row erledigt">
          <button class="kaestchen an" @click="toggleDone(item)" aria-label="Doch noch offen">
            <Icon name="haken" class="icon" />
          </button>
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-meta">
              <span class="menge">{{ item.quantity }} {{ item.unit }}</span>
              <span class="urheber"><Icon name="profil" class="icon" />{{ item.author }}</span>
            </div>
          </div>
          <button class="loeschen" @click="remove(item)" aria-label="Vom Zettel streichen">
            <Icon name="schliessen" class="icon" />
          </button>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getShoppingItems, createShoppingItem, updateShoppingItem, deleteShoppingItem, clearErledigte } from '../api/index.js'
import Icon from '../components/Icon.vue'

const items = ref([])
const loading = ref(false)

const urgencies = [
  { value: 'niedrig', label: 'Niedrig' },
  { value: 'mittel', label: 'Mittel' },
  { value: 'hoch', label: 'Hoch' },
  { value: 'dringend', label: 'Dringend' },
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
  await createShoppingItem({ ...newForm.value })
  newForm.value.name = ''
  newForm.value.quantity = 1
  newForm.value.urgency = 'mittel'
  await load()
}

async function toggleDone(item) {
  await updateShoppingItem(item.id, { erledigt: !item.erledigt })
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
.menge-reihe { display: flex; gap: 14px; }

/* Dringlichkeit: gestempelte Marken, nicht bunte Pillen */
.stufen { display: flex; gap: 7px; flex-wrap: wrap; }
.stufe {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--linie);
  background: transparent;
  color: var(--tinte-blass);
  font-family: var(--schrift-stempel);
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  cursor: pointer;
  min-height: 40px;
  -webkit-tap-highlight-color: transparent;
}
.stufe.an {
  color: var(--gebrannt);
  border-color: var(--gebrannt);
  background: rgba(53, 29, 8, 0.07);
}
.stufe.an.dringend { color: var(--rot); border-color: var(--rot); background: var(--rot-blass); }

/* Dringende Zeilen bekommen einen roten Rotstift-Strich an den Rand */
.item-row.dringend { box-shadow: inset 3px 0 0 var(--rot); padding-left: 10px; }
.item-row.hoch { box-shadow: inset 3px 0 0 rgba(158, 58, 34, 0.4); padding-left: 10px; }

.kaestchen {
  width: 26px; height: 26px; flex-shrink: 0;
  border: 2px solid var(--tinte);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--tinte);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 15px; padding: 0;
  -webkit-tap-highlight-color: transparent;
}
.kaestchen .icon { stroke-width: 2.6; }

.erledigt .item-name { text-decoration: line-through; opacity: 0.45; }
.erledigt .item-meta { opacity: 0.45; }
.erledigt .kaestchen { opacity: 0.55; }

.notiz-zusatz {
  font-family: var(--schrift-hand);
  font-size: 16px;
  color: var(--tinte-blass);
  margin-top: 2px;
}

.loeschen {
  border: none; background: none; cursor: pointer;
  color: var(--tinte-blass);
  font-size: 15px; padding: 6px;
  display: flex; align-items: center; flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}
.loeschen:active { color: var(--rot); }
</style>
