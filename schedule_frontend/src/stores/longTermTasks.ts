import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  completeLongTermSubtask,
  createDailyTaskFromLongTermSubtask,
  createLongTermSubtask,
  createLongTermTask,
  deleteLongTermSubtask,
  deleteLongTermTask,
  fetchLongTermSubtasks,
  fetchLongTermTasks,
  uncompleteLongTermSubtask,
  updateLongTermSubtask,
  updateLongTermTask,
  updateLongTermTaskStatus,
} from '@/api/longTermTasks'
import type {
  LongTermSubtask,
  LongTermSubtaskCreateDailyTaskPayload,
  LongTermSubtaskPayload,
  LongTermTask,
  LongTermTaskPayload,
  LongTermTaskStatus,
} from '@/types/longTermTask'
import { notifySuccess } from '@/utils/message'

export const useLongTermTasksStore = defineStore('longTermTasks', () => {
  const tasks = ref<LongTermTask[]>([])
  const subtasks = ref<LongTermSubtask[]>([])
  const selectedTaskId = ref<number | null>(null)
  const loading = ref(false)
  const subtasksLoading = ref(false)
  const statusFilter = ref<LongTermTaskStatus | 'all'>('all')
  const keyword = ref('')

  const selectedTask = computed(() => tasks.value.find((item) => item.id === selectedTaskId.value) || null)
  const activeCount = computed(() => tasks.value.filter((item) => item.status === 'active').length)
  const completedCount = computed(() => tasks.value.filter((item) => item.status === 'completed').length)
  const averageProgress = computed(() => {
    if (!tasks.value.length) return 0
    return Math.round(tasks.value.reduce((sum, item) => sum + item.progress_percent, 0) / tasks.value.length)
  })

  async function loadTasks(): Promise<void> {
    loading.value = true
    try {
      tasks.value = await fetchLongTermTasks({
        status: statusFilter.value,
        keyword: keyword.value,
      })
      if (!selectedTaskId.value && tasks.value.length) {
        selectedTaskId.value = tasks.value[0].id
      }
      if (selectedTaskId.value && !tasks.value.some((item) => item.id === selectedTaskId.value)) {
        selectedTaskId.value = tasks.value[0]?.id ?? null
      }
    } finally {
      loading.value = false
    }
  }

  async function loadSubtasks(taskId = selectedTaskId.value): Promise<void> {
    if (!taskId) {
      subtasks.value = []
      return
    }

    subtasksLoading.value = true
    try {
      subtasks.value = await fetchLongTermSubtasks(taskId)
    } finally {
      subtasksLoading.value = false
    }
  }

  async function loadDashboard(): Promise<void> {
    await loadTasks()
    await loadSubtasks()
  }

  async function selectTask(taskId: number): Promise<void> {
    selectedTaskId.value = taskId
    await loadSubtasks(taskId)
  }

  async function saveTask(payload: LongTermTaskPayload, taskId?: number): Promise<LongTermTask> {
    const item = taskId ? await updateLongTermTask(taskId, payload) : await createLongTermTask(payload)
    selectedTaskId.value = item.id
    await loadDashboard()
    notifySuccess(taskId ? '长期任务已更新' : '长期任务已创建')
    return item
  }

  async function removeTask(taskId: number): Promise<void> {
    await deleteLongTermTask(taskId)
    if (selectedTaskId.value === taskId) {
      selectedTaskId.value = null
    }
    await loadDashboard()
    notifySuccess('长期任务已删除')
  }

  async function changeTaskStatus(taskId: number, status: LongTermTaskStatus): Promise<void> {
    await updateLongTermTaskStatus(taskId, status)
    await loadDashboard()
    notifySuccess('长期任务状态已更新')
  }

  async function saveSubtask(payload: LongTermSubtaskPayload, subtaskId?: number): Promise<LongTermSubtask> {
    if (!selectedTaskId.value && !subtaskId) {
      throw new Error('请先选择长期任务')
    }
    const item = subtaskId
      ? await updateLongTermSubtask(subtaskId, payload)
      : await createLongTermSubtask(selectedTaskId.value as number, payload)
    await loadDashboard()
    notifySuccess(subtaskId ? '子任务已更新' : '子任务已创建')
    return item
  }

  async function removeSubtask(subtaskId: number): Promise<void> {
    await deleteLongTermSubtask(subtaskId)
    await loadDashboard()
    notifySuccess('子任务已删除')
  }

  async function toggleSubtask(subtask: LongTermSubtask): Promise<void> {
    if (subtask.status === 'completed') {
      await uncompleteLongTermSubtask(subtask.id)
      notifySuccess('子任务已恢复为待办')
    } else {
      await completeLongTermSubtask(subtask.id)
      notifySuccess('子任务已完成')
    }
    await loadDashboard()
  }

  async function createDailyTask(subtaskId: number, payload?: LongTermSubtaskCreateDailyTaskPayload): Promise<void> {
    await createDailyTaskFromLongTermSubtask(subtaskId, payload)
    await loadDashboard()
    notifySuccess('已生成今日任务')
  }

  return {
    tasks,
    subtasks,
    selectedTaskId,
    selectedTask,
    loading,
    subtasksLoading,
    statusFilter,
    keyword,
    activeCount,
    completedCount,
    averageProgress,
    loadTasks,
    loadSubtasks,
    loadDashboard,
    selectTask,
    saveTask,
    removeTask,
    changeTaskStatus,
    saveSubtask,
    removeSubtask,
    toggleSubtask,
    createDailyTask,
  }
})
