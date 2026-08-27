<template>
  <div class="budgets-page">
    <div class="page-header">
      <h2>预算管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 添加预算
      </el-button>
    </div>
    
    <el-row :gutter="20" class="budget-overview">
      <el-col :span="8">
        <el-card>
          <div class="overview-item">
            <div class="overview-label">本月总预算</div>
            <div class="overview-value">¥{{ totalBudget.toFixed(2) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="overview-item">
            <div class="overview-label">已花费</div>
            <div class="overview-value expense">¥{{ totalSpent.toFixed(2) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="overview-item">
            <div class="overview-label">剩余预算</div>
            <div class="overview-value" :class="totalRemaining >= 0 ? 'income' : 'expense'">
              ¥{{ totalRemaining.toFixed(2) }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="budget-list">
      <el-table :data="budgets" v-loading="loading">
        <el-table-column prop="category_name" label="分类" width="150">
          <template #default="{ row }">
            {{ row.category_name || '总预算' }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="预算金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.amount.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="spent" label="已花费" width="120" align="right">
          <template #default="{ row }">
            <span class="expense">¥{{ (row.spent || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="使用进度">
          <template #default="{ row }">
            <el-progress
              :percentage="row.usage_percent || 0"
              :status="getProgressStatus(row.usage_percent)"
              :stroke-width="20"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="remaining" label="剩余" width="120" align="right">
          <template #default="{ row }">
            <span :class="(row.remaining || 0) >= 0 ? 'income' : 'expense'">
              ¥{{ (row.remaining || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="alert_threshold" label="预警阈值" width="100">
          <template #default="{ row }">
            {{ row.alert_threshold }}%
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showAddDialog" title="添加预算" width="400px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="总预算（留空）" clearable style="width: 100%">
            <el-option
              v-for="cat in expenseCategories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="form.amount" :min="1" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="周期">
          <el-select v-model="form.period" style="width: 100%">
            <el-option label="月度" value="monthly" />
            <el-option label="周度" value="weekly" />
            <el-option label="年度" value="yearly" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份" prop="year">
          <el-input-number v-model="form.year" :min="2020" :max="2100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="月份" v-if="form.period === 'monthly'">
          <el-select v-model="form.month" style="width: 100%">
            <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警阈值">
          <el-slider v-model="form.alert_threshold" :min="0" :max="100" show-input />
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
import { budgetsApi, categoriesApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const formRef = ref()
const budgets = ref<any[]>([])
const expenseCategories = ref<any[]>([])

const today = new Date()
const form = reactive({
  category_id: null,
  amount: 1000,
  period: 'monthly',
  year: today.getFullYear(),
  month: today.getMonth() + 1,
  alert_threshold: 80,
})

const rules = {
  amount: [{ required: true, message: '请输入金额' }],
  year: [{ required: true, message: '请输入年份' }],
}

const totalBudget = computed(() => budgets.value.reduce((sum, b) => sum + b.amount, 0))
const totalSpent = computed(() => budgets.value.reduce((sum, b) => sum + (b.spent || 0), 0))
const totalRemaining = computed(() => totalBudget.value - totalSpent.value)

onMounted(() => {
  loadBudgets()
  loadCategories()
})

async function loadBudgets() {
  loading.value = true
  try {
    budgets.value = await budgetsApi.list(form.year, form.month)
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    expenseCategories.value = await categoriesApi.list('expense')
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

function getProgressStatus(percent: number) {
  if (percent >= 100) return 'exception'
  if (percent >= 80) return 'warning'
  return ''
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    submitting.value = true
    await budgetsApi.create(form)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadBudgets()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这个预算吗？', '确认')
    await budgetsApi.delete(id)
    ElMessage.success('已删除')
    loadBudgets()
  } catch (error) {
    // 用户取消
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

.budget-overview {
  margin-bottom: 20px;
}

.overview-item {
  text-align: center;
}

.overview-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.overview-value {
  font-size: 24px;
  font-weight: bold;
}

.income { color: #67c23a; }
.expense { color: #f56c6c; }
</style>
