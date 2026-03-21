<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
        <div>
          <h1>企业中心</h1>
          <p>通过模块切换管理企业资料、认证、候选人与数据分析。</p>
        </div>
        <button class="hero-primary-btn" :disabled="primaryActionLoading" @click="runPrimaryAction">
          <span class="hero-primary-dot"></span>
          <span>{{ primaryActionLabel }}</span>
        </button>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="module-tabs">
          <button
            v-for="tab in moduleTabs"
            :key="tab.key"
            type="button"
            class="module-btn"
            :class="{ active: activeModule === tab.key }"
            @click="switchModule(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="activeModule === 'profile'" class="profile-layout">
          <div class="card profile-side">
            <div class="profile-brand">
              <div class="brand-badge">{{ companyInitial }}</div>
              <div>
                <h3>{{ company.company_name || '未填写企业名称' }}</h3>
                <p class="mono">企业账号 #{{ company.user_id || '--' }}</p>
              </div>
            </div>
            <div class="status-chip" :class="statusClass(company.status)">
              {{ statusLabel(company.status) }}
            </div>
            <div class="completion-block">
              <div class="completion-head">
                <span class="mono">资料完整度</span>
                <strong>{{ profileCompletion }}%</strong>
              </div>
              <div class="completion-track">
                <div class="completion-bar" :style="{ width: `${profileCompletion}%` }"></div>
              </div>
            </div>
            <p class="mono">资料越完整，系统推荐的人才和岗位分析越准确。</p>
          </div>

          <div class="card profile-main">
            <div class="profile-section">
              <div class="section-head">
                <h3>基础信息</h3>
                <p>用于企业对外展示与校方审核。</p>
              </div>
              <div class="field-grid">
                <label class="field">
                  <span>企业名称</span>
                  <input v-model="company.company_name" placeholder="请输入企业名称" />
                </label>
                <label class="field">
                  <span>统一信用代码</span>
                  <input v-model="company.credit_code" placeholder="请输入统一信用代码" />
                </label>
                <label class="field">
                  <span>所属行业</span>
                  <input v-model="company.industry" placeholder="如：互联网 / 智能制造" />
                </label>
                <label class="field">
                  <span>企业规模</span>
                  <input v-model="company.scale" placeholder="如：100-500人" />
                </label>
                <label class="field">
                  <span>企业地址</span>
                  <input v-model="company.address" placeholder="请输入企业地址" />
                </label>
                <label class="field">
                  <span>企业官网</span>
                  <input v-model="company.website" placeholder="https://example.com" />
                </label>
              </div>
            </div>

            <div class="profile-section">
              <div class="section-head">
                <h3>联系人信息</h3>
              </div>
              <div class="field-grid">
                <label class="field">
                  <span>联系人</span>
                  <input v-model="company.contact_name" placeholder="请输入联系人姓名" />
                </label>
                <label class="field">
                  <span>联系电话</span>
                  <input v-model="company.contact_phone" placeholder="请输入联系电话" />
                </label>
              </div>
            </div>

            <div class="profile-section">
              <div class="section-head">
                <h3>企业简介</h3>
              </div>
              <label class="field field-full">
                <span>对外介绍</span>
                <textarea v-model="company.description" rows="4" placeholder="介绍企业业务、团队特点、招聘方向"></textarea>
              </label>
            </div>

            <div class="profile-section">
              <div class="section-head">
                <h3>资质与素材</h3>
              </div>
              <div class="upload-grid">
                <label class="upload-card">
                  <div class="upload-title">营业执照</div>
                  <div class="upload-meta mono">{{ company.license_url ? simplifyAsset(company.license_url) : '未上传' }}</div>
                  <span class="upload-btn">{{ company.license_url ? '重新上传' : '上传执照' }}</span>
                  <input type="file" accept=".pdf,.png,.jpg,.jpeg" @change="uploadLicense" />
                </label>
                <label class="upload-card">
                  <div class="upload-title">企业宣传图</div>
                  <div class="upload-meta mono">{{ company.promo_image_url ? simplifyAsset(company.promo_image_url) : '未上传' }}</div>
                  <span class="upload-btn">{{ company.promo_image_url ? '重新上传' : '上传宣传图' }}</span>
                  <input type="file" accept=".png,.jpg,.jpeg" @change="uploadPromoImage" />
                </label>
              </div>
            </div>

            <div class="profile-section">
              <div class="section-head">
                <h3>福利标签</h3>
              </div>
              <div class="welfare-editor">
                <input
                  v-model="welfareInput"
                  placeholder="输入福利后回车，例如：弹性工作"
                  @keyup.enter="addWelfare"
                />
                <button type="button" class="btn btn-outline" @click="addWelfare">添加</button>
              </div>
              <div class="welfare-tags">
                <div v-for="tag in company.welfare_tags" :key="tag" class="welfare-tag">
                  <span>{{ tag }}</span>
                  <button type="button" @click="removeWelfare(tag)">x</button>
                </div>
                <span v-if="!company.welfare_tags?.length" class="mono">暂未设置福利标签</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeModule === 'certification'" class="card">
          <h3>认证状态</h3>
          <p class="mono">当前状态：{{ statusLabel(company.status) }}</p>
          <button class="btn btn-outline" @click="submitCertification">提交认证</button>
          <div class="divider"></div>
          <h3>推荐人才</h3>
          <div v-if="recommendations.length === 0" class="mono">暂无推荐</div>
          <div v-else class="talent" v-for="talent in recommendations" :key="talent.student_id">
            <div>
              <strong>{{ talent.name }}</strong>
              <p class="mono">{{ talent.major }} · {{ talent.grade }}</p>
            </div>
            <div class="actions">
              <span class="tag mono">匹配度 {{ talent.match_score }}%</span>
              <button class="btn btn-outline" @click="requestVerify(talent.student_id)">申请核验</button>
            </div>
          </div>
          <div class="divider"></div>
          <h3>核验请求</h3>
          <div v-if="verifyRequests.length === 0" class="mono">暂无核验请求</div>
          <div v-else class="talent" v-for="item in verifyRequests" :key="item.id">
            <div>
              <strong>请求 #{{ item.id }}</strong>
              <p class="mono">学生 {{ item.student_id }} · 字段 {{ (item.fields || []).join(', ') || '无' }}</p>
            </div>
            <StatusPill kind="verify" :status="item.status" />
          </div>
        </div>

        <div v-else-if="activeModule === 'candidates'" class="card">
          <div class="candidate-head">
            <h3>候选人筛选</h3>
            <span class="mono">共 {{ filteredCandidates.length }} 人 · 第 {{ candidatePage }} / {{ candidateTotalPages }} 页</span>
          </div>
          <div class="form-grid">
            <input v-model="candidateFilters.school" placeholder="学校筛选" />
            <input v-model="candidateFilters.major" placeholder="专业筛选" />
            <input v-model="candidateFilters.skill" placeholder="技能筛选（单个）" />
            <select v-model="candidateFilters.status">
              <option value="">投递状态</option>
              <option v-for="item in candidateStatusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </div>
          <div class="candidate-toolbar">
            <input v-model="candidateKeyword" placeholder="搜索：姓名 / 岗位 / 学校 / 专业" />
            <div class="actions">
              <select v-model="candidateSort">
                <option value="latest">按最新投递</option>
                <option value="oldest">按最早投递</option>
                <option value="name_asc">按姓名 A-Z</option>
                <option value="status">按流程状态</option>
              </select>
              <button class="btn btn-outline" :disabled="candidateLoading" @click="loadCandidates">{{ candidateLoading ? '筛选中...' : '筛选' }}</button>
              <button class="btn btn-outline" @click="clearCandidateFilters">清空条件</button>
            </div>
          </div>
          <div v-if="filteredCandidates.length" class="batch-toolbar">
            <label class="batch-check" @click.stop>
              <input type="checkbox" :checked="allVisibleSelected" @change="toggleSelectAllVisible($event.target.checked)" />
              本页全选
            </label>
            <span class="mono">已选 {{ selectedCandidateIds.length }} 人</span>
            <select v-model="batchStatusDraft">
              <option value="">批量更新到</option>
              <option v-for="item in candidateStatusOptions" :key="`batch-${item.value}`" :value="item.value">{{ item.label }}</option>
            </select>
            <button class="btn btn-outline" :disabled="batchUpdating" @click="applyBatchStatus">
              {{ batchUpdating ? '批量更新中...' : '批量更新状态' }}
            </button>
          </div>

          <DataTable
            :columns="candidateColumns"
            :rows="pagedCandidates"
            row-key="application_id"
            :loading="candidateLoading && !candidates.length"
            :loading-rows="4"
            empty-text="暂无候选人记录"
            v-model:page="candidatePage"
            :total-pages="candidateTotalPages"
            row-class="candidate-row"
            clickable
            @row-click="handleCandidateRowClick"
          >
            <template #row="{ row: item, gridTemplate }">
              <div class="candidate-row-grid" :style="{ gridTemplateColumns: gridTemplate }">
                <div class="candidate-main">
                  <label class="row-check" @click.stop>
                    <input
                      type="checkbox"
                      :checked="isCandidateSelected(item.application_id)"
                      @change="toggleCandidateSelection(item.application_id, $event.target.checked)"
                    />
                  </label>
                  <div class="candidate-col">
                    <strong>{{ item.student_name }} · {{ item.job_name }}</strong>
                    <p class="mono">{{ candidateMeta(item) }}</p>
                  </div>
                </div>
                <div class="candidate-col">
                  <p class="mono">{{ item.school }} · {{ item.major }} · {{ item.grade }}</p>
                </div>
                <div class="candidate-col">
                  <p class="mono">{{ (item.skills || []).join(', ') || '无' }}</p>
                </div>
                <div class="candidate-status-col">
                  <StatusPill kind="application" :status="item.status" />
                </div>
                <div class="candidate-action-col">
                  <button type="button" class="btn btn-outline" @click.stop="openCandidateDetail(item.application_id)">查看简历与流程</button>
                </div>
              </div>
            </template>
          </DataTable>
        </div>

        <div v-else class="card analytics-shell">
          <div class="analytics-head">
            <div>
              <h3>数据分析</h3>
              <p>统一查看岗位曝光、投递转化、人才来源和趋势变化。</p>
            </div>
            <button class="btn btn-outline analytics-refresh" @click="loadAnalytics()" :disabled="analyticsLoading">
              {{ analyticsLoading ? '刷新中...' : '刷新数据' }}
            </button>
          </div>

          <div v-if="companyAnalytics" class="analytics-content">
            <div class="analytics-overview">
              <div class="analytics-kpi">
                <span class="mono">岗位数</span>
                <strong>{{ analyticsSummary.totalJobs }}</strong>
              </div>
              <div class="analytics-kpi">
                <span class="mono">总浏览</span>
                <strong>{{ analyticsSummary.totalViews }}</strong>
              </div>
              <div class="analytics-kpi">
                <span class="mono">总投递</span>
                <strong>{{ analyticsSummary.totalApplications }}</strong>
              </div>
              <div class="analytics-kpi">
                <span class="mono">平均转化率</span>
                <strong>{{ analyticsSummary.avgConversion }}%</strong>
              </div>
            </div>

            <div class="analytics-block">
              <h4>岗位表现</h4>
              <div v-if="(companyAnalytics.job_stats || []).length === 0" class="mono">暂无岗位数据</div>
              <div v-else class="job-stat-list">
                <div v-for="js in companyAnalytics.job_stats" :key="js.job_id" class="job-stat-item">
                  <div class="job-stat-head">
                    <strong>{{ js.job_name }}</strong>
                    <span class="mono">浏览 {{ js.views }} · 投递 {{ js.applications }} · 转化 {{ js.conversion_rate }}%</span>
                  </div>
                  <div class="analytics-track">
                    <div class="analytics-fill" :style="{ width: `${barPercent(js.views, maxJobViews)}%` }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="analytics-two-col">
              <div class="analytics-block">
                <h4>人才来源</h4>
                <div v-if="(companyAnalytics.talent_source || []).length === 0" class="mono">暂无人才来源数据</div>
                <div v-else class="source-list">
                  <div v-for="ts in companyAnalytics.talent_source" :key="`${ts.type}-${ts.name}`" class="source-item">
                    <div class="source-head">
                      <span>{{ ts.name }}</span>
                      <span class="tag mono">{{ sourceTypeLabel(ts.type) }} · {{ ts.count }}人</span>
                    </div>
                    <div class="analytics-track">
                      <div class="analytics-fill soft" :style="{ width: `${barPercent(ts.count, maxSourceCount)}%` }"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="analytics-block">
                <h4>招聘漏斗</h4>
                <div class="funnel-list">
                  <div v-for="f in companyAnalytics.funnel" :key="f.status" class="funnel-item">
                    <div class="source-head">
                      <span>{{ funnelLabel(f.status) }}</span>
                      <strong class="mono">{{ f.count }}</strong>
                    </div>
                    <div class="analytics-track">
                      <div class="analytics-fill warm" :style="{ width: `${barPercent(f.count, maxFunnelCount)}%` }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="analytics-block">
              <h4>近 6 个月投递趋势</h4>
              <div v-if="(companyAnalytics.trend || []).length === 0" class="mono">暂无趋势数据</div>
              <div v-else class="trend-grid">
                <div v-for="item in companyAnalytics.trend" :key="item.month" class="trend-item">
                  <div class="trend-bar-wrap">
                    <div class="trend-bar" :style="{ height: `${barPercent(item.application_count, maxTrendCount)}%` }"></div>
                  </div>
                  <strong class="mono">{{ item.application_count }}</strong>
                  <span class="mono">{{ item.month }}</span>
                </div>
              </div>
            </div>

            <p class="mono analytics-time">最后更新时间：{{ analyticsUpdatedAt || '刚刚' }}</p>
          </div>

          <div v-else class="empty-analytics">
            <h4>暂无分析数据</h4>
            <p>点击右上角“刷新数据”获取最新统计。</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createVerificationRequest,
  fetchCompany,
  fetchCompanyApplications,
  fetchCompanyRecommendations,
  fetchCompanyVerificationRequests,
  submitCompanyCertification,
  updateApplicationStatus,
  updateCompany,
  uploadFile,
  fetchCompanyAnalytics,
} from "../services/api";
import { useAuth } from "../store/auth";
import DataTable from "../components/DataTable.vue";
import StatusPill from "../components/StatusPill.vue";
import {
  APPLICATION_STATUS_OPTIONS,
  applicationStatusLabel as getApplicationStatusLabel,
  companyStatusLabel as getCompanyStatusLabel,
  canApplicationStatusTransition
} from "../constants/status";
import toast from '../utils/toast';

