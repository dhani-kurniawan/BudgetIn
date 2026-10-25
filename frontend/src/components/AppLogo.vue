<template>
  <div class="app-logo" :class="size">
    <svg
      class="logo-icon"
      viewBox="0 0 120 120"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Logo Budgetin"
    >
      <rect x="0" y="0" width="120" height="120" rx="28" fill="#FCD34D" />
      <rect x="25" y="40" width="70" height="48" rx="8" fill="#1E3A5F" />
      <path
        d="M25 48 Q25 40 33 40 L87 40 Q95 40 95 48 L95 54 L25 54 Z"
        fill="#2D4A6B"
      />
      <rect x="73" y="59" width="18" height="13" rx="3" fill="#13293F" />
      <circle cx="83" cy="33" r="15" fill="#F59E0B" stroke="#B45309" stroke-width="1.5" />
      <text
        x="83"
        y="38"
        text-anchor="middle"
        font-size="13"
        font-weight="700"
        fill="#7C3B0A"
        font-family="Arial, sans-serif"
      >Rp</text>
      <path d="M83 19 Q78 10 85 6 Q88 13 83 19 Z" fill="#10B981" />
      <path d="M83 19 Q90 11 96 14 Q93 21 83 19 Z" fill="#34D399" />
    </svg>

    <span v-if="!iconOnly" class="logo-text">
      Budget<span class="accent">in</span>
    </span>
  </div>
</template>

<script setup>
defineProps({
  // Kalau true, cuma tampilkan ikon (tanpa tulisan "Budgetin")
  iconOnly: { type: Boolean, default: false },
  // Ukuran: "sm" (header/navbar), "md" (default), "lg" (halaman login/hero)
  size: { type: String, default: "md" },
});
</script>

<style scoped>
.app-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
}

.logo-icon {
  flex-shrink: 0;
  display: block;
}

.logo-text {
  font-weight: 700;
  color: #1e3a5f;
  letter-spacing: -0.01em;
}

.accent {
  color: #f59e0b;
}

/* Ukuran sm: dipakai di header/navbar */
.app-logo.sm .logo-icon {
  width: 28px;
  height: 28px;
}
.app-logo.sm .logo-text {
  font-size: 1.1rem;
}

/* Ukuran md: default, serbaguna */
.app-logo.md .logo-icon {
  width: 40px;
  height: 40px;
}
.app-logo.md .logo-text {
  font-size: 1.4rem;
}

/* Ukuran lg: halaman login / hero */
.app-logo.lg {
  flex-direction: column;
  gap: 0.75rem;
}
.app-logo.lg .logo-icon {
  width: 72px;
  height: 72px;
}
.app-logo.lg .logo-text {
  font-size: 2rem;
}
</style>
