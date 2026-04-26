import { del, get, post, put } from '@/api/client'
import type { DeleteResult } from '@/types/common'
import type { StudySession, StudySessionPayload, StudySessionsData } from '@/types/study'

export function fetchStudySessions(query?: {
  start_date?: string
  end_date?: string
  category?: string
  task_id?: number
  page?: number
  page_size?: number
}): Promise<StudySessionsData> {
  return get<StudySessionsData>('/api/study-sessions', { query })
}

export function fetchStudySession(sessionId: number): Promise<StudySession> {
  return get<StudySession>(`/api/study-sessions/${sessionId}`)
}

export function createStudySession(payload: StudySessionPayload): Promise<StudySession> {
  return post<StudySession>('/api/study-sessions', { body: payload })
}

export function updateStudySession(sessionId: number, payload: StudySessionPayload): Promise<StudySession> {
  return put<StudySession>(`/api/study-sessions/${sessionId}`, { body: payload })
}

export function deleteStudySession(sessionId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/study-sessions/${sessionId}`)
}

export function exportStudySessions(query?: {
  format?: 'json' | 'csv'
  start_date?: string
  end_date?: string
}): Promise<{ format: string; file_name: string; item_count: number; content: string }> {
  return get<{ format: string; file_name: string; item_count: number; content: string }>('/api/study-sessions/export', {
    query,
  })
}