const auth = useAuth();
const route = useRoute();
const router = useRouter();
const activeModule = ref('profile');
const moduleTabs = [
  { key: 'profile', label: '企业资料' },
  { key: 'certification', label: '认证与推荐' },
  { key: 'candidates', label: '候选人筛选' },
  { key: 'analytics', label: '数据分析' }
];
const candidateColumns = [
  { key: 'candidate', label: '候选人', width: '2fr' },
  { key: 'school', label: '学校专业', width: '1.4fr' },
  { key: 'skills', label: '技能', width: '1.2fr' },
  { key: 'status', label: '状态', width: 'auto' },
  { key: 'actions', label: '操作', width: 'auto' }
];
const candidateStatusOptions = APPLICATION_STATUS_OPTIONS;

const company = ref({
  user_id: auth.user.value?.id || 0,
  company_name: "",
  credit_code: "",
  license_url: "",
  contact_name: "",
  contact_phone: "",
  status: "pending",
  description: "",
  industry: "",
  scale: "",
  address: "",
  website: "",
  welfare_tags: []
});

const recommendations = ref([]);
const verifyRequests = ref([]);
const companyAnalytics = ref(null);
const analyticsLoading = ref(false);
const analyticsUpdatedAt = ref('');
const profileSaving = ref(false);
const certSubmitting = ref(false);
const candidateLoading = ref(false);
const welfareInput = ref('');

