<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>通知中心</h1>
            <p>集中查看系统、投递和面试通知。</p>
          </div>
          <button class="btn btn-outline" :disabled="loading" @click="readAll">全部标记已读</button>
        </div>
        <div class="filter-row">
          <button
            v-for="t in types"
            :key="t.value"
            class="chip"
            :class="{ active: filterType === t.value }"
            :disabled="loading"
            @click="applyFilter(t.value)"
          >
            {{ t.label }}
          </button>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="loading" class="card empty-state">加载中...</div>
        <div v-else-if="!notifications.length" class="card empty-state">暂无通知</div>
        <div v-else class="notification-list">
          <article
            v-for="n in displayNotifications"
            :key="n.id"
            class="card notification-card"
            :class="{ unread: !n.is_read }"
          >
            <div class="notification-head">
              <div class="title-row">
                <strong>{{ n.title }}</strong>
                <span class="tag">{{ n.notification_type }}</span>
              </div>
              <span class="mono time">{{ formatTime(n.create_time) }}</span>
            </div>
            <p class="content">{{ n.content }}</p>
            <div class="actions">
              <button class="btn btn-outline btn-sm" @click="openDetail(n)">查看详情</button>
              <button v-if="!n.is_read" class="btn btn-outline btn-sm" @click="markRead(n)">标记已读</button>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../services/api.js'
import { useAuth } from '../store/auth.js'
import { compareNotifications, resolveNotificationTarget } from '../utils/notificationRoute.js'
import toast from '../utils/toast.js'

const notifications = ref([])
const filterType = ref('')
const loading = ref(false)
const route = useRoute()
const router = useRouter()
const auth = useAuth()
const types = [
  { label: '全部', value: '' },
  { label: '投递', value: 'application' },
  { label: '面试', value: 'interview' },
  { label: '系统', value: 'system' },
  { label: '公告', value: 'announcement' },
]

const displayNotifications = computed(() => {
  return [...notifications.value].sort(compareNotifications)
})

function formatTime(v) {
  return v ? String(v).replace('T', ' ').slice(0, 16) : ''
}

async function load() {
  loading.value = true
  try {
    const params = filterType.value ? { notification_type: filterType.value } : {}
    notifications.value = await fetchNotifications(params)
  } catch (e) {
    toast.error('加载通知失败')
  } finally {
    loading.value = false
  }
}

function applyFilter(value) {
  filterType.value = value;
  router.replace({
    query: {
      ...route.query,
      type: value || undefined
    }
  });
  load();
}

async function markRead(n, options = { silent: false }) {
  const { silent = false } = options;
  try {
    await markNotificationRead(n.id)
    n.is_read = true
    if (!silent) toast.success('已标记为已读')
  } catch (e) {
    if (!silent) toast.error('标记失败')
    throw e
  }
}

async function openDetail(n) {
  if (!n.is_read) {
    await markRead(n, { silent: true })
  }
  const target = resolveNotificationTarget(n, auth.role.value)
  router.push({
    path: target.path,
    query: target.query || {}
  })
}

async function readAll() {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach((n) => {
      n.is_read = true
    })
    toast.success('已全部标记为已读')
  } catch (e) {
    toast.error('批量标记失败')
  }
}

onMounted(() => {
  const type = typeof route.query.type === 'string' ? route.query.type : ''
  if (types.some((item) => item.value === type)) {
    filterType.value = type
  }
  load()
})

watch(
  () => route.query.type,
  (value) => {
    const next = typeof value === 'string' ? value : ''
    if (!types.some((item) => item.value === next)) return
    if (filterType.value === next) return
    filterType.value = next
    load()
  }
)
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

.filter-row {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}

.chip.active {
  border-color: var(--accent);
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
  font-weight: 600;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-card {
  border: 1px solid #d8eee1;
}

.notification-card.unread {
  border-left: 4px solid var(--accent);
}

.notification-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time {
  color: #8a9a95;
}

.content {
  margin: 0;
  color: #30443d;
}

.btn-sm {
  font-size: 12px;
  padding: 6px 12px;
}

@media (max-width: 760px) {
  .notification-head {
    flex-direction: column;
  }
}
</style>
