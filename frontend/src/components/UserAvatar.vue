<template>
  <span class="avatar" :style="{ width: size + 'px', height: size + 'px', fontSize: size * 0.38 + 'px' }">
    <img v-if="src" :src="src" alt="Foto profil" />
    <template v-else>{{ initials(user?.name) }}</template>
  </span>
</template>

<script setup>
import { computed } from "vue";
import { photoSrc } from "../services/api";
import { initials } from "../utils/format";

const props = defineProps({
  user: { type: Object, default: null },
  size: { type: Number, default: 36 },
  previewUrl: { type: String, default: null }, // preview lokal sebelum disimpan
});

const src = computed(() => props.previewUrl || photoSrc(props.user));
</script>

<style scoped>
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--navy-700);
  color: var(--cream-50);
  font-family: var(--font-display);
  font-weight: 600;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid var(--amber-500);
}
.avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
</style>
