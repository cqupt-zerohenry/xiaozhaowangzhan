<template>
  <div class="notification-bell" @click="toggleDropdown">
    <span class="bell-icon">&#128276;</span>
    <span v-if="unreadCount > 0" class="bell-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    <div v-if="showDropdown" class="bell-dropdown" @click.stop>
      <div class="bell-header">
        <strong>通知</strong>
        <button v-if="notifications.length" class="btn-link" @click="readAll">全部已读</button>
      </div>
      <div v-if="!notifications.length" class="bell-empty">暂无通知</div>
      <div v-for="n in notifications.slice(0, 8)" :key="n.id" class="bell-item" :class="{ unread: !n.is_read }" @click="onClickNotification(n)">
        <div class="bell-item-title">{{ n.title }}</div>
        <div class="bell-item-content">{{ n.content.slice(0, 60) }}</div>
        <div class="bell-item-time mono">{{ formatTime(n.create_time) }}</div>
      </div>
      <router-link to="/notifications" class="bell-footer" @click="showDropdown = false">查看全部</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchNotifications, fetchNotificationUnreadCount, markNotificationRead, markAllNotificationsRead } from '../services/api.js'

const unreadCount = ref(0)
const notifications = ref([])
const showDropdown = ref(false)
let timer = null

function formatTime(v) {
  return v ? String(v).replace('T', ' ').slice(0, 16) : ''
}

async function loadData() {
  try {
    const res = await fetchNotificationUnreadCount()
    unreadCount.value = res.count || 0
    const list = await fetchNotifications({ limit: 8 })
    notifications.value = list || []
  } catch (e) { /* ignore */ }
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value) loadData()
}

async function onClickNotification(n) {
  if (!n.is_read) {
    try { await markNotificationRead(n.id) } catch (e) { /* */ }
    n.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
}

async function readAll() {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (e) { /* */ }
}

onMounted(() => {
  loadData()
  timer = setInterval(loadData, 15000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// Close dropdown on outside click
function onDocClick(e) {
  if (!e.target.closest('.notification-bell')) showDropdown.value = false
}
onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

<style scoped>
.notification-bell { position: relative; cursor: pointer; display: inline-flex; align-items: center; margin-right: 8px; }
.bell-icon { font-size: 20px; }
.bell-badge { position: absolute; top: -6px; right: -10px; background: #e53e3e; color: #fff; font-size: 11px; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 4px; }
.bell-dropdown { position: absolute; top: 32px; right: -20px; width: 320px; background: #fff; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,.12); z-index: 1000; overflow: hidden; }
.bell-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #e1ebe6; }
.btn-link { background: none; border: none; color: #18a058; cursor: pointer; font-size: 13px; }
.bell-empty { padding: 24px; text-align: center; color: #6b7c78; }
.bell-item { padding: 10px 16px; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
.bell-item:hover { background: #f6f8f7; }
.bell-item.unread { background: #f0faf5; }
.bell-item-title { font-weight: 600; font-size: 13px; margin-bottom: 2px; }
.bell-item-content { font-size: 12px; color: #6b7c78; }
.bell-item-time { font-size: 11px; color: #aaa; margin-top: 2px; }
.bell-footer { display: block; text-align: center; padding: 10px; color: #18a058; text-decoration: none; font-size: 13px; border-top: 1px solid #e1ebe6; }
.bell-footer:hover { background: #f6f8f7; }
</style>
