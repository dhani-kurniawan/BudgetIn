<template>
  <div id="layout">
    <AppHeader v-if="isAuthenticated" />
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppHeader from "./components/AppHeader.vue";
import { auth } from "./stores/auth";

const isAuthenticated = auth.isAuthenticated;
</script>
