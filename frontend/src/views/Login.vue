<template>
  <div class="auth-screen">
    <div class="auth-panel">
      <AppLogo size="lg" />
      <p class="auth-panel-tagline">
        Catat duit, pantau target, tahu ke mana uangmu pergi bulan ini.
      </p>
    </div>

    <div class="auth-form-side">
      <div class="auth-form-box">
        <h1>Selamat datang kembali</h1>
        <p class="auth-subtitle">Masuk untuk lanjut pantau keuanganmu.</p>

        <form @submit.prevent="handleLogin">
          <div class="field">
            <label for="email">Email</label>
            <input id="email" v-model="email" type="email" placeholder="kamu@email.com" required />
          </div>

          <div class="field">
            <label for="password">Password</label>
            <input id="password" v-model="password" type="password" placeholder="Password kamu" required />
            <router-link to="/forgot-password" class="forgot-link">Lupa password?</router-link>
          </div>

          <button type="submit" class="btn-primary auth-submit" :disabled="loading">
            {{ loading ? "Memproses..." : "Masuk" }}
          </button>

          <p v-if="error" class="error-text">{{ error }}</p>
          <div v-if="unverified" class="resend-box">
            <button type="button" class="btn-ghost btn-sm" :disabled="resending" @click="resend">
              {{ resending ? "Mengirim..." : "Kirim ulang email verifikasi" }}
            </button>
            <p v-if="resendMsg" class="success-text">{{ resendMsg }}</p>
          </div>
        </form>

        <p class="auth-switch">
          Belum punya akun?
          <router-link to="/register">Daftar di sini</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import AppLogo from "../components/AppLogo.vue";
import { auth } from "../stores/auth";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const unverified = ref(false);
const resending = ref(false);
const resendMsg = ref("");
const router = useRouter();

async function resend() {
  resending.value = true;
  try {
    const { data } = await api.post("/auth/resend-verification", { email: email.value });
    resendMsg.value = data.message;
  } catch (err) {
    resendMsg.value = err.response?.data?.error || "Gagal mengirim ulang.";
  } finally {
    resending.value = false;
  }
}

async function handleLogin() {
  error.value = "";
  unverified.value = false;
  resendMsg.value = "";
  loading.value = true;
  try {
    const response = await api.post("/auth/login", {
      email: email.value,
      password: password.value,
    });
    auth.login(response.data.access_token, response.data.user);
    router.push("/");
  } catch (err) {
    error.value = err.response?.data?.error || "Login gagal";
    unverified.value = err.response?.data?.code === "EMAIL_NOT_VERIFIED";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-screen {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr;
}

.auth-panel {
  background: var(--navy-700);
  color: var(--cream-50);
  padding: 2.5rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.auth-panel :deep(.logo-text) {
  color: var(--cream-50);
}

.auth-panel-tagline {
  color: #c7d4e0;
  max-width: 320px;
  font-size: 0.95rem;
}

.auth-form-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1.5rem;
}

.auth-form-box {
  width: 100%;
  max-width: 360px;
}

.auth-subtitle {
  margin-top: -0.3rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.field {
  margin-bottom: 1rem;
}

.auth-submit {
  width: 100%;
  margin-top: 0.5rem;
}

.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.forgot-link {
  display: inline-block;
  margin-top: 0.4rem;
  font-size: 0.82rem;
  font-weight: 600;
}

.resend-box {
  margin-top: 0.8rem;
  text-align: center;
}

.auth-switch {
  text-align: center;
  font-size: 0.88rem;
  margin-top: 1.5rem;
}

.auth-switch a {
  font-weight: 600;
}

@media (min-width: 840px) {
  .auth-screen {
    grid-template-columns: 0.9fr 1.1fr;
  }
  .auth-panel {
    padding: 3rem;
    justify-content: center;
  }
}
</style>
