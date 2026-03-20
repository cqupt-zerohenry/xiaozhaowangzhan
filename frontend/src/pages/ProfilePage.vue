<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-row">
        <div>
          <h1>学生档案</h1>
          <p>维护个人信息、求职意向与简历。</p>
        </div>
        <button class="btn" @click="saveAll">保存资料</button>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="card">
          <h3>学校核验状态</h3>
          <p class="mono">{{ profile.verified ? "已核验" : "未核验" }}</p>
        </div>
      </div>
    </section>

    <section>
      <div class="container grid profile-grid">
        <div class="card">
          <h3>个人信息</h3>
          <div class="form-grid">
            <input v-model="profile.name" placeholder="姓名" />
            <input v-model="profile.student_no" placeholder="学号" />
            <input v-model="profile.school" placeholder="学校" />
            <input v-model="profile.major" placeholder="专业" />
            <input v-model="profile.grade" placeholder="年级" />
            <input v-model="profile.phone" placeholder="手机号" />
            <input v-model="profile.email" placeholder="邮箱" />
          </div>
          <div class="form-grid">
            <input v-model="skillsInput" placeholder="技能标签（逗号分隔）" />
            <input v-model="awardsInput" placeholder="获奖情况（逗号分隔）" />
            <input v-model="internshipsInput" placeholder="实习经历（逗号分隔）" />
            <input v-model="projectsInput" placeholder="项目经历（逗号分隔）" />
          </div>
          <textarea v-model="profile.bio" rows="3" placeholder="自我评价"></textarea>
        </div>

        <div class="card">
          <h3>求职意向</h3>
          <div class="form-grid">
            <input v-model="intention.expected_job" placeholder="期望岗位" />
            <input v-model="intention.expected_city" placeholder="期望城市" />
            <input v-model="intention.expected_salary" placeholder="期望薪资" />
            <input v-model="intention.expected_industry" placeholder="期望行业" />
            <input v-model="intention.arrival_time" placeholder="到岗时间" />
          </div>
          <label class="checkbox">
            <input type="checkbox" v-model="intention.accept_internship" />
            接受实习
          </label>
        </div>

        <div class="card">
          <h3>简历列表</h3>
          <div v-if="resumes.length === 0" class="mono">暂无简历</div>
          <div v-else class="resume-list">
            <template v-for="resume in resumes" :key="resume.id">
              <div class="resume-item">
                <div>
                  <strong>版本 {{ resume.version_no }}</strong>
                  <p class="mono">{{ resume.resume_type }}{{ resume.file_url ? ' (附件)' : '' }}</p>
                </div>
                <div class="resume-actions">
                  <span class="mono">{{ formatTime(resume.create_time) }}</span>
                  <button class="btn btn-outline" @click="previewResume = previewResume === resume.id ? null : resume.id">
                    {{ previewResume === resume.id ? '收起' : '预览' }}
                  </button>
                  <a v-if="resume.file_url" :href="resume.file_url" target="_blank" class="btn btn-outline">下载</a>
                </div>
              </div>
              <div v-if="previewResume === resume.id && resume.content_json" class="resume-preview">
                <div v-if="resume.content_json.skills?.length" class="preview-section">
                  <strong>技能：</strong>
                  <div class="tags"><span class="tag" v-for="s in resume.content_json.skills" :key="s">{{ s }}</span></div>
                </div>
                <div v-if="resume.content_json.projects?.length" class="preview-section">
                  <strong>项目：</strong>
                  <div class="tags"><span class="tag" v-for="p in resume.content_json.projects" :key="p">{{ p }}</span></div>
                </div>
              </div>
            </template>
          </div>
          <button class="btn btn-outline" @click="addResume">新增在线简历</button>
          <label class="upload-label">
            上传 PDF 简历
            <input type="file" accept=".pdf,.doc,.docx" @change="uploadResumePdf" />
          </label>

          <!-- Resume Parsing -->
          <div style="margin-top: 16px; border-top: 1px dashed var(--line); padding-top: 16px;">
            <h4>简历智能解析</h4>
            <p class="mono" style="font-size: 12px; margin-bottom: 8px;">上传PDF/DOCX简历，AI自动提取信息填充到档案</p>
            <label class="upload-label">
              选择简历文件解析
              <input type="file" accept=".pdf,.docx,.doc,.txt" @change="handleParseResume" />
            </label>
            <div v-if="parseLoading" class="mono" style="margin-top: 8px;">解析中...</div>
            <div v-if="parseResult" class="resume-preview" style="margin-top: 12px;">
              <p><strong>姓名：</strong>{{ parseResult.name }}</p>
              <p><strong>学校：</strong>{{ parseResult.school }}</p>
              <p><strong>专业：</strong>{{ parseResult.major }}</p>
              <p><strong>手机：</strong>{{ parseResult.phone }}</p>
              <p v-if="parseResult.skills?.length"><strong>技能：</strong>{{ parseResult.skills.join(', ') }}</p>
              <button class="btn" style="margin-top: 8px;" @click="applyParseResult">应用到档案</button>
            </div>
          </div>
        </div>

        <!-- Student Analytics -->
        <div class="card">
          <h3>就业分析</h3>
          <button class="btn btn-outline" @click="loadAnalytics" :disabled="analyticsLoading">{{ analyticsLoading ? '加载中...' : '查看分析' }}</button>
          <div v-if="analytics">
            <h4 style="margin-top: 16px;">技能竞争力</h4>
            <div v-for="sk in analytics.skill_competitiveness" :key="sk.skill" style="margin-bottom: 8px;">
              <div style="display: flex; justify-content: space-between; font-size: 13px;">
                <span>{{ sk.skill }}</span><span class="mono">稀缺度 {{ sk.percentile }}%</span>
              </div>
              <div style="height: 6px; background: #e1ebe6; border-radius: 3px; overflow: hidden;">
                <div :style="{ width: sk.percentile + '%', height: '100%', background: '#18a058', borderRadius: '3px' }"></div>
              </div>
            </div>
            <h4 style="margin-top: 16px;">薪资基准</h4>
            <div v-if="analytics.salary_benchmark.sample_count" class="mono" style="font-size: 13px;">
              范围 {{ analytics.salary_benchmark.min }}~{{ analytics.salary_benchmark.max }}
              | 均值 {{ analytics.salary_benchmark.avg_min }}~{{ analytics.salary_benchmark.avg_max }}
              ({{ analytics.salary_benchmark.sample_count }}个样本)
            </div>
            <div v-else class="mono" style="font-size: 12px; color: #aaa;">暂无匹配薪资数据</div>
            <h4 style="margin-top: 16px;">投递统计</h4>
            <div v-if="analytics.application_stats" class="mono" style="font-size: 13px;">
              投递 {{ analytics.application_stats.total_applied }}
              | 面试率 {{ analytics.application_stats.interview_rate }}%
              | Offer率 {{ analytics.application_stats.offer_rate }}%
            </div>
          </div>
        </div>

        <!-- Verification Requests -->
        <div class="card">
          <h3>核验请求</h3>
          <div v-if="!verifications.length" class="mono">暂无核验请求</div>
          <div v-for="v in verifications" :key="v.id" style="border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between;">
              <span>企业ID: {{ v.company_id }}</span>
              <span class="tag" :style="{ background: v.status === 'approved' ? '#18a058' : v.status === 'rejected' ? '#e53e3e' : '#f0a020', color: '#fff' }">{{ v.status }}</span>
            </div>
            <div class="mono" style="font-size: 12px;">核验字段: {{ (v.fields || []).join(', ') }}</div>
            <div v-if="v.result" style="font-size: 13px; margin-top: 4px;">结果: {{ v.result }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import {
  createResume,
  fetchResumes,
  fetchStudentIntention,
  fetchStudentProfile,
  updateStudentIntention,
  updateStudentProfile,
  uploadFile,
  parseResume,
  fetchStudentAnalytics,
  fetchStudentVerifications,
} from "../services/api";
import { useAuth } from "../store/auth";
import toast from '../utils/toast';

const auth = useAuth();
const userId = auth.user.value?.id || 0;

const profile = ref({
  user_id: userId,
  name: auth.user.value?.name || "",
  student_no: "",
  school: "",
  major: "",
  grade: "",
  phone: "",
  email: auth.user.value?.email || "",
  skills: [],
  awards: [],
  internships: [],
  projects: [],
  bio: ""
});

const intention = ref({
  student_id: userId,
  expected_job: "",
  expected_city: "",
  expected_salary: "",
  expected_industry: "",
  arrival_time: "",
  accept_internship: true
});

const resumes = ref([]);
const skillsInput = ref('');
const awardsInput = ref('');
const internshipsInput = ref('');
const projectsInput = ref('');
const previewResume = ref(null);
const parseLoading = ref(false);
const parseResult = ref(null);
const analytics = ref(null);
const analyticsLoading = ref(false);
const verifications = ref([]);

async function loadData() {
  if (!userId) return;
  try {
    profile.value = await fetchStudentProfile(userId);
    skillsInput.value = (profile.value.skills || []).join(', ');
    awardsInput.value = (profile.value.awards || []).join(', ');
    internshipsInput.value = (profile.value.internships || []).join(', ');
    projectsInput.value = (profile.value.projects || []).join(', ');
  } catch (err) {
    // keep defaults
  }
  try {
    intention.value = await fetchStudentIntention(userId);
  } catch (err) {
    // keep defaults
  }
  try {
    resumes.value = await fetchResumes(userId);
  } catch (err) {
    resumes.value = [];
  }
}

async function saveAll() {
  if (!userId) return;
  profile.value.skills = skillsInput.value.split(',').map(s => s.trim()).filter(Boolean);
  profile.value.awards = awardsInput.value.split(',').map(s => s.trim()).filter(Boolean);
  profile.value.internships = internshipsInput.value.split(',').map(s => s.trim()).filter(Boolean);
  profile.value.projects = projectsInput.value.split(',').map(s => s.trim()).filter(Boolean);
  try {
    await updateStudentProfile(userId, profile.value);
    await updateStudentIntention(userId, intention.value);
    toast.success('资料已保存');
  } catch (err) {
    toast.error('保存失败，请重试');
  }
}

async function addResume() {
  if (!userId) return;
  try {
    await createResume(userId, {
      student_id: userId,
      resume_type: "online",
      content_json: { skills: profile.value.skills || [], projects: profile.value.projects || [] },
      file_url: "",
      version_no: 1
    });
    toast.success('简历已创建');
    await loadData();
  } catch (err) {
    toast.error('创建简历失败');
  }
}

async function uploadResumePdf(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  try {
    const result = await uploadFile(file);
    await createResume(userId, {
      student_id: userId,
      resume_type: 'file',
      content_json: null,
      file_url: result.file_url,
      version_no: 1
    });
    await loadData();
  } catch (e) {
    toast.error('上传失败');
  }
}

async function handleParseResume(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  parseLoading.value = true;
  parseResult.value = null;
  try {
    parseResult.value = await parseResume(file);
    toast.success('解析完成');
  } catch (e) { toast.error('解析失败'); }
  parseLoading.value = false;
}

function applyParseResult() {
  if (!parseResult.value) return;
  const r = parseResult.value;
  if (r.name) profile.value.name = r.name;
  if (r.school) profile.value.school = r.school;
  if (r.major) profile.value.major = r.major;
  if (r.phone) profile.value.phone = r.phone;
  if (r.email) profile.value.email = r.email;
  if (r.skills?.length) {
    profile.value.skills = r.skills;
    skillsInput.value = r.skills.join(', ');
  }
  toast.success('已应用到档案，请保存');
}

async function loadAnalytics() {
  analyticsLoading.value = true;
  try {
    analytics.value = await fetchStudentAnalytics(userId);
  } catch (e) { toast.error('加载分析失败'); }
  analyticsLoading.value = false;
}

async function loadVerifications() {
  try {
    verifications.value = await fetchStudentVerifications(userId);
  } catch (e) { /* */ }
}

function formatTime(value) {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

onMounted(() => { loadData(); loadVerifications(); });
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

.profile-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.form-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
}

.resume-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resume-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.upload-label {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: var(--muted);
  cursor: pointer;
}

.upload-label input[type="file"] {
  display: none;
}

.resume-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.resume-preview {
  border: 1px dashed var(--line);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