const companyInitial = computed(() => {
  const text = (company.value.company_name || '').trim();
  if (!text) return '企业';
  return text.slice(0, 2);
});

const profileCompletion = computed(() => {
  const fields = [
    company.value.company_name,
    company.value.credit_code,
    company.value.contact_name,
    company.value.contact_phone,
    company.value.industry,
    company.value.scale,
    company.value.address,
    company.value.website,
    company.value.description,
    company.value.license_url,
    company.value.promo_image_url
  ];
  const filled = fields.filter((item) => String(item || '').trim().length > 0).length;
  return Math.round((filled / fields.length) * 100);
});

const primaryActionLabel = computed(() => {
  if (activeModule.value === 'profile') return profileSaving.value ? '保存中...' : '保存资料';
  if (activeModule.value === 'certification') return certSubmitting.value ? '提交中...' : '提交认证';
  if (activeModule.value === 'candidates') return candidateLoading.value ? '筛选中...' : '筛选候选人';
  return analyticsLoading.value ? '加载中...' : '刷新分析';
});

const primaryActionLoading = computed(() => {
  if (activeModule.value === 'profile') return profileSaving.value;
  if (activeModule.value === 'certification') return certSubmitting.value;
  if (activeModule.value === 'candidates') return candidateLoading.value;
  return analyticsLoading.value;
});

