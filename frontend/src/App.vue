<template>
  <div v-if="!isAuthPage" class="app-root">
    <!-- Wasserzeichen liegt im Pergament und scrollt nicht mit -->
    <div class="wasserzeichen" aria-hidden="true" />

    <header class="holzleiste">
      <router-link to="/" class="brandzeichen" aria-label="Startseite" />
      <span class="luecke" />

      <!-- Zweigeteilter Schalter: die aktive Seite ist ins Holz gebrannt -->
      <div class="schalter" role="group" aria-label="Lagerzustand">
        <button
          class="seg"
          :class="{ an: mode === 'lager' }"
          :aria-pressed="mode === 'lager'"
          @click="setMode('lager')"
        >
          <Icon name="zelt" class="icon" />Lager
        </button>
        <button
          class="seg"
          :class="{ an: mode === 'jahr' }"
          :aria-pressed="mode === 'jahr'"
          @click="setMode('jahr')"
        >
          <Icon name="haus" class="icon" />Jahr
        </button>
      </div>

      <router-link to="/profile" class="konto" :title="user?.display_name || 'Profil'">
        <span v-if="pendingCount" class="konto-punkt">{{ pendingCount }}</span>
        {{ initials }}
      </router-link>
    </header>

    <!-- key=mode erzwingt Neu-Laden der View wenn Modus wechselt -->
    <router-view :key="mode" />

    <nav>
      <router-link to="/search"><Icon name="suche" class="icon" />Suchen</router-link>
      <router-link to="/items"><Icon name="dinge" class="icon" />Dinge</router-link>
      <router-link to="/locations"><Icon name="orte" class="icon" />Orte</router-link>
      <!-- Im Jahresbetrieb nicht nutzbar, aber sichtbar: sonst wundert man
           sich, wo der Tab hin ist. -->
      <router-link
        to="/drinks"
        :class="{ gesperrt: mode !== 'lager' }"
        :tabindex="mode === 'lager' ? undefined : -1"
        :title="mode === 'lager' ? 'Getränke' : 'Nur auf dem Lager'"
      ><Icon name="getraenke" class="icon" />Getränke</router-link>
      <router-link to="/shopping"><Icon name="einkauf" class="icon" />Einkauf</router-link>
      <router-link to="/notes"><Icon name="notizen" class="icon" />Notizen</router-link>
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
import Icon from './components/Icon.vue'

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
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Wasserzeichen im Pergament ─────────────────────────────────── */
.wasserzeichen {
  position: fixed;
  left: 50%;
  top: 48%;
  transform: translate(-50%, -50%) rotate(-4deg);
  width: min(88vw, 460px);
  aspect-ratio: 1;
  background-color: #5d4a2c;
  -webkit-mask: url('/logo.png') center / contain no-repeat;
  mask: url('/logo.png') center / contain no-repeat;
  opacity: 0.085;
  z-index: 0;
  pointer-events: none;
}

/* ── Obere Holzleiste ───────────────────────────────────────────── */
.holzleiste {
  position: sticky;
  top: 0;
  z-index: 101;
  background: var(--holz);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  padding-top: calc(8px + env(safe-area-inset-top, 0px));
  box-shadow: 0 3px 8px rgba(40, 22, 6, 0.4), inset 0 -2px 5px rgba(40, 22, 6, 0.3);
}

/* Das Logo als Brandzeichen: die Silhouette dient als Maske über der
   Brandfarbe, damit der Wal die Farbe des verkohlten Holzes annimmt
   statt als Bild darauf zu liegen. Der helle Grat unten ist die
   aufgeworfene Holzfaser am Rand des Brandzeichens. */
.brandzeichen {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  background-color: rgba(40, 21, 5, 0.88);
  -webkit-mask: url('/logo.png') center / contain no-repeat;
  mask: url('/logo.png') center / contain no-repeat;
  filter: drop-shadow(0 1.5px 0 var(--kerbe));
  -webkit-tap-highlight-color: transparent;
}
.brandzeichen:active { opacity: 0.75; }

.holzleiste .luecke { flex: 1; }

/* ── Umschalter: in das Holz gefräste Rille ─────────────────────── */
.schalter {
  display: flex;
  flex-shrink: 0;
  background: rgba(40, 21, 5, 0.34);
  border-radius: 4px;
  padding: 2px;
  box-shadow: inset 0 2px 4px rgba(25, 12, 2, 0.55);
}
.schalter .seg {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 11px;
  min-height: 34px;
  border: none;
  background: transparent;
  border-radius: 3px;
  font-family: var(--schrift-stempel);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: rgba(247, 226, 192, 0.5);
  white-space: nowrap;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.schalter .seg .icon { font-size: 15px; }
.schalter .seg.an {
  background: linear-gradient(#8d5f36, #7b5230);
  color: var(--gebrannt);
  text-shadow: 0 1px 0 var(--kerbe);
  box-shadow: 0 1px 0 var(--kerbe), 0 1px 3px rgba(25, 12, 2, 0.4);
}
.schalter .seg.an .icon { filter: drop-shadow(0 1px 0 var(--kerbe)); }
.schalter .seg:focus-visible { outline: 2px solid #f7e2c0; outline-offset: 1px; }

/* ── Profil-Knopf: eingelassene Scheibe ─────────────────────────── */
.konto {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgba(40, 21, 5, 0.3);
  color: #f2dcb6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--schrift-stempel);
  font-size: 12.5px;
  text-decoration: none;
  box-shadow: inset 0 2px 4px rgba(25, 12, 2, 0.5);
  -webkit-tap-highlight-color: transparent;
}
.konto:active { opacity: 0.8; }
.konto-punkt {
  position: absolute;
  top: -3px;
  right: -3px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--rot);
  color: #fff;
  font-family: var(--schrift-text);
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(25, 12, 2, 0.5);
}

/* ── Kleine Telefone ────────────────────────────────────────────── */
@media (max-width: 390px) {
  .holzleiste { padding: 6px 10px; padding-top: calc(6px + env(safe-area-inset-top, 0px)); gap: 8px; }
  .brandzeichen { width: 40px; height: 40px; }
  .schalter .seg { padding: 6px 8px; font-size: 10px; min-height: 32px; }
  .schalter .seg .icon { font-size: 13px; }
  .konto { width: 32px; height: 32px; font-size: 11.5px; }
  .wasserzeichen { width: 92vw; }
}

/* Sehr schmal: Schalter nur mit Symbolen, Beschriftung weg */
@media (max-width: 340px) {
  .schalter .seg { padding: 6px 9px; }
  .schalter .seg { font-size: 0; gap: 0; }
  .schalter .seg .icon { font-size: 15px; }
}
</style>
