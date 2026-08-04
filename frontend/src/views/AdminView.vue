<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Verwaltung</h1>
    </div>

    <div class="admin-tabs">
      <button :class="{ active: tab === 'freigaben' }" @click="tab = 'freigaben'">
        Freigaben
        <span v-if="pending.length" class="pill">{{ pending.length }}</span>
      </button>
      <button :class="{ active: tab === 'personen' }" @click="tab = 'personen'">Personen</button>
      <button :class="{ active: tab === 'gruppen' }" @click="tab = 'gruppen'">Gruppen</button>
      <button :class="{ active: tab === 'kategorien' }" @click="tab = 'kategorien'">Kategorien</button>
    </div>

    <!-- Die Lagerorte sind aus der Navigation hierher gewandert: man legt sie
         selten an, braucht sie aber täglich als Angabe am Gegenstand. -->
    <router-link to="/locations" class="card ortverwaltung">
      <Icon name="orte" class="icon gross" />
      <span class="ov-text">
        <span class="ov-titel">Lagerorte verwalten</span>
        <span class="ov-unter">Bauwagen, Regale, Fächer und Kisten anlegen und umbauen</span>
      </span>
      <Icon name="weiter" class="icon" />
    </router-link>

    <!-- Abrechnung: erst sichern, dann leeren. Auf der Strichliste selbst
         sieht jeder nur seinen eigenen Zettel -- die Gesamtübersicht ist
         genau dieses PDF. -->
    <div class="card abrechnung">
      <div class="ab-kopf">
        <Icon name="pdf" class="icon gross" />
        <span class="ov-text">
          <span class="ov-titel">Getränke-Abrechnung</span>
          <span class="ov-unter">
            <template v-if="strichSumme === null">Wird geladen …</template>
            <template v-else-if="strichSumme === 0">Zurzeit sind keine Striche gesetzt.</template>
            <template v-else>
              {{ strichSumme }} {{ strichSumme === 1 ? 'Strich' : 'Striche' }}
              von {{ personenMitStrichen }} {{ personenMitStrichen === 1 ? 'Person' : 'Personen' }}
            </template>
          </span>
        </span>
      </div>

      <div class="ab-knoepfe">
        <button class="btn btn-primary" :disabled="!strichSumme || exportiert" @click="exportPDF">
          <Icon name="pdf" class="icon" />{{ exportiert ? 'Erstellt …' : 'Als PDF sichern' }}
        </button>
        <button class="btn btn-danger" :disabled="!strichSumme || leert" @click="alleZuruecksetzen">
          <Icon name="muell" class="icon" />{{ leert ? 'Läuft …' : 'Alles auf null' }}
        </button>
      </div>
      <p class="ab-hinweis">
        Erst das PDF sichern, dann zurücksetzen – gelöschte Striche lassen sich
        nicht wiederherstellen.
      </p>
      <div v-if="abMeldung" class="hint ok">{{ abMeldung }}</div>
    </div>

    <div v-if="loading" class="loading">Laden ...</div>

    <!-- ===== FREIGABEN ===== -->
    <template v-else-if="tab === 'freigaben'">
      <div v-if="!pending.length" class="empty">
        <Icon name="haken" class="icon" />
        <div class="hinweis">Keine offenen Registrierungen</div>
      </div>
      <div v-for="u in pending" :key="u.id" class="card row-card">
        <div style="flex:1; min-width:0">
          <div class="row-name">{{ u.display_name }}</div>
          <div class="row-meta">@{{ u.username }}</div>
        </div>
        <button class="btn btn-primary btn-sm" @click="approve(u)">
          <Icon name="haken" class="icon" />Freigeben
        </button>
        <button class="btn btn-sm btn-reject" @click="removeUser(u)">Ablehnen</button>
      </div>
    </template>

    <!-- ===== PERSONEN ===== -->
    <template v-else-if="tab === 'personen'">
      <div v-for="u in users" :key="u.id" class="card row-card">
        <div style="flex:1; min-width:0">
          <router-link :to="'/users/' + u.id" class="row-name link">{{ u.display_name }}</router-link>
          <div class="row-meta">
            @{{ u.username }}
            <span v-if="u.is_superuser" class="mini-badge">Admin</span>
            <span v-for="g in u.groups" :key="g.id" class="mini-group">{{ g.emoji }} {{ g.name }}</span>
          </div>
        </div>
        <div class="row-actions">
          <button
            v-if="u.id !== me.id"
            class="btn btn-sm btn-secondary"
            @click="toggleAdmin(u)"
          >{{ u.is_superuser ? 'Admin entziehen' : 'Zum Admin' }}</button>
          <button class="btn btn-sm btn-secondary" @click="askPassword(u)">Passwort</button>
          <button v-if="u.id !== me.id" class="btn btn-sm btn-reject" @click="removeUser(u)" aria-label="Konto löschen">
            <Icon name="muell" class="icon" />
          </button>
        </div>
      </div>
    </template>

    <!-- ===== GRUPPEN ===== -->
    <template v-else>
      <div class="card" style="margin-bottom:14px">
        <p class="muted" style="margin-bottom:14px">
          Gruppen beschreiben nur, wer im Lager was macht. Sie vergeben keine Rechte.
        </p>
        <div class="new-group">
          <input v-model="newGroup.emoji" placeholder="🍳" maxlength="4" class="emoji-input" />
          <input v-model="newGroup.name" placeholder="Name der Gruppe" maxlength="50" @keyup.enter="addGroup" />
          <button class="btn btn-primary btn-sm" :disabled="!newGroup.name.trim()" @click="addGroup">Anlegen</button>
        </div>
        <div v-if="groupErr" class="hint err" style="margin-top:10px">{{ groupErr }}</div>
      </div>

      <div v-for="g in groups" :key="g.id" class="card row-card">
        <div style="flex:1; min-width:0">
          <div class="row-name">{{ g.emoji }} {{ g.name }}</div>
          <div class="row-meta">{{ g.member_count }} {{ g.member_count === 1 ? 'Mitglied' : 'Mitglieder' }}</div>
        </div>
        <button class="btn btn-sm btn-reject" @click="removeGroup(g)" aria-label="Gruppe löschen">
          <Icon name="muell" class="icon" />
        </button>
      </div>
    </template>

    <!-- ===== KATEGORIEN ===== -->
    <template v-if="tab === 'kategorien'">
      <div class="card" style="margin-bottom:14px">
        <p class="muted">
          Kategorien entstehen beim Anlegen eines Gegenstands. Hier lassen sie
          sich umbenennen — gibst du einen Namen ein, den es schon gibt, werden
          beide zusammengeführt.
        </p>
      </div>

      <div v-if="!kategorien.length" class="empty">
        <Icon name="dinge" class="icon" />
        <div class="hinweis">Noch keine Kategorien vergeben</div>
      </div>

      <div v-for="k in kategorien" :key="k.name" class="card row-card">
        <template v-if="katBearbeitet === k.name">
          <input v-model="katEntwurf" class="kat-eingabe" @keyup.enter="katSpeichern(k)" />
          <div class="row-actions">
            <button class="btn btn-sm btn-secondary" @click="katBearbeitet = null">Abbrechen</button>
            <button class="btn btn-sm btn-primary" :disabled="!katEntwurf.trim()" @click="katSpeichern(k)">
              <Icon name="haken" class="icon" />Übernehmen
            </button>
          </div>
        </template>
        <template v-else>
          <div style="flex:1; min-width:0">
            <div class="row-name">{{ k.name }}</div>
            <div class="row-meta">{{ k.anzahl }} {{ k.anzahl === 1 ? 'Gegenstand' : 'Gegenstände' }}</div>
          </div>
          <div class="row-actions">
            <button class="btn btn-sm btn-secondary" @click="katBearbeiten(k)">
              <Icon name="stift" class="icon" />Umbenennen
            </button>
            <button class="btn btn-sm btn-reject" @click="katEntfernen(k)" aria-label="Kategorie entfernen">
              <Icon name="muell" class="icon" />
            </button>
          </div>
        </template>
      </div>
      <div v-if="katMeldung" class="hint ok" style="margin-top:12px">{{ katMeldung }}</div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getPendingUsers, getUsers, adminUpdateUser, deleteUser, adminResetPassword,
  getGroups, createGroup, deleteGroup,
  getAllSummaries, getDrinks, resetAllTallies,
  getCategoryStats, renameCategory, deleteCategory,
} from '../api/index.js'
import { useAuth } from '../composables/useAuth.js'
import Icon from '../components/Icon.vue'

