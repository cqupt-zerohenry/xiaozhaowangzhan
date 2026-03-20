<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>{{ job.job_name || '岗位详情' }}</h1>
          <p class="mono">{{ job.city }} · {{ job.education }} · {{ job.salary_min }}-{{ job.salary_max }} 元/月</p>
        </div>
        <div class="hero-actions">
          <button v-if="role === 'student'" class="btn" :class="{ 'btn-outline': isFavorited }" @click="toggleFavorite">
            {{ isFavorited ? '已收藏' : '收藏' }}
          </button>
          <button v-if="role === 'student'" class="btn" @click="applyJob">立即投递</button>
          <button class="btn btn-outline" @click="$router.back()">返回</button>
        </div>
      </div>
    </section>

    <section>
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
            <span>{{ job.salary_min }} - {{ job.salary_max }} 元/月</span>
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
            <div v-else class="mono">加载中...</div>
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

const isFavorited = computed(() => favorites.value.some(f => f.job_id === job.value.id));

async function loadJob() {
  const id = route.params.id;
  if (!id) return;
  try {
    job.value = await fetchJob(id);
    if (job.value.company_id) {
      company.value = await fetchCompany(job.value.company_id);
    }
    similarJobs.value = await fetchSimilarJobs(id);
  } catch (e) {
    job.value = {};
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
  } catch (e) {
    resumes.value = [];
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
  } catch (e) {}
}

async function applyJob() {
  if (resumes.value.length === 0) {
    toast.warn('请先在个人中心创建简历');
    return;
  }
  try {
    await createApplication({
      student_id: auth.user.value.id,
      job_id: job.value.id,
      resume_id: resumes.value[0].id,
      status: 'submitted'
    });
    toast.success('投递成功');
  } catch (e) {
    toast.error('投递失败，可能已投递过');
  }
}

function formatTime(value) {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 16);
}

watch(() => route.params.id, () => {
  loadJob();
  loadFavorites();
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

.detail-grid {
  grid-template-columns: 1.2fr 0.8fr;
}

.side-col {
  display: flex;
  flex-direction: column;
  gap: 24px;
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
