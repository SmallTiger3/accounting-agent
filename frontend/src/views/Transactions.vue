<template>
  <div class="transactions-page">
    <div class="page-header">
      <div>
        <div class="page-title">交易记录</div>
        <div class="page-subtitle">共 {{ pagination.total }} 笔</div>
      </div>
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon>
        记一笔
      </el-button>
    </div>

    <!-- 筛选 -->
    <div class="app-card filter-card">
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent="loadTransactions">
        <el-form-item label="类型">
          <el-select v-model="filters.transaction_type" clearable placeholder="全部" style="width: 110px">
            <el-option label="收入" value="income" />
            <el-option label="支出" value="expense" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="date-picker"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索描述"
            clearable
            class="keyword-input"
            @keyup.enter="loadTransactions"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTransactions">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 桌面端表格 -->
    <div class="app-card table-card desktop-only">
      <el-table :data="transactions" v-loading="loading" class="txn-table">
        <el-table-column prop="transaction_date" label="日期" width="120" />
        <el-table-column prop="transaction_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.transaction_type === 'income' ? 'success' : 'danger'" size="small">
              {{ row.transaction_type === 'income' ? '收入' : '支出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="110" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" width="140" align="right">
          <template #default="{ row }">
            <span class="money" :class="row.transaction_type">
              {{ formatSignedMoney(row.amount, row.transaction_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="account_name" label="账户" width="120" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="loadTransactions"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 移动端卡片列表 -->
    <div class="mobile-list mobile-only" v-loading="loading">
      <div v-if="transactions.length">
        <div v-for="txn in transactions" :key="txn.id" class="app-card txn-card">
          <div class="txn-icon" :class="txn.transaction_type">
            <el-icon :size="17">
              <component :is="txn.transaction_type === 'income' ? 'Top' : 'Bottom'" />
            </el-icon>
          </div>
          <div class="txn-main">
            <div class="txn-desc">{{ txn.description || txn.category_name || '未分类' }}</div>
            <div class="txn-meta">
              <span class="cat-chip">{{ txn.category_name }}</span>
              <span>{{ txn.transaction_date }}</span>
              <span>{{ txn.account_name }}</span>
            </div>
          </div>
          <div class="txn-right">
            <div class="money txn-amount" :class="txn.transaction_type">
              {{ formatSignedMoney(txn.amount, txn.transaction_type) }}
            </div>
            <button class="txn-delete" @click="handleDelete(txn.id)">
              <el-icon :size="15"><Delete /></el-icon>
            </button>
          </div>
        </div>
      </div>
      <div v-else-if="!loading" class="mobile-empty">
        <el-icon :size="36"><Document /></el-icon>
        <p>没有找到交易记录</p>
      </div>

      <div v-if="pagination.total > pagination.pageSize" class="mobile-pagination">
        <el-button
          :disabled="pagination.page <= 1"
          round
          @click="pagination.page--; loadTransactions()"
        >
          上一页
        </el-button>
        <span>{{ pagination.page }} / {{ Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) }}</span>
        <el-button
          :disabled="pagination.page >= Math.ceil(pagination.total / pagination.pageSize)"
          round
          @click="pagination.page++; loadTransactions()"
        >
          下一页
        </el-button>
      </div>
    </div>

    <!-- 记一笔弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      title="记一笔"
      class="app-dialog"
      width="520px"
      destroy-on-close
    >
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-position="top">
        <div class="type-switch">
          <button
            :class="['type-btn', 'expense', { active: addForm.transaction_type === 'expense' }]"
            @click="addForm.transaction_type = 'expense'"
          >
            <el-icon :size="18"><Bottom /></el-icon>
            支出
          </button>
          <button
            :class="['type-btn', 'income', { active: addForm.transaction_type === 'income' }]"
            @click="addForm.transaction_type = 'income'"
          >
            <el-icon :size="18"><Top /></el-icon>
            收入
          </button>
        </div>

        <el-form-item prop="amount" label="金额">
          <div class="amount-input">
            <span class="amount-prefix">¥</span>
            <el-input
              v-model="amountText"
              type="text"
              inputmode="decimal"
              placeholder="0.00"
              size="large"
              @input="handleAmountInput"
            />
          </div>
        </el-form-item>

        <div class="form-grid">
          <el-form-item prop="category_id" label="分类">
            <el-select v-model="addForm.category_id" placeholder="选择分类" style="width: 100%">
              <el-option
                v-for="cat in filteredCategories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item prop="account_id" label="账户">
            <el-select v-model="addForm.account_id" placeholder="选择账户" style="width: 100%">
              <el-option
                v-for="acc in accounts"
                :key="acc.id"
                :label="acc.name"
                :value="acc.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item prop="transaction_date" label="日期">
            <el-date-picker
              v-model="addForm.transaction_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="addForm.description" type="textarea" :rows="2" placeholder="可选" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="adding">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { transactionsApi, accountsApi, categoriesApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatSignedMoney } from '@/utils/format'

const loading = ref(false)
const adding = ref(false)
const showAddDialog = ref(false)
const addFormRef = ref()
const transactions = ref<any[]>([])
const accounts = ref<any[]>([])
const categories = ref<any[]>([])
const dateRange = ref<string[]>([])
const amountText = ref('')

const filters = reactive({
  transaction_type: '',
  start_date: '',
  end_date: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const addForm = reactive({
  transaction_type: 'expense',
  amount: 0,
  category_id: null,
  account_id: null,
  transaction_date: new Date().toISOString().split('T')[0],
  description: '',
})

const addRules = {
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    {
      validator: (rule: any, value: number, callback: Function) => {
        if (!value || value <= 0) callback(new Error('金额需大于 0'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  account_id: [{ required: true, message: '请选择账户', trigger: 'change' }],
  transaction_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
}

const filteredCategories = computed(() => {
  return categories.value.filter((c) => c.category_type === addForm.transaction_type)
})

onMounted(() => {
  loadTransactions()
  loadAccounts()
  loadCategories()
})

async function loadTransactions() {
  loading.value = true
  try {
    const data: any = await transactionsApi.list({
      ...filters,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    transactions.value = data.items
    pagination.total = data.total
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadAccounts() {
  try {
    accounts.value = await accountsApi.list()
  } catch (error) {
    console.error('Failed to load accounts:', error)
  }
}

async function loadCategories() {
  try {
    categories.value = await categoriesApi.list()
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

function handleDateChange(dates: string[]) {
  if (dates) {
    filters.start_date = dates[0]
    filters.end_date = dates[1]
  } else {
    filters.start_date = ''
    filters.end_date = ''
  }
}

function handleSizeChange() {
  pagination.page = 1
  loadTransactions()
}

function openAdd() {
  addForm.amount = 0
  amountText.value = ''
  addForm.description = ''
  showAddDialog.value = true
}

function handleAmountInput(value: string) {
  const cleaned = value.replace(/[^\d.]/g, '')
  const parts = cleaned.split('.')
  let normalized = parts[0]
  if (parts.length > 1) normalized += '.' + parts.slice(1).join('').slice(0, 2)
  amountText.value = normalized
  addForm.amount = parseFloat(normalized) || 0
}

async function handleAdd() {
  try {
    await addFormRef.value?.validate()
    adding.value = true
    await transactionsApi.create(addForm)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadTransactions()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    adding.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这笔交易吗？', '确认')
    await transactionsApi.delete(id)
    ElMessage.success('已删除')
    loadTransactions()
  } catch (error) {
    // 用户取消
  }
}
</script>

<style scoped>
.filter-card {
  padding: 16px;
  margin-bottom: 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: flex-end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.date-picker {
  width: 260px;
}

.keyword-input {
  width: 180px;
}

.table-card {
  padding: 8px 16px 16px;
}

.txn-table {
  width: 100%;
}

.txn-table :deep(.el-table__header th) {
  background: #f8fafc;
  color: var(--app-text-2);
  font-weight: 600;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* ============ 移动端卡片 ============ */
.mobile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.txn-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
}

.txn-icon {
  width: 40px;
  height: 40px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.txn-icon.income {
  background: var(--app-income-soft);
  color: var(--app-income);
}

.txn-icon.expense {
  background: var(--app-expense-soft);
  color: var(--app-expense);
}

.txn-main {
  flex: 1;
  min-width: 0;
}

.txn-desc {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.txn-meta {
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--app-text-3);
  overflow: hidden;
  white-space: nowrap;
}

.cat-chip {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--app-text-2);
  flex-shrink: 0;
}

.txn-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.txn-amount {
  font-size: 15px;
  font-weight: 700;
}

.txn-delete {
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

.txn-delete:active {
  background: var(--app-expense-soft);
  color: var(--app-expense);
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

.mobile-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 8px 0 4px;
  font-size: 13px;
  color: var(--app-text-2);
}

/* ============ 记一笔弹窗 ============ */
.type-switch {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
}

.type-btn {
  flex: 1;
  height: 44px;
  border: 1.5px solid var(--app-border);
  background: var(--app-surface);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-2);
  cursor: pointer;
  transition: all 0.15s ease;
}

.type-btn.expense.active {
  border-color: var(--app-expense);
  background: var(--app-expense-soft);
  color: var(--app-expense);
}

.type-btn.income.active {
  border-color: var(--app-income);
  background: var(--app-income-soft);
  color: var(--app-income);
}

.amount-input {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 6px 14px;
}

.amount-prefix {
  font-size: 20px;
  font-weight: 700;
  color: var(--app-text-2);
}

.amount-input :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none !important;
}

.amount-input :deep(.el-input__inner) {
  font-size: 26px;
  font-weight: 700;
  height: 40px;
  color: var(--app-text);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 14px;
}

.form-grid :deep(.el-form-item:last-child) {
  grid-column: 1 / -1;
}

@media (max-width: 1023.98px) {
  .filter-card {
    padding: 14px;
  }

  .filter-form {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-form :deep(.el-form-item) {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    margin-bottom: 10px;
  }

  .filter-form :deep(.el-form-item__label) {
    justify-content: flex-start;
    padding-bottom: 4px;
  }

  .date-picker,
  .keyword-input {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .form-grid :deep(.el-form-item:last-child) {
    grid-column: auto;
  }
}
</style>
