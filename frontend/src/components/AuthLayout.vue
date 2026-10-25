<template>
  <div class="auth-screen">
    <div class="auth-panel">
      <AppLogo size="lg" />
      <p class="auth-panel-tagline">Catat duit, pantau target, tahu ke mana uangmu pergi bulan ini.</p>
    </div>
    <div class="auth-form-side">
      <div class="auth-form-box"><slot /></div>
    </div>
  </div>
</template>

<script setup>
import AppLogo from "./AppLogo.vue";
</script>

<style scoped>
.auth-screen { min-height: 100vh; display: grid; grid-template-columns: 1fr; }
.auth-panel { background: var(--navy-700); color: var(--cream-50); padding: 2.5rem 2rem; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 1rem; }
.auth-panel :deep(.logo-text) { color: var(--cream-50); }
.auth-panel-tagline { color: #c7d4e0; max-width: 320px; font-size: 0.95rem; }
.auth-form-side { display: flex; align-items: center; justify-content: center; padding: 2.5rem 1.5rem; }
.auth-form-box { width: 100%; max-width: 360px; }
.auth-form-box :deep(.auth-subtitle) { margin-top: -0.3rem; margin-bottom: 1.5rem; font-size: 0.9rem; }
.auth-form-box :deep(.auth-submit) { width: 100%; margin-top: 0.5rem; }
.auth-form-box :deep(.auth-switch) { text-align: center; font-size: 0.88rem; margin-top: 1.5rem; }
.auth-form-box :deep(.auth-switch a) { font-weight: 600; }
.auth-form-box :deep(.status-box) { text-align: center; padding: 1rem 0; }
.auth-form-box :deep(.status-icon) { width: 56px; height: 56px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-bottom: 0.8rem; }
.auth-form-box :deep(.status-icon.ok) { background: var(--green-100); color: var(--green-600); }
.auth-form-box :deep(.status-icon.bad) { background: var(--red-100); color: var(--red-600); }
@media (min-width: 840px) {
  .auth-screen { grid-template-columns: 0.9fr 1.1fr; }
  .auth-panel { padding: 3rem; justify-content: center; }
}
</style>
