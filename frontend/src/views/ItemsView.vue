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

    <div v-if="loading" class="loading">Laden …</div>

    <template v-else>
      <div v-if="!items.length" class="empty">
        <Icon name="dinge" class="icon" />
        <div class="hinweis">Noch nichts aufgenommen</div>
        <button class="btn btn-primary" style="margin-top: 16px" @click="$router.push('/items/new')">
          <Icon name="plus" class="icon" />Ersten Gegenstand aufnehmen
        </button>
      </div>
      <div v-else class="polaroids">
        <Polaroid
          v-for="item in items"
          :key="item.id"
          :item="item"
          :breadcrumb="activeBreadcrumb(item)"
          @oeffnen="$router.push('/items/' + item.id)"
        />
      </div>
    </template>

    <button class="fab" @click="$router.push('/items/new')" aria-label="Gegenstand aufnehmen">
      <Icon name="plus" class="icon" />
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getItems, getCategories } from '../api/index.js'
import { useMode } from '../composables/useMode.js'
import Icon from '../components/Icon.vue'
import Polaroid from '../components/Polaroid.vue'

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
.filter-row { display: flex; gap: 7px; flex-wrap: wrap; margin-bottom: 6px; }

/* Pinnwand: zwei Spalten, mit Luft für die Klebestreifen */
.polaroids {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px 15px;
  margin-top: 12px;
  padding-top: 6px;
}
</style>
