<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>学生档案</h1>
            <p>统一维护个人资料、求职意向、简历与就业分析。</p>
          </div>
          <div class="hero-actions">
            <span class="tag mono" :class="profile.verified ? 'ok' : 'pending'">
              {{ profile.verified ? '学校已核验' : '待学校核验' }}
            </span>
            <button class="btn" @click="saveAll">保存资料</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="summary-grid">
          <div class="card summary-card">
            <strong>{{ profileCompletion }}%</strong>
            <span class="mono">档案完整度</span>
          </div>
          <div class="card summary-card">
            <strong>{{ resumes.length }}</strong>
            <span class="mono">简历数量</span>
          </div>
          <div class="card summary-card">
            <strong>{{ verifications.length }}</strong>
            <span class="mono">核验请求</span>
          </div>
          <div class="card summary-card">
            <strong>{{ intention.accept_internship ? '是' : '否' }}</strong>
            <span class="mono">接受实习</span>
          </div>
        </div>

        <div class="module-tabs">
          <button class="module-btn" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">基础信息</button>
          <button class="module-btn" :class="{ active: activeTab === 'intention' }" @click="activeTab = 'intention'">求职意向</button>
          <button class="module-btn" :class="{ active: activeTab === 'resume' }" @click="activeTab = 'resume'">简历中心</button>
          <button class="module-btn" :class="{ active: activeTab === 'insight' }" @click="switchInsightTab">分析与核验</button>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="activeTab === 'profile'" class="grid profile-stack">
          <div class="card section-card">
            <div class="section-head">
              <h3>个人信息</h3>
              <span class="mono section-tip">建议填写真实信息，便于企业联系</span>
            </div>
            <div class="field-grid profile-field-grid">
              <label class="field">
                <span class="field-label">姓名</span>
                <input v-model="profile.name" placeholder="请输入姓名" />
              </label>
              <label class="field">
                <span class="field-label">学号</span>
                <input v-model="profile.student_no" placeholder="请输入学号" />
              </label>
              <label class="field">
                <span class="field-label">学校</span>
                <input v-model="profile.school" placeholder="请输入学校" />
              </label>
              <label class="field">
                <span class="field-label">专业</span>
                <input v-model="profile.major" placeholder="请输入专业" />
              </label>
              <label class="field">
                <span class="field-label">年级</span>
                <input v-model="profile.grade" placeholder="如 2023 级" />
              </label>
              <label class="field">
                <span class="field-label">手机号</span>
                <input v-model="profile.phone" placeholder="请输入手机号" />
              </label>
              <label class="field field-full">
                <span class="field-label">邮箱</span>
                <input v-model="profile.email" placeholder="请输入邮箱" />
              </label>
            </div>
          </div>

          <div class="card section-card experience-card">
            <div class="section-head">
              <h3>个人经历</h3>
              <span class="mono section-tip">支持多行输入，信息展示更完整</span>
            </div>
            <div class="experience-grid profile-field-grid">
              <div class="list-editor field-full">
                <div class="list-head">
                  <div class="list-title-row">
                    <span class="field-label">技能能力</span>
                    <span class="mono list-count">{{ skillItems.length }} 项</span>
                  </div>
                  <div class="list-tools">
                    <span class="mono list-sub">支持逐条添加和批量粘贴</span>
                    <button type="button" class="list-clear" :disabled="skillItems.length === 0" @click="clearSkillItems">清空</button>
                  </div>
                </div>
                <div class="list-chip-wrap">
                  <span v-for="(item, idx) in skillItems" :key="`skill-${idx}-${item}`" class="list-chip">
                    {{ item }}
                    <button type="button" class="chip-x" @click="removeSkillItem(idx)">×</button>
                  </span>
                  <span v-if="skillItems.length === 0" class="mono list-empty">暂无技能标签，可从下方添加</span>
                </div>
                <div class="list-add-row">
                  <input
                    v-model="skillDraft"
                    placeholder="例如：Vue3 / Spring Boot / 数据分析"
                    @keydown.enter.prevent="addSkillItem"
                  />
                  <button type="button" class="btn btn-outline btn-mini" @click="addSkillItem">+ 添加</button>
                </div>
                <label class="field batch-area">
                  <span class="field-label">批量粘贴（每行一个）</span>
                  <textarea v-model="skillsInput" rows="4" placeholder="例如&#10;Vue3&#10;FastAPI&#10;MySQL"></textarea>
                </label>
              </div>

              <div class="list-editor field-full">
                <div class="list-head">
                  <div class="list-title-row">
                    <span class="field-label">获奖情况</span>
                    <span class="mono list-count">{{ awardItems.length }} 项</span>
                  </div>
                  <div class="list-tools">
                    <span class="mono list-sub">建议写完整奖项名称</span>
                    <button type="button" class="list-clear" :disabled="awardItems.length === 0" @click="clearAwardItems">清空</button>
                  </div>
                </div>
                <div class="list-chip-wrap">
                  <span v-for="(item, idx) in awardItems" :key="`award-${idx}-${item}`" class="list-chip">
                    {{ item }}
                    <button type="button" class="chip-x" @click="removeAwardItem(idx)">×</button>
                  </span>
                  <span v-if="awardItems.length === 0" class="mono list-empty">暂无获奖记录，可从下方添加</span>
                </div>
                <div class="list-add-row">
                  <input
                    v-model="awardDraft"
                    placeholder="例如：数学建模省一等奖"
                    @keydown.enter.prevent="addAwardItem"
                  />
                  <button type="button" class="btn btn-outline btn-mini" @click="addAwardItem">+ 添加</button>
                </div>
                <label class="field batch-area">
                  <span class="field-label">批量粘贴（每行一个）</span>
                  <textarea v-model="awardsInput" rows="4" placeholder="例如&#10;数学建模省一等奖&#10;校级优秀毕业生"></textarea>
                </label>
              </div>

              <div class="experience-group field-full">
                <div class="experience-group-head">
                  <h4>实习经历</h4>
                  <button type="button" class="btn btn-outline btn-mini" @click="addExperience('internship')">+ 新增实习</button>
                </div>
                <div class="experience-list">
                  <div class="experience-item" v-for="(item, idx) in internshipItems" :key="item.id">
                    <div class="experience-item-head">
                      <span class="mono">实习经历 #{{ idx + 1 }}</span>
                      <button type="button" class="btn btn-outline btn-mini" @click="removeExperience('internship', item.id)">删除</button>
                    </div>
                    <div class="experience-item-grid">
                      <label class="field">
                        <span class="field-label">岗位名称</span>
                        <input v-model="item.title" placeholder="如 后端开发实习生" />
                      </label>
                      <label class="field">
                        <span class="field-label">公司/组织</span>
                        <input v-model="item.organization" placeholder="如 XX 科技有限公司" />
                      </label>
                      <label class="field">
                        <span class="field-label">时间范围</span>
                        <input v-model="item.period" placeholder="如 2025.07 - 2025.10" />
                      </label>
                    </div>
                    <label class="field field-full">
                      <span class="field-label">经历描述</span>
                      <textarea v-model="item.description" rows="5" placeholder="描述负责内容、成果和量化结果"></textarea>
                    </label>
                  </div>
                </div>
              </div>

              <div class="experience-group field-full">
                <div class="experience-group-head">
                  <h4>项目经历</h4>
                  <button type="button" class="btn btn-outline btn-mini" @click="addExperience('project')">+ 新增项目</button>
                </div>
                <div class="experience-list">
                  <div class="experience-item" v-for="(item, idx) in projectItems" :key="item.id">
                    <div class="experience-item-head">
                      <span class="mono">项目经历 #{{ idx + 1 }}</span>
                      <button type="button" class="btn btn-outline btn-mini" @click="removeExperience('project', item.id)">删除</button>
                    </div>
                    <div class="experience-item-grid">
                      <label class="field">
                        <span class="field-label">项目名称</span>
                        <input v-model="item.title" placeholder="如 校园招聘平台" />
                      </label>
                      <label class="field">
                        <span class="field-label">项目角色</span>
                        <input v-model="item.organization" placeholder="如 全栈开发 / 后端负责人" />
                      </label>
                      <label class="field">
                        <span class="field-label">时间范围</span>
                        <input v-model="item.period" placeholder="如 2024.03 - 2024.08" />
                      </label>
                    </div>
                    <label class="field field-full">
                      <span class="field-label">项目描述</span>
                      <textarea v-model="item.description" rows="5" placeholder="描述技术栈、职责和项目成果"></textarea>
                    </label>
                  </div>
                </div>
              </div>

              <label class="field field-full bio-field">
                <span class="field-label">自我评价</span>
                <textarea v-model="profile.bio" rows="6" placeholder="突出你的核心优势、项目成果和求职方向"></textarea>
              </label>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'intention'" class="grid two-col">
          <div class="card section-card">
            <div class="section-head">
              <h3>求职意向</h3>
              <span class="mono section-tip">完善越完整，推荐越准确</span>
            </div>
            <div class="field-grid">
              <label class="field">
                <span class="field-label">期望岗位</span>
                <input v-model="intention.expected_job" placeholder="如 前端开发工程师" />
              </label>
              <label class="field">
                <span class="field-label">期望城市</span>
                <input v-model="intention.expected_city" placeholder="如 上海 / 深圳" />
              </label>
              <label class="field">
                <span class="field-label">期望薪资</span>
                <input v-model="intention.expected_salary" placeholder="如 15K-20K" />
              </label>
              <label class="field">
                <span class="field-label">期望行业</span>
                <input v-model="intention.expected_industry" placeholder="如 互联网 / AI" />
              </label>
              <label class="field">
                <span class="field-label">到岗时间</span>
                <input v-model="intention.arrival_time" placeholder="如 2 周内" />
              </label>
            </div>
            <div class="switch-row">
              <div>
                <strong>接受实习机会</strong>
                <p class="mono">开启后将同步匹配实习岗位</p>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="intention.accept_internship" />
                <span class="switch-slider"></span>
              </label>
            </div>
          </div>

          <div class="card intention-tip">
            <h3>建议</h3>
            <p>补齐期望岗位与城市，可提升岗位推荐准确度。</p>
            <p>保持薪资预期区间合理，有助于提升面试邀请率。</p>
            <p>更新到岗时间，便于企业做流程安排。</p>
          </div>
        </div>

        <div v-else-if="activeTab === 'resume'" class="grid one-col">
          <div class="card">
            <div class="section-head">
              <h3>简历列表</h3>
              <div class="actions">
                <button class="btn btn-outline" @click="addResume">新增在线简历</button>
                <label class="upload-label">
                  上传 PDF 简历
                  <input type="file" accept=".pdf,.doc,.docx" @change="uploadResumePdf" />
                </label>
              </div>
            </div>

            <div v-if="resumes.length === 0" class="empty-state card">暂无简历</div>
            <div v-else class="resume-list">
              <div class="resume-item" v-for="resume in resumes" :key="resume.id">
                <div class="resume-main">
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
              </div>
            </div>
          </div>

          <div class="card">
            <div class="section-head">
              <h3>简历智能解析</h3>
              <label class="upload-label">
                选择简历文件解析
                <input type="file" accept=".pdf,.docx,.doc,.txt" @change="handleParseResume" />
              </label>
            </div>
            <p class="mono">上传 PDF/DOCX，AI 自动提取并可一键应用到档案。</p>
            <div v-if="parseLoading" class="mono">解析中...</div>
            <div v-if="parseResult" class="resume-preview">
              <p><strong>姓名：</strong>{{ parseResult.name || '--' }}</p>
              <p><strong>学校：</strong>{{ parseResult.school || '--' }}</p>
              <p><strong>专业：</strong>{{ parseResult.major || '--' }}</p>
              <p><strong>手机：</strong>{{ parseResult.phone || '--' }}</p>
              <p v-if="parseResult.skills?.length"><strong>技能：</strong>{{ parseResult.skills.join(', ') }}</p>
              <button class="btn" @click="applyParseResult">应用到档案</button>
            </div>
          </div>
        </div>

        <div v-else class="grid two-col">
          <div class="card">
            <div class="section-head">
              <h3>就业分析</h3>
              <button class="btn btn-outline" @click="loadAnalytics" :disabled="analyticsLoading">
                {{ analyticsLoading ? '加载中...' : '查看分析' }}
              </button>
            </div>

            <div v-if="!analytics" class="empty-state card">点击“查看分析”加载数据</div>
            <div v-else>
              <h4>技能竞争力</h4>
              <div v-for="sk in analytics.skill_competitiveness" :key="sk.skill" class="skill-bar-row">
                <div class="skill-meta">
                  <span>{{ sk.skill }}</span><span class="mono">稀缺度 {{ sk.percentile }}%</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: sk.percentile + '%' }"></div>
                </div>
              </div>

              <h4>薪资基准</h4>
              <div v-if="analytics.salary_benchmark.sample_count" class="mono">
                范围 {{ analytics.salary_benchmark.min }}~{{ analytics.salary_benchmark.max }}
                | 均值 {{ analytics.salary_benchmark.avg_min }}~{{ analytics.salary_benchmark.avg_max }}
                ({{ analytics.salary_benchmark.sample_count }} 个样本)
              </div>
              <div v-else class="mono muted">暂无匹配薪资数据</div>

              <h4>投递统计</h4>
              <div v-if="analytics.application_stats" class="mono">
                投递 {{ analytics.application_stats.total_applied }}
                | 面试率 {{ analytics.application_stats.interview_rate }}%
                | Offer率 {{ analytics.application_stats.offer_rate }}%
              </div>
            </div>
          </div>

          <div class="card">
            <h3>核验请求</h3>
            <div v-if="!verifications.length" class="empty-state card">暂无核验请求</div>
            <div v-else class="verification-list">
              <div v-for="v in verifications" :key="v.id" class="verification-item">
                <div class="verification-head">
                  <span>企业ID: {{ v.company_id }}</span>
                  <span class="status-pill" :class="statusClass(v.status)">{{ statusText(v.status) }}</span>
                </div>
                <div class="mono">核验字段: {{ (v.fields || []).join(', ') || '--' }}</div>
                <div v-if="v.result">结果: {{ v.result }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
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
  bio: "",
  verified: false,
});

