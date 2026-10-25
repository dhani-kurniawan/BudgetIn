<template>
  <AuthLayout>
    <h1>Lupa password?</h1>
    <p class="auth-subtitle">Masukkan email akunmu. Kami kirim tautan untuk membuat password baru.</p>

    <form v-if="!sent" @submit.prevent="submit">
      <div class="field">
        <label for="email">Email</label>
        <input id="email" v-model="email" type="email" placeholder="kamu@email.com" required autofocus />
      </div>
      <button type="submit" class="btn-primary auth-submit" :disabled="loading">{{ loading ? "Mengirim..." : "Kirim tautan reset" }}</button>
      <p v-if="error" class="error-text">{{ error }}</p>
    </form>

    <div v-else class="status-box">
      <div class="status-icon ok">✉</div>
      <p class="success-text">{{ message }}</p>
      <p class="hint">Tautan berlaku 30 menit dan hanya bisa dipakai sekali.</p>
    </div>

    <p class="auth-switch"><router-link to="/login">← Kembali ke halaman login</router-link></p>
  </AuthLayout>
</template>

<script setup>
import { ref } from "vue";
import api from "../services/api";
import AuthLayout from "../components/AuthLayout.vue";

const email = ref("");
const loading = ref(false);
const sent = ref(false);
const message = ref("");
const error = ref("");

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    const { data } = await api.post("/auth/forgot-password", { email: email.value });
    message.value = data.message;
    sent.value = true;
  } catch (err) {
    error.value = err.response?.data?.error || "Gagal mengirim permintaan, coba lagi.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.hint { font-size: 0.82rem; color: var(--ink-faint); }
</style>
