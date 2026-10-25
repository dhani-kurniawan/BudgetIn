<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Transaksi</h1>
        <p>Catatan pemasukan dan pengeluaranmu. Data disimpan maksimal 3 tahun.</p>
      </div>
      <div class="header-actions">
        <button class="btn-ghost" type="button" :disabled="!filtered.length" @click="exportCsv">Ekspor CSV</button>
        <button class="btn-primary" type="button" @click="openAdd">+ Tambah Transaksi</button>
      </div>
    </div>

    <!-- Tab -->
    <div class="tabs-row">
      <div class="tabs">
        <button :class="{ active: tab === 'expense' }" @click="tab = 'expense'">Pengeluaran ({{ counts.expense }})</button>
        <button :class="{ active: tab === 'income' }" @click="tab = 'income'">Pemasukan ({{ counts.income }})</button>
      </div>
    </div>

    <!-- Saldo per sumber dana -->
    <div v-if="sourceList.length" class="sources-strip">
      <div v-for="s in sourceList" :key="s.id" class="source-chip" :class="{ low: s.balance <= 0 }">
        <span class="source-name">{{ s.name }}</span>
        <strong>{{ formatRupiah(s.balance) }}</strong>
        <small>sisa dari {{ formatRupiah(s.income) }}</small>
      </div>
    </div>

    <!-- Search & filter -->
    <div class="card toolbar">
      <div class="search-row">
        <input v-model="searchInput" type="search" placeholder="Cari kategori atau catatan..." />
        <button class="btn-ghost" type="button" @click="showFilters = !showFilters">
          Filter<span v-if="activeFilterCount" class="badge">{{ activeFilterCount }}</span>
        </button>
      </div>

      <div v-show="showFilters" class="filters">
        <div class="field">
          <label>Kategori</label>
          <select v-model="filters.category_id">
            <option value="">Semua</option>
            <option v-for="c in tabCategories" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Mata uang</label>
          <select v-model="filters.currency">
            <option value="">Semua</option>
            <option v-for="c in usedCurrencies" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div v-if="tab === 'expense'" class="field">
          <label>Sumber dana</label>
          <select v-model="filters.source_id">
            <option value="">Semua</option>
            <option v-for="s in allSources" :key="s.id" :value="String(s.id)">{{ s.name }}</option>
            <option value="none">Belum dikelompokkan</option>
          </select>
        </div>
        <div class="field">
          <label>Tanggal dari</label>
          <input v-model="filters.date_from" type="date" />
        </div>
        <div class="field">
          <label>Tanggal sampai</label>
          <input v-model="filters.date_to" type="date" />
        </div>
        <div class="field">
          <label>Total (Rp) min</label>
          <input v-model.number="filters.amount_min" type="number" min="0" placeholder="0" />
        </div>
        <div class="field">
          <label>Total (Rp) maks</label>
          <input v-model.number="filters.amount_max" type="number" min="0" placeholder="∞" />
        </div>
        <div class="field">
          <label>Kurs min</label>
          <input v-model.number="filters.rate_min" type="number" min="0" step="any" />
        </div>
        <div class="field">
          <label>Kurs maks</label>
          <input v-model.number="filters.rate_max" type="number" min="0" step="any" />
        </div>
        <div class="filters-foot">
          <button class="btn-ghost btn-sm" type="button" @click="resetFilters">Reset filter</button>
        </div>
      </div>
    </div>

    <!-- Ringkasan hasil -->
    <div class="result-bar">
      <span>{{ filtered.length }} transaksi</span>
      <strong :class="tab">Total: {{ formatRupiah(filteredTotal) }}</strong>
    </div>

    <!-- Tabel -->
    <div class="card table-card">
      <p v-if="loading" class="empty-text">Memuat data...</p>
      <p v-else-if="!filtered.length" class="empty-text">
        {{ rows.length ? "Tidak ada transaksi yang cocok dengan pencarian/filter." : "Belum ada transaksi." }}
      </p>

      <table v-else class="tx-table">
        <thead>
          <tr>
            <th class="sortable" @click="toggleSort('transaction_date')">Tanggal {{ sortIcon("transaction_date") }}</th>
            <th>Kategori</th>
            <th v-if="tab === 'expense'">Sumber dana</th>
            <th class="num sortable" @click="toggleSort('amount')">Jumlah Uang {{ sortIcon("amount") }}</th>
            <th class="num">Kurs ke IDR</th>
            <th class="num sortable" @click="toggleSort('amount_idr')">Total (Rp) {{ sortIcon("amount_idr") }}</th>
            <th>Catatan</th>
            <th class="actions-col">Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in paged" :key="t.id">
            <td data-label="Tanggal">{{ formatDate(t.transaction_date) }}</td>
            <td data-label="Kategori"><span class="chip">{{ t.category_name }}</span></td>
            <td v-if="tab === 'expense'" data-label="Sumber dana">
              <span class="chip" :class="t.source_name ? 'green' : 'amber'">{{ t.source_name || "Belum dikelompokkan" }}</span>
            </td>
            <td data-label="Jumlah Uang" class="num"><span class="ccy">{{ t.currency_code }}</span> {{ formatNumber(t.amount, 2) }}</td>
            <td data-label="Kurs ke IDR" class="num">{{ t.currency_code === "IDR" ? "-" : "Rp " + formatNumber(t.exchange_rate, 2) }}</td>
            <td data-label="Total (Rp)" class="num strong" :class="t.type">{{ formatRupiah(t.amount_idr) }}</td>
            <td data-label="Catatan" class="note">{{ t.note || "-" }}</td>
            <td class="actions-col">
              <div class="row-actions">
                <button v-if="t.has_receipt" class="icon-btn" type="button" title="Lihat foto bon" aria-label="Lihat foto bon" @click="viewReceipt(t)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h12v20l-3-2-3 2-3-2-3 2z" /><path d="M9 7h6M9 11h6M9 15h3" /></svg>
                </button>
                <button class="icon-btn" type="button" title="Edit" aria-label="Edit" @click="openEdit(t)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z" /></svg>
                </button>
                <button class="icon-btn danger" type="button" title="Hapus" aria-label="Hapus" @click="askDelete(t)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18" /><path d="M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /><path d="M10 11v6M14 11v6" /></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="filtered.length" class="pager">
        <label class="per-page">
          Tampil
          <select v-model.number="perPage">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </label>
        <div class="pager-nav">
          <button class="btn-ghost btn-sm" :disabled="page <= 1" @click="page--">‹</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button class="btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++">›</button>
        </div>
      </div>
    </div>

    <!-- Modal tambah/edit -->
    <BaseModal v-model="formOpen" :title="editingId ? 'Edit Transaksi' : 'Tambah Transaksi'">
      <form id="tx-form" @submit.prevent="save">
        <div class="type-toggle">
          <button type="button" :class="{ active: form.type === 'expense' }" @click="setType('expense')">Pengeluaran</button>
          <button type="button" :class="{ active: form.type === 'income' }" @click="setType('income')">Pemasukan</button>
        </div>

        <!-- Foto bon -->
        <div class="receipt-box" :class="{ filled: receiptSrc }">
          <input ref="receiptCam" type="file" accept="image/*" capture="environment" hidden @change="onReceiptPick" />
          <input ref="receiptGal" type="file" accept="image/*" hidden @change="onReceiptPick" />
          <template v-if="receiptSrc">
            <img :src="receiptSrc" class="receipt-thumb" alt="Foto bon" />
            <div class="receipt-side">
              <strong>Foto bon terlampir</strong>
              <div class="receipt-actions">
                <button v-if="receiptFile" class="btn-primary btn-sm" type="button" :disabled="scanning" @click="rescan">
                  {{ scanning ? `Membaca… ${scanProgress ? scanProgress + "%" : ""}` : "Isi otomatis dari bon" }}
                </button>
                <button class="btn-ghost btn-sm" type="button" @click="receiptGal.click()">Ganti</button>
                <button class="btn-ghost btn-sm" type="button" @click="clearReceipt">Hapus</button>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="receipt-side">
              <strong>Foto bon <small>(opsional)</small></strong>
              <span class="field-hint">Lampirkan bon sebagai bukti, atau scan agar form terisi otomatis.</span>
              <div class="receipt-actions">
                <button class="btn-ghost btn-sm" type="button" @click="receiptCam.click()">Ambil foto</button>
                <button class="btn-ghost btn-sm" type="button" @click="receiptGal.click()">Dari galeri</button>
              </div>
            </div>
          </template>
        </div>
        <p v-if="scanMsg.text" class="scan-msg" :class="scanMsg.type">{{ scanMsg.text }}</p>

        <div class="field" :class="{ 'needs-input': needsCategory }">
          <label for="f-cat">Kategori</label>
          <select id="f-cat" v-model="form.category_id" required>
            <option value="" disabled>Pilih kategori</option>
            <option v-for="c in formCategories" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
          </select>
        </div>

        <div class="field newcat">
          <button v-if="!newCatOpen" class="link-btn" type="button" @click="newCatOpen = true">
            + Kategori {{ form.type === "income" ? "pemasukan" : "pengeluaran" }} baru
          </button>
          <div v-else class="newcat-row">
            <input v-model="newCatName" maxlength="50" placeholder="Nama kategori" @keydown.enter.prevent="addCategory" />
            <button class="btn-ghost btn-sm" type="button" @click="addCategory">Tambah</button>
            <button class="btn-ghost btn-sm" type="button" @click="newCatOpen = false">Batal</button>
          </div>
          <p v-if="form.type === 'income'" class="field-hint">Kategori pemasukan juga menjadi sumber dana untuk pengeluaran.</p>
        </div>

        <div v-if="form.type === 'expense'" class="field">
          <label for="f-src">Dibayar dari (sumber dana)</label>
          <select id="f-src" v-model="form.source_id" required>
            <option value="" disabled>Pilih sumber dana</option>
            <option v-for="s in allSources" :key="s.id" :value="String(s.id)">{{ s.name }} — sisa {{ formatRupiah(availableFor(s.id)) }}</option>
          </select>
          <p v-if="form.source_id" class="field-hint" :class="{ 'error-text': remainingAfter < 0 }">
            Sisa setelah transaksi ini: <strong>{{ formatRupiah(remainingAfter) }}</strong>
          </p>
        </div>

        <div class="field">
          <label for="f-ccy">Mata uang</label>
          <div class="input-affix">
            <span class="affix symbol">{{ currencySymbol(form.currency_code) }}</span>
            <select id="f-ccy" v-model="form.currency_code" @change="onCurrencyChange">
              <option v-for="c in CURRENCIES" :key="c" :value="c">{{ currencySymbol(c) }} · {{ c }} — {{ currencyName(c) }}</option>
            </select>
          </div>
        </div>

        <div class="amount-rate-row">
          <div class="field" :class="{ 'needs-input': needsAmount }">
            <label for="f-amount">Jumlah Uang</label>
            <div class="input-affix">
              <span class="affix symbol">{{ currencySymbol(form.currency_code) }}</span>
              <input id="f-amount" v-model.number="form.amount" type="number" min="0" step="any" inputmode="decimal" placeholder="0" required />
            </div>
            <p class="field-hint">Nominal dalam {{ form.currency_code }}</p>
          </div>

          <div class="field">
            <label for="f-rate">
              Kurs ke IDR
              <span v-if="form.currency_code !== 'IDR'" class="rate-chip" :class="rateAuto ? 'auto' : 'manual'">{{ rateAuto ? "Otomatis" : "Manual" }}</span>
            </label>
            <div class="input-affix" :class="{ disabled: form.currency_code === 'IDR' }">
              <span class="affix symbol">Rp</span>
              <input id="f-rate" v-model.number="form.exchange_rate" type="number" min="0" step="any" inputmode="decimal" :disabled="form.currency_code === 'IDR'" required @input="rateAuto = false" />
              <button v-if="form.currency_code !== 'IDR'" class="affix-btn" type="button" title="Ambil kurs terbaru" aria-label="Ambil kurs terbaru" :disabled="rateLoading" @click="fetchRate">
                <svg :class="{ spin: rateLoading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-3-6.7" /><path d="M21 4v5h-5" /></svg>
              </button>
            </div>
            <p v-if="rateError" class="error-text">{{ rateError }}</p>
            <p v-else-if="form.currency_code === 'IDR'" class="field-hint">Rupiah, tanpa konversi</p>
            <p v-else class="field-hint">1 {{ form.currency_code }} = {{ formatRupiah(form.exchange_rate) }}</p>
          </div>
        </div>

        <p v-if="form.currency_code !== 'IDR' && rateInfo && !rateError" class="field-hint rate-source">{{ rateInfo }}</p>
        <div v-if="form.currency_code !== 'IDR'" class="rate-total">
          <span>Total dalam Rupiah</span>
          <strong>{{ formatRupiah(previewTotal) }}</strong>
        </div>

        <div class="field">
          <label for="f-date">Tanggal</label>
          <input id="f-date" v-model="form.transaction_date" type="date" :min="minDate" required />
        </div>

        <div class="field">
          <label for="f-note">Catatan</label>
          <textarea id="f-note" v-model="form.note" rows="2" maxlength="255" placeholder="Opsional"></textarea>
        </div>

        <p v-if="formError" class="error-text">{{ formError }}</p>
      </form>
      <template #footer>
        <button class="btn-ghost" type="button" @click="formOpen = false">Batal</button>
        <button class="btn-primary" type="submit" form="tx-form" :disabled="saving">{{ saving ? "Menyimpan..." : "Simpan" }}</button>
      </template>
    </BaseModal>

    <!-- Konfirmasi hapus -->
    <BaseModal v-model="deleteOpen" title="Hapus transaksi?" size="sm">
      <p v-if="toDelete" class="confirm-text">
        {{ toDelete.category_name }} · {{ formatRupiah(toDelete.amount_idr) }} ({{ formatDate(toDelete.transaction_date) }}) akan dihapus permanen.
      </p>
      <template #footer>
        <button class="btn-ghost" type="button" @click="deleteOpen = false">Batal</button>
        <button class="btn-danger" type="button" :disabled="saving" @click="confirmDelete">Hapus</button>
      </template>
    </BaseModal>

    <ScanBillModal v-model="scanOpen" @done="handleScanDone" />

    <BaseModal v-model="viewerOpen" title="Foto bon" size="lg">
      <p v-if="viewerLoading" class="empty-text">Memuat foto…</p>
      <img v-else-if="viewerUrl" :src="viewerUrl" class="viewer-img" alt="Foto bon" />
      <p v-else class="error-text">Foto bon tidak dapat dimuat.</p>
    </BaseModal>

    <div v-if="toast.msg" class="toast" :class="toast.type">{{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../services/api";
import BaseModal from "../components/BaseModal.vue";
import ScanBillModal from "../components/ScanBillModal.vue";
import { scanBill } from "../services/billScanner";
import { compressImage } from "../utils/image";
import { CURRENCIES, currencySymbol, currencyName, formatNumber, formatRupiah, formatDate, todayISO, retentionMinISO } from "../utils/format";

const rows = ref([]);
const categories = ref([]);
const loading = ref(true);

/* ---------- Sumber dana (kategori pemasukan yang membiayai pengeluaran) ---------- */
const sources = ref({ sources: [], unassigned_expense: 0 });
const allSources = computed(() => sources.value.sources);
const sourceList = computed(() => allSources.value.filter((s) => s.income > 0 || s.expense > 0));
const originalTx = ref(null); // transaksi yang sedang diedit (untuk mengembalikan saldonya)

function bestSource() {
  const best = allSources.value.reduce((b, s) => (!b || s.balance > b.balance ? s : b), null);
  return best && best.balance > 0 ? String(best.id) : "";
}
function availableFor(id) {
  const s = allSources.value.find((x) => x.id === Number(id));
  let bal = s ? s.balance : 0;
  const o = originalTx.value;
  if (editingId.value && o && o.type === "expense" && o.source_id === Number(id)) bal += o.amount_idr;
  return bal;
}

/* ---------- Tab, search, filter ---------- */
const tab = ref("expense");
const searchInput = ref("");
const search = ref("");
const showFilters = ref(false);
const page = ref(1);
const perPage = ref(10);
const sort = reactive({ key: "transaction_date", dir: "desc" });

const blankFilters = () => ({ category_id: "", source_id: "", currency: "", date_from: "", date_to: "", amount_min: null, amount_max: null, rate_min: null, rate_max: null });
const filters = reactive(blankFilters());

// Debounce pencarian 250 ms
let searchTimer;
watch(searchInput, (v) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => (search.value = v.trim().toLowerCase()), 250);
});

