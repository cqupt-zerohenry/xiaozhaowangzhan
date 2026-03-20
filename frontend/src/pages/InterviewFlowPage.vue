<template>
  <div class="container" style="padding-top: 32px; max-width: 800px;">
    <!-- Start Screen -->
    <div v-if="stage === 'setup'" class="card">
      <h2>AI 模拟面试</h2>
      <p style="color: #6b7c78; margin-bottom: 16px;">选择岗位开始一场完整的面试模拟，每道题限时作答，即时获得反馈。</p>
      <label>目标岗位</label>
      <input v-model="jobTitle" placeholder="如：后端开发工程师" class="input" />
      <label>题目数量</label>
      <input v-model.number="questionCount" type="number" min="1" max="20" class="input" style="width: 100px;" />
      <button class="btn" style="margin-top: 16px;" :disabled="loading" @click="startInterview">{{ loading ? '准备中...' : '开始面试' }}</button>
    </div>

    <!-- Interview In Progress -->
    <div v-if="stage === 'answering'" class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h3>题目 {{ currentIndex + 1 }} / {{ questions.length }}</h3>
        <span class="tag" :style="{ background: timer <= 30 ? '#e53e3e' : '#18a058', color: '#fff' }">{{ formatTimer(timer) }}</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" :style="{ width: (currentIndex / questions.length * 100) + '%' }"></div></div>
      <div class="question-box">{{ questions[currentIndex]?.question }}</div>
      <textarea v-model="currentAnswer" rows="6" class="input" placeholder="请输入你的回答..." :disabled="submitting"></textarea>
      <div style="display: flex; gap: 8px; margin-top: 12px;">
        <button class="btn" :disabled="submitting || !currentAnswer.trim()" @click="submitAnswer">{{ submitting ? '提交中...' : '提交回答' }}</button>
        <button class="btn btn-outline" @click="skipQuestion">跳过</button>
      </div>

      <!-- Per-question feedback -->
      <div v-if="lastFeedback" class="feedback-box" style="margin-top: 16px;">
        <strong>即时反馈</strong>（得分：{{ lastScore }}）
        <p>{{ lastFeedback }}</p>
        <button class="btn" style="margin-top: 8px;" @click="nextQuestion">{{ currentIndex >= questions.length - 1 ? '查看结果' : '下一题' }}</button>
      </div>
    </div>

    <!-- Result Screen -->
    <div v-if="stage === 'result'" class="card">
      <h2>面试结果</h2>
      <div class="score-big">{{ result.total_score }}<span style="font-size: 20px; color: #6b7c78;">/100</span></div>
      <p style="margin: 16px 0; color: #333;">{{ result.overall_feedback }}</p>

      <h3 style="margin-top: 24px;">维度评分</h3>
      <div v-for="d in result.dimension_scores" :key="d.dimension" style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; font-size: 14px;">
          <span>{{ d.dimension }}</span><span class="mono">{{ d.score }}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" :style="{ width: d.score + '%', background: d.score >= 80 ? '#18a058' : d.score >= 60 ? '#f0a020' : '#e53e3e' }"></div></div>
        <div style="font-size: 12px; color: #6b7c78;">{{ d.comment }}</div>
      </div>

      <h3 style="margin-top: 24px;">各题详情</h3>
      <div v-for="qf in result.question_feedbacks" :key="qf.index" class="card" style="margin-bottom: 8px; padding: 12px; background: #f6f8f7;">
        <div style="font-weight: 600;">Q{{ qf.index + 1 }}: {{ qf.question }}</div>
        <div style="margin: 8px 0; font-size: 13px;">{{ qf.answer || '(未作答)' }}</div>
        <span class="tag">得分: {{ qf.score }}</span>
      </div>

      <button class="btn" style="margin-top: 16px;" @click="resetAll">再来一次</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { startInterviewFlow, answerInterviewFlow, getInterviewFlowResult } from '../services/api.js'
import { toast } from '../utils/toast.js'

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
  if (!jobTitle.value.trim()) { toast.error('请输入目标岗位'); return }
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
  } catch (e) { toast.error('启动失败: ' + e.message) }
  loading.value = false
}

async function submitAnswer() {
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
  } catch (e) { toast.error('提交失败') }
  submitting.value = false
}

function skipQuestion() {
  currentAnswer.value = ''
  submitAnswer()
}

async function nextQuestion() {
  if (currentIndex.value >= questions.value.length - 1) {
    // Get final result
    try {
      result.value = await getInterviewFlowResult(sessionId.value)
      stage.value = 'result'
    } catch (e) { toast.error('获取结果失败') }
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

onUnmounted(() => { if (timerInterval) clearInterval(timerInterval) })
</script>

<style scoped>
.input { width: 100%; padding: 10px 14px; border: 1px solid #e1ebe6; border-radius: 8px; font-size: 14px; margin-top: 4px; margin-bottom: 12px; box-sizing: border-box; }
textarea.input { resize: vertical; font-family: inherit; }
.question-box { background: #f6f8f7; padding: 16px; border-radius: 10px; font-size: 15px; margin-bottom: 12px; line-height: 1.6; }
.feedback-box { background: #f0faf5; padding: 12px 16px; border-radius: 10px; border-left: 3px solid #18a058; }
.feedback-box p { margin: 8px 0 0; font-size: 14px; }
.progress-bar { height: 6px; background: #e1ebe6; border-radius: 3px; margin-bottom: 12px; overflow: hidden; }
.progress-fill { height: 100%; background: #18a058; border-radius: 3px; transition: width 0.3s; }
.score-big { font-size: 56px; font-weight: 700; color: #18a058; text-align: center; }
label { display: block; font-weight: 600; font-size: 14px; margin-bottom: 4px; }
</style>
