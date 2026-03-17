<template>
  <div class="login-page">
    <section class="login-hero">
      <div class="container login-grid">
        <div class="login-copy">
          <span class="tag mono">校园招聘 · 统一入口</span>
          <h1>登录或注册，进入对应角色工作台</h1>
          <p>学生、校方、招聘公司分开管理，数据与流程更清晰。</p>
          <div class="login-points">
            <div class="point">
              <strong>学生</strong>
              <span>岗位匹配 + 面试准备</span>
            </div>
            <div class="point">
              <strong>校方</strong>
              <span>资质审核 + 数据监管</span>
            </div>
            <div class="point">
              <strong>招聘公司</strong>
              <span>岗位发布 + 候选人沟通</span>
            </div>
          </div>
        </div>
        <div class="card login-card">
          <div class="mode-tabs">
            <button class="chip" :class="{ active: mode === 'login' }" @click="mode = 'login'">
              登录
            </button>
            <button class="chip" :class="{ active: mode === 'register' }" @click="mode = 'register'">
              注册
            </button>
          </div>

          <div v-if="mode === 'register'" class="role-tabs">
            <button class="chip" :class="{ active: role === 'student' }" @click="role = 'student'">
              学生注册
            </button>
            <button class="chip" :class="{ active: role === 'company' }" @click="role = 'company'">
              企业注册
            </button>
          </div>

          <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="login-form">
            <label>
              邮箱
              <input v-model="loginForm.email" type="email" placeholder="请输入邮箱" required />
            </label>
            <label>
              密码
              <input v-model="loginForm.password" type="password" placeholder="请输入密码" required />
            </label>
            <button class="btn" type="submit" :disabled="loading">
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </form>

          <form v-else @submit.prevent="handleRegister" class="login-form">
            <template v-if="role === 'student'">
              <label>
                姓名
                <input v-model="studentForm.name" placeholder="请输入姓名" required />
              </label>
              <label>
                学号
                <input v-model="studentForm.student_no" placeholder="请输入学号" required />
              </label>
              <label>
                学校
                <input v-model="studentForm.school" placeholder="请输入学校" required />
              </label>
              <label>
                专业
                <input v-model="studentForm.major" placeholder="请输入专业" required />
              </label>
              <label>
                年级
                <input v-model="studentForm.grade" placeholder="请输入年级" required />
              </label>
              <label>
                电话
                <input v-model="studentForm.phone" placeholder="请输入手机号" required />
              </label>
              <label>
                邮箱
                <input v-model="studentForm.email" type="email" placeholder="请输入邮箱" required />
              </label>
              <label>
                密码
                <input v-model="studentForm.password" type="password" placeholder="请输入密码" required />
              </label>
            </template>

            <template v-else>
              <label>
                企业名称
                <input v-model="companyForm.company_name" placeholder="请输入企业名称" required />
              </label>
              <label>
                统一信用代码
                <input v-model="companyForm.credit_code" placeholder="请输入信用代码" required />
              </label>
              <label>
                联系人
                <input v-model="companyForm.contact_name" placeholder="请输入联系人" required />
              </label>
              <label>
                联系电话
                <input v-model="companyForm.contact_phone" placeholder="请输入联系电话" required />
              </label>
              <label>
                企业邮箱
                <input v-model="companyForm.email" type="email" placeholder="请输入邮箱" required />
              </label>
              <label>
                密码
                <input v-model="companyForm.password" type="password" placeholder="请输入密码" required />
              </label>
              <label>
                所属行业
                <input v-model="companyForm.industry" placeholder="请输入行业" />
              </label>
              <label>
                企业规模
                <input v-model="companyForm.scale" placeholder="例如 50-100" />
              </label>
              <label>
                企业地址
                <input v-model="companyForm.address" placeholder="请输入企业地址" />
              </label>
              <label>
                企业官网
                <input v-model="companyForm.website" placeholder="请输入官网" />
              </label>
              <label>
                企业简介
                <input v-model="companyForm.description" placeholder="一句话介绍企业" />
              </label>
              <label>
                福利标签（逗号分隔）
                <input v-model="companyForm.welfare" placeholder="如 弹性工作, 年度体检" />
              </label>
            </template>

            <button class="btn" type="submit" :disabled="loading">
              {{ loading ? '提交中...' : '完成注册' }}
            </button>
          </form>

          <div v-if="error" class="error">{{ error }}</div>

          <div v-if="mode === 'login'" class="quick-login">
            <p class="mono">演示账号（密码统一 123456）：</p>
            <div class="quick-actions">
              <button class="chip" @click="fillDemo('student')">学生 student@test.com</button>
              <button class="chip" @click="fillDemo('company')">企业 company@test.com</button>
              <button class="chip" @click="fillDemo('admin')">管理员 admin@test.com</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { registerCompany, registerStudent } from "../services/api";
import { useAuth } from "../store/auth";

const router = useRouter();
const auth = useAuth();

const mode = ref("login");
const role = ref("student");
const loading = ref(false);
const error = ref("");

const loginForm = ref({
  email: "",
  password: ""
});

const studentForm = ref({
  name: "",
  student_no: "",
  school: "",
  major: "",
  grade: "",
  phone: "",
  email: "",
  password: ""
});

const companyForm = ref({
  company_name: "",
  credit_code: "",
  contact_name: "",
  contact_phone: "",
  email: "",
  password: "",
  description: "",
  industry: "",
  scale: "",
  address: "",
  website: "",
  welfare: ""
});

const demoAccounts = {
  student: { email: "student@test.com", password: "123456" },
  company: { email: "company@test.com", password: "123456" },
  admin: { email: "admin@test.com", password: "123456" }
};

function fillDemo(type) {
  const demo = demoAccounts[type];
  loginForm.value.email = demo.email;
  loginForm.value.password = demo.password;
  handleLogin();
}

async function handleLogin() {
  loading.value = true;
  error.value = "";
  try {
    await auth.login({ email: loginForm.value.email, password: loginForm.value.password });
    router.push("/dashboard");
  } catch (err) {
    error.value = "登录失败，请检查邮箱或密码。";
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  loading.value = true;
  error.value = "";
  try {
    if (role.value === "student") {
      await registerStudent(studentForm.value);
      await auth.login({ email: studentForm.value.email, password: studentForm.value.password });
    } else {
      await registerCompany({
        ...companyForm.value,
        welfare_tags: companyForm.value.welfare
          ? companyForm.value.welfare.split(",").map((item) => item.trim()).filter(Boolean)
          : []
      });
      await auth.login({ email: companyForm.value.email, password: companyForm.value.password });
    }
    router.push("/dashboard");
  } catch (err) {
    error.value = "注册失败，请检查填写内容。";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  padding: 32px 0 60px;
}

.login-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  align-items: start;
}

.login-copy {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.login-points {
  display: grid;
  gap: 12px;
}

.point {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 14px;
  background: #fff;
}

.login-card {
  gap: 16px;
}

.mode-tabs,
.role-tabs {
  display: flex;
  gap: 8px;
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
}

.error {
  color: #eb5757;
  font-size: 13px;
}

.quick-login {
  border-top: 1px dashed var(--line);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
