import type { PagedData } from '@/types/common'

export type StudySessionSource = 'timer' | 'manual' | 'import'

export interface StudySession {
  id: number
  task_id?: number | null
  task_title_snapshot: string
  category_snapshot: string
  session_date: string
  start_at: string
  end_at: string
  duration_minutes: number
  source: StudySessionSource
  note?: string | null
  created_at: string
}

export interface StudySessionPayload {
  task_id?: number | null
  task_title_snapshot?: string | null
  category_snapshot?: string | null
  session_date: string
  start_at: string
  end_at: string
  duration_minutes?: number | null
  source: StudySessionSource
  note?: string | null
}

export interface StudySessionsData extends PagedData<StudySession> {}

export interface StudyStatsOverview {
  today_minutes: number
  week_minutes: number
  month_minutes: number
  total_minutes: number
  query_total_minutes: number
}

export interface StudyCategoryStat {
  category: string
  duration_minutes: number
}

export interface StudyTaskStat {
  task_id?: number | null
  task_title: string
  duration_minutes: number
}

export interface StudyDayStat {
  session_date: string
  duration_minutes: number
}

export interface StudyDateRange {
  start_date?: string
  end_date?: string
}
