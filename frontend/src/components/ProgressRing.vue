<template>
  <div class="ring" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :viewBox="`0 0 ${size} ${size}`">
      <circle :cx="c" :cy="c" :r="r" fill="none" stroke="var(--cream-100)" :stroke-width="stroke" />
      <circle
        :cx="c" :cy="c" :r="r" fill="none" :stroke="color" :stroke-width="stroke" stroke-linecap="round"
        :stroke-dasharray="circ" :stroke-dashoffset="offset" :transform="`rotate(-90 ${c} ${c})`"
        style="transition: stroke-dashoffset 0.6s ease"
      />
    </svg>
    <div class="ring-label">
      <slot><strong>{{ Math.round(percent) }}%</strong></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  percent: { type: Number, default: 0 },
  size: { type: Number, default: 96 },
  stroke: { type: Number, default: 9 },
  color: { type: String, default: "var(--green-500)" },
});

const c = computed(() => props.size / 2);
const r = computed(() => (props.size - props.stroke) / 2);
const circ = computed(() => 2 * Math.PI * r.value);
const offset = computed(() => circ.value * (1 - Math.min(Math.max(props.percent, 0), 100) / 100));
</script>

<style scoped>
.ring { position: relative; flex-shrink: 0; }
.ring svg { width: 100%; height: 100%; display: block; }
.ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  color: var(--navy-700);
  font-size: 0.95rem;
  text-align: center;
}
</style>
