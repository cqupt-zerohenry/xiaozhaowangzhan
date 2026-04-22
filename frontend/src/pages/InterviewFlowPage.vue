<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>AI 模拟面试</h1>
            <p>选择岗位开始完整模拟，每道题限时作答并即时反馈。</p>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container container-narrow">
        <div v-if="stage === 'setup'" class="card stage-card">
          <h3>面试设置</h3>
          <label>目标岗位</label>
          <input v-model="jobTitle" placeholder="如：后端开发工程师" class="input" />
          <label>题目数量</label>
          <input v-model.number="questionCount" type="number" min="1" max="20" class="input count-input" />

          <div class="resume-config">
            <label class="toggle-line">
              <input v-model="useResumeContext" type="checkbox" />
              <span>结合简历定制问题（可选）</span>
            </label>
            <p class="mono">不上传简历时，系统仅根据岗位生成题目。</p>

            <div v-if="useResumeContext" class="resume-upload-block">
              <label class="file-picker" :class="{ 'is-disabled': loading || resumeParsing }">
                <span class="btn btn-outline file-picker-btn">选择简历文件</span>
                <span class="mono file-picker-name">{{ resumeFileName || '未选择文件（PDF / DOC / DOCX / TXT / MD）' }}</span>
                <input type="file" :disabled="loading || resumeParsing" accept=".pdf,.doc,.docx,.txt,.md" @change="onResumeFileChange" />
              </label>
              <p v-if="resumeFileName && resumeParsing" class="mono">正在解析：{{ resumeFileName }}</p>
              <p v-if="resumeParseError" class="resume-error mono">{{ resumeParseError }}</p>

              <div v-if="resumeProfile" class="resume-preview">
                <div class="preview-tags">
                  <span v-if="resumeProfile.name" class="tag mono">姓名：{{ resumeProfile.name }}</span>
                  <span v-if="resumeProfile.school" class="tag mono">学校：{{ resumeProfile.school }}</span>
                  <span v-if="resumeProfile.major" class="tag mono">专业：{{ resumeProfile.major }}</span>
                </div>
                <div v-if="resumeProfile.skills?.length" class="preview-tags">
                  <span class="mono">技能：</span>
                  <span v-for="item in resumeProfile.skills.slice(0, 10)" :key="item" class="tag mono">{{ item }}</span>
                </div>
                <div v-if="resumeProfile.experience_cards?.length" class="experience-list">
                  <div
                    v-for="(exp, idx) in resumeProfile.experience_cards.slice(0, 2)"
                    :key="`${exp.company || 'exp'}-${exp.position || 'role'}-${idx}`"
                    class="experience-card"
                  >
                    <div class="experience-head">
                      <strong>{{ exp.company || '项目/实习经历' }}</strong>
                      <span v-if="exp.period" class="tag mono">{{ exp.period }}</span>
                    </div>
                    <p class="mono experience-meta">{{ exp.meta || '岗位信息待补充' }}</p>
                    <div v-if="exp.projects?.length" class="experience-projects">
                      <span class="mono">项目亮点：</span>
                      <ul>
                        <li v-for="(proj, pIdx) in exp.projects.slice(0, 2)" :key="`${idx}-proj-${pIdx}`">{{ proj }}</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <div v-else-if="resumeProfile.experience?.length" class="mono">
                  经历摘要：{{ resumeProfile.experience.slice(0, 2).join('；') }}
                </div>
              </div>
            </div>
          </div>

          <button class="btn" :disabled="loading || resumeParsing" @click="startInterview">
            {{ loading ? '准备中...' : resumeParsing ? '解析简历中...' : '开始面试' }}
          </button>
          <AiProcessingOverlay
            :visible="processing.visible && stage === 'setup'"
            :title="processing.title"
            :description="processing.description"
            :progress="processing.progress"
            :stages="processing.stages"
            :stage-index="processing.stageIndex"
          />
        </div>

        <div v-if="stage === 'answering'" class="card stage-card">
          <div class="head-row">
            <h3>题目 {{ currentIndex + 1 }} / {{ questions.length }}</h3>
            <span class="tag timer-tag" :class="{ danger: timer <= 30 }">{{ formatTimer(timer) }}</span>
          </div>

          <div class="progress-bar"><div class="progress-fill" :style="{ width: (currentIndex / questions.length * 100) + '%' }"></div></div>

          <div class="question-box">{{ questions[currentIndex]?.question }}</div>
          <textarea v-model="currentAnswer" rows="6" class="input" placeholder="请输入你的回答..." :disabled="submitting"></textarea>

          <div class="actions-row">
            <button class="btn" :disabled="submitting || !currentAnswer.trim()" @click="submitAnswer">{{ submitting ? '提交中...' : '提交回答' }}</button>
            <button class="btn btn-outline" :disabled="submitting" @click="skipQuestion">跳过</button>
          </div>

          <div v-if="lastFeedback" class="feedback-box">
            <strong>即时反馈</strong>（得分：{{ lastScore }}）
            <p>{{ lastFeedback }}</p>
            <button class="btn" @click="nextQuestion">{{ currentIndex >= questions.length - 1 ? '查看结果' : '下一题' }}</button>
          </div>
          <AiProcessingOverlay
            :visible="processing.visible && stage === 'answering'"
            :title="processing.title"
            :description="processing.description"
            :progress="processing.progress"
            :stages="processing.stages"
            :stage-index="processing.stageIndex"
          />
        </div>

        <div v-if="stage === 'result'" class="card stage-card">
          <h2>面试结果</h2>
          <div class="score-big">{{ result.total_score }}<span>/100</span></div>
          <p class="overall-feedback">{{ result.overall_feedback }}</p>

          <h3>维度评分</h3>
          <div v-for="d in result.dimension_scores" :key="d.dimension" class="dimension-item">
            <div class="dimension-head">
              <span>{{ d.dimension }}</span>
              <span class="mono">{{ d.score }}</span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :class="{ warn: d.score < 80 && d.score >= 60, bad: d.score < 60 }"
                :style="{ width: d.score + '%' }"
              ></div>
            </div>
            <div class="dimension-comment">{{ d.comment }}</div>
          </div>

          <h3>各题详情</h3>
          <div v-for="qf in result.question_feedbacks" :key="qf.index" class="question-item">
            <div class="question-title">Q{{ qf.index + 1 }}: {{ qf.question }}</div>
            <div class="question-answer">{{ qf.answer || '(未作答)' }}</div>
            <span class="tag">得分: {{ qf.score }}</span>
          </div>

          <button class="btn" @click="resetAll">再来一次</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { startInterviewFlow, answerInterviewFlow, getInterviewFlowResult, parseResume } from '../services/api.js'
