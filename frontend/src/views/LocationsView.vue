<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Lagerorte</h1>
      <button class="btn btn-primary btn-sm" @click="openCreate(null)">+ Neu</button>
    </div>

    <!-- Collapse-All / Expand-All -->
    <div v-if="tree.length" class="tree-controls">
      <button class="btn btn-secondary btn-sm" @click="doExpandAll"><Icon name="ab" class="icon" />Alle aufklappen</button>
      <button class="btn btn-secondary btn-sm" @click="doCollapseAll"><Icon name="weiter" class="icon" />Alle zuklappen</button>
    </div>

    <div v-if="loading" class="loading">Laden ...</div>

    <div v-else-if="!tree.length" class="empty">
      <Icon name="bauwagen" class="icon" />
      <div>Noch keine Lagerorte angelegt</div>
      <div style="font-size:14px; color:var(--text-muted); margin-top:6px">
        Starte mit dem Anlegen von „Bauwagen" oder „Schopf"
      </div>
      <button class="btn btn-primary" style="margin-top:16px" @click="openCreate(null)">
        Ersten Ort anlegen
      </button>
    </div>

    <div v-else class="tree-root">
      <draggable
        :list="tree"
        item-key="id"
        handle=".drag-handle"
        :animation="150"
        ghost-class="drag-ghost"
        chosen-class="drag-chosen"
        @end="onRootDragEnd"
      >
        <template #item="{ element }">
          <LocationNode :node="element" />
        </template>
      </draggable>
    </div>

    <!-- Modal: Lagerort anlegen / bearbeiten -->
    <!-- Verschieben: Ziel auswählen. Das Backend liefert nur Orte, unter
         denen der Typ erlaubt ist und die nicht im Ort selbst liegen.

         Teleport an den Body: die Seite (.page) hat selbst z-index 1, und
         damit zaehlt fuer alles darin dieser eine Wert gegenueber der
         Navigationsleiste (z-index 100) -- der z-index 200 des Fensters
         half nichts, die Leiste lag trotzdem darueber und verdeckte die
         Knoepfe. Ausserhalb der Seite gilt der Wert wieder direkt. -->
    <Teleport to="body">
    <div v-if="umzug.open" class="modal-backdrop" @click.self="umzug.open = false">
      <div class="modal-box">
        <div class="modal-kopf">
          <h2 class="modal-title">„{{ umzug.name }}" verschieben</h2>
          <!-- Eine Kiste kann unter dem Jahr woanders stehen. Gegenstände
               darin ziehen automatisch mit -- sie bleiben in der Kiste. -->
          <div class="umzug-modus">
            <button
              class="um-seite" :class="{ an: umzug.modus === 'lager' }"
              @click="umzugModus('lager')"
            ><Icon name="zelt" class="icon" />Auf dem Lager</button>
            <button
              class="um-seite" :class="{ an: umzug.modus === 'jahr' }"
              @click="umzugModus('jahr')"
            ><Icon name="haus" class="icon" />Unter dem Jahr</button>
          </div>
          <p class="umzug-hinweis">
            <template v-if="umzug.modus === 'jahr'">
              Wo steht die Kiste außerhalb des Lagers? Ohne Angabe steht sie
              ganzjährig am selben Platz.
            </template>
            <template v-else>
              Wohin auf dem Lager? Die Gegenstände ziehen automatisch mit.
            </template>
          </p>
        </div>

        <div class="modal-inhalt">
        <div v-if="umzug.laedt" class="loading">Ziele werden gesucht …</div>
        <div v-else-if="!umzug.ziele.length" class="empty">
          <Icon name="orte" class="icon" />
          <div class="hinweis">Für diesen Ort gibt es keinen passenden Platz woanders.</div>
        </div>
        <div v-else class="ziel-liste">
          <button
            v-if="umzug.modus === 'jahr'"
            class="ziel" :class="{ an: umzug.zielId === -1 }"
            @click="umzug.zielId = -1"
          >
            <Icon name="haken" class="icon" />
            <span class="ziel-text">
              <span class="ziel-name">Wie auf dem Lager</span>
              <span class="ziel-pfad">steht ganzjährig am selben Platz</span>
            </span>
          </button>
          <button
            v-for="z in umzug.ziele" :key="z.id"
            class="ziel"
            :class="{ an: umzug.zielId === z.id }"
            @click="umzug.zielId = z.id"
          >
            <Icon :name="z.id === 0 ? 'haus' : typIcon(z.type)" class="icon" />
            <span class="ziel-text">
              <span class="ziel-name">{{ z.name }}</span>
              <span v-if="z.breadcrumb" class="ziel-pfad">{{ z.breadcrumb }}</span>
            </span>
          </button>
        </div>

        </div>

        <div class="modal-fuss">
          <div v-if="umzug.error" class="error-msg">{{ umzug.error }}</div>
          <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="umzug.open = false">Abbrechen</button>
          <button
            type="button" class="btn btn-primary"
            :disabled="umzug.zielId === null || umzug.saving"
            @click="umzugAusfuehren"
          >{{ umzug.saving ? '…' : 'Verschieben' }}</button>
          </div>
        </div>
      </div>
    </div>
    </Teleport>

    <Teleport to="body">
    <div v-if="modal.open" class="modal-backdrop" @click.self="modal.open = false">
      <div class="modal-box">
        <div class="modal-kopf">
          <h2 class="modal-title">{{ modal.id ? 'Ort bearbeiten' : 'Neuer Lagerort' }}</h2>
        </div>

        <form class="modal-form" @submit.prevent="saveModal">
        <div class="modal-inhalt">
        <div v-if="allowedTypes.length" class="type-hint">
          <span v-if="modal.form.parent_id">
            Unter <strong>{{ parentName }}</strong> erlaubt:
            <span v-for="t in allowedTypes" :key="t" class="type-chip">{{ typLabel(t) }}</span>
          </span>
          <span v-else>Root-Ebene: Bauwagen, Schopf oder Sonstiges</span>
        </div>
        <div v-else-if="modal.form.parent_id" class="type-hint type-hint-warn">
          Dieser Typ kann keine Unterbereiche haben.
        </div>

          <div class="form-group">
            <label>Name *</label>
            <input v-model="modal.form.name" required placeholder="z.B. Bauwagen, Regal A, Schrank Links ..." />
          </div>

          <div class="form-group">
            <label>Typ</label>
            <div class="type-grid">
              <button
                v-for="t in allowedTypes"
                :key="t"
                type="button"
                class="type-btn"
                :class="{ active: modal.form.type === t }"
                @click="modal.form.type = t"
              >
                <span class="type-btn-icon"><Icon :name="typIcon(t)" class="icon" /></span>
                <span>{{ typLabel(t) }}</span>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>Lagerzustand</label>
            <select v-model="modal.form.storage_mode">
              <option value="both">Immer (Lager &amp; Jahr)</option>
              <option value="lager">Nur Auf dem Lager</option>
              <option value="jahr">Nur Unter dem Jahr</option>
            </select>
          </div>

          <div class="form-group">
            <label>Beschreibung</label>
            <textarea v-model="modal.form.description" placeholder="Optional ..."></textarea>
          </div>

          <div class="coord-row">
            <div class="form-group" style="flex:1"><label>X</label><input v-model.number="modal.form.coordinate_x" type="number" step="0.1" placeholder="0" /></div>
            <div class="form-group" style="flex:1"><label>Y</label><input v-model.number="modal.form.coordinate_y" type="number" step="0.1" placeholder="0" /></div>
            <div class="form-group" style="flex:1"><label>Z</label><input v-model.number="modal.form.coordinate_z" type="number" step="0.1" placeholder="0" /></div>
          </div>

        </div>

        <div class="modal-fuss">
          <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="modal.open = false">Abbrechen</button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="modal.saving || !allowedTypes.includes(modal.form.type)"
            >{{ modal.saving ? '…' : 'Speichern' }}</button>
          </div>
        </div>
        </form>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import draggable from 'vuedraggable'
