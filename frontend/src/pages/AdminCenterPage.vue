<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
        <div>
          <h1>管理中心</h1>
          <p>用户管理、公告管理、学生核验审批。</p>
        </div>
        <button class="btn" @click="loadAll">刷新数据</button>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="module-tabs">
          <button
            v-for="tab in adminTabs"
            :key="tab.key"
            type="button"
            class="module-btn"
            :class="{ active: activeTab === tab.key }"
            @click="switchTab(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="overview-strip">
          <article class="kpi-chip">
            <span class="mono">用户总数</span>
            <strong>{{ users.length }}</strong>
          </article>
          <article class="kpi-chip">
            <span class="mono">公告数量</span>
            <strong>{{ announcements.length }}</strong>
          </article>
          <article class="kpi-chip">
            <span class="mono">待处理核验</span>
            <strong>{{ pendingVerificationCount }}</strong>
          </article>
          <article class="kpi-chip">
            <span class="mono">日志条数</span>
            <strong>{{ operationLogs.length }}</strong>
          </article>
          <article class="kpi-chip kpi-meta">
            <span class="mono">最近刷新</span>
            <strong>{{ lastLoadedAt || '--' }}</strong>
          </article>
        </div>

        <div class="grid layout">
        <div class="card" v-if="activeTab === 'overview' && enhancedStats">
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

        <div class="card" v-if="activeTab === 'users'">
          <div class="section-header compact">
            <h3>用户管理</h3>
            <span class="mono">共 {{ filteredUsers.length }} 人 · 第 {{ userPage }} / {{ userTotalPages }} 页</span>
          </div>
          <div class="toolbar-row">
            <input v-model="userKeyword" placeholder="搜索姓名 / 邮箱 / 角色" />
            <select v-model="userSort">
              <option value="latest">按最新注册</option>
              <option value="name">按姓名</option>
              <option value="role">按角色</option>
            </select>
          </div>
          <DataTable
            :columns="userColumns"
            :rows="pagedUsers"
            row-key="id"
            :loading="usersLoading"
            :loading-rows="4"
            empty-text="暂无用户"
            v-model:page="userPage"
            :total-pages="userTotalPages"
            row-class="admin-row"
          >
            <template #row="{ row: user, gridTemplate }">
              <div class="admin-row-grid user-row-grid" :style="{ gridTemplateColumns: gridTemplate }">
                <div>
                  <strong>{{ user.name || '未命名用户' }}</strong>
                  <p class="mono">{{ user.role || '--' }} · {{ user.email || '--' }}</p>
                </div>
                <div>
                  <span class="status-chip" :class="{ disabled: user.status !== 'active' }">
                    {{ userStatusLabel(user.status) }}
                  </span>
                </div>
                <div class="actions">
                  <button class="btn btn-outline" @click.stop="toggleUserStatus(user)">
                    {{ user.status === 'active' ? '禁用' : '启用' }}
                  </button>
                  <button class="btn btn-outline" @click.stop="resetPasswordId = resetPasswordId === user.id ? null : user.id">
                    重置密码
                  </button>
                </div>
              </div>
              <div v-if="resetPasswordId === user.id" class="reset-row" @click.stop>
                <input v-model="resetPasswordValue" type="password" placeholder="新密码（至少6位）" minlength="6" class="reset-input" />
                <button class="btn" @click="doResetPassword(user.id)">确认重置</button>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="card" v-if="activeTab === 'announcements'">
          <div class="section-header compact">
            <h3>公告管理</h3>
            <span class="mono">共 {{ filteredAnnouncements.length }} 条 · 第 {{ announcementPage }} / {{ announcementTotalPages }} 页</span>
          </div>
          <div class="form-grid">
            <input v-model="announcementForm.title" placeholder="公告标题" />
            <select v-model="announcementForm.status">
              <option v-for="item in announcementStatusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </div>
          <textarea v-model="announcementForm.content" rows="3" placeholder="公告内容"></textarea>
          <div class="action-row">
            <label class="checkbox">
              <input type="checkbox" v-model="announcementForm.pinned" />
              置顶
            </label>
            <div class="actions">
              <button class="btn" @click="createNewAnnouncement">{{ editingAnnouncementId ? "保存公告" : "发布公告" }}</button>
              <button v-if="editingAnnouncementId" class="btn btn-outline" @click="cancelEdit">取消编辑</button>
            </div>
          </div>
          <div class="toolbar-row">
            <input v-model="announcementKeyword" placeholder="搜索标题 / 内容" />
            <select v-model="announcementSort">
              <option value="latest">按最新</option>
              <option value="pinned">按是否置顶</option>
              <option value="status">按状态</option>
              <option value="title">按标题</option>
            </select>
          </div>
          <DataTable
            :columns="announcementColumns"
            :rows="pagedAnnouncements"
            row-key="id"
            :loading="false"
            empty-text="暂无公告"
            v-model:page="announcementPage"
            :total-pages="announcementTotalPages"
            row-class="admin-row"
          >
            <template #row="{ row: item, gridTemplate }">
              <div class="admin-row-grid announcement-row-grid" :style="{ gridTemplateColumns: gridTemplate }">
                <div>
                  <strong>{{ item.title || '未命名公告' }}</strong>
                  <p class="mono announcement-content">{{ announcementPreview(item.content) }}</p>
                  <p class="mono announcement-meta">{{ item.pinned ? '置顶公告' : '普通公告' }} · {{ formatTime(item.update_time || item.updated_at || item.create_time) }}</p>
                </div>
                <div>
                  <span class="status-chip" :class="{ disabled: item.status !== 'published' }">
                    {{ announcementStatusLabel(item.status) }}
                  </span>
                </div>
                <div class="actions">
                  <button class="btn btn-outline" @click.stop="startEdit(item)">编辑</button>
                  <button class="btn btn-outline" @click.stop="toggleAnnouncementStatus(item)">
                    {{ item.status === 'published' ? '撤回' : '发布' }}
                  </button>
                  <button class="btn btn-outline" @click.stop="removeAnnouncement(item.id)">删除</button>
                </div>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="card" v-if="activeTab === 'verifications'">
          <div class="section-header compact">
            <h3>学生核验审批</h3>
            <span class="mono">共 {{ filteredVerificationRequests.length }} 条 · 第 {{ verificationPage }} / {{ verificationTotalPages }} 页</span>
          </div>
          <div class="toolbar-row">
            <input v-model="verificationKeyword" placeholder="搜索请求ID / 企业ID / 学生ID / 字段" />
            <select v-model="verificationStatus">
              <option value="">全部状态</option>
              <option value="pending">待审核</option>
              <option value="approved">已通过</option>
              <option value="rejected">已驳回</option>
            </select>
          </div>
          <DataTable
            :columns="verificationColumns"
            :rows="pagedVerificationRequests"
            row-key="id"
            :loading="false"
            empty-text="暂无核验请求"
            v-model:page="verificationPage"
            :total-pages="verificationTotalPages"
            row-class="admin-row"
          >
            <template #row="{ row: item, gridTemplate }">
              <div class="admin-row-grid verification-row-grid" :style="{ gridTemplateColumns: gridTemplate }">
                <div>
                  <strong>请求 #{{ item.id }}</strong>
                  <p class="mono">企业 {{ item.company_id }} -> 学生 {{ item.student_id }}</p>
                  <p class="mono">字段：{{ (item.fields || []).join(', ') || '无' }}</p>
                </div>
                <div>
                  <StatusPill kind="verify" :status="item.status" />
                </div>
                <div class="actions">
                  <button class="btn btn-outline" :disabled="item.status === 'approved'" @click.stop="review(item, 'approved')">通过</button>
                  <button class="btn btn-outline" :disabled="item.status === 'rejected'" @click.stop="review(item, 'rejected')">驳回</button>
                </div>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="card" v-if="activeTab === 'algorithm'">
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

        <div class="card" v-if="activeTab === 'logs'">
          <div class="section-header compact">
            <h3>操作日志</h3>
            <span class="mono">共 {{ filteredOperationLogs.length }} 条 · 第 {{ logPage }} / {{ logTotalPages }} 页</span>
          </div>
          <div class="toolbar-row">
            <input v-model="logKeyword" placeholder="搜索动作 / 目标类型 / 详情 / 用户ID" />
            <select v-model="logSort">
              <option value="latest">按最新记录</option>
              <option value="action">按动作名称</option>
            </select>
          </div>
          <DataTable
            :columns="logColumns"
            :rows="pagedOperationLogs"
            row-key="id"
            :loading="false"
            empty-text="暂无日志记录"
            v-model:page="logPage"
            :total-pages="logTotalPages"
            row-class="admin-row"
          >
            <template #row="{ row: log, gridTemplate }">
              <div class="admin-row-grid log-row-grid" :style="{ gridTemplateColumns: gridTemplate }">
                <div>
                  <strong>{{ log.action || '未知动作' }}</strong>
                  <p class="mono">用户 {{ log.user_id || '--' }} · {{ log.target_type || '--' }} #{{ log.target_id || '--' }}</p>
                  <p class="mono">{{ log.detail || '无详细说明' }}</p>
                </div>
                <div class="mono">{{ formatTime(log.create_time) }}</div>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="card section-card" v-if="activeTab === 'algorithm'">
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

        <div class="card section-card" v-if="activeTab === 'overview'">
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
              <span class="tag" v-for="item in analytics.skill_gap" :key="item.skill" style="background:rgba(24,160,88,0.1);color:#0f8f59">
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
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
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
import DataTable from '../components/DataTable.vue';
import StatusPill from '../components/StatusPill.vue';
import { applicationStatusLabel as getApplicationStatusLabel } from '../constants/status';
import toast from '../utils/toast';

