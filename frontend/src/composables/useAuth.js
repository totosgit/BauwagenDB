import { ref, computed } from 'vue'
import { getMe, logout as apiLogout } from '../api/index.js'

// Modul-level singleton -- der angemeldete Benutzer wird einmal geladen
// und dann in der ganzen App geteilt.
const user = ref(null)
const loaded = ref(false)

export function useAuth() {
  const isAdmin = computed(() => !!user.value?.is_superuser)

  /** Lädt das eigene Profil. Gibt null zurück, wenn nicht angemeldet. */
  async function refresh() {
    try {
      user.value = await getMe()
    } catch {
      user.value = null
    } finally {
      loaded.value = true
    }
    return user.value
  }

  /** Wie refresh(), aber nur beim ersten Aufruf ein Request. */
  async function ensureLoaded() {
    if (loaded.value) return user.value
    return refresh()
  }

  async function logout() {
    try {
      await apiLogout()
    } finally {
      user.value = null
      loaded.value = false
    }
  }

  return { user, isAdmin, loaded, refresh, ensureLoaded, logout }
}
