import { ref } from 'vue'
import { defineStore } from 'pinia'

import { deleteStudySession, fetchStudySessions } from '@/api/studySessions'
import {
  fetchStudyStatsByDay,
  fetchStudyStatsBySubject,
  fetchStudyStatsByTask,
  fetchStudyStatsOverview,
} from '@/api/studyStats'
import type {
  StudyCategoryStat,
  StudyDateRange,
  StudyDayStat,
  StudySession,
  StudyStatsOverview,
  StudyTaskStat,
} from '@/types/study'
import { notifySuccess } from '@/utils/message'

export const useStudyStore = defineStore('study', () => {
  const loading = ref(false)
  const sessions = ref<StudySession[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const overview = ref<StudyStatsOverview | null>(null)
  const categoryStats = ref<StudyCategoryStat[]>([])
  const taskStats = ref<StudyTaskStat[]>([])
  const dayStats = ref<StudyDayStat[]>([])
  const currentRange = ref<StudyDateRange>({})

  async function loadDashboard(range: StudyDateRange = currentRange.value): Promise<void> {
    currentRange.value = range
    loading.value = true
    try {
      const [sessionData, overviewData, categories, tasks, days] = await Promise.all([
        fetchStudySessions({
          ...range,
          page: page.value,
          page_size: pageSize.value,
        }),
        fetchStudyStatsOverview(range),
        fetchStudyStatsBySubject(range),
        fetchStudyStatsByTask(range),
        fetchStudyStatsByDay(range),
      ])

      sessions.value = sessionData.items
      total.value = sessionData.total
      page.value = sessionData.page
      pageSize.value = sessionData.page_size
      overview.value = overviewData
      categoryStats.value = categories
      taskStats.value = tasks
      dayStats.value = days
    } finally {
      loading.value = false
    }
  }

  async function changePage(nextPage: number): Promise<void> {
    page.value = nextPage
    await loadDashboard(currentRange.value)
  }

  async function removeSession(sessionId: number): Promise<void> {
    await deleteStudySession(sessionId)
    notifySuccess('学习记录已删除')
    await loadDashboard(currentRange.value)
  }

  return {
    loading,
    sessions,
    total,
    page,
    pageSize,
    overview,
    categoryStats,
    taskStats,
    dayStats,
    currentRange,
    loadDashboard,
    changePage,
    removeSession,
  }
})
