<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>管理中心</h1>
          <p>用户管理、公告管理、学生核验审批。</p>
        </div>
        <button class="btn" @click="loadAll">刷新数据</button>
      </div>
    </section>

    <section>
      <div class="container grid layout">
        <div class="card" v-if="enhancedStats">
          <h3>平台数据统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-num">{{ enhancedStats.student_total }}</span>
              <span class="mono">学生总数</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ enhancedStats.company_total }}</span>
              <span class="mono">企业总数</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ enhancedStats.job_total }}</span>
              <span class="mono">岗位总数</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ enhancedStats.application_total }}</span>
              <span class="mono">投递总数</span>
            </div>
          </div>
          <div class="divider"></div>
          <h4>热门岗位类型</h4>
          <div class="tags">
            <span class="tag" v-for="item in enhancedStats.hot_job_types" :key="item.type">
              {{ item.type }} ({{ item.count }})
            </span>
            <span v-if="!enhancedStats.hot_job_types?.length" class="mono">暂无数据</span>
          </div>
          <div class="divider"></div>
          <h4>活跃企业</h4>
          <div class="tags">
            <span class="tag" v-for="item in enhancedStats.active_companies" :key="item.name">
              {{ item.name }} ({{ item.job_count }}个岗位)
            </span>
            <span v-if="!enhancedStats.active_companies?.length" class="mono">暂无数据</span>
          </div>
        </div>

        <div class="card">
          <h3>用户管理</h3>
          <div v-if="users.length === 0" class="mono">暂无用户</div>
          <div v-else class="list">
            <div class="item" v-for="user in users" :key="user.id">
              <div class="item-main">
                <div>
                  <strong>{{ user.name }}</strong>
                  <p class="mono">{{ user.role }} · {{ user.email }}</p>
                </div>
                <div class="actions">
                  <button class="btn btn-outline" @click="toggleUserStatus(user)">
                    {{ user.status === 'active' ? '禁用' : '启用' }}
                  </button>
                  <button class="btn btn-outline" @click="resetPasswordId = resetPasswordId === user.id ? null : user.id">
                    重置密码
                  </button>
                </div>
              </div>
              <div v-if="resetPasswordId === user.id" class="reset-row">
                <input v-model="resetPasswordValue" type="password" placeholder="新密码（至少6位）" minlength="6" class="reset-input" />
                <button class="btn" @click="doResetPassword(user.id)">确认重置</button>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>公告管理</h3>
          <div class="form-grid">
            <input v-model="announcementForm.title" placeholder="公告标题" />
            <input v-model="announcementForm.status" placeholder="状态 draft/published" />
          </div>
          <textarea v-model="announcementForm.content" rows="3" placeholder="公告内容"></textarea>
          <label class="checkbox">
            <input type="checkbox" v-model="announcementForm.pinned" />
            置顶
          </label>
          <button class="btn" @click="createNewAnnouncement">
            {{ editingAnnouncementId ? "保存公告" : "发布公告" }}
          </button>
          <button v-if="editingAnnouncementId" class="btn btn-outline" @click="cancelEdit">取消编辑</button>

          <div class="list">
            <div class="item" v-for="item in announcements" :key="item.id">
              <div>
                <strong>{{ item.title }}</strong>
                <p class="mono">{{ item.status }} · {{ item.pinned ? '置顶' : '普通' }}</p>
              </div>
              <div class="actions">
                <button class="btn btn-outline" @click="startEdit(item)">编辑</button>
                <button class="btn btn-outline" @click="toggleAnnouncementStatus(item)">
                  {{ item.status === 'published' ? '撤回' : '发布' }}
                </button>
                <button class="btn btn-outline" @click="removeAnnouncement(item.id)">删除</button>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>学生核验审批</h3>
          <div v-if="verifyRequests.length === 0" class="mono">暂无核验请求</div>
          <div v-else class="list">
            <div class="item" v-for="item in verifyRequests" :key="item.id">
              <div>
                <strong>请求 #{{ item.id }}</strong>
                <p class="mono">企业 {{ item.company_id }} -> 学生 {{ item.student_id }}</p>
                <p class="mono">字段：{{ (item.fields || []).join(', ') || '无' }}</p>
                <p class="mono">状态：{{ item.status }}</p>
              </div>
              <div class="actions">
                <button class="btn btn-outline" @click="review(item, 'approved')">通过</button>
                <button class="btn btn-outline" @click="review(item, 'rejected')">驳回</button>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>推荐算法配置</h3>
          <div class="form-grid">
            <div>
              <label class="mono">协同过滤权重</label>
              <input v-model.number="recommendConfig.collaborative_weight" type="number" step="0.1" min="0" max="1" />
            </div>
            <div>
              <label class="mono">内容分析权重</label>
              <input v-model.number="recommendConfig.content_weight" type="number" step="0.1" min="0" max="1" />
            </div>
          </div>
          <button class="btn" @click="saveRecommendConfig">保存配置</button>
        </div>

        <div class="card">
          <h3>操作日志</h3>
          <div v-if="operationLogs.length === 0" class="mono">暂无日志记录</div>
          <div v-else class="list">
            <div class="item" v-for="log in operationLogs" :key="log.id">
              <div>
                <strong>{{ log.action }}</strong>
                <p class="mono">用户 {{ log.user_id }} · {{ log.target_type }} #{{ log.target_id }}</p>
                <p class="mono" v-if="log.detail">{{ log.detail }}</p>
              </div>
              <span class="mono">{{ formatTime(log.create_time) }}</span>
            </div>
          </div>
        </div>

        <div class="card section-card">
          <div class="section-header">
            <h3>推荐算法评测</h3>
            <button class="btn btn-outline" @click="loadEvaluation">运行评测</button>
          </div>
          <div v-if="evaluation" class="eval-grid">
            <div class="eval-item">
              <span class="mono">评测学生数</span>
              <strong>{{ evaluation.evaluated_students }} / {{ evaluation.total_students }}</strong>
            </div>
            <div class="eval-item">
              <span class="mono">冷启动用户</span>
              <strong>{{ evaluation.cold_start_users }}</strong>
            </div>
            <div class="eval-item">
              <span class="mono">Precision@5</span>
              <strong>{{ (evaluation.precision_at_5 * 100).toFixed(1) }}%</strong>
            </div>
            <div class="eval-item">
              <span class="mono">Recall@5</span>
              <strong>{{ (evaluation.recall_at_5 * 100).toFixed(1) }}%</strong>
            </div>
            <div class="eval-item">
              <span class="mono">命中率</span>
              <strong>{{ (evaluation.hit_rate * 100).toFixed(1) }}%</strong>
            </div>
            <div class="eval-item">
              <span class="mono">覆盖率</span>
              <strong>{{ (evaluation.coverage * 100).toFixed(1) }}%</strong>
            </div>
            <div class="eval-item">
              <span class="mono">平均匹配技能</span>
              <strong>{{ evaluation.avg_matched_skills }}</strong>
            </div>
            <div class="eval-item">
              <span class="mono">算法版本</span>
              <strong class="mono">{{ evaluation.algorithm_version }}</strong>
            </div>
          </div>
          <p v-else class="mono">点击"运行评测"查看推荐算法质量指标</p>
        </div>

        <div class="card section-card">
          <div class="section-header">
            <h3>就业数据分析</h3>
            <button class="btn btn-outline" @click="loadAnalytics">刷新数据</button>
          </div>
          <div v-if="analytics">
            <h4>专业投递热度 Top 10</h4>
            <div class="analytics-list">
              <div class="analytics-row" v-for="item in analytics.major_heatmap" :key="item.major">
                <span>{{ item.major }}</span>
                <div class="progress" style="flex:1"><div class="progress-bar" :style="{ width: (item.application_count / Math.max(...analytics.major_heatmap.map(m => m.application_count), 1) * 100) + '%' }"></div></div>
                <strong class="mono">{{ item.application_count }}</strong>
              </div>
            </div>

            <h4>岗位类型热度</h4>
            <div class="analytics-list">
              <div class="analytics-row" v-for="item in analytics.job_type_popularity" :key="item.job_type">
                <span>{{ item.job_type }}</span>
                <strong class="mono">{{ item.application_count }} 次投递</strong>
              </div>
            </div>

            <h4>投递转化漏斗</h4>
            <div class="funnel-grid">
              <div class="funnel-item" v-for="item in analytics.conversion_funnel" :key="item.status">
                <strong>{{ item.count }}</strong>
                <span class="mono">{{ funnelLabel(item.status) }}</span>
              </div>
            </div>

            <h4>技能缺口 Top 15</h4>
            <div class="tags" style="margin-top:8px">
              <span class="tag" v-for="item in analytics.skill_gap" :key="item.skill" style="background:rgba(255,107,53,0.1);color:#ff6b35">
                {{ item.skill }} ({{ item.missing_count }})
              </span>
            </div>

            <h4>企业响应率</h4>
            <div class="analytics-list">
              <div class="analytics-row" v-for="item in analytics.company_activity" :key="item.company_name">
                <span>{{ item.company_name }}</span>
                <strong class="mono">{{ (item.response_rate * 100).toFixed(0) }}% ({{ item.total_reviewed }}/{{ item.total_received }})</strong>
              </div>
            </div>

            <h4>月度投递趋势</h4>
            <div class="analytics-list">
              <div class="analytics-row" v-for="item in analytics.monthly_trend" :key="item.month">
                <span class="mono">{{ item.month }}</span>
                <strong>{{ item.application_count }} 投递</strong>
              </div>
            </div>
          </div>
          <p v-else class="mono">点击"刷新数据"查看就业分析</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import {
  createAnnouncement,
  deleteAnnouncement,
  fetchAnnouncements,
  fetchEmploymentAnalytics,
  fetchEnhancedStats,
  fetchOperationLogs,
  fetchRecommendConfig,
  fetchRecommendEvaluation,
  fetchUsers,
  fetchVerificationRequests,
  resetUserPassword,
  updateAnnouncement,
  updateRecommendConfig,
  updateUserStatus,
  updateVerificationRequest
} from '../services/api';
import toast from '../utils/toast';

