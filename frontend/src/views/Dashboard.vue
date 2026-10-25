<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p>Ringkasan kondisi keuanganmu, {{ monthLabel }}<template v-if="activeSourceName"> · sumber dana {{ activeSourceName }}</template>.</p>
      </div>
      <div class="source-filter">
        <label for="src-filter">Sumber dana</label>
        <select id="src-filter" v-model="sourceId">
          <option value="">Semua sumber</option>
          <option v-for="s in sourceData.sources" :key="s.id" :value="String(s.id)">{{ s.name }}</option>
        </select>
      </div>
    </div>

    <!-- Metric cards -->
    <div class="metric-grid">
      <div class="metric-card">
        <span class="metric-label">Pemasukan bulan ini</span>
        <span class="metric-value positive">{{ formatRupiah(cur.total_income) }}</span>
        <span class="delta" :class="deltaClass(incomeDelta, true)">{{ deltaText(incomeDelta) }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Pengeluaran bulan ini</span>
        <span class="metric-value negative">{{ formatRupiah(cur.total_expense) }}</span>
        <span class="delta" :class="deltaClass(expenseDelta, false)">{{ deltaText(expenseDelta) }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Selisih bulan ini</span>
        <span class="metric-value" :class="cur.balance >= 0 ? 'positive' : 'negative'">{{ formatRupiah(cur.balance) }}</span>
        <span class="delta neutral">Pemasukan − pengeluaran</span>
      </div>
      <div class="metric-card highlight">
        <span class="metric-label">{{ sourceId ? "Saldo sumber dana" : "Total saldo" }}</span>
        <span class="metric-value">{{ formatRupiah(all.balance) }}</span>
        <span class="delta neutral">Seluruh data tercatat</span>
      </div>
    </div>

    <!-- Sumber dana -->
    <div v-if="visibleSources.length" class="card">
      <div class="card-head">
        <h2>Sumber dana</h2>
        <span class="chart-hint no-mb">Klik salah satu untuk memfilter dashboard</span>
      </div>
      <div class="source-list">
        <button
          v-for="s in visibleSources" :key="s.id" type="button" class="source-row"
          :class="{ active: String(s.id) === sourceId }"
          @click="sourceId = String(s.id) === sourceId ? '' : String(s.id)"
        >
          <div class="source-top">
            <strong>{{ s.name }}</strong>
            <span class="source-balance" :class="{ neg: s.balance < 0 }">Sisa {{ formatRupiah(s.balance) }}</span>
          </div>
          <div class="bar-track"><div class="bar-fill" :style="{ width: Math.min(s.used_percent, 100) + '%', background: usedColor(s.used_percent) }"></div></div>
          <div class="source-sub">
            <span>Masuk {{ formatRupiah(s.income) }}</span>
            <span>Terpakai {{ formatRupiah(s.expense) }} ({{ Math.round(s.used_percent) }}%)</span>
          </div>
        </button>
      </div>
      <p v-if="sourceData.unassigned_expense > 0" class="unassigned">
        Pengeluaran lama senilai {{ formatRupiah(sourceData.unassigned_expense) }} belum dikelompokkan.
        Atur sumber dananya lewat tombol edit di halaman <router-link to="/transactions">Transaksi</router-link>.
      </p>
    </div>

    <!-- Grafik tren -->
    <div class="card trend-card">
      <div class="card-head">
        <h2>Pemasukan vs pengeluaran</h2>
        <div class="tabs">
          <button v-for="p in periods" :key="p.value" :class="{ active: period === p.value }" @click="period = p.value">
            {{ p.label }}
          </button>
        </div>
      </div>
      <p class="chart-hint">{{ periodHint }}</p>
      <TrendChart v-if="trend" :labels="trend.labels" :income="trend.income" :expense="trend.expense" />
      <div v-else class="empty-text">Memuat grafik...</div>
    </div>

    <div class="two-col">
      <!-- Kategori -->
      <div class="card">
        <h2>Pengeluaran per kategori</h2>
        <p class="chart-hint">Bulan ini</p>
        <template v-if="cur.expense_by_category.length">
          <DoughnutChart :labels="catLabels" :values="catValues" :colors="catColors" />
          <ul class="legend">
            <li v-for="(item, i) in topCategories" :key="item.category">
              <span class="dot" :style="{ background: catColors[i % catColors.length] }"></span>
              <span class="legend-name">{{ item.category }}</span>
              <span class="legend-pct">{{ pct(item.total) }}%</span>
              <span class="legend-amt">{{ formatRupiah(item.total) }}</span>
            </li>
          </ul>
        </template>
        <p v-else class="empty-text">Belum ada pengeluaran bulan ini.</p>
      </div>

      <!-- Rasio tabungan + rata-rata -->
      <div class="card">
        <h2>Kesehatan keuangan</h2>
        <p class="chart-hint">Bulan ini</p>
        <div class="health">
          <ProgressRing :percent="Math.max(savingsRate, 0)" :size="120" :stroke="12" :color="savingsRate >= 20 ? 'var(--green-500)' : savingsRate > 0 ? 'var(--amber-500)' : 'var(--red-600)'">
            <div class="ring-text"><strong>{{ savingsRate }}%</strong><small>ditabung</small></div>
          </ProgressRing>
          <p class="health-text">{{ savingsMessage }}</p>
        </div>
        <div class="mini-stats">
          <div><span>Rata-rata pengeluaran / hari</span><strong>{{ formatRupiah(avgDaily) }}</strong></div>
          <div><span>Jumlah transaksi bulan ini</span><strong>{{ monthTxCount }}</strong></div>
        </div>
      </div>
    </div>

    <!-- Target -->
    <div class="card">
      <div class="card-head">
        <h2>Progres target</h2>
        <router-link to="/targets" class="link-more">Kelola target →</router-link>
      </div>

      <div v-if="targets.length" class="target-summary">
        <span class="chip green">{{ countBy(["aman", "tercapai"]) }} aman / tercapai</span>
        <span class="chip amber">{{ countBy(["mendekati_batas"]) }} mendekati batas</span>
        <span class="chip red">{{ countBy(["terlampaui"]) }} terlampaui</span>
      </div>

      <div v-if="activeTargets.length" class="target-grid">
        <router-link v-for="t in activeTargets" :key="t.id" to="/targets" class="target-mini">
          <ProgressRing :percent="t.progress_percent" :size="76" :stroke="8" :color="statusColor(t.status)" />
          <div class="target-mini-text">
            <strong>{{ t.name }}</strong>
            <span>{{ t.type === "expense_limit" ? "Batas pengeluaran" : "Tabungan" }}<template v-if="t.category_name"> · {{ t.category_name }}</template></span>
            <span class="target-amt">{{ formatRupiah(t.current_value) }} / {{ formatRupiah(t.target_amount) }}</span>
            <span class="target-days">{{ t.days_left }} hari lagi</span>
          </div>
        </router-link>
      </div>
      <p v-else class="empty-text">Belum ada target aktif. <router-link to="/targets">Buat target pertamamu</router-link>.</p>
    </div>

    <!-- Transaksi terbaru -->
    <div class="card">
      <div class="card-head">
        <h2>Transaksi terbaru</h2>
        <router-link to="/transactions" class="link-more">Lihat semua →</router-link>
      </div>
      <ul v-if="recent.length" class="recent">
        <li v-for="t in recent" :key="t.id">
          <span class="recent-icon" :class="t.type">{{ t.type === "income" ? "↓" : "↑" }}</span>
          <div class="recent-main">
            <strong>{{ t.category_name }}</strong>
            <span>{{ t.note || "Tanpa catatan" }} · {{ formatDate(t.transaction_date) }}</span>
          </div>
          <span class="recent-amt" :class="t.type">
            {{ t.type === "income" ? "+" : "−" }}{{ formatRupiah(t.amount_idr) }}
          </span>
        </li>
      </ul>
      <p v-else class="empty-text">Belum ada transaksi.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import api from "../services/api";
import TrendChart from "../components/TrendChart.vue";
import DoughnutChart from "../components/DoughnutChart.vue";
import ProgressRing from "../components/ProgressRing.vue";
import { formatRupiah, formatDate, monthRange } from "../utils/format";

const emptySummary = () => ({ total_income: 0, total_expense: 0, balance: 0, expense_by_category: [] });

const cur = ref(emptySummary());
const prev = ref(emptySummary());
const all = ref(emptySummary());
const trend = ref(null);
const targets = ref([]);
const recent = ref([]);
const monthTxCount = ref(0);

/* ---------- Sumber dana ---------- */
const sourceId = ref("");
const sourceData = ref({ sources: [], unassigned_expense: 0 });
const activeSourceName = computed(() => sourceData.value.sources.find((s) => String(s.id) === sourceId.value)?.name || "");
const visibleSources = computed(() => sourceData.value.sources.filter((s) => s.income > 0 || s.expense > 0));
const srcParams = () => (sourceId.value ? { source_id: sourceId.value } : {});
const usedColor = (p) => (p >= 100 ? "var(--red-600)" : p >= 80 ? "var(--amber-500)" : "var(--green-500)");

const periods = [
  { value: "day", label: "Harian" },
  { value: "week", label: "Mingguan" },
  { value: "month", label: "Bulanan" },
  { value: "year", label: "Tahunan" },
];
const period = ref("month");
const periodHint = computed(
  () => ({ day: "30 hari terakhir", week: "12 minggu terakhir (per Senin)", month: "12 bulan terakhir", year: "3 tahun terakhir" }[period.value])
);

const monthLabel = new Date().toLocaleDateString("id-ID", { month: "long", year: "numeric" });

/* ---------- Delta vs bulan lalu ---------- */
function delta(now, before) {
  if (!before) return now ? null : 0;
  return ((now - before) / before) * 100;
}
const incomeDelta = computed(() => delta(cur.value.total_income, prev.value.total_income));
const expenseDelta = computed(() => delta(cur.value.total_expense, prev.value.total_expense));
function deltaText(d) {
  if (d === null) return "Belum ada data bulan lalu";
  if (d === 0) return "Sama seperti bulan lalu";
  return `${d > 0 ? "▲" : "▼"} ${Math.abs(d).toFixed(0)}% vs bulan lalu`;
}
function deltaClass(d, higherIsGood) {
  if (d === null || d === 0) return "neutral";
  return (d > 0) === higherIsGood ? "good" : "bad";
}

/* ---------- Kategori ---------- */
const catColors = ["#1e3a5f", "#f59e0b", "#10b981", "#6366f1", "#ef4444", "#14b8a6", "#a855f7", "#94a3b8"];
const topCategories = computed(() => cur.value.expense_by_category.slice(0, 6));
const catLabels = computed(() => topCategories.value.map((c) => c.category));
const catValues = computed(() => topCategories.value.map((c) => c.total));
function pct(v) {
  return cur.value.total_expense ? Math.round((v / cur.value.total_expense) * 100) : 0;
}

/* ---------- Kesehatan keuangan ---------- */
const savingsRate = computed(() => {
  const { total_income: inc, balance } = cur.value;
  return inc ? Math.round((balance / inc) * 100) : 0;
});
const savingsMessage = computed(() => {
  if (!cur.value.total_income) return "Catat pemasukan bulan ini untuk melihat rasio tabunganmu.";
  if (savingsRate.value >= 20) return "Mantap! Kamu menyisihkan lebih dari 20% pemasukan.";
  if (savingsRate.value > 0) return "Sudah surplus, tapi coba naikkan rasio tabungan hingga 20%.";
  return "Pengeluaran melebihi pemasukan bulan ini. Cek kategori terbesar.";
});
const avgDaily = computed(() => cur.value.total_expense / Math.max(new Date().getDate(), 1));

/* ---------- Target ---------- */
const activeTargets = computed(() => targets.value.filter((t) => t.is_active).slice(0, 4));
function countBy(statuses) {
  return targets.value.filter((t) => t.is_active && statuses.includes(t.status)).length;
}
function statusColor(s) {
  return { aman: "var(--green-500)", tercapai: "var(--green-500)", mendekati_batas: "var(--amber-500)", terlampaui: "var(--red-600)", belum_tercapai: "var(--navy-500)" }[s];
}

/* ---------- Loader ---------- */
async function loadTrend() {
  trend.value = null;
  const { data } = await api.get("/dashboard/trend", { params: { period: period.value, ...srcParams() } });
  trend.value = data;
}
watch(period, loadTrend);

async function loadAll() {
  const m = monthRange(0);
  const pm = monthRange(-1);
  const sp = srcParams();
  const [c, p, a, t, tg, r, src] = await Promise.all([
    api.get("/dashboard/summary", { params: { ...m, ...sp } }),
    api.get("/dashboard/summary", { params: { ...pm, ...sp } }),
    api.get("/dashboard/summary", { params: sp }),
    api.get("/dashboard/trend", { params: { period: period.value, ...sp } }),
    api.get("/targets"),
    api.get("/transactions", { params: { start: m.start, end: m.end, ...sp } }),
    api.get("/dashboard/sources"),
  ]);
  cur.value = c.data;
  prev.value = p.data;
  all.value = a.data;
  trend.value = t.data;
  targets.value = tg.data;
  sourceData.value = src.data;
  monthTxCount.value = r.data.length;
  recent.value = r.data.length >= 5 ? r.data.slice(0, 5) : (await api.get("/transactions", { params: { limit: 5, ...sp } })).data;
}

watch(sourceId, loadAll);
onMounted(loadAll);
</script>

<style scoped>
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.25rem; }
.metric-card {
  background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-md);
  padding: 1.1rem 1.25rem; display: flex; flex-direction: column; gap: 0.3rem; min-width: 0;
}
.metric-card.highlight { background: var(--navy-700); border-color: var(--navy-700); }
.metric-card.highlight .metric-label, .metric-card.highlight .delta { color: #c7d4e0; }
.metric-card.highlight .metric-value { color: var(--cream-50); }
.metric-label { font-size: 0.8rem; color: var(--ink-faint); font-weight: 600; }
.metric-value { font-family: var(--font-display); font-size: 1.3rem; font-weight: 600; color: var(--navy-700); overflow-wrap: anywhere; }
.metric-value.positive { color: var(--green-600); }
.metric-value.negative { color: var(--red-600); }
.delta { font-size: 0.76rem; font-weight: 600; }
.delta.good { color: var(--green-600); }
.delta.bad { color: var(--red-600); }
.delta.neutral { color: var(--ink-faint); }

.source-filter { display: flex; flex-direction: column; gap: 0.25rem; min-width: 180px; }
.source-filter label { margin: 0; font-size: 0.78rem; color: var(--ink-faint); }
.chart-hint.no-mb { margin: 0; }
.source-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.9rem; margin-top: 0.6rem; }
.source-row {
  text-align: left; background: var(--paper); border: 1.5px solid var(--line); border-radius: var(--radius-md);
  padding: 0.9rem; display: flex; flex-direction: column; gap: 0.5rem; color: inherit;
}
.source-row:hover { border-color: var(--navy-500); }
.source-row.active { border-color: var(--navy-700); background: var(--cream-50); }
.source-top { display: flex; justify-content: space-between; gap: 0.5rem; align-items: baseline; }
.source-top strong { color: var(--navy-700); }
.source-balance { font-weight: 700; color: var(--green-600); font-size: 0.9rem; }
.source-balance.neg { color: var(--red-600); }
.source-sub { display: flex; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap; font-size: 0.75rem; color: var(--ink-faint); }
.bar-track { height: 8px; background: var(--cream-100); border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
.unassigned { margin: 1rem 0 0; font-size: 0.85rem; background: var(--amber-100); color: var(--amber-600); padding: 0.6rem 0.8rem; border-radius: var(--radius-sm); }

.card { margin-bottom: 1.25rem; }
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
.card-head h2 { margin: 0; }
.chart-hint { margin: 0 0 0.9rem; font-size: 0.82rem; color: var(--ink-faint); }
.link-more { font-size: 0.85rem; font-weight: 600; text-decoration: none; color: var(--navy-500); }
.link-more:hover { text-decoration: underline; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.two-col .card { margin-bottom: 0; }
.two-col + .card { margin-top: 1.25rem; }

.legend { list-style: none; margin: 1rem 0 0; padding: 0; display: flex; flex-direction: column; gap: 0.5rem; }
.legend li { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.legend-pct { color: var(--ink-faint); width: 2.5rem; text-align: right; }
.legend-amt { font-weight: 600; color: var(--navy-700); min-width: 6.5rem; text-align: right; }

.health { display: flex; align-items: center; gap: 1.25rem; margin-bottom: 1.25rem; }
.health-text { margin: 0; font-size: 0.9rem; }
.ring-text { display: flex; flex-direction: column; line-height: 1.1; }
.ring-text strong { font-size: 1.5rem; }
.ring-text small { font-size: 0.72rem; color: var(--ink-faint); font-family: var(--font-body); }
.mini-stats { display: grid; gap: 0.6rem; }
.mini-stats div { display: flex; justify-content: space-between; gap: 1rem; background: var(--cream-100); padding: 0.65rem 0.85rem; border-radius: var(--radius-sm); font-size: 0.85rem; }
.mini-stats span { color: var(--ink-soft); }
.mini-stats strong { color: var(--navy-700); white-space: nowrap; }

.target-summary { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0 1rem; }
.target-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.9rem; }
.target-mini {
  display: flex; gap: 0.9rem; align-items: center; text-decoration: none; color: inherit;
  border: 1px solid var(--line); border-radius: var(--radius-md); padding: 0.9rem;
}
.target-mini:hover { border-color: var(--navy-500); }
.target-mini-text { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; font-size: 0.8rem; color: var(--ink-faint); }
.target-mini-text strong { color: var(--navy-700); font-size: 0.95rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.target-amt { color: var(--ink-soft); font-weight: 600; }

.recent { list-style: none; margin: 0.5rem 0 0; padding: 0; }
.recent li { display: flex; align-items: center; gap: 0.8rem; padding: 0.7rem 0; border-bottom: 1px solid var(--cream-100); }
.recent li:last-child { border-bottom: none; }
.recent-icon { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.recent-icon.income { background: var(--green-100); color: var(--green-600); }
.recent-icon.expense { background: var(--amber-100); color: var(--amber-600); }
.recent-main { flex: 1; min-width: 0; display: flex; flex-direction: column; font-size: 0.8rem; color: var(--ink-faint); }
.recent-main strong { color: var(--ink); font-size: 0.9rem; }
.recent-main span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent-amt { font-weight: 700; font-size: 0.9rem; white-space: nowrap; }
.recent-amt.income { color: var(--green-600); }
.recent-amt.expense { color: var(--red-600); }

@media (max-width: 960px) {
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
  .source-filter { width: 100%; }
  .two-col { grid-template-columns: 1fr; }
  .target-grid { grid-template-columns: 1fr; }
  .health { flex-direction: column; text-align: center; }
  .card-head .tabs { width: 100%; }
  .card-head .tabs button { flex: 1; padding: 0.45rem 0.5rem; }
}
@media (max-width: 420px) {
  .metric-grid { grid-template-columns: 1fr; }
  .legend-amt { min-width: 0; }
}
</style>