const analyticsSummary = computed(() => {
  const data = companyAnalytics.value;
  if (!data) {
    return { totalJobs: 0, totalViews: 0, totalApplications: 0, avgConversion: 0 };
  }
  const jobStats = data.job_stats || [];
  const totalViews = jobStats.reduce((sum, item) => sum + (item.views || 0), 0);
  const totalApplications = jobStats.reduce((sum, item) => sum + (item.applications || 0), 0);
  const avgConversion = jobStats.length
    ? Math.round(jobStats.reduce((sum, item) => sum + (item.conversion_rate || 0), 0) / jobStats.length)
    : 0;
  return {
    totalJobs: jobStats.length,
    totalViews,
    totalApplications,
    avgConversion
  };
});

const maxJobViews = computed(() => {
  const rows = companyAnalytics.value?.job_stats || [];
  return Math.max(1, ...rows.map((item) => item.views || 0));
});

const maxSourceCount = computed(() => {
  const rows = companyAnalytics.value?.talent_source || [];
  return Math.max(1, ...rows.map((item) => item.count || 0));
});

const maxFunnelCount = computed(() => {
  const rows = companyAnalytics.value?.funnel || [];
  return Math.max(1, ...rows.map((item) => item.count || 0));
});

const maxTrendCount = computed(() => {
  const rows = companyAnalytics.value?.trend || [];
  return Math.max(1, ...rows.map((item) => item.application_count || 0));
});

