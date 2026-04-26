import type { DailyTaskCompletePayload } from '@/types/dailyTask'

export const TASK_COMPLETION_QUICK_FILL_VALUES = [5, 10, 15, 30, 45, 60] as const

export function buildTaskCompletionDraft(plannedMinutes: number, isStudy: boolean): DailyTaskCompletePayload {
  const safeMinutes = Number.isFinite(plannedMinutes) ? Math.max(0, Math.trunc(plannedMinutes)) : 0
  return {
    actual_duration_minutes: safeMinutes,
    sync_study_session: isStudy,
  }
}
