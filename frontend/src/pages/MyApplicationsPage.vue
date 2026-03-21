<template>
  <div class="page-wrap my-app-page">
    <section class="page-hero hero-shell">
      <div class="container hero-head">
        <div>
          <p class="hero-eyebrow">投递进度中心</p>
          <h1>我的投递记录</h1>
          <p>按状态筛选、按公司和岗位搜索，实时跟踪每份投递进度。</p>
        </div>
        <div class="hero-actions">
          <router-link to="/jobs" class="btn">继续投递</router-link>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="loading" class="card mono">加载中...</div>

        <div v-else-if="applications.length === 0" class="card empty-state">
          <h3>你还没有投递记录</h3>
          <p>去职位页投递后会在这里显示进度。</p>
          <router-link to="/jobs" class="btn">去投递</router-link>
        </div>

        <template v-else>
          <div class="summary-grid">
            <article class="summary-card">
              <strong>{{ summaryStats.total }}</strong>
              <span>总投递</span>
            </article>
            <article class="summary-card">
              <strong>{{ summaryStats.pending }}</strong>
              <span>进行中</span>
            </article>
            <article class="summary-card">
              <strong>{{ summaryStats.interviewing }}</strong>
              <span>面试阶段</span>
            </article>
            <article class="summary-card">
              <strong>{{ summaryStats.passed }}</strong>
              <span>已通过</span>
            </article>
          </div>

          <div class="record-layout">
            <aside class="card filter-panel">
              <h3>筛选条件</h3>
              <label class="filter-label">搜索公司/岗位</label>
              <input v-model.trim="searchKeyword" placeholder="例如：腾讯 / 前端开发" />

              <label class="filter-label">投递状态</label>
              <div class="status-filter-list">
                <button
                  v-for="opt in statusFilters"
                  :key="opt.key"
                  type="button"
                  class="status-filter-btn"
                  :class="{ active: activeStatus === opt.key }"
                  @click="activeStatus = opt.key"
                >
                  <span>{{ opt.label }}</span>
                  <span class="count">{{ statusCount(opt.key) }}</span>
                </button>
              </div>
            </aside>

            <div class="record-main">
              <div class="record-toolbar card">
                <span class="mono">共 {{ filteredApplications.length }} 条 · 第 {{ page }} / {{ totalPages }} 页</span>
                <div class="toolbar-actions">
                  <select v-model="sortBy">
                    <option value="latest">按最近更新</option>
                    <option value="oldest">按最早投递</option>
                    <option value="company">按企业名称</option>
                    <option value="status">按状态</option>
                  </select>
                  <button type="button" class="btn btn-outline" @click="resetFilters">重置筛选</button>
                </div>
              </div>

              <div v-if="filteredApplications.length === 0" class="card empty-state">
                <h3>没有匹配到结果</h3>
                <p>可以调整状态筛选或搜索关键词。</p>
              </div>

              <article v-for="item in pagedApplications" :key="item.id" class="card app-card">
                <div class="app-header">
                  <div>
                    <h3>
                      <router-link :to="`/jobs/${item.job_id}`" class="job-link">{{ jobName(item.job_id) }}</router-link>
                    </h3>
                    <p class="company-line">{{ companyName(item.job_id) || '企业信息加载中' }}</p>
                  </div>
                  <div class="header-right">
                    <span class="status-pill" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
                    <span class="mono">投递于 {{ formatTime(item.create_time) }}</span>
                  </div>
                </div>

                <div class="progress-wrap">
                  <div class="step-bar">
                    <template v-for="(step, idx) in appSteps" :key="step.key">
                      <div class="step-node" :class="stepClass(item.status, step.key)"></div>
                      <div v-if="idx < appSteps.length - 1" class="step-line" :class="{ done: stepDone(item.status, step.key) }"></div>
                    </template>
                  </div>
                  <div class="step-labels">
                    <span
                      v-for="step in appSteps"
                      :key="step.key"
                      class="step-label"
                      :class="{ active: item.status === step.key }"
                    >
                      {{ step.label }}
                    </span>
                  </div>
                </div>

                <div class="app-actions">
                  <button
                    v-if="item.status === 'submitted'"
                    type="button"
                    class="btn btn-outline"
                    @click="withdraw(item.id)"
                  >
                    撤回投递
                  </button>
                  <router-link :to="`/jobs/${item.job_id}`" class="btn btn-outline">查看岗位详情</router-link>
                </div>
              </article>

              <div v-if="totalPages > 1" class="pager">
                <button type="button" class="btn btn-outline" :disabled="page <= 1" @click="page -= 1">上一页</button>
                <span class="mono">第 {{ page }} / {{ totalPages }} 页</span>
                <button type="button" class="btn btn-outline" :disabled="page >= totalPages" @click="page += 1">下一页</button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import toast from '../utils/toast';
