import { describe, expect, it } from 'vitest'

import { formatLongTermDateRange, formatLongTermTaskStatus, getLongTermStatusTone } from '@/utils/longTermTask'

describe('long term task helpers', () => {
  it('formats task status labels', () => {
    expect(formatLongTermTaskStatus('active')).toBe('进行中')
    expect(formatLongTermTaskStatus('completed')).toBe('已完成')
  })

  it('maps status tones', () => {
    expect(getLongTermStatusTone('active')).toBe('primary')
    expect(getLongTermStatusTone('paused')).toBe('warning')
  })

  it('formats date ranges', () => {
    expect(formatLongTermDateRange('2026-04-01', '2026-04-30')).toBe('2026-04-01 - 2026-04-30')
    expect(formatLongTermDateRange(null, null)).toBe('未设置周期')
  })
})
