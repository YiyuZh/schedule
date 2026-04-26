function pad(value: number): string {
  return String(value).padStart(2, '0')
}

export function todayDateString(): string {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export function shiftDate(dateString: string, offsetDays: number): string {
  const date = new Date(`${dateString}T00:00:00`)
  date.setDate(date.getDate() + offsetDays)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function getWeekdayLabel(dateString: string): string {
  const date = new Date(`${dateString}T00:00:00`)
  const labels = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return labels[date.getDay()]
}

export function formatDisplayDate(dateString: string): string {
  const date = new Date(`${dateString}T00:00:00`)
  return `${date.getFullYear()}年${pad(date.getMonth() + 1)}月${pad(date.getDate())}日`
}

export function isToday(dateString: string): boolean {
  return todayDateString() === dateString
}

export function toDateRangePayload(range: string[] | undefined): { start_date?: string; end_date?: string } {
  if (!range || range.length !== 2) {
    return {}
  }

  return {
    start_date: range[0],
    end_date: range[1],
  }
}

export function buildRangeByShortcut(shortcut: 'today' | 'week' | 'month' | 'year'): { start_date: string; end_date: string } {
  const now = new Date()
  const end = todayDateString()

  if (shortcut === 'today') {
    return { start_date: end, end_date: end }
  }

  if (shortcut === 'week') {
    const start = new Date(now)
    const weekday = start.getDay() || 7
    start.setDate(start.getDate() - weekday + 1)
    return {
      start_date: `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())}`,
      end_date: end,
    }
  }

  if (shortcut === 'month') {
    return {
      start_date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`,
      end_date: end,
    }
  }

  return {
    start_date: `${now.getFullYear()}-01-01`,
    end_date: end,
  }
}
