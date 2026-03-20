<template>
  <div class="container" style="padding-top: 32px;">
    <h2>通知中心</h2>
    <div style="display: flex; gap: 8px; margin-bottom: 16px;">
      <button v-for="t in types" :key="t.value" class="btn" :class="{ 'btn-outline': filterType !== t.value }" @click="filterType = t.value; load()">{{ t.label }}</button>
      <button class="btn btn-outline" @click="readAll" style="margin-left: auto;">全部标记已读</button>
    </div>
    <div v-if="!notifications.length" class="card" style="text-align: center; padding: 48px; color: #6b7c78;">暂无通知</div>
    <div v-for="n in notifications" :key="n.id" class="card" :style="{ borderLeft: n.is_read ? '' : '3px solid #18a058', marginBottom: '8px', padding: '16px' }">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <strong>{{ n.title }}</strong>
          <span class="tag" style="margin-left: 8px;">{{ n.notification_type }}</span>
        </div>
        <span class="mono" style="font-size: 12px; color: #aaa;">{{ formatTime(n.create_time) }}</span>
      </div>
      <p style="margin: 8px 0 0; color: #333;">{{ n.content }}</p>
      <button v-if="!n.is_read" class="btn btn-outline" style="margin-top: 8px; font-size: 12px; padding: 4px 12px;" @click="markRead(n)">标记已读</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../services/api.js'
import { toast } from '../utils/toast.js'

const notifications = ref([])
const filterType = ref('')
const types = [
  { label: '全部', value: '' },
  { label: '投递', value: 'application' },
  { label: '面试', value: 'interview' },
  { label: '系统', value: 'system' },
  { label: '公告', value: 'announcement' },
]

function formatTime(v) { return v ? String(v).replace('T', ' ').slice(0, 16) : '' }

async function load() {
  try {
    const params = filterType.value ? { notification_type: filterType.value } : {}
    notifications.value = await fetchNotifications(params)
  } catch (e) { toast.error('加载通知失败') }
}

async function markRead(n) {
  try {
    await markNotificationRead(n.id)
    n.is_read = true
  } catch (e) { /* */ }
}

async function readAll() {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => n.is_read = true)
    toast.success('已全部标记为已读')
  } catch (e) { /* */ }
}

onMounted(load)
</script>
