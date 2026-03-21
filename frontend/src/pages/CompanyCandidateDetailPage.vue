<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
        <div>
          <button type="button" class="btn btn-outline back-btn" @click="goBack">返回候选人筛选</button>
          <h1>{{ detail ? `${detail.student_name} 的投递详情` : '候选人详情' }}</h1>
          <p v-if="detail">{{ detail.job_name }} · {{ detail.school }} · {{ detail.major }}</p>
          <p v-else>查看候选人简历与流程状态。</p>
        </div>
        <StatusPill v-if="detail" kind="application" :status="detail.status" />
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="loading" class="card mono">加载中...</div>

        <div v-else-if="!detail" class="card empty-state">
          <h3>未找到候选人投递记录</h3>
          <p>该记录可能不存在，或你没有访问权限。</p>
          <button type="button" class="btn btn-outline" @click="goBack">返回</button>
        </div>

        <div v-else>
          <div class="overview-strip">
            <article class="card overview-card">
              <span class="mono">当前状态</span>
              <StatusPill kind="application" :status="detail.status" />
            </article>
            <article class="card overview-card">
              <span class="mono">投递时间</span>
              <strong>{{ formatTime(detail.apply_time) }}</strong>
            </article>
            <article class="card overview-card">
              <span class="mono">简历来源</span>
              <strong>{{ resumeSourceLabel }}</strong>
            </article>
            <article class="card overview-card">
              <span class="mono">流程进度</span>
              <strong>{{ progressPercent }}%</strong>
            </article>
          </div>

          <div class="detail-grid">
            <div class="card">
            <h3>候选人信息</h3>
            <div class="meta-grid">
              <div><span class="mono">姓名</span><strong>{{ detail.student_name }}</strong></div>
              <div><span class="mono">学校</span><strong>{{ detail.school }}</strong></div>
              <div><span class="mono">专业</span><strong>{{ detail.major }}</strong></div>
              <div><span class="mono">年级</span><strong>{{ detail.grade }}</strong></div>
            </div>
            <div class="meta-actions">
              <router-link class="btn btn-outline" :to="`/jobs/${detail.job_id}`">查看岗位详情</router-link>
              <a
                v-if="detail.resume_file_url"
                class="btn btn-outline"
                :href="detail.resume_file_url"
                target="_blank"
                rel="noreferrer"
              >
                打开附件简历
              </a>
            </div>
            <div class="divider"></div>
            <h4>技能标签</h4>
            <div class="tags">
              <span v-for="skill in detail.skills" :key="skill" class="tag">{{ skill }}</span>
              <span v-if="!detail.skills?.length" class="mono">暂无技能标签</span>
            </div>
            <div class="divider"></div>
            <h4>简历内容</h4>
            <div v-if="detail.resume_content" class="resume-content">
              <template v-if="Array.isArray(detail.resume_content.skills) && detail.resume_content.skills.length">
                <p class="mono">技能</p>
                <div class="tags">
                  <span v-for="s in detail.resume_content.skills" :key="`rs-${s}`" class="tag">{{ s }}</span>
                </div>
              </template>
              <template v-if="Array.isArray(detail.resume_content.projects) && detail.resume_content.projects.length">
                <p class="mono">项目经历</p>
                <ul>
                  <li v-for="p in detail.resume_content.projects" :key="`rp-${p}`">{{ p }}</li>
                </ul>
              </template>
              <template v-if="Array.isArray(detail.resume_content.internships) && detail.resume_content.internships.length">
                <p class="mono">实习经历</p>
                <ul>
                  <li v-for="i in detail.resume_content.internships" :key="`ri-${i}`">{{ i }}</li>
                </ul>
              </template>
              <template v-if="resumeStructuredItems.length">
                <p class="mono">完整简历信息</p>
                <div class="resume-structured">
                  <div v-for="item in resumeStructuredItems" :key="item.key" class="resume-block">
                    <div class="resume-block-title">{{ item.label }}</div>

                    <div v-if="item.type === 'text'" class="resume-block-text">{{ item.text }}</div>

                    <div v-else-if="item.type === 'list'" class="resume-list">
                      <span v-for="line in item.lines" :key="`${item.key}-${line}`" class="tag">{{ line }}</span>
                    </div>

                    <div v-else-if="item.type === 'object'" class="resume-kv">
                      <div v-for="pair in item.pairs" :key="`${item.key}-${pair.key}`" class="resume-kv-item">
                        <span class="mono">{{ pair.key }}</span>
                        <strong>{{ pair.value }}</strong>
                      </div>
                    </div>

                    <div v-else-if="item.type === 'list-object'" class="resume-list-object">
                      <div v-for="(line, idx) in item.lines" :key="`${item.key}-${idx}`" class="resume-list-object-item">
                        {{ line }}
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
            <p v-else class="mono">该投递暂无在线简历内容。</p>
            </div>

            <div class="card">
            <h3>投递流程</h3>
            <div class="timeline-head">
              <span class="mono">投递时间：{{ formatTime(detail.apply_time) }}</span>
              <span class="mono">最近更新：{{ formatTime(detail.update_time || detail.apply_time) }}</span>
            </div>

            <div class="step-bar">
              <template v-for="(step, idx) in steps" :key="step.key">
                <div class="step-node" :class="stepClass(detail.status, step.key)"></div>
                <div v-if="idx < steps.length - 1" class="step-line" :class="{ done: stepDone(detail.status, step.key) }"></div>
              </template>
            </div>
            <div class="step-labels">
              <span
                v-for="step in steps"
                :key="step.key"
                class="step-label"
                :class="{ active: detail.status === step.key }"
              >
                {{ step.label }}
              </span>
            </div>

            <div class="divider"></div>
            <h4>流程操作</h4>
            <div v-if="nextStatusOptions.length" class="status-action">
              <div class="next-status-tags">
                <button
                  v-for="opt in nextStatusOptions"
                  :key="`next-${opt}`"
                  type="button"
                  class="next-status-btn"
                  :class="{ active: statusDraft === opt }"
                  @click="statusDraft = opt"
                >
                  {{ statusLabel(opt) }}
                </button>
              </div>
              <select v-model="statusDraft">
                <option v-for="opt in nextStatusOptions" :key="opt" :value="opt">{{ statusLabel(opt) }}</option>
              </select>
              <button class="btn" :disabled="statusUpdating" @click="submitStatusUpdate">
                {{ statusUpdating ? '更新中...' : '更新状态' }}
              </button>
            </div>
            <p v-else class="mono">{{ statusActionHint }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import toast from '../utils/toast';
import { fetchCompanyApplicationDetail, updateApplicationStatus } from '../services/api';
import StatusPill from '../components/StatusPill.vue';
import {
  APPLICATION_STATUS_TRANSITIONS,
  applicationStatusLabel as getApplicationStatusLabel,
  canApplicationStatusTransition
} from '../constants/status';

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const detail = ref(null);
const statusDraft = ref('');
const statusUpdating = ref(false);

const steps = [
  { key: 'submitted', label: '已投递' },
  { key: 'viewed', label: '已查看' },
  { key: 'reviewing', label: '筛选中' },
  { key: 'to_contact', label: '待沟通' },
  { key: 'interview_scheduled', label: '已安排面试' },
  { key: 'interviewing', label: '面试中' },
  { key: 'accepted', label: '已通过' }
];

const stepOrder = steps.map((s) => s.key);

const nextStatusOptions = computed(() => {
  const currentStatus = detail.value?.status;
  if (!currentStatus) return [];
  return APPLICATION_STATUS_TRANSITIONS[currentStatus] || [];
});

const progressPercent = computed(() => {
  const status = detail.value?.status;
  if (!status) return 0;
  if (status === 'rejected' || status === 'withdrawn') return 100;
  const idx = stepOrder.indexOf(status);
  if (idx < 0) return 0;
  return Math.round(((idx + 1) / steps.length) * 100);
});

const resumeSourceLabel = computed(() => {
  const hasOnline = Boolean(detail.value?.resume_content);
  const hasFile = Boolean(detail.value?.resume_file_url);
  if (hasOnline && hasFile) return '在线 + 附件';
  if (hasOnline) return '在线简历';
  if (hasFile) return '附件简历';
  return '暂无简历';
});

const statusActionHint = computed(() => {
  const currentStatus = detail.value?.status;
  if (!currentStatus) return '暂无可操作流程状态。';
  if (currentStatus === 'accepted') return '候选人已通过，流程已完成。';
  if (currentStatus === 'rejected') return '候选人已淘汰，流程已结束。';
  if (currentStatus === 'withdrawn') return '候选人已撤回，流程已结束。';
  return '当前状态不可继续流转。';
});

const resumeStructuredItems = computed(() => {
  const content = detail.value?.resume_content;
  if (!content || typeof content !== 'object' || Array.isArray(content)) return [];

  const skipKeys = new Set(['skills', 'projects', 'internships']);
  return Object.entries(content)
    .filter(([key, value]) => !skipKeys.has(key) && hasMeaningfulValue(value))
    .map(([key, value]) => toResumeItem(key, value));
});

function goBack() {
  router.push({ path: '/company-center', query: { tab: 'candidates' } });
}

function statusLabel(status) {
  return getApplicationStatusLabel(status);
}

function stepClass(status, stepKey) {
  if (status === 'rejected' || status === 'withdrawn') return '';
  const current = stepOrder.indexOf(status);
  const target = stepOrder.indexOf(stepKey);
  if (target < current) return 'done';
  if (target === current) return 'current';
  return '';
}

function stepDone(status, stepKey) {
  if (status === 'rejected' || status === 'withdrawn') return false;
  return stepOrder.indexOf(stepKey) < stepOrder.indexOf(status);
}

function formatTime(value) {
  if (!value) return '--';
  return String(value).replace('T', ' ').slice(0, 16);
}

function hasMeaningfulValue(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'object') return Object.keys(value).length > 0;
  return true;
}

