import { reactive, watch } from 'vue'

const STORAGE_KEY = 'bauwagen_expanded'

// Modul-level singleton — bleibt über Komponenten hinweg erhalten
const state = reactive(
  JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
)

watch(state, () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state }))
}, { deep: true })

export function useExpanded() {
  /** Ist ein Node expandiert? Default: true (aufgeklappt). */
  function isExpanded(id) {
    return state[id] !== false  // undefined → true (default aufgeklappt)
  }

  function toggle(id) {
    state[id] = !isExpanded(id)
  }

  /** Alle IDs auf expanded=true setzen. */
  function expandAll(ids) {
    ids.forEach(id => { state[id] = true })
  }

  /** Alle IDs auf expanded=false setzen. */
  function collapseAll(ids) {
    ids.forEach(id => { state[id] = false })
  }

  return { isExpanded, toggle, expandAll, collapseAll }
}