const route = useRoute();
const router = useRouter();
const adminTabs = [
  { key: 'overview', label: '平台概览' },
  { key: 'users', label: '用户管理' },
  { key: 'announcements', label: '公告管理' },
  { key: 'verifications', label: '核验审批' },
  { key: 'algorithm', label: '算法配置' },
  { key: 'logs', label: '操作日志' }
];
const activeTab = ref('overview');

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
const usersLoading = ref(false);
const lastLoadedAt = ref('');
const userKeyword = ref('');
const userSort = ref('latest');
const userPage = ref(1);
const USER_PAGE_SIZE = 8;
const announcementKeyword = ref('');
const announcementSort = ref('latest');
const announcementPage = ref(1);
const ANNOUNCEMENT_PAGE_SIZE = 6;
const verificationKeyword = ref('');
const verificationStatus = ref('');
const verificationPage = ref(1);
const VERIFICATION_PAGE_SIZE = 8;
const logKeyword = ref('');
const logSort = ref('latest');
const logPage = ref(1);
const LOG_PAGE_SIZE = 10;
const announcementStatusOptions = [
  { value: 'published', label: '已发布' },
  { value: 'draft', label: '草稿' }
];
const userColumns = [
  { key: 'user', label: '用户信息', width: '1.8fr' },
  { key: 'status', label: '状态', width: 'auto' },
  { key: 'actions', label: '操作', width: 'auto' }
];
const announcementColumns = [
  { key: 'announcement', label: '公告内容', width: '1.8fr' },
  { key: 'status', label: '状态', width: 'auto' },
  { key: 'actions', label: '操作', width: 'auto' }
];
const verificationColumns = [
  { key: 'request', label: '核验请求', width: '1.8fr' },
  { key: 'status', label: '审批状态', width: 'auto' },
  { key: 'actions', label: '操作', width: 'auto' }
];
const logColumns = [
  { key: 'detail', label: '日志详情', width: '2fr' },
  { key: 'time', label: '时间', width: 'auto' }
];
const pendingVerificationCount = computed(() => verifyRequests.value.filter((item) => item.status === 'pending').length);

