<template>
  <template v-if="route.path !== '/login'">
    <div class="mode-bar" :class="mode === 'lager' ? 'mode-lager' : 'mode-jahr'">
      <button
        class="mode-btn"
        :class="{ active: mode === 'lager' }"
        @click="setMode('lager')"
      >🏕️ Auf dem Lager</button>
      <button
        class="mode-btn"
        :class="{ active: mode === 'jahr' }"
        @click="setMode('jahr')"
      >🏠 Unter dem Jahr</button>
      <button class="logout-btn" @click="doLogout" title="Abmelden">⏻</button>
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
      <router-link to="/drinks">
        <span class="icon">🥤</span>
        Getränke
      </router-link>
    </nav>
  </template>

  <router-view v-else />
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useMode } from './composables/useMode.js'
import { logout } from './api/index.js'

const route = useRoute()
const router = useRouter()
const { mode, setMode } = useMode()

async function doLogout() {
  if (!confirm('Wirklich abmelden?')) return
  await logout()
  router.push('/login')
}
</script>

<style>
.mode-bar {
  position: sticky;
  top: 0;
  z-index: 101;
  display: flex;
  padding: 8px 12px;
  gap: 8px;
  border-bottom: 2px solid transparent;
  transition: background 0.2s;
}
.mode-bar.mode-lager { background: #e8f5e9; border-color: #2c5f2e; }
.mode-bar.mode-jahr  { background: #e3f2fd; border-color: #1565c0; }

.mode-btn {
  flex: 1;
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid transparent;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  background: transparent;
  color: #555;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.15s;
}
.mode-bar.mode-lager .mode-btn.active { background: #2c5f2e; color: white; border-color: #2c5f2e; }
.mode-bar.mode-jahr  .mode-btn.active { background: #1565c0; color: white; border-color: #1565c0; }

.logout-btn {
  width: 36px; height: 36px; flex-shrink: 0;
  border: 2px solid transparent; border-radius: 8px;
  background: transparent; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); -webkit-tap-highlight-color: transparent;
  transition: all 0.15s;
}
.logout-btn:active { background: rgba(0,0,0,0.08); }
</style>
