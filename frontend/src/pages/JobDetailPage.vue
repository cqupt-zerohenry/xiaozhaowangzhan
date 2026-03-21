<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
        <div>
          <h1>{{ job.job_name || '岗位详情' }}</h1>
          <p class="mono hero-meta">
            {{ company?.company_name || '企业信息加载中...' }}
            · {{ job.city || '城市待定' }}
            · {{ job.education || '学历不限' }}
            · {{ salaryText }}
          </p>
        </div>
        <div class="hero-actions">
          <button v-if="role === 'student'" class="btn" :class="{ 'btn-outline': isFavorited }" @click="toggleFavorite">
            {{ isFavorited ? '已收藏' : '收藏' }}
          </button>
          <button class="btn btn-outline" @click="$router.back()">返回</button>
        </div>
        </div>
      </div>
    </section>

    <section v-if="!job.id" class="empty-wrap">
      <div class="container">
        <div class="card empty-card">
        <h3>岗位未找到</h3>
        <p>该岗位可能已下架或不存在。</p>
        <button class="btn btn-outline" @click="$router.push('/jobs')">浏览其他岗位</button>
        </div>
      </div>
    </section>

    <section v-else>
      <div class="container grid detail-grid">
        <div class="card">
          <h3>岗位信息</h3>
          <div class="info-row">
            <span class="label">岗位类型</span>
            <span>{{ job.job_type }}</span>
          </div>
          <div class="info-row">
            <span class="label">工作城市</span>
            <span>{{ job.city }}</span>
          </div>
          <div class="info-row">
            <span class="label">薪资范围</span>
            <span class="salary">{{ salaryText }}</span>
          </div>
          <div class="info-row">
            <span class="label">学历要求</span>
            <span>{{ job.education }}</span>
          </div>
          <div class="info-row">
            <span class="label">截止日期</span>
            <span>{{ job.deadline || '长期有效' }}</span>
          </div>
          <div class="info-row">
            <span class="label">发布时间</span>
            <span class="mono">{{ formatTime(job.create_time) }}</span>
          </div>
          <div class="divider"></div>
          <h3>技能要求</h3>
          <div class="tags">
            <span class="tag" v-for="skill in job.skill_tags" :key="skill">{{ skill }}</span>
            <span v-if="!job.skill_tags?.length" class="mono">暂无</span>
          </div>
          <div class="divider"></div>
          <h3>岗位职责</h3>
          <p class="desc-text">{{ job.description || '暂无' }}</p>
          <div class="divider"></div>
          <h3>任职要求</h3>
          <p class="desc-text">{{ job.requirement || '暂无' }}</p>
        </div>

        <div class="side-col">
          <div v-if="role === 'student'" class="card apply-card">
            <h3>投递操作</h3>
            <div class="apply-meta">
              <span class="mono">当前简历数：{{ resumes.length }}</span>
              <span class="mono">投递状态：{{ applicationStatusText }}</span>
            </div>
            <div v-if="resumes.length > 0" class="apply-form">
              <label class="mono">选择投递简历</label>
              <select v-model.number="selectedResumeId">
                <option v-for="resume in resumes" :key="resume.id" :value="resume.id">
                  版本 {{ resume.version_no }} · {{ resume.resume_type }}
                </option>
              </select>
            </div>
            <button
              class="btn"
              :disabled="!canApplyNow || applying"
              @click="applyJob"
            >
              {{ applyButtonText }}
            </button>
            <p class="mono apply-hint">{{ applyHintText }}</p>
          </div>

          <div class="card">
            <h3>企业信息</h3>
            <div v-if="company">
              <h4>{{ company.company_name }}</h4>
              <p>{{ company.description || '暂无简介' }}</p>
              <div class="info-row" v-if="company.industry">
                <span class="label">行业</span>
                <span>{{ company.industry }}</span>
              </div>
              <div class="info-row" v-if="company.scale">
                <span class="label">规模</span>
                <span>{{ company.scale }}</span>
              </div>
              <div class="info-row" v-if="company.address">
                <span class="label">地址</span>
                <span>{{ company.address }}</span>
              </div>
              <div class="tags" v-if="company.welfare_tags?.length">
                <span class="tag" v-for="tag in company.welfare_tags" :key="tag">{{ tag }}</span>
              </div>
            </div>
            <div v-else class="mono">暂无企业信息</div>
          </div>

          <div class="card" v-if="similarJobs.length > 0">
            <h3>相似岗位</h3>
            <div class="similar-list">
              <router-link v-for="item in similarJobs" :key="item.job_id" :to="`/jobs/${item.job_id}`" class="similar-item">
                <div>
                  <strong>{{ item.job_name }}</strong>
                  <p class="mono">相似度 {{ item.similarity_score }}%</p>
                </div>
                <div class="tags">
                  <span class="tag" v-for="s in item.common_skills" :key="s">{{ s }}</span>
                </div>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  addFavorite,
  createApplication,
  fetchApplications,
  fetchCompany,
  fetchFavorites,
  fetchJob,
  fetchResumes,
  fetchSimilarJobs,
  removeFavorite
} from '../services/api';
import { useAuth } from '../store/auth';

