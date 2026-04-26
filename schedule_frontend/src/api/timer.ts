import { get, post } from '@/api/client'
import type { TimerOperationData, TimerState } from '@/types/timer'

export function fetchCurrentTimer(): Promise<TimerState> {
  return get<TimerState>('/api/timer/current')
}

export function startTimer(taskId: number): Promise<TimerOperationData> {
  return post<TimerOperationData>('/api/timer/start', { body: { task_id: taskId } })
}

export function pauseTimer(): Promise<TimerOperationData> {
  return post<TimerOperationData>('/api/timer/pause')
}

export function resumeTimer(): Promise<TimerOperationData> {
  return post<TimerOperationData>('/api/timer/resume')
}

export function stopTimer(note?: string): Promise<TimerOperationData> {
  return post<TimerOperationData>('/api/timer/stop', { body: { note } })
}

export function discardTimer(): Promise<TimerOperationData> {
  return post<TimerOperationData>('/api/timer/discard')
}

export function switchTimer(newTaskId: number, saveCurrentSession = true, note?: string): Promise<TimerOperationData> {
  return post<TimerOperationData>('/api/timer/switch', {
    body: {
      new_task_id: newTaskId,
      save_current_session: saveCurrentSession,
      note,
    },
  })
}
