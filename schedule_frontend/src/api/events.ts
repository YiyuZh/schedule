import { del, get, patch, post, put } from '@/api/client'
import type { DeleteResult } from '@/types/common'
import type {
  ConflictCheckPayload,
  ConflictCheckResult,
  EventItem,
  EventListData,
  EventPayload,
  EventStatus,
  TimelineData,
} from '@/types/event'

export async function fetchEvents(query?: {
  date?: string
  start_date?: string
  end_date?: string
  category?: string
  status?: EventStatus
}): Promise<EventItem[]> {
  const data = await get<EventListData>('/api/events', { query })
  return data.items
}

export function fetchEvent(eventId: number): Promise<EventItem> {
  return get<EventItem>(`/api/events/${eventId}`)
}

export function createEvent(payload: EventPayload): Promise<EventItem> {
  return post<EventItem>('/api/events', { body: payload })
}

export function updateEvent(eventId: number, payload: EventPayload): Promise<EventItem> {
  return put<EventItem>(`/api/events/${eventId}`, { body: payload })
}

export function patchEvent(eventId: number, payload: Partial<EventPayload>): Promise<EventItem> {
  return patch<EventItem>(`/api/events/${eventId}`, { body: payload })
}

export function deleteEvent(eventId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/events/${eventId}`)
}

export function updateEventStatus(eventId: number, status: EventStatus): Promise<EventItem> {
  return post<EventItem>(`/api/events/${eventId}/status`, {
    body: { status },
  })
}

export function checkEventConflict(payload: ConflictCheckPayload): Promise<ConflictCheckResult> {
  return post<ConflictCheckResult>('/api/events/check-conflict', { body: payload })
}

export function fetchTimeline(date: string): Promise<TimelineData> {
  return get<TimelineData>('/api/events/timeline', { query: { date } })
}
