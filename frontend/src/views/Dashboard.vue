<template>
  <div class="dashboard">
    <h2>数据看板</h2>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本月收入</div>
              <div class="stat-value income">￥{{ stats.totalIncome.toFixed(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本月支出</div>
              <div class="stat-value expense">￥{{ stats.totalExpense.toFixed(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff">
              <el-icon size="24"><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本月结余</div>
              <div class="stat-value" :class="stats.netIncome >= 0 ? 'income' : 'expense'">
                ￥{{ stats.netIncome.toFixed(2) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon size="24"><List /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">交易笔数</div>
              <div class="stat-value">{{ stats.transactionCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts">
      <el-col :span="12">
        <el-card>
          <template #header>支出分类占比</template>
          <div ref="pieChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>最近7天收支趋势</template>
          <div ref="lineChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { transactionsApi } from '@/api'
import * as echarts from 'echarts'

const pieChart = ref<HTMLElement>()
const lineChart = ref<HTMLElement>()

const stats = reactive({
  totalIncome: 0,
  totalExpense: 0,
  netIncome: 0,
  transactionCount: 0,
})

onMounted(async () => {
  await loadStats()
  initCharts()
})

async function loadStats() {
  try {
    const today = new Date()
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
    
    const data: any = await transactionsApi.list({
      start_date: startOfMonth,
      page_size: 1000,
    })
    
    stats.transactionCount = data.total
    data.items.forEach((t: any) => {
      if (t.transaction_type === 'income') {
        stats.totalIncome += t.amount
      } else {
        stats.totalExpense += t.amount
      }
    })
    stats.netIncome = stats.totalIncome - stats.totalExpense
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

function initCharts() {
  // 饼图 - 支出分类占比
  if (pieChart.value) {
    const chart = echarts.init(pieChart.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: '60%',
        data: [
          { value: 1048, name: '餐饮' },
          { value: 735, name: '交通' },
          { value: 580, name: '购物' },
          { value: 484, name: '娱乐' },
          { value: 300, name: '其他' },
        ],
      }],
    })
  }
  
  // 折线图 - 最近7天趋势
  if (lineChart.value) {
    const chart = echarts.init(lineChart.value)
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['收入', '支出'] },
      xAxis: { type: 'category', data: days },
      yAxis: { type: 'value' },
      series: [
        { name: '收入', type: 'line', data: [0, 0, 5000, 0, 0, 0, 0] },
        { name: '支出', type: 'line', data: [120, 85, 200, 150, 300, 180, 95] },
      ],
    })
  }
}
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
  color: #303133;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-value.income { color: #67c23a; }
.stat-value.expense { color: #f56c6c; }

.charts {
  margin-top: 20px;
}
</style>
