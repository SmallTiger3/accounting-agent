<template>
  <div class="app-shell">
    <!-- 桌面端侧边导航 -->
    <aside class="sidebar desktop-only">
      <div class="brand">
        <div class="brand-logo">
          <el-icon :size="20"><Wallet /></el-icon>
        </div>
        <span class="brand-name">记账Agent</span>
      </div>

      <nav class="nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { active: isActive(item.path) }]"
        >
          <el-icon :size="19"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-user">
        <div class="avatar">{{ avatarText }}</div>
        <div class="user-meta">
          <div class="user-name">{{ displayName }}</div>
          <button class="logout-btn" @click="handleLogout">退出登录</button>
        </div>
      </div>
    </aside>

    <div class="app-body">
      <!-- 移动端顶栏 -->
      <header class="topbar mobile-only">
        <div class="brand compact">
          <div class="brand-logo">
            <el-icon :size="18"><Wallet /></el-icon>
          </div>
          <span class="brand-name">记账Agent</span>
        </div>
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="topbar-user">
            <div class="avatar small">{{ avatarText }}</div>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>{{ displayName }}</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <main :class="['content', { 'is-chat': route.path === '/chat' }]">
        <router-view />
      </main>
    </div>

    <!-- 移动端底部导航 -->
    <nav class="bottom-nav mobile-only">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="['tab-item', { active: isActive(item.path) }]"
      >
        <el-icon :size="22"><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { path: '/', label: '看板', icon: 'DataAnalysis' },
  { path: '/chat', label: '对话', icon: 'ChatDotRound' },
  { path: '/transactions', label: '交易', icon: 'List' },
  { path: '/accounts', label: '账户', icon: 'CreditCard' },
  { path: '/budgets', label: '预算', icon: 'Money' },
]

const displayName = computed(() => authStore.user?.username || '用户')
const avatarText = computed(() => displayName.value.slice(0, 1).toUpperCase())

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function handleCommand(command: string) {
  if (command === 'logout') handleLogout()
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-shell {
  height: 100dvh;
  display: flex;
  flex-direction: column;
}

/* ============ 桌面端侧边栏 ============ */
.sidebar {
  width: 224px;
  flex-shrink: 0;
  background: var(--app-surface);
  border-right: 1px solid var(--app-border);
  display: none;
  flex-direction: column;
  padding: 20px 14px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
}

.brand.compact {
  padding: 0;
}

.brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(135deg, #10b981, #0d9488);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.35);
  flex-shrink: 0;
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--app-text);
  letter-spacing: 0.5px;
}

.nav {
  flex: 1;
  margin-top: 26px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 12px;
  color: var(--app-text-2);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: #f3f4f6;
  color: var(--app-text);
}

.nav-item.active {
  background: var(--app-primary-soft);
  color: var(--app-primary-strong);
  font-weight: 600;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: #f8fafc;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #0d9488);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
}

.avatar.small {
  width: 32px;
  height: 32px;
  font-size: 13px;
}

.user-meta {
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-btn {
  border: none;
  background: none;
  padding: 0;
  margin-top: 2px;
  font-size: 12px;
  color: var(--app-text-3);
  cursor: pointer;
}

.logout-btn:hover {
  color: var(--app-expense);
}

/* ============ 移动端顶栏 ============ */
.topbar {
  height: var(--topbar-h);
  flex-shrink: 0;
  display: none;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--app-border);
}

.topbar-user {
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
}

/* ============ 内容区 ============ */
.app-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 28px;
}

.content > :deep(*) {
  max-width: 1160px;
  margin-left: auto;
  margin-right: auto;
}

.content.is-chat {
  overflow: hidden;
  padding: 0;
}

/* ============ 移动端底部导航 ============ */
.bottom-nav {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid var(--app-border);
  display: none;
  padding-bottom: env(safe-area-inset-bottom);
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: var(--tabbar-h);
  flex: 1;
  color: var(--app-text-3);
  font-size: 11px;
  text-decoration: none;
  transition: color 0.15s ease;
}

.tab-item.active {
  color: var(--app-primary-strong);
  font-weight: 600;
}

.tab-item.active .el-icon {
  filter: drop-shadow(0 2px 6px rgba(16, 185, 129, 0.35));
}

/* ============ 响应式断点（参考 Maybe：lg = 1024px） ============ */
@media (min-width: 1024px) {
  .app-shell {
    flex-direction: row;
  }

  .sidebar {
    display: flex;
  }

  .app-body {
    flex: 1;
    min-width: 0;
  }
}

@media (max-width: 1023.98px) {
  .topbar {
    display: flex;
  }

  .bottom-nav {
    display: flex;
  }
}
</style>
