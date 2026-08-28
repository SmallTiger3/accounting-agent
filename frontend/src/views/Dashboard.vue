<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <div class="page-title">数据看板</div>
        <div class="page-subtitle">{{ monthLabel }} 收支概览</div>
      </div>
      <el-button type="primary" round @click="$router.push('/transactions')">
        <el-icon><Plus /></el-icon>
        记一笔
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="app-card stat-card">
        <div class="stat-icon income-bg"><el-icon :size="20"><TrendCharts /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本月收入</div>
          <div class="stat-value money income">{{ formatMoney(stats.totalIncome) }}</div>
        </div>
      </div>
      <div class="app-card stat-card">
        <div class="stat-icon expense-bg"><el-icon :size="20"><TrendCharts /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本月支出</div>
          <div class="stat-value money expense">{{ formatMoney(stats.totalExpense) }}</div>
        </div>
      </div>
      <div class="app-card stat-card">
        <div class="stat-icon primary-bg"><el-icon :size="20"><Wallet /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本月结余</div>
          <div class="stat-value money" :class="stats.netIncome >= 0 ? 'income' : 'expense'">
            {{ formatMoney(stats.netIncome) }}
          </div>
        </div>
      </div>
      <div class="app-card stat-card">
        <div class="stat-icon warning-bg"><el-icon :size="20"><List /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">交易笔数</div>
          <div class="stat-value">{{ stats.transactionCount }}</div>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="charts-grid">
      <div class="app-card chart-card">
        <div class="chart-header">
          <div class="chart-title">支出分类占比</div>
          <span class="chart-sub">本月</span>
        </div>
        <div v-if="pieData.length" ref="pieEl" class="chart-body"></div>
        <div v-else class="chart-empty">
          <el-icon :size="36"><PieChart /></el-icon>
          <p>本月还没有支出记录</p>
        </div>
      </div>

      <div class="app-card chart-card">
        <div class="chart-header">
          <div class="chart-title">近 7 天收支趋势</div>
          <span class="chart-sub">收入 / 支出</span>
        </div>
        <div v-if="hasTrendData" ref="lineEl" class="chart-body"></div>
        <div v-else class="chart-empty">
          <el-icon :size="36"><TrendCharts /></el-icon>
          <p>近 7 天还没有收支数据</p>
        </div>
      </div>
    </div>

    <!-- 最近交易 -->
    <div class="app-card recent-card">
      <div class="recent-header">
        <div class="chart-title">最近交易</div>
        <router-link to="/transactions" class="view-all">查看全部</router-link>
      </div>
      <div v-if="recentTransactions.length" class="recent-list">
        <div v-for="txn in recentTransactions" :key="txn.id" class="recent-item">
          <div class="txn-icon" :class="txn.transaction_type">
            <el-icon :size="16">
              <component :is="txn.transaction_type === 'income' ? 'Top' : 'Bottom'" />
            </el-icon>
          </div>
          <div class="txn-main">
            <div class="txn-desc">{{ txn.description || txn.category_name || '未分类' }}</div>
            <div class="txn-meta">
              {{ txn.category_name }} · {{ txn.account_name }} · {{ txn.transaction_date }}
            </div>
          </div>
          <div class="money txn-amount" :class="txn.transaction_type">
            {{ formatSignedMoney(txn.amount, txn.transaction_type) }}
          </div>
        </div>
      </div>
      <div v-else class="recent-empty">
        <el-icon :size="32"><Document /></el-icon>
        <p>还没有交易记录，试试说「今天午餐花了 35 元」</p>
        <router-link to="/chat" class="go-chat">去 AI 对话记账 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { transactionsApi } from '@/api'
