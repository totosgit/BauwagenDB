import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import SearchView from './views/SearchView.vue'
import LocationsView from './views/LocationsView.vue'
import ItemsView from './views/ItemsView.vue'
import ItemFormView from './views/ItemFormView.vue'
import ItemDetailView from './views/ItemDetailView.vue'
import DrinksView from './views/DrinksView.vue'
import NotesView from './views/NotesView.vue'
import LoginView from './views/LoginView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/', redirect: '/search' },
    { path: '/search', component: SearchView },
    { path: '/items', component: ItemsView },
    { path: '/items/new', component: ItemFormView },
    { path: '/items/:id', component: ItemDetailView },
    { path: '/items/:id/edit', component: ItemFormView },
    { path: '/locations', component: LocationsView },
    { path: '/drinks', component: DrinksView },
    { path: '/notes', component: NotesView },
  ]
})

// Auth-Status wird einmal gecacht, damit nicht jede Navigation einen Request macht
let authVerified = false

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  if (authVerified) return true

  try {
    await fetch('/api/auth/check', { credentials: 'include' })
      .then(r => { if (!r.ok) throw new Error() })
    authVerified = true
    return true
  } catch {
    return '/login'
  }
})

// Nach erfolgreichem Login: Cache zurücksetzen damit check neu gemacht wird
export function resetAuthCache() { authVerified = false }

createApp(App).use(router).mount('#app')
