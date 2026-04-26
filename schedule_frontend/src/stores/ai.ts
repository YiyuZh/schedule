import { reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  applyAiParse,
  applyAiPlan,
  createAiPlan,
  deleteAiLog,
  fetchAiConfig,
  fetchAiLog,
  fetchAiLogs,
  parseAiInput,
  testAiService,
} from '@/api/ai'
import type {
  AiApplyFeedback,
  AiConnectionState,
  AiLog,
  AiLogExportPayload,
  AiLogFilter,
  AiParseAction,
  AiParseApplyResult,
  AiParseDraft,
  AiParseResult,
  AiPlanApplyResult,
  AiPlanDraft,
  AiPlanResult,
  AiRetryDraft,
} from '@/types/ai'
import type { AiConfig } from '@/types/settings'
import { todayDateString } from '@/utils/date'
import { notifyError, notifyInfo, notifySuccess } from '@/utils/message'

type JsonRecord = Record<string, unknown>

function safeParseJson(value: string | null | undefined): unknown {
  if (!value) {
    return null
  }

  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function buildApplyDetail(label: string, ids: number[] | undefined): string | null {
  if (!ids?.length) {
    return null
  }
  return `${label}：${ids.length} 项（${ids.join(', ')}）`
}

export function buildAiRetryDraft(log: AiLog): AiRetryDraft | null {
  const context = safeParseJson(log.context_json)
  if (!context || typeof context !== 'object') {
    return null
  }

  const contextRecord = context as JsonRecord

  if (log.log_type === 'parse') {
    return {
      kind: 'parse',
      payload: {
        text: log.user_input,
        date_context: typeof contextRecord.date_context === 'string' ? contextRecord.date_context : undefined,
      },
    }
  }

  if (log.log_type === 'plan') {
    const date = typeof contextRecord.date === 'string' ? contextRecord.date : ''
    const userInput = typeof contextRecord.user_input === 'string' ? contextRecord.user_input : log.user_input
    const optionCount = typeof contextRecord.option_count === 'number' ? contextRecord.option_count : 3

    if (!date || !userInput) {
      return null
    }

    return {
      kind: 'plan',
      payload: {
        date,
        user_input: userInput,
        include_habits: Object.prototype.hasOwnProperty.call(contextRecord, 'habit_snapshot'),
        option_count: Math.min(3, Math.max(1, optionCount)),
      },
    }
  }

  return null
}

export function buildAiLogExportPayload(log: AiLog): AiLogExportPayload {
  return {
    id: log.id,
    log_type: log.log_type,
    provider: log.provider,
    model_name: log.model_name,
    user_input: log.user_input,
    context_json: safeParseJson(log.context_json) ?? log.context_json,
    ai_output_json: safeParseJson(log.ai_output_json) ?? log.ai_output_json,
    parsed_success: log.parsed_success,
    applied_success: log.applied_success,
    error_message: log.error_message,
    created_at: log.created_at,
  }
}

export function summarizeAiApplyResult(
  kind: 'parse' | 'plan',
  rawLogId: number,
  result: AiParseApplyResult | AiPlanApplyResult,
  createdAt = new Date().toISOString(),
): AiApplyFeedback {
  const details: string[] = []

  if (kind === 'parse') {
    const parseResult = result as AiParseApplyResult
    const taskDetail = buildApplyDetail('创建任务', parseResult.created_task_ids)
    const eventDetail = buildApplyDetail('创建事件', parseResult.created_event_ids)
    const courseDetail = buildApplyDetail('创建课程', parseResult.created_course_ids)

    if (taskDetail) details.push(taskDetail)
    if (eventDetail) details.push(eventDetail)
    if (courseDetail) details.push(courseDetail)
  } else {
    const planResult = result as AiPlanApplyResult
    const eventDetail = buildApplyDetail('创建事件', planResult.created_event_ids)
    const scheduleDetail = buildApplyDetail('安排任务', planResult.scheduled_task_ids)

    if (eventDetail) details.push(eventDetail)
    if (scheduleDetail) details.push(scheduleDetail)
  }

  if (!details.length) {
    details.push('本次应用没有新增或调度任何条目。')
  }

  return {
    kind,
    message: kind === 'parse' ? 'AI 解析结果已应用' : 'AI 规划方案已应用',
    details,
    raw_log_id: rawLogId,
    created_at: createdAt,
  }
}

export function formatAiLogJson(value: string | null | undefined): string {
  const parsed = safeParseJson(value)
  if (parsed === null) {
    return value || '--'
  }
  return JSON.stringify(parsed, null, 2)
}

export const useAiStore = defineStore('ai', () => {
  const configLoading = ref(false)
  const testingConnection = ref(false)
  const parseLoading = ref(false)
  const parseApplying = ref(false)
  const planLoading = ref(false)
  const planApplyingIndex = ref<number | null>(null)
  const logsLoading = ref(false)
  const detailLoading = ref(false)

  const aiConfig = ref<AiConfig | null>(null)
  const connectionState = ref<AiConnectionState | null>(null)
  const parseResult = ref<AiParseResult | null>(null)
  const planResult = ref<AiPlanResult | null>(null)
  const logs = ref<AiLog[]>([])
  const totalLogs = ref(0)
  const selectedLog = ref<AiLog | null>(null)
  const lastApplyFeedback = ref<AiApplyFeedback | null>(null)
  const logFilter = ref<AiLogFilter>('all')
  const logPage = ref(1)
  const logPageSize = ref(10)

  const parseDraft = reactive<AiParseDraft>({
    text: '',
    date_context: todayDateString(),
  })

  const planDraft = reactive<AiPlanDraft>({
    date: todayDateString(),
    user_input: '',
    include_habits: true,
    option_count: 3,
  })

  async function loadConfig(): Promise<void> {
    configLoading.value = true
    try {
      aiConfig.value = await fetchAiConfig()
    } finally {
      configLoading.value = false
    }
  }

  async function testConnection(): Promise<void> {
    testingConnection.value = true
    try {
      const result = await testAiService()
      connectionState.value = {
        ok: result.ok,
        message: result.message,
        checked_at: new Date().toISOString(),
      }
      if (result.ok) {
        notifySuccess(result.message)
      } else {
        notifyError(result.message)
      }
    } catch (error) {
      connectionState.value = {
        ok: false,
        message: error instanceof Error ? error.message : 'AI 连接测试失败',
        checked_at: new Date().toISOString(),
      }
      throw error
    } finally {
      testingConnection.value = false
    }
  }

  async function runParse(): Promise<void> {
    parseLoading.value = true
    try {
      if (lastApplyFeedback.value?.kind === 'parse') {
        lastApplyFeedback.value = null
      }

      parseResult.value = await parseAiInput({
        text: parseDraft.text.trim(),
        date_context: parseDraft.date_context || undefined,
      })
      await loadLogs()
    } finally {
      parseLoading.value = false
    }
  }

  async function applyParseResult(actions?: AiParseAction[]): Promise<void> {
    if (!parseResult.value) {
      return
    }

    parseApplying.value = true
    try {
      const result = await applyAiParse({
        log_id: parseResult.value.raw_log_id,
        actions: actions ?? parseResult.value.actions,
      })
      lastApplyFeedback.value = summarizeAiApplyResult('parse', parseResult.value.raw_log_id, result)
      notifySuccess(lastApplyFeedback.value.message)
      await Promise.all([loadLogs(), loadLogDetail(parseResult.value.raw_log_id)])
    } finally {
      parseApplying.value = false
    }
  }

  async function runPlan(): Promise<void> {
    planLoading.value = true
    try {
      if (lastApplyFeedback.value?.kind === 'plan') {
        lastApplyFeedback.value = null
      }

      planResult.value = await createAiPlan({
        date: planDraft.date,
        user_input: planDraft.user_input.trim(),
        include_habits: planDraft.include_habits,
        option_count: planDraft.option_count,
      })
      await loadLogs()
    } finally {
      planLoading.value = false
    }
  }

  async function applyPlanResult(index: number): Promise<void> {
    if (!planResult.value) {
      return
    }

    planApplyingIndex.value = index
    try {
      const result = await applyAiPlan({
        log_id: planResult.value.raw_log_id,
        selected_option_index: index,
      })
      lastApplyFeedback.value = summarizeAiApplyResult('plan', planResult.value.raw_log_id, result)
      notifySuccess(lastApplyFeedback.value.message)
      await Promise.all([loadLogs(), loadLogDetail(planResult.value.raw_log_id)])
    } finally {
      planApplyingIndex.value = null
    }
  }

  async function loadLogs(page = logPage.value): Promise<void> {
    logsLoading.value = true
    logPage.value = page
    try {
      const data = await fetchAiLogs({
        log_type: logFilter.value === 'all' ? undefined : logFilter.value,
        page: logPage.value,
        page_size: logPageSize.value,
      })
      logs.value = data.items
      totalLogs.value = data.total
      logPage.value = data.page
      logPageSize.value = data.page_size
    } finally {
      logsLoading.value = false
    }
  }

  async function loadLogDetail(logId: number): Promise<void> {
    detailLoading.value = true
    try {
      selectedLog.value = await fetchAiLog(logId)
    } catch (error) {
      selectedLog.value = null
      throw error
    } finally {
      detailLoading.value = false
    }
  }

  async function removeLog(logId: number): Promise<void> {
    await deleteAiLog(logId)
    if (selectedLog.value?.id === logId) {
      selectedLog.value = null
    }
    notifySuccess('AI 日志已删除')
    await loadLogs()
  }

  function applyRetryDraft(log: AiLog): AiRetryDraft | null {
    const draft = buildAiRetryDraft(log)
    if (!draft) {
      return null
    }

    if (draft.kind === 'parse') {
      parseDraft.text = draft.payload.text
      parseDraft.date_context = draft.payload.date_context
      parseResult.value = null
      notifyInfo('已填入 AI 解析重试草稿')
      return draft
    }

    planDraft.date = draft.payload.date
    planDraft.user_input = draft.payload.user_input
    planDraft.include_habits = draft.payload.include_habits
    planDraft.option_count = draft.payload.option_count
    planResult.value = null
    notifyInfo('已填入 AI 规划重试草稿')
    return draft
  }

  function resetParse(): void {
    parseResult.value = null
    parseDraft.text = ''
    parseDraft.date_context = todayDateString()
    if (lastApplyFeedback.value?.kind === 'parse') {
      lastApplyFeedback.value = null
    }
  }

  function resetPlan(): void {
    planResult.value = null
    planDraft.date = todayDateString()
    planDraft.user_input = ''
    planDraft.include_habits = true
    planDraft.option_count = 3
    if (lastApplyFeedback.value?.kind === 'plan') {
      lastApplyFeedback.value = null
    }
  }

  function clearApplyFeedback(kind?: 'parse' | 'plan'): void {
    if (!kind || lastApplyFeedback.value?.kind === kind) {
      lastApplyFeedback.value = null
    }
  }

  return {
    configLoading,
    testingConnection,
    parseLoading,
    parseApplying,
    planLoading,
    planApplyingIndex,
    logsLoading,
    detailLoading,
    aiConfig,
    connectionState,
    parseResult,
    planResult,
    logs,
    totalLogs,
    selectedLog,
    lastApplyFeedback,
    logFilter,
    logPage,
    logPageSize,
    parseDraft,
    planDraft,
    loadConfig,
    testConnection,
    runParse,
    applyParseResult,
    runPlan,
    applyPlanResult,
    loadLogs,
    loadLogDetail,
    removeLog,
    applyRetryDraft,
    resetParse,
    resetPlan,
    clearApplyFeedback,
  }
})
