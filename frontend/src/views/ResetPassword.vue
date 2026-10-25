<template>
  <AuthLayout>
    <h1>Buat password baru</h1>

    <div v-if="!token" class="status-box">
      <div class="status-icon bad">!</div>
      <p class="error-text">Tautan reset tidak lengkap. Minta tautan baru.</p>
      <router-link to="/forgot-password" class="btn-primary auth-submit" style="text-decoration:none;display:inline-block">Minta tautan baru</router-link>
    </div>

    <div v-else-if="done" class="status-box">
      <div class="status-icon ok">✓</div>
      <p class="success-text">{{ message }}</p>
      <router-link to="/login" class="btn-primary auth-submit" style="text-decoration:none;display:inline-block">Ke halaman login</router-link>
    </div>

    <form v-else @submit.prevent="submit">
      <p class="auth-subtitle">Pilih password baru untuk akunmu (minimal 8 karakter).</p>
      <div class="field">
        <label for="pw">Password baru</label>
        <input id="pw" v-model="password" type="password" minlength="8" maxlength="72" autocomplete="new-password" required />
      </div>
      <div class="field">
        <label for="pw2">Ulangi password baru</label>
        <input id="pw2" v-model="confirm" type="password" minlength="8" maxlength="72" autocomplete="new-password" required />
      </div>
      <button type="submit" class="btn-primary auth-submit" :disabled="loading">{{ loading ? "Menyimpan..." : "Simpan password baru" }}</button>
      <p v-if="error" class="error-text">{{ error }}</p>
      <p v-if="expired" class="auth-switch"><router-link to="/forgot-password">Minta tautan reset baru</router-link></p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import api from "../services/api";
import AuthLayout from "../components/AuthLayout.vue";

const route = useRoute();
const token = ref(String(route.query.token || ""));
const password = ref("");
const confirm = ref("");
const loading = ref(false);
const done = ref(false);
const message = ref("");
const error = ref("");
const expired = ref(false);

async function submit() {
  error.value = "";
  expired.value = false;
  if (password.value !== confirm.value) return (error.value = "Konfirmasi password tidak sama.");
  loading.value = true;
  try {
    const { data } = await api.post("/auth/reset-password", { token: token.value, password: password.value });
    message.value = data.message;
    done.value = true;
  } catch (err) {
    error.value = err.response?.data?.error || "Gagal mengubah password, coba lagi.";
    expired.value = err.response?.status === 400 && /tautan/i.test(error.value);
  } finally {
    loading.value = false;
  }
}
</script>
