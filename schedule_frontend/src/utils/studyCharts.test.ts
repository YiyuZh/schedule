import { describe, expect, it } from 'vitest'

import { buildStudyCategoryChart, buildStudyDayBars } from '@/utils/studyCharts'

describe('study chart helpers', () => {
  it('builds donut chart data from category stats', () => {
    const chart = buildStudyCategoryChart([
      { category: '英语', duration_minutes: 60 },
      { category: '数学', duration_minutes: 30 },
    ])

    expect(chart.totalMinutes).toBe(90)
    expect(chart.items).toHaveLength(2)
    expect(chart.items[0]).toMatchObject({
      label: '英语',
      minutes: 60,
    })
    expect(chart.items[0].percent).toBeCloseTo(66.7, 1)
    expect(chart.gradient.startsWith('conic-gradient(')).toBe(true)
  })

  it('builds day bars with proportional heights', () => {
    const chart = buildStudyDayBars([
      { session_date: '2026-04-22', duration_minutes: 30 },
      { session_date: '2026-04-23', duration_minutes: 60 },
    ])

    expect(chart.items).toHaveLength(2)
    expect(chart.items[0].displayLabel).toBe('04-22')
    expect(chart.items[0].heightPercent).toBe(50)
    expect(chart.items[1].heightPercent).toBe(100)
  })
})
