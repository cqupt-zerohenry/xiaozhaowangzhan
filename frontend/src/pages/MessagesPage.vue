<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
        <div>
          <h1>消息</h1>
          <p>集中处理沟通与面试邀约。</p>
        </div>
        <button class="btn btn-outline" @click="loadMessages">刷新会话</button>
        </div>
      </div>
    </section>

    <section>
      <div class="container message-grid">
        <div class="card message-list">
          <h3>会话列表</h3>
          <div v-if="conversations.length === 0" class="mono">暂无会话记录</div>
          <div v-else class="conversation-scroll">
            <button
              v-for="conversation in conversations"
              :key="conversation.peerId"
              class="message-item"
              :class="{ active: conversation.peerId === activePeerId }"
              @click="openConversation(conversation.peerId)"
            >
              <div class="item-main">
                <div class="avatar">
                  {{ userInitial(conversation.peerId) }}
                  <span class="online-dot" :class="{ active: isOnline(conversation.peerId) }"></span>
                </div>
                <div class="item-body">
                  <div class="item-head">
                    <strong>{{ userName(conversation.peerId) }}</strong>
                    <span class="mono item-time">{{ formatTime(conversation.lastTime) }}</span>
                  </div>
                  <p class="item-preview">{{ previewText(conversation.lastContent) }}</p>
                </div>
                <span v-if="conversation.unreadCount > 0" class="unread-badge">
                  {{ conversation.unreadCount > 99 ? "99+" : conversation.unreadCount }}
                </span>
              </div>
            </button>
          </div>
        </div>
        <div class="card message-detail">
          <h3>沟通详情</h3>
          <div v-if="activePeerId">
            <div class="chat-head">
              <strong>{{ userName(activePeerId) }}</strong>
              <span class="mono">{{ isOnline(activePeerId) ? '在线' : '离线' }}</span>
            </div>
            <div class="history">
              <div
                class="message-row"
                v-for="item in currentMessages"
                :key="item.id"
                :class="{ mine: item.sender_id === myUserId, system: isSystemMessage(item) }"
              >
                <div class="bubble" :class="{ mine: item.sender_id === myUserId, system: isSystemMessage(item) }">
                  <div class="bubble-head">
                    <strong>{{ item.sender_id === myUserId ? '我' : userName(item.sender_id) }}</strong>
                    <span class="mono">{{ formatTime(item.create_time) }}</span>
                  </div>
                  <p>{{ item.content }}</p>
                  <span v-if="item.message_type !== 'text'" class="tag mono">{{ item.message_type }}</span>
                </div>
              </div>
            </div>
            <div class="reply-box">
              <textarea v-model="reply" rows="3" placeholder="输入回复内容"></textarea>
              <button class="btn" :disabled="!reply.trim() || !activePeerId" @click="sendReply">发送</button>
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
import toast from '../utils/toast';
import { fetchMessages, fetchOnlineUsers, fetchUsers, markMessageRead, sendMessage } from '../services/api';
import { useAuth } from '../store/auth';

const auth = useAuth();
const messages = ref([]);
const activePeerId = ref(null);
const reply = ref('');
const userNames = ref({});
const myUserId = computed(() => auth.user.value?.id || 0);

async function loadUserNames() {
  try {
    const users = await fetchUsers();
    const map = {};
    for (const u of users) {
      map[u.id] = u.name || u.email;
    }
    userNames.value = map;
  } catch (e) {
    // Non-admin may not have access to user list — build from messages
    const map = {};
    map[auth.user.value?.id] = auth.user.value?.name || '我';
    userNames.value = map;
  }
}

function userName(id) {
  if (!id || Number(id) === 0) return '系统通知';
  return userNames.value[id] || `用户 ${id}`;
}
const socket = ref(null);
const onlineUsers = ref([]);
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
  if (!userId || Number(userId) === 0) return false;
  return onlineUsers.value.includes(userId);
}

function isSystemMessage(message) {
  if (!message) return false;
  return Number(message.sender_id || 0) === 0 || message.message_type === 'system';
}