// Setiap filter/pencarian/tab berubah -> kembali ke halaman 1
watch([search, tab, perPage, () => ({ ...filters })], () => (page.value = 1), { deep: true });
// Ganti tab -> kategori yang dipilih belum tentu ada di tab baru
watch(tab, () => {
  filters.category_id = "";
  filters.source_id = "";
});

function resetFilters() {
  Object.assign(filters, blankFilters());
  searchInput.value = "";
  search.value = "";
}

const activeFilterCount = computed(() => Object.values(filters).filter((v) => v !== "" && v !== null && v !== undefined).length);

const counts = computed(() => ({
  expense: rows.value.filter((r) => r.type === "expense").length,
  income: rows.value.filter((r) => r.type === "income").length,
}));
const tabRows = computed(() => rows.value.filter((r) => r.type === tab.value));
const tabCategories = computed(() => categories.value.filter((c) => c.type === tab.value));
const usedCurrencies = computed(() => [...new Set(tabRows.value.map((r) => r.currency_code))].sort());

const filtered = computed(() => {
  const f = filters;
  const q = search.value;
  const list = tabRows.value.filter((r) => {
    if (q && !`${r.category_name} ${r.note || ""}`.toLowerCase().includes(q)) return false;
    if (f.category_id && String(r.category_id) !== f.category_id) return false;
    if (f.currency && r.currency_code !== f.currency) return false;
    if (f.source_id === "none" ? r.source_id : f.source_id && String(r.source_id) !== f.source_id) return false;
    if (f.date_from && r.transaction_date < f.date_from) return false;
    if (f.date_to && r.transaction_date > f.date_to) return false;
    if (isNum(f.amount_min) && r.amount_idr < f.amount_min) return false;
    if (isNum(f.amount_max) && r.amount_idr > f.amount_max) return false;
    if (isNum(f.rate_min) && r.exchange_rate < f.rate_min) return false;
    if (isNum(f.rate_max) && r.exchange_rate > f.rate_max) return false;
    return true;
  });
  const dir = sort.dir === "asc" ? 1 : -1;
  return list.sort((a, b) => {
    const x = a[sort.key], y = b[sort.key];
    return (x < y ? -1 : x > y ? 1 : b.id - a.id) * dir;
  });
});
const isNum = (v) => typeof v === "number" && !Number.isNaN(v);

