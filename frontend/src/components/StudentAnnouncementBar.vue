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
          >
            {{ item.title }}：{{ summary(item.content) }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { fetchPublishedAnnouncements } from '../services/api';

const announcements = ref([]);
let refreshTimer = null;

const visibleAnnouncements = computed(() => announcements.value.slice(0, 8));
const loopAnnouncements = computed(() => [...visibleAnnouncements.value, ...visibleAnnouncements.value]);

function summary(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text) return '暂无内容';
  if (text.length <= 32) return text;
  return `${text.slice(0, 32)}...`;
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
