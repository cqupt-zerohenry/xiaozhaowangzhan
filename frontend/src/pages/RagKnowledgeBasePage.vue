<template>
  <div class="page-wrap rag-detail-page">
    <section class="page-hero">
      <div class="container">
        <div class="detail-hero card">
          <div class="detail-hero-main">
            <button class="btn btn-outline btn-compact" @click="goBack">返回知识库列表</button>
            <h1>{{ selectedKb?.name || "知识库详情" }}</h1>
            <p>{{ selectedKb?.description || "在本页上传文档、自动切块，并查看分块详情与 RAG 对话。" }}</p>
          </div>
          <div class="hero-badges">
            <span class="tag mono">{{ kbDocuments.length }} 文档</span>
            <span class="tag mono">{{ selectedKbChunkTotal }} 分块</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container detail-shell">
        <div class="detail-layout">
          <section class="detail-column detail-column-upload">
            <section class="card detail-card" :class="{ disabled: !selectedKbId }">
              <div class="detail-head">
                <div>
                  <h3>上传文档并自动切块</h3>
                  <p class="mono">支持粘贴内容或上传 txt / md / pdf / doc / docx。</p>
                </div>
                <button class="btn btn-outline btn-compact" :disabled="aiBusy || kbRebuilding || !selectedKbId" @click="rebuildSelectedKbEmbeddings">
                  {{ kbRebuilding ? "重算中..." : "自动重算向量" }}
                </button>
              </div>
              <template v-if="selectedKbId">
                <input v-model="kbDocForm.title" placeholder="文档标题" />
                <textarea v-model="kbDocForm.content" rows="6" placeholder="粘贴知识内容（技术文档、面试题库、课程笔记等）"></textarea>
                <div class="actions">
                  <button class="btn" :disabled="aiBusy" @click="addDocPaste">添加文档</button>
                  <label class="file-picker" :class="{ 'is-disabled': aiBusy }">
                    <span class="btn btn-outline file-picker-btn">选择文件</span>
                    <span class="mono file-picker-name">{{ kbUploadFileName || "未选择文件（txt/md/pdf/doc/docx）" }}</span>
                    <input type="file" :disabled="aiBusy" accept=".txt,.md,.pdf,.doc,.docx" @change="uploadDoc" />
                  </label>
                </div>
              </template>
              <div v-else class="mono">未找到当前知识库，请返回上一页重新选择。</div>
            </section>
          </section>

          <section class="detail-column detail-column-docs">
            <section class="card detail-card">
              <div class="detail-head">
                <h3>文档列表</h3>
                <span class="tag mono">{{ kbDocuments.length }} 篇</span>
              </div>
              <div v-if="kbDocuments.length === 0" class="mono">暂无文档，可先添加文档或上传文件。</div>
              <div v-else class="doc-list">
                <article
                  v-for="doc in kbDocuments"
                  :key="doc.id"
                  class="doc-item"
                  :class="{ active: chunkViewDocId === doc.id }"
                  @click="openDocChunks(doc)"
                >
                  <div>
                    <strong>{{ doc.title }}</strong>
                    <p class="mono">{{ doc.source_type }} · {{ doc.chunk_count }} 个切片 · {{ doc.status }}</p>
                  </div>
                  <div class="actions">
                    <button class="btn btn-outline btn-compact" :disabled="aiBusy" @click.stop="openDocChunks(doc)">查看分块</button>
                    <button class="btn btn-outline btn-compact" :disabled="aiBusy" @click.stop="removeDoc(doc.id)">删除</button>
                  </div>
                </article>
              </div>
            </section>

            <section class="card detail-card chunk-panel">
              <div class="detail-head">
                <h3>分块详情</h3>
                <span class="tag mono">{{ chunkStats.total_chunks }} 个切片</span>
              </div>
              <div v-if="!chunkViewDocId" class="mono">请从上方文档列表选择一篇文档。</div>
              <div v-else class="chunk-list">
                <div class="chunk-card" v-for="chunk in chunkList" :key="chunk.id">
                  <div class="chunk-card-head">
                    <div>
                      <div class="chunk-id">Chunk {{ String(chunk.chunk_index + 1).padStart(2, "0") }}</div>
                      <div class="mono">{{ chunk.char_count }} 字 · {{ chunk.token_count }} token</div>
                    </div>
                  </div>
                  <p class="chunk-text">{{ chunk.content_preview }}</p>
                  <div class="result-tags">
                    <span v-for="tag in chunk.tags" :key="`${chunk.id}-${tag}`" class="tag mono">{{ tag }}</span>
                  </div>
                  <details>
                    <summary class="mono">查看完整分块内容</summary>
                    <pre class="chunk-content">{{ chunk.content }}</pre>
                  </details>
                </div>
              </div>
            </section>
          </section>

          <section class="detail-column detail-column-rag">
            <section class="card detail-card">
              <div class="detail-head">
                <div>
                  <h3>职业 RAG 助手</h3>
                  <p class="mono">面向当前知识库提问，回复在聊天框内滚动查看。</p>
                </div>
                <button class="btn btn-outline btn-compact" :disabled="aiBusy || ragMessages.length === 0" @click="clearRagChat">清空会话</button>
              </div>
              <textarea v-model="ragQuestion" rows="4" placeholder="例如：SRE 需要学习什么？"></textarea>
              <button class="btn" :disabled="aiBusy" @click="runRag">提问</button>

              <div class="rag-chat">
                <div ref="ragChatScrollRef" class="rag-chat-scroll">
                  <div v-if="ragMessages.length === 0" class="rag-chat-empty mono">
                    还没有对话，输入问题后 AI 回复会显示在这里。
                  </div>
                  <article v-for="message in ragMessages" :key="message.id" class="chat-msg" :class="message.role">
                    <div class="chat-meta mono">{{ message.role === "user" ? "我" : "AI 助手" }} · {{ message.time }}</div>
                    <div class="chat-bubble">
                      <p class="chat-text">{{ message.content }}</p>
                      <template v-if="message.role === 'assistant'">
                        <div v-if="message.learningPath.length" class="result-tags" style="margin-top:8px">
                          <span class="tag mono" v-for="item in message.learningPath" :key="`${message.id}-${item}`">{{ item }}</span>
                        </div>
                        <p v-if="message.skillTree.length" class="mono" style="margin-top:8px">
                          技能树：{{ message.skillTree.join(" | ") }}
                        </p>
                        <details v-if="message.sources.length" class="chat-source">
                          <summary class="mono">查看检索来源（{{ message.sources.length }}）</summary>
                          <div class="doc-list" style="margin-top:8px">
                            <div class="doc-item" v-for="(src, idx) in message.sources" :key="`${message.id}-${idx}`">
                              <div>
                                <strong>{{ displaySourceTitle(src) }}</strong>
                                <p class="mono">{{ displaySourceContent(src) }}</p>
                              </div>
                              <span class="tag mono">{{ displaySourceScore(src) }}</span>
                            </div>
                          </div>
                        </details>
                        <p v-else class="mono" style="margin-top:8px;color:#6f8279">本次回答没有可展示的检索来源。</p>
                      </template>
                    </div>
                  </article>
                </div>
              </div>
            </section>
          </section>
        </div>

        <AiProcessingOverlay
          :visible="aiProcessing.visible"
          :title="aiProcessing.title"
          :description="aiProcessing.description"
          :progress="aiProcessing.progress"
          :stages="aiProcessing.stages"
          :stage-index="aiProcessing.stageIndex"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  addKBDocumentPaste,
  deleteKBDocument,
  fetchKBDocumentChunks,
  fetchKBDocuments,
  fetchKnowledgeBases,
  rag,
  rebuildKBEmbeddings,
  uploadKBDocument,
  uploadKBDocumentExtended
} from "../services/api";
import toast from "../utils/toast";
import AiProcessingOverlay from "../components/AiProcessingOverlay.vue";

