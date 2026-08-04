<template>
  <div class="page">
    <div class="page-header">
      <button class="btn btn-secondary btn-sm" @click="$router.back()"><Icon name="zurueck" class="icon" />Zurück</button>
      <h1 class="page-title">{{ isEdit ? 'Bearbeiten' : 'Neu' }}</h1>
    </div>

    <div v-if="loading" class="loading">Laden …</div>

    <form v-else @submit.prevent="save">

      <!-- Foto: geht jetzt schon beim Anlegen. Der Upload braucht eine
           Gegenstands-Nummer, deshalb wird das Bild bis zum Speichern
           vorgehalten und direkt danach hochgeladen. -->
      <div class="card foto-karte">
        <div class="foto-vorschau" :class="{ leer: !vorschau }" @click="galerieOeffnen">
          <img v-if="vorschau" :src="vorschau" alt="Vorschau" />
          <template v-else>
            <Icon name="kamera" class="icon gross" />
            <span class="foto-hinweis">Foto aufnehmen oder auswählen</span>
          </template>
        </div>
        <div class="foto-knoepfe">
          <button type="button" class="btn btn-secondary btn-sm" @click="kameraOeffnen">
            <Icon name="kamera" class="icon" />Aufnehmen
          </button>
          <button type="button" class="btn btn-secondary btn-sm" @click="galerieOeffnen">
            <Icon name="orte" class="icon" />Auswählen
          </button>
          <button v-if="vorschau" type="button" class="btn btn-sm btn-danger" @click="fotoEntfernen">
            <Icon name="muell" class="icon" />Entfernen
          </button>
        </div>
        <!-- Zwei getrennte Eingaben: mit "capture" öffnet iOS direkt die
             Kamera und lässt gar keine Auswahl aus der Mediathek zu.
             Deshalb ein zweites Feld ohne capture zum Auswählen. -->
        <input ref="kameraEingabe" type="file" accept="image/*" capture="environment"
               style="display:none" @change="fotoGewaehlt" />
        <input ref="galerieEingabe" type="file" accept="image/*"
               style="display:none" @change="fotoGewaehlt" />
        <div v-if="fotoFehler" class="error-msg" style="margin-top:8px">{{ fotoFehler }}</div>
      </div>

      <!-- Basis-Infos -->
      <div class="card" style="margin-top: 14px;">
        <div class="form-group">
          <label>Name *</label>
          <input v-model="form.name" required placeholder="z.B. Akkuschrauber" />
        </div>
        <div class="form-group">
          <label>Kategorie</label>
          <!-- Freitext mit Vorschlägen: so entstehen neue Kategorien beim
               Tippen, und vorhandene lassen sich mit einem Tipp übernehmen -->
          <input v-model="form.category" list="kategorie-liste" placeholder="z.B. Werkzeug" />
          <datalist id="kategorie-liste">
            <option v-for="k in kategorien" :key="k" :value="k" />
          </datalist>
          <div v-if="kategorien.length" class="vorschlaege scrollbar">
            <button
              v-for="k in kategorien" :key="k"
              type="button" class="vorschlag"
              :class="{ an: form.category === k }"
              @click="form.category = form.category === k ? '' : k"
            >{{ k }}</button>
          </div>
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
      </div>

      <!-- Lagerort Auf dem Lager -->
      <div class="card loc-card" style="margin-top: 14px;">
        <div class="loc-card-header">
          <span class="loc-card-title"><Icon name="zelt" class="icon" />Auf dem Lager</span>
        </div>

        <div class="aufgebaut-row" @click="form.aufgebaut = !form.aufgebaut">
          <div class="aufgebaut-check" :class="{ active: form.aufgebaut }">
            <Icon v-if="form.aufgebaut" name="haken" class="icon" />
          </div>
          <div>
            <div class="aufgebaut-label">Aufgebaut während dem Lager</div>
            <div class="aufgebaut-hint">statt einem fixen Lagerort</div>
          </div>
        </div>

        <div v-if="form.aufgebaut" style="margin-top: 12px;">
          <label>Wo aufgebaut / Notiz</label>
          <input v-model="form.aufgebaut_notiz" placeholder="z.B. Werkstattzelt, Zeltdorf …" />
        </div>

        <div v-else style="margin-top: 12px;">
          <LocationWizard v-model="form.location_lager_id" :locations="allLocations" />
        </div>
      </div>

      <!-- Lagerort Unter dem Jahr -->
      <div class="card" style="margin-top: 14px;">
        <div class="loc-card-header">
          <span class="loc-card-title"><Icon name="haus" class="icon" />Unter dem Jahr</span>
        </div>
        <div style="margin-top: 12px;">
          <LocationWizard v-model="form.location_jahr_id" :locations="allLocations" />
        </div>
      </div>

      <!-- Zusatz-Infos -->
      <div class="card" style="margin-top: 14px;">
        <div class="form-group">
          <label>Beschreibung</label>
          <textarea v-model="form.description" placeholder="Optionale Beschreibung …"></textarea>
        </div>

        <div class="form-group">
          <label>Tags</label>
          <div v-if="gewaehlteTags.length" class="tag-reihe">
            <button
              v-for="t in gewaehlteTags" :key="t"
              type="button" class="tag-marke" @click="tagEntfernen(t)"
            >{{ t }}<Icon name="schliessen" class="icon" /></button>
          </div>
          <input
            v-model="tagEingabe"
            placeholder="Tag eingeben und Enter"
            @keydown.enter.prevent="tagAusEingabe"
            @keydown.,.prevent="tagAusEingabe"
          />
          <div v-if="offeneVorschlaege.length" class="vorschlaege scrollbar">
            <button
              v-for="t in offeneVorschlaege" :key="t"
              type="button" class="vorschlag" @click="tagHinzufuegen(t)"
            >+ {{ t }}</button>
          </div>
          <div v-else-if="tagEingabe.trim()" class="tag-leer">
            Kein vorhandener Tag passt — Enter legt „{{ tagEingabe.trim() }}" neu an.
          </div>
        </div>

        <div class="form-group" style="margin-bottom:0">
          <label>Notizen</label>
          <textarea v-model="form.notes" placeholder="Weitere Hinweise …"></textarea>
        </div>
      </div>

      <div v-if="error" class="error-msg" style="margin-top: 10px;">{{ error }}</div>

      <button type="submit" class="btn btn-primary btn-lg" style="width:100%; margin-top:14px" :disabled="saving">
        <Icon name="speichern" class="icon" />{{ saving ? saveSchritt : 'Speichern' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getItem, createItem, updateItem, getLocations,
  getCategories, getTags, uploadImage, deleteImage,
} from '../api/index.js'
import LocationWizard from '../components/LocationWizard.vue'
import Icon from '../components/Icon.vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id
const isEdit = !!id && route.path.includes('/edit')

const MAX_MB = 12

const form = ref({
  name: '', category: '', quantity: 1, unit: 'Stück', storage_mode: 'both',
  location_lager_id: null, location_jahr_id: null,
  aufgebaut: false, aufgebaut_notiz: '',
  description: '', tags: '', notes: '',
})
const allLocations = ref([])
const kategorien = ref([])
const alleTags = ref([])
const loading = ref(false)
const saving = ref(false)
const saveSchritt = ref('Speichern …')
const error = ref('')

// ── Foto ──
const kameraEingabe = ref(null)
const galerieEingabe = ref(null)
const gewaehlteDatei = ref(null)     // wird erst nach dem Speichern hochgeladen
const vorschau = ref('')             // Data-URL oder vorhandener Bildpfad
const fotoFehler = ref('')
const fotoGeloescht = ref(false)

// ── Tags als Marken statt als Kommatext ──
const tagEingabe = ref('')
const gewaehlteTags = computed(() =>
  (form.value.tags || '').split(',').map(t => t.trim()).filter(Boolean)
)
// Alle vorhandenen Tags anbieten, nicht nur eine Auswahl -- sonst findet
// man genau den nicht, den man sucht. Die Liste bekommt stattdessen eine
// Höhenbegrenzung und scrollt bei Bedarf.
const offeneVorschlaege = computed(() => {
  const schon = new Set(gewaehlteTags.value.map(t => t.toLowerCase()))
  const suche = tagEingabe.value.trim().toLowerCase()
  return alleTags.value
    .filter(t => !schon.has(t.toLowerCase()))
    .filter(t => !suche || t.toLowerCase().includes(suche))
})

function setzeTags(liste) {
  form.value.tags = liste.join(', ')
}
function tagHinzufuegen(t) {
  const sauber = t.trim()
  if (!sauber) return
  if (gewaehlteTags.value.some(x => x.toLowerCase() === sauber.toLowerCase())) return
  setzeTags([...gewaehlteTags.value, sauber])
  tagEingabe.value = ''
}
function tagAusEingabe() {
  tagHinzufuegen(tagEingabe.value)
}
function tagEntfernen(t) {
  setzeTags(gewaehlteTags.value.filter(x => x !== t))
}

function kameraOeffnen() {
  fotoFehler.value = ''
  kameraEingabe.value?.click()
}
function galerieOeffnen() {
  fotoFehler.value = ''
  galerieEingabe.value?.click()
}

function fotoGewaehlt(e) {
  const datei = e.target.files?.[0]
  if (!datei) return
  if (!datei.type.startsWith('image/')) {
    fotoFehler.value = 'Bitte ein Bild auswählen'
    return
  }
  if (datei.size > MAX_MB * 1024 * 1024) {
    fotoFehler.value = `Das Bild ist zu groß (max. ${MAX_MB} MB)`
    return
  }
  gewaehlteDatei.value = datei
  fotoGeloescht.value = false
  const leser = new FileReader()
  leser.onload = () => { vorschau.value = leser.result }
  leser.readAsDataURL(datei)
  // zurücksetzen, sonst löst dieselbe Datei beim zweiten Mal kein change aus
  e.target.value = ''
}

function fotoEntfernen() {
  gewaehlteDatei.value = null
  vorschau.value = ''
  fotoFehler.value = ''
  fotoGeloescht.value = true
  if (kameraEingabe.value) kameraEingabe.value.value = ''
  if (galerieEingabe.value) galerieEingabe.value.value = ''
}

async function load() {
  loading.value = true
  try {
    const [orte, kats, tags] = await Promise.all([
      getLocations(), getCategories(), getTags(),
    ])
    allLocations.value = orte
    kategorien.value = kats
    alleTags.value = tags
    if (isEdit) {
      const item = await getItem(id)
      form.value = { ...item, aufgebaut_notiz: item.aufgebaut_notiz || '', tags: item.tags || '' }
      if (item.image_path) vorschau.value = '/images/' + item.image_path
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  saveSchritt.value = 'Speichern …'
  error.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.category) payload.category = null
    if (!payload.tags) payload.tags = null
    if (!payload.aufgebaut_notiz) payload.aufgebaut_notiz = null
    if (payload.aufgebaut) payload.location_lager_id = null

    const saved = isEdit ? await updateItem(id, payload) : await createItem(payload)

    // Das Bild braucht die Nummer des Gegenstands, geht also erst jetzt.
    if (gewaehlteDatei.value) {
      saveSchritt.value = 'Foto wird geladen …'
      try {
        await uploadImage(saved.id, gewaehlteDatei.value)
      } catch {
        // Der Gegenstand ist gespeichert -- das soll ein Bildfehler nicht
        // zunichte machen. Nachtragen geht in der Detailansicht.
        error.value = 'Gespeichert, aber das Foto konnte nicht geladen werden.'
      }
    } else if (isEdit && fotoGeloescht.value) {
      try { await deleteImage(saved.id) } catch { /* nicht kritisch */ }
    }

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
.error-msg { color: var(--rot); font-size: 15px; }

.loc-card-header { margin-bottom: 4px; }
.loc-card-title {
  font-family: var(--schrift-stempel);
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.11em;
  color: var(--tinte-blass);
  display: inline-flex; align-items: center; gap: 6px;
}

/* ── Foto ── */
.foto-karte { display: flex; flex-direction: column; gap: 12px; }
.foto-vorschau {
  aspect-ratio: 4 / 3;
  max-height: 260px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px;
  cursor: pointer;
  background: var(--blatt-tief);
  -webkit-tap-highlight-color: transparent;
}
.foto-vorschau.leer {
  background:
    repeating-linear-gradient(45deg, rgba(53,29,8,.04) 0 6px, transparent 6px 12px),
    var(--blatt-tief);
  border: 1.5px dashed var(--linie-stark);
  color: var(--tinte-blass);
}
.foto-vorschau img { width: 100%; height: 100%; object-fit: cover; }
.foto-vorschau .gross { font-size: 40px; opacity: 0.65; }
.foto-hinweis { font-family: var(--schrift-hand); font-size: 18px; }
.foto-knoepfe { display: flex; gap: 8px; flex-wrap: wrap; }
.foto-knoepfe .btn { flex: 1; min-width: 130px; }

/* ── Vorschläge für Kategorie und Tags ── */
.vorschlaege { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
/* Bei vielen Tags wird die Liste sonst endlos -- lieber scrollen lassen. */
.vorschlaege.scrollbar { max-height: 132px; overflow-y: auto; padding-right: 2px; }
.tag-leer {
  margin-top: 8px; font-size: 14px; color: var(--tinte-blass); line-height: 1.35;
}
.vorschlag {
  padding: 6px 11px; min-height: 36px;
  border: 1px solid var(--linie); border-radius: var(--radius-sm);
  background: transparent; color: var(--tinte-blass);
  font-family: var(--schrift-stempel);
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.08em;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.vorschlag.an { color: var(--gebrannt); border-color: var(--gebrannt); background: rgba(53,29,8,.07); }

.tag-reihe { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tag-marke {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 10px; min-height: 36px;
  border: 1.5px solid var(--gebrannt); border-radius: var(--radius-sm);
  background: rgba(53,29,8,.07); color: var(--gebrannt);
  font-family: var(--schrift-hand); font-size: 16px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.tag-marke .icon { font-size: 13px; opacity: 0.7; }

/* ── Aufgebaut ── */
.aufgebaut-row {
  display: flex; align-items: center; gap: 14px;
  cursor: pointer; padding: 10px 0 6px;
  -webkit-tap-highlight-color: transparent;
}
.aufgebaut-check {
  width: 34px; height: 34px; border-radius: var(--radius-sm);
  border: 2px solid var(--tinte); background: transparent;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: var(--tinte);
  flex-shrink: 0; transition: all 0.15s;
}
.aufgebaut-check.active { background: rgba(53,29,8,.09); }
.aufgebaut-label { font-size: 17px; font-weight: 600; }
.aufgebaut-hint { font-size: 13px; color: var(--tinte-blass); margin-top: 2px; }
</style>