const filteredTotal = computed(() => filtered.value.reduce((s, r) => s + r.amount_idr, 0));
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage.value)));
const paged = computed(() => filtered.value.slice((page.value - 1) * perPage.value, page.value * perPage.value));

function toggleSort(key) {
  if (sort.key === key) sort.dir = sort.dir === "asc" ? "desc" : "asc";
  else Object.assign(sort, { key, dir: "desc" });
}
const sortIcon = (key) => (sort.key === key ? (sort.dir === "asc" ? "▲" : "▼") : "");

/* ---------- Form tambah / edit ---------- */
const CURRENCY_DEFAULT = "IDR";
const formOpen = ref(false);
const editingId = ref(null);
const saving = ref(false);
const formError = ref("");
const rateLoading = ref(false);
const rateError = ref("");
const minDate = retentionMinISO();

const blankForm = (type) => ({
  type,
  category_id: "",
  source_id: "",
  amount: null,
  currency_code: CURRENCY_DEFAULT,
  exchange_rate: 1,
  transaction_date: todayISO(),
  note: "",
});
const form = reactive(blankForm("expense"));

const formCategories = computed(() => categories.value.filter((c) => c.type === form.type));
const previewTotal = computed(() => (Number(form.amount) || 0) * (Number(form.exchange_rate) || 0));
const remainingAfter = computed(() => availableFor(form.source_id) - previewTotal.value);