const route = useRoute();
const router = useRouter();

const knowledgeBases = ref([]);
const selectedKbId = ref(null);
const selectedKb = computed(() => (
  knowledgeBases.value.find((kb) => String(kb.id) === String(selectedKbId.value ?? "")) || null
));

const kbDocForm = ref({ title: "", content: "" });
const kbDocuments = ref([]);
const kbUploadFileName = ref("");
const kbRebuilding = ref(false);

const chunkViewDocId = ref(0);
const chunkList = ref([]);
const chunkStats = ref({ total_chunks: 0, avg_chunk_chars: 0 });

const ragQuestion = ref("");
const ragMessages = ref([]);
const ragChatScrollRef = ref(null);

const aiProcessing = ref({
  visible: false,
  title: "AI 正在处理中",
  description: "",
  progress: 0,
  stages: [],
  stageIndex: 0
});
const aiBusy = computed(() => aiProcessing.value.visible);
const selectedKbChunkTotal = computed(() => (
  kbDocuments.value.reduce((sum, doc) => sum + Number(doc?.chunk_count || 0), 0)
));

let aiProgressTimer = null;
let aiStageTimer = null;
let aiHideTimer = null;

function goBack() {
  router.push("/rag");
}

function buildChatTime() {
  return new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function clearChunkView() {
  chunkViewDocId.value = 0;
  chunkList.value = [];
  chunkStats.value = { total_chunks: 0, avg_chunk_chars: 0 };
}

function normalizeRagText(rawText) {
  let text = String(rawText || "");
  text = text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*/g, "")
    .replace(/__/g, "")
    .replace(/^\s{0,3}#{1,6}\s*/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+[.)、]\s+/gm, "")
    .replace(/\|/g, " ")
    .replace(/[-=]{3,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  text = lines.join("\n");
  const maxChars = 300;
  if (text.length > maxChars) {
    text = `${text.slice(0, maxChars).replace(/\s+\S*$/, "")}…`;
  }
  return text;
}

function normalizeRagSources(rawSources) {
  if (!Array.isArray(rawSources)) return [];
  return rawSources.map((item) => {
    const source = item && typeof item === "object" ? item : {};
    const title = String(
      source.document_title
      || source.documentTitle
      || source.title
      || source.doc_title
      || ""
    ).trim();
    const content = String(
      source.chunk_content
      || source.chunkContent
      || source.content
      || source.content_preview
      || ""
    ).trim();
    const scoreValue = Number(
      source.relevance_score
      ?? source.relevanceScore
      ?? source.score
      ?? 0
    );
    return {
      document_title: title || "未命名来源",
      chunk_content: content || "该来源暂无可展示片段",
      relevance_score: Number.isFinite(scoreValue) ? Math.max(0, Math.min(1, scoreValue)) : 0
    };
  });
}

function displaySourceTitle(src) {
  return String(src?.document_title || "未命名来源");
}

function displaySourceContent(src) {
  const content = String(src?.chunk_content || "该来源暂无可展示片段");
  return content.length > 120 ? `${content.slice(0, 120)}...` : content;
}

function displaySourceScore(src) {
  const score = Number(src?.relevance_score || 0);
  const pct = Number.isFinite(score) ? Math.max(0, Math.min(100, Math.round(score * 100))) : 0;
  return `${pct}%`;
}

function pushRagMessage(payload) {
  ragMessages.value.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    role: payload.role,
    time: buildChatTime(),
    content: payload.content,
    learningPath: payload.learningPath || [],
    skillTree: payload.skillTree || [],
    sources: payload.sources || []
  });
}

async function scrollRagChatToBottom() {
  await nextTick();
  const el = ragChatScrollRef.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

function clearRagChat() {
  ragMessages.value = [];
}

function clearAiProcessingTimers() {
  if (aiProgressTimer) clearInterval(aiProgressTimer);
  if (aiStageTimer) clearInterval(aiStageTimer);
  if (aiHideTimer) clearTimeout(aiHideTimer);
  aiProgressTimer = null;
  aiStageTimer = null;
  aiHideTimer = null;
}

function beginAiProcessing({ title, description = "", stages = [] }) {
  clearAiProcessingTimers();
  aiProcessing.value = {
    visible: true,
    title: title || "AI 正在处理中",
    description,
    progress: 8,
    stages,
    stageIndex: 0
  };
  aiProgressTimer = setInterval(() => {
    if (!aiProcessing.value.visible) return;
    const now = aiProcessing.value.progress;
    if (now >= 92) return;
    aiProcessing.value.progress = Math.min(92, now + Math.max(1, Math.floor((95 - now) / 8)));
  }, 220);
  if (stages.length > 1) {
    aiStageTimer = setInterval(() => {
      if (!aiProcessing.value.visible) return;
      aiProcessing.value.stageIndex = Math.min(stages.length - 1, aiProcessing.value.stageIndex + 1);
    }, 1050);
  }
}

function endAiProcessing() {
  return new Promise((resolve) => {
    if (!aiProcessing.value.visible) {
      resolve();
      return;
    }
    aiProcessing.value.progress = 100;
    if (aiProcessing.value.stages.length) {
      aiProcessing.value.stageIndex = aiProcessing.value.stages.length - 1;
    }
    if (aiProgressTimer) clearInterval(aiProgressTimer);
    if (aiStageTimer) clearInterval(aiStageTimer);
    aiProgressTimer = null;
    aiStageTimer = null;
    aiHideTimer = setTimeout(() => {
      aiProcessing.value.visible = false;
      resolve();
    }, 260);
  });
}

async function withAiProcessing(options, task) {
  beginAiProcessing(options);
  try {
    return await task();
  } finally {
    await endAiProcessing();
  }
}

async function loadKnowledgeBaseContext() {
  try {
    knowledgeBases.value = await fetchKnowledgeBases();
    const targetId = String(route.params.kbId || "");
    const found = knowledgeBases.value.find((kb) => String(kb.id) === targetId);
    if (!found) {
      toast.warn("未找到该知识库，请重新选择");
      router.replace("/rag");
      return;
    }
    selectedKbId.value = found.id;
    kbDocuments.value = await fetchKBDocuments(found.id);
    clearChunkView();
  } catch (_) {
    toast.error("加载知识库详情失败");
  }
}

async function addDocPaste() {
  if (!selectedKbId.value) return;
  if (!kbDocForm.value.title || !kbDocForm.value.content) {
    toast.warn("请填写标题和内容");
    return;
  }
  try {
    await withAiProcessing(
      {
        title: "AI 正在处理文档",
        description: "会自动切片并向量化写入知识库",
        stages: ["接收文档", "文本切片", "向量化并入库"]
      },
      async () => addKBDocumentPaste(selectedKbId.value, kbDocForm.value)
    );
    kbDocForm.value = { title: "", content: "" };
    toast.success("文档已添加并完成向量化");
    kbDocuments.value = await fetchKBDocuments(selectedKbId.value);
  } catch (_) {
    toast.error("添加文档失败");
  }
}

async function uploadDoc(event) {
  const file = event?.target?.files?.[0];
  if (!file || !selectedKbId.value) return;
  kbUploadFileName.value = String(file.name || "");
  const lower = String(file.name || "").toLowerCase();
  try {
    await withAiProcessing(
      {
        title: "AI 正在上传并向量化文件",
        description: "会提取文本、切片并更新知识库索引",
        stages: ["上传文件", "提取文本", "向量化并入库"]
      },
      async () => {
        if (lower.endsWith(".pdf") || lower.endsWith(".docx") || lower.endsWith(".doc")) {
          await uploadKBDocumentExtended(selectedKbId.value, file);
        } else {
          await uploadKBDocument(selectedKbId.value, file);
        }
      }
    );
    toast.success("文件已上传并完成向量化");
    kbDocuments.value = await fetchKBDocuments(selectedKbId.value);
  } catch (_) {
    toast.error("上传失败");
  }
}

async function removeDoc(docId) {
  if (!selectedKbId.value) return;
  try {
    await withAiProcessing(
      {
        title: "AI 正在删除文档",
        description: "会同步清理该文档关联的向量切片",
        stages: ["定位文档", "删除切片", "刷新索引"]
      },
      async () => deleteKBDocument(selectedKbId.value, docId)
    );
    if (chunkViewDocId.value === docId) {
      clearChunkView();
    }
    toast.success("文档已删除");
    kbDocuments.value = await fetchKBDocuments(selectedKbId.value);
  } catch (_) {
    toast.error("删除失败");
  }
}

async function rebuildSelectedKbEmbeddings() {
  if (!selectedKbId.value) return;
  kbRebuilding.value = true;
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在重算向量",
        description: "会重新编码切片并更新向量索引",
        stages: ["读取切片", "批量向量化", "写回索引"]
      },
      async () => rebuildKBEmbeddings(selectedKbId.value)
    );
    toast.success(`重算完成：${result.reembedded_chunks} 条`);
    kbDocuments.value = await fetchKBDocuments(selectedKbId.value);
  } catch (_) {
    toast.error("向量重算失败");
  } finally {
    kbRebuilding.value = false;
  }
}

