<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
        <div>
          <h1>企业审核</h1>
          <p>校方审核企业资质后才可发布岗位。</p>
        </div>
        <div class="hero-actions">
          <button class="chip" :class="{ active: filterStatus === '' }" @click="filterStatus = ''">全部 {{ reviewCounts.all }}</button>
          <button class="chip" :class="{ active: filterStatus === 'pending' }" @click="filterStatus = 'pending'">待审核 {{ reviewCounts.pending }}</button>
          <button class="chip" :class="{ active: filterStatus === 'approved' }" @click="filterStatus = 'approved'">已通过 {{ reviewCounts.approved }}</button>
          <button class="chip" :class="{ active: filterStatus === 'rejected' }" @click="filterStatus = 'rejected'">已驳回 {{ reviewCounts.rejected }}</button>
          <button class="btn btn-outline" @click="loadCompanies">刷新</button>
        </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="summary-grid">
          <article class="card summary-card">
            <span class="mono">企业总数</span>
            <strong>{{ reviewCounts.all }}</strong>
            <p>当前可审核企业池</p>
          </article>
          <article class="card summary-card">
            <span class="mono">待审核</span>
            <strong>{{ reviewCounts.pending }}</strong>
            <p>建议优先处理该批次</p>
          </article>
          <article class="card summary-card">
            <span class="mono">已通过</span>
            <strong>{{ reviewCounts.approved }}</strong>
            <p>可发布岗位企业</p>
          </article>
          <article class="card summary-card">
            <span class="mono">已驳回</span>
            <strong>{{ reviewCounts.rejected }}</strong>
            <p>待企业补充材料</p>
          </article>
        </div>

        <div class="list-toolbar card">
          <input v-model="keyword" placeholder="搜索企业名称 / 信用代码 / 联系人" />
          <div class="toolbar-actions">
            <select v-model="companySort">
              <option value="latest">按最新提交</option>
              <option value="name">按企业名称</option>
              <option value="status">按审核状态</option>
            </select>
            <span class="mono">共 {{ sortedCompanies.length }} 家 · 第 {{ page }} / {{ totalPages }} 页</span>
          </div>
        </div>
        <DataTable
          :columns="companyColumns"
          :rows="pagedCompanies"
          row-key="user_id"
          :loading="companiesLoading"
          :loading-rows="6"
          empty-text="暂无企业数据，请先通过后台创建企业信息。"
          v-model:page="page"
          :total-pages="totalPages"
          row-class="company-row"
        >
          <template #row="{ row: company, gridTemplate }">
            <div class="company-row-grid" :style="{ gridTemplateColumns: gridTemplate }">
              <div class="company-col">
                <h3>{{ company.company_name || '未命名企业' }}</h3>
                <p>{{ company.description || '暂无企业介绍' }}</p>
                <div class="mono">信用代码：{{ company.credit_code }}</div>
                <label class="reject-row">
                  <span class="mono">驳回原因（驳回时必填）</span>
                  <input
                    :value="rejectReasonMap[company.user_id] || ''"
                    @input="setRejectReason(company.user_id, $event.target.value)"
                    placeholder="如：营业执照信息不完整，请补充后重新提交"
                  />
                </label>
              </div>
              <div class="company-col">
                <div class="mono">联系人：{{ company.contact_name || '--' }}</div>
                <div class="mono">联系电话：{{ company.contact_phone || '--' }}</div>
                <div class="mono">企业官网：{{ company.website || '--' }}</div>
              </div>
              <div class="company-status">
                <StatusPill kind="company" :status="company.status" />
              </div>
              <div class="actions">
                <a
                  v-if="company.license_url"
                  class="btn btn-outline"
                  :href="company.license_url"
                  target="_blank"
                  rel="noreferrer"
                >
                  查看执照
                </a>
                <button
                  class="btn btn-outline"
                  :disabled="updatingCompanyId === company.user_id || company.status === 'approved'"
                  @click="setStatus(company, 'approved')"
                >
                  通过
                </button>
                <button
                  class="btn btn-outline"
                  :disabled="updatingCompanyId === company.user_id"
                  @click="setStatus(company, 'rejected')"
                >
                  驳回
                </button>
              </div>
            </div>
          </template>
        </DataTable>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { createAudit, fetchCompanies, updateCompanyStatus } from "../services/api";
import { useAuth } from "../store/auth";
import DataTable from "../components/DataTable.vue";
import StatusPill from "../components/StatusPill.vue";
import { companyStatusLabel } from "../constants/status";
import toast from '../utils/toast';

const companies = ref([]);
const filterStatus = ref('');
const keyword = ref('');
const companySort = ref('latest');
const auth = useAuth();
const updatingCompanyId = ref(null);
const rejectReasonMap = ref({});
const page = ref(1);
const PAGE_SIZE = 8;
const companiesLoading = ref(false);
const companyColumns = [
  { key: 'company', label: '企业信息', width: '2.2fr' },
  { key: 'contact', label: '联系人', width: '1.2fr' },
  { key: 'status', label: '状态', width: 'auto' },
  { key: 'actions', label: '操作', width: 'auto' }
];

