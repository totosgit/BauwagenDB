<template>
  <div class="page">
    <div v-if="loading" class="loading">Laden ...</div>

    <template v-else-if="profile">
      <!-- Kopf -->
      <div class="card profile-head">
        <div class="avatar">{{ initials }}</div>
        <div style="flex:1; min-width:0">
          <div class="profile-name">{{ profile.display_name }}</div>
          <div class="profile-user">@{{ profile.username }}</div>
        </div>
        <span v-if="profile.is_superuser" class="admin-badge">Admin</span>
      </div>

      <!-- Gruppen -->
      <div class="section-label">Gruppen</div>
      <div class="card">
        <div v-if="profile.groups.length" class="badge-row">
          <span v-for="g in profile.groups" :key="g.id" class="group-badge">
            {{ g.emoji }} {{ g.name }}
          </span>
        </div>
        <div v-else class="muted">
          {{ isSelf ? 'Du bist noch in keiner Gruppe.' : 'Keine Gruppen.' }}
        </div>
      </div>

      <!-- Gruppen beitreten (nur eigenes Profil) -->
      <template v-if="isSelf">
        <div class="section-label" style="margin-top:22px">Gruppen beitreten</div>
        <div class="card">
          <p class="muted" style="margin-bottom:14px">
            Gruppen sind nur zur Info fürs Profil – sie geben keine zusätzlichen Rechte.
          </p>
          <div v-if="!groups.length" class="muted">Es gibt noch keine Gruppen.</div>
          <div v-for="g in groups" :key="g.id" class="group-row">
            <div style="flex:1; min-width:0">
              <div class="group-name">{{ g.emoji }} {{ g.name }}</div>
              <div class="group-meta">
                {{ g.member_count }} {{ g.member_count === 1 ? 'Mitglied' : 'Mitglieder' }}
                <span v-if="g.description"> · {{ g.description }}</span>
              </div>
            </div>
            <button
              class="btn btn-sm"
              :class="g.is_member ? 'btn-secondary' : 'btn-primary'"
              :disabled="busyGroup === g.id"
              @click="toggleGroup(g)"
            >{{ g.is_member ? 'Austreten' : 'Beitreten' }}</button>
          </div>
        </div>

        <!-- Eigene Daten -->
        <div class="section-label" style="margin-top:22px">Meine Daten</div>
        <div class="card">
          <div class="form-group">
            <label>Anzeigename</label>
            <input v-model="edit.display_name" maxlength="100" />
          </div>
          <div class="form-group">
            <label>E-Mail (optional)</label>
            <input v-model="edit.email" type="email" placeholder="nur falls du magst" />
          </div>
          <div v-if="saveMsg" class="hint ok">{{ saveMsg }}</div>
          <div v-if="saveErr" class="hint err">{{ saveErr }}</div>
          <button class="btn btn-primary" :disabled="saving" @click="saveProfile">Speichern</button>
        </div>

        <!-- Passwort -->
        <div class="section-label" style="margin-top:22px">Passwort ändern</div>
        <div class="card">
          <div class="form-group">
            <label>Aktuelles Passwort</label>
            <input v-model="pw.current" type="password" autocomplete="current-password" />
          </div>
          <div class="form-group">
            <label>Neues Passwort</label>
            <input v-model="pw.next" type="password" autocomplete="new-password" />
          </div>
          <div v-if="pwMsg" class="hint ok">{{ pwMsg }}</div>
          <div v-if="pwErr" class="hint err">{{ pwErr }}</div>
          <p class="muted" style="margin-bottom:12px">
            Beim Ändern werden alle anderen Geräte abgemeldet.
          </p>
          <button class="btn btn-primary" :disabled="savingPw" @click="changePassword">Passwort ändern</button>
        </div>

        <!-- Aktionen -->
        <div class="card" style="margin-top:22px; display:flex; gap:10px; flex-wrap:wrap">
          <router-link v-if="isAdmin" to="/admin" class="btn btn-secondary">
            <Icon name="verwaltung" class="icon" />Verwaltung
          </router-link>
          <button class="btn btn-danger" @click="doLogout">
            <Icon name="abmelden" class="icon" />Abmelden
          </button>
        </div>
      </template>

      <div v-else style="margin-top:22px">
        <button class="btn btn-secondary" @click="$router.back()">
          <Icon name="zurueck" class="icon" />Zurück
        </button>
      </div>
    </template>

    <div v-else class="empty">
      <Icon name="profil" class="icon" />
      <div class="hinweis">Profil nicht gefunden</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getUser, getGroups, joinGroup, leaveGroup, updateMe } from '../api/index.js'