function humanizeKey(raw) {
  const map = {
    name: '姓名',
    phone: '电话',
    email: '邮箱',
    school: '学校',
    major: '专业',
    grade: '年级',
    student_no: '学号',
    education: '学历',
    expected_job: '期望岗位',
    expected_city: '期望城市',
    expected_salary: '期望薪资',
    awards: '获奖情况',
    certificates: '证书',
    bio: '自我介绍',
    summary: '个人总结'
  };
  if (map[raw]) return map[raw];
  return raw.replace(/_/g, ' ').replace(/\b\w/g, (s) => s.toUpperCase());
}

function stringifyPrimitive(value) {
  if (typeof value === 'boolean') return value ? '是' : '否';
  return String(value);
}

function summarizeObject(value) {
  return Object.entries(value).map(([k, v]) => `${humanizeKey(k)}：${displayValue(v)}`).join('；');
}

function displayValue(value) {
  if (value === null || value === undefined) return '--';
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === 'object' ? summarizeObject(item) : stringifyPrimitive(item))).join('，');
  }
  if (typeof value === 'object') return summarizeObject(value);
  return stringifyPrimitive(value);
}

function toResumeItem(key, value) {
  const label = humanizeKey(key);
  if (Array.isArray(value)) {
    if (value.every((item) => item === null || ['string', 'number', 'boolean'].includes(typeof item))) {
      return {
        key,
        label,
        type: 'list',
        lines: value.map((item) => stringifyPrimitive(item))
      };
    }
    return {
      key,
      label,
      type: 'list-object',
      lines: value.map((item) => (typeof item === 'object' ? summarizeObject(item) : stringifyPrimitive(item)))
    };
  }
  if (typeof value === 'object') {
    return {
      key,
      label,
      type: 'object',
      pairs: Object.entries(value).map(([subKey, subValue]) => ({
        key: humanizeKey(subKey),
        value: displayValue(subValue)
      }))
    };
  }
  return {
    key,
    label,
    type: 'text',
    text: stringifyPrimitive(value)
  };
}

