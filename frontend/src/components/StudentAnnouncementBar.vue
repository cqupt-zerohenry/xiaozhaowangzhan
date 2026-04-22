<template>
  <section v-if="visibleAnnouncements.length" class="announce-wrap">
    <div class="container announce-inner">
      <div class="announce-label">
        <span class="dot"></span>
        <strong>校园公告</strong>
      </div>
      <div class="announce-track">
        <div class="announce-marquee">
          <span
            v-for="(item, idx) in loopAnnouncements"
            :key="`${item.id}-${idx}`"
            class="announce-item"
            :title="`${item.title}：${item.content}`"
            role="button"
            tabindex="0"
            @click="openAnnouncement(item)"
            @keydown.enter.prevent="openAnnouncement(item)"
          >
            {{ item.title }}：{{ summary(item.content) }}
          </span>
        </div>
      </div>
    </div>
  </section>
  <div v-if="dialogVisible" class="announce-dialog-mask" @click.self="closeDialog">
    <div class="announce-dialog card">
      <div class="announce-dialog-head">
        <h3>{{ activeAnnouncement?.title || '校园公告' }}</h3>
        <button class="btn btn-outline" @click="closeDialog">关闭</button>
      </div>
      <p class="mono" v-if="activeAnnouncement?.create_time">发布时间：{{ formatTime(activeAnnouncement.create_time) }}</p>
      <p class="announce-dialog-content">{{ activeAnnouncement?.content || '暂无内容' }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { fetchPublishedAnnouncements } from '../services/api';

const announcements = ref([]);
const dialogVisible = ref(false);
const activeAnnouncement = ref(null);
let refreshTimer = null;

const visibleAnnouncements = computed(() => announcements.value.slice(0, 8));
const loopAnnouncements = computed(() => [...visibleAnnouncements.value, ...visibleAnnouncements.value]);

function summary(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text) return '暂无内容';
  if (text.length <= 32) return text;
  return `${text.slice(0, 32)}...`;
}

function formatTime(value) {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 16);
}

function openAnnouncement(item) {
  activeAnnouncement.value = item;
  dialogVisible.value = true;
}

function closeDialog() {
  dialogVisible.value = false;
}

async function loadAnnouncements() {
  try {
    const rows = await fetchPublishedAnnouncements();
    announcements.value = Array.isArray(rows) ? rows : [];
  } catch (_) {
    announcements.value = [];
  }
}

onMounted(() => {
  loadAnnouncements();
  refreshTimer = setInterval(loadAnnouncements, 60000);
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<style scoped>
.announce-wrap {
  border-bottom: 1px solid #d8ece0;
  background: linear-gradient(90deg, #f4fbf7 0%, #f8fcfa 100%);
}

.announce-inner {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.announce-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--accent-dark);
  font-size: 13px;
  white-space: nowrap;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 6px rgba(24, 160, 88, 0.18);
}

.announce-track {
  overflow: hidden;
  flex: 1;
}

.announce-marquee {
  display: inline-flex;
  align-items: center;
  gap: 28px;
  white-space: nowrap;
  min-width: max-content;
  animation: ticker-scroll 38s linear infinite;
}

.announce-track:hover .announce-marquee {
  animation-play-state: paused;
}

.announce-item {
  color: #355647;
  font-size: 13px;
  cursor: pointer;
}

.announce-item:hover {
  color: var(--accent-dark);
}

.announce-dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 20, 18, 0.42);
  display: grid;
  place-items: center;
  z-index: 80;
  padding: 18px;
}

.announce-dialog {
  width: min(680px, 100%);
  max-height: min(76vh, 720px);
  overflow: auto;
}

.announce-dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.announce-dialog-content {
  white-space: pre-wrap;
  line-height: 1.65;
  margin: 0;
}

@keyframes ticker-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

@media (max-width: 860px) {
  .announce-inner {
    height: 38px;
  }

  .announce-label strong {
    font-size: 12px;
  }

  .announce-item {
    font-size: 12px;
  }
}
</style>