const filteredCompanies = computed(() => {
  const status = filterStatus.value;
  const search = String(keyword.value || '').trim().toLowerCase();
  return companies.value.filter((company) => {
    if (status && company.status !== status) return false;
    if (!search) return true;
    const target = [
      company.company_name,
      company.credit_code,
      company.contact_name,
      company.contact_phone
    ]
      .map((item) => String(item || '').toLowerCase())
      .join(' ');
    return target.includes(search);
  });
});

const sortedCompanies = computed(() => {
  const rows = [...filteredCompanies.value];
  if (companySort.value === 'name') {
    return rows.sort((a, b) => String(a.company_name || '').localeCompare(String(b.company_name || ''), 'zh-CN'));
  }
  if (companySort.value === 'status') {
    const order = { pending: 0, rejected: 1, approved: 2, disabled: 3 };
    return rows.sort((a, b) => (order[a.status] ?? 9) - (order[b.status] ?? 9));
  }
  return rows.sort((a, b) => Number(b.user_id || 0) - Number(a.user_id || 0));
});

const totalPages = computed(() => Math.max(1, Math.ceil(sortedCompanies.value.length / PAGE_SIZE)));

const pagedCompanies = computed(() => {
  const current = Math.min(page.value, totalPages.value);
  const start = (current - 1) * PAGE_SIZE;
  return sortedCompanies.value.slice(start, start + PAGE_SIZE);
});

const reviewCounts = computed(() => {
  const all = companies.value.length;
  const pending = companies.value.filter((item) => item.status === 'pending').length;
  const approved = companies.value.filter((item) => item.status === 'approved').length;
  const rejected = companies.value.filter((item) => item.status === 'rejected').length;
  return { all, pending, approved, rejected };
});

async function loadCompanies() {
  companiesLoading.value = true;
  try {
    companies.value = await fetchCompanies();
    page.value = 1;
  } catch (err) {
    companies.value = [];
    toast.error('企业列表加载失败');
  } finally {
    companiesLoading.value = false;
  }
}

function setRejectReason(companyId, value) {
  rejectReasonMap.value = {
    ...rejectReasonMap.value,
    [companyId]: String(value || '')
  };
}

async function setStatus(company, status) {
  if (updatingCompanyId.value) return;
  if (company.status === status) {
    toast.info(`当前已是${statusLabel(status)}`);
    return;
  }
  let rejectReason = '';
  if (status === 'rejected') {
    rejectReason = String(rejectReasonMap.value[company.user_id] || '').trim();
    if (!rejectReason) {
      toast.warn('请填写驳回原因，便于企业修改后再次提交');
      return;
    }
  }
  updatingCompanyId.value = company.user_id;
  try {
    await updateCompanyStatus(company.user_id, { status });
    await createAudit({
      audit_type: "company",
      target_id: company.user_id,
      auditor_id: auth.user.value?.id || 0,
      result: status,
      remark: status === "approved" ? "审核通过" : `审核驳回：${rejectReason}`
    });
    await loadCompanies();
    if (status === 'rejected') {
      setRejectReason(company.user_id, '');
    }
    toast.success(`企业已${status === 'approved' ? '通过' : '驳回'}`);
  } catch (err) {
    toast.error(`操作失败：企业${status === 'approved' ? '通过' : '驳回'}未完成`);
  } finally {
    updatingCompanyId.value = null;
  }
}

onMounted(loadCompanies);

watch([filterStatus, keyword, companySort], () => {
  page.value = 1;
});

watch(totalPages, (total) => {
  if (page.value > total) page.value = total;
});

function statusLabel(status) {
  return companyStatusLabel(status);
}
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

.list-toolbar {
  margin-bottom: 14px;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.summary-card {
  padding: 14px 16px;
  gap: 6px;
  border: 1px solid #d5edde;
  box-shadow: 0 10px 24px rgba(15, 122, 70, 0.06);
}

.summary-card strong {
  font-size: 28px;
  color: var(--accent-dark);
  line-height: 1;
}

.summary-card p {
  margin: 0;
  font-size: 12px;
}

.toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-actions select {
  height: 42px;
  border-radius: 10px;
  border: 1px solid var(--line);
  padding: 0 10px;
  background: #fff;
}

.company-row-grid {
  display: grid;
  align-items: start;
  gap: 12px;
  min-width: 0;
}

.company-col {
  min-width: 0;
}

.company-col h3 {
  margin: 0 0 6px;
}

.company-col p {
  margin: 0 0 8px;
}

.company-status {
  display: flex;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.reject-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.hero-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}

.chip.active {
  border-color: rgba(24, 160, 88, 0.5);
  background: rgba(24, 160, 88, 0.1);
  color: var(--accent-dark);
}

@media (max-width: 880px) {
  .list-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-actions {
    justify-content: space-between;
  }

  .company-row-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
