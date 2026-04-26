export type TimePreference = 'none' | 'morning' | 'afternoon' | 'evening' | 'night'

export interface TaskTemplate {
  id: number
  title: string
  category: string
  is_study: boolean
  default_duration_minutes: number
  default_start_time?: string | null
  default_end_time?: string | null
  time_preference: TimePreference
  priority: number
  is_enabled: boolean
  inherit_unfinished: boolean
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface TaskTemplatePayload {
  title: string
  category: string
  is_study: boolean
  default_duration_minutes: number
  default_start_time?: string | null
  default_end_time?: string | null
  time_preference: TimePreference
  priority: number
  is_enabled: boolean
  inherit_unfinished: boolean
  notes?: string | null
}

export interface TaskTemplateListData {
  items: TaskTemplate[]
}

export interface TaskTemplateRefreshResult {
  date: string
  created_count: number
  skipped_count: number
  task_ids: number[]
}
