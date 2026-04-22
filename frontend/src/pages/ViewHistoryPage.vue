<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>浏览记录</h1>
            <p>查看你最近浏览过的岗位。</p>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="!history.length" class="card empty-state">暂无浏览记录</div>
        <div v-else class="history-grid">
          <article v-for="item in history" :key="item.id" class="card history-item">
            <div class="history-top">
              <span class="history-mark">最近浏览</span>
              <span class="mono time">{{ formatTime(item.create_time) }}</span>
            </div>
            <router-link :to="`/jobs/${item.job_id}`" class="job-link">{{ item.job_name }}</router-link>
            <div class="history-meta">
              <router-link v-if="item.company_name" :to="`/jobs/${item.job_id}`" class="company-link">
                {{ item.company_name }}
              </router-link>
              <span v-else class="company-name">未知企业</span>
              <router-link :to="`/jobs/${item.job_id}`" class="btn btn-outline btn-sm">查看职位</router-link>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchViewHistory } from '../services/api.js'
import { useAuth } from '../store/auth.js'
import toast from '../utils/toast.js'

const { user } = useAuth()
const history = ref([])

function formatTime(v) {
  return v ? String(v).replace('T', ' ').slice(0, 16) : ''
}

onMounted(async () => {
  try {
    history.value = await fetchViewHistory(user.value.id)
  } catch (e) {
    toast.error('加载浏览记录失败')
  }
})
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

.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.history-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.history-item {
  border: 1px solid #d8eee1;
  background: linear-gradient(140deg, #ffffff 0%, #f7fcf9 100%);
  box-shadow: 0 10px 20px rgba(15, 122, 70, 0.08);
}

.history-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.history-mark {
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 600;
}

.history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.job-link {
  font-weight: 600;
  color: var(--ink);
  font-size: 18px;
}

.job-link:hover {
  color: var(--accent);
}

.company-link,
.company-name {
  color: var(--muted);
}

.time {
  color: #8a9a95;
}

@media (max-width: 760px) {
  .history-meta {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