const filteredUsers = computed(() => {
  const keyword = String(userKeyword.value || '').trim().toLowerCase();
  if (!keyword) return users.value;
  return users.value.filter((user) => {
    const target = [user.name, user.email, user.role]
      .map((item) => String(item || '').toLowerCase())
      .join(' ');
    return target.includes(keyword);
  });
});

const sortedUsers = computed(() => {
  const rows = [...filteredUsers.value];
  if (userSort.value === 'name') {
    return rows.sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'zh-CN'));
  }
  if (userSort.value === 'role') {
    return rows.sort((a, b) => String(a.role || '').localeCompare(String(b.role || ''), 'zh-CN'));
  }
  return rows.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
});

const userTotalPages = computed(() => Math.max(1, Math.ceil(sortedUsers.value.length / USER_PAGE_SIZE)));

const pagedUsers = computed(() => {
  const page = Math.min(userPage.value, userTotalPages.value);
  const start = (page - 1) * USER_PAGE_SIZE;
  return sortedUsers.value.slice(start, start + USER_PAGE_SIZE);
});

const filteredAnnouncements = computed(() => {
  const keyword = String(announcementKeyword.value || '').trim().toLowerCase();
  if (!keyword) return announcements.value;
  return announcements.value.filter((item) => {
    const target = [item.title, item.content, announcementStatusLabel(item.status)]
      .map((value) => String(value || '').toLowerCase())
      .join(' ');
    return target.includes(keyword);
  });
});