/* Tambah kategori baru langsung dari form */
const newCatOpen = ref(false);
const newCatName = ref("");
async function addCategory() {
  const name = newCatName.value.trim();
  if (!name) return;
  try {
    const { data } = await api.post("/categories", { name, type: form.type });
    categories.value.push(data);
    form.category_id = String(data.id);
    newCatName.value = "";
    newCatOpen.value = false;
    if (data.type === "income") sources.value.sources.push({ id: data.id, name: data.name, income: 0, expense: 0, balance: 0, used_percent: 0 });
  } catch (err) {
    formError.value = err.response?.data?.error || "Gagal menambah kategori";
  }
}

function setType(t) {
  if (form.type === t) return;
  form.type = t;
  form.category_id = "";
  form.source_id = t === "expense" ? bestSource() : "";
  newCatOpen.value = false;
}

/* ---------- Foto bon & scan ---------- */
const route = useRoute();
const router = useRouter();
const scanOpen = ref(false);
const scanning = ref(false);
const scanProgress = ref(0);
const scanMsg = reactive({ type: "ok", text: "" });
const missing = reactive({ amount: false, category: false }); // field yang perlu diisi manual setelah scan
const needsAmount = computed(() => missing.amount && !(form.amount > 0));
const needsCategory = computed(() => missing.category && !form.category_id);
const setScanMsg = (text = "", type = "ok") => Object.assign(scanMsg, { text, type });
const receiptCam = ref(null);
const receiptGal = ref(null);
const receiptFile = ref(null); // File baru yang akan diunggah
const receiptPreview = ref(null); // object URL untuk file baru
const existingUrl = ref(null); // object URL foto bon yang sudah tersimpan (saat edit)
const receiptRemoved = ref(false);
const receiptSrc = computed(() => receiptPreview.value || (receiptRemoved.value ? null : existingUrl.value));

