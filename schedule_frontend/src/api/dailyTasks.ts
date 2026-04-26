import { del, get, patch, post, put } from '@/api/client'
import type { DeleteResult } from '@/types/common'
import type {
  DailyTaskCompletePayload,
  DailyTask,
  DailyTaskInheritPayload,
  DailyTaskInheritResult,
  DailyTaskListData,
  DailyTaskPatchPayload,
  DailyTaskPayload,
  DailyTaskReorderPayload,
  DailyTaskSummary,
  TaskStatus,
} from '@/types/dailyTask'

export async function fetchDailyTasks(query: {
  date: string
  status?: TaskStatus
  category?: string
  is_study?: boolean
  source?: string
}): Promise<DailyTask[]> {
  const data = await get<DailyTaskListData>('/api/daily-tasks', { query })
  return data.items
}

export function fetchDailyTask(taskId: number): Promise<DailyTask> {
  return get<DailyTask>(`/api/daily-tasks/${taskId}`)
}

export function createDailyTask(payload: DailyTaskPayload): Promise<DailyTask> {
  return post<DailyTask>('/api/daily-tasks', { body: payload })
}

export function updateDailyTask(taskId: number, payload: DailyTaskPayload): Promise<DailyTask> {
  return put<DailyTask>(`/api/daily-tasks/${taskId}`, { body: payload })
}

export function patchDailyTask(taskId: number, payload: DailyTaskPatchPayload): Promise<DailyTask> {
  return patch<DailyTask>(`/api/daily-tasks/${taskId}`, { body: payload })
}

export function deleteDailyTask(taskId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/daily-tasks/${taskId}`)
}

export function updateDailyTaskStatus(taskId: number, status: TaskStatus): Promise<DailyTask> {
  return post<DailyTask>(`/api/daily-tasks/${taskId}/status`, {
    body: { status },
  })
}

export function completeDailyTask(taskId: number, payload?: DailyTaskCompletePayload): Promise<DailyTask> {
  return post<DailyTask>(`/api/daily-tasks/${taskId}/complete`, payload ? { body: payload } : undefined)
}

export function uncompleteDailyTask(taskId: number): Promise<DailyTask> {
  return post<DailyTask>(`/api/daily-tasks/${taskId}/uncomplete`)
}

export function reorderDailyTasks(payload: DailyTaskReorderPayload): Promise<{ date: string; updated_count: number }> {
  return post<{ date: string; updated_count: number }>('/api/daily-tasks/reorder', { body: payload })
}

export function inheritUnfinishedDailyTasks(payload: DailyTaskInheritPayload): Promise<DailyTaskInheritResult> {
  return post<DailyTaskInheritResult>('/api/daily-tasks/inherit-unfinished', { body: payload })
}

export function fetchDailyTaskSummary(date: string): Promise<DailyTaskSummary> {
  return get<DailyTaskSummary>('/api/daily-tasks/summary', { query: { date } })
}
