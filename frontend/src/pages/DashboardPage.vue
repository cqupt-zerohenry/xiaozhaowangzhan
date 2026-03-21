<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>{{ dashboardTitle }}</h1>
            <p>{{ dashboardSubtitle }}</p>
          </div>
          <div class="hero-actions">
            <span class="tag mono">角色：{{ roleLabel }}</span>
            <button class="btn btn-outline" @click="logoutAndGo">退出登录</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container grid kpi-grid">
        <article class="card kpi-card" v-for="item in kpiCards" :key="item.label">
          <p class="mono">{{ item.label }}</p>
          <strong>{{ item.value }}</strong>
          <span>{{ item.tip }}</span>
        </article>
      </div>
    </section>

    <section>
      <div class="container grid cards-grid">
        <div class="card" v-for="item in dashboardCards" :key="item.title">
          <div class="card-top">
            <span class="entry-icon">{{ item.icon }}</span>
          </div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
          <button class="btn btn-outline" @click="go(item.path)">{{ item.action }}</button>
        </div>
      </div>
    </section>

    <section class="secondary" v-if="role === 'student'">
      <div class="container">
        <div class="section-title">
          <h2>学习与准备</h2>
          <p>来自 AI 的学习路径与面试建议。</p>
        </div>
        <div class="grid cards-3">
          <div class="card">
            <h3>学习路径</h3>
            <p>AI 根据你的技能和目标岗位生成个性化学习路径。</p>
            <button class="btn btn-outline" @click="go('/ai')">查看详情</button>
          </div>
          <div class="card">
            <h3>模拟面试计划</h3>
            <p>为目标岗位生成面试清单。</p>
            <button class="btn btn-outline" @click="go('/ai')">进入 AI</button>
          </div>
          <div class="card">
            <h3>简历改进建议</h3>
            <p>基于岗位 JD 的优化清单。</p>
            <button class="btn btn-outline" @click="go('/ai')">查看建议</button>
          </div>
        </div>
      </div>
    </section>

    <section class="secondary" v-else-if="role === 'company'">
      <div class="container">
        <div class="section-title">
          <h2>招聘效率面板</h2>
          <p>集中管理候选人、岗位与 AI 面试。</p>
        </div>
        <div class="grid cards-3">
          <div class="card">
            <h3>候选人池</h3>
            <p>按技能与学校快速筛选。</p>
            <button class="btn btn-outline" @click="go('/company-center')">查看候选人</button>
          </div>
          <div class="card">
            <h3>AI 面试流程</h3>
            <p>为岗位生成标准问题与评分。</p>
            <button class="btn btn-outline" @click="go('/ai')">进入 AI</button>
          </div>
          <div class="card">
            <h3>消息提醒</h3>
            <p>统一查看沟通与面试邀约。</p>
            <button class="btn btn-outline" @click="go('/messages')">查看消息</button>
          </div>
        </div>
      </div>
    </section>

    <section class="secondary" v-else>
      <div class="container">
        <div class="section-title">
          <h2>校方监管看板</h2>
          <p>聚合企业审核、学生认证与就业数据。</p>
        </div>
        <div class="grid cards-3">
          <div class="card">
            <h3>企业审核进度</h3>
            <p>待审核企业：{{ pendingCompanies }}</p>
            <button class="btn btn-outline" @click="go('/companies')">进入审核</button>
          </div>
          <div class="card">
            <h3>平台统计</h3>
            <p>学生 {{ stats.student_total }} · 企业 {{ stats.company_total }}</p>
            <button class="btn btn-outline" @click="go('/admin-center')">查看数据</button>
          </div>
          <div class="card">
            <h3>公告管理</h3>
            <p>已发布 {{ announcements.length }} 条公告</p>
            <button class="btn btn-outline" @click="go('/admin-center')">管理公告</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchAnnouncements, fetchApplications, fetchCompanies, fetchFavorites, fetchJobs, fetchStats } from "../services/api";
import { useAuth } from "../store/auth";

const router = useRouter();
const auth = useAuth();

const role = computed(() => auth.role.value);
const roleLabel = computed(() => ({
  student: "学生",
  company: "招聘公司",
  admin: "校方"
})[role.value] || "未知");

const stats = ref({ student_total: 0, company_total: 0, job_total: 0, application_total: 0 });
const announcements = ref([]);
const pendingCompanies = ref(0);
const favoriteCount = ref(0);
const studentApplicationCount = ref(0);
const studentInterviewingCount = ref(0);
const companyJobCount = ref(0);
const companyApplicationCount = ref(0);
const companyActiveProcessCount = ref(0);

const dashboardTitle = computed(() => {
  if (role.value === "student") return "学生工作台";
  if (role.value === "company") return "企业招聘工作台";
  return "校方管理工作台";
});

const dashboardSubtitle = computed(() => {
  if (role.value === "student") return "聚合职位、AI 与学习建议。";
  if (role.value === "company") return "集中管理岗位、候选人与沟通。";
  return "统一审核、监管与就业统计。";
});