const conversations = computed(() => {
  const map = new Map();
  const currentUserId = auth.user.value?.id;
  // Messages come sorted by id desc from API, so iterate in reverse to get chronological order
  const sorted = [...messages.value].sort((a, b) => (a.id || 0) - (b.id || 0));
  for (const item of sorted) {
    const peerId = item.sender_id === currentUserId ? item.receiver_id : item.sender_id;
    // Always overwrite so the last (newest) message wins
    map.set(peerId, {
      peerId,
      lastContent: item.content,
      lastTime: item.create_time,
      unreadCount: 0
    });
    if (item.sender_id === peerId && item.receiver_id === currentUserId && !item.is_read) {
      map.get(peerId).unreadCount += 1;
    }
  }
  return Array.from(map.values()).reverse();
});

function userInitial(id) {
  const name = userName(id);
  if (!name) return '讯';
  return String(name).slice(0, 1);
}

function previewText(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text) return '暂无消息内容';
  if (text.length <= 36) return text;
  return `${text.slice(0, 36)}...`;
}

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

async function openConversation(peerId) {
  activePeerId.value = peerId;
  const myId = auth.user.value?.id;
  const unread = messages.value.filter(
    m => m.sender_id === peerId && m.receiver_id === myId && !m.is_read
  );
  for (const m of unread) {
    try { await markMessageRead(m.id); m.is_read = true; } catch (_) {}
  }
}

async function sendReply() {
  if (!reply.value || !activePeerId.value) return;
  const text = reply.value;
  try {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      // WebSocket handler persists to DB and pushes to receiver in real-time
      socket.value.send(`to:${activePeerId.value}:${text}`);
    } else {
      // Fallback: use HTTP API when WebSocket is disconnected
      await sendMessage({
        sender_id: auth.user.value?.id || 0,
        receiver_id: activePeerId.value,
        content: text,
        message_type: 'text'
      });
    }
    reply.value = '';
    await loadMessages();
  } catch (err) {
    toast.error('发送失败，请重试');
  }
}

function connectSocket() {
  const userId = auth.user.value?.id;
  if (!userId) return;
  const apiBase = import.meta.env.VITE_API_BASE || '';
  let wsHost;
  if (apiBase && apiBase.startsWith('http')) {
    const url = new URL(apiBase);
    wsHost = url.host;
  } else {
    wsHost = window.location.host;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${wsHost}/ws/chat/${userId}`;
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
  ws.onerror = () => {
    console.warn('WebSocket connection error');
    socket.value = null;
  };
  ws.onclose = () => {
    socket.value = null;
  };
  socket.value = ws;
}

onMounted(async () => {
  await loadUserNames();
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

.conversation-scroll {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 520px;
  overflow: auto;
  padding-right: 2px;
}

.message-item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
  text-align: left;
  background: #fff;
  display: block;
  cursor: pointer;
}

.message-item.active {
  border-color: rgba(24, 160, 88, 0.4);
  background: rgba(24, 160, 88, 0.08);
}

.item-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #eaf6ee;
  border: 1px solid #cbe8d7;
  color: var(--accent-dark);
  display: grid;
  place-items: center;
  font-weight: 700;
  position: relative;
  flex-shrink: 0;
}

.item-body {
  min-width: 0;
  flex: 1;
}

.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.item-time {
  color: #8fa09a;
  flex-shrink: 0;
}

.item-preview {
  margin: 2px 0 0;
  color: #5f7470;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-badge {
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background: #e53e3e;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
}

.message-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0 2px;
  border-bottom: 1px dashed var(--line);
}

.history {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow: auto;
  padding: 2px 2px 4px;
}

.message-row {
  display: flex;
  justify-content: flex-start;
}

.message-row.mine {
  justify-content: flex-end;
}

.bubble {
  width: min(84%, 560px);
  border-radius: 16px;
  border: 1px solid var(--line);
  padding: 16px;
  background: #fff;
}

.bubble.mine {
  background: #e9f8ef;
  border-color: #b8dfc9;
}

.bubble.system {
  background: #f6f7f8;
  border-color: #dfe5e7;
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
  position: absolute;
  right: -2px;
  bottom: -1px;
  margin-right: 0;
  vertical-align: initial;
  border: 2px solid #fff;
}

.online-dot.active {
  background: var(--accent);
  box-shadow: 0 0 6px rgba(24, 160, 88, 0.4);
}

@media (max-width: 900px) {
  .message-grid {
    grid-template-columns: 1fr;
  }
}
</style>
