<template>
  <div v-if="!isAuthPage" class="app-root">
    <!-- Der Wal ist groß in die Wand gebrannt und scrollt nicht mit -->
    <div class="wandzeichen" aria-hidden="true" />

    <header class="holzleiste">
      <router-link to="/" class="brandzeichen" aria-label="Startseite" />
      <span class="luecke" />

      <!-- Schieber: die Stellung des Griffs IST der Zustand. Zusätzlich ist
           das Symbol der aktiven Seite voll deckend, das der anderen blass --
           Stellung und Betonung sagen dasselbe. -->
      <button
        class="schieber"
        role="switch"
        :aria-checked="mode === 'jahr'"
        :aria-label="mode === 'lager' ? 'Auf dem Lager – umschalten auf Jahresbetrieb' : 'Unter dem Jahr – umschalten auf Lagerbetrieb'"
        @click="setMode(mode === 'lager' ? 'jahr' : 'lager')"
      >
        <Icon name="zelt" class="icon ende" :class="{ an: mode === 'lager' }" />
        <span class="nut">
          <span class="griff" :class="mode === 'lager' ? 'links' : 'rechts'">
            <i /><i /><i />
          </span>
        </span>
        <Icon name="haus" class="icon ende" :class="{ an: mode === 'jahr' }" />
      </button>

      <router-link to="/profile" class="konto" :title="user?.display_name || 'Profil'">
        <span v-if="pendingCount" class="konto-punkt">{{ pendingCount }}</span>
        {{ initials }}
      </router-link>
    </header>

    <!-- key=mode erzwingt Neu-Laden der View wenn Modus wechselt -->
    <router-view :key="mode" />

    <nav>
      <router-link to="/items"><Icon name="dinge" class="icon" />Dinge</router-link>
      <!-- Im Jahresbetrieb nicht nutzbar, aber sichtbar: sonst wundert man
           sich, wo der Tab hin ist. -->
      <router-link
        to="/drinks"
        :class="{ gesperrt: mode !== 'lager' }"
        :tabindex="mode === 'lager' ? undefined : -1"
        :title="mode === 'lager' ? 'Getränke' : 'Nur auf dem Lager'"
      ><Icon name="getraenke" class="icon" />Trinken</router-link>
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

/* ── Der Wal, groß in die Holzwand gebrannt ─────────────────────── */
.wandzeichen {
  position: fixed;
  left: 50%;
  top: 48%;
  transform: translate(-50%, -50%) rotate(-4deg);
  width: min(90vw, 480px);
  aspect-ratio: 1;
  background-color: #5a3a18;
  -webkit-mask: url('/logo.png') center / contain no-repeat;
  mask: url('/logo.png') center / contain no-repeat;
  /* Kräftiger als ein Wasserzeichen auf Papier -- Holz verzeiht mehr,
     und der Grat unten lässt es eingebrannt statt aufgedruckt wirken. */
  opacity: 0.13;
  filter: drop-shadow(0 2px 0 rgba(255, 246, 228, 0.22));
  z-index: 0;
  pointer-events: none;
}

/* ── Obere Holzleiste ───────────────────────────────────────────── */
.holzleiste {
  position: sticky;
  top: 0;
  z-index: 101;
  background: var(--holz-leiste);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  padding-top: calc(8px + env(safe-area-inset-top, 0px));
  box-shadow: 0 3px 8px rgba(60, 34, 10, 0.3), inset 0 -2px 5px rgba(80, 50, 20, 0.2);
}

/* Das Logo als Brandzeichen: die Silhouette dient als Maske über der
   Brandfarbe, damit der Wal die Farbe des verkohlten Holzes annimmt
   statt als Bild darauf zu liegen. Der helle Grat unten ist die
   aufgeworfene Holzfaser am Rand des Brandzeichens. */
.brandzeichen {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  background-color: var(--gebrannt);
  -webkit-mask: url('/logo.png') center / contain no-repeat;
  mask: url('/logo.png') center / contain no-repeat;
  filter: drop-shadow(0 1.5px 0 var(--kerbe));
  -webkit-tap-highlight-color: transparent;
}
.brandzeichen:active { opacity: 0.75; }

.holzleiste .luecke { flex: 1; }

/* ── Schieber: rechteckige Nut im Holz, dunkler Griff mit Riffelung ──
   Nichts Rundes, und der Griff dunkel: dadurch hebt er sich klar vom
   hellen Holz ab statt darin zu verschwinden. */
.schieber {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  flex-shrink: 0;
  padding: 4px 2px;
  border: none;
  background: transparent;
  color: var(--gebrannt);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.schieber .ende {
  font-size: 17px;
  opacity: 0.3;
  transition: opacity 0.15s;
}
.schieber .ende.an {
  opacity: 1;
  filter: drop-shadow(0 1px 0 var(--kerbe));
}

/* Die Nut: eingefräst, dunkel, mit hellem Grat an der Unterkante */
.schieber .nut {
  position: relative;
  width: 56px;
  height: 26px;
  border-radius: 2px;
  background: rgba(48, 26, 6, 0.42);
  box-shadow:
    inset 0 2px 5px rgba(30, 15, 3, 0.7),
    inset 0 -1px 0 rgba(255, 250, 235, 0.2);
}

/* Der Griff: dunkles Eisen, mit Riffelung und Fase oben */
.schieber .griff {
  position: absolute;
  top: 3px;
  width: 26px;
  height: 20px;
  border-radius: 1px;
  background: linear-gradient(#4a3116, #33200c 55%, #241505);
  box-shadow:
    0 1px 3px rgba(20, 10, 2, 0.6),
    inset 0 1px 0 rgba(255, 236, 200, 0.28),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  transition: left 0.16s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2.5px;
}
/* Griffrillen -- machen klar, dass man daran zieht */
.schieber .griff i {
  display: block;
  width: 1.5px;
  height: 10px;
  border-radius: 1px;
  background: rgba(255, 240, 210, 0.34);
}
.schieber .griff.links { left: 3px; }
.schieber .griff.rechts { left: 27px; }

.schieber:focus-visible { outline: 2px solid var(--gebrannt); outline-offset: 2px; }

/* ── Profil-Knopf: eingelassene Scheibe ─────────────────────────── */
.konto {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgba(60, 34, 10, 0.22);
  color: var(--gebrannt);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--schrift-stempel);
  font-size: 13px;
  text-decoration: none;
  box-shadow: inset 0 2px 4px rgba(60, 34, 10, 0.35);
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
  .konto { width: 33px; height: 33px; font-size: 12px; }
  .wandzeichen { width: 94vw; }
  .schieber { gap: 7px; }
  .schieber .nut { width: 50px; height: 24px; }
  .schieber .griff { width: 23px; height: 18px; }
  .schieber .griff.rechts { left: 24px; }
  .schieber .ende { font-size: 16px; }
}
</style>
