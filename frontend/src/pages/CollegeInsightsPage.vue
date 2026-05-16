<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>学院详情查看</h1>
            <p>按学院或学校查看企业详情、相关岗位与学生投递进度。</p>
          </div>
          <button class="btn btn-outline" @click="openDetail('applications')">查看投递总览</button>
        </div>
      </div>
    </section>

    <section>
      <div class="container college-layout">
        <aside class="card college-sidebar">
          <h3>学院列表</h3>
          <p v-if="loading" class="mono">数据加载中...</p>
          <p v-else-if="!colleges.length" class="mono">暂无学院数据</p>
          <button
            v-for="item in colleges"
            :key="item.id"
            class="college-btn"
            :class="{ active: item.id === activeCollegeId }"
            @click="activeCollegeId = item.id"
          >
            {{ item.name }}
          </button>
        </aside>

        <div class="college-main">
          <div class="kpi-grid">
            <article class="card kpi-card clickable" @click="jumpToSection('companies')">
              <span class="mono">企业详情</span>
              <strong>{{ filteredCompanies.length }}</strong>
              <p class="mono">企业资质、规模、负责人和联系方式</p>
            </article>
            <article class="card kpi-card clickable" @click="jumpToSection('jobs')">
              <span class="mono">专业匹配岗位库</span>
              <strong>{{ filteredJobs.length }}</strong>
              <p class="mono">可查看岗位详情、批量投递与投递学生</p>
            </article>
            <article class="card kpi-card clickable" @click="jumpToSection('applications')">
              <span class="mono">学生投递情况</span>
              <strong>{{ filteredApplications.length }}</strong>
              <p class="mono">按年级筛选并查看投递流程进度</p>
            </article>
          </div>

          <div class="card section-switch">
            <button class="module-btn" :class="{ active: section === 'companies' }" @click="section = 'companies'">企业详情</button>
            <button class="module-btn" :class="{ active: section === 'jobs' }" @click="section = 'jobs'">专业匹配岗位库</button>
            <button class="module-btn" :class="{ active: section === 'applications' }" @click="section = 'applications'">学生投递情况</button>
          </div>

          <div v-if="section === 'companies'" class="card">
            <div class="section-head">
              <h3>企业详情</h3>
              <button class="btn btn-outline btn-sm" @click="openDetail('companies')">查看详情</button>
            </div>
            <div class="filter-grid">
              <input v-model="companyKeyword" placeholder="搜索企业名称/负责人" />
              <select v-model="companyScaleFilter">
                <option value="">全部规模</option>
                <option v-for="scale in uniqueCompanyScales" :key="scale" :value="scale">{{ scale }}</option>
              </select>
              <button class="btn btn-outline btn-sm" @click="resetCompanyFilter">清空条件</button>
            </div>
            <div class="company-list">
              <article class="company-item" v-for="company in pagedCompanies" :key="company.id">
                <div class="company-main">
                  <strong>{{ company.name }}</strong>
                  <p class="mono">资质：{{ company.license }}</p>
                  <p class="mono">规模：{{ company.scale }}</p>
                </div>
                <div class="company-side">
                  <p class="mono">负责人：{{ company.contact }}</p>
                  <p class="mono">联系方式：{{ company.phone }}</p>
                </div>
                <div class="company-jobs">
                  <span class="mono">相关岗位：</span>
                  <span class="tag mono" v-for="jobName in company.jobs" :key="`${company.id}-${jobName}`">{{ jobName }}</span>
                </div>
              </article>
              <div v-if="!pagedCompanies.length" class="mono">暂无符合条件的数据</div>
            </div>
            <div class="pager">
              <button class="btn btn-outline btn-sm" :disabled="companyPage <= 1" @click="companyPage -= 1">上一页</button>
              <span class="mono">第 {{ companyPage }} / {{ companyTotalPages }} 页</span>
              <button class="btn btn-outline btn-sm" :disabled="companyPage >= companyTotalPages" @click="companyPage += 1">下一页</button>
            </div>
          </div>

          <div v-else-if="section === 'jobs'" class="card">
            <div class="section-head">
              <h3>学院专业匹配岗位库</h3>
              <div class="actions">
                <button class="btn btn-outline btn-sm" @click="openDetail('jobs')">查看详情</button>
                <label class="upload-label">
                  批量导入简历
                  <input type="file" accept=".pdf,.doc,.docx,.zip" @change="handleBatchResumeUpload" />
                </label>
                <button class="btn btn-outline btn-sm" @click="triggerBatchApply">批量投递</button>
              </div>
            </div>
            <div class="filter-grid">
              <input v-model="jobKeyword" placeholder="搜索岗位/企业名称" />
              <select v-model="jobCityFilter">
                <option value="">全部城市</option>
                <option v-for="city in uniqueJobCities" :key="city" :value="city">{{ city }}</option>
              </select>
              <button class="btn btn-outline btn-sm" @click="resetJobFilter">清空条件</button>
            </div>
            <p v-if="uploadedBatchFileName" class="mono">已导入文件：{{ uploadedBatchFileName }}</p>
            <div class="job-list">
              <article class="job-item" v-for="job in pagedJobs" :key="job.id">
                <div>
                  <strong>{{ job.name }}</strong>
                  <p class="mono">{{ job.company }} · {{ job.city }} · {{ job.salary }}</p>
                  <p class="mono">专业方向：{{ job.major }}</p>
                </div>
                <div class="actions">
                  <button class="btn btn-outline btn-sm" @click="openJob(job.id)">查看岗位详情</button>
                  <button class="btn btn-outline btn-sm" @click="openJobApplicants(job)">查看投递学生</button>
                  <span class="tag mono">{{ job.applicationCount }} 人投递</span>
                </div>
              </article>
              <div v-if="!pagedJobs.length" class="mono">暂无符合条件的数据</div>
            </div>
            <div class="pager">
              <button class="btn btn-outline btn-sm" :disabled="jobPage <= 1" @click="jobPage -= 1">上一页</button>
              <span class="mono">第 {{ jobPage }} / {{ jobTotalPages }} 页</span>
              <button class="btn btn-outline btn-sm" :disabled="jobPage >= jobTotalPages" @click="jobPage += 1">下一页</button>
            </div>
          </div>

          <div v-else class="card">
            <div class="section-head">
              <h3>学生投递情况</h3>
              <button class="btn btn-outline btn-sm" @click="openDetail('applications')">查看详情</button>
            </div>
            <div class="filter-grid">
              <select v-model="gradeFilter">
                <option value="">全部年级</option>
                <option v-for="grade in activeCollege.grades" :key="grade" :value="grade">{{ grade }}</option>
              </select>
              <select v-model="statusFilter">
                <option value="">全部状态</option>
                <option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
              </select>
              <button class="btn btn-outline btn-sm" @click="resetApplicationFilter">清空条件</button>
            </div>
            <div class="status-overview">
              <article class="status-box" v-for="item in applicationStatusSummary" :key="item.key">
                <span class="mono">{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
              </article>
            </div>
            <div class="app-list">
              <article class="app-item" v-for="row in pagedApplications" :key="row.id">
                <div class="app-head">
                  <div>
                    <strong>{{ row.studentName }} · {{ row.grade }}</strong>
                    <p class="mono">{{ row.jobName }} · {{ row.companyName }}</p>
                  </div>
                  <span class="status-pill" :class="statusClass(row.status)">{{ statusLabel(row.status) }}</span>
                </div>
                <div class="timeline">
                  <div class="step-bar">
                    <template v-for="(step, idx) in appSteps" :key="`${row.id}-${step.key}`">
                      <div class="step-node" :class="stepNodeClass(row.status, step.key)"></div>
                      <div v-if="idx < appSteps.length - 1" class="step-line" :class="{ done: stepDone(row.status, step.key) }"></div>
                    </template>
                  </div>
                  <div class="step-labels">
                    <span class="step-label" v-for="step in appSteps" :key="`${row.id}-label-${step.key}`">
                      {{ step.label }}
                    </span>
                  </div>
                </div>
              </article>
              <div v-if="!pagedApplications.length" class="mono">暂无符合条件的数据</div>
            </div>
            <div class="pager">
              <button class="btn btn-outline btn-sm" :disabled="applicationPage <= 1" @click="applicationPage -= 1">上一页</button>
              <span class="mono">第 {{ applicationPage }} / {{ applicationTotalPages }} 页</span>
              <button class="btn btn-outline btn-sm" :disabled="applicationPage >= applicationTotalPages" @click="applicationPage += 1">下一页</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="detailDialog.visible" class="dialog-mask" @click.self="closeDetail">
      <div class="card dialog">
        <div class="section-head">
          <h3>{{ detailDialog.title }}</h3>
          <button class="btn btn-outline btn-sm" @click="closeDetail">关闭</button>
        </div>
        <div class="dialog-list">
          <template v-if="detailDialog.type === 'companies'">
            <div v-for="item in detailPagedRows" :key="`d-company-${item.id}`" class="dialog-item">
              <strong>{{ item.name }}</strong>
              <p class="mono">资质：{{ item.license }} · 规模：{{ item.scale }}</p>
              <p class="mono">负责人：{{ item.contact }} · 联系方式：{{ item.phone }}</p>
            </div>
          </template>
          <template v-else-if="detailDialog.type === 'jobs'">
            <div v-for="item in detailPagedRows" :key="`d-job-${item.id}`" class="dialog-item">
              <strong>{{ item.name }}</strong>
              <p class="mono">{{ item.company }} · {{ item.city }} · {{ item.salary }}</p>
              <p class="mono">投递人数：{{ item.applicationCount }}</p>
            </div>
          </template>
          <template v-else>
            <div v-for="item in detailPagedRows" :key="`d-app-${item.id}`" class="dialog-item">
              <strong>{{ item.studentName }} · {{ item.grade }}</strong>
              <p class="mono">{{ item.jobName }} · {{ item.companyName }}</p>
              <p class="mono">当前状态：{{ statusLabel(item.status) }}</p>
            </div>
          </template>
          <div v-if="!detailPagedRows.length" class="mono">暂无详情数据</div>
        </div>
        <div class="pager">
          <button class="btn btn-outline btn-sm" :disabled="detailPage <= 1" @click="detailPage -= 1">上一页</button>
          <span class="mono">第 {{ detailPage }} / {{ detailTotalPages }} 页</span>
          <button class="btn btn-outline btn-sm" :disabled="detailPage >= detailTotalPages" @click="detailPage += 1">下一页</button>
        </div>
      </div>
    </div>

    <div v-if="applicantsDialog.visible" class="dialog-mask" @click.self="closeApplicantsDialog">
      <div class="card dialog">
        <div class="section-head">
          <h3>{{ applicantsDialog.jobName }} · 投递学生</h3>
          <button class="btn btn-outline btn-sm" @click="closeApplicantsDialog">关闭</button>
        </div>
        <div class="dialog-list">
          <div v-for="(row, idx) in pagedApplicants" :key="`applicant-${idx}-${row.name}`" class="dialog-item">
            <strong>{{ row.name }} · {{ row.grade }}</strong>
            <p class="mono">当前状态：{{ statusLabel(row.status) }}</p>
          </div>
          <div v-if="!pagedApplicants.length" class="mono">暂无投递学生数据</div>
        </div>
        <div class="pager">
          <button class="btn btn-outline btn-sm" :disabled="applicantsPage <= 1" @click="applicantsPage -= 1">上一页</button>
          <span class="mono">第 {{ applicantsPage }} / {{ applicantsTotalPages }} 页</span>
          <button class="btn btn-outline btn-sm" :disabled="applicantsPage >= applicantsTotalPages" @click="applicantsPage += 1">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { fetchCollegeInsights } from "../services/api";
import toast from "../utils/toast";

const router = useRouter();
const section = ref("companies");
const companyKeyword = ref("");
const companyScaleFilter = ref("");
const jobKeyword = ref("");
const jobCityFilter = ref("");
const gradeFilter = ref("");
const statusFilter = ref("");
const uploadedBatchFileName = ref("");
const loading = ref(false);

const companyPage = ref(1);
const jobPage = ref(1);
const applicationPage = ref(1);

const detailDialog = ref({ visible: false, type: "", title: "" });
const detailPage = ref(1);

const applicantsDialog = ref({ visible: false, jobName: "", rows: [] });
const applicantsPage = ref(1);

const statusOptions = [
  { value: "submitted", label: "已投递" },
  { value: "viewed", label: "已查看" },
  { value: "reviewing", label: "筛选中" },
  { value: "to_contact", label: "待沟通" },
  { value: "interviewing", label: "面试中" },
  { value: "accepted", label: "已通过" },
  { value: "rejected", label: "已淘汰" }
];

const appSteps = [
  { key: "submitted", label: "已投递" },
  { key: "viewed", label: "已查看" },
  { key: "reviewing", label: "筛选中" },
  { key: "to_contact", label: "待沟通" },
  { key: "interviewing", label: "面试中" },
  { key: "accepted", label: "已通过" }
];

const colleges = ref([]);

const fallbackCollege = {
  id: "",
  name: "",
  grades: [],
  companies: [],
  jobs: [],
  applications: []
};

const activeCollegeId = ref("");

const activeCollege = computed(() => (
  colleges.value.find((item) => item.id === activeCollegeId.value) || colleges.value[0] || fallbackCollege
));

const uniqueCompanyScales = computed(() => (
  [...new Set((activeCollege.value?.companies || []).map((item) => item.scale).filter(Boolean))]
));

const uniqueJobCities = computed(() => (
  [...new Set((activeCollege.value?.jobs || []).map((item) => item.city).filter(Boolean))]
));

const filteredCompanies = computed(() => {
  const keyword = String(companyKeyword.value || "").trim().toLowerCase();
  const scale = String(companyScaleFilter.value || "");
  return (activeCollege.value?.companies || []).filter((item) => {
    const target = `${item.name} ${item.contact}`.toLowerCase();
    if (keyword && !target.includes(keyword)) return false;
    if (scale && item.scale !== scale) return false;
    return true;
  });
});

const filteredJobs = computed(() => {
  const keyword = String(jobKeyword.value || "").trim().toLowerCase();
  const city = String(jobCityFilter.value || "");
  return (activeCollege.value?.jobs || []).filter((item) => {
    const target = `${item.name} ${item.company}`.toLowerCase();
    if (keyword && !target.includes(keyword)) return false;
    if (city && item.city !== city) return false;
    return true;
  });
});

const filteredApplications = computed(() => {
  const grade = String(gradeFilter.value || "");
  const status = String(statusFilter.value || "");
  return (activeCollege.value?.applications || []).filter((item) => {
    if (grade && item.grade !== grade) return false;
    if (status && item.status !== status) return false;
    return true;
  });
});

const applicationStatusSummary = computed(() => {
  const list = filteredApplications.value;
  const keys = ["submitted", "viewed", "reviewing", "to_contact", "interviewing", "accepted", "rejected"];
  return keys.map((key) => ({
    key,
    label: statusLabel(key),
    count: list.filter((item) => item.status === key).length
  }));
});

const COMPANY_PAGE_SIZE = 3;
const JOB_PAGE_SIZE = 4;
const APPLICATION_PAGE_SIZE = 4;
const DETAIL_PAGE_SIZE = 5;
const APPLICANT_PAGE_SIZE = 5;

const companyTotalPages = computed(() => Math.max(1, Math.ceil(filteredCompanies.value.length / COMPANY_PAGE_SIZE)));
const jobTotalPages = computed(() => Math.max(1, Math.ceil(filteredJobs.value.length / JOB_PAGE_SIZE)));
const applicationTotalPages = computed(() => Math.max(1, Math.ceil(filteredApplications.value.length / APPLICATION_PAGE_SIZE)));

const pagedCompanies = computed(() => {
  const page = Math.min(companyPage.value, companyTotalPages.value);
  const start = (page - 1) * COMPANY_PAGE_SIZE;
  return filteredCompanies.value.slice(start, start + COMPANY_PAGE_SIZE);
});

const pagedJobs = computed(() => {
  const page = Math.min(jobPage.value, jobTotalPages.value);
  const start = (page - 1) * JOB_PAGE_SIZE;
  return filteredJobs.value.slice(start, start + JOB_PAGE_SIZE);
});

const pagedApplications = computed(() => {
  const page = Math.min(applicationPage.value, applicationTotalPages.value);
  const start = (page - 1) * APPLICATION_PAGE_SIZE;
  return filteredApplications.value.slice(start, start + APPLICATION_PAGE_SIZE);
});

const detailRows = computed(() => {
  if (detailDialog.value.type === "companies") return filteredCompanies.value;
  if (detailDialog.value.type === "jobs") return filteredJobs.value;
  return filteredApplications.value;
});

const detailTotalPages = computed(() => Math.max(1, Math.ceil(detailRows.value.length / DETAIL_PAGE_SIZE)));
const detailPagedRows = computed(() => {
  const page = Math.min(detailPage.value, detailTotalPages.value);
  const start = (page - 1) * DETAIL_PAGE_SIZE;
  return detailRows.value.slice(start, start + DETAIL_PAGE_SIZE);
});

const applicantsTotalPages = computed(() => Math.max(1, Math.ceil(applicantsDialog.value.rows.length / APPLICANT_PAGE_SIZE)));
const pagedApplicants = computed(() => {
  const page = Math.min(applicantsPage.value, applicantsTotalPages.value);
  const start = (page - 1) * APPLICANT_PAGE_SIZE;
  return applicantsDialog.value.rows.slice(start, start + APPLICANT_PAGE_SIZE);
});

watch(companyTotalPages, (value) => {
  if (companyPage.value > value) companyPage.value = value;
});
watch(jobTotalPages, (value) => {
  if (jobPage.value > value) jobPage.value = value;
});
watch(applicationTotalPages, (value) => {
  if (applicationPage.value > value) applicationPage.value = value;
});
watch(detailTotalPages, (value) => {
  if (detailPage.value > value) detailPage.value = value;
});
watch(applicantsTotalPages, (value) => {
  if (applicantsPage.value > value) applicantsPage.value = value;
});

watch([companyKeyword, companyScaleFilter], () => {
  companyPage.value = 1;
});
watch([jobKeyword, jobCityFilter], () => {
  jobPage.value = 1;
});
watch([gradeFilter, statusFilter], () => {
  applicationPage.value = 1;
});

watch(activeCollegeId, () => {
  section.value = "companies";
  companyKeyword.value = "";
  companyScaleFilter.value = "";
  jobKeyword.value = "";
  jobCityFilter.value = "";
  gradeFilter.value = "";
  statusFilter.value = "";
  uploadedBatchFileName.value = "";
  companyPage.value = 1;
  jobPage.value = 1;
  applicationPage.value = 1;
});

function statusLabel(status) {
  const map = {
    submitted: "已投递",
    viewed: "已查看",
    reviewing: "筛选中",
    to_contact: "待沟通",
    interviewing: "面试中",
    accepted: "已通过",
    rejected: "已淘汰"
  };
  return map[status] || status;
}

function statusClass(status) {
  if (status === "accepted") return "ok";
  if (status === "rejected") return "bad";
  if (status === "interviewing") return "info";
  return "pending";
}

function normalizeProgressStatus(status) {
  if (status === "rejected") return "reviewing";
  return status;
}

function stepDone(status, stepKey) {
  const safeStatus = normalizeProgressStatus(status);
  const currentIndex = appSteps.findIndex((item) => item.key === safeStatus);
  const targetIndex = appSteps.findIndex((item) => item.key === stepKey);
  return targetIndex < currentIndex;
}

function stepNodeClass(status, stepKey) {
  const safeStatus = normalizeProgressStatus(status);
  const currentIndex = appSteps.findIndex((item) => item.key === safeStatus);
  const targetIndex = appSteps.findIndex((item) => item.key === stepKey);
  if (targetIndex < currentIndex) return "done";
  if (targetIndex === currentIndex) return "current";
  return "";
}

function jumpToSection(type) {
  section.value = type;
}

function openDetail(type) {
  const titleMap = {
    companies: "企业详情（分页）",
    jobs: "专业匹配岗位库（分页）",
    applications: "学生投递详情（分页）"
  };
  detailPage.value = 1;
  detailDialog.value = { visible: true, type, title: titleMap[type] || "详情" };
}

function closeDetail() {
  detailDialog.value = { visible: false, type: "", title: "" };
}

function openJob(jobId) {
  router.push(`/jobs/${jobId}`);
}

function openJobApplicants(job) {
  applicantsPage.value = 1;
  applicantsDialog.value = {
    visible: true,
    jobName: job.name,
    rows: Array.isArray(job.applicants) ? job.applicants : []
  };
}

function closeApplicantsDialog() {
  applicantsDialog.value = { visible: false, jobName: "", rows: [] };
}

function resetCompanyFilter() {
  companyKeyword.value = "";
  companyScaleFilter.value = "";
}

function resetJobFilter() {
  jobKeyword.value = "";
  jobCityFilter.value = "";
}

function resetApplicationFilter() {
  gradeFilter.value = "";
  statusFilter.value = "";
}

function handleBatchResumeUpload(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  uploadedBatchFileName.value = file.name;
  toast.success(`已导入简历文件：${file.name}`);
}

function triggerBatchApply() {
  if (!uploadedBatchFileName.value) {
    toast.warn("请先导入批量简历文件");
    return;
  }
  toast.success(`已触发批量投递：${uploadedBatchFileName.value}`);
}

async function loadCollegeData() {
  loading.value = true;
  try {
    const result = await fetchCollegeInsights();
    colleges.value = Array.isArray(result) ? result : [];
    if (!colleges.value.find((item) => item.id === activeCollegeId.value)) {
      activeCollegeId.value = colleges.value[0]?.id || "";
    }
  } catch (err) {
    colleges.value = [];
    toast.error("学院数据加载失败");
  } finally {
    loading.value = false;
  }
}

onMounted(loadCollegeData);
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
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.college-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 18px;
}