async function loadDetail() {
  const id = Number(route.params.applicationId);
  if (!id) {
    toast.error('无效的投递记录 ID');
    return;
  }
  loading.value = true;
  try {
    detail.value = await fetchCompanyApplicationDetail(id);
    statusDraft.value = nextStatusOptions.value[0] || '';
  } catch (err) {
    detail.value = null;
    toast.error('加载候选人详情失败');
  } finally {
    loading.value = false;
  }
}

async function submitStatusUpdate() {
  if (!detail.value || !statusDraft.value) return;
  if (!canApplicationStatusTransition(detail.value.status, statusDraft.value)) {
    toast.warn('请选择当前流程可达的状态');
    return;
  }
  statusUpdating.value = true;
  try {
    await updateApplicationStatus(detail.value.application_id, { status: statusDraft.value });
    toast.success(`状态已更新为：${statusLabel(statusDraft.value)}`);
    await loadDetail();
  } catch (err) {
    toast.error('状态更新失败');
  } finally {
    statusUpdating.value = false;
  }
}

onMounted(loadDetail);
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

.back-btn {
  margin-bottom: 10px;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.overview-card {
  padding: 14px 16px;
  gap: 6px;
}

.overview-card strong {
  color: var(--accent-dark);
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(300px, 1fr) minmax(300px, 1fr);
  gap: 16px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.meta-grid div {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.resume-content ul {
  margin: 6px 0 12px;
  padding-left: 18px;
}

.resume-structured {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-block {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  background: #fbfdfc;
}

.resume-block-title {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
}

.resume-block-text {
  white-space: pre-wrap;
}

.resume-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.resume-kv {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}

.resume-kv-item {
  border: 1px dashed var(--line);
  border-radius: 8px;
  padding: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.resume-list-object {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.resume-list-object-item {
  border-left: 3px solid rgba(24, 160, 88, 0.25);
  padding: 6px 8px;
  background: #f7fbf9;
  border-radius: 6px;
}

.timeline-head {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.status-action {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
}

.next-status-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.next-status-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  color: #456b5b;
  cursor: pointer;
  transition: all 0.15s ease;
}

.next-status-btn.active {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
  font-weight: 600;
}

.status-action select {
  height: 44px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0 10px;
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 10px 0;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }

  .status-action {
    align-items: stretch;
  }
}
</style>
