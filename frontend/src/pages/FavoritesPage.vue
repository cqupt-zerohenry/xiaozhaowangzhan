<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>我的收藏</h1>
          <p>收藏的岗位集中查看，快速投递。</p>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="loading" class="mono">加载中...</div>
        <div v-else-if="jobs.length === 0" class="card empty-state">
          <h3>暂无收藏岗位</h3>
          <p>去职位页浏览并收藏感兴趣的岗位吧。</p>
          <router-link to="/jobs" class="btn btn-outline">浏览职位</router-link>
        </div>
        <div v-else class="grid list-grid">
          <div class="card job-card" v-for="job in jobs" :key="job.id">
            <div class="job-main">
              <h3><router-link :to="`/jobs/${job.id}`" class="job-link">{{ job.job_name }}</router-link></h3>
              <div class="job-meta">
                <span>{{ job.city }}</span>
                <span class="salary">{{ job.salary_min }}K-{{ job.salary_max }}K</span>
                <span>{{ job.education }}</span>
              </div>
              <div class="tags">
                <span class="tag" v-for="skill in (job.skill_tags || []).slice(0, 5)" :key="skill">{{ skill }}</span>
              </div>
            </div>
            <div class="job-side">
              <button class="btn btn-outline" @click="unfav(job.id)">取消收藏</button>
              <router-link :to="`/jobs/${job.id}`" class="btn">查看详情</router-link>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import toast from '../utils/toast';
import { fetchFavorites, fetchJob, removeFavorite } from '../services/api';

const jobs = ref([]);
const loading = ref(true);

async function loadFavJobs() {
  loading.value = true;
  try {
    const favs = await fetchFavorites();
    const results = [];
    for (const fav of favs) {
      try {
        const job = await fetchJob(fav.job_id);
        results.push(job);
      } catch (e) { /* job may have been deleted */ }
    }
    jobs.value = results;
  } catch (e) {
    jobs.value = [];
  } finally {
    loading.value = false;
  }
}

async function unfav(jobId) {
  try {
    await removeFavorite(jobId);
    jobs.value = jobs.value.filter(j => j.id !== jobId);
    toast.success('已取消收藏');
  } catch (e) {
    toast.error('操作失败');
  }
}

onMounted(loadFavJobs);
</script>

<style scoped>
.page-wrap { display: flex; flex-direction: column; gap: 24px; }
.page-hero { padding: 32px 0 16px; }
.hero-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.list-grid { grid-template-columns: 1fr; }
.job-card { display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: center; transition: transform 0.2s ease; }
.job-card:hover { transform: translateY(-2px); }
.job-main { display: flex; flex-direction: column; gap: 8px; }
.job-meta { display: flex; gap: 12px; font-size: 13px; color: var(--muted); }
.job-side { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.job-link { color: inherit; text-decoration: none; }
.job-link:hover { color: var(--accent); }
.empty-state { text-align: center; padding: 48px 24px; gap: 16px; }

@media (max-width: 860px) {
  .job-card { grid-template-columns: 1fr; }
  .job-side { align-items: flex-start; }
}
</style>