import {
  getLocationsTree, getLocations,
  createLocation, updateLocation, deleteLocation, reorderLocations,
  getNachfahren, relocateLocation,
} from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import { useExpanded } from '../composables/useExpanded.js'
import LocationNode from '../components/LocationNode.vue'
import LocationWizard from '../components/LocationWizard.vue'
import Icon from '../components/Icon.vue'
import { typIcon, typLabel } from '../utils/orttypen.js'

const { mode } = useMode()
const { expandAll, collapseAll } = useExpanded()

const tree = ref([])
const allLocations = ref([])
const loading = ref(false)

// ── Hierarchie-Regeln ────────────────────────────────────────────
const VALID_CHILDREN = {
  null:      ['bauwagen', 'schopf', 'sonstiges'],
  bauwagen:  ['regal', 'schrank', 'kiste', 'wand'],
  schopf:    ['regal', 'schrank', 'kiste', 'wand'],
  sonstiges: ['regal', 'schrank', 'kiste', 'wand', 'sonstiges'],
  regal:     ['fach'],
  fach:      ['boden'],
  schrank:   ['boden'],
  boden:     ['kiste'],
  kiste:     [],
  wand:      [],
}

// ── Modal ────────────────────────────────────────────────────────
const emptyForm = (parentId = null, parentType = null) => {
  const allowed = VALID_CHILDREN[parentType] ?? VALID_CHILDREN[null]
  return {
    name: '', type: allowed[0] ?? 'bauwagen', storage_mode: 'both',
    parent_id: parentId, description: '',
    coordinate_x: null, coordinate_y: null, coordinate_z: null,
  }
}
const modal = ref({ open: false, id: null, saving: false, error: '', form: emptyForm() })