const dashboardCards = computed(() => {
  if (role.value === "student") {
    return [
      { title: "推荐职位", desc: favoriteCount.value > 0 ? `已收藏 ${favoriteCount.value} 个岗位` : "根据技能匹配岗位。", action: "去找职位", path: "/jobs", icon: "职" },
      { title: "AI 助手", desc: "岗位匹配、RAG 与面试。", action: "进入 AI", path: "/ai", icon: "智" },
      { title: "消息中心", desc: "查看企业沟通。", action: "查看消息", path: "/messages", icon: "信" }
    ];
  }
  if (role.value === "company") {
    return [
      { title: "职位管理", desc: "发布与管理岗位。", action: "进入职位", path: "/jobs", icon: "岗" },
      { title: "企业中心", desc: "完善主页与认证信息。", action: "进入中心", path: "/company-center", icon: "企" },
      { title: "消息中心", desc: "沟通与邀约集中处理。", action: "查看消息", path: "/messages", icon: "信" }
    ];
  }
  return [
    { title: "企业审核", desc: "审核企业资质。", action: "进入审核", path: "/companies", icon: "审" },
    { title: "平台统计", desc: "查看就业数据。", action: "进入中心", path: "/admin-center", icon: "数" },
    { title: "公告管理", desc: "发布通知公告。", action: "管理公告", path: "/admin-center", icon: "告" }
  ];
});

const kpiCards = computed(() => {
  if (role.value === "student") {
    return [
      { label: "我的投递", value: studentApplicationCount.value, tip: "累计投递记录" },
      { label: "面试阶段", value: studentInterviewingCount.value, tip: "面试中状态" },
      { label: "岗位收藏", value: favoriteCount.value, tip: "收藏可快速复投" }
    ];
  }
  if (role.value === "company") {
    return [
      { label: "我的岗位", value: companyJobCount.value, tip: "当前可管理岗位" },
      { label: "收到投递", value: companyApplicationCount.value, tip: "所有候选人投递" },
      { label: "进行中流程", value: companyActiveProcessCount.value, tip: "待继续推进候选人" }
    ];
  }
  return [
    { label: "学生总数", value: stats.value.student_total, tip: "平台注册学生" },
    { label: "企业总数", value: stats.value.company_total, tip: "认证企业总量" },
    { label: "待审企业", value: pendingCompanies.value, tip: "待校方处理" },
    { label: "公告数量", value: announcements.value.length, tip: "已发布平台公告" }
  ];
});

function go(path) {
  router.push(path);
}

function logoutAndGo() {
  auth.logout();
  router.push("/login");
}

onMounted(async () => {
  if (role.value === "admin") {
    try {
      stats.value = await fetchStats();
    } catch (err) {
      // ignore
    }
    try {
      announcements.value = await fetchAnnouncements();
    } catch (err) {
      announcements.value = [];
    }
    try {
      const companies = await fetchCompanies();
      pendingCompanies.value = companies.filter((item) => item.status === "pending").length;
    } catch (err) {
      pendingCompanies.value = 0;
    }
  }
  if (role.value === "student") {
    try {
      const favs = await fetchFavorites();
      favoriteCount.value = favs.length;
    } catch (e) {
      favoriteCount.value = 0;
    }
    try {
      const applications = await fetchApplications();
      studentApplicationCount.value = applications.length;
      studentInterviewingCount.value = applications.filter((item) => item.status === "interviewing").length;
    } catch (e) {
      studentApplicationCount.value = 0;
      studentInterviewingCount.value = 0;
    }
  }
  if (role.value === "company") {
    try {
      const jobs = await fetchJobs();
      companyJobCount.value = jobs.filter((job) => Number(job.company_id) === Number(auth.user.value?.id)).length;
    } catch (e) {
      companyJobCount.value = 0;
    }
    try {
      const applications = await fetchApplications();
      companyApplicationCount.value = applications.length;
      const activeStatuses = new Set(["submitted", "viewed", "reviewing", "to_contact", "interview_scheduled", "interviewing"]);
      companyActiveProcessCount.value = applications.filter((item) => activeStatuses.has(item.status)).length;
    } catch (e) {
      companyApplicationCount.value = 0;
      companyActiveProcessCount.value = 0;
    }
  }
});
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero {
  padding: 28px 0 8px;
}

.hero-panel {
  border-radius: 22px;
  border: 1px solid #cfeadb;
  background: linear-gradient(130deg, #f3fbf7 0%, #eff9f3 56%, #ffffff 100%);
  box-shadow: 0 16px 30px rgba(15, 122, 70, 0.08);
  padding: clamp(18px, 2.3vw, 28px);
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cards-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.kpi-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.kpi-card {
  border: 1px solid #d2eadc;
  padding: 16px 18px;
  gap: 6px;
}

.kpi-card strong {
  color: var(--accent-dark);
  font-size: 30px;
  line-height: 1.1;
}

.kpi-card span {
  color: #4f6f63;
  font-size: 13px;
}

.cards-3 {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.cards-grid .card,
.cards-3 .card {
  border: 1px solid #d8eee1;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.cards-grid .card:hover,
.cards-3 .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 28px rgba(15, 122, 70, 0.08);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.entry-icon {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.section-title {
  margin-bottom: 20px;
}

.secondary {
  padding-top: 0;
}
</style>