const { user: me } = useAuth()

const tab = ref('freigaben')
const loading = ref(true)
const pending = ref([])
const users = ref([])
const groups = ref([])
const newGroup = ref({ name: '', emoji: '' })
const groupErr = ref('')

// ── Getränke-Abrechnung ──
const summaries = ref([])
const drinks = ref([])
const strichSumme = ref(null)      // null = noch nicht geladen
const exportiert = ref(false)
const leert = ref(false)
const abMeldung = ref('')

// ── Kategorien ──
const kategorien = ref([])
const katBearbeitet = ref(null)
const katEntwurf = ref('')
const katMeldung = ref('')

function katBearbeiten(k) {
  katBearbeitet.value = k.name
  katEntwurf.value = k.name
  katMeldung.value = ''
}

async function katSpeichern(k) {
  const neu = katEntwurf.value.trim()
  if (!neu || neu === k.name) { katBearbeitet.value = null; return }
  const schonDa = kategorien.value.some(
    x => x.name.toLowerCase() === neu.toLowerCase() && x.name !== k.name
  )
  if (schonDa && !confirm(`„${neu}" gibt es schon. Beide zusammenführen?`)) return
  try {
    const erg = await renameCategory(k.name, neu)
    katMeldung.value = schonDa
      ? `${erg.umbenannt} Gegenstände zu „${neu}" zusammengeführt.`
      : `„${k.name}" heißt jetzt „${neu}" (${erg.umbenannt} Gegenstände).`
  } catch (e) {
    katMeldung.value = e.response?.data?.detail || 'Umbenennen fehlgeschlagen'
  } finally {
    katBearbeitet.value = null
    await load()
  }
}

