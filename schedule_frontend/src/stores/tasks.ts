import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  completeDailyTask,
  createDailyTask,
  deleteDailyTask,
  fetchDailyTaskSummary,
  fetchDailyTasks,
  patchDailyTask,
  uncompleteDailyTask,
  updateDailyTask,
} from '@/api/dailyTasks'
import {
  createTaskTemplate,
  deleteTaskTemplate,
  fetchTaskTemplates,
  refreshTodayTaskTemplates,
  toggleTaskTemplate,
  updateTaskTemplate,
} from '@/api/taskTemplates'
import type { DailyTask, DailyTaskPatchPayload, DailyTaskPayload, DailyTaskSummary } from '@/types/dailyTask'
import type { DailyTaskCompletePayload } from '@/types/dailyTask'
import type { TaskTemplate, TaskTemplatePayload } from '@/types/taskTemplate'
import { notifySuccess } from '@/utils/message'

export const useTasksStore = defineStore('tasks', () => {
  const todayTasks = ref<DailyTask[]>([])
  const todaySummary = ref<DailyTaskSummary | null>(null)
  const templates = ref<TaskTemplate[]>([])
  const tasksLoading = ref(false)
  const templatesLoading = ref(false)

  const studyTasks = computed(() => todayTasks.value.filter((task) => task.is_study))

  async function loadTodayTasks(date: string): Promise<void> {
    tasksLoading.value = true
    try {
      todayTasks.value = await fetchDailyTasks({ date })
    } finally {
      tasksLoading.value = false
    }
  }

  async function loadTodaySummary(date: string): Promise<void> {
    todaySummary.value = await fetchDailyTaskSummary(date)
  }

  async function loadTodayDashboard(date: string): Promise<void> {
    await Promise.all([loadTodayTasks(date), loadTodaySummary(date)])
  }

  async function saveTask(payload: DailyTaskPayload, taskId?: number): Promise<DailyTask> {
    const savedTask = taskId ? await updateDailyTask(taskId, payload) : await createDailyTask(payload)
    await loadTodayDashboard(savedTask.task_date)
    notifySuccess(taskId ? '任务已更新' : '任务已创建')
    return savedTask
  }

  async function patchTask(taskId: number, payload: DailyTaskPatchPayload, date: string): Promise<DailyTask> {
    const task = await patchDailyTask(taskId, payload)
    await loadTodayDashboard(date)
    notifySuccess('任务已更新')
    return task
  }

  async function removeTask(task: DailyTask): Promise<void> {
    await deleteDailyTask(task.id)
    await loadTodayDashboard(task.task_date)
    notifySuccess('任务已删除')
  }

  async function completeTask(task: DailyTask, payload?: DailyTaskCompletePayload): Promise<void> {
    await completeDailyTask(task.id, payload)
    await loadTodayDashboard(task.task_date)
    notifySuccess('任务已完成')
  }

  async function uncompleteTask(task: DailyTask): Promise<void> {
    await uncompleteDailyTask(task.id)
    await loadTodayDashboard(task.task_date)
    notifySuccess('任务已恢复为待办')
  }

  async function toggleTask(task: DailyTask, payload?: DailyTaskCompletePayload): Promise<void> {
    if (task.status === 'completed') {
      await uncompleteTask(task)
    } else {
      await completeTask(task, payload)
    }
  }

  async function loadTemplates(): Promise<void> {
    templatesLoading.value = true
    try {
      templates.value = await fetchTaskTemplates()
    } finally {
      templatesLoading.value = false
    }
  }

  async function saveTemplate(payload: TaskTemplatePayload, templateId?: number): Promise<TaskTemplate> {
    const template = templateId
      ? await updateTaskTemplate(templateId, payload)
      : await createTaskTemplate(payload)
    await loadTemplates()
    notifySuccess(templateId ? '模板已更新' : '模板已创建')
    return template
  }

  async function removeTemplate(templateId: number): Promise<void> {
    await deleteTaskTemplate(templateId)
    await loadTemplates()
    notifySuccess('模板已删除')
  }

  async function switchTemplateEnabled(template: TaskTemplate): Promise<void> {
    await toggleTaskTemplate(template.id, !template.is_enabled)
    await loadTemplates()
    notifySuccess(template.is_enabled ? '模板已停用' : '模板已启用')
  }

  async function refreshTodayTemplates(date: string): Promise<void> {
    await refreshTodayTaskTemplates(date)
    await loadTodayDashboard(date)
    notifySuccess('今日模板任务已刷新')
  }

  return {
    todayTasks,
    todaySummary,
    templates,
    tasksLoading,
    templatesLoading,
    studyTasks,
    loadTodayTasks,
    loadTodaySummary,
    loadTodayDashboard,
    saveTask,
    patchTask,
    removeTask,
    completeTask,
    uncompleteTask,
    toggleTask,
    loadTemplates,
    saveTemplate,
    removeTemplate,
    switchTemplateEnabled,
    refreshTodayTemplates,
  }
})
