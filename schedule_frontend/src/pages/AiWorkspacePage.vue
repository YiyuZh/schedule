<template>
  <section class="page-grid">
    <PageHeader
      title="AI 工作区"
      description="集中管理 AI 解析、AI 规划、连接诊断与日志详情，方便直接观察每一次调用的结果。"
      eyebrow="AI Workspace"
    >
      <template #actions>
        <el-button class="topbar-button" @click="handleRefresh">刷新工作区</el-button>
        <el-button class="topbar-button" @click="router.push('/settings')">前往 AI 设置</el-button>
        <el-button
          type="primary"
          class="topbar-button"
          data-testid="test-connection-button"
          :loading="aiStore.testingConnection"
          @click="handleTestConnection"
        >
          测试连接
        </el-button>
      </template>
    </PageHeader>

    <AiParseActionDialog
      v-model="parseApplyDialogVisible"
      :result="aiStore.parseResult"
      :default-date="aiStore.parseDraft.date_context || aiStore.planDraft.date"
      :loading="aiStore.parseApplying"
      @apply="handleApplyParseActions"
    />

    <el-card class="panel-card">
      <div class="summary-grid ai-diagnostics-grid">
        <div class="summary-tile">
          <span class="summary-title">AI 状态</span>
          <strong>{{ aiStore.aiConfig?.enabled ? '已启用' : '未启用' }}</strong>
        </div>
        <div class="summary-tile">
          <span class="summary-title">Provider</span>
          <strong>{{ aiStore.aiConfig?.provider || '--' }}</strong>
        </div>
        <div class="summary-tile">
          <span class="summary-title">聊天 / 解析模型</span>
          <strong>{{ modelUsage.parseModel }}</strong>
        </div>
        <div class="summary-tile">
          <span class="summary-title">规划 / 推理模型</span>
          <strong>{{ modelUsage.planModel }}</strong>
        </div>
        <div class="summary-tile">
          <span class="summary-title">最近连接结果</span>
          <strong>{{ connectionSummary }}</strong>
        </div>
      </div>

      <div class="ai-diagnostics-meta">
        <div>
          <span class="muted-text">Base URL：</span>
          <span>{{ aiStore.aiConfig?.base_url || '--' }}</span>
        </div>
        <div>
          <span class="muted-text">密钥状态：</span>
          <span>{{ aiStore.aiConfig?.has_api_key ? '已配置' : '未配置' }}</span>
        </div>
        <div>
          <span class="muted-text">Timeout：</span>
          <span>{{ aiStore.aiConfig?.timeout ?? '--' }} 秒</span>
        </div>
        <div>
          <span class="muted-text">Temperature：</span>
          <span>{{ aiStore.aiConfig?.temperature ?? '--' }}</span>
        </div>
        <div>
          <span class="muted-text">运行模式：</span>
          <span>{{ appStore.runtimeModeLabel }}</span>
        </div>
        <div>
          <span class="muted-text">最近检测时间：</span>
          <span>{{ connectionCheckedAt }}</span>
        </div>
      </div>

      <el-alert
        v-if="aiStore.connectionState"
        class="ai-connection-alert"
        :type="aiStore.connectionState.ok ? 'success' : 'warning'"
        :closable="false"
        show-icon
        :title="aiStore.connectionState.message"
      />

      <el-alert
        v-if="workspaceErrorMessage"
        class="ai-connection-alert"
        data-testid="workspace-error-alert"
        type="warning"
        :closable="false"
        show-icon
        :title="workspaceErrorMessage"
      />
    </el-card>

    <div class="page-grid grid-two ai-workspace-grid">
      <div ref="parseSectionRef">
      <el-card class="panel-card section-stack">
        <template #header>
          <div class="inline-actions panel-header-actions">
            <div>
              <strong>自然语言解析</strong>
              <div class="muted-text">当前模型：{{ modelUsage.parseModel }}。把一句自然语言转换为任务或事件，并在确认后写入系统。</div>
            </div>
            <el-button @click="aiStore.resetParse()">清空</el-button>
          </div>
        </template>

        <div class="sample-chip-row">
          <span class="muted-text">示例：</span>
          <el-button
            v-for="sample in parseSamples"
            :key="sample.label"
            text
            class="sample-chip"
            @click="fillParseSample(sample)"
          >
            {{ sample.label }}
          </el-button>
        </div>

        <el-form label-position="top" class="section-stack">
          <el-form-item label="输入文本">
            <el-input
              v-model="aiStore.parseDraft.text"
              type="textarea"
              :rows="5"
              placeholder="例如：明天下午 3 点开项目复盘会，地点 A 会议室。"
            />
          </el-form-item>

          <el-form-item label="日期上下文">
            <el-date-picker
              v-model="aiStore.parseDraft.date_context"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              class="full-width"
            />
          </el-form-item>

          <div class="inline-actions">
            <el-button type="primary" data-testid="parse-submit-button" :loading="aiStore.parseLoading" @click="handleParse">
              开始解析
            </el-button>
            <el-button
              :disabled="!aiStore.parseResult"
              data-testid="parse-apply-button"
              :loading="aiStore.parseApplying"
              @click="handleApplyParse"
            >
              应用解析结果
            </el-button>
            <el-button :disabled="!aiStore.parseResult" @click="copyParseJson">复制 JSON</el-button>
          </div>
        </el-form>

        <el-alert
          v-if="parseFeedback"
          type="success"
          :closable="false"
          show-icon
          :title="parseFeedback.message"
          :description="parseFeedback.details.join('；')"
        />

        <EmptyState
          v-if="!aiStore.parseResult"
          title="暂无解析预览"
          description="完成一次解析后，这里会展示结构化 actions，并支持直接应用。"
          icon="AI"
        />

        <div v-else class="section-stack">
          <div
            v-for="(action, index) in aiStore.parseResult.actions"
            :key="`${action.action_type}-${index}`"
            class="page-card ai-preview-card"
          >
            <div class="inline-actions preview-card-header">
              <strong>{{ action.title || '未命名动作' }}</strong>
              <span class="status-pill is-primary">{{ action.action_type }}</span>
            </div>
            <div class="muted-text">{{ action.date || '--' }} · {{ formatTimeRange(action.start_time, action.end_time) }}</div>
            <div class="soft-text">
              分类：{{ action.category || '未分类' }} · 学习任务：{{ action.is_study ? '是' : '否' }} · 时长：
              {{ action.planned_duration_minutes || 0 }} 分钟
            </div>
          </div>
        </div>
      </el-card>
      </div>

      <div ref="planSectionRef">
      <el-card class="panel-card section-stack">
        <template #header>
          <div class="inline-actions panel-header-actions">
            <div>
              <strong>智能日程规划</strong>
              <div class="muted-text">当前模型：{{ modelUsage.planModel }}。根据当天任务、事件、课程与习惯信息生成可直接应用的候选方案。</div>
            </div>
            <el-button @click="aiStore.resetPlan()">清空</el-button>
          </div>
        </template>

        <div class="sample-chip-row">
          <span class="muted-text">示例：</span>
          <el-button
            v-for="sample in planSamples"
            :key="sample.label"
            text
            class="sample-chip"
            @click="fillPlanSample(sample)"
          >
            {{ sample.label }}
          </el-button>
        </div>

        <el-form label-position="top" class="section-stack">
          <div class="field-row">
            <el-form-item label="目标日期">
              <el-date-picker
                v-model="aiStore.planDraft.date"
                type="date"
                value-format="YYYY-MM-DD"
                format="YYYY-MM-DD"
                class="full-width"
              />
            </el-form-item>
            <el-form-item label="候选数量">
              <el-input-number v-model="aiStore.planDraft.option_count" :min="1" :max="3" class="full-width" />
            </el-form-item>
          </div>

          <div class="field-row">
            <el-form-item label="纳入习惯参考">
              <el-switch v-model="aiStore.planDraft.include_habits" />
            </el-form-item>
          </div>

          <el-form-item label="规划需求">
            <el-input
              v-model="aiStore.planDraft.user_input"
              type="textarea"
              :rows="5"
              placeholder="例如：帮我把今天剩下的学习任务和晚上的健身安排好，最好 23:00 前结束。"
            />
          </el-form-item>

          <div class="inline-actions">
            <el-button type="primary" data-testid="plan-submit-button" :loading="aiStore.planLoading" @click="handlePlan">
              生成方案
            </el-button>
            <el-button :disabled="!aiStore.planResult" @click="copyPlanJson">复制 JSON</el-button>
          </div>
        </el-form>

        <el-alert
          v-if="planFeedback"
          type="success"
          :closable="false"
          show-icon
          :title="planFeedback.message"
          :description="planFeedback.details.join('；')"
        />

        <EmptyState
          v-if="!aiStore.planResult"
          title="暂无规划候选"
          description="生成规划后，这里会展示多个 AI 候选方案，并支持单独应用。"
          icon="AI"
        />

        <div v-else class="section-stack">
          <el-card
            v-for="(option, index) in aiStore.planResult.plan_options"
            :key="`${aiStore.planResult.raw_log_id}-${index}`"
            class="page-card"
          >
            <template #header>
              <div class="inline-actions preview-card-header">
                <div>
                  <strong>{{ option.name }}</strong>
                  <div class="muted-text">{{ option.reason }}</div>
                </div>
                <el-button
                  type="primary"
                  size="small"
                  data-testid="plan-apply-button"
                  :loading="aiStore.planApplyingIndex === index"
                  @click="handleApplyPlan(index)"
                >
                  应用方案
                </el-button>
              </div>
            </template>

            <div class="section-stack">
              <div
                v-for="(item, itemIndex) in option.items"
                :key="`${item.item_type}-${item.title}-${itemIndex}`"
                class="ai-preview-card"
              >
                <div class="inline-actions preview-card-header">
                  <strong>{{ item.title }}</strong>
                  <span :class="['status-pill', item.item_type === 'event' ? 'is-primary' : 'is-warning']">
                    {{ item.item_type === 'event' ? '事件' : '任务安排' }}
                  </span>
                </div>
                <div class="muted-text">{{ item.date }} · {{ item.start_time }} - {{ item.end_time }}</div>
                <div class="soft-text">
                  分类：{{ item.category || '未分类' }}
                  <template v-if="item.task_id"> · Task ID：{{ item.task_id }}</template>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-card>
      </div>
    </div>

    <el-card class="panel-card">
      <template #header>
        <div class="inline-actions panel-header-actions">
          <div>
            <strong>AI 调用日志</strong>
            <div class="muted-text">查看解析 / 规划的上下文、模型输出、错误信息与应用状态。</div>
          </div>

          <div class="log-toolbar">
            <el-select v-model="aiStore.logFilter" style="width: 150px;" @change="handleFilterChange">
              <el-option label="全部日志" value="all" />
              <el-option label="解析记录" value="parse" />
              <el-option label="规划记录" value="plan" />
            </el-select>
            <el-input
              v-model="logKeyword"
              clearable
              style="width: 220px;"
              placeholder="筛选当前页日志"
            />
            <el-button @click="aiStore.loadLogs()">刷新日志</el-button>
          </div>
        </div>
      </template>

      <div class="log-meta-row muted-text">
        当前页展示 {{ filteredLogs.length }} 条，服务端总计 {{ aiStore.totalLogs }} 条。
      </div>

      <el-table :data="filteredLogs" v-loading="aiStore.logsLoading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <span class="status-pill">{{ row.log_type }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="provider" label="Provider" min-width="120" />
        <el-table-column prop="model_name" label="模型" min-width="140" />
        <el-table-column label="解析状态" width="100">
          <template #default="{ row }">
            <span :class="['status-pill', row.parsed_success ? 'is-success' : 'is-danger']">
              {{ row.parsed_success ? '成功' : '失败' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="应用状态" width="100">
          <template #default="{ row }">
            <span :class="['status-pill', row.applied_success ? 'is-success' : '']">
              {{ row.applied_success ? '已应用' : '未应用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="错误摘要" min-width="220">
          <template #default="{ row }">
            {{ row.error_message || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="inline-actions">
              <el-button link @click="openLogDetail(row.id)">详情</el-button>
              <el-button link :disabled="!canRetry(row)" @click="handleRetry(row)">重试</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="logs-pagination">
        <el-pagination
          layout="prev, pager, next, total"
          :current-page="aiStore.logPage"
          :page-size="aiStore.logPageSize"
          :total="aiStore.totalLogs"
          @current-change="aiStore.loadLogs"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      :title="detailTitle"
      size="48%"
      destroy-on-close
    >
      <div v-loading="aiStore.detailLoading" class="section-stack">
        <el-alert
          v-if="detailErrorMessage"
          data-testid="detail-error-alert"
          type="warning"
          :closable="false"
          show-icon
          :title="detailErrorMessage"
        />

        <template v-if="aiStore.selectedLog">
          <div class="detail-grid">
            <div class="detail-item">
              <span class="muted-text">日志类型</span>
              <strong>{{ aiStore.selectedLog.log_type }}</strong>
            </div>
            <div class="detail-item">
              <span class="muted-text">Provider</span>
              <strong>{{ aiStore.selectedLog.provider || '--' }}</strong>
            </div>
            <div class="detail-item">
              <span class="muted-text">模型</span>
              <strong>{{ aiStore.selectedLog.model_name || '--' }}</strong>
            </div>
            <div class="detail-item">
              <span class="muted-text">创建时间</span>
              <strong>{{ formatDateTime(aiStore.selectedLog.created_at) }}</strong>
            </div>
            <div class="detail-item">
              <span class="muted-text">解析状态</span>
              <strong>{{ aiStore.selectedLog.parsed_success ? '成功' : '失败' }}</strong>
            </div>
            <div class="detail-item">
              <span class="muted-text">应用状态</span>
              <strong>{{ aiStore.selectedLog.applied_success ? '已应用' : '未应用' }}</strong>
            </div>
          </div>

          <el-alert
            v-if="aiStore.selectedLog.error_message"
            type="warning"
            :closable="false"
            show-icon
            :title="aiStore.selectedLog.error_message"
          />

          <div class="drawer-action-row">
            <el-button :disabled="!retryDraft" @click="retrySelectedLog">填入重试草稿</el-button>
            <el-button @click="copyUserInput">复制原始输入</el-button>
            <el-button @click="copyContextJson">复制 Context JSON</el-button>
            <el-button @click="copyOutputJson">复制 Output JSON</el-button>
            <el-button @click="exportSelectedLog">导出日志 JSON</el-button>
          </div>
          <div v-if="!retryDraft" class="muted-text">当前日志上下文不足，无法自动生成重试草稿。</div>

          <div class="section-stack">
            <div>
              <strong>用户输入</strong>
              <pre class="code-block">{{ aiStore.selectedLog.user_input }}</pre>
            </div>
            <div>
              <strong>Context JSON</strong>
              <pre class="code-block">{{ formattedContext }}</pre>
            </div>
            <div>
              <strong>AI Output JSON</strong>
              <pre class="code-block">{{ formattedOutput }}</pre>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AiParseActionDialog from '@/components/ai/AiParseActionDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useAppStore } from '@/stores/app'
import { buildAiLogExportPayload, buildAiRetryDraft, formatAiLogJson, useAiStore } from '@/stores/ai'
import type { AiLog, AiParseAction } from '@/types/ai'
import { resolveAiModelUsage } from '@/utils/aiConfig'
import { formatDateTime, formatTimeRange } from '@/utils/format'
import { confirmAction, notifyError, notifySuccess } from '@/utils/message'
import { listenPageRefresh } from '@/utils/pageEvents'
import { copyText, downloadJsonFile } from '@/utils/share'

interface ParseSample {
  label: string
  text: string
  date_context: string
}

interface PlanSample {
  label: string
  user_input: string
  date: string
  include_habits: boolean
  option_count: number
}

const parseSamples: ParseSample[] = [
  {
    label: '项目复盘会',
    text: '明天下午 3 点开项目复盘会，地点 A 会议室。',
    date_context: '2026-04-24',
  },
  {
    label: '英语学习',
    text: '今晚 8 点学习英语 90 分钟。',
    date_context: '2026-04-23',
  },
  {
    label: '晨间阅读',
    text: '后天早上 7 点安排 45 分钟晨间阅读。',
    date_context: '2026-04-25',
  },
]

const planSamples: PlanSample[] = [
  {
    label: '今晚学习+健身',
    user_input: '帮我把今天剩下的学习任务和晚上的健身安排好，最好 23:00 前结束。',
    date: '2026-04-23',
    include_habits: true,
    option_count: 2,
  },
  {
    label: '考前冲刺',
    user_input: '我今晚想集中复习数学和英语，再留一点放松时间。',
    date: '2026-04-23',
    include_habits: true,
    option_count: 3,
  },
  {
    label: '轻量工作日',
    user_input: '今天比较忙，请给我一个保守一点的安排方案，留出机动时间。',
    date: '2026-04-23',
    include_habits: false,
    option_count: 2,
  },
]

const router = useRouter()
const appStore = useAppStore()
const aiStore = useAiStore()
const detailVisible = ref(false)
const parseApplyDialogVisible = ref(false)
const workspaceErrorMessage = ref('')
const detailErrorMessage = ref('')
const logKeyword = ref('')
const parseSectionRef = ref<HTMLElement | null>(null)
const planSectionRef = ref<HTMLElement | null>(null)
let removeRefreshListener: (() => void) | null = null

const connectionSummary = computed(() => {
  if (!aiStore.connectionState) {
    return '未检测'
  }
  return aiStore.connectionState.ok ? '连接正常' : '连接失败'
})

const connectionCheckedAt = computed(() => {
  if (!aiStore.connectionState) {
    return '--'
  }
  return formatDateTime(aiStore.connectionState.checked_at)
})

const modelUsage = computed(() => resolveAiModelUsage(aiStore.aiConfig))
const formattedContext = computed(() => formatAiLogJson(aiStore.selectedLog?.context_json))
const formattedOutput = computed(() => formatAiLogJson(aiStore.selectedLog?.ai_output_json))
const retryDraft = computed(() => (aiStore.selectedLog ? buildAiRetryDraft(aiStore.selectedLog) : null))
const parseFeedback = computed(() => (aiStore.lastApplyFeedback?.kind === 'parse' ? aiStore.lastApplyFeedback : null))
const planFeedback = computed(() => (aiStore.lastApplyFeedback?.kind === 'plan' ? aiStore.lastApplyFeedback : null))
const detailTitle = computed(() => (aiStore.selectedLog ? `AI 日志详情 #${aiStore.selectedLog.id}` : 'AI 日志详情'))
const filteredLogs = computed(() => {
  const keyword = logKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return aiStore.logs
  }

  return aiStore.logs.filter((log) =>
    [log.user_input, log.error_message, log.provider, log.model_name]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword)),
  )
})

function canRetry(log: AiLog): boolean {
  return buildAiRetryDraft(log) !== null
}

function fillParseSample(sample: ParseSample): void {
  aiStore.parseDraft.text = sample.text
  aiStore.parseDraft.date_context = sample.date_context
  aiStore.clearApplyFeedback('parse')
}

function fillPlanSample(sample: PlanSample): void {
  aiStore.planDraft.date = sample.date
  aiStore.planDraft.user_input = sample.user_input
  aiStore.planDraft.include_habits = sample.include_habits
  aiStore.planDraft.option_count = sample.option_count
  aiStore.clearApplyFeedback('plan')
}

function scrollToSection(kind: 'parse' | 'plan'): void {
  const target = kind === 'parse' ? parseSectionRef.value : planSectionRef.value
  nextTick(() => {
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

async function handleRefresh(): Promise<void> {
  workspaceErrorMessage.value = ''
  const results = await Promise.allSettled([aiStore.loadConfig(), aiStore.loadLogs(), appStore.refreshRuntimeState()])
  if (results.some((item) => item.status === 'rejected')) {
    workspaceErrorMessage.value = '工作区有部分数据刷新失败，请检查后端服务和 AI 配置后重试。'
  }
}

async function handleTestConnection(): Promise<void> {
  try {
    await aiStore.testConnection()
  } catch {
    // API client already shows a user-facing error message.
  }
}

async function handleParse(): Promise<void> {
  if (!aiStore.parseDraft.text.trim()) {
    notifyError('请输入要解析的自然语言内容')
    return
  }
  try {
    await aiStore.runParse()
  } catch {
    // Keep the current draft so the user can retry after fixing the issue.
  }
}

async function handleApplyParse(): Promise<void> {
  if (!aiStore.parseResult) {
    return
  }
  parseApplyDialogVisible.value = true
}

async function handleApplyParseActions(actions: AiParseAction[]): Promise<void> {
  try {
    await aiStore.applyParseResult(actions)
    parseApplyDialogVisible.value = false
  } catch {
    // Preserve the current preview for retry.
  }
}

async function handlePlan(): Promise<void> {
  if (!aiStore.planDraft.user_input.trim()) {
    notifyError('请输入要规划的需求')
    return
  }
  try {
    await aiStore.runPlan()
  } catch {
    // Keep the current draft so the user can retry after fixing the issue.
  }
}

async function handleApplyPlan(index: number): Promise<void> {
  try {
    await aiStore.applyPlanResult(index)
  } catch {
    // Preserve the current preview for retry.
  }
}

async function copyParseJson(): Promise<void> {
  if (!aiStore.parseResult) {
    return
  }
  await copyText(JSON.stringify(aiStore.parseResult.actions, null, 2))
  notifySuccess('解析结果 JSON 已复制')
}

async function copyPlanJson(): Promise<void> {
  if (!aiStore.planResult) {
    return
  }
  await copyText(JSON.stringify(aiStore.planResult.plan_options, null, 2))
  notifySuccess('规划结果 JSON 已复制')
}

async function handleFilterChange(): Promise<void> {
  await aiStore.loadLogs(1)
}

async function openLogDetail(logId: number): Promise<void> {
  detailVisible.value = true
  detailErrorMessage.value = ''
  try {
    await aiStore.loadLogDetail(logId)
  } catch (error) {
    detailErrorMessage.value = error instanceof Error ? error.message : 'AI 日志详情加载失败'
  }
}

function handleRetry(log: AiLog): void {
  const draft = aiStore.applyRetryDraft(log)
  detailVisible.value = false
  if (draft) {
    scrollToSection(draft.kind)
  }
}

function retrySelectedLog(): void {
  if (!aiStore.selectedLog) {
    return
  }
  const draft = aiStore.applyRetryDraft(aiStore.selectedLog)
  detailVisible.value = false
  if (draft) {
    scrollToSection(draft.kind)
  }
}

async function handleDelete(log: AiLog): Promise<void> {
  const confirmed = await confirmAction(`确定删除 AI 日志 #${log.id} 吗？`)
  if (!confirmed) {
    return
  }
  try {
    await aiStore.removeLog(log.id)
  } catch {
    // API client already shows a user-facing error message.
  }
}

async function copyUserInput(): Promise<void> {
  if (!aiStore.selectedLog) {
    return
  }
  await copyText(aiStore.selectedLog.user_input)
  notifySuccess('原始输入已复制')
}

async function copyContextJson(): Promise<void> {
  await copyText(formattedContext.value)
  notifySuccess('Context JSON 已复制')
}

async function copyOutputJson(): Promise<void> {
  await copyText(formattedOutput.value)
  notifySuccess('AI Output JSON 已复制')
}

function exportSelectedLog(): void {
  if (!aiStore.selectedLog) {
    return
  }
  downloadJsonFile(
    `ai-log-${aiStore.selectedLog.id}-${aiStore.selectedLog.log_type}.json`,
    buildAiLogExportPayload(aiStore.selectedLog),
  )
  notifySuccess('AI 日志已导出')
}

onMounted(async () => {
  await handleRefresh()
  removeRefreshListener = listenPageRefresh(handleRefresh)
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>

<style scoped>
.ai-diagnostics-grid {
  margin-bottom: 18px;
}

.ai-diagnostics-meta {
  display: grid;
  gap: 10px 22px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.ai-connection-alert {
  margin-top: 16px;
}

.ai-workspace-grid {
  align-items: start;
}

.panel-header-actions {
  justify-content: space-between;
  width: 100%;
}

.sample-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.sample-chip {
  padding: 0 4px;
  font-weight: 600;
}

.ai-preview-card {
  display: grid;
  gap: 6px;
}

.preview-card-header {
  justify-content: space-between;
  width: 100%;
}

.log-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.log-meta-row {
  margin-bottom: 14px;
}

.logs-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-card-subtle);
}

.drawer-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .log-toolbar {
    width: 100%;
  }
}
</style>
