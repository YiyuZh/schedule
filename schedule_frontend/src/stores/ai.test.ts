import { describe, expect, it } from 'vitest'

import { buildAiLogExportPayload, buildAiRetryDraft, summarizeAiApplyResult } from '@/stores/ai'
import type { AiLog } from '@/types/ai'

function buildLog(overrides: Partial<AiLog>): AiLog {
  return {
    id: 1,
    log_type: 'parse',
    provider: 'openai-compatible',
    model_name: 'gpt-test',
    user_input: '测试输入',
    context_json: null,
    ai_output_json: null,
    parsed_success: true,
    applied_success: false,
    error_message: null,
    created_at: '2026-04-23T12:00:00',
    ...overrides,
  }
}

describe('AI workspace helpers', () => {
  it('builds parse retry drafts from parse logs', () => {
    const draft = buildAiRetryDraft(
      buildLog({
        log_type: 'parse',
        user_input: '明天下午三点开会',
        context_json: JSON.stringify({ date_context: '2026-04-24' }),
      }),
    )

    expect(draft).toEqual({
      kind: 'parse',
      payload: {
        text: '明天下午三点开会',
        date_context: '2026-04-24',
      },
    })
  })

  it('builds plan retry drafts from plan logs', () => {
    const draft = buildAiRetryDraft(
      buildLog({
        log_type: 'plan',
        user_input: '把今晚的学习和健身安排好',
        context_json: JSON.stringify({
          date: '2026-04-23',
          user_input: '把今晚的学习和健身安排好',
          option_count: 2,
          habit_snapshot: { preferred_study_window: 'evening' },
        }),
      }),
    )

    expect(draft).toEqual({
      kind: 'plan',
      payload: {
        date: '2026-04-23',
        user_input: '把今晚的学习和健身安排好',
        include_habits: true,
        option_count: 2,
      },
    })
  })

  it('returns null when context is not enough to retry', () => {
    const draft = buildAiRetryDraft(
      buildLog({
        log_type: 'plan',
        context_json: JSON.stringify({ option_count: 3 }),
      }),
    )

    expect(draft).toBeNull()
  })

  it('summarizes parse apply results', () => {
    const summary = summarizeAiApplyResult(
      'parse',
      88,
      {
        created_task_ids: [1, 2],
        created_event_ids: [9],
        created_course_ids: [],
      },
      '2026-04-23T20:00:00',
    )

    expect(summary).toEqual({
      kind: 'parse',
      message: 'AI 解析结果已应用',
      details: ['创建任务：2 项（1, 2）', '创建事件：1 项（9）'],
      raw_log_id: 88,
      created_at: '2026-04-23T20:00:00',
    })
  })

  it('builds export payloads with parsed json when available', () => {
    const payload = buildAiLogExportPayload(
      buildLog({
        log_type: 'plan',
        context_json: JSON.stringify({ date: '2026-04-23' }),
        ai_output_json: JSON.stringify({ plan_options: [{ name: 'A' }] }),
      }),
    )

    expect(payload.context_json).toEqual({ date: '2026-04-23' })
    expect(payload.ai_output_json).toEqual({ plan_options: [{ name: 'A' }] })
  })
})
