<template>
  <div class="page-wrap rag-entry-page">
    <section class="page-hero">
      <div class="container">
        <div class="entry-hero card">
          <div class="entry-hero-main">
            <div class="hero-pill mono">RAG · Knowledge Base</div>
            <h1>RAG 知识库中心</h1>
            <p>先在本页完成知识库创建与选择，进入下一页后再进行文档上传、自动切块与分块查看。</p>
            <div class="hero-guide mono">流程：创建或选择知识库 → 进入详情页上传文档与查看分块</div>
          </div>
          <div class="hero-actions">
            <button class="btn btn-outline" :disabled="aiBusy" @click="loadKnowledgeBases">刷新列表</button>
            <button class="btn" :disabled="aiBusy" @click="createSampleKnowledgeBase">一键创建示例</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container entry-layout">
        <section class="card entry-card">
          <div class="entry-head">
            <h3>新建知识库</h3>
          </div>
          <div class="entry-form">
            <input v-model="kbForm.name" placeholder="知识库名称（如：SRE 知识库）" />
            <input v-model="kbForm.description" placeholder="知识库描述（可选）" />
            <button class="btn" :disabled="aiBusy" @click="createKB">创建知识库</button>
          </div>
          <p v-if="kbStatus" class="mono status-text">{{ kbStatus }}</p>
        </section>

        <section class="card entry-card">
          <div class="entry-head">
            <h3>我的知识库</h3>
            <span class="tag mono">{{ knowledgeBases.length }} 个</span>
          </div>
          <div v-if="knowledgeBases.length === 0" class="mono">暂无知识库，请先创建。</div>
          <div v-else class="kb-list">
            <article v-for="kb in knowledgeBases" :key="kb.id" class="kb-item">
              <div class="kb-main">
                <strong>{{ kb.name }}</strong>
                <p class="mono">{{ kb.description || "无描述" }}</p>
              </div>
              <div class="actions">
                <button class="btn btn-outline btn-compact" :disabled="aiBusy" @click="openKbDetail(kb.id)">进入知识库</button>
                <button class="btn btn-outline btn-compact" :disabled="aiBusy" @click="renameKB(kb)">改名</button>
                <button class="btn btn-outline btn-compact" :disabled="aiBusy" @click="removeKB(kb.id)">删除</button>
              </div>
            </article>
          </div>
        </section>
      </div>
    </section>

    <AiProcessingOverlay
      :visible="aiProcessing.visible"
      :title="aiProcessing.title"
      :description="aiProcessing.description"
      :progress="aiProcessing.progress"
      :stages="aiProcessing.stages"
      :stage-index="aiProcessing.stageIndex"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { createKnowledgeBase, deleteKnowledgeBase, fetchKnowledgeBases, updateKnowledgeBase } from "../services/api";
import AiProcessingOverlay from "../components/AiProcessingOverlay.vue";

const router = useRouter();

const knowledgeBases = ref([]);
const kbForm = ref({ name: "", description: "" });
const kbStatus = ref("");

const aiProcessing = ref({
  visible: false,
  title: "AI 正在处理中",
  description: "",
  progress: 0,
  stages: [],
  stageIndex: 0
});
const aiBusy = computed(() => aiProcessing.value.visible);

let aiProgressTimer = null;
let aiStageTimer = null;
let aiHideTimer = null;

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

async function loadKnowledgeBases() {
  try {
    knowledgeBases.value = await fetchKnowledgeBases();
  } catch (_) {
    knowledgeBases.value = [];
  }
}

async function createKB() {
  if (!kbForm.value.name) {
    kbStatus.value = "请输入知识库名称";
    return;
  }
  try {
    const created = await withAiProcessing(
      {
        title: "AI 正在创建知识库",
        description: "会完成知识库初始化并准备索引",
        stages: ["创建知识库", "写入基础信息", "准备完成"]
      },
      async () => createKnowledgeBase(kbForm.value)
    );
    kbForm.value = { name: "", description: "" };
    kbStatus.value = "知识库已创建";
    await loadKnowledgeBases();
    if (created?.id) {
      openKbDetail(created.id);
    }
  } catch (_) {
    kbStatus.value = "创建失败";
  }
}

