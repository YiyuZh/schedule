import { ref } from 'vue'
import { defineStore } from 'pinia'

import { applyAiPlan, createAiPlan } from '@/api/ai'
import { fetchCoursesDayView } from '@/api/courses'
import { checkEventConflict, createEvent, deleteEvent, fetchEvents, fetchTimeline, updateEvent } from '@/api/events'
import type { AiPlanResult } from '@/types/ai'
import type { CourseOccurrence } from '@/types/course'
import type { ConflictCheckPayload, ConflictCheckResult, EventItem, EventPayload, TimelineItem } from '@/types/event'
import { notifySuccess } from '@/utils/message'

export const useScheduleStore = defineStore('schedule', () => {
  const loading = ref(false)
  const selectedDate = ref('')
  const events = ref<EventItem[]>([])
  const timelineItems = ref<TimelineItem[]>([])
  const courseOccurrences = ref<CourseOccurrence[]>([])
  const conflictResult = ref<ConflictCheckResult | null>(null)
  const aiPlan = ref<AiPlanResult | null>(null)

  async function loadSchedule(date: string): Promise<void> {
    selectedDate.value = date
    loading.value = true

    try {
      const [timelineData, eventItems, courseData] = await Promise.all([
        fetchTimeline(date),
        fetchEvents({ date }),
        fetchCoursesDayView(date),
      ])

      timelineItems.value = timelineData.items
      events.value = eventItems
      courseOccurrences.value = courseData.items
      conflictResult.value = null
    } finally {
      loading.value = false
    }
  }

  async function saveEvent(payload: EventPayload, eventId?: number): Promise<EventItem> {
    const event = eventId ? await updateEvent(eventId, payload) : await createEvent(payload)
    await loadSchedule(payload.event_date)
    notifySuccess(eventId ? '事件已更新' : '事件已创建')
    return event
  }

  async function removeEvent(event: EventItem): Promise<void> {
    await deleteEvent(event.id)
    await loadSchedule(event.event_date)
    notifySuccess('事件已删除')
  }

  async function detectConflict(payload: ConflictCheckPayload): Promise<ConflictCheckResult> {
    const result = await checkEventConflict(payload)
    conflictResult.value = result
    return result
  }

  async function createPlan(date: string, userInput: string, includeHabits = true, optionCount = 3): Promise<void> {
    aiPlan.value = await createAiPlan({
      date,
      user_input: userInput,
      include_habits: includeHabits,
      option_count: optionCount,
    })
  }

  async function applyPlan(selectedOptionIndex: number): Promise<void> {
    if (!aiPlan.value) {
      return
    }

    await applyAiPlan({
      log_id: aiPlan.value.raw_log_id,
      selected_option_index: selectedOptionIndex,
    })
    notifySuccess('AI 规划已应用')
    await loadSchedule(selectedDate.value)
  }

  return {
    loading,
    selectedDate,
    events,
    timelineItems,
    courseOccurrences,
    conflictResult,
    aiPlan,
    loadSchedule,
    saveEvent,
    removeEvent,
    detectConflict,
    createPlan,
    applyPlan,
  }
})
