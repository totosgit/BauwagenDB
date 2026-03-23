<template>
  <div class="loc-node">
    <div class="loc-row card">

      <!-- Drag-Handle -->
      <span class="drag-handle" title="Verschieben">⠿</span>

      <!-- Expand-Toggle -->
      <button
        class="expand-btn"
        :class="{ 'no-children': !node.children?.length }"
        @click.stop="toggle(node.id)"
      >
        <span v-if="node.children?.length">{{ expanded ? '▾' : '▸' }}</span>
        <span v-else class="leaf-dot">·</span>
      </button>

      <!-- Icon + Name + Meta -->
      <div class="loc-main" @click="node.children?.length && toggle(node.id)">
        <span class="type-icon">{{ TYPE_ICON[node.type] || '📌' }}</span>
        <div class="loc-info">
          <div class="loc-name">{{ node.name }}</div>
          <div class="loc-meta">
            <span class="type-badge">{{ TYPE_LABEL[node.type] || node.type }}</span>
            <span v-if="node.item_count" class="meta-pill">{{ node.item_count }} Dinge</span>
            <span v-if="node.children?.length" class="meta-pill meta-children">
              {{ node.children.length }} {{ expanded ? '▾' : '▸' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Aktionen -->
      <div class="loc-actions">
        <button
          v-if="canHaveChildren"
          class="btn btn-secondary btn-sm"
          @click="handlers.onCreate(node.id)"
          title="Unterbereich anlegen"
        >+</button>
        <button class="btn btn-secondary btn-sm" @click="handlers.onEdit(node)">✏️</button>
        <button class="btn btn-sm btn-del" @click="handlers.onDelete(node)">🗑️</button>
      </div>
    </div>

    <!-- Kinder als draggable Liste -->
    <div v-if="expanded && node.children?.length" class="loc-children">
      <draggable
        :list="node.children"
        item-key="id"
        handle=".drag-handle"
        :animation="150"
        ghost-class="drag-ghost"
        chosen-class="drag-chosen"
        @end="onDragEnd(node.children)"
      >
        <template #item="{ element, index }">
          <LocationNode :node="element" />
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup>
import { inject, computed } from 'vue'
import draggable from 'vuedraggable'
import { useExpanded } from '../composables/useExpanded.js'

const props = defineProps({
  node: { type: Object, required: true },
})

const handlers = inject('locHandlers')
const { isExpanded, toggle } = useExpanded()
const expanded = computed(() => isExpanded(props.node.id))

const VALID_CHILDREN = {
  bauwagen:  ['regal', 'schrank', 'kiste', 'wand'],
  schopf:    ['regal', 'schrank', 'kiste', 'wand'],
  sonstiges: ['regal', 'schrank', 'kiste', 'wand', 'sonstiges'],
  regal:     ['fach'],
  fach:      ['boden'],
  schrank:   ['boden'],
  boden:     ['kiste'],
  kiste:     [],
  wand:      [],
}
const TYPE_ICON = {
  bauwagen: '🚌', schopf: '🏚️', sonstiges: '🏠',
  regal: '🗄️', schrank: '🪟',
  fach: '🗃️', boden: '▭',
  kiste: '📦', wand: '🧱',
}
const TYPE_LABEL = {
  bauwagen: 'Bauwagen', schopf: 'Schopf', sonstiges: 'Sonstiges',
  regal: 'Regal', schrank: 'Schrank',
  fach: 'Fach', boden: 'Boden',
  kiste: 'Kiste', wand: 'Wand',
}

const canHaveChildren = computed(
  () => (VALID_CHILDREN[props.node.type] ?? []).length > 0
)

function onDragEnd(siblings) {
  // Neue Reihenfolge an das Backend senden
  handlers.onReorder(siblings.map(s => s.id))
}
</script>

<style scoped>
.loc-node { margin-top: 8px; }

.loc-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  min-height: 62px;
}

/* Drag-Handle */
.drag-handle {
  font-size: 20px;
  color: var(--border);
  cursor: grab;
  padding: 6px 4px;
  flex-shrink: 0;
  touch-action: none;
  user-select: none;
  line-height: 1;
}
.drag-handle:active { cursor: grabbing; color: var(--green); }

/* Expand */
.expand-btn {
  width: 34px; height: 34px; flex-shrink: 0;
  border: none; background: var(--cream); border-radius: 8px;
  font-size: 18px; cursor: pointer; display: flex; align-items: center;
  justify-content: center; color: var(--text-muted);
  -webkit-tap-highlight-color: transparent; transition: background 0.12s;
}
.expand-btn:active { background: var(--border); }
.expand-btn.no-children { cursor: default; background: transparent; }
.leaf-dot { font-size: 22px; color: var(--border); }

/* Hauptbereich */
.loc-main {
  display: flex; align-items: center; gap: 10px;
  flex: 1; min-width: 0; cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.type-icon { font-size: 24px; flex-shrink: 0; }
.loc-info { flex: 1; min-width: 0; }
.loc-name {
  font-weight: 700; font-size: 16px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.loc-meta { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 3px; }
.meta-pill {
  font-size: 11px; font-weight: 600; padding: 2px 7px;
  border-radius: 999px; background: var(--cream); color: var(--text-muted);
}
.meta-children { color: var(--green); background: var(--green-pale); }

/* Aktionen */
.loc-actions { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.btn-del { background: #fff0f0; color: #c62828; }

/* Kinder */
.loc-children {
  margin-left: 20px;
  padding-left: 12px;
  border-left: 2px solid var(--border);
}

/* Drag-Zustände */
.drag-ghost { opacity: 0.35; background: var(--green-pale) !important; }
.drag-chosen { box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important; }
</style>