async function katEntfernen(k) {
  if (!confirm(`Kategorie „${k.name}" von ${k.anzahl} Gegenständen entfernen?\n\nDie Gegenstände bleiben erhalten, sie haben danach keine Kategorie.`)) return
  await deleteCategory(k.name)
  katMeldung.value = `„${k.name}" entfernt.`
  await load()
}

const personenMitStrichen = computed(
  () => summaries.value.filter(s => s.grand_total > 0).length
)

async function load() {
  loading.value = true
  try {
    [pending.value, users.value, groups.value, summaries.value, drinks.value, kategorien.value] =
      await Promise.all([
        getPendingUsers(), getUsers(), getGroups(), getAllSummaries(), getDrinks(),
        getCategoryStats(),
      ])
    strichSumme.value = summaries.value.reduce((n, s) => n + s.grand_total, 0)
  } finally {
    loading.value = false
  }
}

async function exportPDF() {
  exportiert.value = true
  abMeldung.value = ''
  try {
    // Erst hier laden: die PDF-Bibliothek ist gross und wird nur in der
    // Verwaltung gebraucht. Im Hauptbundle hat sie alle Seitenaufrufe
    // verlangsamt, auch die von Leuten, die nie ein PDF erzeugen.
    const { generateTallyPDF } = await import('../utils/tallyPDF.js')
    generateTallyPDF(summaries.value, drinks.value)
    abMeldung.value = 'PDF erstellt. Danach kannst du zurücksetzen.'
  } catch {
    abMeldung.value = 'PDF konnte nicht erstellt werden.'
  } finally {
    // kurz gesperrt, damit ein Doppeltipp nicht zwei Dateien erzeugt
    setTimeout(() => { exportiert.value = false }, 1200)
  }
}

async function alleZuruecksetzen() {
  const frage = `Wirklich ALLE ${strichSumme.value} Striche löschen?\n\n`
    + 'Das betrifft jede Person und lässt sich nicht rückgängig machen. '
    + 'Hast du das PDF gesichert?'
  if (!confirm(frage)) return

  leert.value = true
  abMeldung.value = ''
  try {
    const ergebnis = await resetAllTallies()
    abMeldung.value = `${ergebnis.striche} Striche gelöscht. Die Liste ist auf null.`
    await load()
  } finally {
    leert.value = false
  }
}

async function approve(u) {
  await adminUpdateUser(u.id, { is_active: true })
  await load()
}

async function toggleAdmin(u) {
  const target = !u.is_superuser
  const frage = target
    ? `„${u.display_name}" zum Admin machen? Admins können Konten freigeben und löschen.`
    : `„${u.display_name}" die Adminrechte entziehen?`
  if (!confirm(frage)) return
  await adminUpdateUser(u.id, { is_superuser: target })
  await load()
}