function revoke(url) {
  if (url) URL.revokeObjectURL(url);
}
function resetReceipt() {
  revoke(receiptPreview.value);
  revoke(existingUrl.value);
  receiptFile.value = receiptPreview.value = existingUrl.value = null;
  receiptRemoved.value = false;
  setScanMsg();
  missing.amount = missing.category = false;
  scanning.value = false;
}
function setReceiptFile(file) {
  revoke(receiptPreview.value);
  receiptFile.value = file;
  receiptPreview.value = URL.createObjectURL(file);
  receiptRemoved.value = false;
}
function clearReceipt() {
  revoke(receiptPreview.value);
  receiptFile.value = receiptPreview.value = null;
  receiptRemoved.value = true;
  setScanMsg();
}
async function onReceiptPick(e) {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  try {
    setReceiptFile(await compressImage(file));
    setScanMsg();
  } catch (err) {
    formError.value = err.message;
  }
}

// Foto bon bersifat privat, jadi diambil lewat API ber-token lalu dijadikan object URL
async function fetchReceiptUrl(id) {
  const { data } = await api.get(`/transactions/${id}/receipt`, { responseType: "blob" });
  return URL.createObjectURL(data);
}

/** Isi form dari hasil scan, lalu tampilkan pesan sesuai apa yang terbaca. */
async function applyScan(res) {
  if (form.type !== "expense") setType("expense"); // bon = pengeluaran

  const hasAmount = Number(res.amount) > 0;
  if (hasAmount) form.amount = res.amount;
  form.currency_code = CURRENCIES.includes(res.currency) ? res.currency : "IDR";
  form.exchange_rate = 1;

  const hasDate = !!res.date && res.date >= minDate && res.date <= todayISO();
  if (hasDate) form.transaction_date = res.date;
  if (res.note) form.note = res.note.slice(0, 255); // hasil baca lainnya masuk ke Catatan

  const cat = categories.value.find(
    (c) => c.type === "expense" && (c.id === res.category_id || c.name.toLowerCase() === (res.category_name || "").toLowerCase())
  );
  if (cat) form.category_id = String(cat.id);

  missing.amount = !hasAmount;
  missing.category = !cat;
  if (form.currency_code !== "IDR") await fetchRate();

  const engine = res.engine === "claude" ? "AI" : "OCR browser";
  if (res.is_receipt === false) {
    setScanMsg("Gambar tidak terdeteksi sebagai bon, tetapi tetap dilampirkan. Silakan isi manual detail transaksi.", "warn");
  } else if (!hasAmount && !cat) {
    setScanMsg("Bon sudah dilampirkan, tetapi detail tidak terbaca. Silakan isi manual detail transaksi (jumlah uang dan kategori).", "warn");
  } else if (!hasAmount || !cat) {
    const gone = [!hasAmount && "jumlah uang (kata “Total” tidak ditemukan)", !cat && "kategori"].filter(Boolean).join(" dan ");
    setScanMsg(`Bon dilampirkan dan sebagian data terisi dari bon (${engine}), tetapi ${gone} tidak terbaca. Silakan lengkapi manual.`, "warn");
  } else {
    setScanMsg(
      `Jumlah uang, kategori, dan catatan terisi dari bon (${engine}).` +
        (hasDate ? "" : " Tanggal tidak terbaca, dipakai hari ini.") +
        " Periksa kembali sebelum menyimpan.",
      "ok"
    );
  }
}

async function rescan() {
  if (!receiptFile.value) return;
  scanning.value = true;
  scanProgress.value = 0;
  formError.value = "";
  try {
    await applyScan(await scanBill(receiptFile.value, (p) => (scanProgress.value = p)));
  } catch (err) {
    formError.value = err.message || "Gagal membaca bon";
  } finally {
    scanning.value = false;
  }
}