import toast from '../utils/toast.js'
import AiProcessingOverlay from '../components/AiProcessingOverlay.vue'

const stage = ref('setup')
const jobTitle = ref('')
const questionCount = ref(5)
const loading = ref(false)
const submitting = ref(false)

const sessionId = ref(null)
const questions = ref([])
const currentIndex = ref(0)
const currentAnswer = ref('')
const timer = ref(120)
const lastFeedback = ref('')
const lastScore = ref(0)
const result = ref({})
const useResumeContext = ref(false)
const resumeFileName = ref('')
const resumeParsing = ref(false)
const resumeParseError = ref('')
const resumeProfile = ref(null)
const processing = ref({
  visible: false,
  title: 'AI 正在处理中',
  description: '',
  progress: 0,
  stages: [],
  stageIndex: 0
})

let timerInterval = null
let processingProgressTimer = null
let processingStageTimer = null
let processingHideTimer = null

function formatTimer(s) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

function startTimer(seconds) {
  timer.value = seconds
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    timer.value--
    if (timer.value <= 0) {
      clearInterval(timerInterval)
      submitAnswer()
    }
  }, 1000)
}

function clearProcessingTimers() {
  if (processingProgressTimer) clearInterval(processingProgressTimer)
  if (processingStageTimer) clearInterval(processingStageTimer)
  if (processingHideTimer) clearTimeout(processingHideTimer)
  processingProgressTimer = null
  processingStageTimer = null
  processingHideTimer = null
}

