import type { LongTermSubtaskStatus, LongTermTaskStatus } from '@/types/longTermTask'

export function formatLongTermTaskStatus(status: LongTermTaskStatus): string {
  return {
    active: '进行中',
    paused: '已暂停',
    completed: '已完成',
    archived: '已归档',
  }[status]
}

export function formatLongTermSubtaskStatus(status: LongTermSubtaskStatus): string {
  return {
    pending: '待办',
    in_progress: '进行中',
    completed: '已完成',
    skipped: '已跳过',
  }[status]
}

export function getLongTermStatusTone(status: LongTermTaskStatus): 'primary' | 'success' | 'warning' | 'danger' {
  if (status === 'completed') return 'success'
  if (status === 'paused') return 'warning'
  if (status === 'archived') return 'danger'
  return 'primary'
}

export function getLongTermSubtaskStatusTone(status: LongTermSubtaskStatus): 'primary' | 'success' | 'warning' | 'danger' {
  if (status === 'completed') return 'success'
  if (status === 'in_progress') return 'primary'
  if (status === 'skipped') return 'warning'
  return 'danger'
}

export function formatLongTermDateRange(startDate?: string | null, dueDate?: string | null): string {
  if (startDate && dueDate) return `${startDate} - ${dueDate}`
  if (startDate) return `从 ${startDate} 开始`
  if (dueDate) return `${dueDate} 截止`
  return '未设置周期'
}
