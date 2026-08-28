<template>
  <div class="accounts-page">
    <div class="page-header">
      <div>
        <div class="page-title">账户管理</div>
        <div class="page-subtitle">{{ accounts.length }} 个账户</div>
      </div>
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon>
        添加账户
      </el-button>
    </div>

    <!-- 总资产概览 -->
    <div class="app-card summary-card">
      <div class="summary-main">
        <div class="summary-label">总资产</div>
        <div class="summary-value money" :class="totalAssets >= 0 ? 'income' : 'expense'">
          {{ formatMoney(totalAssets) }}
        </div>
      </div>
      <div class="summary-types">
        <div v-for="t in summaryByType" :key="t.label" class="summary-type">
          <span class="dot" :style="{ background: t.color }"></span>
          <span>{{ t.label }}</span>
          <b class="money">{{ formatMoney(t.total) }}</b>
        </div>
      </div>
    </div>

    <!-- 账户卡片 -->
    <div class="accounts-grid" v-loading="loading">
      <div v-for="account in accounts" :key="account.id" class="app-card account-card">
        <div class="account-top">
          <div class="account-icon" :style="{ background: getAccountColor(account.account_type) }">
            <el-icon :size="20"><component :is="getAccountIcon(account.account_type)" /></el-icon>
          </div>
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, account)">
            <button class="more-btn">
              <el-icon :size="18"><MoreFilled /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="account-name">{{ account.name }}</div>
        <div class="account-type">{{ getAccountTypeName(account.account_type) }}</div>
        <div class="account-balance money" :class="account.balance >= 0 ? 'income' : 'expense'">
          {{ formatMoney(account.balance) }}
        </div>
        <div class="account-desc" v-if="account.description">{{ account.description }}</div>
      </div>
    </div>

    <!-- 添加/编辑弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingAccount ? '编辑账户' : '添加账户'"
      class="app-dialog"
      width="440px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="账户名称" />
        </el-form-item>
        <el-form-item label="类型" prop="account_type">
          <div class="type-grid">
            <button
              v-for="t in accountTypes"
              :key="t.value"
              :class="['type-option', { active: form.account_type === t.value }]"
              @click="form.account_type = t.value"
            >
              <el-icon :size="16"><component :is="t.icon" /></el-icon>
              {{ t.label }}
            </button>
          </div>
        </el-form-item>
        <el-form-item label="初始余额" prop="balance" v-if="!editingAccount">
          <el-input-number
            v-model="form.balance"
            :precision="2"
            :step="100"
            :controls="false"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { accountsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatMoney } from '@/utils/format'

const accounts = ref<any[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitting = ref(false)
const editingAccount = ref<any>(null)
const formRef = ref()

const accountTypes = [
  { label: '现金', value: 'cash', icon: 'Money' },
  { label: '银行卡', value: 'bank', icon: 'CreditCard' },
  { label: '信用卡', value: 'credit', icon: 'Wallet' },
  { label: '投资', value: 'investment', icon: 'TrendCharts' },
]

const form = reactive({
  name: '',
  account_type: 'cash',
  balance: 0,
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入账户名称', trigger: 'blur' }],
  account_type: [{ required: true, message: '请选择账户类型', trigger: 'change' }],
}

const totalAssets = computed(() =>
  accounts.value.reduce((sum, a) => sum + Number(a.balance || 0), 0)
)

const summaryByType = computed(() => {
  return accountTypes.map((t) => {
    const total = accounts.value
      .filter((a) => a.account_type === t.value)
      .reduce((sum, a) => sum + Number(a.balance || 0), 0)
    return { label: t.label, total, color: getAccountColor(t.value) }
  })
})

onMounted(() => {
  loadAccounts()
})

async function loadAccounts() {
  loading.value = true
  try {
    accounts.value = await accountsApi.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function getAccountColor(type: string) {
  const colors: Record<string, string> = {
    cash: '#10b981',
    bank: '#6366f1',
    credit: '#f59e0b',
    investment: '#06b6d4',
  }
  return colors[type] || '#94a3b8'
}

function getAccountIcon(type: string) {
  const icons: Record<string, string> = {
    cash: 'Money',
    bank: 'CreditCard',
    credit: 'Wallet',
    investment: 'TrendCharts',
  }
  return icons[type] || 'Wallet'
}

function getAccountTypeName(type: string) {
  return accountTypes.find((t) => t.value === type)?.label || type
}

function openAdd() {
  editingAccount.value = null
  form.name = ''
  form.account_type = 'cash'
  form.balance = 0
  form.description = ''
  showAddDialog.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (editingAccount.value) {
      await accountsApi.update(editingAccount.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await accountsApi.create(form)
      ElMessage.success('添加成功')
    }

    showAddDialog.value = false
    loadAccounts()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    submitting.value = false
  }
}

function handleCommand(command: string, account: any) {
  if (command === 'edit') {
    editingAccount.value = account
    form.name = account.name
    form.account_type = account.account_type
    form.description = account.description || ''
    showAddDialog.value = true
  } else if (command === 'delete') {
    ElMessageBox.confirm('确定要删除这个账户吗？', '确认')
      .then(async () => {
        await accountsApi.delete(account.id)
        ElMessage.success('已删除')
        loadAccounts()
      })
      .catch(() => {})
  }
}
</script>

<style scoped>
.summary-card {
  padding: 22px 20px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.summary-label {
  font-size: 13px;
  color: var(--app-text-3);
}

.summary-value {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.summary-types {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
}

.summary-type {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--app-text-3);
}

.summary-type b {
  font-size: 13px;
  color: var(--app-text-2);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.accounts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.account-card {
  padding: 18px;
}

.account-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.account-icon {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.12);
}

.more-btn {
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  border-radius: 10px;
  color: var(--app-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.more-btn:active {
  background: #f3f4f6;
}

.account-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

.account-type {
  margin-top: 3px;
  font-size: 12px;
  color: var(--app-text-3);
}

.account-balance {
  margin-top: 12px;
  font-size: 24px;
  font-weight: 800;
}

.account-desc {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--app-border);
  font-size: 12.5px;
  color: var(--app-text-3);
}

/* 类型选择 */
.type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.type-option {
  height: 44px;
  border: 1.5px solid var(--app-border);
  background: var(--app-surface);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: var(--app-text-2);
  cursor: pointer;
  transition: all 0.15s ease;
}

.type-option.active {
  border-color: var(--app-primary);
  background: var(--app-primary-soft);
  color: var(--app-primary-strong);
  font-weight: 600;
}

@media (min-width: 640px) {
  .accounts-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}

@media (min-width: 1024px) {
  .accounts-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .summary-card {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .summary-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-value {
    font-size: 34px;
  }
}
</style>