const sourceTypeLabel = (type) => (type === 'school' ? '学校' : '专业');

function barPercent(value, max) {
  if (!value || !max) return 0;
  return Math.max(8, Math.round((value / max) * 100));
}

function funnelLabel(status) {
  return getApplicationStatusLabel(status);
}

function applicationStatusText(status) {
  return getApplicationStatusLabel(status);
}

function candidateMeta(item) {
  const timeText = formatTime(item?.apply_time || item?.create_time);
  if (timeText !== '--') return `投递时间：${timeText}`;
  return `申请编号：${item?.application_id || '--'}`;
}

function switchModule(key, options = { syncRoute: true }) {
  const { syncRoute = true } = options;
  if (!moduleTabs.some((item) => item.key === key)) return;
  activeModule.value = key;
  if (syncRoute && route.query.tab !== key) {
    router.replace({ query: { ...route.query, tab: key } });
  }
  if (key === 'analytics' && !companyAnalytics.value) {
    loadAnalytics({ silent: true });
  }
}

function runPrimaryAction() {
  if (activeModule.value === 'profile') {
    saveProfile();
    return;
  }
  if (activeModule.value === 'certification') {
    submitCertification();
    return;
  }
  if (activeModule.value === 'candidates') {
    loadCandidates();
    return;
  }
  loadAnalytics();
}

function openCandidateDetail(applicationId) {
  if (!applicationId) return;
  router.push(`/company-center/candidates/${applicationId}`);
}

function handleCandidateRowClick(payload) {
  const applicationId = payload?.row?.application_id;
  openCandidateDetail(applicationId);
}

async function loadAnalytics({ silent = false } = {}) {
  const targetCompanyId = company.value.user_id || auth.user.value?.id;
  if (!targetCompanyId) {
    toast.warn('未获取到企业身份，暂时无法加载数据分析');
    return;
  }
  analyticsLoading.value = true;
  try {
    companyAnalytics.value = await fetchCompanyAnalytics(targetCompanyId);
    analyticsUpdatedAt.value = new Date().toLocaleString('zh-CN', { hour12: false });
    if (!silent) toast.success('数据分析已刷新');
  } catch (e) {
    if (!silent) toast.error('加载分析失败');
  } finally {
    analyticsLoading.value = false;
  }
}
const candidateFilters = ref({
  school: "",
  major: "",
  skill: "",
  status: ""
});
const candidateKeyword = ref('');
const candidates = ref([]);
const candidatePage = ref(1);
const CANDIDATE_PAGE_SIZE = 8;
const selectedCandidateIds = ref([]);
const batchStatusDraft = ref('');
const batchUpdating = ref(false);
const candidateSort = ref('latest');

const filteredCandidates = computed(() => {
  const school = String(candidateFilters.value.school || '').trim().toLowerCase();
  const major = String(candidateFilters.value.major || '').trim().toLowerCase();
  const skill = String(candidateFilters.value.skill || '').trim().toLowerCase();
  const status = String(candidateFilters.value.status || '').trim();
  const keyword = String(candidateKeyword.value || '').trim().toLowerCase();

  return candidates.value.filter((item) => {
    const itemSchool = String(item.school || '').toLowerCase();
    const itemMajor = String(item.major || '').toLowerCase();
    const itemStatus = String(item.status || '');
    const skills = Array.isArray(item.skills) ? item.skills.map((entry) => String(entry || '').toLowerCase()) : [];
    const keywordTarget = [
      item.student_name,
      item.job_name,
      item.school,
      item.major
    ]
      .map((part) => String(part || '').toLowerCase())
      .join(' ');

    if (school && !itemSchool.includes(school)) return false;
    if (major && !itemMajor.includes(major)) return false;
    if (status && itemStatus !== status) return false;
    if (skill && !skills.some((entry) => entry.includes(skill))) return false;
    if (keyword && !keywordTarget.includes(keyword)) return false;
    return true;
  });
});