async function createSampleKnowledgeBase() {
  const name = `测试知识库-${new Date().toISOString().slice(0, 10)}`;
  try {
    const created = await withAiProcessing(
      {
        title: "AI 正在创建示例知识库",
        description: "会快速创建可直接使用的示例库",
        stages: ["创建知识库", "配置示例项", "准备完成"]
      },
      async () => createKnowledgeBase({
        name,
        description: "用于测试 RAG 问答与切块流程"
      })
    );
    kbStatus.value = "示例知识库已创建";
    await loadKnowledgeBases();
    if (created?.id) {
      openKbDetail(created.id);
    }
  } catch (_) {
    kbStatus.value = "示例创建失败";
  }
}

function openKbDetail(kbId) {
  router.push(`/rag/kb/${kbId}`);
}

async function renameKB(kb) {
  const newName = prompt("输入新名称", kb.name);
  if (!newName || newName === kb.name) return;
  try {
    await withAiProcessing(
      {
        title: "AI 正在更新知识库",
        description: "会保存新的知识库名称",
        stages: ["校验名称", "更新知识库", "刷新列表"]
      },
      async () => updateKnowledgeBase(kb.id, { name: newName, description: kb.description })
    );
    kbStatus.value = "知识库已更名";
    await loadKnowledgeBases();
  } catch (_) {
    kbStatus.value = "更名失败";
  }
}

async function removeKB(kbId) {
  if (!confirm("确定要删除该知识库吗？相关文档将一并删除。")) return;
  try {
    await withAiProcessing(
      {
        title: "AI 正在删除知识库",
        description: "会同时清理关联文档与向量切片",
        stages: ["校验权限", "删除文档与切片", "删除知识库"]
      },
      async () => deleteKnowledgeBase(kbId)
    );
    kbStatus.value = "知识库已删除";
    await loadKnowledgeBases();
  } catch (_) {
    kbStatus.value = "删除失败";
  }
}

onMounted(loadKnowledgeBases);

onUnmounted(() => {
  clearAiProcessingTimers();
});
</script>

<style scoped>
.rag-entry-page {
  background: #f4f7f2;
}

.entry-hero {
  border-radius: 26px;
  border: 1px solid #d9e6d7;
  box-shadow: 0 12px 40px rgba(36, 64, 45, 0.08);
  padding: 24px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 16px;
  text-align: left;
}

.entry-hero-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  border: 1px solid #dce9da;
  background: #f7fbf6;
  color: #4c6b53;
  padding: 4px 12px;
  font-size: 12px;
  margin-bottom: 10px;
}

.entry-hero h1 {
  margin: 0;
}

.entry-hero p {
  margin: 8px 0 0;
  color: #5f6f67;
  max-width: 760px;
}

.hero-guide {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed #d8e4d5;
  color: #607269;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
}

.entry-layout {
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(320px, 0.7fr) minmax(0, 1.3fr);
}

.entry-card {
  border-radius: 20px;
  border: 1px solid #d9e6d7;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.entry-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.entry-head h3 {
  margin: 0;
}

.entry-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kb-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 540px;
  overflow: auto;
  padding-right: 2px;
}

.kb-item {
  border: 1px solid #e4ebe2;
  border-radius: 14px;
  background: #fcfdfc;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kb-main p {
  margin: 4px 0 0;
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

.status-text {
  margin: 0;
  color: #5f7269;
}

textarea,
input,
select {
  width: 100%;
}

@media (max-width: 980px) {
  .entry-hero {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    margin-left: 0;
    justify-content: flex-start;
  }

  .entry-layout {
    grid-template-columns: 1fr;
  }

  .kb-list {
    max-height: none;
  }
}
</style>
