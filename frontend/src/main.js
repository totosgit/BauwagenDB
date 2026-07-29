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
import ShoppingView from './views/ShoppingView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import ProfileView from './views/ProfileView.vue'
import AdminView from './views/AdminView.vue'
import { useAuth } from './composables/useAuth.js'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/register', component: RegisterView, meta: { public: true } },
    { path: '/', redirect: '/search' },
    { path: '/search', component: SearchView },
    { path: '/items', component: ItemsView },
    { path: '/items/new', component: ItemFormView },
    { path: '/items/:id', component: ItemDetailView },
    { path: '/items/:id/edit', component: ItemFormView },
    { path: '/locations', component: LocationsView },
    { path: '/drinks', component: DrinksView },
    { path: '/notes', component: NotesView },
    { path: '/shopping', component: ShoppingView },
    { path: '/profile', component: ProfileView },
    { path: '/users/:id', component: ProfileView },
    { path: '/admin', component: AdminView, meta: { admin: true } },
  ]
})

const { ensureLoaded, user } = useAuth()

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  // Wird nur beim ersten Aufruf zum Request -- danach aus dem Cache.
  await ensureLoaded()
  if (!user.value) return { path: '/login', query: { weiter: to.fullPath } }

  if (to.meta.admin && !user.value.is_superuser) return '/profile'
  return true
})

createApp(App).use(router).mount('#app')
