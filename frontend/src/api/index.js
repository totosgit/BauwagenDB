import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

// Öffentliche Seiten -- hier darf ein 401 nicht zur Weiterleitung führen,
// sonst landet man beim Anmeldeversuch in einer Schleife.
const PUBLIC_PAGES = ['/login', '/register']

// Bei abgelaufener Sitzung zurück zum Login
api.interceptors.response.use(
  r => r,
  err => {
    const onPublicPage = PUBLIC_PAGES.some(p => window.location.pathname.startsWith(p))
    if (err.response?.status === 401 && !onPublicPage) {
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// --- Auth ---
export const login = (username, password) => api.post('/auth/login', { username, password }).then(r => r.data)
export const logout = () => api.post('/auth/logout').then(r => r.data)
export const register = (data) => api.post('/auth/register', data).then(r => r.data)
export const getMe = () => api.get('/auth/me').then(r => r.data)

// --- Benutzer & Profile ---
export const getUsers = () => api.get('/users/').then(r => r.data)
export const getUser = (id) => api.get(`/users/${id}`).then(r => r.data)
export const getPendingUsers = () => api.get('/users/pending').then(r => r.data)
export const updateMe = (data) => api.patch('/users/me', data).then(r => r.data)
export const adminUpdateUser = (id, data) => api.patch(`/users/${id}`, data).then(r => r.data)
export const adminResetPassword = (id, password) => api.post(`/users/${id}/password`, { password })
export const deleteUser = (id) => api.delete(`/users/${id}`)

// --- Gruppen (reine Profil-Labels, ohne Rechte) ---
export const getGroups = () => api.get('/groups/').then(r => r.data)
export const createGroup = (data) => api.post('/groups/', data).then(r => r.data)
export const updateGroup = (id, data) => api.patch(`/groups/${id}`, data).then(r => r.data)
export const deleteGroup = (id) => api.delete(`/groups/${id}`)
export const getGroupMembers = (id) => api.get(`/groups/${id}/members`).then(r => r.data)
export const joinGroup = (id) => api.post(`/groups/${id}/join`).then(r => r.data)
export const leaveGroup = (id) => api.delete(`/groups/${id}/join`).then(r => r.data)

// Sucht nur Gegenstände -- Lagerorte werden bewusst nicht durchsucht.
export const searchAll = (q, mode) => api.get('/search/', { params: { q, mode } }).then(r => r.data)

export const getItems = (params = {}) => api.get('/items/', { params }).then(r => r.data)  // params kann { mode, category, location_id } enthalten
export const getItem = (id) => api.get(`/items/${id}`).then(r => r.data)
export const createItem = (data) => api.post('/items/', data).then(r => r.data)
export const updateItem = (id, data) => api.put(`/items/${id}`, data).then(r => r.data)
export const deleteItem = (id) => api.delete(`/items/${id}`)
/**
 * @param onProgress Rückmeldung 0..100 während der Übertragung. Ohne sie
 *   sieht man bei einem Handyfoto über Mobilfunk sekundenlang gar nichts.
 */
export const uploadImage = (id, file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/items/${id}/image`, form, {
    onUploadProgress: (e) => {
      if (!onProgress) return
      // total fehlt bei manchen Servern -- dann lieber nichts melden als raten
      if (e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  }).then(r => r.data)
}
export const deleteImage = (id) => api.delete(`/items/${id}/image`).then(r => r.data)
export const getCategories = () => api.get('/items/categories').then(r => r.data)
export const getCategoryStats = () => api.get('/items/categories/stats').then(r => r.data)
export const renameCategory = (name, neu) =>
  api.patch(`/items/categories/${encodeURIComponent(name)}`, null, { params: { neu } }).then(r => r.data)
export const deleteCategory = (name) =>
  api.delete(`/items/categories/${encodeURIComponent(name)}`)
// Bereits vergebene Tags -- Vorschläge im Gegenstandsformular
export const getTags = () => api.get('/items/tags').then(r => r.data)

// --- Getränke ---
export const getDrinks = () => api.get('/drinks/').then(r => r.data)
export const createDrink = (data) => api.post('/drinks/', data).then(r => r.data)
export const updateDrink = (id, data) => api.put(`/drinks/${id}`, data).then(r => r.data)
export const deleteDrink = (id) => api.delete(`/drinks/${id}`)
export const deductDrink = (id, amount = 1) => api.post(`/drinks/${id}/deduct`, null, { params: { amount } }).then(r => r.data)
export const restockDrink = (id, amount) => api.post(`/drinks/${id}/restock`, null, { params: { amount } }).then(r => r.data)

// --- Strichliste (jeder nur für sich selbst) ---
export const getAllSummaries = () => api.get('/tally/').then(r => r.data)
export const getMyTally = () => api.get('/tally/me').then(r => r.data)
export const addTally = (drink_id, count = 1) => api.post('/tally/', { drink_id, count }).then(r => r.data)
export const removeLastTally = (drink_id) => api.delete(`/tally/last/${drink_id}`)
export const resetTallies = (user_id) => api.delete(`/tally/reset/${user_id}`)
// Abrechnung für alle: die ganze Strichliste auf null (nur Admin)
export const resetAllTallies = () => api.delete('/tally/').then(r => r.data)

// --- Notizen ---
export const getNotes = () => api.get('/notes/').then(r => r.data)
export const createNote = (data) => api.post('/notes/', data).then(r => r.data)
export const deleteNote = (id) => api.delete(`/notes/${id}`)

// --- Einkaufsliste ---
// mode=lager blendet aus, was erst bis zum nächsten Lager gebraucht wird
export const getShoppingItems = (mode) => api.get('/shopping/', { params: mode ? { mode } : {} }).then(r => r.data)
export const createShoppingItem = (data) => api.post('/shopping/', data).then(r => r.data)
export const updateShoppingItem = (id, data) => api.patch(`/shopping/${id}`, data).then(r => r.data)
export const deleteShoppingItem = (id) => api.delete(`/shopping/${id}`)
export const clearErledigte = () => api.delete('/shopping/')

export const getLocationsTree = (mode) => api.get('/locations/tree', { params: mode ? { mode } : {} }).then(r => r.data)
export const getLocations = (mode) => api.get('/locations/', { params: mode ? { mode } : {} }).then(r => r.data)
export const getLocation = (id) => api.get(`/locations/${id}`).then(r => r.data)
export const createLocation = (data) => api.post('/locations/', data).then(r => r.data)
export const updateLocation = (id, data) => api.put(`/locations/${id}`, data).then(r => r.data)
export const deleteLocation = (id) => api.delete(`/locations/${id}`)
export const moveLocation = (id, direction) => api.patch(`/locations/${id}/move`, null, { params: { direction } }).then(r => r.data)
// Umhängen an einen anderen Elternort (ziel_id 0 = oberste Ebene)
export const getMoveTargets = (id) => api.get(`/locations/${id}/verschiebe-ziele`).then(r => r.data)
// Der Ort selbst und alles darunter -- als Sperrliste für die Zielauswahl
export const getNachfahren = (id, modus = 'lager') =>
  api.get(`/locations/${id}/nachfahren`, { params: { modus } }).then(r => r.data)
export const relocateLocation = (id, ziel_id) =>
  api.patch(`/locations/${id}/verschiebe`, null, { params: { ziel_id } }).then(r => r.data)
export const reorderLocations = (orderedIds) => api.post('/locations/reorder', orderedIds)

// --- Einstellungen ---
export const getLagerZeitraum = () => api.get('/einstellungen/lager-zeitraum').then(r => r.data)
export const setLagerZeitraum = (start, ende) =>
  api.put('/einstellungen/lager-zeitraum', { start, ende }).then(r => r.data)
