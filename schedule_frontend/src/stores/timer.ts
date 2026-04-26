import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  discardTimer as discardTimerRequest,
  fetchCurrentTimer,
  pauseTimer as pauseTimerRequest,
  resumeTimer as resumeTimerRequest,
  startTimer as startTimerRequest,
  stopTimer as stopTimerRequest,
  switchTimer as switchTimerRequest,
} from '@/api/timer'
import { useAppStore } from '@/stores/app'
import { useTasksStore } from '@/stores/tasks'
import type { TimerOperationData, TimerState } from '@/types/timer'
import { notifySuccess } from '@/utils/message'

export const useTimerStore = defineStore('timer', () => {
  const currentTimer = ref<TimerState | null>(null)
  const loading = ref(false)

  const hasActiveTimer = computed(() => Boolean(currentTimer.value?.has_active_timer))

  async function refreshRelatedData(): Promise<void> {
    const appStore = useAppStore()
    const tasksStore = useTasksStore()
    await Promise.all([loadCurrentTimer(), tasksStore.loadTodayDashboard(appStore.currentDate)])
  }

  async function loadCurrentTimer(): Promise<void> {
    currentTimer.value = await fetchCurrentTimer()
  }

  async function runOperation(executor: () => Promise<TimerOperationData>, successText: string): Promise<TimerOperationData> {
    loading.value = true
    let result: TimerOperationData

    try {
      result = await executor()
      currentTimer.value = result.timer
      notifySuccess(result.message || successText)
    } finally {
      loading.value = false
    }

    await refreshRelatedData()
    return result
  }

  async function startTimer(taskId: number): Promise<TimerOperationData> {
    return runOperation(() => startTimerRequest(taskId), '计时已开始')
  }

  async function pauseTimer(): Promise<TimerOperationData> {
    return runOperation(() => pauseTimerRequest(), '计时已暂停')
  }

  async function resumeTimer(): Promise<TimerOperationData> {
    return runOperation(() => resumeTimerRequest(), '计时已恢复')
  }

  async function stopTimer(note?: string): Promise<TimerOperationData> {
    return runOperation(() => stopTimerRequest(note), '计时已结束')
  }

  async function discardTimer(): Promise<TimerOperationData> {
    return runOperation(() => discardTimerRequest(), '计时已放弃')
  }

  async function switchTimer(taskId: number, saveCurrentSession = true, note?: string): Promise<TimerOperationData> {
    return runOperation(() => switchTimerRequest(taskId, saveCurrentSession, note), '计时任务已切换')
  }

  return {
    currentTimer,
    loading,
    hasActiveTimer,
    loadCurrentTimer,
    startTimer,
    pauseTimer,
    resumeTimer,
    stopTimer,
    discardTimer,
    switchTimer,
  }
})
