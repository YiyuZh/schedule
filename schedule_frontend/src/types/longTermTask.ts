import type { DailyTask } from '@/types/dailyTask'

export type LongTermTaskStatus = 'active' | 'paused' | 'completed' | 'archived'
export type LongTermSubtaskStatus = 'pending' | 'in_progress' | 'completed' | 'skipped'

export interface LongTermTask {
  id: number
  title: string
  category: string
  description?: string | null
  start_date?: string | null
  due_date?: string | null
  status: LongTermTaskStatus
  priority: number
  progress_percent: number
  sort_order: number
  completed_at?: string | null
  created_at: string
  updated_at: string
  subtask_count: number
  completed_subtask_count: number
}

export interface LongTermTaskPayload {
  title: string
  category: string
  description?: string | null
  start_date?: string | null
  due_date?: string | null
  status: LongTermTaskStatus
  priority: number
  sort_order: number
}

export interface LongTermTaskPatchPayload extends Partial<LongTermTaskPayload> {}

export interface LongTermSubtask {
  id: number
  long_task_id: number
  title: string
  category: string
  is_study: boolean
  description?: string | null
  due_date?: string | null
  planned_duration_minutes: number
  status: LongTermSubtaskStatus
  priority: number
  sort_order: number
  linked_daily_task_id?: number | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

export interface LongTermSubtaskPayload {
  title: string
  category: string
  is_study: boolean
  description?: string | null
  due_date?: string | null
  planned_duration_minutes: number
  status: LongTermSubtaskStatus
  priority: number
  sort_order: number
}

export interface LongTermSubtaskPatchPayload extends Partial<LongTermSubtaskPayload> {}

export interface LongTermSubtaskCreateDailyTaskPayload {
  task_date?: string
}

export interface LongTermSubtaskCreateDailyTaskResult {
  subtask: LongTermSubtask
  daily_task: DailyTask
}
