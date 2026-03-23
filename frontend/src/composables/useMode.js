import { ref } from 'vue'

// Modul-level singleton — wird in der ganzen App geteilt
const mode = ref(localStorage.getItem('bauwagen_mode') || 'lager')

export function useMode() {
  function setMode(m) {
    mode.value = m
    localStorage.setItem('bauwagen_mode', m)
  }
  return { mode, setMode }
}