const allowedTypes = computed(() => {
  const parentId = modal.value.form.parent_id
  if (!parentId) return VALID_CHILDREN[null]
  const parent = allLocations.value.find(l => l.id === parentId)
  return VALID_CHILDREN[parent?.type] ?? VALID_CHILDREN[null]
})
const parentName = computed(() => {
  const parentId = modal.value.form.parent_id
  return allLocations.value.find(l => l.id === parentId)?.name ?? null
})

// ── Daten laden ──────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    ;[tree.value, allLocations.value] = await Promise.all([
      getLocationsTree(mode.value),
      getLocations(),
    ])
  } finally {
    loading.value = false
  }
}

// ── Expand All / Collapse All ────────────────────────────────────
function collectAllIds(nodes) {
  const ids = []
  function walk(node) {
    ids.push(node.id)
    node.children?.forEach(walk)
  }
  nodes.forEach(walk)
  return ids
}
function doExpandAll() { expandAll(collectAllIds(tree.value)) }
function doCollapseAll() { collapseAll(collectAllIds(tree.value)) }

// ── CRUD ─────────────────────────────────────────────────────────
function openCreate(parentId) {
  const parent = parentId ? allLocations.value.find(l => l.id === parentId) : null
  modal.value = { open: true, id: null, saving: false, error: '', form: emptyForm(parentId, parent?.type ?? null) }
}

function openEdit(node) {
  modal.value = {
    open: true, id: node.id, saving: false, error: '',
    form: {
      name: node.name, type: node.type, storage_mode: node.storage_mode || 'both',
      parent_id: node.parent_id, description: node.description || '',
      coordinate_x: node.coordinate_x, coordinate_y: node.coordinate_y, coordinate_z: node.coordinate_z,
    },
  }
}

async function saveModal() {
  modal.value.saving = true
  modal.value.error = ''
  try {
    if (modal.value.id) await updateLocation(modal.value.id, modal.value.form)
    else await createLocation(modal.value.form)
    modal.value.open = false
    await load()
  } catch (e) {
    modal.value.error = e.response?.data?.detail || 'Fehler beim Speichern'
  } finally {
    modal.value.saving = false
  }
}