async function openDocChunks(doc) {
  if (!selectedKbId.value || !doc?.id) return;
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在读取分块详情",
        description: "会展示分块内容、大小和自动标签",
        stages: ["读取分块", "分析标签", "整理展示"]
      },
      async () => fetchKBDocumentChunks(selectedKbId.value, doc.id)
    );
    chunkViewDocId.value = doc.id;
    chunkList.value = Array.isArray(result?.chunks) ? result.chunks : [];
    chunkStats.value = {
      total_chunks: Number(result?.total_chunks || chunkList.value.length || 0),
      avg_chunk_chars: Number(result?.avg_chunk_chars || 0)
    };
  } catch (_) {
    toast.error("读取分块失败");
  }
}

async function runRag() {
  const question = String(ragQuestion.value || "").trim();
  if (!question) {
    toast.warn("请输入问题");
    return;
  }
  pushRagMessage({ role: "user", content: question });
  await scrollRagChatToBottom();
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在检索知识库",
        description: "会召回相关分块并生成回答",
        stages: ["理解问题", "检索分块", "组织答案"]
      },
      async () => rag({
        question,
        kb_id: selectedKbId.value || undefined
      })
    );
    const normalizedAnswer = normalizeRagText(result?.answer || "") || "已完成检索，但暂无可展示的总结内容。你可以换个更具体的问题试试。";
    const normalizedSources = normalizeRagSources(result?.sources);
    pushRagMessage({
      role: "assistant",
      content: normalizedAnswer,
      learningPath: (result?.learning_path || []).slice(0, 6),
      skillTree: (result?.skill_tree || []).slice(0, 5),
      sources: normalizedSources
    });
    await scrollRagChatToBottom();
    ragQuestion.value = "";
  } catch (_) {
    pushRagMessage({
      role: "assistant",
      content: "抱歉，这次检索失败了。你可以稍后重试。"
    });
    await scrollRagChatToBottom();
    toast.error("RAG 提问失败，请稍后重试");
  }
}