import { useAuth } from '../composables/useAuth.js'
import Icon from '../components/Icon.vue'

const route = useRoute()
const router = useRouter()
const { user, isAdmin, refresh, logout } = useAuth()

const profile = ref(null)
const groups = ref([])
const loading = ref(true)
const busyGroup = ref(null)

const edit = ref({ display_name: '', email: '' })
const saving = ref(false)
const saveMsg = ref('')
const saveErr = ref('')

const pw = ref({ current: '', next: '' })
const savingPw = ref(false)
const pwMsg = ref('')
const pwErr = ref('')

const isSelf = computed(() => !route.params.id || route.params.id === user.value?.id)
const initials = computed(() => {
  const name = profile.value?.display_name || ''
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('') || '?'
})

async function load() {
  loading.value = true
  try {
    if (isSelf.value) {
      profile.value = await refresh()
      groups.value = await getGroups()
      edit.value = {
        display_name: profile.value?.display_name || '',
        email: profile.value?.email || '',
      }
    } else {
      profile.value = await getUser(route.params.id)
    }
  } catch {
    profile.value = null
  } finally {
    loading.value = false
  }
}

async function toggleGroup(g) {
  busyGroup.value = g.id
  try {
    const updated = g.is_member ? await leaveGroup(g.id) : await joinGroup(g.id)
    const idx = groups.value.findIndex(x => x.id === g.id)
    if (idx !== -1) groups.value[idx] = updated
    profile.value = await refresh()
  } finally {
    busyGroup.value = null
  }
}

async function saveProfile() {
  saving.value = true
  saveMsg.value = ''
  saveErr.value = ''
  try {
    const payload = { display_name: edit.value.display_name.trim() }
    if (edit.value.email.trim()) payload.email = edit.value.email.trim()
    await updateMe(payload)
    profile.value = await refresh()
    saveMsg.value = 'Gespeichert.'
  } catch (e) {
    saveErr.value = e.response?.data?.detail || 'Speichern fehlgeschlagen'
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  pwMsg.value = ''
  pwErr.value = ''
  if (pw.value.next.length < 8) { pwErr.value = 'Das neue Passwort braucht mindestens 8 Zeichen'; return }

  savingPw.value = true
  try {
    await updateMe({ password: pw.value.next, current_password: pw.value.current })
    pw.value = { current: '', next: '' }
    pwMsg.value = 'Passwort geändert.'
  } catch (e) {
    pwErr.value = e.response?.data?.detail || 'Ändern fehlgeschlagen'
  } finally {
    savingPw.value = false
  }
}

async function doLogout() {
  if (!confirm('Wirklich abmelden?')) return
  await logout()
  router.push('/login')
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<style scoped>
.profile-head { display: flex; align-items: center; gap: 14px; }
.avatar {
  width: 60px; height: 60px; flex-shrink: 0;
  border-radius: 50%; background: var(--green); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 800;
}
.profile-name { font-size: 22px; font-weight: 800; }
.profile-user { color: var(--text-muted); font-size: 15px; }
.admin-badge {
  background: var(--green-pale); color: var(--green-light);
  padding: 4px 12px; border-radius: 999px;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}

.section-label {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: var(--text-muted);
  margin: 22px 0 10px;
}
.badge-row { display: flex; flex-wrap: wrap; gap: 8px; }
.group-badge {
  background: var(--surface-2); border: 1.5px solid var(--border);
  padding: 8px 14px; border-radius: 999px;
  font-size: 15px; font-weight: 600;
}
.group-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 0; border-bottom: 1px solid var(--border);
}
.group-row:last-child { border-bottom: none; padding-bottom: 0; }
.group-name { font-weight: 700; font-size: 16px; }
.group-meta { font-size: 13px; color: var(--text-muted); margin-top: 2px; }
.muted { color: var(--text-muted); font-size: 15px; line-height: 1.4; }
.hint { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.hint.ok { color: var(--green-light); }
.hint.err { color: var(--rot); }
</style>