.college-sidebar {
  position: sticky;
  top: 118px;
  height: fit-content;
}

.college-btn {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #f9fcfa;
  padding: 12px 14px;
  text-align: left;
  margin-top: 8px;
  cursor: pointer;
  font-weight: 600;
  color: #2f4940;
  transition: border-color 0.2s ease, transform 0.2s ease, background 0.2s ease;
}

.college-btn:hover {
  transform: translateY(-1px);
  border-color: #b9dfcb;
  background: #f2fbf6;
}

.college-btn.active {
  border-color: rgba(24, 160, 88, 0.5);
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
}

.college-main {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  border: 1px solid #d8eee1;
  min-height: 132px;
  justify-content: center;
}

.kpi-card strong {
  font-size: 26px;
  color: var(--accent-dark);
}

.kpi-card.clickable {
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.kpi-card.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(15, 122, 70, 0.14);
}

.section-switch {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.module-btn {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 9px 16px;
  background: #fff;
  cursor: pointer;
  font-weight: 600;
  color: #466257;
}

.module-btn.active {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.filter-grid input,
.filter-grid select {
  width: 100%;
  min-height: 42px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #f9fcfa;
  color: #27453a;
}

.filter-grid select {
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, #6f8f82 50%),
    linear-gradient(135deg, #6f8f82 50%, transparent 50%);
  background-position:
    calc(100% - 18px) calc(50% - 3px),
    calc(100% - 12px) calc(50% - 3px);
  background-size: 6px 6px, 6px 6px;
  background-repeat: no-repeat;
}

.company-list,
.job-list,
.app-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.company-item,
.job-item,
.app-item {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fdfefe;
}

.company-main,
.company-side {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: center;
}

.company-jobs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.job-item {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.status-box {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
  background: #f6fbf8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-box strong {
  color: var(--accent-dark);
  font-size: 18px;
}

.app-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.status-pill {
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  border: 1px solid var(--line);
}

.status-pill.pending {
  background: #fff7e8;
  border-color: #f0d8a5;
  color: #9a6400;
}

.status-pill.info {
  background: #eff8ff;
  border-color: #bcdfff;
  color: #18598a;
}

.status-pill.ok {
  background: #ebf8f1;
  border-color: #bde5cc;
  color: #0e7a48;
}

.status-pill.bad {
  background: #fff0f0;
  border-color: #f0c2c2;
  color: #a03838;
}

.timeline {
  border-top: 1px dashed var(--line);
  padding-top: 12px;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.38);
  z-index: 90;
  display: grid;
  place-items: center;
  padding: 16px;
}

.dialog {
  width: min(720px, 100%);
  max-height: 82vh;
  overflow: auto;
}

.dialog-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dialog-item {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 12px;
}

.upload-label {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: #456256;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 7px 12px;
  cursor: pointer;
  background: #fff;
}

.upload-label input {
  display: none;
}

.actions {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.btn-sm {
  padding: 7px 12px;
  font-size: 12px;
}

@media (max-width: 980px) {
  .college-layout {
    grid-template-columns: 1fr;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .status-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .job-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