async function doDelete(node) {
  if (!confirm(`"${node.name}" wirklich loeschen?`)) return
  try {
    await deleteLocation(node.id)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Loeschen')
  }
}

async function doReorder(orderedIds) {
  await reorderLocations(orderedIds)
  // Kein reload nötig — vuedraggable hat die Liste bereits lokal sortiert
}

function onRootDragEnd() {
  doReorder(tree.value.map(n => n.id))
}

// ── Verschieben an einen anderen Elternort ──────────────────────
const umzug = ref({ open: false, id: null, name: '', ziele: [], zielId: null, laedt: false, saving: false, error: '' })

async function openRelocate(node) {
  // Wohin darf dieser Typ? Das sind genau die Eltern-Typen, unter denen er
  // laut Hierarchie erlaubt ist -- plus die oberste Ebene, falls zulässig.
  const erlaubt = Object.entries(VALID_CHILDREN)
    .filter(([, kinder]) => kinder.includes(node.type))
    .map(([elternTyp]) => (elternTyp === 'null' ? '__root__' : elternTyp))

  umzug.value = {
    open: true, id: node.id, name: node.name, modus: 'lager',
    zielId: null, gesperrt: [], erlaubteTypen: erlaubt,
    laedt: true, saving: false, error: '',
  }
  await gesperrteLaden()
}

/** Der Ort selbst und alles darunter darf kein Ziel sein -- sonst Kreis. */
async function gesperrteLaden() {
  umzug.value.laedt = true
  umzug.value.error = ''
  try {
    umzug.value.gesperrt = await getNachfahren(umzug.value.id, umzug.value.modus)
  } catch {
    umzug.value.gesperrt = [umzug.value.id]   // im Zweifel wenigstens sich selbst
  } finally {
    umzug.value.laedt = false
  }
}

async function umzugModus(m) {
  umzug.value.modus = m
  umzug.value.zielId = null
  await gesperrteLaden()
}

async function umzugAusfuehren() {
  umzug.value.saving = true
  umzug.value.error = ''
  try {
    if (umzug.value.modus === 'jahr') {
      // -1 = wie auf dem Lager, also den zweiten Ort wieder entfernen
      const ziel = umzug.value.zielId === -1 ? null : umzug.value.zielId
      await updateLocation(umzug.value.id, { parent_jahr_id: ziel })
    } else {
      await relocateLocation(umzug.value.id, umzug.value.zielId)
    }
    umzug.value.open = false
    await load()
  } catch (e) {
    umzug.value.error = e.response?.data?.detail || 'Verschieben fehlgeschlagen'
  } finally {
    umzug.value.saving = false
  }
}

// ── Handlers via provide() an LocationNode weitergeben ───────────
provide('locHandlers', {
  onCreate:   openCreate,
  onEdit:     openEdit,
  onDelete:   doDelete,
  onReorder:  doReorder,
  onRelocate: openRelocate,
})

onMounted(load)
</script>

<style scoped>
.tree-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
.tree-root {
  padding-bottom: 8px;
}

/* Typ-Auswahl */


/* Modal */
/* Der Speichern-Knopf lag auf dem Handy unter der Navigationsleiste.
   Erster Versuch mit position:sticky und negativem bottom war falsch --
   damit klebt er unterhalb des sichtbaren Bereichs. Jetzt eine feste
   Aufteilung: Kopf oben, Inhalt scrollt, Knöpfe unverrückbar am Fuß. */

</style>

<!-- Nicht scoped: die Fenster haengen per Teleport am Body und lagen
     damit ausserhalb der Reichweite der scoped-Regeln. -->