watch(() => route.params.kbId, loadKnowledgeBaseContext);

onMounted(loadKnowledgeBaseContext);

onUnmounted(() => {
  clearAiProcessingTimers();
});
</script>

<style scoped>
.rag-detail-page {
  background: #f4f7f2;
}

.detail-hero {
  border-radius: 22px;
  border: 1px solid #d9e6d7;
  padding: 18px;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: nowrap;
  text-align: left;
}

.detail-hero-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.detail-hero h1 {
  margin: 4px 0 0;
  text-align: left;
}

.detail-hero p {
  margin: 0;
  color: #5f7269;
  text-align: left;
}

.hero-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
  align-self: flex-start;
}

.detail-shell {
  position: relative;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.86fr) minmax(420px, 1.14fr) minmax(320px, 0.9fr);
  gap: 14px;
  align-items: start;
}

.detail-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
}

.detail-column-rag .detail-card {
  position: sticky;
  top: 12px;
}

.detail-card {
  border-radius: 18px;
  border: 1px solid #d9e6d7;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-card.disabled {
  opacity: 0.72;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-head h3 {
  margin: 0;
}

.doc-list,
.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
  padding-right: 2px;
}

.detail-column-docs .doc-list {
  max-height: 300px;
}

.detail-column-docs .chunk-list {
  max-height: 430px;
}

