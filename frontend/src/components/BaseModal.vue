<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @mousedown.self="close">
      <div class="modal" :class="size" role="dialog" aria-modal="true">
        <div class="modal-head">
          <h2>{{ title }}</h2>
          <button class="icon-btn" type="button" aria-label="Tutup" @click="close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
        <div class="modal-body"><slot /></div>
        <div v-if="$slots.footer" class="modal-foot"><slot name="footer" /></div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { watch, onBeforeUnmount } from "vue";

const props = defineProps({
  modelValue: Boolean,
  title: { type: String, default: "" },
  size: { type: String, default: "md" }, // sm | md | lg
});
const emit = defineEmits(["update:modelValue"]);

function close() {
  emit("update:modelValue", false);
}
function onKey(e) {
  if (e.key === "Escape") close();
}

watch(
  () => props.modelValue,
  (open) => {
    document.body.style.overflow = open ? "hidden" : "";
    if (open) window.addEventListener("keydown", onKey);
    else window.removeEventListener("keydown", onKey);
  }
);

onBeforeUnmount(() => {
  document.body.style.overflow = "";
  window.removeEventListener("keydown", onKey);
});
</script>

<style>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(19, 41, 63, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 100;
}
.modal {
  background: var(--paper);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 520px;
  max-height: calc(100vh - 2rem);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(19, 41, 63, 0.3);
}
.modal.sm { max-width: 400px; }
.modal.lg { max-width: 680px; }
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.4rem;
  border-bottom: 1px solid var(--line);
}
.modal-head h2 { margin: 0; }
.modal-body { padding: 1.25rem 1.4rem; overflow-y: auto; }
.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  padding: 1rem 1.4rem;
  border-top: 1px solid var(--line);
}

/* Di HP: modal naik dari bawah (bottom sheet) */
@media (max-width: 560px) {
  .modal-overlay { align-items: flex-end; padding: 0; }
  .modal {
    max-width: none;
    max-height: 92vh;
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
  }
  .modal-foot > button { flex: 1; }
}
</style>
