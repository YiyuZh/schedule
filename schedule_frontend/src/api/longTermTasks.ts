import { del, get, patch, post, put } from '@/api/client'
import type { DeleteResult } from '@/types/common'
import type {
  LongTermSubtask,
  LongTermSubtaskCreateDailyTaskPayload,
  LongTermSubtaskCreateDailyTaskResult,
  LongTermSubtaskPatchPayload,
  LongTermSubtaskPayload,
  LongTermTask,
  LongTermTaskPatchPayload,
  LongTermTaskPayload,
  LongTermTaskStatus,
} from '@/types/longTermTask'

export async function fetchLongTermTasks(query?: {
  status?: LongTermTaskStatus | 'all'
  keyword?: string
}): Promise<LongTermTask[]> {
  const data = await get<{ items: LongTermTask[] }>('/api/long-term-tasks', {
    query: {
      ...query,
      status: query?.status === 'all' ? undefined : query?.status,
    },
  })
  return data.items
}

export function fetchLongTermTask(taskId: number): Promise<LongTermTask> {
  return get<LongTermTask>(`/api/long-term-tasks/${taskId}`)
}

export function createLongTermTask(payload: LongTermTaskPayload): Promise<LongTermTask> {
  return post<LongTermTask>('/api/long-term-tasks', { body: payload })
}

export function updateLongTermTask(taskId: number, payload: LongTermTaskPayload): Promise<LongTermTask> {
  return put<LongTermTask>(`/api/long-term-tasks/${taskId}`, { body: payload })
}

export function patchLongTermTask(taskId: number, payload: LongTermTaskPatchPayload): Promise<LongTermTask> {
  return patch<LongTermTask>(`/api/long-term-tasks/${taskId}`, { body: payload })
}

export function deleteLongTermTask(taskId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/long-term-tasks/${taskId}`)
}

export function updateLongTermTaskStatus(taskId: number, status: LongTermTaskStatus): Promise<LongTermTask> {
  return post<LongTermTask>(`/api/long-term-tasks/${taskId}/status`, { body: { status } })
}

export async function fetchLongTermSubtasks(taskId: number): Promise<LongTermSubtask[]> {
  const data = await get<{ items: LongTermSubtask[] }>(`/api/long-term-tasks/${taskId}/subtasks`)
  return data.items
}

export function createLongTermSubtask(taskId: number, payload: LongTermSubtaskPayload): Promise<LongTermSubtask> {
  return post<LongTermSubtask>(`/api/long-term-tasks/${taskId}/subtasks`, { body: payload })
}

export function updateLongTermSubtask(subtaskId: number, payload: LongTermSubtaskPayload): Promise<LongTermSubtask> {
  return put<LongTermSubtask>(`/api/long-term-subtasks/${subtaskId}`, { body: payload })
}

export function patchLongTermSubtask(subtaskId: number, payload: LongTermSubtaskPatchPayload): Promise<LongTermSubtask> {
  return patch<LongTermSubtask>(`/api/long-term-subtasks/${subtaskId}`, { body: payload })
}

export function deleteLongTermSubtask(subtaskId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/long-term-subtasks/${subtaskId}`)
}

export function completeLongTermSubtask(subtaskId: number): Promise<LongTermSubtask> {
  return post<LongTermSubtask>(`/api/long-term-subtasks/${subtaskId}/complete`)
}

export function uncompleteLongTermSubtask(subtaskId: number): Promise<LongTermSubtask> {
  return post<LongTermSubtask>(`/api/long-term-subtasks/${subtaskId}/uncomplete`)
}

export function createDailyTaskFromLongTermSubtask(
  subtaskId: number,
  payload?: LongTermSubtaskCreateDailyTaskPayload,
): Promise<LongTermSubtaskCreateDailyTaskResult> {
  return post<LongTermSubtaskCreateDailyTaskResult>(
    `/api/long-term-subtasks/${subtaskId}/create-daily-task`,
    payload ? { body: payload } : undefined,
  )
}
