import { ref } from 'vue'
import { getLagerZeitraum } from '../api/index.js'

const SCHLUESSEL = 'bauwagen_mode'
const MANUELL = 'bauwagen_mode_manuell'

// Modul-level singleton — wird in der ganzen App geteilt
const mode = ref(localStorage.getItem(SCHLUESSEL) || 'lager')
const zeitraum = ref(null)

export function useMode() {
  function setMode(m) {
    mode.value = m
    localStorage.setItem(SCHLUESSEL, m)
    // Merken, dass von Hand umgeschaltet wurde: der Lagerzeitraum soll die
    // bewusste Entscheidung nicht beim nächsten Laden wieder überschreiben.
    localStorage.setItem(MANUELL, new Date().toISOString())
  }

  /**
   * Holt den eingestellten Lagerzeitraum und setzt den Modus danach --
   * aber nur, wenn heute nicht schon von Hand umgeschaltet wurde.
   */
  async function modusAusZeitraum() {
    try {
      const z = await getLagerZeitraum()
      zeitraum.value = z

      const zuletzt = localStorage.getItem(MANUELL)
      const heuteManuell = zuletzt && zuletzt.slice(0, 10) === new Date().toISOString().slice(0, 10)
      if (heuteManuell) return z

      if (z.empfohlener_modus && z.empfohlener_modus !== mode.value) {
        mode.value = z.empfohlener_modus
        localStorage.setItem(SCHLUESSEL, z.empfohlener_modus)
      }
      return z
    } catch {
      return null   // ohne Netz bleibt es beim zuletzt bekannten Modus
    }
  }

  return { mode, setMode, zeitraum, modusAusZeitraum }
}
