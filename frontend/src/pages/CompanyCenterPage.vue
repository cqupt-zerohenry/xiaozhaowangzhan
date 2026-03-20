<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>企业中心</h1>
          <p>完善公司信息并管理招聘内容。</p>
        </div>
        <button class="btn" @click="saveProfile">保存资料</button>
      </div>
    </section>

    <section>
      <div class="container grid layout">
        <div class="card">
          <h3>企业资料</h3>
          <div class="form-grid">
            <input v-model="company.company_name" placeholder="企业名称" />
            <input v-model="company.credit_code" placeholder="统一信用代码" />
            <input v-model="company.contact_name" placeholder="联系人" />
            <input v-model="company.contact_phone" placeholder="联系电话" />
            <input v-model="company.industry" placeholder="所属行业" />
            <input v-model="company.scale" placeholder="企业规模" />
            <input v-model="company.address" placeholder="企业地址" />
            <input v-model="company.website" placeholder="企业官网" />
          </div>
          <textarea v-model="company.description" rows="3" placeholder="企业简介"></textarea>
          <div class="upload-row">
            <div class="upload-item">
              <span class="label">营业执照：</span>
              <span v-if="company.license_url" class="mono">{{ company.license_url }}</span>
              <label class="upload-label">
                {{ company.license_url ? '重新上传' : '上传执照' }}
                <input type="file" accept=".pdf,.png,.jpg,.jpeg" @change="uploadLicense" />
              </label>
            </div>
            <div class="upload-item">
              <span class="label">企业宣传图：</span>
              <span v-if="company.promo_image_url" class="mono">{{ company.promo_image_url }}</span>
              <label class="upload-label">
                {{ company.promo_image_url ? '重新上传' : '上传宣传图' }}
                <input type="file" accept=".png,.jpg,.jpeg" @change="uploadPromoImage" />
              </label>
            </div>
          </div>
          <div class="tags-row">
            <span class="tag" v-for="tag in company.welfare_tags" :key="tag">{{ tag }}</span>
            <button class="chip" @click="addWelfare">添加福利</button>
          </div>
        </div>

        <div class="card">
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
            <span class="tag mono">{{ item.status }}</span>
          </div>
        </div>

        <div class="card">
          <h3>候选人筛选</h3>
          <div class="form-grid">
            <input v-model="candidateFilters.school" placeholder="学校筛选" />
            <input v-model="candidateFilters.major" placeholder="专业筛选" />
            <input v-model="candidateFilters.skill" placeholder="技能筛选（单个）" />
            <select v-model="candidateFilters.status">
              <option value="">投递状态</option>
              <option value="submitted">已投递</option>
              <option value="reviewing">筛选中</option>
              <option value="to_contact">待沟通</option>
              <option value="accepted">已通过</option>
              <option value="rejected">已淘汰</option>
              <option value="withdrawn">已撤回</option>
            </select>
          </div>
          <button class="btn btn-outline" @click="loadCandidates">筛选</button>

          <div v-if="candidates.length === 0" class="mono">暂无候选人记录</div>
          <div v-else class="talent" v-for="item in candidates" :key="item.application_id">
            <div>
              <strong>{{ item.student_name }} · {{ item.job_name }}</strong>
              <p class="mono">{{ item.school }} · {{ item.major }} · {{ item.grade }}</p>
              <p class="mono">技能：{{ (item.skills || []).join(', ') || '无' }}</p>
            </div>
            <span class="tag mono">{{ item.status }}</span>
          </div>
        </div>

        <!-- Company Analytics Card -->
        <div class="card">
          <h3>数据分析</h3>
          <button class="btn btn-outline" @click="loadAnalytics" :disabled="analyticsLoading">{{ analyticsLoading ? '加载中...' : '查看数据分析' }}</button>
          <div v-if="companyAnalytics">
            <h4 style="margin-top: 16px;">各岗位数据</h4>
            <div v-for="js in companyAnalytics.job_stats" :key="js.job_id" style="border: 1px solid var(--line); border-radius: 8px; padding: 10px; margin-bottom: 8px;">
              <strong>{{ js.job_name }}</strong>
              <div class="mono" style="font-size: 12px;">浏览 {{ js.views }} | 投递 {{ js.applications }} | 转化率 {{ js.conversion_rate }}%</div>
            </div>

            <h4 style="margin-top: 16px;">人才来源</h4>
            <div v-for="ts in companyAnalytics.talent_source" :key="ts.name" style="display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0;">
              <span>{{ ts.name }} <span class="tag" style="font-size: 11px;">{{ ts.type }}</span></span>
              <span class="mono">{{ ts.count }}人</span>
            </div>

            <h4 style="margin-top: 16px;">招聘漏斗</h4>
            <div v-for="f in companyAnalytics.funnel" :key="f.status" style="margin-bottom: 6px;">
              <div style="display: flex; justify-content: space-between; font-size: 13px;">
                <span>{{ f.status }}</span><span class="mono">{{ f.count }}</span>
              </div>
              <div style="height: 6px; background: #e1ebe6; border-radius: 3px; overflow: hidden;">
                <div :style="{ width: Math.min(100, f.count * 10) + '%', height: '100%', background: '#18a058', borderRadius: '3px' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import {
  createVerificationRequest,
  fetchCompany,
  fetchCompanyApplications,
  fetchCompanyRecommendations,
  fetchCompanyVerificationRequests,
  submitCompanyCertification,
  updateCompany,
  uploadFile,
  fetchCompanyAnalytics,
} from "../services/api";
import { useAuth } from "../store/auth";
import toast from '../utils/toast';

const auth = useAuth();
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

async function loadAnalytics() {
  analyticsLoading.value = true;
  try {
    companyAnalytics.value = await fetchCompanyAnalytics(auth.user.value?.id);
  } catch (e) { toast.error('加载分析失败'); }
  analyticsLoading.value = false;
}
const candidateFilters = ref({
  school: "",
  major: "",
  skill: "",
  status: ""
});
const candidates = ref([]);

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
  try {
    candidates.value = await fetchCompanyApplications(candidateFilters.value);
  } catch (err) {
    candidates.value = [];
    toast.warn('候选人加载失败');
  }
}

async function saveProfile() {
  if (!company.value.user_id) return;
  try {
    await updateCompany(company.value.user_id, company.value);
    await loadCompany();
    toast.success('资料已保存');
  } catch (err) {
    toast.error('保存失败，请重试');
  }
}

async function submitCertification() {
  if (!company.value.user_id) return;
  try {
    await submitCompanyCertification(company.value.user_id);
    await loadCompany();
    toast.success('认证申请已提交');
  } catch (err) {
    toast.error('提交失败，请重试');
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
  } catch (err) {
    // ignore
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
  const tag = prompt("请输入福利标签");
  if (tag) {
    company.value.welfare_tags.push(tag);
  }
}

function statusLabel(status) {
  const mapping = {
    approved: "已通过",
    pending: "待审核",
    rejected: "已驳回",
    disabled: "已禁用"
  };
  return mapping[status] || status || "未知";
}

onMounted(async () => {
  await loadCompany();
  await loadRecommendations();
  await loadVerifyRequests();
  await loadCandidates();
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
  grid-template-columns: minmax(280px, 1.1fr) minmax(240px, 0.9fr);
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

.tags-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
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

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.upload-item .label {
  color: var(--muted);
  font-size: 13px;
  min-width: 80px;
}

.upload-label {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: var(--accent);
  cursor: pointer;
}

.upload-label input[type="file"] {
  display: none;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
