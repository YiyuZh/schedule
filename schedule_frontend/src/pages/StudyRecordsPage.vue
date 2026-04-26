<template>
  <section class="page-grid">
    <PageHeader
      title="学习记录"
      description="查看学习统计总览、科目时长、每日趋势与详细记录，支持 JSON / CSV 导出。"
      eyebrow="Study"
    >
      <template #actions>
        <el-radio-group v-model="selectedShortcut" @change="handleShortcutGroupChange">
          <el-radio-button label="today">今日</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="year">全年</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
        <el-button class="topbar-button" @click="loadData(true)">刷新</el-button>
        <el-button class="topbar-button" @click="handleExport('csv')">导出 CSV</el-button>
        <el-button type="primary" class="topbar-button" @click="handleExport('json')">导出 JSON</el-button>
      </template>
    </PageHeader>

    <StudyStatsCards :overview="studyStore.overview" />

    <StudyChartsPanel
      :category-stats="studyStore.categoryStats"
      :day-stats="studyStore.dayStats"
      :loading="studyStore.loading"
    />

    <el-card class="panel-card">
      <template #header>
        <strong>学习科目时长排行</strong>
      </template>

      <EmptyState
        v-if="!studyStore.categoryStats.length"
        title="暂无科目数据"
        description="把学习任务的分类填写为数学、Python 或英语后，这里会按科目汇总学习时长。"
        icon="科目"
      />
      <div v-else class="subject-ranking-list">
        <div v-for="(item, index) in subjectRanking" :key="item.category" class="subject-ranking-item">
          <span :class="['subject-rank', index < 3 ? 'is-top' : '']">
            {{ index < 3 ? `TOP ${index + 1}` : index + 1 }}
          </span>
          <div class="subject-name-cell">
            <strong>{{ item.category || '未分类' }}</strong>
            <span class="muted-text">学习科目累计</span>
          </div>
          <el-progress :percentage="item.percent" :stroke-width="8" />
          <span>{{ formatDurationMinutes(item.duration_minutes) }}</span>
        </div>
      </div>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <strong>任务维度统计</strong>
      </template>

      <el-table :data="studyStore.taskStats" v-loading="studyStore.loading" border>
        <el-table-column prop="task_title" label="任务" min-width="220" />
        <el-table-column label="时长" min-width="140">
          <template #default="{ row }">
            {{ formatDurationMinutes(row.duration_minutes) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <StudySessionTable
      :sessions="studyStore.sessions"
      :total="studyStore.total"
      :page="studyStore.page"
      :page-size="studyStore.pageSize"
      :loading="studyStore.loading"
      @page-change="handlePageChange"
      @remove="handleRemoveSession"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { exportStudySessions } from '@/api/studySessions'
import PageHeader from '@/components/common/PageHeader.vue'
import StudyChartsPanel from '@/components/study/StudyChartsPanel.vue'
import StudySessionTable from '@/components/study/StudySessionTable.vue'
import StudyStatsCards from '@/components/study/StudyStatsCards.vue'
import { useStudyStore } from '@/stores/study'
import { buildRangeByShortcut, toDateRangePayload } from '@/utils/date'
import { formatDurationMinutes } from '@/utils/format'
import { confirmAction, notifySuccess } from '@/utils/message'
import { listenPageExport, listenPageRefresh } from '@/utils/pageEvents'

const studyStore = useStudyStore()
const dateRange = ref<string[]>([])
const selectedShortcut = ref<'today' | 'week' | 'month' | 'year'>('week')
let removeRefreshListener: (() => void) | null = null
let removeExportListener: (() => void) | null = null

const subjectRanking = computed(() => {
  const maxMinutes = Math.max(...studyStore.categoryStats.map((item) => item.duration_minutes), 0)
  return [...studyStore.categoryStats]
    .sort((left, right) => right.duration_minutes - left.duration_minutes)
    .map((item) => ({
      ...item,
      percent: maxMinutes > 0 ? Math.round((item.duration_minutes / maxMinutes) * 100) : 0,
    }))
})

function syncRangeByShortcut(shortcut: 'today' | 'week' | 'month' | 'year'): void {
  const range = buildRangeByShortcut(shortcut)
  dateRange.value = [range.start_date, range.end_date]
}

async function loadData(resetPage = false): Promise<void> {
  if (resetPage) {
    studyStore.page = 1
  }
  await studyStore.loadDashboard(toDateRangePayload(dateRange.value))
}

async function handleShortcutChange(shortcut: 'today' | 'week' | 'month' | 'year'): Promise<void> {
  syncRangeByShortcut(shortcut)
  await loadData(true)
}

function handleShortcutGroupChange(value: string | number | boolean | undefined): Promise<void> {
  return handleShortcutChange((value as 'today' | 'week' | 'month' | 'year') || 'week')
}

async function handlePageChange(page: number): Promise<void> {
  await studyStore.changePage(page)
}

async function handleRemoveSession(sessionId: number): Promise<void> {
  const confirmed = await confirmAction('确定删除这条学习记录吗？')
  if (!confirmed) {
    return
  }

  await studyStore.removeSession(sessionId)
}

async function handleExport(format: 'json' | 'csv'): Promise<void> {
  const result = await exportStudySessions({
    format,
    ...toDateRangePayload(dateRange.value),
  })

  const mimeType = format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json;charset=utf-8'
  const blob = new Blob([result.content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = result.file_name
  link.click()
  window.URL.revokeObjectURL(url)
  notifySuccess(`已导出 ${result.item_count} 条学习记录`)
}

onMounted(async () => {
  syncRangeByShortcut(selectedShortcut.value)
  await loadData(true)
  removeRefreshListener = listenPageRefresh(() => loadData(false))
  removeExportListener = listenPageExport(() => handleExport('json'))
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
  removeExportListener?.()
})
</script>

<style scoped>
.subject-ranking-list {
  display: grid;
  gap: 12px;
}

.subject-ranking-item {
  display: grid;
  grid-template-columns: 72px minmax(120px, 180px) minmax(180px, 1fr) 120px;
  gap: 14px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  background: #f8fbfd;
}

.subject-rank {
  display: grid;
  place-items: center;
  width: 56px;
  height: 28px;
  border-radius: 999px;
  color: var(--app-text-muted);
  background: #edf2f7;
  font-weight: 700;
  font-size: 12px;
}

.subject-rank.is-top {
  color: #fff;
  background: var(--app-primary);
}

.subject-name-cell {
  display: grid;
  gap: 2px;
}

@media (max-width: 900px) {
  .subject-ranking-item {
    grid-template-columns: 40px minmax(0, 1fr);
  }
}
</style>
