import { get } from '@/api/client'
import type { StudyCategoryStat, StudyDayStat, StudyStatsOverview, StudyTaskStat } from '@/types/study'

export function fetchStudyStatsOverview(query?: { start_date?: string; end_date?: string }): Promise<StudyStatsOverview> {
  return get<StudyStatsOverview>('/api/study-stats/overview', { query })
}

export async function fetchStudyStatsByCategory(query?: {
  start_date?: string
  end_date?: string
}): Promise<StudyCategoryStat[]> {
  const data = await get<{ items: StudyCategoryStat[] }>('/api/study-stats/by-category', { query })
  return data.items
}

export async function fetchStudyStatsBySubject(query?: {
  start_date?: string
  end_date?: string
}): Promise<StudyCategoryStat[]> {
  const data = await get<{ items: StudyCategoryStat[] }>('/api/study-stats/by-subject', { query })
  return data.items
}

export async function fetchStudyStatsByTask(query?: { start_date?: string; end_date?: string }): Promise<StudyTaskStat[]> {
  const data = await get<{ items: StudyTaskStat[] }>('/api/study-stats/by-task', { query })
  return data.items
}

export async function fetchStudyStatsByDay(query?: { start_date?: string; end_date?: string }): Promise<StudyDayStat[]> {
  const data = await get<{ items: StudyDayStat[] }>('/api/study-stats/by-day', { query })
  return data.items
}
