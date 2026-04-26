export type TaskStatus = 'pending' | 'running' | 'completed' | 'skipped'
export type TaskSource = 'manual' | 'template' | 'ai' | 'import'

export interface DailyTask {
  id: number
  template_id?: number | null
  title: string
  category: string
  is_study: boolean
  task_date: string
  start_time?: string | null
  end_time?: string | null
  planned_duration_minutes: number
  actual_duration_minutes: number
  priority: number
  status: TaskStatus
  source: TaskSource
  sort_order: number
  notes?: string | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

export interface DailyTaskPayload {
  template_id?: number | null
  title: string
  category: string
  is_study: boolean
  task_date: string
  start_time?: string | null
  end_time?: string | null
  planned_duration_minutes: number
  priority: number
  status: TaskStatus
  source: TaskSource
  sort_order: number
  notes?: string | null
}

export interface DailyTaskPatchPayload extends Partial<DailyTaskPayload> {}

export interface DailyTaskCompletePayload {
  actual_duration_minutes?: number
  sync_study_session?: boolean
}

export interface DailyTaskListData {
  items: DailyTask[]
}

export interface DailyTaskSummary {
  date: string
  total_count: number
  completed_count: number
  skipped_count: number
  pending_count: number
  running_count: number
  completion_rate: number
  study_task_count: number
}

export interface DailyTaskReorderPayload {
  date: string
  items: Array<{ id: number; sort_order: number }>
}

export interface DailyTaskInheritPayload {
  from_date: string
  to_date: string
}

export interface DailyTaskInheritResult {
  from_date: string
  to_date: string
  created_count: number
  skipped_count: number
  task_ids: number[]
}
