<template>
  <div class="chart-box"><canvas ref="canvas"></canvas></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { Chart, BarController, BarElement, LineController, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend } from "chart.js";
import { formatCompact, formatRupiah } from "../utils/format";

Chart.register(BarController, BarElement, LineController, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

const props = defineProps({
  labels: { type: Array, default: () => [] },
  income: { type: Array, default: () => [] },
  expense: { type: Array, default: () => [] },
});

const canvas = ref(null);
let chart = null;

function build() {
  chart?.destroy();
  chart = new Chart(canvas.value, {
    type: "bar",
    data: {
      labels: props.labels,
      datasets: [
        { label: "Pemasukan", data: props.income, backgroundColor: "#10b981", borderRadius: 5, maxBarThickness: 26 },
        { label: "Pengeluaran", data: props.expense, backgroundColor: "#f59e0b", borderRadius: 5, maxBarThickness: 26 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { family: "Plus Jakarta Sans" } } },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${formatRupiah(c.parsed.y)}` } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 10, font: { size: 11 } } },
        y: { beginAtZero: true, ticks: { callback: (v) => formatCompact(v), font: { size: 11 } }, grid: { color: "#efe9da" } },
      },
    },
  });
}

onMounted(build);
watch(() => [props.labels, props.income, props.expense], build, { deep: true });
onBeforeUnmount(() => chart?.destroy());
</script>

<style scoped>
.chart-box { position: relative; height: 300px; width: 100%; }
@media (max-width: 720px) { .chart-box { height: 240px; } }
</style>
