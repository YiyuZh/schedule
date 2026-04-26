import { del, get, patch, post, put } from '@/api/client'
import type { DeleteResult } from '@/types/common'
import type {
  TaskTemplate,
  TaskTemplateListData,
  TaskTemplatePayload,
  TaskTemplateRefreshResult,
} from '@/types/taskTemplate'

export async function fetchTaskTemplates(query?: {
  enabled?: boolean
  category?: string
  is_study?: boolean
}): Promise<TaskTemplate[]> {
  const data = await get<TaskTemplateListData>('/api/task-templates', { query })
  return data.items
}

export function fetchTaskTemplate(templateId: number): Promise<TaskTemplate> {
  return get<TaskTemplate>(`/api/task-templates/${templateId}`)
}

export function createTaskTemplate(payload: TaskTemplatePayload): Promise<TaskTemplate> {
  return post<TaskTemplate>('/api/task-templates', { body: payload })
}

export function updateTaskTemplate(templateId: number, payload: TaskTemplatePayload): Promise<TaskTemplate> {
  return put<TaskTemplate>(`/api/task-templates/${templateId}`, { body: payload })
}

export function patchTaskTemplate(templateId: number, payload: Partial<TaskTemplatePayload>): Promise<TaskTemplate> {
  return patch<TaskTemplate>(`/api/task-templates/${templateId}`, { body: payload })
}

export function deleteTaskTemplate(templateId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/task-templates/${templateId}`)
}

export function toggleTaskTemplate(templateId: number, isEnabled: boolean): Promise<TaskTemplate> {
  return post<TaskTemplate>(`/api/task-templates/${templateId}/toggle`, {
    body: { is_enabled: isEnabled },
  })
}

export function refreshTodayTaskTemplates(date?: string): Promise<TaskTemplateRefreshResult> {
  return post<TaskTemplateRefreshResult>('/api/task-templates/refresh-today', {
    body: { date },
  })
}