const sortedCandidates = computed(() => {
  const orderMap = candidateStatusOptions.reduce((acc, item, index) => {
    acc[item.value] = index;
    return acc;
  }, {});
  const rows = [...filteredCandidates.value];
  if (candidateSort.value === 'name_asc') {
    return rows.sort((a, b) => String(a.student_name || '').localeCompare(String(b.student_name || ''), 'zh-CN'));
  }
  if (candidateSort.value === 'status') {
    return rows.sort((a, b) => (orderMap[a.status] ?? 99) - (orderMap[b.status] ?? 99));
  }
  const factor = candidateSort.value === 'oldest' ? 1 : -1;
  return rows.sort((a, b) => (Number(a.application_id || 0) - Number(b.application_id || 0)) * factor);
});

const candidateTotalPages = computed(() => Math.max(1, Math.ceil(sortedCandidates.value.length / CANDIDATE_PAGE_SIZE)));

const pagedCandidates = computed(() => {
  const page = Math.min(candidatePage.value, candidateTotalPages.value);
  const start = (page - 1) * CANDIDATE_PAGE_SIZE;
  return sortedCandidates.value.slice(start, start + CANDIDATE_PAGE_SIZE);
});

const allVisibleSelected = computed(() => {
  if (!pagedCandidates.value.length) return false;
  return pagedCandidates.value.every((item) => selectedCandidateIds.value.includes(item.application_id));
});

async function loadCompany() {
  if (!company.value.user_id) return;
  try {
    company.value = await fetchCompany(company.value.user_id);
  } catch (err) {
    // keep defaults
  }
}

async function loadRecommendations() {
  if (!company.value.user_id) return;
  try {
    const result = await fetchCompanyRecommendations(company.value.user_id);
    recommendations.value = result.results || [];
  } catch (err) {
    recommendations.value = [];
    toast.warn('人才推荐加载失败');
  }
}

async function loadVerifyRequests() {
  if (!company.value.user_id) return;
  try {
    verifyRequests.value = await fetchCompanyVerificationRequests(company.value.user_id);
  } catch (err) {
    verifyRequests.value = [];
  }
}

async function loadCandidates() {
  if (!company.value.user_id) return;
  candidateLoading.value = true;
  try {
    candidates.value = await fetchCompanyApplications(candidateFilters.value);
    candidatePage.value = 1;
    selectedCandidateIds.value = [];
  } catch (err) {
    candidates.value = [];
    toast.warn('候选人加载失败');
  } finally {
    candidateLoading.value = false;
  }
}

function isCandidateSelected(applicationId) {
  return selectedCandidateIds.value.includes(applicationId);
}

function toggleCandidateSelection(applicationId, checked) {
  const next = new Set(selectedCandidateIds.value);
  if (checked) next.add(applicationId);
  else next.delete(applicationId);
  selectedCandidateIds.value = Array.from(next);
}

function toggleSelectAllVisible(checked) {
  const visibleIds = pagedCandidates.value.map((item) => item.application_id);
  const next = new Set(selectedCandidateIds.value);
  if (checked) {
    visibleIds.forEach((id) => next.add(id));
  } else {
    visibleIds.forEach((id) => next.delete(id));
  }
  selectedCandidateIds.value = Array.from(next);
}

async function applyBatchStatus() {
  const nextStatus = batchStatusDraft.value;
  if (!nextStatus) {
    toast.warn('请先选择目标状态');
    return;
  }
  if (!selectedCandidateIds.value.length) {
    toast.warn('请先勾选候选人');
    return;
  }
  const selectedSet = new Set(selectedCandidateIds.value);
  const selectedRows = candidates.value.filter((item) => selectedSet.has(item.application_id));
  const validRows = selectedRows.filter((item) => canApplicationStatusTransition(item.status, nextStatus));
  const skipped = selectedRows.length - validRows.length;

  if (!validRows.length) {
    toast.warn('所选候选人的当前状态不支持更新到该目标状态');
    return;
  }

  batchUpdating.value = true;
  let success = 0;
  let failed = 0;

  await Promise.all(
    validRows.map(async (item) => {
      try {
        await updateApplicationStatus(item.application_id, { status: nextStatus });
        success += 1;
      } catch (err) {
        failed += 1;
      }
    })
  );

  batchUpdating.value = false;

  if (success) {
    toast.success(`已更新 ${success} 位候选人为「${applicationStatusText(nextStatus)}」`);
  }
  if (skipped) {
    toast.info(`${skipped} 位候选人不满足流转条件，已跳过`);
  }
  if (failed) {
    toast.error(`${failed} 位候选人更新失败`);
  }

  await loadCandidates();
}

function clearCandidateFilters() {
  candidateFilters.value = {
    school: '',
    major: '',
    skill: '',
    status: ''
  };
  candidateKeyword.value = '';
  candidatePage.value = 1;
  selectedCandidateIds.value = [];
  loadCandidates();
}

