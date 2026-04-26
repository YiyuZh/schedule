export type AiActionType = 'add_task' | 'add_event' | 'add_course' | 'schedule_task'
export type AiLogType = 'parse' | 'plan'
export type AiLogFilter = AiLogType | 'all'

export interface AiParseAction {
  action_type: AiActionType
  title?: string | null
  date?: string | null
  start_time?: string | null
  end_time?: string | null
  category?: string | null
  is_study?: boolean | null
  planned_duration_minutes?: number | null
  time_preference?: string | null
  task_id?: number | null
  weekday?: number | null
  week_list?: number[] | null
  location?: string | null
  teacher?: string | null
  term_name?: string | null
  term_start_date?: string | null
  term_end_date?: string | null
}

export interface AiParseResult {
  actions: AiParseAction[]
  raw_log_id: number
}

export interface AiParseApplyPayload {
  log_id: number
  actions: AiParseAction[]
}

export interface AiParseApplyResult {
  created_task_ids: number[]
  created_event_ids: number[]
  created_course_ids: number[]
}

export interface AiPlanItem {
  item_type: 'event' | 'task_schedule'
  task_id?: number | null
  title: string
  date: string
  start_time: string
  end_time: string
  category?: string | null
}

export interface AiPlanOption {
  name: string
  items: AiPlanItem[]
  reason: string
}

export interface AiPlanResult {
  plan_options: AiPlanOption[]
  raw_log_id: number
}

export interface AiPlanApplyResult {
  created_event_ids: number[]
  scheduled_task_ids: number[]
}

export interface AiApplyFeedback {
  kind: 'parse' | 'plan'
  message: string
  details: string[]
  raw_log_id: number
  created_at: string
}

export interface AiLog {
  id: number
  log_type: AiLogType
  provider?: string | null
  model_name?: string | null
  user_input: string
  context_json?: string | null
  ai_output_json?: string | null
  parsed_success: boolean
  applied_success: boolean
  error_message?: string | null
  created_at: string
}

export interface AiLogExportPayload {
  id: number
  log_type: AiLogType
  provider?: string | null
  model_name?: string | null
  user_input: string
  context_json: unknown
  ai_output_json: unknown
  parsed_success: boolean
  applied_success: boolean
  error_message?: string | null
  created_at: string
}

export interface AiConnectionState {
  ok: boolean
  message: string
  checked_at: string
}

export interface AiParseDraft {
  text: string
  date_context?: string
}

export interface AiPlanDraft {
  date: string
  user_input: string
  include_habits: boolean
  option_count: number
}

export type AiRetryDraft =
  | {
      kind: 'parse'
      payload: AiParseDraft
    }
  | {
      kind: 'plan'
      payload: AiPlanDraft
    }
