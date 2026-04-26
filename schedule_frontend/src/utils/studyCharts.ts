import type { StudyCategoryStat, StudyDayStat } from '@/types/study'

const CHART_COLORS = ['#005fb8', '#4d6673', '#f59e0b', '#34a853', '#7c6ee6', '#ef6c5b', '#13b7a6', '#9aa5b1']

export interface StudyCategoryChartItem {
  label: string
  minutes: number
  percent: number
  color: string
}

export interface StudyCategoryChartModel {
  totalMinutes: number
  gradient: string
  items: StudyCategoryChartItem[]
}

export interface StudyDayBarItem {
  sessionDate: string
  displayLabel: string
  minutes: number
  heightPercent: number
  color: string
}

function roundPercent(value: number): number {
  return Math.round(value * 10) / 10
}

export function buildStudyCategoryChart(stats: StudyCategoryStat[]): StudyCategoryChartModel {
  const totalMinutes = stats.reduce((sum, item) => sum + item.duration_minutes, 0)
  if (totalMinutes <= 0) {
    return {
      totalMinutes: 0,
      gradient: 'conic-gradient(#dbe5ee 0deg 360deg)',
      items: stats.map((item, index) => ({
        label: item.category || '未分类',
        minutes: item.duration_minutes,
        percent: 0,
        color: CHART_COLORS[index % CHART_COLORS.length],
      })),
    }
  }

  let currentDegree = 0

  const items = stats.map((item, index) => {
    const percent = totalMinutes > 0 ? (item.duration_minutes / totalMinutes) * 100 : 0
    const degree = totalMinutes > 0 ? (item.duration_minutes / totalMinutes) * 360 : 0
    const startDegree = currentDegree
    currentDegree += degree
    return {
      label: item.category || '未分类',
      minutes: item.duration_minutes,
      percent: roundPercent(percent),
      color: CHART_COLORS[index % CHART_COLORS.length],
      startDegree,
      endDegree: currentDegree,
    }
  })

  const gradient = items.length
    ? `conic-gradient(${items.map((item) => `${item.color} ${item.startDegree}deg ${item.endDegree}deg`).join(', ')})`
    : 'conic-gradient(#dbe5ee 0deg 360deg)'

  return {
    totalMinutes,
    gradient,
    items: items.map(({ startDegree: _startDegree, endDegree: _endDegree, ...item }) => item),
  }
}

export function buildStudyDayBars(stats: StudyDayStat[]): { items: StudyDayBarItem[] } {
  const maxMinutes = stats.reduce((max, item) => Math.max(max, item.duration_minutes), 0)

  return {
    items: stats.map((item, index) => ({
      sessionDate: item.session_date,
      displayLabel: item.session_date.slice(5),
      minutes: item.duration_minutes,
      heightPercent: maxMinutes > 0 ? Math.max(10, Math.round((item.duration_minutes / maxMinutes) * 100)) : 0,
      color: CHART_COLORS[index % CHART_COLORS.length],
    })),
  }
}
