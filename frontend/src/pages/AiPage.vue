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
          <div v-if="activeTab === 'knowledge-base'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>知识库管理</h2>
                <p>上传文档或粘贴内容构建 RAG 知识库，用于面试出题和职业问答。</p>
              </div>
            </div>
            <div class="form-grid">
              <input v-model="kbForm.name" placeholder="知识库名称（如：后端技术文档）" />
              <input v-model="kbForm.description" placeholder="描述（可选）" />
              <button class="btn" @click="createKB">创建知识库</button>
            </div>
            <p v-if="kbStatus" class="mono">{{ kbStatus }}</p>

            <div class="list-wrap">
              <h3>我的知识库</h3>
              <div v-if="knowledgeBases.length === 0" class="mono">暂无知识库，请先创建</div>
              <div v-else class="list">
                <div
                  class="list-item"
                  :class="{ active: selectedKbId === kb.id }"
                  v-for="kb in knowledgeBases"
                  :key="kb.id"
                  @click="selectKB(kb.id)"
                  style="cursor:pointer"
                >
                  <div>
                    <strong>{{ kb.name }}</strong>
                    <p class="mono">{{ kb.description || '无描述' }}</p>
                  </div>
                  <div class="actions">
                    <button class="btn btn-outline" @click.stop="renameKB(kb)">改名</button>
                    <button class="btn btn-outline" @click.stop="removeKB(kb.id)">删除</button>
                  </div>
                </div>
              </div>
            </div>

            <template v-if="selectedKbId">
              <div class="divider"></div>
              <h3>添加文档到知识库</h3>
              <div class="form-grid">
                <input v-model="kbDocForm.title" placeholder="文档标题" />
              </div>
              <textarea v-model="kbDocForm.content" rows="6" placeholder="粘贴知识内容（技术文档、面试题库、课程笔记等）"></textarea>
              <div class="actions">
                <button class="btn" @click="addDocPaste">添加文档</button>
                <label class="upload-label">
                  上传文件（txt/md）
                  <input type="file" accept=".txt,.md" @change="uploadDoc" />
                </label>
              </div>

              <div class="list-wrap">
                <h3>文档列表</h3>
                <div v-if="kbDocuments.length === 0" class="mono">暂无文档</div>
                <div v-else class="list">
                  <div class="list-item" v-for="doc in kbDocuments" :key="doc.id">
                    <div>
                      <strong>{{ doc.title }}</strong>
                      <p class="mono">{{ doc.source_type }} · {{ doc.chunk_count }} 个切片 · {{ doc.status }}</p>
                    </div>
                    <button class="btn btn-outline" @click="removeDoc(doc.id)">删除</button>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div v-else-if="activeTab === 'match'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>岗位匹配</h2>
                <p>输入技能后自动计算匹配度与差距。</p>
              </div>
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
                <!-- Score breakdown bar -->
                <div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden; margin: 8px 0;">
                  <div :style="{ width: Math.max(match.content_score, 5) + '%', background: '#18a058' }" :title="'内容得分 ' + match.content_score + '%'"></div>
                  <div :style="{ width: Math.max(match.collaborative_score, 5) + '%', background: '#4dabf7' }" :title="'协同得分 ' + match.collaborative_score + '%'"></div>
                </div>
                <div style="display: flex; gap: 16px; font-size: 12px; margin-bottom: 8px;">
                  <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#18a058;margin-right:4px;"></span>内容 {{ match.content_score }}%</span>
                  <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#4dabf7;margin-right:4px;"></span>协同 {{ match.collaborative_score }}%</span>
                </div>
                <!-- Skill tags -->
                <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">
                  <span v-for="s in match.matched_skills" :key="s" class="tag" style="background: rgba(24,160,88,0.12); color: #18a058; font-size: 11px;">{{ s }}</span>
                  <span v-for="s in match.missing_skills" :key="'m'+s" class="tag" style="background: rgba(229,62,62,0.08); color: #e53e3e; font-size: 11px; text-decoration: line-through;">{{ s }}</span>
                </div>
                <!-- Expandable reason -->
                <details v-if="match.reason" style="margin-top: 4px;">
                  <summary style="cursor: pointer; font-size: 13px; color: #18a058;">为什么推荐？</summary>
                  <p class="mono" style="white-space:pre-wrap;font-size:12px;color:var(--muted);margin-top:6px;padding:8px;background:#f8faf9;border-radius:8px">{{ match.reason }}</p>
                </details>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'rag'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>职业 RAG 助手</h2>
                <p>基于知识库检索回答职业问题。</p>
              </div>
            </div>
            <select v-model="ragKbId">
              <option :value="null">全部知识库（默认）</option>
              <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
            </select>
            <textarea v-model="ragQuestion" rows="3" placeholder="例如：SRE 需要学习什么？"></textarea>
            <button class="btn" @click="runRag">提问</button>
            <div v-if="ragAnswer" class="result-block">
              <p style="white-space:pre-wrap">{{ ragAnswer.answer }}</p>
              <div class="result-tags">
                <span class="tag" v-for="path in ragAnswer.learning_path" :key="path">{{ path }}</span>
              </div>
              <p class="mono">技能树：{{ ragAnswer.skill_tree.join(' | ') }}</p>
              <template v-if="ragAnswer.sources && ragAnswer.sources.length > 0">
                <div class="divider"></div>
                <h4>检索来源</h4>
                <div class="list">
                  <div class="list-item" v-for="(src, idx) in ragAnswer.sources" :key="idx">
                    <div>
                      <strong>{{ src.document_title }}</strong>
                      <p class="mono">{{ src.chunk_content.slice(0, 150) }}{{ src.chunk_content.length > 150 ? '...' : '' }}</p>
                    </div>
                    <span class="tag mono">{{ (src.relevance_score * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </template>
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
            <div class="form-grid">
              <select v-model.number="selectedTemplateId">
                <option :value="0">选择模板</option>
                <option v-for="item in templates" :key="item.id" :value="item.id">
                  {{ item.name }}（{{ item.job_title }}）
                </option>
              </select>
              <select v-model="screeningKbId">
                <option :value="null">不使用知识库</option>
                <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
              </select>
            </div>
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
              <div v-if="screeningPack.dimension_scores && screeningPack.dimension_scores.length" class="dimension-grid">
                <div class="dimension-item" v-for="dim in screeningPack.dimension_scores" :key="dim.dimension">
                  <div class="dim-header">
                    <span>{{ dim.dimension }}</span>
                    <strong>{{ dim.score }}分</strong>
                  </div>
                  <div class="progress"><div class="progress-bar" :style="{ width: dim.score + '%' }"></div></div>
                  <p class="mono" style="font-size:11px">{{ dim.comment }}</p>
                </div>
              </div>
              <ul>
                <li v-for="question in screeningPack.questions" :key="question">{{ question }}</li>
              </ul>
            </div>

            <div class="list-wrap">
              <div class="list-header">
                <h3>近期初筛记录</h3>
                <button class="chip" @click="loadSessions('screening')">刷新</button>
              </div>
              <div v-if="screeningSessions.length === 0" class="mono">暂无记录</div>
              <div v-else class="list">
                <div class="list-item" v-for="item in screeningSessions" :key="item.id">
                  <div>
                    <strong>会话 #{{ item.id }}</strong>
                    <p class="mono">{{ item.session_type }} · {{ formatTime(item.create_time) }}</p>
                  </div>
                  <span class="tag mono">{{ (item.generated_questions || []).length }} 题</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'resume-optimize'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 简历优化建议</h2>
                <p>输入目标岗位，AI 分析你的简历并给出优化建议。</p>
              </div>
            </div>
            <input v-model="resumeJobTitle" placeholder="目标岗位（如：后端开发工程师）" />
            <button class="btn" @click="runResumeOptimize" :disabled="resumeLoading">
              {{ resumeLoading ? '分析中...' : '开始分析' }}
            </button>
            <div v-if="resumeResult" class="result-block">
              <p><strong>总评：</strong>{{ resumeResult.summary }}</p>
              <div v-if="resumeResult.strengths.length">
                <strong>优势</strong>
                <div class="tags" style="margin-top:6px">
                  <span class="tag" v-for="s in resumeResult.strengths" :key="s">{{ s }}</span>
                </div>
              </div>
              <div v-if="resumeResult.suggestions.length">
                <strong>改进建议</strong>
                <ul>
                  <li v-for="s in resumeResult.suggestions" :key="s">{{ s }}</li>
                </ul>
              </div>
              <div v-if="resumeResult.missing_skills.length">
                <strong>建议补充的技能</strong>
                <div class="tags" style="margin-top:6px">
                  <span class="tag" v-for="s in resumeResult.missing_skills" :key="s" style="background:rgba(255,107,53,0.1);color:#ff6b35">{{ s }}</span>
                </div>
              </div>
              <div v-if="resumeResult.bio_rewrite">
                <strong>自我评价改写建议</strong>
                <p style="white-space:pre-wrap;background:#f8faf9;padding:12px;border-radius:10px;margin-top:6px">{{ resumeResult.bio_rewrite }}</p>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'student-mock-upload'" class="panel-content">
            <div class="panel-header">
              <div>
                <h2>学习内容模拟面试</h2>
                <p>上传或粘贴学习内容，结合知识库生成定制面试问题与反馈。</p>
              </div>
            </div>
            <div class="form-grid">
              <input v-model="mockUploadForm.job_title" placeholder="目标岗位" />
              <select v-model="mockKbId">
                <option :value="null">不使用知识库</option>
                <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
              </select>
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
              <div v-if="mockUploadPack.dimension_scores && mockUploadPack.dimension_scores.length" class="dimension-grid">
                <div class="dimension-item" v-for="dim in mockUploadPack.dimension_scores" :key="dim.dimension">
                  <div class="dim-header">
                    <span>{{ dim.dimension }}</span>
                    <strong>{{ dim.score }}分</strong>
                  </div>
                  <div class="progress"><div class="progress-bar" :style="{ width: dim.score + '%' }"></div></div>
                  <p class="mono" style="font-size:11px">{{ dim.comment }}</p>
                </div>
              </div>
            </div>

            <div class="list-wrap">
              <div class="list-header">
                <h3>近期模拟记录</h3>
                <button class="chip" @click="loadSessions('mock')">刷新</button>
              </div>
              <div v-if="mockSessions.length === 0" class="mono">暂无记录</div>
              <div v-else class="list">
                <div class="list-item" v-for="item in mockSessions" :key="item.id">
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
  addKBDocumentPaste,
  createInterviewTemplate,
  createKnowledgeBase,
  deleteInterviewTemplate,
  deleteKBDocument,
  deleteKnowledgeBase,
  updateKnowledgeBase,
  fetchInterviewSessions,
  fetchInterviewTemplates,
  fetchKBDocuments,
  fetchKnowledgeBases,
  interview,
  jobRecommend,
  mockInterview,
  rag,
  resumeOptimize,
  screeningInterview,
  studentMockUpload,
  updateInterviewTemplate,
  uploadKBDocument
} from "../services/api";
import { useAuth } from "../store/auth";
import toast from '../utils/toast';

const auth = useAuth();
const role = computed(() => auth.role.value);
const canManageTemplates = computed(() => role.value === "company");
const canStudentMockUpload = computed(() => role.value === "student");

const tabs = computed(() => {
  const base = [
    { key: "knowledge-base", title: "知识库", desc: "管理 RAG 知识库" },
    { key: "match", title: "岗位匹配", desc: "技能匹配与差距" },
    { key: "rag", title: "职业 RAG", desc: "学习路径与技能树" },
    { key: "interview", title: "AI 面试官", desc: "快速问题与评价" }
  ];
  if (canManageTemplates.value) {
    base.push({ key: "company-template", title: "题型模板", desc: "企业题型配置" });
    base.push({ key: "company-screening", title: "AI 初筛", desc: "模板化初筛" });
  }
  if (canStudentMockUpload.value) {
    base.push({ key: "resume-optimize", title: "简历优化", desc: "AI 优化建议" });
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

const matchSkills = ref("");
const ragQuestion = ref("");
const interviewRole = ref("");
const mockRole = ref("");
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
  question_types_input: "",
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
  job_title: "",
  learning_content: "",
  learning_focus_input: "",
  question_types_input: "",
  difficulty: "medium",
  question_count: 5
});
const mockUploadPack = ref(null);
const screeningSessions = ref([]);
const mockSessions = ref([]);

// Knowledge Base state
const knowledgeBases = ref([]);
const kbForm = ref({ name: "", description: "" });
const kbDocForm = ref({ title: "", content: "" });
const selectedKbId = ref(null);
const kbDocuments = ref([]);
const kbStatus = ref("");
const ragKbId = ref(null);
const screeningKbId = ref(null);
const mockKbId = ref(null);
const resumeJobTitle = ref('');
const resumeResult = ref(null);
const resumeLoading = ref(false);

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
    ragAnswer.value = await rag({
      question: ragQuestion.value,
      kb_id: ragKbId.value || undefined,
      top_k: 5
    });
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
    question_types_input: "",
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
  if (!confirm('确定要删除该面试模板吗？')) return;
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
      candidate_experience: screeningCandidate.value.candidate_experience,
      kb_id: screeningKbId.value || undefined
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
  mockUploadForm.value.learning_content = (mockUploadForm.value.learning_content || '').trim();
  if (mockUploadForm.value.learning_content.length < 10) {
    toast.warn('学习内容至少需要 10 个字符');
    return;
  }
  try {
    mockUploadPack.value = await studentMockUpload({
      job_title: mockUploadForm.value.job_title,
      learning_content: mockUploadForm.value.learning_content,
      learning_focus: parseList(mockUploadForm.value.learning_focus_input),
      question_types: parseList(mockUploadForm.value.question_types_input),
      difficulty: mockUploadForm.value.difficulty,
      question_count: Number(mockUploadForm.value.question_count) || 5,
      kb_id: mockKbId.value || undefined
    });
    await loadSessions("mock");
  } catch (err) {
    mockUploadPack.value = null;
  }
}

async function loadSessions(sessionType = "") {
  try {
    const data = await fetchInterviewSessions({
      session_type: sessionType || undefined,
      limit: 10
    });
    if (sessionType === "screening") {
      screeningSessions.value = data;
    } else if (sessionType === "mock") {
      mockSessions.value = data;
    } else {
      screeningSessions.value = data;
      mockSessions.value = data;
    }
  } catch (err) {
    if (sessionType === "screening") {
      screeningSessions.value = [];
    } else if (sessionType === "mock") {
      mockSessions.value = [];
    }
  }
}

async function runResumeOptimize() {
  if (!resumeJobTitle.value) { toast.warn('请输入目标岗位'); return; }
  resumeLoading.value = true;
  try {
    resumeResult.value = await resumeOptimize({ job_title: resumeJobTitle.value });
  } catch (e) {
    toast.error('简历优化分析失败');
    resumeResult.value = null;
  } finally {
    resumeLoading.value = false;
  }
}

// --- Knowledge Base functions ---
async function loadKnowledgeBases() {
  try {
    knowledgeBases.value = await fetchKnowledgeBases();
  } catch (e) {
    knowledgeBases.value = [];
  }
}

async function createKB() {
  if (!kbForm.value.name) { kbStatus.value = "请输入知识库名称"; return; }
  try {
    await createKnowledgeBase(kbForm.value);
    kbForm.value = { name: "", description: "" };
    kbStatus.value = "知识库已创建";
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "创建失败"; }
}

async function renameKB(kb) {
  const newName = prompt('输入新名称', kb.name);
  if (!newName || newName === kb.name) return;
  try {
    await updateKnowledgeBase(kb.id, { name: newName, description: kb.description });
    kbStatus.value = '知识库已更名';
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = '更名失败'; }
}

async function removeKB(kbId) {
  if (!confirm('确定要删除该知识库吗？相关文档将一并删除。')) return;
  try {
    await deleteKnowledgeBase(kbId);
    if (selectedKbId.value === kbId) { selectedKbId.value = null; kbDocuments.value = []; }
    kbStatus.value = "知识库已删除";
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "删除失败"; }
}

async function selectKB(kbId) {
  selectedKbId.value = kbId;
  try {
    kbDocuments.value = await fetchKBDocuments(kbId);
  } catch (e) { kbDocuments.value = []; }
}

async function addDocPaste() {
  if (!selectedKbId.value) { kbStatus.value = "请先选择知识库"; return; }
  if (!kbDocForm.value.title || !kbDocForm.value.content) { kbStatus.value = "请填写标题和内容"; return; }
  try {
    await addKBDocumentPaste(selectedKbId.value, kbDocForm.value);
    kbDocForm.value = { title: "", content: "" };
    kbStatus.value = "文档已添加并完成向量化";
    await selectKB(selectedKbId.value);
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "添加失败"; }
}

async function uploadDoc(event) {
  const file = event?.target?.files?.[0];
  if (!file || !selectedKbId.value) return;
  try {
    await uploadKBDocument(selectedKbId.value, file);
    kbStatus.value = "文件已上传并完成向量化";
    await selectKB(selectedKbId.value);
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "上传失败"; }
}

async function removeDoc(docId) {
  if (!selectedKbId.value) return;
  try {
    await deleteKBDocument(selectedKbId.value, docId);
    kbStatus.value = "文档已删除";
    await selectKB(selectedKbId.value);
  } catch (e) { kbStatus.value = "删除失败"; }
}

async function refreshRoleData() {
  await loadKnowledgeBases();
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

.list-item.active {
  border-color: rgba(24, 160, 88, 0.4);
  background: rgba(24, 160, 88, 0.08);
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 8px 0;
}

h4 {
  margin: 0 0 8px;
  font-size: 14px;
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

.dimension-grid {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

@media (max-width: 900px) {
  .ai-grid {
    grid-template-columns: 1fr;
  }
}
</style>
