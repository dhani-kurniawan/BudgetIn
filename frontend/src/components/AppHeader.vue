<template>
  <header class="navbar">
    <div class="navbar-inner">
      <router-link to="/" class="logo-link" aria-label="Ke Dashboard">
        <AppLogo size="sm" />
      </router-link>

      <nav class="navbar-links" :class="{ open: menuOpen }">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/transactions">Transaksi</router-link>
        <router-link to="/targets">Target</router-link>
      </nav>

      <div class="navbar-right">
        <button class="scan-btn" type="button" title="Tambah transaksi dari foto bon" @click="goScan">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h3l2-3h6l2 3h3a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V9a1 1 0 011-1z" /><circle cx="12" cy="13" r="3.5" /></svg>
          <span>Scan Bon</span>
        </button>
        <div class="profile-wrap" ref="profileWrap">
          <button class="avatar-btn" type="button" aria-label="Menu profil" @click="profileOpen = !profileOpen">
            <UserAvatar :user="user" :size="38" />
          </button>

          <div v-if="profileOpen" class="dropdown">
            <div class="dropdown-user">
              <UserAvatar :user="user" :size="46" />
              <div class="dropdown-user-text">
                <strong>{{ user?.name }}</strong>
                <span>{{ user?.email }}</span>
              </div>
            </div>
            <div class="dropdown-meta">
              <span>Last Access</span>
              <strong>{{ formatDateTime(user?.last_login) }}</strong>
            </div>
            <button class="dropdown-item" type="button" @click="openProfile">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z" /></svg>
              Edit Profil
            </button>
            <button class="dropdown-item danger" type="button" @click="logout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><path d="M16 17l5-5-5-5M21 12H9" /></svg>
              Logout
            </button>
          </div>
        </div>

        <button class="burger" type="button" aria-label="Menu" @click="menuOpen = !menuOpen">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path v-if="!menuOpen" d="M4 7h16M4 12h16M4 17h16" />
            <path v-else d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="user && user.email_verified === false" class="verify-banner">
      <span>Email <strong>{{ user.email }}</strong> belum diverifikasi.</span>
      <button v-if="!verifySent" type="button" :disabled="verifySending" @click="resendVerification">
        {{ verifySending ? "Mengirim..." : "Kirim ulang tautan" }}
      </button>
      <span v-else class="sent">Tautan dikirim, cek emailmu.</span>
    </div>

    <ProfileModal v-model="profileModal" />
  </header>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppLogo from "./AppLogo.vue";
import UserAvatar from "./UserAvatar.vue";
import ProfileModal from "./ProfileModal.vue";
import api from "../services/api";
import { auth } from "../stores/auth";
import { formatDateTime } from "../utils/format";

const router = useRouter();
const route = useRoute();
const user = auth.user;

const menuOpen = ref(false);
const profileOpen = ref(false);
const profileModal = ref(false);
const profileWrap = ref(null);

const verifySent = ref(false);
const verifySending = ref(false);
async function resendVerification() {
  verifySending.value = true;
  try {
    await api.post("/auth/resend-verification", { email: user.value.email });
    verifySent.value = true;
  } finally {
    verifySending.value = false;
  }
}

function goScan() {
  menuOpen.value = false;
  // Transactions.vue membuka pop up scan saat query "scan" berubah
  router.push({ name: "transactions", query: { scan: String(Date.now()) } });
}

function openProfile() {
  profileOpen.value = false;
  profileModal.value = true;
}

function logout() {
  profileOpen.value = false;
  auth.logout();
  router.push("/login");
}

function onDocClick(e) {
  if (profileWrap.value && !profileWrap.value.contains(e.target)) profileOpen.value = false;
}

watch(() => route.fullPath, () => {
  menuOpen.value = false;
  profileOpen.value = false;
});

