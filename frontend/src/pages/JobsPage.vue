<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container">
        <div class="hero-panel">
          <div class="boss-layout">
            <div class="boss-intro">
              <h1>{{ title }}</h1>
              <p>{{ subtitle }}</p>
              <p class="boss-note">筛选更集中，信息层级更清楚，把高频操作放在同一区域，减少来回跳视线。</p>
            </div>
            <div class="boss-main">
              <div class="boss-primary-row">
                <label class="boss-field">
                  <span>公司</span>
                  <input v-model="company" placeholder="公司名称" @keyup.enter="loadJobs" />
                </label>
                <label class="boss-field">
                  <span>地点</span>
                  <input v-model="city" placeholder="城市" @keyup.enter="loadJobs" />
                </label>
                <label class="boss-field">
                  <span>学历</span>
                  <input v-model="education" placeholder="学历" @keyup.enter="loadJobs" />
                </label>
                <label class="boss-field boss-field-keyword">
                  <span>关键词</span>
                  <input v-model="keyword" placeholder="岗位名称或关键词" @keyup.enter="loadJobs" />
                </label>
                <button class="btn boss-btn-primary" @click="loadJobs">搜索</button>
                <button class="btn boss-btn-ghost" @click="clearFilter">清空</button>
              </div>

              <div class="quick-tags boss-tags">
                <button
                  v-for="cat in quickCategories"
                  :key="cat"
                  class="chip"
                  :class="{ active: keyword === cat }"
                  @click="onQuickCategoryClick(cat)"
                >{{ cat }}</button>
              </div>

              <div class="boss-secondary-row">
                <label class="boss-field boss-field-mini">
                  <span>最低薪资</span>
                  <input v-model.number="salaryMin" type="number" placeholder="K" @keyup.enter="loadJobs" />
                </label>
                <label class="boss-field boss-field-mini">
                  <span>排序</span>
                  <select v-model="sort">
                    <option value="">默认排序</option>
                    <option value="latest">最新发布</option>
                  </select>
                </label>
                <div class="boss-secondary-actions">
                  <button class="btn boss-btn-ghost" @click="saveFilterPreset">保存筛选</button>
                  <button class="btn boss-btn-primary" @click="loadJobs">立即搜索</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section v-if="role === 'company'">
      <div class="container">
        <div class="card">
          <h3>{{ editingJobId ? '编辑岗位' : '发布岗位' }}</h3>
          <div class="form-grid">
            <input v-model="jobForm.job_name" placeholder="岗位名称" />
            <input v-model="jobForm.job_type" placeholder="岗位类型" />
            <input v-model="jobForm.city" placeholder="城市" />
            <input v-model.number="jobForm.salary_min" type="number" placeholder="最低薪资" />
            <input v-model.number="jobForm.salary_max" type="number" placeholder="最高薪资" />
            <input v-model="jobForm.education" placeholder="学历" />
            <input v-model="jobForm.deadline" placeholder="截止日期 YYYY-MM-DD" />
            <input v-model="skillsInput" placeholder="技能标签，逗号分隔" />
          </div>
          <textarea v-model="jobForm.description" rows="3" placeholder="岗位职责"></textarea>
          <textarea v-model="jobForm.requirement" rows="3" placeholder="岗位要求"></textarea>
          <div class="actions">
            <button class="btn" @click="submitJob">{{ editingJobId ? '保存修改' : '发布岗位' }}</button>
            <button v-if="editingJobId" class="btn btn-outline" @click="resetJobForm">取消编辑</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="loadingJobs" class="mono">加载中...</div>
        <template v-else>
          <div class="list-toolbar card">
            <span class="mono">共 {{ sortedJobs.length }} 个岗位 · 第 {{ listPage }} / {{ totalJobPages }} 页</span>
            <div class="toolbar-actions">
              <select v-model="listSort">
                <option value="latest">按最近发布</option>
                <option value="salary_desc">按最高薪资</option>
                <option value="salary_asc">按最低薪资</option>
                <option value="company">按公司名称</option>
              </select>
            </div>
          </div>

          <div class="grid list-grid">
            <div class="card job-card" v-for="job in pagedJobs" :key="job.id" @click="openJobDetail(job, $event)">
              <div class="job-main">
                <div>
                  <h3><router-link :to="`/jobs/${job.id}`" class="job-link">{{ job.job_name }}</router-link></h3>
                  <p class="job-desc">{{ (job.description || '').slice(0, 80) }}{{ (job.description || '').length > 80 ? '...' : '' }}</p>
                  <div class="job-meta">
                    <span v-if="jobCompanyName(job)" class="company-name">{{ jobCompanyName(job) }}</span>
                    <span>{{ job.city }}</span>
                    <span class="salary">{{ job.salary_min }}K-{{ job.salary_max }}K</span>
                    <span>{{ job.education }}</span>
                    <span v-if="job.job_type">{{ job.job_type }}</span>
                  </div>
                </div>
                <div class="tags">
                  <span class="tag" v-for="skill in (job.skill_tags || []).slice(0, 5)" :key="skill">{{ skill }}</span>
                </div>
              </div>
              <div class="job-side">
                <div class="actions" v-if="role === 'company'">
                  <button class="btn btn-outline" @click="startEdit(job)">编辑</button>
                  <button class="btn btn-outline" @click="removeJob(job.id)">删除</button>
                </div>
                <template v-else-if="role === 'student'">
                  <button class="btn" @click="applyJob(job)">立即投递</button>
                  <button class="btn btn-outline" @click.stop="toggleFavorite(job.id)">
                    {{ isFavorited(job.id) ? '取消收藏' : '收藏' }}
                  </button>
                </template>
                <router-link v-else :to="`/jobs/${job.id}`" class="btn btn-outline">查看详情</router-link>
              </div>
            </div>
            <div v-if="sortedJobs.length === 0" class="empty-state card">
              <h3>暂无匹配岗位</h3>
              <p>尝试调整筛选条件。</p>
            </div>
          </div>

          <div v-if="totalJobPages > 1" class="pager">
            <button class="btn btn-outline" :disabled="listPage <= 1" @click="listPage -= 1">上一页</button>
            <span class="mono">第 {{ listPage }} / {{ totalJobPages }} 页</span>
            <button class="btn btn-outline" :disabled="listPage >= totalJobPages" @click="listPage += 1">下一页</button>
          </div>
        </template>
      </div>
    </section>

    <section v-if="role === 'company'">
      <div class="container">
        <div class="card">
          <div class="section-header compact">
            <h3>岗位投递记录</h3>
            <span class="mono">共 {{ filteredCompanyApplications.length }} 条 · 第 {{ applicationPage }} / {{ totalCompanyApplicationPages }} 页</span>
          </div>

          <div class="application-toolbar">
            <input v-model.trim="applicationKeyword" placeholder="搜索岗位名称 / 企业名称 / 学生ID" />
            <div class="toolbar-actions">
              <select v-model="applicationFilterStatus">
                <option value="">全部状态</option>
                <option v-for="item in companyApplicationStatusOptions" :key="`filter-${item.value}`" :value="item.value">{{ item.label }}</option>
              </select>
              <select v-model="applicationSort">
                <option value="latest">按最新投递</option>
                <option value="oldest">按最早投递</option>
                <option value="status">按状态</option>
                <option value="job">按岗位名称</option>
              </select>
            </div>
          </div>

          <div v-if="filteredCompanyApplications.length" class="batch-toolbar">
            <label class="batch-check">
              <input type="checkbox" :checked="allVisibleApplicationsSelected" @change="toggleSelectAllVisibleApplications($event.target.checked)" />
              本页全选
            </label>
            <span class="mono">已选 {{ selectedApplicationIds.length }} 条</span>
            <select v-model="batchStatusDraft">
              <option value="">批量更新状态</option>
              <option v-for="item in companyApplicationStatusOptions" :key="`batch-${item.value}`" :value="item.value">{{ item.label }}</option>
            </select>
            <button class="btn btn-outline" :disabled="batchUpdating" @click="applyBatchApplicationStatus">
              {{ batchUpdating ? '批量处理中...' : '批量更新' }}
            </button>
          </div>

          <div v-if="filteredCompanyApplications.length === 0" class="empty-state">
            暂无投递记录
          </div>

          <div v-else class="application-list">
            <div class="application-item" v-for="item in pagedCompanyApplications" :key="item.id">
              <div class="app-info">
                <div class="app-info-head">
                  <label class="app-select">
                    <input type="checkbox" :checked="isApplicationSelected(item.id)" @change="toggleApplicationSelection(item.id, $event.target.checked)" />
                  </label>
                  <strong>{{ applicationJobName(item) }}</strong>
                </div>
                <p v-if="applicationCompanyName(item)" class="mono">{{ applicationCompanyName(item) }}</p>
                <p class="mono app-meta-line">学生 ID：{{ item.student_id }} · 投递时间：{{ formatTime(item.create_time) }}</p>
                <div class="step-bar">
                  <template v-for="(step, idx) in appSteps" :key="step.key">
                    <div class="step-node" :class="stepClass(item.status, step.key)"></div>
                    <div v-if="idx < appSteps.length - 1" class="step-line" :class="{ done: stepDone(item.status, step.key) }"></div>
                  </template>
                </div>
                <div class="step-labels">
                  <span v-for="step in appSteps" :key="step.key" class="step-label" :class="{ active: item.status === step.key }">{{ step.label }}</span>
                </div>
              </div>
              <div class="actions app-status-row">
                <select v-model="applicationStatusDraft[item.id]">
                  <option v-for="statusItem in companyApplicationStatusOptions" :key="`${item.id}-${statusItem.value}`" :value="statusItem.value">{{ statusItem.label }}</option>
                </select>
                <button class="btn btn-outline" @click="updateApplication(item.id)">更新</button>
              </div>
            </div>
          </div>

          <div v-if="totalCompanyApplicationPages > 1" class="pager">
            <button class="btn btn-outline" :disabled="applicationPage <= 1" @click="applicationPage -= 1">上一页</button>
            <span class="mono">第 {{ applicationPage }} / {{ totalCompanyApplicationPages }} 页</span>
            <button class="btn btn-outline" :disabled="applicationPage >= totalCompanyApplicationPages" @click="applicationPage += 1">下一页</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import toast from '../utils/toast';