const users = ref([]);
const announcements = ref([]);
const verifyRequests = ref([]);
const editingAnnouncementId = ref(null);
const enhancedStats = ref(null);
const operationLogs = ref([]);
const recommendConfig = ref({ collaborative_weight: 0.4, content_weight: 0.6 });
const resetPasswordId = ref(null);
const resetPasswordValue = ref('');
const evaluation = ref(null);
const analytics = ref(null);

const announcementForm = ref({
  title: '',
  content: '',
  status: 'published',
  pinned: false
});

async function loadEnhancedStats() {
  try {
    enhancedStats.value = await fetchEnhancedStats();
  } catch (e) {
    enhancedStats.value = null;
  }
}

async function loadOperationLogs() {
  try {
    operationLogs.value = await fetchOperationLogs();
  } catch (e) {
    operationLogs.value = [];
  }
}

async function loadRecommendConfig() {
  try {
    recommendConfig.value = await fetchRecommendConfig();
  } catch (e) {}
}

async function doResetPassword(userId) {
  if (!resetPasswordValue.value || resetPasswordValue.value.length < 6) {
    toast.warn('密码至少6位');
    return;
  }
  try {
    await resetUserPassword(userId, { new_password: resetPasswordValue.value });
    resetPasswordId.value = null;
    resetPasswordValue.value = '';
    toast.success('密码已重置');
  } catch (e) {
    toast.error('重置失败');
  }
}