async function saveProfile() {
  if (!company.value.user_id) return;
  profileSaving.value = true;
  try {
    await updateCompany(company.value.user_id, company.value);
    await loadCompany();
    toast.success('资料已保存');
  } catch (err) {
    toast.error('保存失败，请重试');
  } finally {
    profileSaving.value = false;
  }
}

async function submitCertification() {
  if (!company.value.user_id) return;
  certSubmitting.value = true;
  try {
    await submitCompanyCertification(company.value.user_id);
    await loadCompany();
    toast.success('认证申请已提交');
  } catch (err) {
    toast.error('提交失败，请重试');
  } finally {
    certSubmitting.value = false;
  }
}

async function requestVerify(studentId) {
  if (!company.value.user_id) return;
  try {
    await createVerificationRequest(company.value.user_id, {
      student_id: studentId,
      fields: ["school", "major", "grade", "student_no"]
    });
    await loadVerifyRequests();
    toast.success('核验请求已提交');
  } catch (err) {
    toast.error('核验请求提交失败');
  }
}

async function uploadLicense(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  try {
    const result = await uploadFile(file);
    company.value.license_url = result.file_url;
    await saveProfile();
  } catch (e) {
    toast.error('上传失败');
  }
}

async function uploadPromoImage(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  try {
    const result = await uploadFile(file);
    company.value.promo_image_url = result.file_url;
    await saveProfile();
  } catch (e) {
    toast.error('上传失败');
  }
}

function addWelfare() {
  const next = welfareInput.value.trim();
  if (!next) return;
  if ((company.value.welfare_tags || []).includes(next)) {
    toast.info('该福利标签已存在');
    return;
  }
  company.value.welfare_tags = [...(company.value.welfare_tags || []), next];
  welfareInput.value = '';
}

function removeWelfare(tag) {
  company.value.welfare_tags = (company.value.welfare_tags || []).filter((item) => item !== tag);
}

function statusClass(status) {
  if (status === 'approved') return 'is-approved';
  if (status === 'rejected') return 'is-rejected';
  if (status === 'disabled') return 'is-disabled';
  return 'is-pending';
}

function simplifyAsset(url) {
  if (!url) return '未上传';
  const clean = String(url).split('?')[0];
  const parts = clean.split('/');
  return parts[parts.length - 1] || clean;
}

function statusLabel(status) {
  return getCompanyStatusLabel(status);
}

function formatTime(value) {
  if (!value) return '--';
  return String(value).replace('T', ' ').slice(0, 16);
}

onMounted(async () => {
  const tab = route.query.tab;
  if (typeof tab === 'string' && moduleTabs.some((item) => item.key === tab)) {
    switchModule(tab, { syncRoute: false });
  }
  await loadCompany();
  await loadRecommendations();
  await loadVerifyRequests();
  await loadCandidates();
});

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab !== 'string') return;
    if (!moduleTabs.some((item) => item.key === tab)) return;
    if (tab === activeModule.value) return;
    switchModule(tab, { syncRoute: false });
  }
);

watch(
  [candidateFilters, candidateKeyword, candidateSort],
  () => {
    candidatePage.value = 1;
    selectedCandidateIds.value = [];
  },
  { deep: true }
);