import {
  addFavorite,
  createApplication,
  createJob,
  deleteJob,
  fetchApplications,
  fetchCompany,
  fetchCompanies,
  fetchFavorites,
  fetchJob,
  fetchJobs,
  fetchResumes,
  removeFavorite,
  updateApplicationStatus,
  updateJob
} from '../services/api';
import { useAuth } from '../store/auth';

const appSteps = [
  { key: 'submitted', label: '已投递' },
  { key: 'viewed', label: '已查看' },
  { key: 'reviewing', label: '筛选中' },
  { key: 'to_contact', label: '待沟通' },
  { key: 'interview_scheduled', label: '面试已安排' },
  { key: 'interviewing', label: '面试中' },
  { key: 'accepted', label: '已通过' },
];
const stepOrder = appSteps.map(s => s.key);
const companyApplicationStatusOptions = [
  { value: 'submitted', label: '已投递' },
  { value: 'viewed', label: '已查看' },
  { value: 'reviewing', label: '筛选中' },
  { value: 'to_contact', label: '待沟通' },
  { value: 'interview_scheduled', label: '面试已安排' },
  { value: 'interviewing', label: '面试中' },
  { value: 'accepted', label: '已通过' },
  { value: 'rejected', label: '已淘汰' }
];

function stepClass(status, stepKey) {
  if (status === 'rejected' || status === 'withdrawn') return status === stepKey ? 'current' : '';
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

const jobs = ref([]);
const loadingJobs = ref(false);
const applications = ref([]);
const resumes = ref([]);
const applicationStatusDraft = ref({});
const favorites = ref([]);
const applicationJobMap = ref({});
const applicationCompanyMap = ref({});
const jobCompanyMap = ref({});
const listSort = ref('latest');
const listPage = ref(1);
const JOB_PAGE_SIZE = 8;
const applicationKeyword = ref('');
const applicationFilterStatus = ref('');
const applicationSort = ref('latest');
const applicationPage = ref(1);
const APPLICATION_PAGE_SIZE = 8;
const selectedApplicationIds = ref([]);
const batchStatusDraft = ref('');
const batchUpdating = ref(false);

async function loadFavorites() {
  if (role.value !== 'student') return;
  try {
    favorites.value = await fetchFavorites();
  } catch (e) {
    favorites.value = [];
  }
}

function isFavorited(jobId) {
  return favorites.value.some(f => f.job_id === jobId);
}

async function toggleFavorite(jobId) {
  try {
    if (isFavorited(jobId)) {
      await removeFavorite(jobId);
    } else {
      await addFavorite(jobId);
    }
    await loadFavorites();
  } catch (e) {
    toast.error('操作失败，请重试');
  }
}

const quickCategories = ['后端开发', '前端开发', 'AI算法', '产品经理', '测试', '运维/SRE', '数据分析', '设计'];
const FILTER_PRESET_KEY = 'jobs_filter_preset_v1';
const keyword = ref('');
const company = ref('');
const city = ref('');
const education = ref('');
const salaryMin = ref('');
const sort = ref('');

const router = useRouter();
const auth = useAuth();
const role = computed(() => auth.role.value);

const title = computed(() => (role.value === 'company' ? '职位管理' : '职位'));
const subtitle = computed(() =>
  role.value === 'company' ? '发布、编辑岗位并查看投递。' : '筛选岗位并在线投递。'
);

const editingJobId = ref(null);
const jobForm = ref({
  company_id: auth.user.value?.id || 0,
  job_name: '',
  job_type: '',
  city: '',
  salary_min: 8000,
  salary_max: 12000,
  education: 'Bachelor',
  description: '',
  requirement: '',
  skill_tags: [],
  status: 'active',
  deadline: ''
});
const skillsInput = ref('');

async function loadJobs() {
  loadingJobs.value = true;
  try {
    const list = await fetchJobs({
      keyword: keyword.value,
      company: company.value,
      company_id: role.value === 'company' ? auth.user.value?.id : undefined,
      city: city.value,
      education: education.value,
      salary_min: salaryMin.value,
      sort: sort.value
    });
    if (role.value === 'company') {
      const myCompanyId = Number(auth.user.value?.id || 0);
      jobs.value = (list || []).filter((item) => Number(item.company_id) === myCompanyId);
    } else {
      jobs.value = list || [];
    }
    await loadJobCompanies(jobs.value);
    listPage.value = 1;
  } catch (err) {
    jobs.value = [];
  } finally {
    loadingJobs.value = false;
  }
}

async function loadJobCompanies(list) {
  const companyIds = [...new Set((list || []).map((item) => item.company_id).filter(Boolean))];
  if (!companyIds.length) {
    jobCompanyMap.value = {};
    return;
  }

  // Try batch first for better performance.
  try {
    const companies = await fetchCompanies();
    const map = {};
    for (const company of companies || []) {
      if (companyIds.includes(company.user_id)) {
        map[company.user_id] = company.company_name || '';
      }
    }
    // Fill any missing ids with per-company fetch fallback.
    const missingIds = companyIds.filter((id) => !map[id]);
    if (missingIds.length) {
      const fallback = await Promise.all(
        missingIds.map(async (id) => {
          try {
            const c = await fetchCompany(id);
            return [id, c.company_name || ''];
          } catch (_) {
            return [id, ''];
          }
        })
      );
      for (const [id, name] of fallback) {
        map[id] = name;
      }
    }
    jobCompanyMap.value = map;
  } catch (_) {
    // If batch fails (permission/network), fallback to per-company.
    const entries = await Promise.all(
      companyIds.map(async (id) => {
        try {
          const c = await fetchCompany(id);
          return [id, c.company_name || ''];
        } catch (_) {
          return [id, ''];
        }
      })
    );
    const map = {};
    for (const [id, name] of entries) {
      map[id] = name;
    }
    jobCompanyMap.value = map;
  }
}

function jobCompanyName(job) {
  if (!job?.company_id) return '';
  return jobCompanyMap.value[job.company_id] || '';
}

const sortedJobs = computed(() => {
  const rows = [...jobs.value];
  if (listSort.value === 'salary_desc') {
    return rows.sort((a, b) => Number(b.salary_max || 0) - Number(a.salary_max || 0));
  }
  if (listSort.value === 'salary_asc') {
    return rows.sort((a, b) => Number(a.salary_min || 0) - Number(b.salary_min || 0));
  }
  if (listSort.value === 'company') {
    return rows.sort((a, b) => {
      const companyA = jobCompanyName(a);
      const companyB = jobCompanyName(b);
      return String(companyA || '').localeCompare(String(companyB || ''), 'zh-CN');
    });
  }
  return rows.sort((a, b) => {
    const timeA = new Date(a.create_time || 0).getTime();
    const timeB = new Date(b.create_time || 0).getTime();
    return timeB - timeA;
  });
});

const totalJobPages = computed(() => Math.max(1, Math.ceil(sortedJobs.value.length / JOB_PAGE_SIZE)));

const pagedJobs = computed(() => {
  const page = Math.min(listPage.value, totalJobPages.value);
  const start = (page - 1) * JOB_PAGE_SIZE;
  return sortedJobs.value.slice(start, start + JOB_PAGE_SIZE);
});

const filteredCompanyApplications = computed(() => {
  const keyword = String(applicationKeyword.value || '').trim().toLowerCase();
  const status = applicationFilterStatus.value;
  return applications.value.filter((item) => {
    if (status && item.status !== status) return false;
    if (!keyword) return true;
    const target = [
      item.id,
      item.student_id,
      applicationJobName(item),
      applicationCompanyName(item)
    ]
      .map((value) => String(value || '').toLowerCase())
      .join(' ');
    return target.includes(keyword);
  });
});

const sortedCompanyApplications = computed(() => {
  const rows = [...filteredCompanyApplications.value];
  if (applicationSort.value === 'oldest') {
    return rows.sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
  }
  if (applicationSort.value === 'status') {
    const order = {
      submitted: 0,
      viewed: 1,
      reviewing: 2,
      to_contact: 3,
      interview_scheduled: 4,
      interviewing: 5,
      accepted: 6,
      rejected: 7
    };
    return rows.sort((a, b) => (order[a.status] ?? 99) - (order[b.status] ?? 99));
  }
  if (applicationSort.value === 'job') {
    return rows.sort((a, b) => {
      const jobA = applicationJobName(a);
      const jobB = applicationJobName(b);
      return String(jobA || '').localeCompare(String(jobB || ''), 'zh-CN');
    });
  }
  return rows.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
});

const totalCompanyApplicationPages = computed(() => Math.max(1, Math.ceil(sortedCompanyApplications.value.length / APPLICATION_PAGE_SIZE)));

const pagedCompanyApplications = computed(() => {
  const page = Math.min(applicationPage.value, totalCompanyApplicationPages.value);
  const start = (page - 1) * APPLICATION_PAGE_SIZE;
  return sortedCompanyApplications.value.slice(start, start + APPLICATION_PAGE_SIZE);
});

const allVisibleApplicationsSelected = computed(() => {
  if (!pagedCompanyApplications.value.length) return false;
  return pagedCompanyApplications.value.every((item) => selectedApplicationIds.value.includes(item.id));
});

function openJobDetail(job, event) {
  const target = event?.target;
  if (target && target.closest && target.closest('a,button,input,select,textarea,label')) {
    return;
  }
  router.push(`/jobs/${job.id}`);
}

async function loadApplications() {
  if (!auth.isAuthed.value || role.value !== 'company') return;
  try {
    applications.value = await fetchApplications();
    await loadApplicationMeta(applications.value);
    applicationStatusDraft.value = {};
    for (const item of applications.value) {
      applicationStatusDraft.value[item.id] = item.status;
    }
    applicationPage.value = 1;
    selectedApplicationIds.value = [];
    batchStatusDraft.value = '';
  } catch (err) {
    applications.value = [];
    applicationJobMap.value = {};
    applicationCompanyMap.value = {};
    selectedApplicationIds.value = [];
  }
}

async function loadApplicationMeta(items) {
  const jobIds = [...new Set((items || []).map((item) => item.job_id).filter(Boolean))];
  if (jobIds.length === 0) {
    applicationJobMap.value = {};
    applicationCompanyMap.value = {};
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

  const nextJobMap = {};
  const companyIds = [];
  for (const [jobId, job] of jobEntries) {
    if (job) {
      nextJobMap[jobId] = job;
      if (job.company_id) companyIds.push(job.company_id);
    }
  }
  applicationJobMap.value = nextJobMap;

  const uniqueCompanyIds = [...new Set(companyIds)];
  if (uniqueCompanyIds.length === 0) {
    applicationCompanyMap.value = {};
    return;
  }

  const companyEntries = await Promise.all(
    uniqueCompanyIds.map(async (companyId) => {
      try {
        const company = await fetchCompany(companyId);
        return [companyId, company];
      } catch (_) {
        return [companyId, null];
      }
    })
  );

  const nextCompanyMap = {};
  for (const [companyId, company] of companyEntries) {
    if (company) nextCompanyMap[companyId] = company;
  }
  applicationCompanyMap.value = nextCompanyMap;
}

function applicationJobName(item) {
  const job = applicationJobMap.value[item.job_id];
  return job?.job_name || `岗位 #${item.job_id}`;
}

function applicationCompanyName(item) {
  const job = applicationJobMap.value[item.job_id];
  if (!job?.company_id) return '';
  const company = applicationCompanyMap.value[job.company_id];
  return company?.company_name || '';
}

function formatTime(value) {
  if (!value) return '--';
  return String(value).replace('T', ' ').slice(0, 16);
}

function isApplicationSelected(applicationId) {
  return selectedApplicationIds.value.includes(applicationId);
}

function toggleApplicationSelection(applicationId, checked) {
  if (checked) {
    if (!selectedApplicationIds.value.includes(applicationId)) {
      selectedApplicationIds.value = [...selectedApplicationIds.value, applicationId];
    }
    return;
  }
  selectedApplicationIds.value = selectedApplicationIds.value.filter((id) => id !== applicationId);
}

function toggleSelectAllVisibleApplications(checked) {
  const visibleIds = pagedCompanyApplications.value.map((item) => item.id);
  if (checked) {
    const merged = new Set([...selectedApplicationIds.value, ...visibleIds]);
    selectedApplicationIds.value = [...merged];
    return;
  }
  selectedApplicationIds.value = selectedApplicationIds.value.filter((id) => !visibleIds.includes(id));
}

async function loadResumes() {
  if (role.value !== 'student') return;
  try {
    resumes.value = await fetchResumes(auth.user.value.id);
  } catch (err) {
    resumes.value = [];
  }
}

function clearFilter() {
  keyword.value = '';
  company.value = '';
  city.value = '';
  education.value = '';
  salaryMin.value = '';
  sort.value = '';
  loadJobs();
}

function onQuickCategoryClick(cat) {
  keyword.value = keyword.value === cat ? '' : cat;
  loadJobs();
}

function saveFilterPreset() {
  if (typeof window === 'undefined') return;
  try {
    const preset = {
      keyword: keyword.value,
      company: company.value,
      city: city.value,
      education: education.value,
      salaryMin: salaryMin.value,
      sort: sort.value
    };
    localStorage.setItem(FILTER_PRESET_KEY, JSON.stringify(preset));
    toast.success('筛选条件已保存');
  } catch (_) {
    toast.error('保存失败，请稍后重试');
  }
}

function restoreFilterPreset() {
  if (typeof window === 'undefined') return;
  try {
    const raw = localStorage.getItem(FILTER_PRESET_KEY);
    if (!raw) return;
    const preset = JSON.parse(raw);
    keyword.value = String(preset.keyword || '');
    company.value = String(preset.company || '');
    city.value = String(preset.city || '');
    education.value = String(preset.education || '');
    salaryMin.value = preset.salaryMin === null || preset.salaryMin === undefined ? '' : String(preset.salaryMin);
    sort.value = String(preset.sort || '');
  } catch (_) {
    // Ignore invalid local cache to avoid blocking page render.
  }
}

function resetJobForm() {
  editingJobId.value = null;
  jobForm.value = {
    company_id: auth.user.value?.id || 0,
    job_name: '',
    job_type: '',
    city: '',
    salary_min: 8000,
    salary_max: 12000,
    education: 'Bachelor',
    description: '',
    requirement: '',
    skill_tags: [],
    status: 'active',
    deadline: ''
  };
  skillsInput.value = '';
}

function startEdit(job) {
  editingJobId.value = job.id;
  jobForm.value = { ...job };
  skillsInput.value = (job.skill_tags || []).join(', ');
}

async function submitJob() {
  jobForm.value.skill_tags = skillsInput.value
    ? skillsInput.value.split(',').map((item) => item.trim()).filter(Boolean)
    : [];
  try {
    if (editingJobId.value) {
      await updateJob(editingJobId.value, jobForm.value);
    } else {
      await createJob({ ...jobForm.value, company_id: auth.user.value.id });
    }
    resetJobForm();
    await loadJobs();
  } catch (err) {
    const msg = err.message || '';
    if (msg.includes('not approved')) {
      toast.error('企业资质尚未通过审核，暂时无法发布岗位');
    } else {
      toast.error('岗位保存失败，请重试');
    }
  }
}

async function removeJob(id) {
  if (!confirm('确定要删除该岗位吗？')) return;
  try {
    await deleteJob(id);
    await loadJobs();
    await loadApplications();
  } catch (err) {
    toast.error('删除失败，请重试');
  }
}

async function applyJob(job) {
  if (resumes.value.length === 0) {
    toast.warn('请先在个人中心创建简历');
    router.push('/profile');
    return;
  }
  try {
    await createApplication({
      student_id: auth.user.value.id,
      job_id: job.id,
      resume_id: resumes.value[0].id,
      status: 'submitted'
    });
    toast.success('投递成功');
  } catch (err) {
    const msg = err.message || '';
    if (msg.includes('Already applied')) {
      toast.warn('您已投递过该岗位');
    } else {
      toast.error('投递失败，请稍后重试');
    }
  }
}

async function updateApplication(applicationId) {
  const status = applicationStatusDraft.value[applicationId];
  if (!status) return;
  try {
    await updateApplicationStatus(applicationId, { status });
    toast.success('状态已更新');
    await loadApplications();
  } catch (err) {
    toast.error('状态更新失败');
  }
}

async function applyBatchApplicationStatus() {
  const status = batchStatusDraft.value;
  if (!status) {
    toast.warn('请先选择批量更新状态');
    return;
  }
  if (!selectedApplicationIds.value.length) {
    toast.warn('请先选择需要批量更新的投递记录');
    return;
  }
  batchUpdating.value = true;
  try {
    await Promise.all(
      selectedApplicationIds.value.map((applicationId) => updateApplicationStatus(applicationId, { status }))
    );
    toast.success(`已批量更新 ${selectedApplicationIds.value.length} 条投递记录`);
    await loadApplications();
  } catch (err) {
    toast.error('批量更新失败，请稍后重试');
  } finally {
    batchUpdating.value = false;
  }
}

watch(listSort, () => {
  listPage.value = 1;
});

watch(totalJobPages, (total) => {
  if (listPage.value > total) listPage.value = total;
});

watch([applicationKeyword, applicationFilterStatus, applicationSort], () => {
  applicationPage.value = 1;
});

watch(totalCompanyApplicationPages, (total) => {
  if (applicationPage.value > total) applicationPage.value = total;
});

onMounted(async () => {
  restoreFilterPreset();
  await loadJobs();
  await loadApplications();
  await loadResumes();
  await loadFavorites();
});
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero {
  padding: 28px 0 10px;
}

.hero-panel {
  border-radius: 24px;
  border: 1px solid #d7ece1;
  background: linear-gradient(140deg, #f3faf6 0%, #f8fdf9 55%, #ffffff 100%);
  box-shadow: 0 14px 28px rgba(15, 122, 70, 0.08);
  padding: clamp(16px, 2.1vw, 24px);
}

.boss-layout {
  display: grid;
  grid-template-columns: minmax(180px, 260px) minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.boss-intro {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  padding: 4px 2px;
}

.boss-intro h1 {
  margin: 0;
  font-size: clamp(46px, 4.8vw, 58px);
  line-height: 1;
  letter-spacing: 0.5px;
  color: #10261f;
}

.boss-intro p {
  margin: 0;
  color: #5d766d;
  font-size: 15px;
  line-height: 1.5;
  max-width: 230px;
}

.boss-note {
  font-size: 13px;
  color: #7d938b;
}

.boss-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.boss-primary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-end;
}

.boss-field {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 54px;
  border: 1px solid #d7e9df;
  border-radius: 14px;
  background: #fff;
  padding: 8px 12px;
  flex: 1 1 140px;
}

.boss-field > span {
  color: #96a8a1;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.boss-field input,
.boss-field select {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  width: 100%;
  min-width: 64px;
  height: auto;
  font-size: 15px;
  line-height: 1.3;
  color: #1e3530;
  font-weight: 600;
}

.boss-field input::placeholder {
  color: #a5b4af;
  font-weight: 600;
}

.boss-field select {
  appearance: none;
  cursor: pointer;
}

.boss-field-keyword {
  min-width: 220px;
  flex: 1.4 1 240px;
}

.boss-field-mini {
  min-width: 160px;
  flex: 0.8 1 170px;
}

.boss-btn-primary,
.boss-btn-ghost {
  height: 52px;
  border-radius: 14px;
  padding: 0 18px;
  min-width: 104px;
  font-size: 16px;
  font-weight: 700;
}

.boss-btn-primary {
  background: linear-gradient(180deg, #45ac69 0%, #2f9758 100%);
  border: none;
  box-shadow: 0 12px 24px rgba(43, 146, 84, 0.28);
}

.boss-btn-primary:hover {
  transform: translateY(-1px);
}

.boss-btn-ghost {
  background: #fff;
  color: #20362f;
  border: 1px solid #d9e8e1;
}

.quick-tags {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}

.boss-tags {
  margin-top: 2px;
}

.chip {
  border: 1px solid #d9e8e2;
  background: #fff;
  border-radius: 999px;
  padding: 7px 13px;
  font-size: 13px;
  color: #4d645d;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip:hover {
  border-color: #bfded0;
  color: #2d4d42;
}

.chip.active {
  border-color: #b2dcc6;
  background: rgba(24, 160, 88, 0.12);
  color: #2d8f56;
  font-weight: 600;
}

.boss-secondary-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.boss-secondary-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.form-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.list-grid {
  grid-template-columns: 1fr;
}

.list-toolbar {
  margin-bottom: 12px;
  padding: 14px 16px;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #d8eee1;
  box-shadow: 0 10px 24px rgba(15, 122, 70, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.section-header.compact {
  margin-bottom: 10px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-actions select {
  height: 40px;
  border-radius: 10px;
  border: 1px solid var(--line);
  padding: 0 10px;
  background: #fff;
}

.application-toolbar {
  margin-bottom: 10px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.application-toolbar .toolbar-actions select {
  min-width: 150px;
}

.batch-toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border: 1px dashed #d2e7db;
  border-radius: 12px;
  background: #f7fbf9;
}

.batch-toolbar select {
  height: 38px;
  border-radius: 10px;
  border: 1px solid var(--line);
  padding: 0 10px;
  background: #fff;
}

.batch-check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #496558;
}

.job-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
  border: 1px solid #d8eee1;
}

.job-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(15, 31, 23, 0.12);
}

.job-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-desc {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
  line-height: 1.5;
}

.job-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  color: var(--muted);
  flex-wrap: wrap;
}

.job-meta .company-name {
  color: var(--accent-dark);
  font-weight: 600;
}

.job-meta .salary {
  color: #ff6b35;
  font-weight: 700;
  font-size: 15px;
}

.job-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.empty-state {
  text-align: center;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.application-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.application-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #d8eee1;
  border-radius: 12px;
  padding: 16px;
  gap: 16px;
  flex-wrap: wrap;
}

.app-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 240px;
  flex: 1;
}

.app-info-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-select {
  display: inline-flex;
  align-items: center;
}

.app-meta-line {
  margin: -2px 0 0;
}

.app-status-row {
  justify-content: flex-end;
}

.application-item select {
  height: 38px;
  border-radius: 10px;
  border: 1px solid var(--line);
  padding: 0 10px;
}

.job-link {
  color: inherit;
  text-decoration: none;
}
.job-link:hover {
  color: var(--accent);
}

@media (max-width: 1180px) {
  .boss-layout {
    grid-template-columns: 1fr;
  }

  .boss-intro p {
    max-width: none;
  }
}

@media (max-width: 860px) {
  .boss-primary-row {
    width: 100%;
  }

  .boss-field,
  .boss-field-keyword,
  .boss-field-mini {
    min-width: 100%;
    flex-basis: 100%;
  }

  .boss-btn-primary,
  .boss-btn-ghost {
    width: 100%;
    font-size: 15px;
  }

  .boss-secondary-actions {
    width: 100%;
    margin-left: 0;
  }

  .boss-secondary-actions .btn {
    flex: 1;
  }

  .list-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .application-toolbar {
    grid-template-columns: 1fr;
  }

  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions select {
    width: 100%;
  }

  .batch-toolbar {
    align-items: flex-start;
  }

  .job-card {
    grid-template-columns: 1fr;
  }

  .job-side {
    align-items: flex-start;
  }
}
</style>
