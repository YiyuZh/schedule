import { del, get, post, put } from '@/api/client'
import type {
  AiLog,
  AiParseApplyPayload,
  AiParseApplyResult,
  AiParseResult,
  AiPlanApplyResult,
  AiPlanResult,
} from '@/types/ai'
import type { DeleteResult, PagedData } from '@/types/common'
import type { AiConfig, AiConfigUpdatePayload, AiTestConnectionResult } from '@/types/settings'

export function fetchAiConfig(): Promise<AiConfig> {
  return get<AiConfig>('/api/ai/config')
}

export function saveAiConfig(payload: AiConfigUpdatePayload): Promise<AiConfig> {
  return put<AiConfig>('/api/ai/config', { body: payload })
}

export function testAiService(): Promise<AiTestConnectionResult> {
  return post<AiTestConnectionResult>('/api/ai/test-connection')
}

export function parseAiInput(payload: { text: string; date_context?: string }): Promise<AiParseResult> {
  return post<AiParseResult>('/api/ai/parse', { body: payload })
}

export function applyAiParse(payload: AiParseApplyPayload): Promise<AiParseApplyResult> {
  return post<AiParseApplyResult>('/api/ai/parse/apply', { body: payload })
}

export function createAiPlan(payload: {
  date: string
  user_input: string
  include_habits: boolean
  option_count: number
}): Promise<AiPlanResult> {
  return post<AiPlanResult>('/api/ai/plan', { body: payload })
}

export function applyAiPlan(payload: { log_id: number; selected_option_index: number }): Promise<AiPlanApplyResult> {
  return post<AiPlanApplyResult>('/api/ai/plan/apply', { body: payload })
}

export function fetchAiLogs(query?: { log_type?: 'parse' | 'plan'; page?: number; page_size?: number }): Promise<PagedData<AiLog>> {
  return get<PagedData<AiLog>>('/api/ai/logs', { query })
}

export function fetchAiLog(logId: number): Promise<AiLog> {
  return get<AiLog>(`/api/ai/logs/${logId}`)
}

export function deleteAiLog(logId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/ai/logs/${logId}`)
}