import toast from '../utils/toast';
const route = useRoute();
const router = useRouter();
const auth = useAuth();
const role = computed(() => auth.role.value);

const job = ref({});
const company = ref(null);
const similarJobs = ref([]);
const favorites = ref([]);
const resumes = ref([]);
const selectedResumeId = ref(null);
const applying = ref(false);
const currentApplication = ref(null);

const isFavorited = computed(() => favorites.value.some(f => f.job_id === job.value.id));
const salaryText = computed(() => {
  const min = Number(job.value?.salary_min || 0);
  const max = Number(job.value?.salary_max || 0);
  if (min && max) return `${min}K-${max}K / 月`;
  return '面议';
});
const hasApplied = computed(() => Boolean(currentApplication.value));
const canApplyNow = computed(() => role.value === 'student' && !hasApplied.value && resumes.value.length > 0 && Number(selectedResumeId.value) > 0);
const applyButtonText = computed(() => {
  if (applying.value) return '投递中...';
  if (hasApplied.value) return '已投递';
  return '立即投递';
});
const applicationStatusText = computed(() => {
  if (!currentApplication.value?.status) return '未投递';
  return statusLabel(currentApplication.value.status);
});
const applyHintText = computed(() => {
  if (hasApplied.value) return '你已投递该岗位，可在“我的投递记录”跟踪流程。';
  if (resumes.value.length === 0) return '请先在学生档案中创建简历，再投递该岗位。';
  return '选择一个简历版本后即可投递。';
});

async function loadJob() {
  const id = route.params.id;
  if (!id) return;
  try {
    job.value = await fetchJob(id);
    if (job.value.company_id) {
      try {
        company.value = await fetchCompany(job.value.company_id);
      } catch (_) {
        company.value = null;
      }
    }
    try {
      similarJobs.value = await fetchSimilarJobs(id);
    } catch (_) {
      similarJobs.value = [];
    }
    await loadCurrentApplication();
  } catch (e) {
    job.value = {};
    currentApplication.value = null;
  }
}

async function loadCurrentApplication() {
  if (role.value !== 'student' || !job.value.id) {
    currentApplication.value = null;
    return;
  }
  try {
    const list = await fetchApplications({ job_id: job.value.id });
    currentApplication.value = Array.isArray(list) && list.length ? list[0] : null;
  } catch (_) {
    currentApplication.value = null;
  }
}

async function loadFavorites() {
  if (role.value !== 'student') return;
  try {
    favorites.value = await fetchFavorites();
  } catch (e) {
    favorites.value = [];
  }
}

async function loadResumes() {
  if (role.value !== 'student') return;
  try {
    resumes.value = await fetchResumes(auth.user.value.id);
    if (resumes.value.length > 0) {
      selectedResumeId.value = Number(resumes.value[0].id);
    } else {
      selectedResumeId.value = null;
    }
  } catch (e) {
    resumes.value = [];
    selectedResumeId.value = null;
  }
}

async function toggleFavorite() {
  if (!job.value.id) return;
  try {
    if (isFavorited.value) {
      await removeFavorite(job.value.id);
    } else {
      await addFavorite(job.value.id);
    }
    await loadFavorites();
  } catch (e) {
    toast.error('操作失败，请重试');
  }
}

async function applyJob() {
  if (!canApplyNow.value) {
    if (hasApplied.value) {
      toast.info('该岗位已投递，请到我的投递记录查看进度');
      return;
    }
    toast.warn('请先在个人中心创建简历');
    if (resumes.value.length === 0) {
      router.push('/profile');
    }
    return;
  }
  applying.value = true;
  try {
    await createApplication({
      student_id: auth.user.value.id,
      job_id: job.value.id,
      resume_id: Number(selectedResumeId.value),
      status: 'submitted'
    });
    toast.success('投递成功');
    await loadCurrentApplication();
  } catch (e) {
    toast.error('投递失败，可能已投递过');
    await loadCurrentApplication();
  } finally {
    applying.value = false;
  }
}

function statusLabel(status) {
  const map = {
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
  return map[status] || status;
}

function formatTime(value) {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 16);
}

watch(() => route.params.id, () => {
  loadJob();
  loadFavorites();
  loadResumes();
});

onMounted(() => {
  loadJob();
  loadFavorites();
  loadResumes();
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

.empty-wrap {
  padding: 40px 0;
}

.empty-card {
  max-width: 420px;
  margin: 0 auto;
  text-align: center;
  gap: 12px;
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
  gap: 8px;
  flex-wrap: wrap;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-grid {
  grid-template-columns: 1.2fr 0.8fr;
}

.side-col {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.apply-card {
  border: 1px solid #cae7d8;
  background: linear-gradient(170deg, #f8fcfa 0%, #f1faf5 100%);
}

.apply-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.apply-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.apply-form select {
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0 10px;
  background: #fff;
}

.apply-hint {
  margin: 0;
  color: #5d746a;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed var(--line);
}

.info-row .label {
  color: var(--muted);
  font-size: 13px;
  min-width: 80px;
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 8px 0;
}

.desc-text {
  white-space: pre-wrap;
  line-height: 1.8;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.similar-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  gap: 12px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.similar-item:hover {
  border-color: var(--accent);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

h4 {
  margin: 0 0 8px;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
