import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

// Bei 401 → Login-Seite (außer wenn wir schon auf /login sind)
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// --- Auth ---
export const login = (password) => api.post('/auth/login', { password }).then(r => r.data)
export const logout = () => api.post('/auth/logout').then(r => r.data)
export const checkAuth = () => api.get('/auth/check').then(r => r.data)

export const searchAll = (q) => api.get('/search/', { params: { q } }).then(r => r.data)

export const getItems = (params = {}) => api.get('/items/', { params }).then(r => r.data)  // params kann { mode, category, location_id } enthalten
export const getItem = (id) => api.get(`/items/${id}`).then(r => r.data)
export const createItem = (data) => api.post('/items/', data).then(r => r.data)
export const updateItem = (id, data) => api.put(`/items/${id}`, data).then(r => r.data)
export const deleteItem = (id) => api.delete(`/items/${id}`)
export const uploadImage = (id, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/items/${id}/image`, form).then(r => r.data)
}
export const deleteImage = (id) => api.delete(`/items/${id}/image`).then(r => r.data)
export const getCategories = () => api.get('/items/categories').then(r => r.data)

// --- Getränke ---
export const getDrinks = () => api.get('/drinks/').then(r => r.data)
export const createDrink = (data) => api.post('/drinks/', data).then(r => r.data)
export const updateDrink = (id, data) => api.put(`/drinks/${id}`, data).then(r => r.data)
export const deleteDrink = (id) => api.delete(`/drinks/${id}`)
export const deductDrink = (id, amount = 1) => api.post(`/drinks/${id}/deduct`, null, { params: { amount } }).then(r => r.data)
export const restockDrink = (id, amount) => api.post(`/drinks/${id}/restock`, null, { params: { amount } }).then(r => r.data)

// --- Gruppenleiter & Strichliste ---
export const getGroupLeaders = () => api.get('/group-leaders/').then(r => r.data)
export const createGroupLeader = (name) => api.post('/group-leaders/', { name }).then(r => r.data)
export const deleteGroupLeader = (id) => api.delete(`/group-leaders/${id}`)
export const getTallySummary = (gl_id) => api.get(`/tally/summary/${gl_id}`).then(r => r.data)
export const getAllSummaries = () => api.get('/tally/all-summaries/').then(r => r.data)
export const addTally = (data) => api.post('/tally/', data).then(r => r.data)
export const deleteTally = (id) => api.delete(`/tally/${id}`)
export const resetTallies = (gl_id) => api.delete(`/tally/reset/${gl_id}`)

// --- Notizen ---
export const getNotes = () => api.get('/notes/').then(r => r.data)
export const createNote = (data) => api.post('/notes/', data).then(r => r.data)
export const deleteNote = (id) => api.delete(`/notes/${id}`)

export const getLocationsTree = (mode) => api.get('/locations/tree', { params: mode ? { mode } : {} }).then(r => r.data)
export const getLocations = (mode) => api.get('/locations/', { params: mode ? { mode } : {} }).then(r => r.data)
export const getLocation = (id) => api.get(`/locations/${id}`).then(r => r.data)
export const createLocation = (data) => api.post('/locations/', data).then(r => r.data)
export const updateLocation = (id, data) => api.put(`/locations/${id}`, data).then(r => r.data)
export const deleteLocation = (id) => api.delete(`/locations/${id}`)
export const moveLocation = (id, direction) => api.patch(`/locations/${id}/move`, null, { params: { direction } }).then(r => r.data)
export const reorderLocations = (orderedIds) => api.post('/locations/reorder', orderedIds)