function beginProcessing({ title, description = '', stages = [] }) {
  clearProcessingTimers()
  processing.value = {
    visible: true,
    title: title || 'AI 正在处理中',
    description,
    progress: 10,
    stages,
    stageIndex: 0
  }
  processingProgressTimer = setInterval(() => {
    if (!processing.value.visible) return
    const now = processing.value.progress
    if (now >= 92) return
    processing.value.progress = Math.min(92, now + Math.max(1, Math.floor((95 - now) / 9)))
  }, 240)
  if (stages.length > 1) {
    processingStageTimer = setInterval(() => {
      if (!processing.value.visible) return
      processing.value.stageIndex = Math.min(stages.length - 1, processing.value.stageIndex + 1)
    }, 1100)
  }
}

function endProcessing() {
  return new Promise((resolve) => {
    if (!processing.value.visible) {
      resolve()
      return
    }
    processing.value.progress = 100
    if (processing.value.stages.length) {
      processing.value.stageIndex = processing.value.stages.length - 1
    }
    if (processingProgressTimer) clearInterval(processingProgressTimer)
    if (processingStageTimer) clearInterval(processingStageTimer)
    processingProgressTimer = null
    processingStageTimer = null
    processingHideTimer = setTimeout(() => {
      processing.value.visible = false
      resolve()
    }, 260)
  })
}

async function withProcessing(options, task) {
  beginProcessing(options)
  try {
    return await task()
  } finally {
    await endProcessing()
  }
}

function normalizeResumePayload(parsed) {
  const safeSkills = Array.isArray(parsed?.skills) ? parsed.skills.map((item) => String(item || '').trim()).filter(Boolean) : []
  const { cards, lines } = normalizeExperiencePayload(parsed?.experience)
  return {
    name: String(parsed?.name || '').trim(),
    school: String(parsed?.school || '').trim(),
    major: String(parsed?.major || '').trim(),
    skills: safeSkills.slice(0, 20),
    experience: lines.slice(0, 8),
    experience_cards: cards.slice(0, 4),
    raw_text: String(parsed?.raw_text || '').trim().slice(0, 2400),
  }
}

function normalizeExperiencePayload(value) {
  const rawList = Array.isArray(value) ? value : []
  const cards = []
  const lines = []
  for (const item of rawList) {
    const parsedCards = parseExperienceEntry(item)
    if (parsedCards.length) {
      for (const card of parsedCards) {
        cards.push(card)
        const brief = [card.company, card.position, card.period].filter(Boolean).join(' · ')
        if (brief) lines.push(brief)
        for (const proj of card.projects.slice(0, 2)) {
          lines.push(`${card.company || '经历'}：${proj}`)
        }
      }
      continue
    }
    const text = String(item || '').trim()
    if (text) lines.push(text)
  }
  return {
    cards,
    lines: dedupeStrings(lines),
  }
}

function parseExperienceEntry(entry) {
  if (!entry) return []
  if (typeof entry === 'object' && !Array.isArray(entry)) {
    return [toExperienceCard(entry)]
  }
  const text = String(entry).trim()
  if (!text) return []

  // Handle python-dict-like merged strings:
  // {'company': 'A', ...}；{'company': 'B', ...}
  const blocks = text.match(/\{[\s\S]*?\}/g) || []
  const parsedBlocks = blocks
    .map((block) => parseLooseJsonObject(block))
    .filter(Boolean)
    .map((obj) => toExperienceCard(obj))
  if (parsedBlocks.length) return parsedBlocks

  const single = parseLooseJsonObject(text)
  return single ? [toExperienceCard(single)] : []
}

