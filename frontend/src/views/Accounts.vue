<template>
  <div class="accounts-page">
    <div class="page-header">
      <h2>账户管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 添加账户
      </el-button>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="8" v-for="account in accounts" :key="account.id">
        <el-card class="account-card" shadow="hover">
          <div class="account-header">
            <div class="account-icon" :style="{ background: getAccountColor(account.account_type) }">
              <el-icon size="24"><CreditCard /></el-icon>
            </div>
            <el-dropdown @command="(cmd: string) => handleCommand(cmd, account)">
              <el-icon class="more-btn"><More /></el-icon>
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
          <div class="account-balance" :class="account.balance >= 0 ? 'positive' : 'negative'">
            ¥{{ account.balance.toFixed(2) }}
          </div>
          <div class="account-desc" v-if="account.description">{{ account.description }}</div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-dialog v-model="showAddDialog" :title="editingAccount ? '编辑账户' : '添加账户'" width="400px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="账户名称" />
        </el-form-item>
        <el-form-item label="类型" prop="account_type">
          <el-select v-model="form.account_type" style="width: 100%">
            <el-option label="现金" value="cash" />
            <el-option label="银行卡" value="bank" />
            <el-option label="信用卡" value="credit" />
            <el-option label="投资账户" value="investment" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始余额" prop="balance" v-if="!editingAccount">
          <el-input-number v-model="form.balance" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
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
import { ref, reactive, onMounted } from 'vue'
import { accountsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const accounts = ref<any[]>([])
const showAddDialog = ref(false)
const submitting = ref(false)
const editingAccount = ref<any>(null)
const formRef = ref()

const form = reactive({
  name: '',
  account_type: 'cash',
  balance: 0,
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入账户名称' }],
  account_type: [{ required: true, message: '请选择账户类型' }],
}

onMounted(() => {
  loadAccounts()
})

async function loadAccounts() {
  try {
    accounts.value = await accountsApi.list()
  } catch (error) {
    ElMessage.error('加载失败')
  }
}

function getAccountColor(type: string) {
  const colors: Record<string, string> = {
    cash: '#67c23a',
    bank: '#409eff',
    credit: '#e6a23c',
    investment: '#f56c6c',
  }
  return colors[type] || '#909399'
}

function getAccountTypeName(type: string) {
  const names: Record<string, string> = {
    cash: '现金',
    bank: '银行卡',
    credit: '信用卡',
    investment: '投资账户',
  }
  return names[type] || type
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
    editingAccount.value = null
    form.name = ''
    form.account_type = 'cash'
    form.balance = 0
    form.description = ''
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
    ElMessageBox.confirm('确定要删除这个账户吗？', '确认').then(async () => {
      await accountsApi.delete(account.id)
      ElMessage.success('已删除')
      loadAccounts()
    }).catch(() => {})
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.account-card {
  margin-bottom: 20px;
}

.account-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.account-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.more-btn {
  cursor: pointer;
  color: #909399;
}

.account-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.account-type {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.account-balance {
  font-size: 28px;
  font-weight: bold;
}

.account-balance.positive { color: #67c23a; }
.account-balance.negative { color: #f56c6c; }

.account-desc {
  margin-top: 12px;
  font-size: 14px;
  color: #909399;
}
</style>
