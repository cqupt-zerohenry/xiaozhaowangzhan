<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container">
        <div class="hero-row">
          <div>
            <h1>{{ title }}</h1>
            <p>{{ subtitle }}</p>
          </div>
          <div class="search-bar">
            <input v-model="keyword" placeholder="岗位名称或关键词" />
            <button class="btn" @click="loadJobs">搜索</button>
          </div>
        </div>
        <div class="filters">
          <input v-model="company" placeholder="公司名称" />
          <input v-model="city" placeholder="城市" />
          <input v-model="education" placeholder="学历要求" />
          <input v-model.number="salaryMin" type="number" placeholder="最低薪资" />
          <select v-model="sort">
            <option value="">默认排序</option>
            <option value="latest">最新发布</option>
          </select>
          <button class="btn btn-outline" @click="clearFilter">清空</button>
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
        <div v-else class="grid list-grid">
          <div class="card job-card" v-for="job in jobs" :key="job.id">
            <div class="job-main">
              <div>
                <h3><router-link :to="`/jobs/${job.id}`" class="job-link">{{ job.job_name }}</router-link></h3>
                <p>{{ job.description }}</p>
              </div>
              <div class="job-meta mono">
                {{ job.city }} · {{ job.salary_min }}-{{ job.salary_max }} · {{ job.education }}
              </div>
            </div>
            <div class="job-side">
              <div class="tags">
                <span class="tag" v-for="skill in job.skill_tags" :key="skill">{{ skill }}</span>
              </div>
              <div class="actions" v-if="role === 'company'">
                <button class="btn btn-outline" @click="startEdit(job)">编辑</button>
                <button class="btn btn-outline" @click="removeJob(job.id)">删除</button>
              </div>
              <button v-else-if="role === 'student'" class="btn btn-outline" @click.stop="toggleFavorite(job.id)">
                {{ isFavorited(job.id) ? '已收藏' : '收藏' }}
              </button>
              <button v-if="role === 'student'" class="btn btn-outline" @click="applyJob(job)">
                立即投递
              </button>
              <button v-else class="btn btn-outline">查看详情</button>
            </div>
          </div>
          <div v-if="jobs.length === 0" class="empty-state card">
            <h3>暂无匹配岗位</h3>
            <p>尝试调整筛选条件。</p>
          </div>
        </div>
      </div>
    </section>

    <section v-if="applications.length > 0">
      <div class="container">
        <div class="card">
          <h3>{{ role === 'student' ? '我的投递记录' : '岗位投递记录' }}</h3>
          <div class="application-list">
            <div class="application-item" v-for="item in applications" :key="item.id">
              <div>
                <strong>#{{ item.id }} - 岗位 {{ item.job_id }}</strong>
                <p class="mono">学生 {{ item.student_id }} · 简历 {{ item.resume_id }}</p>
              </div>
              <div class="actions">
                <span class="tag mono">{{ item.status }}</span>
                <template v-if="role === 'company'">
                  <select v-model="applicationStatusDraft[item.id]">
                    <option value="submitted">已投递</option>
                    <option value="reviewing">筛选中</option>
                    <option value="to_contact">待沟通</option>
                    <option value="accepted">已通过</option>
                    <option value="rejected">已淘汰</option>
                  </select>
                  <button class="btn btn-outline" @click="updateApplication(item.id)">更新</button>
                </template>
                <button
                  v-else-if="role === 'student' && item.status === 'submitted'"
                  class="btn btn-outline"
                  @click="withdrawApplication(item.id)"
                >
                  撤回
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import {
  addFavorite,
  createApplication,
  createJob,
  deleteJob,
  fetchApplications,
  fetchFavorites,
  fetchJobs,
  fetchResumes,
  removeFavorite,
  updateApplicationStatus,
  updateJob
} from '../services/api';
import { useAuth } from '../store/auth';

const jobs = ref([]);
const loadingJobs = ref(false);
const applications = ref([]);
const resumes = ref([]);
const applicationStatusDraft = ref({});
const favorites = ref([]);

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
  } catch (e) {}
}

const keyword = ref('');
const company = ref('');
const city = ref('');
const education = ref('');
const salaryMin = ref('');
const sort = ref('');

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
    jobs.value = await fetchJobs({
      keyword: keyword.value,
      company: company.value,
      city: city.value,
      education: education.value,
      salary_min: salaryMin.value,
      sort: sort.value
    });
  } catch (err) {
    jobs.value = [];
  } finally {
    loadingJobs.value = false;
  }
}

async function loadApplications() {
  if (!auth.isAuthed.value) return;
  try {
    applications.value = await fetchApplications();
    applicationStatusDraft.value = {};
    for (const item of applications.value) {
      applicationStatusDraft.value[item.id] = item.status;
    }
  } catch (err) {
    applications.value = [];
  }
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
    // ignore
  }
}

async function removeJob(id) {
  try {
    await deleteJob(id);
    await loadJobs();
    await loadApplications();
  } catch (err) {
    // ignore
  }
}

async function applyJob(job) {
  if (resumes.value.length === 0) {
    alert('请先在个人中心创建简历');
    return;
  }
  try {
    await createApplication({
      student_id: auth.user.value.id,
      job_id: job.id,
      resume_id: resumes.value[0].id,
      status: 'submitted'
    });
    await loadApplications();
  } catch (err) {
    // ignore
  }
}

async function updateApplication(applicationId) {
  const status = applicationStatusDraft.value[applicationId];
  if (!status) return;
  try {
    await updateApplicationStatus(applicationId, { status });
    await loadApplications();
  } catch (err) {
    // ignore
  }
}

async function withdrawApplication(applicationId) {
  try {
    await updateApplicationStatus(applicationId, { status: 'withdrawn' });
    await loadApplications();
  } catch (err) {
    // ignore
  }
}

onMounted(async () => {
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
  padding: 32px 0 16px;
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.search-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.search-bar input {
  min-width: 260px;
  height: 44px;
}

.filters {
  margin-top: 16px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  align-items: center;
}

.filters select {
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--line);
  padding: 0 12px;
}

.form-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.list-grid {
  grid-template-columns: 1fr;
}

.job-card {
  display: grid;
  grid-template-columns: 1.4fr 0.6fr;
  gap: 16px;
  align-items: center;
}

.job-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-meta {
  color: var(--muted);
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

.application-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.application-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  gap: 12px;
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

@media (max-width: 860px) {
  .job-card {
    grid-template-columns: 1fr;
  }

  .job-side {
    align-items: flex-start;
  }
}
</style>
