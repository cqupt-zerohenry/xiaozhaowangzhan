<template>
  <div v-if="visible" class="assistant-wrap">
    <button class="fab" @click="chatOpen = !chatOpen" :title="chatOpen ? '关闭助手' : 'AI 求职助手'">
      <span v-if="!chatOpen" class="fab-icon">AI</span>
      <span v-else class="fab-icon fab-close">x</span>
    </button>

    <transition name="chat-slide">
      <div v-if="chatOpen" class="chat-window">
        <div class="chat-header">
          <strong>AI 求职助手</strong>
          <span class="mono">基于简历 + 岗位知识库</span>
        </div>
        <div class="chat-body" ref="chatBody">
          <div v-if="messages.length === 0" class="chat-welcome">
            <p>你好！我是 AI 求职助手。</p>
            <p>我可以根据你的简历和平台岗位，为你推荐最匹配的职位。</p>
            <div class="quick-asks">
              <button class="chip" @click="sendQuick('帮我推荐适合我的岗位')">推荐岗位</button>
              <button class="chip" @click="sendQuick('我适合什么方向？')">方向建议</button>
              <button class="chip" @click="sendQuick('有哪些北京的技术岗位？')">北京技术岗</button>
            </div>
          </div>
          <template v-for="(msg, i) in messages" :key="i">
            <div :class="['chat-msg', msg.role]">
              <div class="msg-bubble">{{ msg.content }}</div>
            </div>
            <div v-if="msg.jobs && msg.jobs.length" class="job-recs">
              <router-link
                v-for="j in msg.jobs"
                :key="j.job_id"
                :to="`/jobs/${j.job_id}`"
                class="job-rec-card"
                @click="chatOpen = false"
              >
                <strong>{{ j.job_name }}</strong>
                <span class="meta">{{ j.company_name }} · {{ j.city }}</span>
                <span class="salary">{{ j.salary }}元</span>
              </router-link>
            </div>
          </template>
          <div v-if="loading" class="chat-msg assistant">
            <div class="msg-bubble typing">思考中<span class="dots"><span>.</span><span>.</span><span>.</span></span></div>
          </div>
        </div>
        <div class="chat-footer">
          <input
            v-model="input"
            @keyup.enter="send"
            placeholder="输入求职问题..."
            :disabled="loading"
          />
          <button class="send-btn" @click="send" :disabled="loading || !input.trim()">
            发送
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue';
import { useRoute } from 'vue-router';
import { jobAssistant } from '../services/api';
import { useAuth } from '../store/auth';

const auth = useAuth();
const route = useRoute();

const showOnPages = ['dashboard', 'jobs', 'job-detail', 'profile', 'favorites', 'home'];
const visible = computed(() => {
  return auth.isAuthed.value && auth.role.value === 'student' && showOnPages.includes(route.name);
});

const chatOpen = ref(false);
const messages = ref([]);
const input = ref('');
const loading = ref(false);
const chatBody = ref(null);

function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight;
    }
  });
}

function sendQuick(text) {
  input.value = text;
  send();
}

async function send() {
  const text = input.value.trim();
  if (!text || loading.value) return;

  messages.value.push({ role: 'user', content: text });
  input.value = '';
  loading.value = true;
  scrollToBottom();

  // Build history for API (exclude job cards, keep text only)
  const history = messages.value
    .filter(m => !m.jobs)
    .map(m => ({ role: m.role, content: m.content }));

  try {
    const res = await jobAssistant({ message: text, history: history.slice(0, -1) });
    messages.value.push({
      role: 'assistant',
      content: res.reply,
      jobs: res.recommended_jobs || [],
    });
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，服务暂时不可用，请稍后再试。',
      jobs: [],
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}
</script>

<style scoped>
.assistant-wrap {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 1000;
}

.fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  border: none;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(24, 160, 88, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: absolute;
  bottom: 0;
  right: 0;
}

.fab:hover {
  transform: scale(1.08);
  box-shadow: 0 8px 28px rgba(24, 160, 88, 0.5);
}

.fab-icon {
  font-weight: 800;
  font-size: 18px;
  font-family: "IBM Plex Mono", monospace;
}

.fab-close {
  font-size: 24px;
  font-weight: 400;
}

.chat-window {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 380px;
  height: 520px;
  background: #fff;
  border-radius: 20px;
  border: 1px solid var(--line);
  box-shadow: 0 16px 48px rgba(15, 31, 23, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(24, 160, 88, 0.04);
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-welcome {
  text-align: center;
  padding: 20px 0;
  color: var(--muted);
}

.chat-welcome p {
  margin: 4px 0;
  font-size: 14px;
}

.quick-asks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}

.chip {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip:hover {
  border-color: var(--accent);
  background: rgba(24, 160, 88, 0.06);
}

.chat-msg {
  display: flex;
}

.chat-msg.user {
  justify-content: flex-end;
}

.chat-msg.assistant {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.user .msg-bubble {
  background: var(--accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant .msg-bubble {
  background: #f0f4f2;
  color: var(--ink);
  border-bottom-left-radius: 4px;
}

.typing {
  color: var(--muted);
}

.dots span {
  animation: dot-blink 1.4s infinite;
  animation-fill-mode: both;
}

.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}

.job-recs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 8px;
}

.job-rec-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s ease, transform 0.15s ease;
}

.job-rec-card:hover {
  border-color: var(--accent);
  transform: translateX(4px);
}

.job-rec-card strong {
  font-size: 14px;
}

.job-rec-card .meta {
  font-size: 12px;
  color: var(--muted);
}

.job-rec-card .salary {
  font-size: 13px;
  color: #ff6b35;
  font-weight: 700;
}

.chat-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--line);
  display: flex;
  gap: 8px;
  background: #fafcfb;
}

.chat-footer input {
  flex: 1;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  font-size: 13px;
  background: #fff;
}

.send-btn {
  padding: 10px 18px;
  border-radius: 999px;
  border: none;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-dark);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Slide transition */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

@media (max-width: 480px) {
  .assistant-wrap {
    bottom: 16px;
    right: 16px;
  }
  .chat-window {
    width: calc(100vw - 32px);
    height: calc(100vh - 120px);
    bottom: 70px;
    right: 0;
  }
}
</style>
