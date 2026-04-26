import { defineComponent, nextTick, reactive } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AiWorkspacePage from '@/pages/AiWorkspacePage.vue'

const mocks = vi.hoisted(() => ({
  aiStore: null as unknown,
  appStore: null as unknown,
  routerPush: vi.fn(),
  notifyError: vi.fn(),
  notifySuccess: vi.fn(),
  confirmAction: vi.fn(async () => true),
  copyText: vi.fn(async () => {}),
  downloadJsonFile: vi.fn(),
  removeRefreshListener: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mocks.routerPush,
  }),
}))

vi.mock('@/stores/ai', () => ({
  useAiStore: () => mocks.aiStore,
  buildAiRetryDraft: vi.fn(() => null),
  buildAiLogExportPayload: vi.fn((log) => log),
  formatAiLogJson: vi.fn((value: string | null | undefined) => value || '--'),
}))

vi.mock('@/stores/app', () => ({
  useAppStore: () => mocks.appStore,
}))

vi.mock('@/utils/message', () => ({
  notifyError: mocks.notifyError,
  notifySuccess: mocks.notifySuccess,
  confirmAction: mocks.confirmAction,
}))

vi.mock('@/utils/share', () => ({
  copyText: mocks.copyText,
  downloadJsonFile: mocks.downloadJsonFile,
}))

vi.mock('@/utils/pageEvents', () => ({
  listenPageRefresh: vi.fn(() => mocks.removeRefreshListener),
}))

function buildAiStore() {
  const store = reactive({
    configLoading: false,
    testingConnection: false,
    parseLoading: false,
    parseApplying: false,
    planLoading: false,
    planApplyingIndex: null as number | null,
    logsLoading: false,
    detailLoading: false,
    aiConfig: {
      enabled: true,
      provider: 'deepseek',
      model_name: 'deepseek-chat',
      plan_model_name: 'deepseek-reasoner',
      base_url: 'https://api.deepseek.com/v1',
      has_api_key: true,
      timeout: 60,
      temperature: 0.2,
    },
    connectionState: null as { ok: boolean; message: string; checked_at: string } | null,
    parseResult: null as {
      actions: Array<{ action_type: string; title?: string; date?: string; start_time?: string; end_time?: string; category?: string; is_study?: boolean; planned_duration_minutes?: number }>
      raw_log_id: number
    } | null,
    planResult: null as {
      plan_options: Array<{ name: string; reason: string; items: Array<{ item_type: string; title: string; date: string; start_time: string; end_time: string; category?: string; task_id?: number }> }>
      raw_log_id: number
    } | null,
    logs: [] as Array<Record<string, unknown>>,
    totalLogs: 0,
    selectedLog: null as Record<string, unknown> | null,
    lastApplyFeedback: null as { kind: 'parse' | 'plan'; message: string; details: string[]; raw_log_id: number; created_at: string } | null,
    logFilter: 'all' as 'all' | 'parse' | 'plan',
    logPage: 1,
    logPageSize: 10,
    parseDraft: reactive({
      text: '',
      date_context: '2026-04-24',
    }),
    planDraft: reactive({
      date: '2026-04-24',
      user_input: '',
      include_habits: true,
      option_count: 3,
    }),
    loadConfig: vi.fn(async () => {}),
    testConnection: vi.fn(async () => {}),
    runParse: vi.fn(async () => {}),
    applyParseResult: vi.fn(async () => {}),
    runPlan: vi.fn(async () => {}),
    applyPlanResult: vi.fn(async (_index: number) => {}),
    loadLogs: vi.fn(async (page?: number) => {
      if (typeof page === 'number') {
        store.logPage = page
      }
    }),
    loadLogDetail: vi.fn(async (_logId: number) => {
      store.selectedLog = {
        id: 7,
        log_type: 'parse',
        provider: 'deepseek',
        model_name: 'deepseek-chat',
        user_input: '测试输入',
        context_json: '{"date_context":"2026-04-24"}',
        ai_output_json: '{"actions":[]}',
        parsed_success: true,
        applied_success: false,
        error_message: null,
        created_at: '2026-04-24T10:00:00',
      }
    }),
    removeLog: vi.fn(async () => {}),
    applyRetryDraft: vi.fn(() => null),
    resetParse: vi.fn(() => {
      store.parseResult = null
      store.parseDraft.text = ''
      store.parseDraft.date_context = '2026-04-24'
    }),
    resetPlan: vi.fn(() => {
      store.planResult = null
      store.planDraft.date = '2026-04-24'
      store.planDraft.user_input = ''
      store.planDraft.include_habits = true
      store.planDraft.option_count = 3
    }),
    clearApplyFeedback: vi.fn((kind?: 'parse' | 'plan') => {
      if (!kind || store.lastApplyFeedback?.kind === kind) {
        store.lastApplyFeedback = null
      }
    }),
  })

  return store
}

function buildAppStore() {
  return reactive({
    runtimeModeLabel: '桌面端',
    refreshRuntimeState: vi.fn(async () => {}),
  })
}

const ElButtonStub = defineComponent({
  props: {
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
  },
  emits: ['click'],
  template: '<button :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
})

const ElCardStub = defineComponent({
  template: '<div class="el-card"><div v-if="$slots.header"><slot name="header" /></div><slot /></div>',
})

const ElAlertStub = defineComponent({
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
  },
  template: '<div class="el-alert"><strong>{{ title }}</strong><p v-if="description">{{ description }}</p><slot /></div>',
})

