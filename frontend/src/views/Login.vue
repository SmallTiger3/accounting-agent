<template>
  <div class="login-page">
    <div class="decor decor-1"></div>
    <div class="decor decor-2"></div>

    <div class="login-card">
      <div class="login-brand">
        <div class="brand-logo">
          <el-icon :size="26"><Wallet /></el-icon>
        </div>
        <h1>记账Agent</h1>
        <p>智能 AI 记账助手，一句话帮你记好每一笔账</p>
      </div>

      <div class="login-body">
        <div class="segmented">
          <button
            :class="['seg-btn', { active: activeTab === 'login' }]"
            @click="activeTab = 'login'"
          >
            登录
          </button>
          <button
            :class="['seg-btn', { active: activeTab === 'register' }]"
            @click="activeTab = 'register'"
          >
            注册
          </button>
        </div>

        <!-- 登录 -->
        <el-form
          v-show="activeTab === 'login'"
          :model="loginForm"
          :rules="rules"
          ref="loginFormRef"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              size="large"
              placeholder="用户名"
              :prefix-icon="User"
              autocomplete="username"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              size="large"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              show-password
              autocomplete="current-password"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form>

        <!-- 注册 -->
        <el-form
          v-show="activeTab === 'register'"
          :model="registerForm"
          :rules="registerRules"
          ref="registerFormRef"
          @submit.prevent="handleRegister"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              size="large"
              placeholder="用户名（3-50位）"
              :prefix-icon="User"
              autocomplete="username"
            />
          </el-form-item>
          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              size="large"
              placeholder="邮箱"
              :prefix-icon="Message"
              autocomplete="email"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              size="large"
              type="password"
              placeholder="密码（至少6位）"
              :prefix-icon="Lock"
              show-password
              autocomplete="new-password"
            />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              size="large"
              type="password"
              placeholder="确认密码"
              :prefix-icon="Lock"
              show-password
              autocomplete="new-password"
              @keyup.enter="handleRegister"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleRegister"
          >
            注册并登录
          </el-button>
        </el-form>
      </div>

      <div class="login-footer">数据私有安全 · AI 自动分类 · 预算提醒</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50之间', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleLogin() {
  try {
    await loginFormRef.value?.validate()
    loading.value = true
    await authStore.login(loginForm.username, loginForm.password)
    ElMessage.success('欢迎回来')
    router.push('/')
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  try {
    await registerFormRef.value?.validate()
    loading.value = true
    await authStore.register(registerForm.username, registerForm.email, registerForm.password)
    ElMessage.success('注册成功，正在登录…')
    await authStore.login(registerForm.username, registerForm.password)
    router.push('/')
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background:
    radial-gradient(640px 420px at 12% 8%, rgba(16, 185, 129, 0.1), transparent 60%),
    radial-gradient(560px 420px at 88% 92%, rgba(13, 148, 136, 0.1), transparent 60%),
    var(--app-bg);
  position: relative;
  overflow: hidden;
}

.decor {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  opacity: 0.5;
  pointer-events: none;
}

.decor-1 {
  width: 260px;
  height: 260px;
  top: -90px;
  right: -60px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.16), transparent 70%);
}

.decor-2 {
  width: 320px;
  height: 320px;
  bottom: -120px;
  left: -80px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.12), transparent 70%);
}

.login-card {
  position: relative;
  width: 400px;
  max-width: 100%;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 24px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04), 0 24px 64px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.login-brand {
  padding: 36px 36px 8px;
  text-align: center;
}

.brand-logo {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #10b981, #0d9488);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 24px rgba(16, 185, 129, 0.35);
}

.login-brand h1 {
  font-size: 24px;
  font-weight: 800;
  color: var(--app-text);
  letter-spacing: 0.5px;
}

.login-brand p {
  margin-top: 8px;
  font-size: 13px;
  color: var(--app-text-3);
  line-height: 1.6;
}

.login-body {
  padding: 24px 36px 8px;
}

.segmented {
  display: flex;
  background: #f1f2f4;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 22px;
}

.seg-btn {
  flex: 1;
  height: 38px;
  border: none;
  background: transparent;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-3);
  cursor: pointer;
  transition: all 0.18s ease;
}

.seg-btn.active {
  background: var(--app-surface);
  color: var(--app-primary-strong);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
  letter-spacing: 2px;
  font-weight: 600;
}

.login-footer {
  padding: 20px 36px 24px;
  text-align: center;
  font-size: 12px;
  color: var(--app-text-3);
}

@media (max-width: 767px) {
  .login-card {
    border-radius: 20px;
  }

  .login-brand {
    padding: 28px 24px 4px;
  }

  .login-body {
    padding: 20px 24px 4px;
  }

  .login-footer {
    padding: 16px 24px 20px;
  }
}
</style>
