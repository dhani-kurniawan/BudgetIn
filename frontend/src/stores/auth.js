import { reactive, computed } from "vue";
import api from "../services/api";

// State reaktif sederhana (tanpa Pinia) agar header ikut update saat login/logout/edit profil
const state = reactive({
  token: localStorage.getItem("access_token") || null,
  user: JSON.parse(localStorage.getItem("user") || "null"),
});

function setUser(user) {
  state.user = user;
  localStorage.setItem("user", JSON.stringify(user));
}

export const auth = {
  state,
  isAuthenticated: computed(() => !!state.token),
  user: computed(() => state.user),

  login(token, user) {
    state.token = token;
    localStorage.setItem("access_token", token);
    setUser(user);
  },

  logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  },

  setUser,

  async fetchMe() {
    if (!state.token) return;
    const { data } = await api.get("/auth/me");
    setUser(data);
  },
};