onMounted(async () => {
  document.addEventListener("click", onDocClick);
  try {
    await auth.fetchMe(); // sinkron data user terbaru (foto, last access)
  } catch {
    /* interceptor menangani token invalid */
  }
});
onBeforeUnmount(() => document.removeEventListener("click", onDocClick));
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--paper);
  border-bottom: 1px solid var(--line);
}
.navbar-inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.7rem 1.5rem;
}
.logo-link { text-decoration: none; display: inline-flex; }

.navbar-links { display: flex; align-items: center; gap: 1.5rem; margin-left: 1rem; flex: 1; }
.navbar-links a {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink-soft);
  text-decoration: none;
  padding-bottom: 2px;
  border-bottom: 2px solid transparent;
}
.navbar-links a:hover { color: var(--navy-700); }
.navbar-links a.router-link-exact-active { color: var(--navy-700); border-bottom-color: var(--amber-500); }

.navbar-right { display: flex; align-items: center; gap: 0.5rem; margin-left: auto; }
.avatar-btn { background: none; border: none; padding: 0; border-radius: 50%; display: inline-flex; }
.avatar-btn:hover { opacity: 0.85; }

.profile-wrap { position: relative; }
.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  width: 270px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 32px rgba(19, 41, 63, 0.15);
  padding: 0.6rem;
}
.dropdown-user { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; }
.dropdown-user-text { display: flex; flex-direction: column; min-width: 0; }
.dropdown-user-text strong { color: var(--navy-700); font-size: 0.95rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dropdown-user-text span { color: var(--ink-faint); font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dropdown-meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  background: var(--cream-100);
  border-radius: var(--radius-sm);
  padding: 0.55rem 0.75rem;
  margin: 0.3rem 0 0.4rem;
  font-size: 0.78rem;
  color: var(--ink-faint);
}
.dropdown-meta strong { color: var(--navy-700); font-size: 0.85rem; }
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  background: none;
  border: none;
  text-align: left;
  padding: 0.6rem 0.75rem;
  font-size: 0.9rem;
  color: var(--ink);
  border-radius: var(--radius-sm);
}
.dropdown-item svg { width: 17px; height: 17px; }
.dropdown-item:hover { background: var(--cream-100); }
.dropdown-item.danger { color: var(--red-600); }

.verify-banner {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 0.6rem;
  background: var(--amber-100); color: var(--amber-600); font-size: 0.82rem; padding: 0.45rem 1rem; text-align: center;
}
.verify-banner button { background: none; border: none; padding: 0; color: var(--navy-700); font-weight: 700; text-decoration: underline; font-size: 0.82rem; }
.verify-banner .sent { font-weight: 700; }

.scan-btn {
  display: inline-flex; align-items: center; gap: 0.45rem;
  background: var(--amber-500); color: var(--navy-900); border: none; border-radius: 999px;
  padding: 0.5rem 0.95rem; font-size: 0.85rem; font-weight: 700; white-space: nowrap;
}
.scan-btn:hover { filter: brightness(0.95); }
.scan-btn svg { width: 18px; height: 18px; }

.burger {
  display: none;
  background: none;
  border: 1.5px solid var(--line);
  width: 38px;
  height: 38px;
  padding: 0;
  color: var(--navy-700);
}
.burger svg { width: 20px; height: 20px; margin: auto; display: block; }

@media (max-width: 720px) {
  .scan-btn { padding: 0.5rem 0.65rem; }
  .scan-btn span { display: none; }
  .navbar-inner { padding: 0.6rem 1rem; gap: 0.75rem; flex-wrap: wrap; }
  .burger { display: inline-flex; align-items: center; justify-content: center; }
  .navbar-links {
    display: none;
    order: 3;
    flex-basis: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    margin: 0;
    padding-top: 0.4rem;
    border-top: 1px solid var(--line);
  }
  .navbar-links.open { display: flex; }
  .navbar-links a { padding: 0.75rem 0.25rem; border-bottom: 1px solid var(--cream-100); }
  .navbar-links a.router-link-exact-active { border-bottom-color: var(--amber-500); }
  .dropdown { position: fixed; right: 0.75rem; left: 0.75rem; top: 62px; width: auto; }
}
</style>