import { fetchApplications, fetchCompanies, fetchCompany, fetchJob, updateApplicationStatus } from '../services/api';

const applications = ref([]);
const loading = ref(false);
const jobsMap = ref({});
const companiesMap = ref({});
const searchKeyword = ref('');
const activeStatus = ref('all');
const sortBy = ref('latest');
const page = ref(1);
const PAGE_SIZE = 6;

const appSteps = [
  { key: 'submitted', label: '已投递' },
  { key: 'viewed', label: '已查看' },
  { key: 'reviewing', label: '筛选中' },
  { key: 'to_contact', label: '待沟通' },
  { key: 'interview_scheduled', label: '面试已安排' },
  { key: 'interviewing', label: '面试中' },
  { key: 'accepted', label: '已通过' },
];

const statusFilters = [
  { key: 'all', label: '全部' },
  { key: 'submitted', label: '已投递' },
  { key: 'viewed', label: '已查看' },
  { key: 'reviewing', label: '筛选中' },
  { key: 'to_contact', label: '待沟通' },
  { key: 'interview_scheduled', label: '面试已安排' },
  { key: 'interviewing', label: '面试中' },
  { key: 'accepted', label: '已通过' },
  { key: 'rejected', label: '已淘汰' },
  { key: 'withdrawn', label: '已撤回' }
];

const stepOrder = appSteps.map((s) => s.key);

const statusTextMap = {
  submitted: '已投递',
  viewed: '已查看',
  reviewing: '筛选中',
  to_contact: '待沟通',
  interview_scheduled: '面试已安排',
  interviewing: '面试中',
  accepted: '已通过',
  rejected: '已淘汰',
  withdrawn: '已撤回'
};

const sortedApplications = computed(() => {
  const rows = [...applications.value];
  if (sortBy.value === 'oldest') {
    return rows.sort((a, b) => {
      const timeA = new Date(a.create_time || 0).getTime();
      const timeB = new Date(b.create_time || 0).getTime();
      return timeA - timeB;
    });
  }
  if (sortBy.value === 'company') {
    return rows.sort((a, b) => {
      const companyA = companyName(a.job_id) || '';
      const companyB = companyName(b.job_id) || '';
      return companyA.localeCompare(companyB, 'zh-CN');
    });
  }
  if (sortBy.value === 'status') {
    const order = {
      submitted: 0,
      viewed: 1,
      reviewing: 2,
      to_contact: 3,
      interview_scheduled: 4,
      interviewing: 5,
      accepted: 6,
      rejected: 7,
      withdrawn: 8
    };
    return rows.sort((a, b) => (order[a.status] ?? 99) - (order[b.status] ?? 99));
  }
  return rows.sort((a, b) => {
    const timeA = new Date(a.update_time || a.create_time || 0).getTime();
    const timeB = new Date(b.update_time || b.create_time || 0).getTime();
    return timeB - timeA;
  });
});

