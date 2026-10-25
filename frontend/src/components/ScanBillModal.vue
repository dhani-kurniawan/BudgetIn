<template>
  <BaseModal v-model="open" title="Scan bon" size="sm">
    <div v-if="state === 'choose'" class="choose">
      <p class="hint">Foto bon akan dibaca otomatis: kata “Total” untuk jumlah uang, nama toko untuk kategori, dan sisanya masuk ke catatan. Pastikan seluruh bon terlihat jelas dan tidak gelap.</p>

      <input ref="camInput" type="file" accept="image/*" capture="environment" hidden @change="onPick" />
      <input ref="galInput" type="file" accept="image/*" hidden @change="onPick" />

      <button class="pick-btn primary" type="button" @click="camInput.click()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h3l2-3h6l2 3h3a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V9a1 1 0 011-1z" /><circle cx="12" cy="13" r="3.5" /></svg>
        <span><strong>Ambil foto</strong><small>Buka kamera</small></span>
      </button>
      <button class="pick-btn" type="button" @click="galInput.click()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="1.8" /><path d="M21 16l-5-5-8 9" /></svg>
        <span><strong>Pilih dari galeri</strong><small>Gunakan foto yang sudah ada</small></span>
      </button>
      <button class="link-btn" type="button" @click="skip">Lewati, isi manual</button>
    </div>

    <div v-else-if="state === 'reading'" class="reading">
      <img v-if="preview" :src="preview" alt="Foto bon" />
      <div class="spinner" aria-hidden="true"></div>
      <p><strong>Membaca bon…</strong></p>
      <p v-if="progress" class="hint">{{ progress }}%</p>
      <p v-else class="hint">Pertama kali mungkin agak lama (memuat data baca).</p>
    </div>

    <div v-else class="failed">
      <img v-if="preview" :src="preview" alt="Foto bon" />
      <p class="error-text">{{ error }}</p>
      <p class="hint">Kamu bisa mencoba foto lain, atau lanjut mengisi manual dengan foto ini sebagai lampiran.</p>
    </div>

    <template v-if="state === 'failed'" #footer>
      <button class="btn-ghost" type="button" @click="reset">Foto lain</button>
      <button class="btn-primary" type="button" @click="skip(true)">Isi manual</button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from "vue";
import BaseModal from "./BaseModal.vue";
import { scanBill } from "../services/billScanner";
import { compressImage } from "../utils/image";

const props = defineProps({ modelValue: Boolean });
const emit = defineEmits(["update:modelValue", "done"]);

const open = computed({ get: () => props.modelValue, set: (v) => emit("update:modelValue", v) });

const camInput = ref(null);
const galInput = ref(null);
const state = ref("choose"); // choose | reading | failed
const preview = ref(null);
const progress = ref(0);
const error = ref("");
let lastFile = null;

watch(open, (v) => v && reset());
onBeforeUnmount(() => preview.value && URL.revokeObjectURL(preview.value));

function reset() {
  state.value = "choose";
  progress.value = 0;
  error.value = "";
  lastFile = null;
  if (preview.value) URL.revokeObjectURL(preview.value);
  preview.value = null;
}

async function onPick(e) {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  if (preview.value) URL.revokeObjectURL(preview.value);
  preview.value = URL.createObjectURL(file);
  lastFile = file;
  state.value = "reading";
  progress.value = 0;
  try {
    // Walau total/kategori tidak terbaca, bon tetap dilampirkan; form yang menampilkan peringatannya
    const result = await scanBill(file, (p) => (progress.value = p));
    emit("done", result);
    open.value = false;
  } catch (err) {
    error.value = err.message || "Gagal membaca bon.";
    state.value = "failed";
  }
}

/** Lanjut ke form tanpa hasil scan (foto, kalau ada, tetap dilampirkan). */
async function skip(withPhoto = false) {
  let file = null;
  if (withPhoto === true && lastFile) {
    try {
      file = await compressImage(lastFile);
    } catch {
      file = null;
    }
  }
  emit("done", { file, engine: null, amount: null, manual: true });
  open.value = false;
}
</script>

<style scoped>
.choose { display: flex; flex-direction: column; gap: 0.75rem; }
.hint { margin: 0; font-size: 0.85rem; color: var(--ink-faint); }
.pick-btn {
  display: flex; align-items: center; gap: 0.9rem; text-align: left; width: 100%;
  background: var(--paper); border: 1.5px solid var(--line); border-radius: var(--radius-md);
  padding: 1rem 1.1rem; color: var(--ink);
}
.pick-btn:hover { border-color: var(--navy-500); }
.pick-btn.primary { background: var(--navy-700); border-color: var(--navy-700); color: var(--cream-50); }
.pick-btn svg { width: 30px; height: 30px; flex-shrink: 0; }
.pick-btn span { display: flex; flex-direction: column; }
.pick-btn small { font-size: 0.78rem; opacity: 0.75; }
.link-btn { background: none; border: none; color: var(--navy-500); text-decoration: underline; font-size: 0.85rem; padding: 0.3rem; }
.reading, .failed { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; text-align: center; }
.reading p, .failed p { margin: 0; }
img { max-width: 100%; max-height: 220px; border-radius: var(--radius-sm); border: 1px solid var(--line); }
.spinner {
  width: 34px; height: 34px; border-radius: 50%; border: 4px solid var(--cream-100);
  border-top-color: var(--amber-500); animation: spin 0.9s linear infinite; margin-top: 0.5rem;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
