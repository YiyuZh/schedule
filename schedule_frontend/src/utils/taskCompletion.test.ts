import { describe, expect, it } from 'vitest'

import { buildTaskCompletionDraft, TASK_COMPLETION_QUICK_FILL_VALUES } from '@/utils/taskCompletion'

describe('task completion helpers', () => {
  it('defaults actual duration to planned minutes and enables study sync for study tasks', () => {
    expect(buildTaskCompletionDraft(90, true)).toEqual({
      actual_duration_minutes: 90,
      sync_study_session: true,
    })
  })

  it('defaults to zero minutes and disables study sync for non-study tasks', () => {
    expect(buildTaskCompletionDraft(0, false)).toEqual({
      actual_duration_minutes: 0,
      sync_study_session: false,
    })
  })

  it('keeps the fixed quick fill presets stable', () => {
    expect(TASK_COMPLETION_QUICK_FILL_VALUES).toEqual([5, 10, 15, 30, 45, 60])
  })
})