/** Hasil dari pop up Scan Bon (tombol di header): buka form tambah dengan data terisi. */
async function handleScanDone(res) {
  openAdd();
  if (res.file) setReceiptFile(res.file);
  if (!res.manual) await applyScan(res);
}

// Tombol "Scan Bon" di header menambah query ?scan=<waktu>
watch(
  () => route.query.scan,
  (v) => {
    if (!v) return;
    scanOpen.value = true;
    router.replace({ name: "transactions", query: {} });
  },
  { immediate: true }
);

/* ---------- Lihat foto bon dari tabel ---------- */
const viewerOpen = ref(false);
const viewerLoading = ref(false);
const viewerUrl = ref(null);
async function viewReceipt(t) {
  viewerOpen.value = true;
  viewerLoading.value = true;
  revoke(viewerUrl.value);
  viewerUrl.value = null;
  try {
    viewerUrl.value = await fetchReceiptUrl(t.id);
  } catch {
    viewerUrl.value = null;
  } finally {
    viewerLoading.value = false;
  }
}
watch(viewerOpen, (o) => {
  if (!o) {
    revoke(viewerUrl.value);
    viewerUrl.value = null;
  }
});
watch(formOpen, (o) => {
  if (!o) resetReceipt();
});
onBeforeUnmount(() => {
  resetReceipt();
  revoke(viewerUrl.value);
});

function openAdd() {
  resetReceipt();
  editingId.value = null;
  Object.assign(form, blankForm(tab.value));
  form.source_id = form.type === "expense" ? bestSource() : "";
  originalTx.value = null;
  newCatOpen.value = false;
  formError.value = rateError.value = "";
  formOpen.value = true;
}

async function openEdit(t) {
  resetReceipt();
  editingId.value = t.id;
  originalTx.value = t;
  newCatOpen.value = false;
  Object.assign(form, {
    type: t.type,
    category_id: String(t.category_id),
    source_id: t.source_id ? String(t.source_id) : "",
    amount: t.amount,
    currency_code: t.currency_code,
    exchange_rate: t.exchange_rate,
    transaction_date: t.transaction_date,
    note: t.note || "",
  });
  formError.value = rateError.value = "";
  rateInfo.value = "";
  formOpen.value = true;
  if (t.has_receipt) {
    try {
      existingUrl.value = await fetchReceiptUrl(t.id);
    } catch {
      /* foto tidak dapat dimuat; form tetap bisa dipakai */
    }
  }
}

function onCurrencyChange() {
  rateError.value = "";
  rateInfo.value = "";
  rateAuto.value = false;
  if (form.currency_code === "IDR") form.exchange_rate = 1;
  else fetchRate();
}

// Ganti tanggal -> kurs otomatis ikut menyesuaikan (kecuali sudah diketik manual)
watch(
  () => form.transaction_date,
  () => {
    if (formOpen.value && rateAuto.value && form.currency_code !== "IDR") fetchRate();
  }
);

const rateInfo = ref("");
const rateAuto = ref(false); // true = kurs berasal dari pengambilan otomatis (bukan diketik manual)

async function fetchRate() {
  rateLoading.value = true;
  rateError.value = "";
  try {
    const { data } = await api.get("/transactions/rate", {
      params: { from: form.currency_code, date: form.transaction_date },
    });
    form.exchange_rate = Number(data.rate);
    rateAuto.value = true;
    rateInfo.value = `Kurs otomatis (Frankfurter) per ${data.date ? formatDate(data.date) : "terbaru"}. Boleh diubah manual.`;
  } catch (err) {
    rateError.value = err.response?.data?.error || "Gagal mengambil kurs, isi manual.";
  } finally {
    rateLoading.value = false;
  }
}

async function save() {
  formError.value = "";
  if (!(form.amount > 0)) return (formError.value = "Jumlah uang harus lebih dari 0");
  if (!(form.exchange_rate > 0)) return (formError.value = "Kurs harus lebih dari 0");
  if (form.type === "expense") {
    if (!form.source_id) return (formError.value = "Pilih sumber dana untuk pengeluaran ini");
    if (remainingAfter.value < 0) return (formError.value = "Saldo sumber dana tidak cukup untuk pengeluaran ini");
  }

  saving.value = true;
  const payload = {
    type: form.type,
    category_id: Number(form.category_id),
    source_id: form.type === "expense" ? Number(form.source_id) : null,
    amount: form.amount,
    currency_code: form.currency_code,
    exchange_rate: form.currency_code === "IDR" ? 1 : form.exchange_rate,
    transaction_date: form.transaction_date,
    note: form.note,
  };
  try {
    const { data: saved } = editingId.value
      ? await api.put(`/transactions/${editingId.value}`, payload)
      : await api.post("/transactions", payload);

    let receiptFailed = false;
    try {
      if (receiptFile.value) {
        const fd = new FormData();
        fd.append("receipt", receiptFile.value);
        await api.post(`/transactions/${saved.id}/receipt`, fd);
      } else if (receiptRemoved.value && originalTx.value?.has_receipt) {
        await api.delete(`/transactions/${saved.id}/receipt`);
      }
    } catch {
      receiptFailed = true;
    }
    formOpen.value = false;
    // Setelah tambah, pindah ke tab sesuai tipe agar langsung terlihat
    if (payload.type !== tab.value) tab.value = payload.type;
    await load();
    if (receiptFailed) showToast("Transaksi tersimpan, tetapi foto bon gagal diunggah. Coba edit dan lampirkan lagi.", "error");
    else showToast(editingId.value ? "Transaksi diperbarui" : "Transaksi ditambahkan");
  } catch (err) {
    formError.value = err.response?.data?.error || "Gagal menyimpan transaksi";
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
    await api.delete(`/transactions/${toDelete.value.id}`);
    deleteOpen.value = false;
    await load();
    if (page.value > totalPages.value) page.value = totalPages.value;
    showToast("Transaksi dihapus");
  } catch (err) {
    showToast(err.response?.data?.error || "Gagal menghapus", "error");
  } finally {
    saving.value = false;
  }
}

