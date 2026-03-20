<template>
  <div class="app-shell">
    <header class="top-nav">
      <div class="container nav-inner">
        <div class="brand">
          <div class="brand-mark">AI</div>
          <div>
            <div class="brand-title">AI 校园招聘</div>
            <div class="brand-subtitle mono">Campus Recruit Platform</div>
          </div>
        </div>
        <nav class="nav-links">
          <RouterLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
          >
            {{ item.label }}
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </RouterLink>
        </nav>
        <div class="nav-actions">
          <NotificationBell v-if="isAuthed" />
          <span class="tag mono">{{ roleLabel }}</span>
          <RouterLink v-if="isAuthed" to="/profile" class="nav-user" v-show="role === 'student'">{{ auth.user.value?.name || '我的' }}</RouterLink>
          <button class="btn btn-outline" style="padding: 4px 10px; font-size: 12px;" @click="toggleLocale">{{ locale === 'zh' ? 'EN' : '中' }}</button>
          <button v-if="showLogin" class="btn btn-outline" @click="goLogin">{{ t('auth.login') }}</button>
          <button v-else-if="isAuthed" class="btn btn-outline" @click="logoutAndGo">{{ t('auth.logout') }}</button>
        </div>
      </div>
    </header>

    <main class="page">
      <RouterView />
    </main>

    <JobAssistantBall />

    <footer class="footer">
      <div class="container footer-inner">
        <div>
          <strong>{{ t('footer.title') }}</strong>
          <p class="mono">{{ t('footer.subtitle') }}</p>
        </div>
        <div class="footer-links">
          <span class="mono">© 2024 Campus Recruit</span>
          <span class="mono">v0.1</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import JobAssistantBall from "./components/JobAssistantBall.vue";
import NotificationBell from "./components/NotificationBell.vue";
import { useAuth } from "./store/auth";
import { fetchUnreadCount } from "./services/api";

const { t, locale } = useI18n();

function toggleLocale() {
  locale.value = locale.value === 'zh' ? 'en' : 'zh';
  localStorage.setItem('locale', locale.value);
}

const router = useRouter();
const route = useRoute();
const auth = useAuth();

const isAuthed = computed(() => auth.isAuthed.value);
const role = computed(() => auth.role.value);

const unreadCount = ref(0);
let unreadTimer = null;

async function loadUnread() {
  if (!isAuthed.value) return;
  try {
    const res = await fetchUnreadCount();
    unreadCount.value = res.count || 0;
  } catch (e) {
    unreadCount.value = 0;
  }
}

onMounted(() => {
  loadUnread();
  unreadTimer = setInterval(loadUnread, 15000);
});

onBeforeUnmount(() => {
  if (unreadTimer) clearInterval(unreadTimer);
});
const roleLabel = computed(() => {
  if (!isAuthed.value) return t('role.notLoggedIn');
  return { student: t('role.student'), company: t('role.company'), admin: t('role.admin') }[role.value] || t('role.unknown');
});

const navItems = computed(() => {
  if (!isAuthed.value) {
    return [
      { label: t('nav.home'), path: "/" }
    ];
  }
  const msgBadge = unreadCount.value > 0 ? (unreadCount.value > 99 ? '99+' : unreadCount.value) : null;
  if (role.value === "student") {
    return [
      { label: t('nav.dashboard'), path: "/dashboard" },
      { label: t('nav.jobs'), path: "/jobs" },
      { label: t('nav.favorites'), path: "/favorites" },
      { label: t('nav.viewHistory'), path: "/view-history" },
      { label: t('nav.ai'), path: "/ai" },
      { label: t('nav.interview'), path: "/interview-flow" },
      { label: t('nav.messages'), path: "/messages", badge: msgBadge },
      { label: t('nav.profile'), path: "/profile" }
    ];
  }
  if (role.value === "company") {
    return [
      { label: t('nav.dashboard'), path: "/dashboard" },
      { label: t('nav.jobManagement'), path: "/jobs" },
      { label: t('nav.companyCenter'), path: "/company-center" },
      { label: t('nav.ai'), path: "/ai" },
      { label: t('nav.aiInterview'), path: "/interview-flow" },
      { label: t('nav.messages'), path: "/messages", badge: msgBadge }
    ];
  }
  return [
    { label: t('nav.dashboard'), path: "/dashboard" },
    { label: t('nav.companies'), path: "/companies" },
    { label: t('nav.adminCenter'), path: "/admin-center" },
    { label: t('nav.messages'), path: "/messages", badge: msgBadge }
  ];
});

const showLogin = computed(() => !isAuthed.value && route.name !== "login");

function goLogin() {
  router.push("/login");
}

function logoutAndGo() {
  auth.logout();
  router.push("/login");
}
</script>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(245, 248, 247, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line);
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 18px;
}

.brand-title {
  font-weight: 700;
}

.brand-subtitle {
  color: var(--muted);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.nav-link {
  color: var(--muted);
  font-weight: 600;
  padding: 6px 8px;
  border-radius: 999px;
}

.nav-link {
  position: relative;
}

.nav-link.router-link-active {
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
}

.nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 99px;
  background: #e53e3e;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  margin-left: 4px;
  line-height: 1;
}

.nav-user {
  font-weight: 600;
  color: var(--accent-dark);
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(24, 160, 88, 0.08);
  font-size: 13px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page {
  min-height: 70vh;
}

.footer {
  padding: 32px 0 48px;
  border-top: 1px solid var(--line);
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.footer-links {
  display: flex;
  gap: 12px;
}

@media (max-width: 900px) {
  .nav-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .nav-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
