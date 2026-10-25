<template>
  <BaseModal v-model="open" title="Edit Profil">
    <form id="profile-form" @submit.prevent="save">
      <div class="photo-row">
        <UserAvatar :user="user" :size="84" :preview-url="removePhoto ? null : preview" />
        <div class="photo-actions">
          <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp" hidden @change="onFile" />
          <button class="btn-ghost btn-sm" type="button" @click="fileInput.click()">Ganti foto</button>
          <button
            v-if="preview || (user?.photo_url && !removePhoto)"
            class="btn-ghost btn-sm"
            type="button"
            @click="clearPhoto"
          >Hapus foto</button>
          <p class="field-hint">JPG, PNG, atau WEBP. Maks. 3 MB.</p>
        </div>
      </div>

      <div class="field">
        <label for="p-name">Nama lengkap</label>
        <input id="p-name" v-model="form.name" required />
      </div>
      <div class="field-row">
        <div class="field">
          <label for="p-username">Username</label>
          <input id="p-username" v-model="form.username" minlength="3" maxlength="30" required />
        </div>
        <div class="field">
          <label for="p-phone">No. HP</label>
          <input id="p-phone" v-model="form.phone" inputmode="tel" placeholder="08xxxxxxxxxx" />
        </div>
      </div>
      <div class="field">
        <label for="p-email">Email</label>
        <input id="p-email" v-model="form.email" type="email" required />
      </div>

      <button class="link-toggle" type="button" @click="showPassword = !showPassword">
        {{ showPassword ? "Batal ganti password" : "Ganti password" }}
      </button>
      <div v-if="showPassword" class="password-box">
        <div class="field">
          <label for="p-cur">Password saat ini</label>
          <input id="p-cur" v-model="form.current_password" type="password" autocomplete="current-password" />
        </div>
        <div class="field">
          <label for="p-new">Password baru</label>
          <input id="p-new" v-model="form.new_password" type="password" minlength="6" autocomplete="new-password" />
        </div>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </form>

    <template #footer>
      <button class="btn-ghost" type="button" @click="open = false">Batal</button>
      <button class="btn-primary" type="submit" form="profile-form" :disabled="saving">
        {{ saving ? "Menyimpan..." : "Simpan" }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import BaseModal from "./BaseModal.vue";
import UserAvatar from "./UserAvatar.vue";
import api from "../services/api";
import { auth } from "../stores/auth";

const props = defineProps({ modelValue: Boolean });
const emit = defineEmits(["update:modelValue"]);

const open = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

const user = auth.user;
const fileInput = ref(null);
const file = ref(null);
const preview = ref(null);
const removePhoto = ref(false);
const showPassword = ref(false);
const saving = ref(false);
const error = ref("");

const form = reactive({ name: "", username: "", email: "", phone: "", current_password: "", new_password: "" });

// Isi ulang form setiap modal dibuka
watch(open, (isOpen) => {
  if (!isOpen) return;
  const u = user.value || {};
  Object.assign(form, {
    name: u.name || "",
    username: u.username || "",
    email: u.email || "",
    phone: u.phone || "",
    current_password: "",
    new_password: "",
  });
  file.value = null;
  preview.value = null;
  removePhoto.value = false;
  showPassword.value = false;
  error.value = "";
});

function onFile(e) {
  const f = e.target.files[0];
  e.target.value = "";
  if (!f) return;
  if (!["image/jpeg", "image/png", "image/webp"].includes(f.type)) {
    error.value = "Format foto harus JPG, PNG, atau WEBP";
    return;
  }
  if (f.size > 3 * 1024 * 1024) {
    error.value = "Ukuran foto maksimal 3 MB";
    return;
  }
  error.value = "";
  file.value = f;
  removePhoto.value = false;
  if (preview.value) URL.revokeObjectURL(preview.value);
  preview.value = URL.createObjectURL(f);
}

function clearPhoto() {
  file.value = null;
  preview.value = null;
  removePhoto.value = true;
}

async function save() {
  error.value = "";
  saving.value = true;
  try {
    const payload = {
      name: form.name,
      username: form.username,
      email: form.email,
      phone: form.phone,
    };
    if (showPassword.value && form.new_password) {
      payload.current_password = form.current_password;
      payload.new_password = form.new_password;
    }
    let { data } = await api.put("/auth/me", payload);
    if (data.access_token) auth.login(data.access_token, data); // ganti password -> token lama dicabut, pakai yang baru

    if (file.value) {
      const fd = new FormData();
      fd.append("photo", file.value);
      ({ data } = await api.post("/auth/me/photo", fd));
    } else if (removePhoto.value && data.photo_url) {
      ({ data } = await api.delete("/auth/me/photo"));
    }

    auth.setUser(data);
    open.value = false;
  } catch (err) {
    error.value = err.response?.data?.error || "Gagal menyimpan profil";
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.photo-row { display: flex; align-items: center; gap: 1.1rem; margin-bottom: 1.2rem; }
.photo-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.photo-actions .field-hint { flex-basis: 100%; margin: 0; }
.link-toggle {
  background: none;
  border: none;
  padding: 0;
  color: var(--navy-500);
  font-size: 0.85rem;
  text-decoration: underline;
  margin-bottom: 0.8rem;
}
.password-box { background: var(--cream-100); border-radius: var(--radius-sm); padding: 0.9rem 0.9rem 0.1rem; }
</style>