/* ---------- Ekspor CSV (sesuai hasil filter) ---------- */
function exportCsv() {
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const header = ["Tanggal", "Tipe", "Kategori", "Sumber dana", "Jumlah Uang", "Mata uang", "Kurs ke IDR", "Total IDR", "Catatan"];
  const lines = filtered.value.map((r) =>
    [r.transaction_date, r.type, r.category_name, r.source_name, r.amount, r.currency_code, r.exchange_rate, r.amount_idr, r.note].map(esc).join(",")
  );
  const blob = new Blob(["\ufeff" + [header.map(esc).join(","), ...lines].join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `transaksi-${tab.value}-${todayISO()}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
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
  const [tx, src] = await Promise.all([api.get("/transactions"), api.get("/dashboard/sources")]);
  rows.value = tx.data;
  sources.value = src.data;
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
.header-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; }
.tabs-row { margin-bottom: 1rem; }

.sources-strip { display: flex; gap: 0.7rem; overflow-x: auto; padding-bottom: 0.3rem; margin-bottom: 0.9rem; }
.source-chip {
  flex: 0 0 auto; min-width: 170px; display: flex; flex-direction: column; gap: 0.1rem;
  background: var(--paper); border: 1px solid var(--line); border-left: 4px solid var(--green-500);
  border-radius: var(--radius-md); padding: 0.6rem 0.9rem;
}
.source-chip.low { border-left-color: var(--red-600); }
.source-name { font-size: 0.75rem; font-weight: 600; color: var(--ink-faint); }
.source-chip strong { font-family: var(--font-display); color: var(--navy-700); }
.source-chip small { font-size: 0.72rem; color: var(--ink-faint); }
.ccy { font-size: 0.72rem; font-weight: 700; color: var(--navy-500); letter-spacing: 0.03em; }

.receipt-box {
  display: flex; gap: 0.9rem; align-items: center; border: 1.5px dashed var(--line);
  border-radius: var(--radius-md); padding: 0.8rem; margin-bottom: 0.9rem; background: var(--cream-50);
}
.receipt-box.filled { border-style: solid; background: var(--paper); }
.receipt-thumb { width: 76px; height: 76px; object-fit: cover; border-radius: var(--radius-sm); border: 1px solid var(--line); flex-shrink: 0; }
.receipt-side { display: flex; flex-direction: column; gap: 0.35rem; min-width: 0; flex: 1; }
.receipt-side strong small { font-weight: 500; color: var(--ink-faint); }
.receipt-side .field-hint { margin: 0; }
.receipt-actions { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.scan-msg { margin: -0.3rem 0 0.9rem; font-size: 0.82rem; background: var(--green-100); color: var(--green-600); padding: 0.55rem 0.8rem; border-radius: var(--radius-sm); }
.scan-msg.warn { background: var(--amber-100); color: var(--amber-600); font-weight: 600; }
.viewer-img { display: block; max-width: 100%; max-height: 70vh; margin: 0 auto; border-radius: var(--radius-sm); }

.amount-rate-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; align-items: start; }
.amount-rate-row .field { min-width: 0; margin-bottom: 0.5rem; }
.input-affix { display: flex; align-items: stretch; border: 1.5px solid var(--line); border-radius: var(--radius-sm); background: var(--paper); overflow: hidden; height: 44px; }
.input-affix:focus-within { border-color: var(--navy-500); }
.input-affix.disabled { background: var(--cream-100); }
.input-affix .affix { display: flex; align-items: center; justify-content: center; min-width: 46px; padding: 0 0.7rem; background: var(--cream-100); color: var(--navy-700); font-weight: 700; font-size: 0.95rem; border-right: 1.5px solid var(--line); white-space: nowrap; }
.input-affix input, .input-affix select { border: none; border-radius: 0; min-width: 0; flex: 1; width: 100%; height: 100%; box-shadow: none; background: transparent; }
.input-affix input:focus, .input-affix select:focus { outline: none; box-shadow: none; }
.affix-btn { display: flex; align-items: center; justify-content: center; width: 42px; border: none; border-left: 1.5px solid var(--line); background: var(--cream-50); color: var(--navy-500); padding: 0; border-radius: 0; }
.affix-btn:hover { background: var(--cream-100); color: var(--navy-700); }
.affix-btn svg { width: 18px; height: 18px; }
.affix-btn svg.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.rate-chip { margin-left: 0.4rem; padding: 0.1rem 0.5rem; border-radius: 999px; font-size: 0.68rem; font-weight: 700; vertical-align: middle; }
.rate-chip.auto { background: var(--green-100); color: var(--green-600); }
.rate-chip.manual { background: var(--amber-100); color: var(--amber-600); }
.rate-source { margin: 0 0 0.6rem; }
.rate-total { display: flex; justify-content: space-between; align-items: baseline; background: var(--cream-50); border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0.65rem 0.9rem; margin-bottom: 0.9rem; font-size: 0.85rem; color: var(--ink-soft); }
.rate-total strong { font-family: var(--font-display); font-size: 1.15rem; color: var(--navy-700); }
.needs-input .input-affix, .needs-input select { border-color: var(--amber-500); background: #fffaf0; }

.newcat { margin-top: -0.4rem; }
.link-btn { background: none; border: none; padding: 0; color: var(--navy-500); font-size: 0.83rem; text-decoration: underline; }
.newcat-row { display: flex; gap: 0.4rem; }
.newcat-row input { flex: 1; min-width: 0; }

.toolbar { padding: 1rem; margin-bottom: 0.9rem; }
.search-row { display: flex; gap: 0.6rem; }
.search-row input { flex: 1; }
.badge {
  background: var(--amber-500); color: var(--navy-900); border-radius: 999px;
  min-width: 18px; height: 18px; font-size: 0.7rem; display: inline-flex; align-items: center; justify-content: center; padding: 0 5px;
}
.filters { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-top: 1rem; }
.filters .field { margin-bottom: 0; }
.filters-foot { grid-column: 1 / -1; display: flex; justify-content: flex-end; }

.result-bar { display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--ink-soft); margin: 0 0.25rem 0.6rem; }
.result-bar strong.expense { color: var(--red-600); }
.result-bar strong.income { color: var(--green-600); }

.table-card { padding: 0; overflow: hidden; }
.table-card > .empty-text { padding: 1.5rem; margin: 0; }
.tx-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.tx-table th {
  text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--ink-faint); padding: 0.85rem 1rem; background: var(--cream-50); border-bottom: 1px solid var(--line); white-space: nowrap;
}
.tx-table th.sortable { cursor: pointer; user-select: none; }
.tx-table th.sortable:hover { color: var(--navy-700); }
.tx-table td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--cream-100); vertical-align: middle; }
.tx-table tr:last-child td { border-bottom: none; }
.num { text-align: right !important; white-space: nowrap; }
.strong { font-weight: 700; }
.strong.expense { color: var(--red-600); }
.strong.income { color: var(--green-600); }
.note { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ink-soft); }
.actions-col { width: 1%; text-align: right; }
.row-actions { display: flex; gap: 0.4rem; justify-content: flex-end; }

.pager { display: flex; align-items: center; justify-content: space-between; padding: 0.8rem 1rem; border-top: 1px solid var(--line); gap: 1rem; }
.per-page { display: flex; align-items: center; gap: 0.5rem; margin: 0; font-weight: 500; color: var(--ink-soft); }
.per-page select { width: auto; padding: 0.3rem 0.5rem; }
.pager-nav { display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; color: var(--ink-soft); }

.type-toggle { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; background: var(--cream-100); border-radius: var(--radius-sm); padding: 4px; margin-bottom: 1rem; }
.type-toggle button { border: none; background: transparent; padding: 0.55rem; color: var(--ink-soft); }
.type-toggle button.active { background: var(--navy-700); color: var(--cream-50); }
.rate-row { display: flex; gap: 0.5rem; }
.confirm-text { margin: 0; }

@media (max-width: 900px) {
  .filters { grid-template-columns: repeat(2, 1fr); }
}

/* HP: tabel berubah jadi kartu per transaksi */
@media (max-width: 720px) {
  .header-actions { width: 100%; }
  .header-actions button { flex: 1; }
  .tabs { width: 100%; }
  .tabs button { flex: 1; padding: 0.5rem 0.4rem; font-size: 0.8rem; }
  .table-card { background: transparent; border: none; }
  .tx-table, .tx-table tbody { display: block; }
  .tx-table thead { display: none; }
  .tx-table tr {
    display: block; background: var(--paper); border: 1px solid var(--line);
    border-radius: var(--radius-md); padding: 0.4rem 0.9rem; margin-bottom: 0.75rem;
  }
  .tx-table td {
    display: flex; justify-content: space-between; align-items: center; gap: 1rem;
    padding: 0.45rem 0; border-bottom: 1px dashed var(--cream-100); text-align: right;
  }
  .tx-table td::before { content: attr(data-label); color: var(--ink-faint); font-size: 0.75rem; font-weight: 600; text-align: left; flex-shrink: 0; }
  .tx-table td.actions-col { border-bottom: none; width: auto; justify-content: flex-end; padding-top: 0.6rem; }
  .tx-table td.actions-col::before { content: none; }
  .note { max-width: 60%; white-space: normal; }
  .pager { background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-md); }
}
@media (max-width: 480px) {
  .amount-rate-row { grid-template-columns: 1fr; gap: 0; }
  .receipt-box { flex-wrap: wrap; }
  .filters { grid-template-columns: 1fr; }
}
</style>
