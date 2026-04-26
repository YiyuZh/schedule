export type EventStatus = 'scheduled' | 'completed' | 'cancelled'
export type EventSource = 'manual' | 'ai' | 'import'

export interface EventItem {
  id: number
  title: string
  category: string
  event_date: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  priority: number
  status: EventStatus
  source: EventSource
  linked_task_id?: number | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface EventPayload {
  title: string
  category: string
  event_date: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  priority: number
  status: EventStatus
  source: EventSource
  linked_task_id?: number | null
  notes?: string | null
}

export interface EventListData {
  items: EventItem[]
}

export interface ConflictItem {
  item_type: 'event' | 'task' | 'course'
  id?: number | null
  title: string
  date: string
  start_time?: string | null
  end_time?: string | null
  source: string
  detail?: string | null
}

export interface ConflictCheckPayload {
  event_date: string
  start_time: string
  end_time: string
  exclude_event_id?: number | null
}

export interface ConflictCheckResult {
  has_conflict: boolean
  conflict_items: ConflictItem[]
}

export interface TimelineItem {
  item_type: 'event' | 'task' | 'course'
  id?: number | null
  title: string
  date: string
  start_time: string
  end_time: string
  source: string
  category?: string | null
  detail?: string | null
}

export interface TimelineData {
  date: string
  items: TimelineItem[]
}
