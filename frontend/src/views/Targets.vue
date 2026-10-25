<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Target keuangan</h1>
        <p>Pantau batas pengeluaran dan target tabunganmu.</p>
      </div>
      <button class="btn-primary" type="button" @click="openAdd">+ Tambah Target</button>
    </div>

    <div class="tabs-row">
      <div class="tabs">
        <button v-for="f in filterTabs" :key="f.value" :class="{ active: filter === f.value }" @click="filter = f.value">
          {{ f.label }} ({{ countFor(f.value) }})
        </button>
      </div>
    </div>

    <p v-if="loading" class="empty-text">Memuat target...</p>
    <div v-else-if="!visible.length" class="card empty-card">
      <p class="empty-text">{{ targets.length ? "Tidak ada target pada kategori ini." : "Belum ada target. Buat target pertamamu!" }}</p>
      <button v-if="!targets.length" class="btn-primary" type="button" @click="openAdd">+ Tambah Target</button>
    </div>

    <div v-else class="target-grid">
      <article v-for="t in visible" :key="t.id" class="card target-card">
        <header class="target-top">
          <div class="target-title">
            <h3>{{ t.name }}</h3>
            <div class="chips">
              <span class="chip">{{ t.type === "expense_limit" ? "Batas pengeluaran" : "Tabungan" }}</span>
              <span v-if="t.category_name" class="chip amber">{{ t.category_name }}</span>
              <span class="chip" :class="statusMeta(t).chip">{{ statusMeta(t).label }}</span>
            </div>
          </div>
          <div class="row-actions">
            <button class="icon-btn" type="button" title="Edit" aria-label="Edit" @click="openEdit(t)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z" /></svg>
            </button>
            <button class="icon-btn danger" type="button" title="Hapus" aria-label="Hapus" @click="askDelete(t)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18" /><path d="M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /><path d="M10 11v6M14 11v6" /></svg>
            </button>
          </div>
        </header>

        <div class="target-body">
          <ProgressRing :percent="t.progress_percent" :size="92" :stroke="10" :color="statusMeta(t).color">
            <strong>{{ Math.round(t.progress_percent) }}%</strong>
          </ProgressRing>
          <div class="target-figures">
            <span class="fig-label">{{ t.type === "expense_limit" ? "Terpakai" : "Terkumpul" }}</span>
            <strong class="fig-main">{{ formatRupiah(t.current_value) }}</strong>
            <span class="fig-sub">dari {{ formatRupiah(t.target_amount) }}</span>
            <span class="fig-sub remaining">{{ remainingText(t) }}</span>
          </div>
        </div>

        <div class="bar-track"><div class="bar-fill" :style="{ width: Math.min(t.progress_percent, 100) + '%', background: statusMeta(t).color }"></div></div>

        <footer class="target-foot">
          <span>{{ formatDate(t.period_start) }} – {{ formatDate(t.period_end) }}</span>
          <span class="days">{{ daysText(t) }}</span>
        </footer>
        <p v-if="t.note" class="target-note">{{ t.note }}</p>
      </article>
    </div>

    <!-- Pop up tambah/edit -->
    <BaseModal v-model="formOpen" :title="editingId ? 'Edit Target' : 'Tambah Target'">
      <form id="target-form" @submit.prevent="save">
        <div class="type-toggle">
          <button type="button" :class="{ active: form.type === 'expense_limit' }" @click="setType('expense_limit')">Batas pengeluaran</button>
          <button type="button" :class="{ active: form.type === 'savings' }" @click="setType('savings')">Tabungan</button>
        </div>

        <div class="field">
          <label for="t-name">Nama target</label>
          <input id="t-name" v-model="form.name" maxlength="100" placeholder="Contoh: Makan bulan Oktober" required />
        </div>

        <div class="field">
          <label for="t-amount">{{ form.type === "expense_limit" ? "Batas maksimal (Rp)" : "Target tabungan (Rp)" }}</label>
          <input id="t-amount" v-model.number="form.target_amount" type="number" min="1" step="any" inputmode="numeric" required />
        </div>

        <div class="field-row">
          <div class="field">
            <label for="t-start">Tanggal mulai</label>
            <input id="t-start" v-model="form.period_start" type="date" required />
          </div>
          <div class="field">
            <label for="t-end">Tanggal selesai</label>
            <input id="t-end" v-model="form.period_end" type="date" :min="form.period_start" required />
          </div>
        </div>

        <div v-if="form.type === 'expense_limit'" class="field">
          <label for="t-cat">Kategori</label>
          <select id="t-cat" v-model="form.category_id">
            <option value="">Semua kategori pengeluaran</option>
            <option v-for="c in expenseCategories" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
          </select>
          <p class="field-hint">Kosongkan untuk membatasi total seluruh pengeluaran.</p>
        </div>
        <p v-else class="field-hint savings-hint">Progres tabungan dihitung dari total pemasukan dikurangi pengeluaran pada periode ini.</p>

        <div class="field">
          <label for="t-note">Catatan</label>
          <textarea id="t-note" v-model="form.note" rows="2" maxlength="255" placeholder="Opsional"></textarea>
        </div>

        <p v-if="formError" class="error-text">{{ formError }}</p>
      </form>
      <template #footer>
        <button class="btn-ghost" type="button" @click="formOpen = false">Batal</button>
        <button class="btn-primary" type="submit" form="target-form" :disabled="saving">{{ saving ? "Menyimpan..." : "Simpan" }}</button>
      </template>
    </BaseModal>

    <BaseModal v-model="deleteOpen" title="Hapus target?" size="sm">
      <p v-if="toDelete" class="confirm-text">Target “{{ toDelete.name }}” akan dihapus. Transaksimu tidak ikut terhapus.</p>
      <template #footer>
        <button class="btn-ghost" type="button" @click="deleteOpen = false">Batal</button>
        <button class="btn-danger" type="button" :disabled="saving" @click="confirmDelete">Hapus</button>
      </template>
    </BaseModal>

    <div v-if="toast.msg" class="toast" :class="toast.type">{{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import api from "../services/api";
import BaseModal from "../components/BaseModal.vue";
import ProgressRing from "../components/ProgressRing.vue";
import { formatRupiah, formatDate, todayISO, monthRange } from "../utils/format";

const targets = ref([]);
const categories = ref([]);
const loading = ref(true);

/* ---------- Filter daftar ---------- */
const filter = ref("active");
const filterTabs = [
  { value: "active", label: "Aktif" },
  { value: "finished", label: "Selesai" },
  { value: "all", label: "Semua" },
];
const matches = (t, f) => (f === "all" ? true : f === "active" ? !t.is_finished : t.is_finished);
const countFor = (f) => targets.value.filter((t) => matches(t, f)).length;
const visible = computed(() => targets.value.filter((t) => matches(t, filter.value)));

const expenseCategories = computed(() => categories.value.filter((c) => c.type === "expense"));

/* ---------- Tampilan status ---------- */
function statusMeta(t) {
  return {
    aman: { label: "Aman", chip: "green", color: "var(--green-500)" },
    mendekati_batas: { label: "Mendekati batas", chip: "amber", color: "var(--amber-500)" },
    terlampaui: { label: "Terlampaui", chip: "red", color: "var(--red-600)" },
    tercapai: { label: "Tercapai", chip: "green", color: "var(--green-500)" },
    belum_tercapai: { label: "Belum tercapai", chip: "", color: "var(--navy-500)" },
  }[t.status];
}
function remainingText(t) {
  const diff = t.target_amount - t.current_value;
  if (t.type === "expense_limit") return diff >= 0 ? `Sisa ${formatRupiah(diff)}` : `Lewat ${formatRupiah(-diff)}`;
  return diff > 0 ? `Kurang ${formatRupiah(diff)}` : "Target tercapai 🎉";
}
function daysText(t) {
  if (t.days_left < 0) return "Periode selesai";
  if (!t.is_active) return "Belum dimulai";
  return t.days_left === 0 ? "Berakhir hari ini" : `${t.days_left} hari lagi`;
}

/* ---------- Form ---------- */
const formOpen = ref(false);
const editingId = ref(null);
const saving = ref(false);
const formError = ref("");

const blankForm = () => {
  const m = monthRange(0);
  return { type: "expense_limit", name: "", target_amount: null, period_start: todayISO(), period_end: m.end, category_id: "", note: "" };
};
const form = reactive(blankForm());

function setType(t) {
  form.type = t;
  if (t === "savings") form.category_id = "";
}

function openAdd() {
  editingId.value = null;
  Object.assign(form, blankForm());
  formError.value = "";
  formOpen.value = true;
}

function openEdit(t) {
  editingId.value = t.id;
  Object.assign(form, {
    type: t.type,
    name: t.name,
    target_amount: t.target_amount,
    period_start: t.period_start,
    period_end: t.period_end,
    category_id: t.category_id ? String(t.category_id) : "",
    note: t.note || "",
  });
  formError.value = "";
  formOpen.value = true;
}

async function save() {
  formError.value = "";
  if (!(form.target_amount > 0)) return (formError.value = "Nominal target harus lebih dari 0");
  if (form.period_end < form.period_start) return (formError.value = "Tanggal selesai tidak boleh sebelum tanggal mulai");

  saving.value = true;
  const payload = {
    type: form.type,
    name: form.name,
    target_amount: form.target_amount,
    period_start: form.period_start,
    period_end: form.period_end,
    category_id: form.type === "expense_limit" && form.category_id ? Number(form.category_id) : null,
    note: form.note,
  };
  try {
    if (editingId.value) await api.put(`/targets/${editingId.value}`, payload);
    else await api.post("/targets", payload);
    formOpen.value = false;
    await load();
    showToast(editingId.value ? "Target diperbarui" : "Target ditambahkan");
  } catch (err) {
    formError.value = err.response?.data?.error || "Gagal menyimpan target";
  } finally {
    saving.value = false;
  }
}

/* ---------- Hapus ---------- */
const deleteOpen = ref(false);
const toDelete = ref(null);
function askDelete(t) {
  toDelete.value = t;
  deleteOpen.value = true;
}
async function confirmDelete() {
  saving.value = true;
  try {
    await api.delete(`/targets/${toDelete.value.id}`);
    deleteOpen.value = false;
    await load();
    showToast("Target dihapus");
  } catch (err) {
    showToast(err.response?.data?.error || "Gagal menghapus", "error");
  } finally {
    saving.value = false;
  }
}

/* ---------- Toast & loader ---------- */
const toast = reactive({ msg: "", type: "ok" });
let toastTimer;
function showToast(msg, type = "ok") {
  Object.assign(toast, { msg, type });
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.msg = ""), 2500);
}