function parseLooseJsonObject(input) {
  const text = String(input || '').trim()
  if (!text.startsWith('{') || !text.endsWith('}')) return null
  const normalized = text
    .replace(/([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)/g, '$1"$2"$3')
    .replace(/\bNone\b/g, 'null')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bFalse\b/g, 'false')
    .replace(/'/g, '"')
  try {
    const parsed = JSON.parse(normalized)
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch (_) {
    return null
  }
}

function toExperienceCard(value) {
  const company = String(value?.company || '').trim()
  const position = String(value?.position || '').trim()
  const department = String(value?.department || '').trim()
  const location = String(value?.location || '').trim()
  const startDate = String(value?.start_date || value?.startDate || '').trim()
  const endDate = String(value?.end_date || value?.endDate || '').trim()
  const period = [startDate, endDate].filter(Boolean).join(' ~ ')
  const projects = normalizeProjectList(value?.projects)
  return {
    company,
    position,
    department,
    location,
    period,
    projects,
    meta: [position, department, location].filter(Boolean).join(' · '),
  }
}

function normalizeProjectList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean)
  }
  if (typeof value === 'string') {
    return value
      .split(/\n+|；|;/)
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return []
}

function dedupeStrings(list) {
  const seen = new Set()
  const result = []
  for (const item of list) {
    const text = String(item || '').trim()
    if (!text) continue
    const key = text.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    result.push(text)
  }
  return result
}

async function onResumeFileChange(event) {
  const file = event?.target?.files?.[0]
  if (!file) return
  resumeFileName.value = file.name
  resumeParseError.value = ''
  resumeProfile.value = null
  resumeParsing.value = true
  try {
    await withProcessing(
      {
        title: 'AI 正在解析简历',
        description: '正在提取技能、专业和项目经历',
        stages: ['读取文件', '解析简历内容', '提取关键要点']
      },
      async () => {
        const parsed = await parseResume(file)
        resumeProfile.value = normalizeResumePayload(parsed)
      }
    )
    toast.success('简历解析完成，已用于定制题目')
  } catch (error) {
    const reason = String(error?.message || '').trim()
    resumeParseError.value = reason ? `简历解析失败：${reason}` : '简历解析失败，本次可继续仅按岗位生成题目'
    toast.warn('简历解析失败，可不使用简历继续面试')
  } finally {
    resumeParsing.value = false
  }
}

async function startInterview() {
  if (!jobTitle.value.trim()) {
    toast.error('请输入目标岗位')
    return
  }
  const useResume = useResumeContext.value && !!resumeProfile.value
  if (useResumeContext.value && resumeFileName.value && !resumeProfile.value && !resumeParsing.value) {
    toast.warn('简历暂未解析成功，本次将仅按岗位出题')
  }
  loading.value = true
  try {
    await withProcessing(
      {
        title: 'AI 正在创建面试流程',
        description: useResume ? '正在结合岗位和简历生成定制题目' : '正在匹配岗位并生成题目',
        stages: useResume ? ['提取岗位能力项', '融合简历要点', '生成定制题目'] : ['读取岗位信息', '生成题目', '准备计时器']
      },
      async () => {
        const payload = {
          job_title: jobTitle.value,
          question_count: questionCount.value
        }
        if (useResume) {
          payload.resume_text = resumeProfile.value.raw_text || ''
          payload.resume_skills = resumeProfile.value.skills || []
          payload.resume_major = resumeProfile.value.major || ''
          payload.resume_experience = resumeProfile.value.experience || []
        }
        const res = await startInterviewFlow(payload)
        sessionId.value = res.session_id
        questions.value = res.questions
        currentIndex.value = 0
        currentAnswer.value = ''
        lastFeedback.value = ''
        stage.value = 'answering'
        startTimer(res.questions[0]?.time_limit || 120)
      }
    )
  } catch (e) {
    toast.error('启动失败: ' + e.message)
  }
  loading.value = false
}

async function submitAnswer() {
  if (submitting.value) return
  if (timerInterval) clearInterval(timerInterval)
  submitting.value = true
  try {
    await withProcessing(
      {
        title: 'AI 正在评估本题回答',
        description: '将从贴题度、深度和表达等维度评分',
        stages: ['理解问题', '分析回答', '输出即时反馈']
      },
      async () => {
        const res = await answerInterviewFlow({
          session_id: sessionId.value,
          question_index: currentIndex.value,
          answer: currentAnswer.value || '(未作答)',
        })
        lastFeedback.value = res.feedback
        lastScore.value = res.score
      }
    )
  } catch (e) {
    toast.error('提交失败')
  }
  submitting.value = false
}