async function saveRecommendConfig() {
  try {
    await updateRecommendConfig({
      collaborative_weight: parseFloat(recommendConfig.value.collaborative_weight) || 0.4,
      content_weight: parseFloat(recommendConfig.value.content_weight) || 0.6
    });
    toast.success('推荐配置已更新');
  } catch (e) {
    toast.error('更新失败');
  }
}

async function loadEvaluation() {
  try {
    evaluation.value = await fetchRecommendEvaluation();
  } catch (e) {
    toast.error('评测运行失败');
  }
}

async function loadAnalytics() {
  try {
    analytics.value = await fetchEmploymentAnalytics();
  } catch (e) {
    toast.error('数据分析加载失败');
  }
}

function funnelLabel(status) {
  const map = { submitted: '已投递', viewed: '已查看', reviewing: '筛选中', to_contact: '待沟通', interview_scheduled: '面试安排', interviewing: '面试中', accepted: '已录用', rejected: '已淘汰', withdrawn: '已撤回' };
  return map[status] || status;
}

function formatTime(value) {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 16);
}

async function loadAll() {
  try {
    users.value = await fetchUsers();
  } catch (err) {
    users.value = [];
  }
  try {
    announcements.value = await fetchAnnouncements();
  } catch (err) {
    announcements.value = [];
  }
  try {
    verifyRequests.value = await fetchVerificationRequests();
  } catch (err) {
    verifyRequests.value = [];
  }
  await loadEnhancedStats();
  await loadOperationLogs();
  await loadRecommendConfig();
}

async function toggleUserStatus(user) {
  const status = user.status === 'active' ? 'disabled' : 'active';
  try {
    await updateUserStatus(user.id, { status });
    await loadAll();
  } catch (err) {
    // ignore
  }
}

async function createNewAnnouncement() {
  if (!announcementForm.value.title || !announcementForm.value.content) return;
  try {
    if (editingAnnouncementId.value) {
      await updateAnnouncement(editingAnnouncementId.value, announcementForm.value);
    } else {
      await createAnnouncement(announcementForm.value);
    }
    cancelEdit();
    await loadAll();
  } catch (err) {
    // ignore
  }
}

function startEdit(item) {
  editingAnnouncementId.value = item.id;
  announcementForm.value = {
    title: item.title,
    content: item.content,
    status: item.status,
    pinned: item.pinned
  };
}

function cancelEdit() {
  editingAnnouncementId.value = null;
  announcementForm.value = { title: '', content: '', status: 'published', pinned: false };
}

async function removeAnnouncement(id) {
  if (!confirm('确定要删除该公告吗？')) return;
  try {
    await deleteAnnouncement(id);
    await loadAll();
  } catch (err) {
    toast.error('删除公告失败');
  }
}

async function toggleAnnouncementStatus(item) {
  const status = item.status === 'published' ? 'draft' : 'published';
  try {
    await updateAnnouncement(item.id, {
      ...item,
      status
    });
    await loadAll();
  } catch (err) {
    // ignore
  }
}

async function review(item, status) {
  const result = status === 'approved' ? '学校核验通过' : '学校核验驳回';
  try {
    await updateVerificationRequest(item.id, { status, result });
    await loadAll();
  } catch (err) {
    // ignore
  }
}

onMounted(loadAll);
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

.layout {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.form-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent);
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 12px 0;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.item-main {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  width: 100%;
}

.reset-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--line);
}

.reset-input {
  max-width: 200px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--line);
}

.eval-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.eval-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fafcfb;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.analytics-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 8px 0 16px;
}

.analytics-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--line);
}

.funnel-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 8px 0 16px;
}

.funnel-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 10px 16px;
  border: 1px solid var(--line);
  border-radius: 12px;
  min-width: 80px;
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

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