async function load() {
  const { data } = await api.get("/targets");
  targets.value = data;
}

onMounted(async () => {
  try {
    const [, cats] = await Promise.all([load(), api.get("/categories")]);
    categories.value = cats.data;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.tabs-row { margin-bottom: 1rem; }
.empty-card { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; padding: 2.5rem 1rem; }

.target-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.1rem; }
.target-card { display: flex; flex-direction: column; gap: 1rem; min-width: 0; }
.target-top { display: flex; justify-content: space-between; gap: 0.75rem; align-items: flex-start; }
.target-title { min-width: 0; }
.target-title h3 { margin-bottom: 0.4rem; overflow-wrap: anywhere; }
.chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.row-actions { display: flex; gap: 0.4rem; flex-shrink: 0; }

.target-body { display: flex; align-items: center; gap: 1.1rem; }
.target-figures { display: flex; flex-direction: column; min-width: 0; }
.fig-label { font-size: 0.75rem; color: var(--ink-faint); font-weight: 600; }
.fig-main { font-family: var(--font-display); font-size: 1.25rem; color: var(--navy-700); overflow-wrap: anywhere; }
.fig-sub { font-size: 0.82rem; color: var(--ink-soft); }
.fig-sub.remaining { font-weight: 600; margin-top: 0.15rem; }

.bar-track { height: 8px; background: var(--cream-100); border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }

.target-foot { display: flex; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap; font-size: 0.78rem; color: var(--ink-faint); }
.days { font-weight: 600; color: var(--navy-500); }
.target-note { margin: 0; font-size: 0.82rem; background: var(--cream-100); border-radius: var(--radius-sm); padding: 0.5rem 0.7rem; }

.type-toggle { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; background: var(--cream-100); border-radius: var(--radius-sm); padding: 4px; margin-bottom: 1rem; }
.type-toggle button { border: none; background: transparent; padding: 0.55rem; color: var(--ink-soft); font-size: 0.88rem; }
.type-toggle button.active { background: var(--navy-700); color: var(--cream-50); }
.savings-hint { background: var(--cream-100); border-radius: var(--radius-sm); padding: 0.6rem 0.8rem; margin: 0 0 0.9rem; }
.confirm-text { margin: 0; }

@media (max-width: 800px) {
  .target-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .page-header > button { width: 100%; }
  .tabs { width: 100%; }
  .tabs button { flex: 1; padding: 0.5rem 0.4rem; }
}
</style>
