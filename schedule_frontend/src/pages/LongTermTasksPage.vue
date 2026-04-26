<template>
  <section class="page-grid">
    <PageHeader
      title="长期任务"
      description="管理跨周、跨月的目标，并把子任务拆到今日任务中执行。"
      eyebrow="Long Term"
    >
      <template #actions>
        <el-select v-model="longTermStore.statusFilter" class="topbar-select" @change="handleRefresh">
          <el-option label="全部状态" value="all" />
          <el-option label="进行中" value="active" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已完成" value="completed" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-button class="topbar-button" @click="handleRefresh">刷新</el-button>
        <el-button type="primary" class="topbar-button" @click="openCreateTask">新建长期任务</el-button>
      </template>
    </PageHeader>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      closable
      @close="errorMessage = ''"
    />

    <div class="summary-grid">
      <div class="summary-tile">
        <span class="summary-title">长期任务总数</span>
        <strong>{{ longTermStore.tasks.length }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">进行中</span>
        <strong>{{ longTermStore.activeCount }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">已完成</span>
        <strong>{{ longTermStore.completedCount }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">平均进度</span>
        <strong>{{ formatPercent(longTermStore.averageProgress) }}</strong>
      </div>
    </div>

    <div class="page-grid long-term-grid">
      <el-card class="panel-card long-term-list-card">
        <div class="table-toolbar long-term-toolbar">
          <el-input
            v-model="longTermStore.keyword"
            clearable
            placeholder="搜索长期任务"
            @keyup.enter="handleRefresh"
            @clear="handleRefresh"
          />
          <el-button @click="handleRefresh">搜索</el-button>
        </div>

        <LoadingBlock v-if="longTermStore.loading" text="正在加载长期任务..." />
        <EmptyState
          v-else-if="!longTermStore.tasks.length"
          title="暂无长期任务"
          description="可以先创建一个本月目标，再拆解成可执行的子任务。"
          icon="目标"
        >
          <el-button type="primary" @click="openCreateTask">创建第一个长期任务</el-button>
        </EmptyState>
        <div v-else class="long-term-task-list">
          <button
            v-for="task in longTermStore.tasks"
            :key="task.id"
            type="button"
            :class="['long-term-task-card', task.id === longTermStore.selectedTaskId ? 'is-active' : '']"
            @click="handleSelectTask(task.id)"
          >
            <div class="long-term-card-header">
              <strong>{{ task.title }}</strong>
              <span :class="['status-pill', `is-${getLongTermStatusTone(task.status)}`]">
                {{ formatLongTermTaskStatus(task.status) }}
              </span>
            </div>
            <div class="long-term-card-meta">
              <span>{{ task.category }}</span>
              <span :class="['deadline-pill', `is-${getDueState(task).tone}`]">
                {{ getDueState(task).label }}
              </span>
            </div>
            <div class="long-term-progress-row">
              <span>{{ formatPercent(task.progress_percent) }}</span>
              <el-progress :percentage="task.progress_percent" :stroke-width="8" />
            </div>
            <div class="long-term-card-footer">
              <span>{{ task.completed_subtask_count }} / {{ task.subtask_count }} 子任务</span>
              <span>{{ formatPriorityLabel(task.priority) }}</span>
            </div>
          </button>
        </div>
      </el-card>

      <el-card class="panel-card">
        <template #header>
          <div v-if="selectedTask" class="inline-actions long-term-detail-header">
            <div>
              <strong>{{ selectedTask.title }}</strong>
              <div class="muted-text">
                {{ selectedTask.category }} · {{ formatLongTermDateRange(selectedTask.start_date, selectedTask.due_date) }}
              </div>
            </div>
            <div class="inline-actions">
              <el-button @click="handleEditTask(selectedTask)">编辑</el-button>
              <el-button type="primary" @click="openCreateSubtask">新增子任务</el-button>
            </div>
          </div>
          <strong v-else>长期任务详情</strong>
        </template>

        <template v-if="selectedTask">
          <div class="section-stack">
            <div class="long-term-detail-summary">
              <div>
                <span class="summary-title">当前进度</span>
                <strong>{{ formatPercent(selectedTask.progress_percent) }}</strong>
              </div>
              <div>
                <span class="summary-title">状态</span>
                <strong>{{ formatLongTermTaskStatus(selectedTask.status) }}</strong>
              </div>
              <div>
                <span class="summary-title">截止提醒</span>
                <strong>{{ getDueState(selectedTask).label }}</strong>
              </div>
              <div>
                <span class="summary-title">优先级</span>
                <strong>{{ formatPriorityLabel(selectedTask.priority) }}</strong>
              </div>
            </div>

            <p v-if="selectedTask.description" class="long-term-description">{{ selectedTask.description }}</p>

            <div class="inline-actions">
              <el-button v-if="selectedTask.status !== 'active'" @click="handleChangeSelectedTaskStatus('active')">
                恢复进行
              </el-button>
              <el-button v-if="selectedTask.status === 'active'" @click="handleChangeSelectedTaskStatus('paused')">
                暂停
              </el-button>
              <el-button v-if="selectedTask.status !== 'completed'" @click="handleChangeSelectedTaskStatus('completed')">
                标记完成
              </el-button>
              <el-button v-if="selectedTask.status !== 'archived'" @click="handleChangeSelectedTaskStatus('archived')">
                归档
              </el-button>
              <el-button type="danger" plain @click="handleRemoveTask(selectedTask)">删除</el-button>
            </div>

            <div class="subtask-section-title">
              <div>
                <strong>子任务拆解</strong>
                <div class="muted-text">
                  已完成 {{ selectedTask.completed_subtask_count }} / {{ selectedTask.subtask_count }}，可把子任务生成今日任务后执行。
                </div>
              </div>
              <el-button @click="openCreateSubtask">新增子任务</el-button>
            </div>

            <el-table :data="longTermStore.subtasks" v-loading="longTermStore.subtasksLoading" border>
              <el-table-column label="完成" width="76">
                <template #default="{ row }">
                  <el-checkbox :model-value="row.status === 'completed'" @change="handleToggleSubtask(row)" />
                </template>
              </el-table-column>
              <el-table-column prop="title" label="子任务" min-width="220">
                <template #default="{ row }">
                  <div class="subtask-title-cell">
                    <div class="inline-actions">
                      <strong>{{ row.title }}</strong>
                      <el-tag v-if="row.linked_daily_task_id" size="small" type="success">已生成今日任务</el-tag>
                    </div>
                    <span class="muted-text">
                      {{ row.is_study ? '学习科目' : '分类' }}：{{ row.category }}
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" min-width="110">
                <template #default="{ row }">
                  <span :class="['status-pill', `is-${getLongTermSubtaskStatusTone(row.status)}`]">
                    {{ formatLongTermSubtaskStatus(row.status) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="计划时长" min-width="110">
                <template #default="{ row }">
                  {{ formatDurationMinutes(row.planned_duration_minutes) }}
                </template>
              </el-table-column>
              <el-table-column label="截止日期" min-width="130">
                <template #default="{ row }">
                  <span :class="['deadline-pill', `is-${getSubtaskDueState(row).tone}`]">
                    {{ getSubtaskDueState(row).label }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="260" fixed="right">
                <template #default="{ row }">
                  <div class="inline-actions">
                    <el-button link @click="handleEditSubtask(row)">编辑</el-button>
                    <el-button link @click="handleCreateDailyTask(row.id)">
                      {{ row.linked_daily_task_id ? '查看今日任务' : '生成今日任务' }}
                    </el-button>
                    <el-button link type="danger" @click="handleRemoveSubtask(row)">删除</el-button>
                  </div>
                </template>
              </el-table-column>
              <template #empty>
                <EmptyState
                  title="还没有子任务"
                  description="把长期目标拆成今天能执行的小步骤，会更容易推进。"
                  icon="拆"
                >
                  <el-button type="primary" @click="openCreateSubtask">新增子任务</el-button>
                </EmptyState>
              </template>
            </el-table>
          </div>
        </template>

        <EmptyState
          v-else
          title="请选择长期任务"
          description="左侧选择一个长期目标后，可以在这里管理子任务。"
          icon="目标"
        />
      </el-card>
    </div>

    <LongTermTaskEditorDialog
      v-model="taskDialogVisible"
      :task="editingTask"
      @save="handleSaveTask"
    />

    <LongTermSubtaskEditorDialog
      v-model="subtaskDialogVisible"
      :subtask="editingSubtask"
      @save="handleSaveSubtask"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/common/EmptyState.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LongTermSubtaskEditorDialog from '@/components/long-term/LongTermSubtaskEditorDialog.vue'
import LongTermTaskEditorDialog from '@/components/long-term/LongTermTaskEditorDialog.vue'
import { useLongTermTasksStore } from '@/stores/longTermTasks'
import type {
  LongTermSubtask,
  LongTermSubtaskPayload,
  LongTermTask,
  LongTermTaskPayload,
  LongTermTaskStatus,
} from '@/types/longTermTask'
import { todayDateString } from '@/utils/date'
import { formatDurationMinutes, formatPercent, formatPriorityLabel } from '@/utils/format'
import {
  formatLongTermDateRange,
  formatLongTermSubtaskStatus,
  formatLongTermTaskStatus,
  getLongTermStatusTone,
  getLongTermSubtaskStatusTone,
} from '@/utils/longTermTask'
import { confirmAction, notifyError } from '@/utils/message'
import { listenPageRefresh } from '@/utils/pageEvents'

type DueTone = 'success' | 'warning' | 'danger' | 'neutral'
type DueState = {
  label: string
  tone: DueTone
}

const route = useRoute()
const router = useRouter()
const longTermStore = useLongTermTasksStore()
const taskDialogVisible = ref(false)
const subtaskDialogVisible = ref(false)
const editingTask = ref<LongTermTask | null>(null)
const editingSubtask = ref<LongTermSubtask | null>(null)
const errorMessage = ref('')
let removeRefreshListener: (() => void) | null = null

const selectedTask = computed(() => longTermStore.selectedTask)

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}

async function runPageAction(action: () => Promise<unknown>, fallback = '操作失败，请稍后重试'): Promise<void> {
  errorMessage.value = ''
  try {
    await action()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, fallback)
    notifyError(errorMessage.value)
  }
}

function getDaysUntil(dateString: string): number {
  const today = new Date(`${todayDateString()}T00:00:00`).getTime()
  const target = new Date(`${dateString}T00:00:00`).getTime()
  return Math.ceil((target - today) / 86_400_000)
}

function formatDueState(dueDate?: string | null, isDone = false): DueState {
  if (isDone) {
    return { label: '已完成', tone: 'success' }
  }

  if (!dueDate) {
    return { label: '未设置截止', tone: 'neutral' }
  }

  const days = getDaysUntil(dueDate)
  if (days < 0) {
    return { label: `已逾期 ${Math.abs(days)} 天`, tone: 'danger' }
  }
  if (days === 0) {
    return { label: '今天截止', tone: 'warning' }
  }
  if (days <= 3) {
    return { label: `${days} 天后截止`, tone: 'warning' }
  }
  return { label: dueDate, tone: 'success' }
}

function getDueState(task: LongTermTask): DueState {
  return formatDueState(task.due_date, task.status === 'completed')
}

function getSubtaskDueState(subtask: LongTermSubtask): DueState {
  return formatDueState(subtask.due_date, subtask.status === 'completed')
}

async function handleRefresh(): Promise<void> {
  await runPageAction(() => longTermStore.loadDashboard(), '加载长期任务失败')
}

async function handleSelectTask(taskId: number): Promise<void> {
  await runPageAction(() => longTermStore.selectTask(taskId), '加载子任务失败')
}

function openCreateTask(): void {
  editingTask.value = null
  taskDialogVisible.value = true
}

function handleEditTask(task: LongTermTask): void {
  editingTask.value = task
  taskDialogVisible.value = true
}

async function handleSaveTask(payload: LongTermTaskPayload, taskId?: number): Promise<void> {
  await runPageAction(() => longTermStore.saveTask(payload, taskId), '保存长期任务失败')
}

async function handleRemoveTask(task: LongTermTask): Promise<void> {
  const confirmed = await confirmAction(`确定删除长期任务“${task.title}”及其全部子任务吗？`)
  if (!confirmed) return
  await runPageAction(() => longTermStore.removeTask(task.id), '删除长期任务失败')
}

async function handleChangeSelectedTaskStatus(status: LongTermTaskStatus): Promise<void> {
  if (!selectedTask.value) {
    return
  }
  const taskId = selectedTask.value.id
  await runPageAction(() => longTermStore.changeTaskStatus(taskId, status), '更新长期任务状态失败')
}

function openCreateSubtask(): void {
  editingSubtask.value = null
  subtaskDialogVisible.value = true
}

function handleEditSubtask(subtask: LongTermSubtask): void {
  editingSubtask.value = subtask
  subtaskDialogVisible.value = true
}

async function handleSaveSubtask(payload: LongTermSubtaskPayload, subtaskId?: number): Promise<void> {
  await runPageAction(() => longTermStore.saveSubtask(payload, subtaskId), '保存子任务失败')
}

async function handleRemoveSubtask(subtask: LongTermSubtask): Promise<void> {
  const confirmed = await confirmAction(`确定删除子任务“${subtask.title}”吗？`)
  if (!confirmed) return
  await runPageAction(() => longTermStore.removeSubtask(subtask.id), '删除子任务失败')
}

async function handleToggleSubtask(subtask: LongTermSubtask): Promise<void> {
  await runPageAction(() => longTermStore.toggleSubtask(subtask), '更新子任务状态失败')
}

async function handleCreateDailyTask(subtaskId: number): Promise<void> {
  await runPageAction(async () => {
    await longTermStore.createDailyTask(subtaskId)
    await router.push('/today')
  }, '生成今日任务失败')
}

function consumeCreateQuery(): void {
  if (route.query.create !== '1') {
    return
  }
  openCreateTask()
  const { create: _create, ...restQuery } = route.query
  void router.replace({ path: '/long-term-tasks', query: restQuery })
}

onMounted(async () => {
  await handleRefresh()
  consumeCreateQuery()
  removeRefreshListener = listenPageRefresh(handleRefresh)
})

watch(() => route.query.create, consumeCreateQuery)

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>

<style scoped>
.topbar-select {
  width: 150px;
}

.long-term-grid {
  grid-template-columns: minmax(300px, 0.85fr) minmax(0, 1.6fr);
}

.long-term-list-card {
  min-height: 520px;
}

.long-term-toolbar {
  grid-template-columns: minmax(0, 1fr) 88px;
}

.long-term-task-list {
  display: grid;
  gap: 12px;
}

.long-term-task-card {
  display: grid;
  gap: 12px;
  width: 100%;
  padding: 16px;
  text-align: left;
  color: var(--app-text);
  background: #ffffff;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  cursor: pointer;
}

.long-term-task-card.is-active {
  border-color: var(--app-primary);
  box-shadow: inset 3px 0 0 var(--app-primary);
}

.long-term-card-header,
.long-term-card-footer,
.long-term-detail-header,
.long-term-card-meta,
.long-term-progress-row,
.subtask-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.long-term-card-header strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.long-term-card-meta,
.long-term-card-footer {
  color: var(--app-text-muted);
  font-size: 13px;
}

.long-term-progress-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  color: var(--app-text-muted);
  font-size: 13px;
  font-weight: 700;
}

.long-term-detail-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.long-term-detail-summary > div {
  padding: 14px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  background: #f8fbfd;
}

.long-term-detail-summary strong {
  display: block;
  margin-top: 6px;
  font-size: 20px;
}

.long-term-description {
  margin: 0;
  padding: 14px;
  color: var(--app-text-muted);
  background: #f8fbfd;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
}

.subtask-section-title {
  align-items: flex-start;
}

.subtask-title-cell {
  display: grid;
  gap: 4px;
}

.deadline-pill {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--app-border);
  color: var(--app-text-muted);
  background: #f8fbfd;
  font-size: 12px;
  font-weight: 700;
}

.deadline-pill.is-success {
  color: var(--app-success);
  background: var(--app-success-soft);
  border-color: transparent;
}

.deadline-pill.is-warning {
  color: var(--app-warning);
  background: var(--app-warning-soft);
  border-color: transparent;
}

.deadline-pill.is-danger {
  color: var(--app-danger);
  background: var(--app-danger-soft);
  border-color: transparent;
}

@media (max-width: 1200px) {
  .long-term-grid {
    grid-template-columns: 1fr;
  }
}
</style>
