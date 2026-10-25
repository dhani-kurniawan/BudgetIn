<template>
  <AuthLayout>
    <h1>Verifikasi email</h1>

    <div v-if="state === 'loading'" class="status-box"><p>Memverifikasi emailmu…</p></div>

    <div v-else-if="state === 'ok'" class="status-box">
      <div class="status-icon ok">✓</div>
      <p class="success-text">{{ message }}</p>
      <router-link :to="loggedIn ? '/' : '/login'" class="btn-primary auth-submit" style="text-decoration:none;display:inline-block">
        {{ loggedIn ? "Ke dashboard" : "Ke halaman login" }}
      </router-link>
    </div>

    <div v-else>
      <div class="status-box">
        <div class="status-icon bad">!</div>
        <p class="error-text">{{ message }}</p>
      </div>
      <form v-if="!resent" @submit.prevent="resend">
        <div class="field">
          <label for="email">Kirim ulang ke email</label>
          <input id="email" v-model="email" type="email" placeholder="kamu@email.com" required />
        </div>
        <button type="submit" class="btn-primary auth-submit" :disabled="loading">{{ loading ? "Mengirim..." : "Kirim tautan verifikasi baru" }}</button>
      </form>
      <p v-else class="success-text">{{ resentMessage }}</p>
    </div>

    <p class="auth-switch"><router-link to="/login">← Kembali ke halaman login</router-link></p>
  </AuthLayout>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "../services/api";
import AuthLayout from "../components/AuthLayout.vue";
import { auth } from "../stores/auth";

const route = useRoute();
const state = ref("loading"); // loading | ok | bad
const message = ref("");
const email = ref("");
const loading = ref(false);
const resent = ref(false);
const resentMessage = ref("");
const loggedIn = auth.isAuthenticated;

onMounted(async () => {
  const token = String(route.query.token || "");
  if (!token) {
    state.value = "bad";
    message.value = "Tautan verifikasi tidak lengkap.";
    return;
  }
  try {
    const { data } = await api.post("/auth/verify-email", { token });
    message.value = data.message;
    state.value = "ok";
    if (auth.isAuthenticated.value) await auth.fetchMe().catch(() => {});
  } catch (err) {
    message.value = err.response?.data?.error || "Verifikasi gagal.";
    state.value = "bad";
  }
});

async function resend() {
  loading.value = true;
  try {
    const { data } = await api.post("/auth/resend-verification", { email: email.value });
    resentMessage.value = data.message;
    resent.value = true;
  } catch (err) {
    message.value = err.response?.data?.error || "Gagal mengirim ulang.";
  } finally {
    loading.value = false;
  }
}
</script>