const filteredApplications = computed(() => {
  let list = sortedApplications.value;

  if (activeStatus.value !== 'all') {
    list = list.filter((item) => item.status === activeStatus.value);
  }

  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return list;

  return list.filter((item) => {
    const name = (jobName(item.job_id) || '').toLowerCase();
    const company = (companyName(item.job_id) || '').toLowerCase();
    return name.includes(keyword) || company.includes(keyword);
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredApplications.value.length / PAGE_SIZE)));

const pagedApplications = computed(() => {
  const current = Math.min(page.value, totalPages.value);
  const start = (current - 1) * PAGE_SIZE;
  return filteredApplications.value.slice(start, start + PAGE_SIZE);
});

const summaryStats = computed(() => {
  const total = applications.value.length;
  const pendingStatuses = ['submitted', 'viewed', 'reviewing', 'to_contact', 'interview_scheduled'];
  const pending = applications.value.filter((item) => pendingStatuses.includes(item.status)).length;
  const interviewing = applications.value.filter((item) => item.status === 'interviewing').length;
  const passed = applications.value.filter((item) => item.status === 'accepted').length;

  return { total, pending, interviewing, passed };
});

function statusCount(statusKey) {
  if (statusKey === 'all') return applications.value.length;
  return applications.value.filter((item) => item.status === statusKey).length;
}

function stepClass(status, stepKey) {
  if (status === 'rejected' || status === 'withdrawn') return '';
  const current = stepOrder.indexOf(status);
  const target = stepOrder.indexOf(stepKey);
  if (target < current) return 'done';
  if (target === current) return 'current';
  return '';
}

function stepDone(status, stepKey) {
  if (status === 'rejected' || status === 'withdrawn') return false;
  return stepOrder.indexOf(stepKey) < stepOrder.indexOf(status);
}

function formatTime(value) {
  if (!value) return '--';
  return String(value).replace('T', ' ').slice(0, 16);
}

function statusLabel(status) {
  return statusTextMap[status] || status;
}

function statusClass(status) {
  const map = {
    submitted: 'pill-s1',
    viewed: 'pill-s2',
    reviewing: 'pill-s3',
    to_contact: 'pill-s4',
    interview_scheduled: 'pill-s5',
    interviewing: 'pill-s6',
    accepted: 'pill-s7',
    rejected: 'pill-s8',
    withdrawn: 'pill-s9'
  };
  return map[status] || 'pill-s9';
}

function jobName(jobId) {
  const job = jobsMap.value[jobId];
  return job?.job_name || `岗位 #${jobId}`;
}

function companyName(jobId) {
  const job = jobsMap.value[jobId];
  if (!job?.company_id) return '';
  return companiesMap.value[job.company_id]?.company_name || '';
}

async function loadApplicationMeta(list) {
  const jobIds = [...new Set((list || []).map((item) => item.job_id).filter(Boolean))];
  if (!jobIds.length) {
    jobsMap.value = {};
    companiesMap.value = {};
    return;
  }

  const jobEntries = await Promise.all(
    jobIds.map(async (jobId) => {
      try {
        const job = await fetchJob(jobId);
        return [jobId, job];
      } catch (_) {
        return [jobId, null];
      }
    })
  );

  const nextJobsMap = {};
  const companyIds = [];
  for (const [jobId, job] of jobEntries) {
    if (job) {
      nextJobsMap[jobId] = job;
      if (job.company_id) companyIds.push(job.company_id);
    }
  }
  jobsMap.value = nextJobsMap;

  const uniqueCompanyIds = [...new Set(companyIds)];
  if (!uniqueCompanyIds.length) {
    companiesMap.value = {};
    return;
  }

  try {
    const companies = await fetchCompanies();
    const map = {};
    for (const item of companies || []) {
      if (uniqueCompanyIds.includes(item.user_id)) {
        map[item.user_id] = item;
      }
    }

    const missing = uniqueCompanyIds.filter((id) => !map[id]);
    if (missing.length) {
      const fallback = await Promise.all(
        missing.map(async (id) => {
          try {
            const c = await fetchCompany(id);
            return [id, c];
          } catch (_) {
            return [id, null];
          }
        })
      );
      for (const [id, c] of fallback) {
        if (c) map[id] = c;
      }
    }
    companiesMap.value = map;
  } catch (_) {
    const entries = await Promise.all(
      uniqueCompanyIds.map(async (id) => {
        try {
          const c = await fetchCompany(id);
          return [id, c];
        } catch (_) {
          return [id, null];
        }
      })
    );
    const map = {};
    for (const [id, c] of entries) {
      if (c) map[id] = c;
    }
    companiesMap.value = map;
  }
}

async function load() {
  loading.value = true;
  try {
    applications.value = await fetchApplications();
    await loadApplicationMeta(applications.value);
    page.value = 1;
  } catch (_) {
    applications.value = [];
    jobsMap.value = {};
    companiesMap.value = {};
    toast.error('加载投递记录失败');
  } finally {
    loading.value = false;
  }
}

async function withdraw(applicationId) {
  if (!confirm('确定要撤回该投递吗？')) return;
  try {
    await updateApplicationStatus(applicationId, { status: 'withdrawn' });
    toast.success('投递已撤回');
    await load();
  } catch (_) {
    toast.error('撤回失败，请稍后重试');
  }
}

function resetFilters() {
  searchKeyword.value = '';
  activeStatus.value = 'all';
  sortBy.value = 'latest';
  page.value = 1;
}

watch([searchKeyword, activeStatus, sortBy], () => {
  page.value = 1;
});

watch(totalPages, (total) => {
  if (page.value > total) page.value = total;
});

onMounted(load);
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.my-app-page {
  --green-main: #0f9f58;
  --green-deep: #0b7d45;
  --green-soft: #edf8f2;
  --green-line: #cfeadb;
}

.hero-shell {
  padding: 30px 0 12px;
}

.hero-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 26px 30px;
  background: linear-gradient(120deg, #f2fbf6 0%, #edf8f2 60%, #ffffff 100%);
  border: 1px solid var(--green-line);
  border-radius: 20px;
}

.hero-eyebrow {
  margin-bottom: 6px;
  color: var(--green-main);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-weight: 700;
  font-size: 11px;
}

.hero-head h1 {
  margin-bottom: 6px;
}

.hero-head p {
  margin: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.summary-card {
  background: #fff;
  border: 1px solid #d5edde;
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-card strong {
  color: var(--green-deep);
  font-size: 28px;
  line-height: 1;
}

.summary-card span {
  color: #4d6e61;
  font-size: 13px;
}

.record-layout {
  display: grid;
  grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.filter-panel {
  position: sticky;
  top: 120px;
  border: 1px solid #d5edde;
  box-shadow: 0 12px 24px rgba(15, 122, 70, 0.08);
}

.filter-label {
  margin-top: 8px;
  margin-bottom: 6px;
  color: #4d6e61;
  font-size: 12px;
  font-weight: 600;
}

.status-filter-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-filter-btn {
  width: 100%;
  border: 1px solid #d5edde;
  background: #f5fbf7;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  color: #1f4637;
  cursor: pointer;
  transition: all 0.16s ease;
}

.status-filter-btn:hover {
  border-color: #b8dfc9;
  background: #edf8f2;
}

.status-filter-btn.active {
  border-color: #70be92;
  background: #e4f5ec;
  color: #0b7d45;
  font-weight: 600;
}

.status-filter-btn .count {
  color: #5f7f72;
  font-size: 12px;
}

.record-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-toolbar {
  border: 1px solid #d5edde;
  box-shadow: 0 10px 22px rgba(15, 122, 70, 0.07);
  padding: 14px 16px;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-actions select {
  height: 40px;
  border-radius: 10px;
  border: 1px solid #cfe4d8;
  padding: 0 10px;
  background: #fff;
}

.app-card {
  border: 1px solid #d5edde;
  box-shadow: 0 12px 26px rgba(15, 122, 70, 0.08);
  gap: 14px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  flex-wrap: wrap;
}

.job-link {
  color: #152748;
  text-decoration: none;
}

.job-link:hover {
  color: var(--green-main);
}

.company-line {
  margin: 6px 0 0;
  color: #5f7f72;
  font-size: 13px;
}

.header-right {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.pill-s1 { background: #edf8f2; color: #0f9f58; border-color: #c4e7d3; }
.pill-s2 { background: #e9f6ef; color: #0e9552; border-color: #bfe2ce; }
.pill-s3 { background: #e3f3eb; color: #0d8c4c; border-color: #b3dbbf; }
.pill-s4 { background: #dff1e8; color: #0c8447; border-color: #a9d6b9; }
.pill-s5 { background: #d9eee3; color: #0b7d45; border-color: #9fd0b2; }
.pill-s6 { background: #d4ebde; color: #0a7440; border-color: #95c9aa; }
.pill-s7 { background: #cef0dd; color: #096d3b; border-color: #8ac2a2; }
.pill-s8 { background: #eef5f1; color: #55756a; border-color: #cadcd3; }
.pill-s9 { background: #f3f6f4; color: #698578; border-color: #d5e2db; }

.progress-wrap {
  background: #f6fbf8;
  border: 1px solid #dcefe4;
  border-radius: 12px;
  padding: 12px;
}

.step-node {
  border-color: #bfdccf;
}

.step-node.done,
.step-node.current {
  border-color: var(--green-main);
  background: var(--green-main);
}

.step-node.current {
  box-shadow: 0 0 0 4px rgba(15, 159, 88, 0.18);
}

.step-line {
  background: #cfe6da;
}

.step-line.done {
  background: var(--green-main);
}

.step-label {
  color: #6a8679;
}

.step-label.active {
  color: var(--green-main);
}

.app-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .record-layout {
    grid-template-columns: 1fr;
  }

  .filter-panel {
    position: static;
  }
}

@media (max-width: 760px) {
  .hero-head {
    padding: 20px;
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .header-right {
    align-items: flex-start;
  }

  .app-actions {
    justify-content: flex-start;
  }

  .record-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .step-label {
    font-size: 10px;
  }
}
</style>