watch(candidateTotalPages, (total) => {
  if (candidatePage.value > total) {
    candidatePage.value = total;
  }
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

.hero-primary-btn {
  border: 1px solid rgba(15, 143, 89, 0.25);
  background: linear-gradient(135deg, #0f8f59 0%, #1fa66a 100%);
  color: #fff;
  border-radius: 14px;
  padding: 12px 18px;
  min-width: 132px;
  font-weight: 700;
  letter-spacing: 0.01em;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 12px 24px rgba(24, 160, 88, 0.28);
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.hero-primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 26px rgba(24, 160, 88, 0.3);
}

.hero-primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.hero-primary-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9ffe8;
}

.module-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
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

.profile-layout {
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
  align-items: start;
}

.profile-side {
  background: linear-gradient(180deg, #ffffff 0%, #f7fcf9 100%);
}

.profile-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-badge {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #12935c, #22b573);
  box-shadow: 0 10px 20px rgba(24, 160, 88, 0.2);
}

.status-chip {
  width: fit-content;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.status-chip.is-approved {
  color: #0f8f59;
  background: rgba(24, 160, 88, 0.12);
  border-color: rgba(24, 160, 88, 0.25);
}

.status-chip.is-pending {
  color: #8a6400;
  background: rgba(240, 160, 32, 0.15);
  border-color: rgba(240, 160, 32, 0.28);
}

.status-chip.is-rejected {
  color: #b93232;
  background: rgba(229, 62, 62, 0.12);
  border-color: rgba(229, 62, 62, 0.24);
}

.status-chip.is-disabled {
  color: #4e5969;
  background: rgba(107, 124, 120, 0.12);
  border-color: rgba(107, 124, 120, 0.24);
}

.completion-block {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 12px;
  background: #fff;
}

.completion-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.completion-track {
  height: 8px;
  border-radius: 999px;
  background: #e4efe9;
  overflow: hidden;
}

.completion-bar {
  height: 100%;
  background: linear-gradient(90deg, #18a058, #74d3a1);
}

.profile-main {
  gap: 16px;
}

.profile-section + .profile-section {
  border-top: 1px dashed var(--line);
  padding-top: 16px;
}

.section-head h3 {
  margin-bottom: 4px;
}

.section-head p {
  margin: 0;
  font-size: 13px;
}

.field-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field span {
  font-size: 12px;
  color: var(--muted);
}

.field-full {
  width: 100%;
}

.form-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.form-grid select {
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--line);
  padding: 0 12px;
}

.upload-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.upload-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px;
  background: #fbfdfc;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
}

.upload-card input[type="file"] {
  display: none;
}

.upload-title {
  font-weight: 600;
}

.upload-meta {
  color: var(--muted);
  font-size: 12px;
}

.upload-btn {
  width: fit-content;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
}

.welfare-editor {
  display: flex;
  gap: 8px;
  align-items: center;
}

.welfare-editor input {
  flex: 1;
}

.welfare-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.welfare-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(24, 160, 88, 0.2);
  background: rgba(24, 160, 88, 0.08);
  color: var(--accent-dark);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
}

.welfare-tag button {
  border: none;
  background: transparent;
  color: #67857a;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 16px 0;
}

.talent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed var(--line);
}

.talent-clickable {
  cursor: pointer;
  transition: background 0.15s ease;
  border-radius: 10px;
  padding: 10px;
}

.talent-clickable:hover {
  background: rgba(24, 160, 88, 0.06);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.candidate-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.candidate-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.candidate-toolbar .actions select {
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0 10px;
  min-width: 140px;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border: 1px dashed var(--line);
  border-radius: 12px;
  background: #fbfdfc;
}

.batch-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--muted);
}

.batch-toolbar select {
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0 10px;
  min-width: 170px;
}

.candidate-main {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.candidate-row-grid {
  display: grid;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.candidate-col {
  min-width: 0;
}

.candidate-col p {
  margin: 2px 0 0;
  word-break: break-word;
}

.row-check {
  margin-top: 2px;
  display: inline-flex;
}

.row-check input {
  width: 16px;
  height: 16px;
}

.candidate-status-col,
.candidate-action-col {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.analytics-shell {
  gap: 16px;
}

.analytics-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.analytics-refresh {
  min-width: 112px;
}

.analytics-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.analytics-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 10px;
}

.analytics-kpi {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  background: #fbfdfc;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.analytics-kpi strong {
  font-size: 22px;
  color: #0f8f59;
}

.analytics-block {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 14px;
  background: #fff;
}

.analytics-block h4 {
  margin: 0 0 10px;
}

.job-stat-list,
.source-list,
.funnel-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.job-stat-item,
.source-item,
.funnel-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.job-stat-head,
.source-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.analytics-track {
  height: 8px;
  border-radius: 999px;
  background: #e4efe9;
  overflow: hidden;
}

.analytics-fill {
  height: 100%;
  background: linear-gradient(90deg, #18a058, #79d8a6);
}

.analytics-fill.soft {
  background: linear-gradient(90deg, #3aa0ff, #78c3ff);
}

.analytics-fill.warm {
  background: linear-gradient(90deg, #ff8d52, #ffc56a);
}

.analytics-two-col {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.trend-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(70px, 1fr));
  align-items: end;
}

.trend-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.trend-bar-wrap {
  width: 100%;
  height: 92px;
  background: #edf5f0;
  border-radius: 8px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.trend-bar {
  width: 100%;
  background: linear-gradient(180deg, #7bd9a9 0%, #18a058 100%);
}

.analytics-time {
  text-align: right;
}

.empty-analytics {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 22px;
  text-align: center;
}

@media (max-width: 900px) {
  .module-tabs {
    width: 100%;
  }

  .profile-layout {
    grid-template-columns: 1fr;
  }

  .welfare-editor {
    flex-direction: column;
    align-items: stretch;
  }

  .candidate-toolbar {
    grid-template-columns: 1fr;
  }

  .batch-toolbar {
    align-items: stretch;
  }

  .candidate-row-grid {
    grid-template-columns: 1fr !important;
  }

  .analytics-time {
    text-align: left;
  }
}
</style>
