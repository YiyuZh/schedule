export type TimerStatus = 'running' | 'paused'

export interface TimerState {
  has_active_timer: boolean
  task_id?: number | null
  task_title?: string | null
  started_at?: string | null
  paused_at?: string | null
  accumulated_seconds: number
  status?: TimerStatus | null
  created_at?: string | null
  updated_at?: string | null
}

export interface TimerOperationData {
  timer: TimerState
  generated_session_id?: number | null
  message?: string | null
}
