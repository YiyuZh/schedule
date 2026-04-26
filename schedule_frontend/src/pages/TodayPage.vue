<template>
  <section class="page-grid">
    <PageHeader
      title="今日任务"
      :description="`当前查看 ${fullDateLabel} 的任务安排与专注进度。`"
      eyebrow="Today"
    >
      <template #actions>
        <el-button class="topbar-button" @click="moveDate(-1)">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <el-button class="topbar-button" @click="resetToday">回到今天</el-button>
        <el-button class="topbar-button" @click="moveDate(1)">
          <el-icon><ArrowRight /></el-icon>
        </el-button>
        <el-button type="primary" class="topbar-button" @click="handleRefreshTemplates">
          刷新今日模板任务
        </el-button>
        <el-button class="topbar-button" @click="router.push('/ai-workspace')">
          AI 工作区
        </el-button>
      </template>
    </PageHeader>

    <div class="summary-grid">
      <div class="summary-tile">
        <span class="summary-title">今日任务总数</span>
        <strong>{{ tasksStore.todaySummary?.total_count ?? 0 }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">已完成</span>
        <strong>{{ tasksStore.todaySummary?.completed_count ?? 0 }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">专注学习时长</span>
        <strong>{{ focusMinutesLabel }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">完成率</span>
        <strong>{{ formatPercent(tasksStore.todaySummary?.completion_rate ?? 0) }}</strong>
      </div>
    </div>

    <div class="page-grid grid-two">
      <div class="section-stack">
        <AiQuickInputPanel :date="currentDate" @applied="loadPageData" />

        <TaskList
          :tasks="tasksStore.todayTasks"
          :loading="tasksStore.tasksLoading"
          :active-timer-task-id="timerStore.currentTimer?.task_id ?? null"
          @edit="handleEditTask"
          @remove="handleRemoveTask"
          @toggle="handleToggleTask"
          @start-timer="handleStartTimer"
        />
      </div>

      <div class="section-stack">
        <TimerPanel
          :study-tasks="tasksStore.studyTasks"
          @complete="handleCompleteTimer"
          @enter-focus="router.push('/focus-mode')"
        />

        <el-card class="panel-card ai-suggestion-card">
          <template #header>
            <div class="inline-actions" style="justify-content: space-between; width: 100%;">
              <strong>AI 日程建议</strong>
              <div class="inline-actions">
                <el-button link type="primary" @click="router.push('/schedule')">前往日程规划</el-button>
                <el-button link @click="router.push('/ai-workspace')">打开 AI 工作区</el-button>
              </div>
            </div>
          </template>

          <template v-if="scheduleStore.aiPlan?.plan_options?.length">
            <div class="section-stack">
              <div class="muted-text">
                AI 已经为当前日期生成 {{ scheduleStore.aiPlan.plan_options.length }} 个候选方案。
                你可以前往“日程规划”或“AI 工作区”查看详情并应用。
              </div>
              <div class="inline-actions">
                <el-button @click="scheduleStore.aiPlan = null">忽略</el-button>
                <el-button @click="router.push('/ai-workspace')">查看日志</el-button>
                <el-button type="primary" @click="router.push('/schedule')">查看方案</el-button>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="section-stack">
              <div class="muted-text">
                在上方输入自然语言，或前往“日程规划 / AI 工作区”生成当天的智能安排建议。
              </div>
              <div class="inline-actions">
                <el-button @click="router.push('/ai-workspace')">打开 AI 工作区</el-button>
                <el-button type="primary" @click="router.push('/schedule')">生成 AI 规划</el-button>
              </div>
            </div>
          </template>
        </el-card>
      </div>
    </div>

    <TaskEditorDialog
      v-model="dialogVisible"
      :task="editingTask"
      :date="currentDate"
      @save="handleSaveTask"
    />

    <TaskCompletionDialog
      v-if="completionTask"
      :model-value="manualCompletionVisible"
      :task-title="completionTask.title"
      :planned-minutes="completionTask.planned_duration_minutes"
      :is-study="completionTask.is_study"
      @update:model-value="handleManualCompletionDialogChange"
      @save="handleSaveTaskCompletion"
    />

    <TimerCompletionDialog
      v-if="completedSession && completedTask"
      v-model="completionDialogVisible"
      :task-title="completedTask.title"
      :actual-minutes="actualMinutes"
      :planned-minutes="plannedMinutes"
      :initial-note="completedSession.note"
      @save="handleSaveCompletion"
      @continue="handleContinueCompletion"
      @new-task="openNewTask"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

import { fetchStudyStatsOverview } from '@/api/studyStats'
import PageHeader from '@/components/common/PageHeader.vue'
import AiQuickInputPanel from '@/components/tasks/AiQuickInputPanel.vue'
import TaskCompletionDialog from '@/components/tasks/TaskCompletionDialog.vue'
import TaskEditorDialog from '@/components/tasks/TaskEditorDialog.vue'
import TaskList from '@/components/tasks/TaskList.vue'
import TimerCompletionDialog from '@/components/timer/TimerCompletionDialog.vue'
import TimerPanel from '@/components/timer/TimerPanel.vue'
import { useTimerCompletion } from '@/composables/useTimerCompletion'
import { useAppStore } from '@/stores/app'
import { useScheduleStore } from '@/stores/schedule'
import { useTasksStore } from '@/stores/tasks'
import { useTimerStore } from '@/stores/timer'
import type { DailyTask, DailyTaskCompletePayload, DailyTaskPayload } from '@/types/dailyTask'
import { formatDisplayDate, getWeekdayLabel, shiftDate, todayDateString } from '@/utils/date'
import { formatDurationCompact, formatPercent } from '@/utils/format'
import { confirmAction, notifyError } from '@/utils/message'
import { listenPageRefresh } from '@/utils/pageEvents'

const router = useRouter()
const appStore = useAppStore()
const tasksStore = useTasksStore()
const timerStore = useTimerStore()
const scheduleStore = useScheduleStore()
const {
  dialogVisible: completionDialogVisible,
  session: completedSession,
  task: completedTask,
  actualMinutes,
  plannedMinutes,
  stopAndOpenDialog,
  saveNote,
  continueTiming,
  openNewTask,
} = useTimerCompletion()

const dialogVisible = ref(false)
const editingTask = ref<DailyTask | null>(null)
const completionTask = ref<DailyTask | null>(null)
const manualCompletionVisible = ref(false)
const todayFocusMinutes = ref(0)
let removeRefreshListener: (() => void) | null = null

const currentDate = computed({
  get: () => appStore.currentDate,
  set: (value: string) => appStore.setCurrentDate(value),
})

const fullDateLabel = computed(() => `${formatDisplayDate(currentDate.value)} ${getWeekdayLabel(currentDate.value)}`)
const focusMinutesLabel = computed(() => formatDurationCompact(todayFocusMinutes.value))

async function loadFocusMinutes(): Promise<void> {
  const overview = await fetchStudyStatsOverview({
    start_date: currentDate.value,
    end_date: currentDate.value,
  })
  todayFocusMinutes.value = overview.query_total_minutes
}

async function loadPageData(): Promise<void> {
  await Promise.all([
    tasksStore.loadTodayDashboard(currentDate.value),
    timerStore.loadCurrentTimer(),
    loadFocusMinutes(),
  ])
}

async function handleRefreshTemplates(): Promise<void> {
  await tasksStore.refreshTodayTemplates(currentDate.value)
  await loadFocusMinutes()
}

function handleEditTask(task: DailyTask): void {
  editingTask.value = task
  dialogVisible.value = true
}

async function handleSaveTask(payload: DailyTaskPayload, taskId?: number): Promise<void> {
  await tasksStore.saveTask(payload, taskId)
  await loadPageData()
}

async function handleRemoveTask(task: DailyTask): Promise<void> {
  const confirmed = await confirmAction(`确定删除任务“${task.title}”吗？`)
  if (!confirmed) {
    return
  }

  await tasksStore.removeTask(task)
  await loadPageData()
}

async function handleToggleTask(task: DailyTask): Promise<void> {
  if (task.status === 'completed') {
    await tasksStore.uncompleteTask(task)
    await loadPageData()
    return
  }

  if (task.id === timerStore.currentTimer?.task_id && timerStore.currentTimer?.has_active_timer) {
    await stopAndOpenDialog(true)
    await loadPageData()
    return
  }

  completionTask.value = task
  manualCompletionVisible.value = true
}

async function handleSaveTaskCompletion(payload: DailyTaskCompletePayload): Promise<void> {
  if (!completionTask.value) {
    return
  }

  if (completionTask.value.is_study && payload.sync_study_session && !payload.actual_duration_minutes) {
    notifyError('学习任务同步到学习记录时，实际时长必须大于 0')
    return
  }

  await tasksStore.completeTask(completionTask.value, payload)
  handleManualCompletionDialogChange(false)
  await loadPageData()
}

function handleManualCompletionDialogChange(value: boolean): void {
  manualCompletionVisible.value = value
  if (!value) {
    completionTask.value = null
  }
}

async function handleStartTimer(task: DailyTask): Promise<void> {
  if (timerStore.currentTimer?.has_active_timer && timerStore.currentTimer.task_id !== task.id) {
    const confirmed = await confirmAction('当前已有进行中的计时，是否切换到新任务并保留当前记录？')
    if (!confirmed) {
      return
    }
    await timerStore.switchTimer(task.id, true)
    await loadPageData()
    return
  }

  if (!timerStore.currentTimer?.has_active_timer) {
    await timerStore.startTimer(task.id)
    await loadPageData()
  }
}

async function handleCompleteTimer(): Promise<void> {
  await stopAndOpenDialog(true)
  await loadPageData()
}

async function handleSaveCompletion(note: string): Promise<void> {
  await saveNote(note)
  await loadPageData()
}

async function handleContinueCompletion(note: string): Promise<void> {
  await continueTiming(note)
  await loadPageData()
}

async function moveDate(offsetDays: number): Promise<void> {
  currentDate.value = shiftDate(currentDate.value, offsetDays)
  await loadPageData()
}

async function resetToday(): Promise<void> {
  currentDate.value = todayDateString()
  await loadPageData()
}

onMounted(async () => {
  await loadPageData()
  removeRefreshListener = listenPageRefresh(loadPageData)
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>

<style scoped>
.ai-suggestion-card {
  border-top: 4px solid #4d6673 !important;
}
</style>