function skipQuestion() {
  currentAnswer.value = ''
  submitAnswer()
}

async function nextQuestion() {
  if (currentIndex.value >= questions.value.length - 1) {
    try {
      await withProcessing(
        {
          title: 'AI 正在生成整场面试报告',
          description: '正在汇总每题表现并生成最终建议',
          stages: ['汇总问答', '计算总分', '生成报告']
        },
        async () => {
          result.value = await getInterviewFlowResult(sessionId.value)
          stage.value = 'result'
        }
      )
    } catch (e) {
      toast.error('获取结果失败')
    }
    return
  }
  currentIndex.value++
  currentAnswer.value = ''
  lastFeedback.value = ''
  startTimer(questions.value[currentIndex.value]?.time_limit || 120)
}

function resetAll() {
  stage.value = 'setup'
  sessionId.value = null
  questions.value = []
  currentIndex.value = 0
  result.value = {}
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
  clearProcessingTimers()
})
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero {
  padding: 28px 0 10px;
}

.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.stage-card {
  gap: 12px;
  border: 1px solid #d8eee1;
  position: relative;
  overflow: hidden;
  min-height: 200px;
}

.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e1ebe6;
  border-radius: 10px;
  font-size: 14px;
  box-sizing: border-box;
}

.count-input {
  max-width: 120px;
}

.resume-config {
  border: 1px solid #dcece3;
  background: #f8fcfa;
  border-radius: 12px;
  padding: 10px 12px;
}

.toggle-line {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.toggle-line input {
  width: 16px;
  height: 16px;
  accent-color: #18a058;
}

.resume-upload-block {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  min-width: 112px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.file-picker-name {
  color: #4f6b61;
  font-size: 13px;
}

.resume-error {
  color: #b54747;
}

.resume-preview {
  border: 1px dashed #d4e9de;
  border-radius: 10px;
  padding: 10px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.experience-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.experience-card {
  border: 1px solid #dcece3;
  border-radius: 10px;
  background: #f8fcfa;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.experience-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.experience-meta {
  margin: 0;
  color: #4f6b61;
}

.experience-projects {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.experience-projects ul {
  margin: 0;
  padding-left: 18px;
  color: #2d4b3f;
}

.experience-projects li {
  line-height: 1.5;
}

.question-box {
  background: #f6fbf8;
  padding: 16px;
  border-radius: 10px;
  font-size: 15px;
  line-height: 1.6;
  border: 1px solid #dcefe4;
}

.feedback-box {
  background: #f0faf5;
  padding: 12px 16px;
  border-radius: 10px;
  border-left: 3px solid #18a058;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-bar {
  height: 6px;
  background: #e1ebe6;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #18a058;
  border-radius: 3px;
  transition: width 0.3s;
}

.progress-fill.warn {
  background: #f0a020;
}

.progress-fill.bad {
  background: #e53e3e;
}

.score-big {
  font-size: 56px;
  font-weight: 700;
  color: #18a058;
  text-align: center;
}

.score-big span {
  font-size: 20px;
  color: var(--muted);
}

label {
  display: block;
  font-weight: 600;
  font-size: 14px;
}

.head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.timer-tag {
  color: #fff;
  background: #18a058;
}

.timer-tag.danger {
  background: #e53e3e;
}

.actions-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.overall-feedback {
  margin: 8px 0 16px;
  color: #2f423a;
}

.dimension-item {
  margin-bottom: 12px;
}

.dimension-head {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.dimension-comment {
  font-size: 12px;
  color: #6b7c78;
}

.question-item {
  margin-bottom: 8px;
  padding: 12px;
  background: #f6f8f7;
  border: 1px solid #dcebe3;
  border-radius: 10px;
}

.question-title {
  font-weight: 600;
}

.question-answer {
  margin: 8px 0;
  font-size: 13px;
}
</style>
