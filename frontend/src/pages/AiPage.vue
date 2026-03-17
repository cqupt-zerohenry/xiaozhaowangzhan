<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>AI 助手</h1>
          <p>岗位匹配、企业初筛、学习内容模拟面试一体化。</p>
        </div>
        <div class="hero-right">
          <span class="tag mono">RAG + Interview Workflow</span>
          <button class="btn btn-outline" @click="refreshRoleData">刷新 AI 数据</button>
        </div>
      </div>
    </section>

    <section>
      <div class="container ai-grid">
        <div class="card ai-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <strong>{{ tab.title }}</strong>
            <span>{{ tab.desc }}</span>
          </button>
          <div class="ai-summary">
            <h3>AI 使用建议</h3>
            <ul>
              <li>企业先配置题型模板，再做候选人初筛。</li>
              <li>学生上传学习内容后做模拟面试更贴近当前能力。</li>
              <li>保留历史会话，便于复盘与改进。</li>
            </ul>
          </div>
        </div>

        <div class="card ai-panel">
          <div v-if="activeTab === 'match'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>岗位匹配</h2>
                <p>输入技能后自动计算匹配度与差距。</p>
              </div>
              <button class="chip" @click="applyMatchPreset">填充示例</button>
            </div>
            <textarea v-model="matchSkills" rows="3" placeholder="技能，如 Linux, Docker, Kubernetes"></textarea>
            <button class="btn" @click="runRecommend">开始匹配</button>
            <div v-if="matchResult" class="result-grid">
              <div class="result-card" v-for="match in matchResult.matches" :key="match.job_id">
                <div class="result-head">
                  <strong>{{ match.job_name }}</strong>
                  <span class="mono">总分 {{ match.final_score }}%</span>
                </div>
                <div class="progress">
                  <div class="progress-bar" :style="{ width: match.final_score + '%' }"></div>
                </div>
                <p class="mono">内容得分：{{ match.content_score }}%</p>
                <p class="mono">协同得分：{{ match.collaborative_score }}%</p>
                <p class="mono">匹配技能：{{ match.matched_skills.join(', ') || '暂无' }}</p>
                <p class="mono">缺失技能：{{ match.missing_skills.join(', ') || '暂无' }}</p>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'rag'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>职业 RAG 助手</h2>
                <p>问答 + 学习路径 + 技能树。</p>
              </div>
            </div>
            <textarea v-model="ragQuestion" rows="3" placeholder="例如：SRE 需要学习什么？"></textarea>
            <button class="btn" @click="runRag">提问</button>
            <div v-if="ragAnswer" class="result-block">
              <p>{{ ragAnswer.answer }}</p>
              <div class="result-tags">
                <span class="tag" v-for="path in ragAnswer.learning_path" :key="path">{{ path }}</span>
              </div>
              <p class="mono">技能树：{{ ragAnswer.skill_tree.join(' | ') }}</p>
            </div>
          </div>

          <div v-else-if="activeTab === 'interview'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 面试官（快速版）</h2>
                <p>快速生成面试问题与评价重点。</p>
              </div>
            </div>
            <input v-model="interviewRole" placeholder="岗位名称" />
            <button class="btn" @click="runInterview">生成问题</button>
            <div v-if="interviewPack" class="result-block">
              <ul>
                <li v-for="question in interviewPack.questions" :key="question">{{ question }}</li>
              </ul>
              <p>{{ interviewPack.evaluation }}</p>
            </div>
          </div>

          <div v-else-if="activeTab === 'company-template'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>企业题型模板</h2>
                <p>设置岗位题型，用于 AI 初筛。</p>
              </div>
            </div>
            <div class="form-grid">
              <input v-model="templateForm.name" placeholder="模板名称（如 Java 后端初筛）" />
              <input v-model="templateForm.job_title" placeholder="目标岗位" />
              <input v-model="templateForm.question_types_input" placeholder="题型，逗号分隔：技术基础,项目经验,场景分析" />
              <select v-model="templateForm.difficulty">
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
              <input v-model.number="templateForm.question_count" type="number" min="1" max="20" placeholder="题目数量" />
            </div>
            <textarea v-model="templateForm.scoring_rules" rows="3" placeholder="评分规则（可选）"></textarea>
            <div class="actions">
              <button class="btn" @click="saveTemplate">保存模板</button>
              <button class="btn btn-outline" @click="resetTemplateForm">清空</button>
            </div>
            <p v-if="templateStatus" class="mono">{{ templateStatus }}</p>

            <div class="list-wrap">
              <div class="list-header">
                <h3>我的模板</h3>
              </div>
              <div v-if="templates.length === 0" class="mono">暂无模板</div>
              <div v-else class="list">
                <div class="list-item" v-for="item in templates" :key="item.id">
                  <div>
                    <strong>{{ item.name }}</strong>
                    <p class="mono">{{ item.job_title }} · {{ item.difficulty }} · {{ item.question_count }} 题</p>
                    <p class="mono">题型：{{ (item.question_types || []).join(', ') || '默认' }}</p>
                  </div>
                  <div class="actions">
                    <button class="btn btn-outline" @click="fillTemplateForm(item)">编辑</button>
                    <button class="btn btn-outline" @click="removeTemplate(item.id)">删除</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'company-screening'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 初筛</h2>
                <p>基于题型模板自动生成初筛问题并输出建议。</p>
              </div>
            </div>
            <select v-model.number="selectedTemplateId">
              <option :value="0">选择模板</option>
              <option v-for="item in templates" :key="item.id" :value="item.id">
                {{ item.name }}（{{ item.job_title }}）
              </option>
            </select>
            <div class="form-grid">
              <input v-model="screeningCandidate.candidate_name" placeholder="候选人姓名（可选）" />
              <input
                v-model="screeningCandidate.candidate_skills_input"
                placeholder="候选人技能，逗号分隔（如 Java, Redis）"
              />
            </div>
            <textarea v-model="screeningCandidate.candidate_summary" rows="3" placeholder="候选人简介"></textarea>
            <textarea v-model="screeningCandidate.candidate_experience" rows="4" placeholder="项目或实习经历"></textarea>
            <button class="btn" @click="runScreening">执行初筛</button>

            <div v-if="screeningPack" class="result-block">
              <p class="mono">会话 #{{ screeningPack.session_id }} · 得分 {{ screeningPack.score }}</p>
              <p>{{ screeningPack.evaluation }}</p>
              <p class="mono">结论：{{ screeningPack.recommendation }}</p>
              <p class="mono">关注点：{{ (screeningPack.focus_areas || []).join('、') }}</p>
              <ul>
                <li v-for="question in screeningPack.questions" :key="question">{{ question }}</li>
              </ul>
            </div>

            <div class="list-wrap">
              <div class="list-header">
                <h3>近期初筛记录</h3>
                <button class="chip" @click="loadSessions('screening')">刷新</button>
              </div>
              <div v-if="sessions.length === 0" class="mono">暂无记录</div>
              <div v-else class="list">
                <div class="list-item" v-for="item in sessions" :key="item.id">
                  <div>
                    <strong>会话 #{{ item.id }}</strong>
                    <p class="mono">{{ item.session_type }} · {{ formatTime(item.create_time) }}</p>
                  </div>
                  <span class="tag mono">{{ (item.generated_questions || []).length }} 题</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'student-mock-upload'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>学习内容模拟面试</h2>
                <p>上传或粘贴学习内容，生成定制面试问题与反馈。</p>
              </div>
            </div>
            <div class="form-grid">
              <input v-model="mockUploadForm.job_title" placeholder="目标岗位" />
              <input v-model="mockUploadForm.learning_focus_input" placeholder="学习重点（逗号分隔，可选）" />
              <input v-model="mockUploadForm.question_types_input" placeholder="题型（逗号分隔，可选）" />
              <select v-model="mockUploadForm.difficulty">
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
              <input v-model.number="mockUploadForm.question_count" type="number" min="1" max="20" placeholder="题目数量" />
            </div>
            <label class="upload-label">
              上传学习内容文件（txt/md）
              <input type="file" accept=".txt,.md" @change="onLearningFileChange" />
            </label>
            <textarea
              v-model="mockUploadForm.learning_content"
              rows="8"
              placeholder="粘贴学习笔记、课程摘要、项目记录等内容"
            ></textarea>
            <button class="btn" @click="runStudentMockUpload">生成模拟面试</button>

            <div v-if="mockUploadPack" class="result-block">
              <p class="mono">会话 #{{ mockUploadPack.session_id }}</p>
              <ul>
                <li v-for="question in mockUploadPack.questions" :key="question">{{ question }}</li>
              </ul>
              <p>{{ mockUploadPack.feedback }}</p>
              <p class="mono">优势：{{ (mockUploadPack.strengths || []).join('；') }}</p>
              <p class="mono">改进：{{ (mockUploadPack.improvements || []).join('；') }}</p>
              <p class="mono">下一步：{{ (mockUploadPack.next_actions || []).join('；') }}</p>
            </div>

            <div class="list-wrap">
              <div class="list-header">
                <h3>近期模拟记录</h3>
                <button class="chip" @click="loadSessions('mock')">刷新</button>
              </div>
              <div v-if="sessions.length === 0" class="mono">暂无记录</div>
              <div v-else class="list">
                <div class="list-item" v-for="item in sessions" :key="item.id">
                  <div>
                    <strong>会话 #{{ item.id }}</strong>
                    <p class="mono">{{ item.session_type }} · {{ formatTime(item.create_time) }}</p>
                  </div>
                  <span class="tag mono">{{ (item.generated_questions || []).length }} 题</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 模拟面试（快速版）</h2>
                <p>快速生成问题与建议。</p>
              </div>
            </div>
            <input v-model="mockRole" placeholder="目标岗位" />
            <button class="btn" @click="runMock">开始模拟</button>
            <div v-if="mockPack" class="result-block">
              <ul>
                <li v-for="question in mockPack.questions" :key="question">{{ question }}</li>
              </ul>
              <p>{{ mockPack.feedback }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import {
  createInterviewTemplate,
  deleteInterviewTemplate,
  fetchInterviewSessions,
  fetchInterviewTemplates,
  interview,
  jobRecommend,
  mockInterview,
  rag,
  screeningInterview,
  studentMockUpload,
  updateInterviewTemplate
} from "../services/api";
import { useAuth } from "../store/auth";

const auth = useAuth();
const role = computed(() => auth.role.value);
const canManageTemplates = computed(() => role.value === "company");
const canStudentMockUpload = computed(() => role.value === "student");

const tabs = computed(() => {
  const base = [
    { key: "match", title: "岗位匹配", desc: "技能匹配与差距" },
    { key: "rag", title: "职业 RAG", desc: "学习路径与技能树" },
    { key: "interview", title: "AI 面试官", desc: "快速问题与评价" }
  ];
  if (canManageTemplates.value) {
    base.push({ key: "company-template", title: "题型模板", desc: "企业题型配置" });
    base.push({ key: "company-screening", title: "AI 初筛", desc: "模板化初筛" });
  }
  if (canStudentMockUpload.value) {
    base.push({ key: "student-mock-upload", title: "学习内容模拟", desc: "上传学习内容" });
  }
  base.push({ key: "mock", title: "快速模拟", desc: "简版模拟面试" });
  return base;
});

const activeTab = ref("match");
watch(
  tabs,
  (nextTabs) => {
    if (!nextTabs.find((tab) => tab.key === activeTab.value)) {
      activeTab.value = nextTabs[0]?.key || "match";
    }
  },
  { immediate: true }
);

const matchSkills = ref("Linux, Docker, Kubernetes");
const ragQuestion = ref("成为 SRE 需要学习什么？");
const interviewRole = ref("后端开发实习生");
const mockRole = ref("DevOps 工程师");
const matchResult = ref(null);
const ragAnswer = ref(null);
const interviewPack = ref(null);
const mockPack = ref(null);

const templates = ref([]);
const selectedTemplateId = ref(0);
const templateStatus = ref("");
const templateForm = ref({
  id: null,
  name: "",
  job_title: "",
  question_types_input: "技术基础,项目经验,场景分析",
  difficulty: "medium",
  question_count: 5,
  scoring_rules: ""
});
const screeningCandidate = ref({
  candidate_name: "",
  candidate_summary: "",
  candidate_skills_input: "",
  candidate_experience: ""
});
const screeningPack = ref(null);

const mockUploadForm = ref({
  job_title: "后端开发实习生",
  learning_content: "",
  learning_focus_input: "",
  question_types_input: "技术基础,项目经验,场景分析",
  difficulty: "medium",
  question_count: 5
});
const mockUploadPack = ref(null);
const sessions = ref([]);

function parseList(text) {
  return (text || "")
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatTime(value) {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
}

function applyMatchPreset() {
  matchSkills.value = "Linux, Docker, Kubernetes";
}

async function runRecommend() {
  try {
    matchResult.value = await jobRecommend({
      student_id: auth.user.value?.id || null,
      skills: parseList(matchSkills.value)
    });
  } catch (err) {
    matchResult.value = null;
  }
}

async function runRag() {
  try {
    ragAnswer.value = await rag({ question: ragQuestion.value });
  } catch (err) {
    ragAnswer.value = null;
  }
}

async function runInterview() {
  try {
    interviewPack.value = await interview({ job_title: interviewRole.value, skills: [] });
  } catch (err) {
    interviewPack.value = null;
  }
}

async function runMock() {
  try {
    mockPack.value = await mockInterview({ job_title: mockRole.value });
  } catch (err) {
    mockPack.value = null;
  }
}

async function loadTemplates() {
  if (!canManageTemplates.value) return;
  try {
    templates.value = await fetchInterviewTemplates();
    if (!selectedTemplateId.value && templates.value.length > 0) {
      selectedTemplateId.value = templates.value[0].id;
    }
  } catch (err) {
    templates.value = [];
  }
}

function resetTemplateForm() {
  templateForm.value = {
    id: null,
    name: "",
    job_title: "",
    question_types_input: "技术基础,项目经验,场景分析",
    difficulty: "medium",
    question_count: 5,
    scoring_rules: ""
  };
}

function fillTemplateForm(item) {
  templateForm.value = {
    id: item.id,
    name: item.name,
    job_title: item.job_title,
    question_types_input: (item.question_types || []).join(","),
    difficulty: item.difficulty || "medium",
    question_count: item.question_count || 5,
    scoring_rules: item.scoring_rules || ""
  };
}

async function saveTemplate() {
  if (!templateForm.value.name || !templateForm.value.job_title) {
    templateStatus.value = "请先填写模板名称和岗位";
    return;
  }

  const payload = {
    name: templateForm.value.name,
    job_title: templateForm.value.job_title,
    question_types: parseList(templateForm.value.question_types_input),
    difficulty: templateForm.value.difficulty,
    question_count: Number(templateForm.value.question_count) || 5,
    scoring_rules: templateForm.value.scoring_rules
  };

  try {
    if (templateForm.value.id) {
      await updateInterviewTemplate(templateForm.value.id, payload);
      templateStatus.value = "模板已更新";
    } else {
      await createInterviewTemplate(payload);
      templateStatus.value = "模板已创建";
    }
    resetTemplateForm();
    await loadTemplates();
  } catch (err) {
    templateStatus.value = "保存失败";
  }
}

async function removeTemplate(id) {
  try {
    await deleteInterviewTemplate(id);
    templateStatus.value = "模板已删除";
    if (selectedTemplateId.value === id) selectedTemplateId.value = 0;
    await loadTemplates();
  } catch (err) {
    templateStatus.value = "删除失败";
  }
}

async function runScreening() {
  if (!selectedTemplateId.value) {
    templateStatus.value = "请先选择模板";
    return;
  }
  try {
    screeningPack.value = await screeningInterview({
      template_id: selectedTemplateId.value,
      candidate_name: screeningCandidate.value.candidate_name,
      candidate_summary: screeningCandidate.value.candidate_summary,
      candidate_skills: parseList(screeningCandidate.value.candidate_skills_input),
      candidate_experience: screeningCandidate.value.candidate_experience
    });
    await loadSessions("screening");
  } catch (err) {
    screeningPack.value = null;
  }
}

function onLearningFileChange(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    mockUploadForm.value.learning_content = String(reader.result || "");
  };
  reader.readAsText(file, "utf-8");
}

async function runStudentMockUpload() {
  if (!mockUploadForm.value.learning_content || mockUploadForm.value.learning_content.length < 10) {
    return;
  }
  try {
    mockUploadPack.value = await studentMockUpload({
      job_title: mockUploadForm.value.job_title,
      learning_content: mockUploadForm.value.learning_content,
      learning_focus: parseList(mockUploadForm.value.learning_focus_input),
      question_types: parseList(mockUploadForm.value.question_types_input),
      difficulty: mockUploadForm.value.difficulty,
      question_count: Number(mockUploadForm.value.question_count) || 5
    });
    await loadSessions("mock");
  } catch (err) {
    mockUploadPack.value = null;
  }
}

async function loadSessions(sessionType = "") {
  try {
    sessions.value = await fetchInterviewSessions({
      session_type: sessionType || undefined,
      limit: 10
    });
  } catch (err) {
    sessions.value = [];
  }
}

async function refreshRoleData() {
  if (canManageTemplates.value) {
    await loadTemplates();
    await loadSessions("screening");
    return;
  }
  if (canStudentMockUpload.value) {
    await loadSessions("mock");
    return;
  }
  await loadSessions();
}

onMounted(async () => {
  await refreshRoleData();
});
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

.hero-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.ai-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.35fr) minmax(0, 1fr);
  gap: 24px;
}

.ai-tabs {
  padding: 20px;
  gap: 12px;
}

.tab {
  text-align: left;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #fff;
  cursor: pointer;
}

.tab strong {
  font-size: 15px;
}

.tab span {
  color: var(--muted);
  font-size: 12px;
}

.tab.active {
  border-color: rgba(24, 160, 88, 0.4);
  background: rgba(24, 160, 88, 0.1);
}

.ai-summary {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
}

.ai-summary ul {
  padding-left: 18px;
  color: var(--muted);
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.result-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.result-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress {
  height: 8px;
  background: rgba(24, 160, 88, 0.1);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #8ce0b6);
}

.result-block {
  border: 1px dashed var(--line);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.list-wrap {
  border-top: 1px dashed var(--line);
  padding-top: 12px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.upload-label {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: var(--muted);
}

textarea,
input,
select {
  width: 100%;
}

@media (max-width: 900px) {
  .ai-grid {
    grid-template-columns: 1fr;
  }
}
</style>
