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
  uploadFile
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
    const nextVersion = resumes.value.length + 1;
    await createResume(userId, {
      student_id: userId,
      resume_type: "online",
      content_json: { skills: profile.value.skills || [], projects: profile.value.projects || [] },
      file_url: "",
      version_no: nextVersion
    });
    await loadData();
  } catch (err) {
    // ignore
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
      version_no: resumes.value.length + 1
    });
    await loadData();
  } catch (e) {
    toast.error('上传失败');
  }
}

function formatTime(value) {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

onMounted(loadData);
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
