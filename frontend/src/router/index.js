import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";
import Dashboard from "../views/Dashboard.vue";
import Transactions from "../views/Transactions.vue";
import Targets from "../views/Targets.vue";
import ForgotPassword from "../views/ForgotPassword.vue";
import ResetPassword from "../views/ResetPassword.vue";
import VerifyEmail from "../views/VerifyEmail.vue";

const routes = [
  { path: "/login", name: "login", component: Login },
  { path: "/register", name: "register", component: Register },
  { path: "/forgot-password", name: "forgot-password", component: ForgotPassword },
  { path: "/reset-password", name: "reset-password", component: ResetPassword },
  { path: "/verify-email", name: "verify-email", component: VerifyEmail },
  { path: "/", name: "dashboard", component: Dashboard, meta: { requiresAuth: true } },
  { path: "/transactions", name: "transactions", component: Transactions, meta: { requiresAuth: true } },
  { path: "/targets", name: "targets", component: Targets, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem("access_token");
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: "login" });
  } else if ((to.name === "login" || to.name === "register") && isAuthenticated) {
    next({ name: "dashboard" });
  } else {
    next();
  }
});

export default router;
