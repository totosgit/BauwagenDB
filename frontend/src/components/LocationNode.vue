<template>
  <div class="loc-node">
    <div class="loc-row card">

      <!-- Drag-Handle -->
      <span class="drag-handle" title="Verschieben"><Icon name="griff" class="icon" /></span>

      <!-- Expand-Toggle -->
      <button
        class="expand-btn"
        :class="{ 'no-children': !node.children?.length }"
        @click.stop="toggle(node.id)"
      >
        <Icon v-if="node.children?.length" :name="expanded ? 'ab' : 'weiter'" class="icon" />
        <span v-else class="leaf-dot">·</span>
      </button>

      <!-- Icon + Name + Meta -->
      <div class="loc-main" @click="node.children?.length && toggle(node.id)">
        <span class="type-icon"><Icon :name="typIcon(node.type)" class="icon" /></span>
        <div class="loc-info">
          <div class="loc-name">{{ node.name }}</div>
          <div class="loc-meta">
            <span class="type-badge">{{ typLabel(node.type) }}</span>
            <span v-if="node.item_count" class="meta-pill">{{ node.item_count }} Dinge</span>
            <span v-if="node.children?.length" class="meta-pill meta-children">
              {{ node.children.length }}<Icon :name="expanded ? 'ab' : 'weiter'" class="icon" />
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
        <button class="btn btn-secondary btn-sm" @click="handlers.onRelocate(node)" aria-label="Woanders hin verschieben"><Icon name="umziehen" class="icon" /></button>
        <button class="btn btn-secondary btn-sm" @click="handlers.onEdit(node)" aria-label="Bearbeiten"><Icon name="stift" class="icon" /></button>
        <button class="btn btn-sm btn-del" @click="handlers.onDelete(node)" aria-label="Löschen"><Icon name="muell" class="icon" /></button>
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
import Icon from './Icon.vue'
import { typIcon, typLabel } from '../utils/orttypen.js'

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
.btn-del { background: transparent; color: var(--rot); box-shadow: inset 0 0 0 1.5px rgba(158,58,34,.5); }

/* Kinder */
.loc-children {
  margin-left: 20px;
  padding-left: 12px;
  border-left: 2px solid var(--border);
}

/* Drag-Zustände */
.drag-ghost { opacity: 0.35; background: var(--green-pale) !important; }
.drag-chosen { box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important; }

@media (max-width: 480px) {
  .loc-row {
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 10px;
    min-height: unset;
  }
  /* Erste Zeile: Handle + Expand + Icon + Name füllen die ganze Breite */
  .loc-main {
    order: 1;
    flex: 1 1 0;
    min-width: 0;
  }
  .drag-handle { order: 0; }
  .expand-btn  { order: 0; }
  /* Zweite Zeile: Aktionen rechtsbündig */
  .loc-actions {
    order: 2;
    flex-basis: 100%;
    justify-content: flex-end;
    gap: 6px;
    padding-left: 80px; /* eingerückt unter dem Namen */
  }
  .loc-children {
    margin-left: 12px;
    padding-left: 8px;
  }
}
</style>