<style>
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: flex-end;
  /* über der Navigationsleiste, die bei z-index 100 liegt */
  z-index: 200;
  /* Begrenzt das Fenster auch dann, wenn der Browser die dvh-Einheit
     unten nicht kennt -- sonst wächst es über den Bildschirm hinaus und
     die Knöpfe sind gar nicht mehr erreichbar. Genau das ist passiert. */
  overflow: hidden;
}
.modal-box {
  background: var(--white);
  border-radius: var(--radius) var(--radius) 0 0;
  width: 100%;
  /* Drei Stufen, absichtlich in dieser Reihenfolge:
     100% greift immer (der Backdrop ist so hoch wie der Bildschirm),
     88vh lässt oben etwas Luft, 88dvh berücksichtigt zusätzlich die
     ein- und ausfahrende Adressleiste. Kennt ein Browser eine Einheit
     nicht, überspringt er nur diese Zeile. */
  max-height: 100%;
  max-height: 88vh;
  max-height: 88dvh;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-form { display: flex; flex-direction: column; min-height: 0; flex: 1; }
.modal-kopf { padding: 20px 22px 0; flex-shrink: 0; }
.modal-inhalt {
  flex: 1; min-height: 0;
  overflow-y: auto;
  padding: 12px 22px 8px;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}
.modal-fuss {
  flex-shrink: 0;
  /* nie zusammenfallen lassen, egal wie lang das Formular ist */
  min-height: fit-content;
  padding: 12px 22px calc(14px + env(safe-area-inset-bottom, 0px));
  background: var(--white);
  box-shadow: 0 -8px 14px -10px rgba(48, 26, 8, 0.3);
}
.modal-title { font-size: 22px; font-weight: 700; }
.modal-actions { display: flex; gap: 10px; }
.modal-actions .btn { flex: 1; }
.umzug-hinweis { font-size: 15px; color: var(--tinte-blass); margin-top: 10px; line-height: 1.4; }
.umzug-modus { display: flex; gap: 7px; margin-top: 12px; }
.um-seite {
  flex: 1; display: inline-flex; align-items: center; justify-content: center;
  gap: 6px; padding: 10px 8px; min-height: 44px;
  border: 1.5px solid var(--linie); border-radius: var(--radius-sm);
  background: transparent; color: var(--tinte-blass);
  font-family: var(--schrift-stempel);
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.07em;
  cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.um-seite.an { color: var(--gebrannt); border-color: var(--gebrannt); background: rgba(53,29,8,.07); }
.um-seite .icon { font-size: 15px; }
.ziel-liste { display: flex; flex-direction: column; gap: 7px; }
.ziel {
  display: flex; align-items: center; gap: 11px;
  padding: 12px 13px; min-height: 56px;
  border: 1.5px solid var(--linie); border-radius: var(--radius-sm);
  background: transparent; color: var(--tinte);
  text-align: left; cursor: pointer; width: 100%;
  -webkit-tap-highlight-color: transparent;
}
.ziel.an { border-color: var(--gebrannt); background: rgba(53,29,8,.08); }
.ziel.gleich { margin-bottom: 14px; }
.ziel .icon { font-size: 21px; color: var(--gebrannt); flex-shrink: 0; }
.ziel-text { display: flex; flex-direction: column; min-width: 0; }
.ziel-name { font-weight: 600; font-size: 16px; }
.ziel-pfad { font-family: var(--schrift-hand); font-size: 14.5px; color: var(--tinte-blass); }
.type-hint {
  font-size: 13px; color: var(--text-muted);
  background: var(--cream); border-radius: var(--radius-sm);
  padding: 8px 12px; margin-bottom: 14px;
}
.type-hint-warn { background: var(--rot-blass); color: var(--rot); }
.type-chip {
  display: inline-block; margin: 0 3px; padding: 1px 7px;
  border-radius: 999px; background: var(--green-pale); color: var(--green);
  font-size: 12px; font-weight: 700;
}
.type-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.type-btn {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 14px; border: 2px solid var(--border); border-radius: var(--radius-sm);
  background: var(--white); cursor: pointer; font-size: 14px; font-weight: 600;
  min-width: 72px; transition: all 0.15s; -webkit-tap-highlight-color: transparent;
}
.type-btn.active { border-color: var(--green); background: var(--green-pale); color: var(--green); }
.type-btn-icon { font-size: 24px; }
.coord-row { display: flex; gap: 8px; }
.error-msg { color: var(--rot); font-size: 14px; margin-top: 6px; }
</style>
