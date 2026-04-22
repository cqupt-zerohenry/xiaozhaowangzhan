<template>
  <transition name="ai-fade">
    <div v-if="visible" class="processing-mask">
      <div class="processing-card">
        <div class="processing-head">
          <div class="spinner" aria-hidden="true"></div>
          <div>
            <strong>{{ title || "AI 正在处理中" }}</strong>
            <p v-if="description" class="mono">{{ description }}</p>
          </div>
          <span class="mono percent">{{ safeProgress }}%</span>
        </div>

        <div class="progress-track">
          <div class="progress-bar" :style="{ width: `${safeProgress}%` }"></div>
        </div>

        <div v-if="stages.length" class="stage-list">
          <span
            v-for="(item, idx) in stages"
            :key="`${idx}-${item}`"
            class="stage-pill mono"
            :class="{ done: idx < safeStageIndex, active: idx === safeStageIndex }"
          >
            {{ item }}
          </span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: "" },
  description: { type: String, default: "" },
  progress: { type: Number, default: 0 },
  stages: { type: Array, default: () => [] },
  stageIndex: { type: Number, default: 0 }
});

const safeProgress = computed(() => Math.max(0, Math.min(100, Number(props.progress) || 0)));
const safeStageIndex = computed(() => {
  if (!props.stages.length) return 0;
  return Math.max(0, Math.min(props.stages.length - 1, Number(props.stageIndex) || 0));
});
</script>

<style scoped>
.processing-mask {
  position: absolute;
  inset: 10px;
  z-index: 30;
  border-radius: 16px;
  background: rgba(246, 251, 248, 0.9);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(24, 160, 88, 0.2);
  display: grid;
  place-items: center;
  padding: 14px;
}

.processing-card {
  width: min(620px, 100%);
  border-radius: 14px;
  border: 1px solid #d6ebdf;
  background: #ffffff;
  box-shadow: 0 16px 30px rgba(15, 122, 70, 0.12);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.processing-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 2px solid #c9e8d7;
  border-top-color: #18a058;
  animation: ai-spin 0.8s linear infinite;
  flex-shrink: 0;
}

.percent {
  margin-left: auto;
  color: #0f8f59;
  font-weight: 600;
}

.progress-track {
  width: 100%;
  height: 7px;
  border-radius: 999px;
  overflow: hidden;
  background: #e4efe8;
}

.progress-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #18a058 0%, #4ec08a 100%);
  transition: width 0.25s ease;
}

.stage-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stage-pill {
  border-radius: 999px;
  border: 1px solid #dbe9e1;
  background: #f6faf8;
  color: #6c8379;
  padding: 5px 10px;
  font-size: 11px;
}

.stage-pill.active {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.12);
  color: #0f8f59;
}

.stage-pill.done {
  border-color: rgba(24, 160, 88, 0.36);
  color: #11784b;
}

.ai-fade-enter-active,
.ai-fade-leave-active {
  transition: opacity 0.18s ease;
}

.ai-fade-enter-from,
.ai-fade-leave-to {
  opacity: 0;
}

@keyframes ai-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
