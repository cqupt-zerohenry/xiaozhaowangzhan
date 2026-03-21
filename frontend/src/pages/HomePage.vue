<template>
  <div class="page-wrap">
    <section class="hero">
      <div class="container hero-shell">
        <div class="hero-grid">
          <div class="hero-content">
            <span class="tag mono">校园招聘 · 多角色协同</span>
            <h1>找人更快，入职更稳。</h1>
            <p>
              企业快速发布岗位，学校审核把关，学生用 AI 提前准备。
              招聘链路更透明，匹配更精准。
            </p>
            <div class="hero-actions">
              <button class="btn" @click="go('/jobs')">立即找职位</button>
              <button class="btn btn-outline" @click="go('/ai')">体验 AI 助手</button>
            </div>
            <div class="hero-metrics">
              <div class="metric">
                <h3>{{ companies.length }}</h3>
                <p class="mono">认证企业</p>
              </div>
              <div class="metric">
                <h3>{{ jobs.length }}</h3>
                <p class="mono">开放岗位</p>
              </div>
              <div class="metric">
                <h3>6</h3>
                <p class="mono">AI 模块</p>
              </div>
            </div>
          </div>
          <div class="card hero-card">
            <h3>校园招聘中枢</h3>
            <p>统一职位、公司、消息、AI 的入口，流程清晰可控。</p>
            <div class="hero-list">
              <div class="hero-list-item">
                <strong>学校主管</strong>
                <span>审核与监管</span>
              </div>
              <div class="hero-list-item">
                <strong>企业招聘</strong>
                <span>发布与沟通</span>
              </div>
              <div class="hero-list-item">
                <strong>学生</strong>
                <span>简历与练习</span>
              </div>
            </div>
            <div class="hero-footer">
              <span class="mono">实时数据来自 FastAPI</span>
              <span class="status" :class="apiHealthy ? 'ok' : 'down'">
                {{ apiHealthy ? '后端在线' : '后端离线' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="quick-actions">
      <div class="container">
        <div class="section-title">
          <h2>核心功能一览</h2>
          <p>突出高频操作，提升招聘效率。</p>
        </div>
        <div class="grid cards-3">
          <div class="card">
            <h3>职位发布与筛选</h3>
            <p>企业发布 JD，学生按技能快速筛选。</p>
            <button class="btn btn-outline" @click="go('/jobs')">查看职位</button>
          </div>
          <div class="card">
            <h3>企业认证与管理</h3>
            <p>学校审核资质，企业通过后展示主页。</p>
            <button class="btn btn-outline" @click="go('/companies')">查看企业</button>
          </div>
          <div class="card">
            <h3>AI 招聘加速</h3>
            <p>匹配、RAG 与面试一体化。</p>
            <button class="btn btn-outline" @click="go('/ai')">进入 AI</button>
          </div>
        </div>
      </div>
    </section>

    <section class="recommend">
      <div class="container">
        <div class="section-title">
          <h2>推荐岗位</h2>
          <p>快速查看最新岗位动态。</p>
        </div>
        <div class="grid list-grid">
          <div class="card job-card" v-for="job in topJobs" :key="job.id" @click="go(`/jobs/${job.id}`)">
            <div>
              <h3>{{ job.job_name }}</h3>
              <p>{{ job.description }}</p>
              <div class="job-meta mono">
                {{ job.city }} · {{ job.salary_min }}-{{ job.salary_max }}
              </div>
            </div>
            <div class="tags">
              <span class="tag" v-for="skill in job.skill_tags" :key="skill">{{ skill }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="ai-strip">
      <div class="container ai-strip-inner">
        <div>
          <h2>AI 助手已就绪</h2>
          <p>把匹配、知识检索、面试准备放在一个入口。</p>
        </div>
        <button class="btn" @click="go('/ai')">立即体验</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchCompanies, fetchJobs } from "../services/api";

const router = useRouter();

const jobs = ref([]);
const companies = ref([]);
const apiHealthy = ref(true);

const topJobs = computed(() => jobs.value.slice(0, 3));

function go(path) {
  router.push(path);
}

onMounted(async () => {
  try {
    jobs.value = await fetchJobs();
    companies.value = await fetchCompanies();
    apiHealthy.value = true;
  } catch (err) {
    jobs.value = [];
    companies.value = [];
    apiHealthy.value = false;
  }
});
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.hero {
  padding: 34px 0 8px;
}

.hero-shell {
  border-radius: 24px;
  border: 1px solid #cfeadb;
  background: linear-gradient(130deg, #f3fbf7 0%, #eff9f3 56%, #ffffff 100%);
  box-shadow: 0 18px 34px rgba(15, 122, 70, 0.08);
  padding: clamp(18px, 2.5vw, 30px);
}

.hero-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  align-items: stretch;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.metric {
  border: 1px solid #d5edde;
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
}

.metric h3 {
  margin: 0 0 6px;
  color: #0b7d45;
}

.hero-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid #d5edde;
}

.hero-list {
  display: grid;
  gap: 12px;
}

.hero-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #d7eee0;
  background: #f7fcf9;
}

.hero-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.status {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
}

.status.ok {
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
}

.status.down {
  background: rgba(235, 87, 87, 0.12);
  color: #eb5757;
}

.section-title {
  margin-bottom: 20px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.cards-3 {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.list-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.job-card {
  gap: 18px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.cards-3 .card {
  border: 1px solid #d8eee1;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.cards-3 .card:hover,
.job-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 28px rgba(15, 122, 70, 0.08);
}

.job-meta {
  color: var(--muted);
}

.ai-strip {
  padding: 24px 0 60px;
}

.ai-strip-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  border-radius: 24px;
  border: 1px solid #d2ebdd;
  background: linear-gradient(120deg, #ffffff, #eef9f3);
  padding: 24px;
}
</style>
