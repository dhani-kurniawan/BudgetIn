import axios from "axios";

export const API_ORIGIN = import.meta.env.VITE_API_ORIGIN || "http://localhost:5000";

const api = axios.create({
  baseURL: `${API_ORIGIN}/api`,
});

// Sisipkan token JWT ke setiap request kalau ada
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Token kedaluwarsa / tidak valid -> keluar otomatis
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const isAuthCall = err.config?.url?.startsWith("/auth/login");
    if ((status === 401 || status === 422) && !isAuthCall && localStorage.getItem("access_token")) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

/** URL absolut foto profil (photo_url dari backend berupa path relatif). */
export function photoSrc(user) {
  if (!user?.photo_url) return null;
  return `${API_ORIGIN}/api${user.photo_url}?v=${encodeURIComponent(user.profile_photo || "")}`;
}

export default api;
