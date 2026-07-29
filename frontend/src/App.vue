<template>
  <div v-if="!isAuthPage" class="app-root" :class="mode === 'lager' ? 'mode-lager' : 'mode-jahr'">
    <div class="mode-bar">
      <div class="mode-bar-title">
        <img src="/logo.png" class="mode-bar-logo" alt="" />
        Blauwagen
      </div>
      <div class="toggle-row">
        <span class="toggle-label" :class="{ active: mode === 'lager' }">🏕️</span>
        <div class="toggle-switch" :class="mode" @click="setMode(mode === 'lager' ? 'jahr' : 'lager')">
          <div class="toggle-knob" />
        </div>
        <span class="toggle-label" :class="{ active: mode === 'jahr' }">🏠</span>
      </div>
      <router-link to="/profile" class="profile-btn" :title="user?.display_name || 'Profil'">
        <span v-if="pendingCount" class="profile-dot">{{ pendingCount }}</span>
        {{ initials }}
      </router-link>
    </div>

    <!-- key=mode erzwingt Neu-Laden der View wenn Modus wechselt -->
    <router-view :key="mode" />

    <nav>
      <router-link to="/search">
        <span class="icon">🔍</span>
        Suchen
      </router-link>
      <router-link to="/items">
        <span class="icon">🔧</span>
        Dinge
      </router-link>
      <router-link to="/locations">
        <span class="icon">📦</span>
        Orte
      </router-link>
      <router-link v-if="mode === 'lager'" to="/drinks">
        <span class="icon">🥤</span>
        Getränke
      </router-link>
      <router-link to="/shopping">
        <span class="icon">🛒</span>
        Einkauf
      </router-link>
      <router-link to="/notes">
        <span class="icon">📝</span>
        Notizen
      </router-link>
    </nav>
  </div>

  <router-view v-else />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMode } from './composables/useMode.js'
import { useAuth } from './composables/useAuth.js'
import { getPendingUsers } from './api/index.js'

const route = useRoute()
const { mode, setMode } = useMode()
const { user, isAdmin } = useAuth()

const pendingCount = ref(0)

// Login und Registrierung bringen ihr eigenes Layout mit (ohne Nav/Header).
const isAuthPage = computed(() => ['/login', '/register'].includes(route.path))

const initials = computed(() => {
  const name = user.value?.display_name || ''
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('') || '?'
})

// Admins sehen offene Registrierungen als Punkt am Profil-Knopf.
watch(() => [isAdmin.value, route.path], async () => {
  if (!isAdmin.value) { pendingCount.value = 0; return }
  try {
    pendingCount.value = (await getPendingUsers()).length
  } catch {
    pendingCount.value = 0
  }
}, { immediate: true })
</script>

<style>
/* ── Gesamter App-Hintergrund wechselt mit Modus ─────────────── */
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--cream);
  transition: background 0.3s;
}
.app-root.mode-lager {
  --cream:     #0c2540;
  --white:     #132e50;
  --surface-2: #1a3a60;
  --border:    #1e4070;
  --text:      #e8f4ff;
  --text-muted:#7aabda;
}

/* ── Header: transparent → verschmilzt mit Seite ─────────────── */
.mode-bar {
  position: sticky;
  top: 0;
  z-index: 101;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  padding: 6px 14px;
  gap: 8px;
  background: transparent;
}

.mode-bar-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--text);
  flex: 1;
  min-width: 0;
}
.mode-bar-logo {
  height: 100px;
  width: 100px;
  object-fit: contain;
  background: #ffffffcc;
  border-radius: 50%;
  padding: 2px;
  flex-shrink: 0;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-shrink: 0;
}
.toggle-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  transition: color 0.2s;
  white-space: nowrap;
}
.toggle-label.active { color: var(--text); }

.toggle-switch {
  position: relative;
  width: 52px; height: 28px;
  border-radius: 14px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.25s;
  -webkit-tap-highlight-color: transparent;
}
.mode-lager .toggle-switch { background: #3a9ae8; }
.mode-jahr  .toggle-switch { background: #1e75c8; }
.toggle-knob {
  position: absolute;
  top: 3px; left: 3px;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: white;
  transition: transform 0.25s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.4);
}
.toggle-switch.jahr .toggle-knob { transform: translateX(24px); }

.profile-btn {
  position: relative;
  width: 40px; height: 40px; flex-shrink: 0;
  border-radius: 50%;
  background: var(--green); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 800; text-decoration: none;
  -webkit-tap-highlight-color: transparent;
}
.profile-btn:active { opacity: 0.8; }
.profile-dot {
  position: absolute; top: -3px; right: -3px;
  min-width: 18px; height: 18px; padding: 0 4px;
  border-radius: 999px; background: #c62828; color: #fff;
  font-size: 11px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}

/* ── Mobile ───────────────────────────────────────────────────── */
@media (max-width: 390px) {
  .mode-bar { padding: 4px 10px; }
  .mode-bar-title { font-size: 18px; gap: 8px; }
  .mode-bar-logo  { height: 48px; width: 48px; }
  .toggle-label { font-size: 12px; }
}
</style>
