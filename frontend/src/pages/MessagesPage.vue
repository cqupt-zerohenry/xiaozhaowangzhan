<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>消息</h1>
          <p>集中处理沟通与面试邀约。</p>
        </div>
        <button class="btn btn-outline" @click="loadMessages">刷新会话</button>
      </div>
    </section>

    <section>
      <div class="container message-grid">
        <div class="card message-list">
          <h3>会话列表</h3>
          <div class="new-msg-row">
            <input v-model="newPeerId" type="number" placeholder="用户 ID" class="peer-input" />
            <button class="btn btn-outline" @click="startNewChat">发起</button>
          </div>
          <div v-if="conversations.length === 0" class="mono">暂无消息</div>
          <button
            v-for="conversation in conversations"
            :key="conversation.peerId"
            class="message-item"
            :class="{ active: conversation.peerId === activePeerId }"
            @click="openConversation(conversation.peerId)"
          >
            <div>
              <strong>
                <span class="online-dot" :class="{ active: isOnline(conversation.peerId) }"></span>
                用户 {{ conversation.peerId }}
              </strong>
              <p>{{ conversation.lastContent }}</p>
            </div>
            <span class="mono">{{ formatTime(conversation.lastTime) }}</span>
          </button>
        </div>
        <div class="card message-detail">
          <h3>沟通详情</h3>
          <div v-if="activePeerId">
            <div class="history">
              <div class="bubble" v-for="item in currentMessages" :key="item.id">
                <div class="bubble-head">
                  <strong>{{ item.sender_id === auth.user.value?.id ? '我' : `用户 ${item.sender_id}` }}</strong>
                  <span class="mono">{{ formatTime(item.create_time) }}</span>
                </div>
                <p>{{ item.content }}</p>
                <span class="tag mono">{{ item.message_type }}</span>
              </div>
            </div>
            <div class="reply-box">
              <textarea v-model="reply" rows="3" placeholder="输入回复内容"></textarea>
              <button class="btn" @click="sendReply">发送</button>
            </div>
          </div>
          <div v-else class="mono">请选择左侧会话</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { fetchMessages, fetchOnlineUsers, sendMessage } from '../services/api';
import { useAuth } from '../store/auth';

const auth = useAuth();
const messages = ref([]);
const activePeerId = ref(null);
const reply = ref('');
const socket = ref(null);
const onlineUsers = ref([]);
const newPeerId = ref('');
let onlineTimer = null;

async function loadOnlineUsers() {
  try {
    const res = await fetchOnlineUsers();
    onlineUsers.value = res.online_user_ids || [];
  } catch (e) {
    onlineUsers.value = [];
  }
}

function isOnline(userId) {
  return onlineUsers.value.includes(userId);
}

function startNewChat() {
  const id = parseInt(newPeerId.value);
  if (!id || id === auth.user.value?.id) return;
  activePeerId.value = id;
  newPeerId.value = '';
  loadMessages();
}

const conversations = computed(() => {
  const map = new Map();
  const currentUserId = auth.user.value?.id;
  for (const item of messages.value) {
    const peerId = item.sender_id === currentUserId ? item.receiver_id : item.sender_id;
    if (!map.has(peerId)) {
      map.set(peerId, {
        peerId,
        lastContent: item.content,
        lastTime: item.create_time
      });
    }
  }
  return Array.from(map.values());
});

const currentMessages = computed(() => {
  if (!activePeerId.value) return [];
  const currentUserId = auth.user.value?.id;
  return messages.value
    .filter((item) => {
      return (
        (item.sender_id === currentUserId && item.receiver_id === activePeerId.value) ||
        (item.sender_id === activePeerId.value && item.receiver_id === currentUserId)
      );
    })
    .sort((a, b) => (a.id || 0) - (b.id || 0));
});

async function loadMessages() {
  try {
    messages.value = await fetchMessages();
    if (!activePeerId.value && conversations.value.length > 0) {
      activePeerId.value = conversations.value[0].peerId;
    }
  } catch (err) {
    messages.value = [];
  }
}

function openConversation(peerId) {
  activePeerId.value = peerId;
}

async function sendReply() {
  if (!reply.value || !activePeerId.value) return;
  const text = reply.value;
  try {
    await sendMessage({
      sender_id: auth.user.value?.id || 0,
      receiver_id: activePeerId.value,
      content: text,
      message_type: 'text'
    });
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(`to:${activePeerId.value}:${text}`);
    }
    reply.value = '';
    await loadMessages();
  } catch (err) {
    // ignore
  }
}

function connectSocket() {
  const userId = auth.user.value?.id;
  if (!userId) return;
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${window.location.host}/ws/chat/${userId}`;
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (event) => {
    const data = event.data;
    if (data.startsWith('from:') || data.startsWith('__online:') || data.startsWith('__offline:')) {
      loadMessages();
      loadOnlineUsers();
    } else {
      loadMessages();
    }
  };
  ws.onclose = () => {
    socket.value = null;
  };
  socket.value = ws;
}

onMounted(async () => {
  await loadMessages();
  await loadOnlineUsers();
  onlineTimer = setInterval(loadOnlineUsers, 10000);
  connectSocket();
});

onBeforeUnmount(() => {
  if (onlineTimer) clearInterval(onlineTimer);
  if (socket.value) {
    socket.value.close();
    socket.value = null;
  }
});

function formatTime(value) {
  if (!value) {
    return '刚刚';
  }
  return String(value).replace('T', ' ').slice(0, 16);
}
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero {
  padding: 32px 0 16px;
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.message-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.4fr) minmax(0, 1fr);
  gap: 24px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  text-align: left;
  background: #fff;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.message-item.active {
  border-color: rgba(24, 160, 88, 0.4);
  background: rgba(24, 160, 88, 0.08);
}

.message-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow: auto;
}

.bubble {
  border-radius: 16px;
  border: 1px solid var(--line);
  padding: 16px;
  background: #fff;
}

.bubble-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.reply-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.online-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--line);
  margin-right: 6px;
  vertical-align: middle;
}

.online-dot.active {
  background: var(--accent);
  box-shadow: 0 0 6px rgba(24, 160, 88, 0.4);
}

.new-msg-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.peer-input {
  width: 100px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--line);
}

@media (max-width: 900px) {
  .message-grid {
    grid-template-columns: 1fr;
  }
}
</style>