const sortedAnnouncements = computed(() => {
  const rows = [...filteredAnnouncements.value];
  if (announcementSort.value === 'title') {
    return rows.sort((a, b) => String(a.title || '').localeCompare(String(b.title || ''), 'zh-CN'));
  }
  if (announcementSort.value === 'status') {
    const order = { published: 0, draft: 1 };
    return rows.sort((a, b) => (order[a.status] ?? 9) - (order[b.status] ?? 9));
  }
  if (announcementSort.value === 'pinned') {
    return rows.sort((a, b) => Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)));
  }
  return rows.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
});

const announcementTotalPages = computed(() => Math.max(1, Math.ceil(sortedAnnouncements.value.length / ANNOUNCEMENT_PAGE_SIZE)));

const pagedAnnouncements = computed(() => {
  const page = Math.min(announcementPage.value, announcementTotalPages.value);
  const start = (page - 1) * ANNOUNCEMENT_PAGE_SIZE;
  return sortedAnnouncements.value.slice(start, start + ANNOUNCEMENT_PAGE_SIZE);
});

const filteredVerificationRequests = computed(() => {
  const keyword = String(verificationKeyword.value || '').trim().toLowerCase();
  const status = String(verificationStatus.value || '');
  return verifyRequests.value.filter((item) => {
    if (status && item.status !== status) return false;
    if (!keyword) return true;
    const target = [
      item.id,
      item.company_id,
      item.student_id,
      (item.fields || []).join(' ')
    ]
      .map((value) => String(value || '').toLowerCase())
      .join(' ');
    return target.includes(keyword);
  });
});

const sortedVerificationRequests = computed(() => {
  const rows = [...filteredVerificationRequests.value];
  return rows.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
});

const verificationTotalPages = computed(() => Math.max(1, Math.ceil(sortedVerificationRequests.value.length / VERIFICATION_PAGE_SIZE)));

const pagedVerificationRequests = computed(() => {
  const page = Math.min(verificationPage.value, verificationTotalPages.value);
  const start = (page - 1) * VERIFICATION_PAGE_SIZE;
  return sortedVerificationRequests.value.slice(start, start + VERIFICATION_PAGE_SIZE);
});

const filteredOperationLogs = computed(() => {
  const keyword = String(logKeyword.value || '').trim().toLowerCase();
  if (!keyword) return operationLogs.value;
  return operationLogs.value.filter((log) => {
    const target = [log.action, log.target_type, log.detail, log.user_id, log.target_id]
      .map((value) => String(value || '').toLowerCase())
      .join(' ');
    return target.includes(keyword);
  });
});

const sortedOperationLogs = computed(() => {
  const rows = [...filteredOperationLogs.value];
  if (logSort.value === 'action') {
    return rows.sort((a, b) => String(a.action || '').localeCompare(String(b.action || ''), 'zh-CN'));
  }
  return rows.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
});

const logTotalPages = computed(() => Math.max(1, Math.ceil(sortedOperationLogs.value.length / LOG_PAGE_SIZE)));

const pagedOperationLogs = computed(() => {
  const page = Math.min(logPage.value, logTotalPages.value);
  const start = (page - 1) * LOG_PAGE_SIZE;
  return sortedOperationLogs.value.slice(start, start + LOG_PAGE_SIZE);
});

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
  } catch (e) {
    toast.error('推荐配置加载失败');
  }
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
  return getApplicationStatusLabel(status);
}

function formatTime(value) {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 16);
}

function announcementStatusLabel(status) {
  if (status === 'published') return '已发布';
  if (status === 'draft') return '草稿';
  return status || '未知';
}

function userStatusLabel(status) {
  return status === 'active' ? '正常' : '已禁用';
}

function announcementPreview(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text) return '暂无内容';
  if (text.length <= 70) return text;
  return `${text.slice(0, 70)}...`;
}

function switchTab(key, options = { syncRoute: true }) {
  const { syncRoute = true } = options;
  if (!adminTabs.some((item) => item.key === key)) return;
  activeTab.value = key;
  if (syncRoute && route.query.tab !== key) {
    router.replace({ query: { ...route.query, tab: key } });
  }
}

