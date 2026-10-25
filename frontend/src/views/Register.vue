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
        <h1>Buat akun</h1>
        <p class="auth-subtitle">Mulai catat keuanganmu dalam 1 menit.</p>

        <form @submit.prevent="handleRegister">
          <div class="field">
            <label for="name">Nama</label>
            <input id="name" v-model="name" type="text" placeholder="Nama kamu" required />
          </div>

          <div class="field">
            <label for="email">Email</label>
            <input id="email" v-model="email" type="email" placeholder="kamu@email.com" required />
          </div>

          <div class="field">
            <label for="password">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              minlength="8"
              maxlength="72"
              placeholder="Minimal 8 karakter"
              required
            />
          </div>

          <button type="submit" class="btn-primary auth-submit" :disabled="loading || registered">
            {{ loading ? "Memproses..." : "Daftar" }}
          </button>

          <p v-if="error" class="error-text">{{ error }}</p>
          <p v-if="success" class="success-text">{{ success }}</p>
          <router-link v-if="registered" to="/login" class="btn-ghost auth-submit" style="text-decoration:none;display:block;text-align:center">Ke halaman login</router-link>
        </form>

        <p class="auth-switch">
          Sudah punya akun?
          <router-link to="/login">Masuk di sini</router-link>
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

const name = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const success = ref("");
const registered = ref(false);
const loading = ref(false);
const router = useRouter();

async function handleRegister() {
  error.value = "";
  success.value = "";
  loading.value = true;
  try {
    const { data } = await api.post("/auth/register", {
      name: name.value,
      email: email.value,
      password: password.value,
    });
    success.value = data.message || "Akun berhasil dibuat. Cek email untuk verifikasi.";
    registered.value = true;
  } catch (err) {
    error.value = err.response?.data?.error || "Registrasi gagal, coba lagi.";
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

.success-text {
  color: var(--green-600);
  font-size: 0.85rem;
  margin: 0.5rem 0 0;
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
