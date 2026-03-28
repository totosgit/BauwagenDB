<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Gegenstände</h1>
    </div>

    <!-- Category filter -->
    <div class="filter-row">
      <button
        class="btn btn-sm"
        :class="activeCategory === null ? 'btn-primary' : 'btn-secondary'"
        @click="activeCategory = null; load()"
      >Alle</button>
      <button
        v-for="cat in categories"
        :key="cat"
        class="btn btn-sm"
        :class="activeCategory === cat ? 'btn-primary' : 'btn-secondary'"
        @click="activeCategory = cat; load()"
      >{{ cat }}</button>
    </div>

    <div v-if="loading" class="loading">Laden ...</div>

    <template v-else>
      <div v-if="!items.length" class="empty">
        <div class="icon">📦</div>
        <div>Noch keine Gegenstände vorhanden</div>
        <button class="btn btn-primary" style="margin-top: 16px" @click="$router.push('/items/new')">Ersten Gegenstand anlegen</button>
      </div>
      <div v-else>
        <div
          v-for="item in items"
          :key="item.id"
          class="item-row"
          @click="$router.push('/items/' + item.id)"
        >
          <div class="item-thumb">
            <img v-if="item.image_path" :src="'/images/' + item.image_path" :alt="item.name" />
            <span v-else>{{ categoryIcon(item.category) }}</span>
          </div>
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-meta">
              {{ item.quantity }} {{ item.unit }}
              <span v-if="activeBreadcrumb(item)"> · 📍 {{ activeBreadcrumb(item) }}</span>
              <span v-if="item.aufgebaut && mode !== 'jahr'" class="aufgebaut-pill">🔧 Aufgebaut</span>
            </div>
          </div>
          <span v-if="item.category" class="tag">{{ item.category }}</span>
        </div>
      </div>
    </template>

    <button class="fab" @click="$router.push('/items/new')">+</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getItems, getCategories } from '../api/index.js'
import { useMode } from '../composables/useMode.js'

const { mode } = useMode()
const items = ref([])
const categories = ref([])
const activeCategory = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const params = { mode: mode.value }
    if (activeCategory.value) params.category = activeCategory.value
    items.value = await getItems(params)
  } finally {
    loading.value = false
  }
}

function categoryIcon(cat) {
  const map = { 'Werkzeug': '🔧', 'Material': '🪵', 'Verbrauchsmaterial': '🔩', 'Elektrik': '⚡', 'Sonstiges': '📦' }
  return map[cat] || '📦'
}

function activeBreadcrumb(item) {
  if (mode.value === 'jahr') return item.breadcrumb_jahr
  return item.breadcrumb_lager
}

onMounted(async () => {
  categories.value = await getCategories()
  await load()
})
</script>

<style scoped>
.filter-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.item-thumb { width: 48px; height: 48px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 28px; border-radius: var(--radius); overflow: hidden; background: var(--surface-2); }
.item-thumb img { width: 100%; height: 100%; object-fit: cover; }
.aufgebaut-pill {
  display: inline-block; padding: 1px 8px; border-radius: 999px;
  background: #2a1800; color: #ffa040; font-size: 12px; font-weight: 700; margin-left: 4px;
}
</style>
