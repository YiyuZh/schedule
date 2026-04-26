import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { completeDailyTask, fetchDailyTask } from '@/api/dailyTasks'
import { fetchStudySession, updateStudySession } from '@/api/studySessions'
import { useTasksStore } from '@/stores/tasks'
import { useTimerStore } from '@/stores/timer'
import type { DailyTask } from '@/types/dailyTask'
import type { StudySession } from '@/types/study'

export function useTimerCompletion() {
  const router = useRouter()
  const timerStore = useTimerStore()
  const tasksStore = useTasksStore()

  const dialogVisible = ref(false)
  const session = ref<StudySession | null>(null)
  const task = ref<DailyTask | null>(null)

  const actualMinutes = computed(() => session.value?.duration_minutes ?? 0)
  const plannedMinutes = computed(() => task.value?.planned_duration_minutes ?? 0)

  async function stopAndOpenDialog(completeTaskAfterStop = false): Promise<void> {
    const activeTaskId = timerStore.currentTimer?.task_id
    if (!activeTaskId) {
      return
    }

    const result = await timerStore.stopTimer()
    if (!result.generated_session_id) {
      return
    }

    const [nextSession, nextTask] = await Promise.all([
      fetchStudySession(result.generated_session_id),
      fetchDailyTask(activeTaskId),
    ])

    if (completeTaskAfterStop) {
      await completeDailyTask(activeTaskId)
      await tasksStore.loadTodayDashboard(nextTask.task_date)
    }

    session.value = nextSession
    task.value = nextTask
    dialogVisible.value = true
  }

  async function saveNote(note: string): Promise<void> {
    if (!session.value) {
      dialogVisible.value = false
      return
    }

    session.value = await updateStudySession(session.value.id, {
      task_id: session.value.task_id ?? null,
      task_title_snapshot: session.value.task_title_snapshot,
      category_snapshot: session.value.category_snapshot,
      session_date: session.value.session_date,
      start_at: session.value.start_at,
      end_at: session.value.end_at,
      duration_minutes: session.value.duration_minutes,
      source: session.value.source,
      note,
    })
    dialogVisible.value = false
  }

  async function continueTiming(note: string): Promise<void> {
    const taskId = task.value?.id
    await saveNote(note)
    if (taskId) {
      await timerStore.startTimer(taskId)
    }
  }

  async function openNewTask(note: string): Promise<void> {
    await saveNote(note)
    await router.push('/today')
  }

  function closeDialog(): void {
    dialogVisible.value = false
  }

  return {
    dialogVisible,
    session,
    task,
    actualMinutes,
    plannedMinutes,
    stopAndOpenDialog,
    saveNote,
    continueTiming,
    openNewTask,
    closeDialog,
  }
}