async function loadAll() {
  userPage.value = 1;
  announcementPage.value = 1;
  verificationPage.value = 1;
  logPage.value = 1;
  usersLoading.value = true;
  try {
    users.value = await fetchUsers();
  } catch (err) {
    users.value = [];
  } finally {
    usersLoading.value = false;
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
  lastLoadedAt.value = formatTime(new Date().toISOString());
}

async function toggleUserStatus(user) {
  const status = user.status === 'active' ? 'disabled' : 'active';
  try {
    await updateUserStatus(user.id, { status });
    await loadAll();
    toast.success(`用户已${status === 'active' ? '启用' : '禁用'}`);
  } catch (err) {
    toast.error('用户状态更新失败');
  }
}

async function createNewAnnouncement() {
  if (!announcementForm.value.title || !announcementForm.value.content) {
    toast.warn('请填写公告标题和内容');
    return;
  }
  try {
    if (editingAnnouncementId.value) {
      await updateAnnouncement(editingAnnouncementId.value, announcementForm.value);
      toast.success('公告已更新');
    } else {
      await createAnnouncement(announcementForm.value);
      toast.success('公告已发布');
    }
    cancelEdit();
    await loadAll();
  } catch (err) {
    toast.error('公告保存失败');
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
    toast.success(status === 'published' ? '公告已发布' : '公告已撤回');
  } catch (err) {
    toast.error('公告状态更新失败');
  }
}

async function review(item, status) {
  const result = status === 'approved' ? '学校核验通过' : '学校核验驳回';
  try {
    await updateVerificationRequest(item.id, { status, result });
    await loadAll();
    toast.success(status === 'approved' ? '核验已通过' : '核验已驳回');
  } catch (err) {
    toast.error('核验操作失败');
  }
}

watch([userKeyword, userSort], () => {
  userPage.value = 1;
});

watch([announcementKeyword, announcementSort], () => {
  announcementPage.value = 1;
});

watch([verificationKeyword, verificationStatus], () => {
  verificationPage.value = 1;
});

watch([logKeyword, logSort], () => {
  logPage.value = 1;
});

watch(userTotalPages, (total) => {
  if (userPage.value > total) userPage.value = total;
});

watch(announcementTotalPages, (total) => {
  if (announcementPage.value > total) announcementPage.value = total;
});

watch(verificationTotalPages, (total) => {
  if (verificationPage.value > total) verificationPage.value = total;
});

watch(logTotalPages, (total) => {
  if (logPage.value > total) logPage.value = total;
});

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab !== 'string') return;
    if (tab === activeTab.value) return;
    switchTab(tab, { syncRoute: false });
  }
);

onMounted(() => {
  const tab = route.query.tab;
  if (typeof tab === 'string') {
    switchTab(tab, { syncRoute: false });
  }
  loadAll();
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

.layout {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.module-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.overview-strip {
  margin-bottom: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}

.kpi-chip {
  border: 1px solid #d5edde;
  background: #fff;
  border-radius: 14px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: 0 8px 20px rgba(15, 122, 70, 0.05);
}

.kpi-chip strong {
  color: var(--accent-dark);
  font-size: 24px;
  line-height: 1.1;
}

.kpi-chip.kpi-meta strong {
  font-size: 14px;
  color: #436757;
}

.module-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
}

.module-btn.active {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
  font-weight: 600;
}

.form-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr;
}

.form-grid select {
  width: 100%;
  height: 46px;
  border-radius: 12px;
  border: 1px solid var(--line);
  padding: 0 12px;
  background: #fff;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.toolbar-row {
  margin-bottom: 10px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.toolbar-row select {
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--line);
  padding: 0 12px;
  background: #fff;
}

.action-row {
  margin-top: 10px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
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

.admin-row-grid {
  display: grid;
  gap: 12px;
  align-items: center;
}

.admin-row-grid > div {
  min-width: 0;
}

.announcement-content {
  margin-top: 4px;
}

.announcement-meta {
  margin-top: 4px;
  color: #7f918a;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
}

.status-chip.disabled {
  background: rgba(97, 109, 104, 0.12);
  color: #607168;
}

.reset-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
  flex-wrap: wrap;
}

.reset-input {
  min-width: 220px;
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

.section-header.compact {
  margin-bottom: 10px;
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

  .module-tabs {
    width: 100%;
  }

  .toolbar-row {
    grid-template-columns: 1fr;
  }

  .action-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