.doc-item,
.chunk-card {
  border: 1px solid #e4ebe2;
  border-radius: 12px;
  background: #fcfdfc;
  padding: 10px;
}

.doc-item {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.doc-item.active {
  border-color: #97d5ac;
  background: #f3fbf5;
}

.doc-item p {
  margin: 4px 0 0;
}

.chunk-panel {
  background: linear-gradient(135deg, #f5fbf6 0%, #ffffff 100%);
}

.chunk-card-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.chunk-id {
  font-size: 12px;
  font-weight: 700;
  color: #32493d;
}

.chunk-text {
  margin: 8px 0;
  color: #5f6f67;
  line-height: 1.55;
}

.chunk-content {
  margin: 8px 0 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
  color: #5f6f67;
}

.rag-chat {
  border: 1px dashed #c6dccd;
  border-radius: 16px;
  background: #f8fbf8;
  padding: 10px;
}

.rag-chat-scroll {
  max-height: 560px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rag-chat-empty {
  color: #6a7d73;
  font-size: 13px;
}

.chat-msg {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-msg.user {
  align-items: flex-end;
}

.chat-meta {
  font-size: 11px;
  color: #7a8c84;
}

.chat-bubble {
  width: 100%;
  border: 1px solid #d7e6db;
  border-radius: 14px;
  background: #fff;
  padding: 10px 12px;
}

.chat-msg.user .chat-bubble {
  width: auto;
  max-width: 92%;
  border-color: #bfe2ca;
  background: #eaf8ef;
}

.chat-text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.65;
  color: #354b40;
}

.chat-source summary {
  cursor: pointer;
  color: #5f7269;
}

.file-picker {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-picker input[type="file"] {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-picker.is-disabled {
  opacity: 0.6;
  pointer-events: none;
}

.file-picker-btn {
  min-height: 38px;
  min-width: 102px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.file-picker-name {
  color: #607068;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-compact {
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1;
}

textarea,
input,
select {
  width: 100%;
}

@media (max-width: 1300px) {
  .detail-layout {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  .detail-column-rag {
    grid-column: 1 / -1;
  }

  .detail-column-rag .detail-card {
    position: static;
  }
}

@media (max-width: 980px) {
  .detail-hero {
    flex-wrap: wrap;
  }

  .hero-badges {
    margin-left: 0;
  }

  .detail-layout {
    grid-template-columns: 1fr;
  }

  .doc-list,
  .chunk-list,
  .rag-chat-scroll {
    max-height: none;
  }
}
</style>