const ElDrawerStub = defineComponent({
  props: {
    modelValue: { type: Boolean, default: false },
    title: { type: String, default: '' },
  },
  template: '<section v-if="modelValue" class="el-drawer"><h3>{{ title }}</h3><slot /></section>',
})

const EmptyStateStub = defineComponent({
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
  },
  template: '<div class="empty-state"><strong>{{ title }}</strong><p>{{ description }}</p><slot /></div>',
})

const PageHeaderStub = defineComponent({
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
    eyebrow: { type: String, default: '' },
  },
  template: '<header><div>{{ eyebrow }}</div><h1>{{ title }}</h1><p>{{ description }}</p><slot name="actions" /></header>',
})

async function flushUi(): Promise<void> {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
}

function mountPage() {
  return mount(AiWorkspacePage, {
    global: {
      components: {
        PageHeader: PageHeaderStub,
        EmptyState: EmptyStateStub,
      },
      stubs: {
        'el-button': ElButtonStub,
        'el-card': ElCardStub,
        'el-form': { template: '<form><slot /></form>' },
        'el-form-item': { template: '<div><slot /></div>' },
        'el-input': { template: '<textarea />' },
        'el-date-picker': { template: '<input />' },
        'el-input-number': { template: '<input type="number" />' },
        'el-switch': { template: '<input type="checkbox" />' },
        'el-select': { template: '<div><slot /></div>' },
        'el-option': { template: '<div />' },
        'el-table': { template: '<div class="el-table"><slot /></div>' },
        'el-table-column': { template: '<div />' },
        'el-pagination': { template: '<div class="el-pagination" />' },
        'el-drawer': ElDrawerStub,
        'el-alert': ElAlertStub,
        'el-empty': { template: '<div class="el-empty"><slot name="description" /></div>' },
      },
      directives: {
        loading: {
          mounted() {},
          updated() {},
        },
      },
    },
  })
}

describe('AiWorkspacePage', () => {
  beforeEach(() => {
    mocks.routerPush.mockReset()
    mocks.notifyError.mockReset()
    mocks.notifySuccess.mockReset()
    mocks.confirmAction.mockReset()
    mocks.confirmAction.mockResolvedValue(true)
    mocks.copyText.mockReset()
    mocks.downloadJsonFile.mockReset()
    mocks.removeRefreshListener.mockReset()
    mocks.aiStore = buildAiStore()
    mocks.appStore = buildAppStore()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('loads config, logs and runtime state on mount', async () => {
    mountPage()
    await flushUi()

    expect((mocks.aiStore as ReturnType<typeof buildAiStore>).loadConfig).toHaveBeenCalledTimes(1)
    expect((mocks.aiStore as ReturnType<typeof buildAiStore>).loadLogs).toHaveBeenCalledTimes(1)
    expect((mocks.appStore as ReturnType<typeof buildAppStore>).refreshRuntimeState).toHaveBeenCalledTimes(1)
  })

  it('shows a workspace warning when initial refresh partially fails', async () => {
    ;(mocks.aiStore as ReturnType<typeof buildAiStore>).loadConfig.mockRejectedValueOnce(new Error('配置加载失败'))

    const wrapper = mountPage()
    await flushUi()

    expect(wrapper.text()).toContain('工作区有部分数据刷新失败')
  })

  it('blocks empty parse submissions and keeps runParse untouched', async () => {
    const wrapper = mountPage()
    await flushUi()

    await wrapper.get('[data-testid="parse-submit-button"]').trigger('click')
    await flushUi()

    expect(mocks.notifyError).toHaveBeenCalledWith('请输入要解析的自然语言内容')
    expect((mocks.aiStore as ReturnType<typeof buildAiStore>).runParse).not.toHaveBeenCalled()
  })

  it('keeps parse preview when applying parse result fails', async () => {
    const aiStore = mocks.aiStore as ReturnType<typeof buildAiStore>
    aiStore.parseResult = {
      raw_log_id: 88,
      actions: [
        {
          action_type: 'add_task',
          title: '英语学习',
          date: '2026-04-24',
          start_time: '20:00',
          end_time: '21:00',
          category: 'study',
          is_study: true,
          planned_duration_minutes: 60,
        },
      ],
    }
    aiStore.applyParseResult.mockRejectedValueOnce(new Error('应用失败'))

    const wrapper = mountPage()
    await flushUi()
    await wrapper.get('[data-testid="parse-apply-button"]').trigger('click')
    await flushUi()
    await (
      wrapper.vm as unknown as {
        handleApplyParseActions: (actions: NonNullable<typeof aiStore.parseResult>['actions']) => Promise<void>
      }
    ).handleApplyParseActions(aiStore.parseResult.actions)
    await flushUi()

    expect(aiStore.applyParseResult).toHaveBeenCalledTimes(1)
    expect(aiStore.parseResult?.actions[0]?.title).toBe('英语学习')
    expect(wrapper.text()).toContain('英语学习')
  })

  it('renders a dedicated detail error state when log detail loading fails', async () => {
    const aiStore = mocks.aiStore as ReturnType<typeof buildAiStore>
    aiStore.loadLogDetail.mockRejectedValueOnce(new Error('日志详情加载失败'))

    const wrapper = mountPage()
    await flushUi()
    await (wrapper.vm as unknown as { openLogDetail: (logId: number) => Promise<void> }).openLogDetail(42)
    await flushUi()

    expect(wrapper.text()).toContain('日志详情加载失败')
  })
})
