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
          <button class="btn" :disabled="loading" @click="startInterview">{{ loading ? '准备中...' : '开始面试' }}</button>
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
import { startInterviewFlow, answerInterviewFlow, getInterviewFlowResult } from '../services/api.js'
import toast from '../utils/toast.js'

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

let timerInterval = null

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

async function startInterview() {
  if (!jobTitle.value.trim()) {
    toast.error('请输入目标岗位')
    return
  }
  loading.value = true
  try {
    const res = await startInterviewFlow({ job_title: jobTitle.value, question_count: questionCount.value })
    sessionId.value = res.session_id
    questions.value = res.questions
    currentIndex.value = 0
    currentAnswer.value = ''
    lastFeedback.value = ''
    stage.value = 'answering'
    startTimer(res.questions[0]?.time_limit || 120)
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
    const res = await answerInterviewFlow({
      session_id: sessionId.value,
      question_index: currentIndex.value,
      answer: currentAnswer.value || '(未作答)',
    })
    lastFeedback.value = res.feedback
    lastScore.value = res.score
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
      result.value = await getInterviewFlowResult(sessionId.value)
      stage.value = 'result'
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
