<template>
  <div class="chart-box"><canvas ref="canvas"></canvas></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { Chart, DoughnutController, ArcElement, Tooltip } from "chart.js";
import { formatRupiah } from "../utils/format";

Chart.register(DoughnutController, ArcElement, Tooltip);

const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  colors: { type: Array, default: () => [] },
});

const canvas = ref(null);
let chart = null;

function build() {
  chart?.destroy();
  chart = new Chart(canvas.value, {
    type: "doughnut",
    data: { labels: props.labels, datasets: [{ data: props.values, backgroundColor: props.colors, borderWidth: 2, borderColor: "#fff" }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "66%",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.label}: ${formatRupiah(c.parsed)}` } },
      },
    },
  });
}

onMounted(build);
watch(() => [props.labels, props.values], build, { deep: true });
onBeforeUnmount(() => chart?.destroy());
</script>

<style scoped>
.chart-box { position: relative; height: 190px; width: 190px; margin: 0 auto; }
</style>
