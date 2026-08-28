<template>
  <div class="budgets-page">
    <div class="page-header">
      <div>
        <div class="page-title">预算管理</div>
        <div class="page-subtitle">按预算控制支出，超支自动提醒</div>
      </div>
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon>
        添加预算
      </el-button>
    </div>

    <!-- 月份切换 + 概览 -->
    <div class="overview-row">
      <div class="overview-cards">
        <div class="app-card overview-card">
          <div class="overview-label">本月总预算</div>
          <div class="overview-value money">{{ formatMoney(totalBudget) }}</div>
        </div>
        <div class="app-card overview-card">
          <div class="overview-label">已花费</div>
          <div class="overview-value money expense">{{ formatMoney(totalSpent) }}</div>
        </div>
        <div class="app-card overview-card">
          <div class="overview-label">剩余预算</div>
          <div class="overview-value money" :class="totalRemaining >= 0 ? 'income' : 'expense'">
            {{ formatMoney(totalRemaining) }}
          </div>
        </div>
      </div>
      <div class="month-picker">
        <el-date-picker
          v-model="viewMonth"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="handleMonthChange"
        />
      </div>
    </div>

    <!-- 桌面端表格 -->
    <div class="app-card table-card desktop-only">
      <el-table :data="budgets" v-loading="loading" class="budget-table">
        <el-table-column prop="category_name" label="分类" width="160">
          <template #default="{ row }">
            <span class="cat-name">{{ row.category_name || '总预算' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="预算金额" width="130" align="right">
          <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="spent" label="已花费" width="130" align="right">
          <template #default="{ row }">
            <span class="money expense">{{ formatMoney(row.spent || 0) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="使用进度" min-width="200">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="Math.min(row.usage_percent || 0, 100)"
                :status="getProgressStatus(row.usage_percent)"
                :stroke-width="14"
                :show-text="false"
              />
              <span class="progress-text" :class="getProgressClass(row.usage_percent)">
                {{ row.usage_percent || 0 }}%
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="remaining" label="剩余" width="130" align="right">
          <template #default="{ row }">
            <span class="money" :class="(row.remaining || 0) >= 0 ? 'income' : 'expense'">
              {{ formatMoney(row.remaining || 0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 移动端卡片 -->
    <div class="mobile-list mobile-only" v-loading="loading">
      <div v-if="budgets.length">
        <div v-for="budget in budgets" :key="budget.id" class="app-card budget-card">
          <div class="budget-head">
            <div class="budget-cat">
              <div class="cat-dot" :class="getProgressClass(budget.usage_percent)"></div>
              <span>{{ budget.category_name || '总预算' }}</span>
            </div>
            <button class="budget-delete" @click="handleDelete(budget.id)">
              <el-icon :size="15"><Delete /></el-icon>
            </button>
          </div>
          <div class="budget-progress">
            <el-progress
              :percentage="Math.min(budget.usage_percent || 0, 100)"
              :status="getProgressStatus(budget.usage_percent)"
              :stroke-width="10"
              :show-text="false"
            />
          </div>
          <div class="budget-stats">
            <div>
              <span class="stat-label">已花费</span>
              <span class="money expense">{{ formatMoney(budget.spent || 0) }}</span>
            </div>
            <div>
              <span class="stat-label">剩余</span>
              <span class="money" :class="(budget.remaining || 0) >= 0 ? 'income' : 'expense'">
                {{ formatMoney(budget.remaining || 0) }}
              </span>
            </div>
            <div>
              <span class="stat-label">预算</span>
              <span class="money">{{ formatMoney(budget.amount) }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="!loading" class="mobile-empty">
        <el-icon :size="36"><Money /></el-icon>
        <p>本月还没有预算，点击右上角添加</p>
      </div>
    </div>

    <!-- 添加预算弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加预算"
      class="app-dialog"
      width="440px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
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
          <el-input-number
            v-model="form.amount"
            :min="1"
            :precision="2"
            :controls="false"
            style="width: 100%"
          />
        </el-form-item>
        <div class="form-row">
          <el-form-item label="周期">
            <el-select v-model="form.period" style="width: 100%">
              <el-option label="月度" value="monthly" />
              <el-option label="周度" value="weekly" />
              <el-option label="年度" value="yearly" />
            </el-select>
          </el-form-item>
          <el-form-item label="月份" v-if="form.period === 'monthly'">
            <el-select v-model="form.month" style="width: 100%">
              <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="预警阈值">
          <div class="threshold-row">
            <el-slider v-model="form.alert_threshold" :min="0" :max="100" class="threshold-slider" />
            <span class="threshold-value">{{ form.alert_threshold }}%</span>
          </div>
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
import dayjs from 'dayjs'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const formRef = ref()
const budgets = ref<any[]>([])
const expenseCategories = ref<any[]>([])
const viewMonth = ref(dayjs().format('YYYY-MM'))

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
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
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

function handleMonthChange(value: string) {
  if (!value) return
  const d = dayjs(value)
  form.year = d.year()
  form.month = d.month() + 1
  loadBudgets()
}

function getProgressStatus(percent: number) {
  if (percent >= 100) return 'exception'
  if (percent >= 80) return 'warning'
  return 'success'
}

function getProgressClass(percent: number) {
  if (percent >= 100) return 'over'
  if (percent >= 80) return 'warn'
  return 'ok'
}

function openAdd() {
  form.category_id = null
  form.amount = 1000
  form.period = 'monthly'
  form.alert_threshold = 80
  showAddDialog.value = true
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
.overview-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.overview-card {
  padding: 16px 14px;
  text-align: center;
}

.overview-label {
  font-size: 12px;
  color: var(--app-text-3);
  margin-bottom: 6px;
}

.overview-value {
  font-size: 17px;
  font-weight: 800;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.month-picker {
  display: flex;
  justify-content: flex-end;
}

.month-picker :deep(.el-date-editor) {
  width: 150px;
}

/* 桌面表格 */
.table-card {
  padding: 8px 16px 16px;
}

.budget-table :deep(.el-table__header th) {
  background: #f8fafc;
  color: var(--app-text-2);
  font-weight: 600;
}

.cat-name {
  font-weight: 600;
  color: var(--app-text);
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-cell :deep(.el-progress) {
  flex: 1;
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  min-width: 34px;
  text-align: right;
}

.ok { color: var(--app-income); }
.warn { color: var(--app-warning); }
.over { color: var(--app-expense); }

/* 移动端卡片 */
.mobile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.budget-card {
  padding: 16px;
}

.budget-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.budget-cat {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}

.cat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.cat-dot.ok { background: var(--app-income); }
.cat-dot.warn { background: var(--app-warning); }
.cat-dot.over { background: var(--app-expense); }

.budget-delete {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: var(--app-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.budget-delete:active {
  background: var(--app-expense-soft);
  color: var(--app-expense);
}

.budget-progress {
  margin-bottom: 14px;
}

.budget-stats {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--app-border);
}

.budget-stats > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-label {
  font-size: 11px;
  color: var(--app-text-3);
}

.budget-stats .money {
  font-size: 13px;
  font-weight: 700;
}

.mobile-empty {
  padding: 60px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--app-text-3);
  font-size: 13px;
}

/* 弹窗 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 14px;
}

.threshold-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
}

.threshold-slider {
  flex: 1;
}

.threshold-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-primary-strong);
  min-width: 42px;
  text-align: right;
}

@media (min-width: 768px) {
  .overview-row {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .overview-cards {
    gap: 16px;
    flex: 1;
  }

  .overview-card {
    padding: 20px;
  }

  .overview-value {
    font-size: 22px;
  }
}

@media (max-width: 767px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
