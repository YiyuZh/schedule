import type { TaskStatus } from '@/types/dailyTask'
import type { EventStatus } from '@/types/event'
import type { TimePreference } from '@/types/taskTemplate'
import type { TimerStatus } from '@/types/timer'

export function formatDurationMinutes(minutes: number | null | undefined): string {
  if (!minutes || minutes <= 0) {
    return '0 分钟'
  }

  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60

  if (hours <= 0) {
    return `${remainMinutes} 分钟`
  }

  if (remainMinutes === 0) {
    return `${hours} 小时`
  }

  return `${hours} 小时 ${remainMinutes} 分钟`
}

export function formatDurationCompact(minutes: number | null | undefined): string {
  if (!minutes || minutes <= 0) {
    return '0m'
  }

  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60

  if (hours <= 0) {
    return `${remainMinutes}m`
  }

  if (remainMinutes === 0) {
    return `${hours}h`
  }

  return `${hours}h ${remainMinutes}m`
}

export function formatSeconds(seconds: number): string {
  const safeSeconds = Math.max(0, seconds)
  const hours = Math.floor(safeSeconds / 3600)
  const minutes = Math.floor((safeSeconds % 3600) / 60)
  const remainSeconds = safeSeconds % 60
  return [hours, minutes, remainSeconds].map((part) => String(part).padStart(2, '0')).join(':')
}

export function formatDateLabel(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }
  return value
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }
  return value.replace('T', ' ')
}

export function formatTimeRange(startTime?: string | null, endTime?: string | null): string {
  if (startTime && endTime) {
    return `${startTime} - ${endTime}`
  }
  if (startTime) {
    return `开始 ${startTime}`
  }
  if (endTime) {
    return `截止 ${endTime}`
  }
  return '未安排时间'
}

export function formatPercent(value: number): string {
  return `${value.toFixed(0)}%`
}

export function formatJsonString(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

export function formatTaskStatusLabel(status: TaskStatus): string {
  return {
    pending: '待办',
    running: '进行中',
    completed: '已完成',
    skipped: '已跳过',
  }[status]
}

export function formatEventStatusLabel(status: EventStatus): string {
  return {
    scheduled: '已安排',
    completed: '已完成',
    cancelled: '已取消',
  }[status]
}

export function formatTimerStatusLabel(status: TimerStatus | null | undefined): string {
  if (status === 'running') return '进行中'
  if (status === 'paused') return '已暂停'
  return '空闲'
}

export function formatTimePreferenceLabel(preference: TimePreference): string {
  return {
    none: '不限',
    morning: '上午',
    afternoon: '下午',
    evening: '晚上',
    night: '夜间',
  }[preference]
}

export function formatPriorityLabel(priority: number): string {
  if (priority >= 5) return '高优先级'
  if (priority >= 3) return '中优先级'
  return '低优先级'
}

export function getTaskStatusTone(status: TaskStatus): 'primary' | 'success' | 'warning' | 'danger' {
  if (status === 'running') return 'primary'
  if (status === 'completed') return 'success'
  if (status === 'skipped') return 'warning'
  return 'danger'
}

export function getPriorityTone(priority: number): 'danger' | 'warning' | 'success' {
  if (priority >= 5) return 'danger'
  if (priority >= 3) return 'warning'
  return 'success'
}

export function calculateMinutesProgress(actualMinutes: number, plannedMinutes: number): number {
  if (!plannedMinutes || plannedMinutes <= 0) {
    return actualMinutes > 0 ? 100 : 0
  }

  return Math.min(100, Math.round((actualMinutes / plannedMinutes) * 100))
}