import * as echarts from 'echarts/core'
import { PieChart as EChartsPieChart, LineChart as EChartsLineChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import dayjs from 'dayjs'
import { formatMoney, formatSignedMoney } from '@/utils/format'

echarts.use([EChartsPieChart, EChartsLineChart, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const pieEl = ref<HTMLElement>()
const lineEl = ref<HTMLElement>()
let pieChart: echarts.ECharts | null = null
let lineChart: echarts.ECharts | null = null

const stats = reactive({
  totalIncome: 0,
  totalExpense: 0,
  netIncome: 0,
  transactionCount: 0,
})

const pieData = ref<{ name: string; value: number }[]>([])
const trendData = ref<{ days: string[]; income: number[]; expense: number[] }>({
  days: [],
  income: [],
  expense: [],
})
const hasTrendData = ref(false)
const recentTransactions = ref<any[]>([])

const monthLabel = dayjs().format('YYYY年M月')
const CATEGORY_COLORS = [
  '#10b981', '#f59e0b', '#6366f1', '#ef4444', '#06b6d4',
  '#8b5cf6', '#ec4899', '#84cc16', '#f97316', '#64748b',
]

onMounted(async () => {
  await loadData()
  await nextTick()
  initCharts()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  lineChart?.dispose()
})

async function loadData() {
  try {
    const monthStart = dayjs().startOf('month').format('YYYY-MM-DD')
    const weekStart = dayjs().subtract(6, 'day').startOf('day').format('YYYY-MM-DD')
    const today = dayjs().format('YYYY-MM-DD')

    const [monthData, weekData] = await Promise.all([
      transactionsApi.list({ start_date: monthStart, page_size: 10000 }),
      transactionsApi.list({ start_date: weekStart, end_date: today, page_size: 10000 }),
    ])

    const items = monthData.items || []
    stats.transactionCount = monthData.total || items.length

    const catMap = new Map<string, number>()
    items.forEach((t: any) => {
      if (t.transaction_type === 'income') stats.totalIncome += t.amount
      else {
        stats.totalExpense += t.amount
        const name = t.category_name || '未分类'
        catMap.set(name, (catMap.get(name) || 0) + t.amount)
      }
    })
    stats.netIncome = stats.totalIncome - stats.totalExpense

    pieData.value = [...catMap.entries()]
      .map(([name, value]) => ({ name, value: Math.round(value * 100) / 100 }))
      .sort((a, b) => b.value - a.value)

    trendData.value = buildTrend(weekData.items || [])
    hasTrendData.value =
      trendData.value.income.some((v) => v > 0) || trendData.value.expense.some((v) => v > 0)

    recentTransactions.value = [...items]
      .sort((a: any, b: any) => b.transaction_date.localeCompare(a.transaction_date))
      .slice(0, 6)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

function buildTrend(items: any[]) {
  const days: string[] = []
  const income: number[] = []
  const expense: number[] = []
  const dateMap = new Map<string, { income: number; expense: number }>()

  items.forEach((t: any) => {
    const entry = dateMap.get(t.transaction_date) || { income: 0, expense: 0 }
    if (t.transaction_type === 'income') entry.income += t.amount
    else entry.expense += t.amount
    dateMap.set(t.transaction_date, entry)
  })

  for (let i = 6; i >= 0; i--) {
    const d = dayjs().subtract(i, 'day')
    days.push(d.format('MM-DD'))
    const entry = dateMap.get(d.format('YYYY-MM-DD')) || { income: 0, expense: 0 }
    income.push(Math.round(entry.income * 100) / 100)
    expense.push(Math.round(entry.expense * 100) / 100)
  }

  return { days, income, expense }
}

function initCharts() {
  if (pieEl.value && pieData.value.length) {
    pieChart = echarts.init(pieEl.value)
    pieChart.setOption({
      color: CATEGORY_COLORS,
      tooltip: {
        trigger: 'item',
        formatter: '{b}<br/>¥{c} ({d}%)',
        backgroundColor: '#111827',
        borderWidth: 0,
        textStyle: { color: '#fff', fontSize: 12 },
        padding: [8, 12],
      },
      legend: {
        orient: 'vertical',
        right: 8,
        top: 'center',
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8,
        itemGap: 12,
        textStyle: { color: '#4b5563', fontSize: 12 },
      },
      series: [
        {
          name: '支出',
          type: 'pie',
          radius: ['48%', '72%'],
          center: ['36%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 600, formatter: '{b}\n¥{c}' },
          },
          data: pieData.value,
        },
      ],
    })
  }

  if (lineEl.value && hasTrendData.value) {
    const { days, income, expense } = trendData.value
    lineChart = echarts.init(lineEl.value)
    lineChart.setOption({
      color: ['#10b981', '#ef4444'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#111827',
        borderWidth: 0,
        textStyle: { color: '#fff', fontSize: 12 },
        axisPointer: { type: 'line', lineStyle: { color: '#d1d5db' } },
        valueFormatter: (v: number) => '¥' + Number(v || 0).toLocaleString(),
      },
      legend: {
        right: 8,
        top: 0,
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8,
        textStyle: { color: '#4b5563', fontSize: 12 },
      },
      grid: { left: 8, right: 8, top: 36, bottom: 8, containLabel: true },
      xAxis: {
        type: 'category',
        data: days,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisTick: { show: false },
        axisLabel: { color: '#9ca3af', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#f3f4f6' } },
        axisLabel: { color: '#9ca3af', fontSize: 11 },
      },
      series: [
        {
          name: '收入',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2.5 },
          data: income,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(16,185,129,0.22)' },
              { offset: 1, color: 'rgba(16,185,129,0.02)' },
            ]),
          },
        },
        {
          name: '支出',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2.5 },
          data: expense,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(239,68,68,0.18)' },
              { offset: 1, color: 'rgba(239,68,68,0.02)' },
            ]),
          },
        },
      ],
    })
  }
}

function handleResize() {
  pieChart?.resize()
  lineChart?.resize()
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 16px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.income-bg { background: var(--app-income-soft); color: var(--app-income); }
.expense-bg { background: var(--app-expense-soft); color: var(--app-expense); }
.primary-bg { background: var(--app-primary-soft); color: var(--app-primary-strong); }
.warning-bg { background: var(--app-warning-soft); color: var(--app-warning); }

.stat-info {
  min-width: 0;
}

.stat-label {
  font-size: 12px;
  color: var(--app-text-3);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 19px;
  font-weight: 700;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  padding: 18px 16px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.chart-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
}

.chart-sub {
  font-size: 12px;
  color: var(--app-text-3);
}

.chart-body {
  height: 260px;
}

.chart-empty {
  height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--app-text-3);
  font-size: 13px;
}

.recent-card {
  padding: 18px 16px;
}

.recent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.view-all {
  font-size: 13px;
  color: var(--app-primary-strong);
  text-decoration: none;
  font-weight: 500;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--app-border);
}

.recent-item:last-child {
  border-bottom: none;
}

.txn-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
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
  font-weight: 500;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.txn-meta {
  margin-top: 3px;
  font-size: 12px;
  color: var(--app-text-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.txn-amount {
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
}

.recent-empty {
  padding: 28px 0 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--app-text-3);
  font-size: 13px;
  text-align: center;
}

.go-chat {
  margin-top: 4px;
  color: var(--app-primary-strong);
  font-weight: 600;
  text-decoration: none;
}

@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  .charts-grid {
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .stat-card {
    padding: 20px;
  }

  .stat-value {
    font-size: 22px;
  }
}
</style>
