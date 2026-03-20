<template>
  <div class="container" style="padding-top: 32px;">
    <h2>浏览记录</h2>
    <div v-if="!history.length" class="card" style="text-align: center; padding: 48px; color: #6b7c78;">暂无浏览记录</div>
    <div v-for="item in history" :key="item.id" class="card" style="margin-bottom: 8px; padding: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <router-link :to="`/jobs/${item.job_id}`" style="font-weight: 600; color: #0f1f17; text-decoration: none;">{{ item.job_name }}</router-link>
        <span v-if="item.company_name" style="color: #6b7c78; margin-left: 8px;">{{ item.company_name }}</span>
      </div>
      <span class="mono" style="font-size: 12px; color: #aaa;">{{ formatTime(item.create_time) }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchViewHistory } from '../services/api.js'
import { useAuth } from '../store/auth.js'
import { toast } from '../utils/toast.js'

const { user } = useAuth()
const history = ref([])

function formatTime(v) { return v ? String(v).replace('T', ' ').slice(0, 16) : '' }

onMounted(async () => {
  try {
    history.value = await fetchViewHistory(user.value.id)
  } catch (e) { toast.error('加载浏览记录失败') }
})
</script>
