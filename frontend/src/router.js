import { createRouter, createWebHistory } from "vue-router";

import HomePage from "./pages/HomePage.vue";
import LoginPage from "./pages/LoginPage.vue";
import DashboardPage from "./pages/DashboardPage.vue";
import JobsPage from "./pages/JobsPage.vue";
import CompaniesPage from "./pages/CompaniesPage.vue";
import AiPage from "./pages/AiPage.vue";
import MessagesPage from "./pages/MessagesPage.vue";
import ProfilePage from "./pages/ProfilePage.vue";
import CompanyCenterPage from "./pages/CompanyCenterPage.vue";
import CompanyCandidateDetailPage from "./pages/CompanyCandidateDetailPage.vue";
import AdminCenterPage from "./pages/AdminCenterPage.vue";
import JobDetailPage from "./pages/JobDetailPage.vue";
import FavoritesPage from "./pages/FavoritesPage.vue";
import NotificationsPage from "./pages/NotificationsPage.vue";
import InterviewFlowPage from "./pages/InterviewFlowPage.vue";
import ViewHistoryPage from "./pages/ViewHistoryPage.vue";
import MyApplicationsPage from "./pages/MyApplicationsPage.vue";
import { useAuth } from "./store/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomePage, meta: { public: true } },
    { path: "/login", name: "login", component: LoginPage, meta: { public: true } },
    { path: "/dashboard", name: "dashboard", component: DashboardPage },
    { path: "/jobs", name: "jobs", component: JobsPage, meta: { public: true } },
    { path: "/jobs/:id", name: "job-detail", component: JobDetailPage, meta: { public: true } },
    { path: "/companies", name: "companies", component: CompaniesPage, meta: { roles: ["admin"] } },
    { path: "/admin-center", name: "admin-center", component: AdminCenterPage, meta: { roles: ["admin"] } },
    { path: "/company-center", name: "company-center", component: CompanyCenterPage, meta: { roles: ["company"] } },
    { path: "/company-center/candidates/:applicationId", name: "company-candidate-detail", component: CompanyCandidateDetailPage, meta: { roles: ["company"] } },
    { path: "/ai", name: "ai", component: AiPage, meta: { roles: ["student", "company", "admin"] } },
    { path: "/messages", name: "messages", component: MessagesPage, meta: { roles: ["student", "company", "admin"] } },
    { path: "/my-applications", name: "my-applications", component: MyApplicationsPage, meta: { roles: ["student"] } },
    { path: "/profile", name: "profile", component: ProfilePage, meta: { roles: ["student"] } },
    { path: "/favorites", name: "favorites", component: FavoritesPage, meta: { roles: ["student"] } },
    { path: "/notifications", name: "notifications", component: NotificationsPage, meta: { roles: ["student", "company", "admin"] } },
    { path: "/interview-flow", name: "interview-flow", component: InterviewFlowPage, meta: { roles: ["student", "company"] } },
    { path: "/view-history", name: "view-history", component: ViewHistoryPage, meta: { roles: ["student"] } }
  ],
  scrollBehavior() {
    return { top: 0 };
  }
});

router.beforeEach((to) => {
  if (to.meta.public) {
    if (to.name === "login") {
      const auth = useAuth();
      if (auth.isAuthed.value) {
        return { name: "dashboard" };
      }
    }
    return true;
  }
  const auth = useAuth();
  if (!auth.isAuthed.value) {
    return { name: "login" };
  }
  if (to.meta.roles && !to.meta.roles.includes(auth.role.value)) {
    return { name: "dashboard" };
  }
  return true;
});

export default router;
