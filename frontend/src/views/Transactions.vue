<template>
  <div class="transactions-page">
    <div class="page-header">
      <h2>交易记录</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 记一笔
      </el-button>
    </div>
    
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="类型">
          <el-select v-model="filters.transaction_type" clearable placeholder="全部">
            <el-option label="收入" value="income" />
            <el-option label="支出" value="expense" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索描述" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTransactions">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="table-card">
      <el-table :data="transactions" v-loading="loading" stripe>
        <el-table-column prop="transaction_date" label="日期" width="120" />
        <el-table-column prop="transaction_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.transaction_type === 'income' ? 'success' : 'danger'">
              {{ row.transaction_type === 'income' ? '收入' : '支出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.transaction_type === 'income' ? 'income' : 'expense'">
              {{ row.transaction_type === 'income' ? '+' : '-' }}¥{{ row.amount.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="account_name" label="账户" width="120" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadTransactions"
        @size-change="loadTransactions"
      />
    </el-card>
    
    <el-dialog v-model="showAddDialog" title="记一笔" width="500px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-width="80px">
        <el-form-item label="类型" prop="transaction_type">
          <el-radio-group v-model="addForm.transaction_type">
            <el-radio-button value="expense">支出</el-radio-button>
            <el-radio-button value="income">收入</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="addForm.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="addForm.category_id" placeholder="选择分类" style="width: 100%">
            <el-option
              v-for="cat in filteredCategories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账户" prop="account_id">
          <el-select v-model="addForm.account_id" placeholder="选择账户" style="width: 100%">
            <el-option
              v-for="acc in accounts"
              :key="acc.id"
              :label="acc.name"
              :value="acc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" prop="transaction_date">
          <el-date-picker v-model="addForm.transaction_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="addForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="adding">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { transactionsApi, accountsApi, categoriesApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const adding = ref(false)
const showAddDialog = ref(false)
const addFormRef = ref()
const transactions = ref<any[]>([])
const accounts = ref<any[]>([])
const categories = ref<any[]>([])
const dateRange = ref<string[]>([])

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
  transaction_type: [{ required: true, message: '请选择类型' }],
  amount: [{ required: true, message: '请输入金额' }],
  category_id: [{ required: true, message: '请选择分类' }],
  account_id: [{ required: true, message: '请选择账户' }],
  transaction_date: [{ required: true, message: '请选择日期' }],
}

const filteredCategories = computed(() => {
  return categories.value.filter(c => c.category_type === addForm.transaction_type)
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

async function handleAdd() {
  try {
    await addFormRef.value?.validate()
    adding.value = true
    await transactionsApi.create(addForm)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadTransactions()
    addForm.amount = 0
    addForm.description = ''
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

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.income { color: #67c23a; }
.expense { color: #f56c6c; }

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