async function removeUser(u) {
  if (!confirm(`„${u.display_name}" wirklich löschen? Auch die Striche dieser Person verschwinden.`)) return
  await deleteUser(u.id)
  await load()
}

async function askPassword(u) {
  const pw = prompt(`Neues Passwort für „${u.display_name}" (mind. 8 Zeichen):`)
  if (!pw) return
  if (pw.length < 8) { alert('Das Passwort braucht mindestens 8 Zeichen.'); return }
  await adminResetPassword(u.id, pw)
  alert(`Passwort gesetzt. „${u.display_name}" wurde auf allen Geräten abgemeldet.`)
}

async function addGroup() {
  groupErr.value = ''
  try {
    await createGroup({
      name: newGroup.value.name.trim(),
      emoji: newGroup.value.emoji.trim() || null,
    })
    newGroup.value = { name: '', emoji: '' }
    await load()
  } catch (e) {
    groupErr.value = e.response?.data?.detail || 'Anlegen fehlgeschlagen'
  }
}

async function removeGroup(g) {
  if (!confirm(`Gruppe „${g.name}" löschen? Die Zugehörigkeiten gehen verloren.`)) return
  await deleteGroup(g.id)
  await load()
}

onMounted(load)
</script>

<style scoped>
.admin-tabs { display: flex; border-bottom: 2px solid var(--border); margin-bottom: 16px; }
.admin-tabs button {
  flex: 1; padding: 12px 8px; border: none; background: none;
  font-size: 15px; font-weight: 700; color: var(--text-muted);
  cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px;
  -webkit-tap-highlight-color: transparent;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
}
.admin-tabs button.active { color: var(--green); border-bottom-color: var(--green); }

/* Einstieg in die Lagerortverwaltung */
.ortverwaltung {
  display: flex; align-items: center; gap: 14px;
  margin-bottom: 16px;
  text-decoration: none;
  color: var(--tinte);
}
.ortverwaltung .gross { font-size: 30px; color: var(--gebrannt); flex-shrink: 0; }
.ov-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.ov-titel {
  font-family: var(--schrift-stempel);
  font-size: 13px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--gebrannt);
}
.ov-unter { font-size: 14px; color: var(--tinte-blass); line-height: 1.3; }

/* Abrechnung: sichern, dann leeren */
.abrechnung { margin-bottom: 16px; }
.ab-kopf { display: flex; align-items: center; gap: 14px; }
.ab-kopf .gross { font-size: 30px; color: var(--gebrannt); flex-shrink: 0; }
.ab-knoepfe { display: flex; gap: 9px; flex-wrap: wrap; margin-top: 14px; }
.ab-knoepfe .btn { flex: 1; min-width: 150px; }
.ab-hinweis {
  font-size: 13.5px; color: var(--tinte-blass);
  line-height: 1.35; margin-top: 10px; max-width: 52ch;
}
.pill {
  background: var(--rot); color: #fff; border-radius: 999px;
  padding: 1px 8px; font-size: 12px; font-weight: 800;
}

.row-card { display: flex; align-items: center; gap: 10px; padding: 14px; flex-wrap: wrap; }
.row-name { font-weight: 700; font-size: 17px; }
.row-name.link { color: var(--text); text-decoration: none; }
.row-meta {
  font-size: 13px; color: var(--text-muted); margin-top: 3px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.row-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-reject { background: transparent; color: var(--rot); box-shadow: inset 0 0 0 1.5px rgba(158,58,34,.5); }
.mini-badge {
  background: var(--green-pale); color: var(--green-light);
  padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 700;
}
.mini-group {
  background: var(--surface-2); border: 1px solid var(--border);
  padding: 1px 8px; border-radius: 999px; font-size: 12px;
}

.new-group { display: flex; gap: 8px; align-items: center; }
.new-group input { flex: 1; min-width: 0; }
.emoji-input { flex: 0 0 68px; text-align: center; }
.muted { color: var(--text-muted); font-size: 15px; line-height: 1.4; }
.hint.err { color: var(--rot); font-size: 15px; font-weight: 600; }

@media (max-width: 480px) {
  .row-actions { width: 100%; }
  .row-actions .btn { flex: 1; }
}
</style>