const intention = ref({
  student_id: userId,
  expected_job: "",
  expected_city: "",
  expected_salary: "",
  expected_industry: "",
  arrival_time: "",
  accept_internship: true,
});

const resumes = ref([]);
const skillsInput = ref('');
const awardsInput = ref('');
const skillDraft = ref('');
const awardDraft = ref('');
const internshipItems = ref([createExperienceItem('internship')]);
const projectItems = ref([createExperienceItem('project')]);
const previewResume = ref(null);
const parseLoading = ref(false);
const parseResult = ref(null);
const analytics = ref(null);
const analyticsLoading = ref(false);
const verifications = ref([]);
const activeTab = ref('profile');

function createExperienceItem(type) {
  return {
    id: `${type}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: '',
    organization: '',
    period: '',
    description: '',
  };
}

function parseExperienceItem(raw, type) {
  const text = String(raw || '').trim();
  if (!text) return createExperienceItem(type);
  const parts = text.split('||');
  if (parts.length === 1) {
    return { ...createExperienceItem(type), title: parts[0] };
  }
  return {
    ...createExperienceItem(type),
    title: parts[0] || '',
    organization: parts[1] || '',
    period: parts[2] || '',
    description: parts[3] || '',
  };
}

function serializeExperienceItem(item) {
  const title = String(item.title || '').trim();
  const organization = String(item.organization || '').trim();
  const period = String(item.period || '').trim();
  const description = String(item.description || '').trim();
  if (!title && !organization && !period && !description) return '';
  return [title, organization, period, description].join('||');
}

function ensureExperienceList(list, type) {
  return list.length ? list : [createExperienceItem(type)];
}

function addExperience(type) {
  if (type === 'internship') {
    internshipItems.value.push(createExperienceItem(type));
    return;
  }
  projectItems.value.push(createExperienceItem(type));
}

function removeExperience(type, id) {
  if (type === 'internship') {
    internshipItems.value = internshipItems.value.filter((item) => item.id !== id);
    internshipItems.value = ensureExperienceList(internshipItems.value, 'internship');
    return;
  }
  projectItems.value = projectItems.value.filter((item) => item.id !== id);
  projectItems.value = ensureExperienceList(projectItems.value, 'project');
}

function dedupeList(list) {
  const seen = new Set();
  return list.filter((item) => {
    const key = String(item || '').toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function parseListInput(value, options = { unique: true }) {
  const { unique = true } = options;
  const rawList = Array.isArray(value) ? value : String(value || '').split(/[\n,，]/);
  const list = rawList
    .map((item) => String(item || '').trim())
    .filter(Boolean);
  return unique ? dedupeList(list) : list;
}

function formatListInput(list) {
  return parseListInput(list).join('\n');
}

const skillItems = computed(() => parseListInput(skillsInput.value));
const awardItems = computed(() => parseListInput(awardsInput.value));

function addListItem(targetRef, draftRef) {
  const value = String(draftRef.value || '').trim();
  if (!value) return;
  const next = parseListInput(targetRef.value, { unique: false });
  const duplicated = next.some((item) => item.toLowerCase() === value.toLowerCase());
  if (duplicated) {
    toast.info('该条目已存在，无需重复添加');
    draftRef.value = '';
    return;
  }
  next.push(value);
  targetRef.value = formatListInput(next);
  draftRef.value = '';
}

function removeListItem(targetRef, index) {
  const next = parseListInput(targetRef.value);
  next.splice(index, 1);
  targetRef.value = formatListInput(next);
}

function addSkillItem() {
  addListItem(skillsInput, skillDraft);
}

function removeSkillItem(index) {
  removeListItem(skillsInput, index);
}

function addAwardItem() {
  addListItem(awardsInput, awardDraft);
}

function removeAwardItem(index) {
  removeListItem(awardsInput, index);
}

function clearSkillItems() {
  skillsInput.value = '';
  skillDraft.value = '';
}

function clearAwardItems() {
  awardsInput.value = '';
  awardDraft.value = '';
}

const profileCompletion = computed(() => {
  const fields = [
    profile.value.name,
    profile.value.student_no,
    profile.value.school,
    profile.value.major,
    profile.value.grade,
    profile.value.phone,
    profile.value.email,
    profile.value.bio,
    intention.value.expected_job,
    intention.value.expected_city,
    intention.value.expected_salary,
  ];
  const filled = fields.filter((v) => String(v || '').trim().length > 0).length;
  return Math.round((filled / fields.length) * 100);
});

async function loadData() {
  if (!userId) return;
  try {
    profile.value = await fetchStudentProfile(userId);
    skillsInput.value = formatListInput(profile.value.skills);
    awardsInput.value = formatListInput(profile.value.awards);
    internshipItems.value = ensureExperienceList(
      (profile.value.internships || []).map((row) => parseExperienceItem(row, 'internship')),
      'internship'
    );
    projectItems.value = ensureExperienceList(
      (profile.value.projects || []).map((row) => parseExperienceItem(row, 'project')),
      'project'
    );
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
  profile.value.skills = parseListInput(skillsInput.value);
  profile.value.awards = parseListInput(awardsInput.value);
  profile.value.internships = internshipItems.value.map(serializeExperienceItem).filter(Boolean);
  profile.value.projects = projectItems.value.map(serializeExperienceItem).filter(Boolean);
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
    const resumeSkills = parseListInput(skillsInput.value);
    const resumeProjects = projectItems.value
      .map((item) => String(item.title || item.description || '').trim())
      .filter(Boolean);
    await createResume(userId, {
      student_id: userId,
      resume_type: "online",
      content_json: { skills: resumeSkills, projects: resumeProjects },
      file_url: "",
      version_no: 1,
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
      version_no: 1,
    });
    toast.success('简历上传成功');
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
  } catch (e) {
    toast.error('解析失败');
  }
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
    skillsInput.value = formatListInput(r.skills);
  }
  toast.success('已应用到档案，请保存');
}

async function loadAnalytics() {
  analyticsLoading.value = true;
  try {
    analytics.value = await fetchStudentAnalytics(userId);
  } catch (e) {
    toast.error('加载分析失败');
  }
  analyticsLoading.value = false;
}

async function loadVerifications() {
  try {
    verifications.value = await fetchStudentVerifications(userId);
  } catch (e) {
    // ignore
  }
}

function switchInsightTab() {
  activeTab.value = 'insight';
  if (!analytics.value) loadAnalytics();
}

function statusClass(status) {
  if (status === 'approved') return 'ok';
  if (status === 'rejected') return 'bad';
  return 'pending';
}

function statusText(status) {
  if (status === 'approved') return '已通过';
  if (status === 'rejected') return '已驳回';
  return '待处理';
}

function formatTime(value) {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

onMounted(() => {
  loadData();
  loadVerifications();
});
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
  gap: 16px;
  flex-wrap: wrap;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag.ok {
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
}

.tag.pending {
  background: rgba(240, 160, 32, 0.15);
  color: #9a6710;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.summary-card {
  border: 1px solid #d8eee1;
  gap: 4px;
}

.summary-card strong {
  font-size: 28px;
  color: #0b7d45;
}

.module-tabs {
  margin-top: 14px;
  display: flex;
  gap: 8px;
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
  border-color: var(--accent);
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
  font-weight: 600;
}

.two-col {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.one-col {
  grid-template-columns: 1fr;
}

.profile-stack {
  grid-template-columns: 1fr;
}

.section-card {
  border: 1px solid #d8eee1;
}

.section-tip {
  color: #7d8d88;
}

.field-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.profile-field-grid {
  grid-template-columns: 1fr;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  color: #6a7f77;
  font-weight: 600;
}

.field-full {
  grid-column: 1 / -1;
}

.field textarea {
  min-height: 132px;
}

.experience-card {
  background: linear-gradient(180deg, #ffffff 0%, #f9fcfa 100%);
}

.experience-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.experience-field textarea {
  min-height: 170px;
}

.list-editor {
  border: 1px solid #dcefe4;
  border-radius: 14px;
  background: #ffffff;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.list-title-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.list-count {
  border: 1px solid #d8ebe1;
  background: #f3faf6;
  color: #396f55;
  border-radius: 999px;
  padding: 2px 8px;
}

.list-tools {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.list-sub {
  color: #7d8d88;
}

.list-clear {
  border: none;
  background: transparent;
  color: #3f8d64;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.list-clear:disabled {
  color: #a5b4ae;
  cursor: not-allowed;
}

.list-chip-wrap {
  min-height: 40px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-start;
}

.list-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ebf8f1;
  border: 1px solid #cfeadb;
  color: #1b6f4d;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 13px;
  line-height: 1.2;
}

.chip-x {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.chip-x:hover {
  color: #0f8f59;
}

.list-empty {
  color: #93a29c;
}

.list-add-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.list-add-row input {
  flex: 1;
}

.list-add-row .btn {
  flex-shrink: 0;
}

.batch-area textarea {
  min-height: 96px;
}

.experience-group {
  border: 1px solid #dcefe4;
  border-radius: 14px;
  background: #ffffff;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.experience-group-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.experience-group-head h4 {
  margin: 0;
}

.experience-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.experience-item {
  border: 1px solid #dbece3;
  border-radius: 12px;
  background: #f9fcfa;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.experience-item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.experience-item-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.btn-mini {
  padding: 6px 12px;
  font-size: 12px;
}

.bio-field textarea {
  min-height: 240px;
}

.switch-row {
  margin-top: 4px;
  border: 1px solid #dcefe4;
  background: #f6fbf8;
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.switch-row p {
  margin: 4px 0 0;
}

.switch {
  position: relative;
  width: 46px;
  height: 26px;
  display: inline-block;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: #c8d8d2;
  transition: 0.2s ease;
  cursor: pointer;
}

.switch-slider::before {
  content: "";
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(16, 30, 24, 0.2);
  transition: 0.2s ease;
}

.switch input:checked + .switch-slider {
  background: #18a058;
}

.switch input:checked + .switch-slider::before {
  transform: translateX(20px);
}

.intention-tip {
  border: 1px solid #d8eee1;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.resume-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-main p {
  margin: 6px 0 0;
}

.resume-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.resume-preview {
  border: 1px dashed var(--line);
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.skill-bar-row {
  margin-bottom: 10px;
}

.skill-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}

.bar-track {
  height: 7px;
  background: #e1ebe6;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: #18a058;
  border-radius: inherit;
}

.muted {
  color: #95a39e;
}

.verification-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.verification-item {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.verification-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
}

.status-pill.ok {
  background: #e9f8ef;
  color: #0f8f59;
}

.status-pill.bad {
  background: #f3f6f4;
  color: #5e7569;
}

.status-pill.pending {
  background: #f8f3e8;
  color: #99711c;
}

@media (max-width: 760px) {
  .list-tools {
    width: 100%;
    justify-content: space-between;
  }

  .list-add-row {
    flex-direction: column;
    align-items: stretch;
  }

  .list-add-row .btn {
    width: 100%;
  }
}
</style>
