<template>
  <span class="tally-marks" :aria-label="count + ' Striche'">
    <!-- Volle Fünfergruppen: vier Striche plus Querstrich -->
    <span v-for="g in fullGroups" :key="'g' + g" class="mark-group">
      <i v-for="n in 4" :key="n" class="mark" />
      <i class="strike" />
    </span>
    <!-- Rest -->
    <span v-if="rest" class="mark-group">
      <i v-for="n in rest" :key="'r' + n" class="mark" />
    </span>
    <span v-if="!count" class="mark-none">—</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  count: { type: Number, default: 0 },
})

const fullGroups = computed(() => Math.floor(props.count / 5))
const rest = computed(() => props.count % 5)
</script>

<style scoped>
.tally-marks {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 14px;
  min-height: 30px;
}

/* Eine Fünfergruppe */
.mark-group {
  position: relative;
  display: inline-flex;
  gap: 5px;
  padding: 2px 0;
}

/* Einzelner Strich -- leicht schief, damit es handgemacht wirkt */
.mark {
  display: block;
  width: 3px;
  height: 26px;
  background: currentColor;
  border-radius: 2px;
}
.mark:nth-child(1) { transform: rotate(-5deg); }
.mark:nth-child(2) { transform: rotate(3deg); }
.mark:nth-child(3) { transform: rotate(-2deg); }
.mark:nth-child(4) { transform: rotate(4deg); }

/* Der Querstrich über die Fünfergruppe */
.strike {
  position: absolute;
  left: -5px;
  top: 50%;
  width: calc(100% + 10px);
  height: 3px;
  background: currentColor;
  border-radius: 2px;
  transform: translateY(-50%) rotate(-18deg);
}

.mark-none { opacity: 0.35; font-size: 22px; }

@media (max-width: 390px) {
  .mark { height: 22px; }
  .tally-marks { gap: 4px 11px; }
}
</style>
