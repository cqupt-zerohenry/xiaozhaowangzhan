<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>企业审核</h1>
          <p>校方审核企业资质后才可发布岗位。</p>
        </div>
        <button class="btn">新增审核任务</button>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="grid list-grid">
          <div class="card company-card" v-for="company in companies" :key="company.user_id">
            <div>
              <h3>{{ company.company_name }}</h3>
              <p>{{ company.description }}</p>
              <div class="mono">信用代码：{{ company.credit_code }}</div>
            </div>
            <div class="company-meta">
              <span class="tag mono">{{ statusLabel(company.status) }}</span>
              <div class="actions">
                <button class="btn btn-outline" @click="setStatus(company, 'approved')">通过</button>
                <button class="btn btn-outline" @click="setStatus(company, 'rejected')">驳回</button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="companies.length === 0" class="empty-state card">
          <h3>暂无企业数据</h3>
          <p>请先通过后台创建企业信息。</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { createAudit, fetchCompanies, updateCompanyStatus } from "../services/api";
import { useAuth } from "../store/auth";

const companies = ref([]);
const auth = useAuth();

async function loadCompanies() {
  try {
    companies.value = await fetchCompanies();
  } catch (err) {
    companies.value = [];
  }
}

async function setStatus(company, status) {
  try {
    await updateCompanyStatus(company.user_id, { status });
    await createAudit({
      audit_type: "company",
      target_id: company.user_id,
      auditor_id: auth.user.value?.id || 0,
      result: status,
      remark: status === "approved" ? "审核通过" : "审核驳回"
    });
    await loadCompanies();
  } catch (err) {
    // ignore
  }
}

onMounted(loadCompanies);

function statusLabel(status) {
  const mapping = {
    approved: "已通过",
    pending: "待审核",
    rejected: "已驳回",
    disabled: "已禁用"
  };
  return mapping[status] || status || "未知";
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

.list-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.company-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  justify-content: space-between;
}

.company-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-state {
  margin-top: 24px;
  text-align: center;
  gap: 12px;
}
</style>
