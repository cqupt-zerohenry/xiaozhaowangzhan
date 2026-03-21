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
        <div v-else class="history-list">
          <article v-for="item in history" :key="item.id" class="card history-item">
            <div class="left">
              <router-link :to="`/jobs/${item.job_id}`" class="job-link">{{ item.job_name }}</router-link>
              <span v-if="item.company_name" class="company-name">{{ item.company_name }}</span>
            </div>
            <span class="mono time">{{ formatTime(item.create_time) }}</span>
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border: 1px solid #d8eee1;
}

.left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.job-link {
  font-weight: 600;
  color: var(--ink);
}

.job-link:hover {
  color: var(--accent);
}

.company-name {
  color: var(--muted);
}

.time {
  color: #8a9a95;
}

@media (max-width: 760px) {
  .history-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
