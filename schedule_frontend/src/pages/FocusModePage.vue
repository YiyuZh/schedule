<template>
  <section class="app-focus-shell">
    <div class="focus-mode-frame">
      <div class="focus-mode-header">
        <div class="inline-actions">
          <el-button class="topbar-button" @click="handleBack">返回工作台</el-button>
        </div>
      </div>

      <el-card v-if="timerStore.currentTimer?.has_active_timer" class="panel-card focus-mode-card">
        <div class="focus-mode-card-body">
          <div class="focus-mode-tags">
            <span class="status-pill">{{ activeTask?.category || '学习任务' }}</span>
            <span class="status-pill is-primary">{{ activeTaskPriority }}</span>
          </div>

          <h1>{{ timerStore.currentTimer.task_title }}</h1>
          <div class="muted-text">专注进行中 · 已开启勿扰通知</div>

          <div class="focus-ring">
            <div class="focus-ring-inner">
              <strong>{{ elapsedText }}</strong>
            </div>
            <svg class="focus-ring-svg" viewBox="0 0 320 320">
              <circle class="focus-ring-track" cx="160" cy="160" r="140" />
              <circle
                class="focus-ring-progress"
                cx="160"
                cy="160"
                r="140"
                :stroke-dasharray="ringLength"
                :stroke-dashoffset="ringOffset"
              />
            </svg>
          </div>

          <div class="focus-meta">
            <div>
              <label>目标时长</label>
              <strong>{{ plannedMinutesText }}</strong>
            </div>
            <div>
              <label>预计完成</label>
              <strong>{{ estimatedFinish }}</strong>
            </div>
          </div>

          <div class="focus-actions">
            <el-button circle @click="timerStore.discardTimer()">
              <el-icon><Close /></el-icon>
            </el-button>

            <el-button
              v-if="timerStore.currentTimer.status === 'running'"
              circle
              type="primary"
              @click="timerStore.pauseTimer()"
            >
              <el-icon><VideoPause /></el-icon>
            </el-button>
            <el-button
              v-else
              circle
              type="primary"
              @click="timerStore.resumeTimer()"
            >
              <el-icon><VideoPlay /></el-icon>
            </el-button>

            <el-button circle @click="handleComplete">
              <el-icon><Check /></el-icon>
            </el-button>
          </div>
        </div>
      </el-card>

      <el-card v-else class="panel-card focus-empty-card">
        <div class="section-stack" style="align-items: center; text-align: center;">
          <h2>当前没有进行中的专注任务</h2>
          <p class="muted-text">返回今日工作台，选择一个学习任务开始进入沉浸式专注。</p>
          <el-button type="primary" @click="router.push('/today')">返回今日工作台</el-button>
        </div>
      </el-card>

      <TimerCompletionDialog
        v-if="completedSession && completedTask"
        v-model="completionDialogVisible"
        :task-title="completedTask.title"
        :actual-minutes="actualMinutes"
        :planned-minutes="plannedMinutes"
        :initial-note="completedSession.note"
        @save="handleSave"
        @continue="handleContinue"
        @new-task="openNewTask"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Check, Close, VideoPause, VideoPlay } from '@element-plus/icons-vue'

import TimerCompletionDialog from '@/components/timer/TimerCompletionDialog.vue'
import { useTimerCompletion } from '@/composables/useTimerCompletion'
import { fetchDailyTask } from '@/api/dailyTasks'
import { useTimerStore } from '@/stores/timer'
import type { DailyTask } from '@/types/dailyTask'
import { formatDurationCompact, formatSeconds } from '@/utils/format'

const router = useRouter()
const timerStore = useTimerStore()
const {
  dialogVisible: completionDialogVisible,
  session: completedSession,
  task: completedTask,
  actualMinutes,
  plannedMinutes: completionPlannedMinutes,
  stopAndOpenDialog,
  saveNote,
  continueTiming,
  openNewTask,
} = useTimerCompletion()

const activeTask = ref<DailyTask | null>(null)
const now = ref(Date.now())
let intervalId: number | null = null

const elapsedSeconds = computed(() => {
  const timer = timerStore.currentTimer
  if (!timer?.has_active_timer) {
    return 0
  }

  const baseSeconds = timer.accumulated_seconds || 0
  if (timer.status !== 'running' || !timer.started_at) {
    return baseSeconds
  }

  const startedAt = new Date(timer.started_at.replace(' ', 'T')).getTime()
  return baseSeconds + Math.max(0, Math.floor((now.value - startedAt) / 1000))
})

const elapsedText = computed(() => formatSeconds(elapsedSeconds.value))
const plannedMinutes = computed(() => activeTask.value?.planned_duration_minutes || completionPlannedMinutes.value || 0)
const plannedMinutesText = computed(() => formatDurationCompact(plannedMinutes.value))
const progress = computed(() => {
  if (!plannedMinutes.value) {
    return elapsedSeconds.value > 0 ? 100 : 0
  }
  return Math.min(100, Math.round((elapsedSeconds.value / 60 / plannedMinutes.value) * 100))
})
const ringLength = 2 * Math.PI * 140
const ringOffset = computed(() => ringLength * (1 - progress.value / 100))
const activeTaskPriority = computed(() => {
  if (!activeTask.value) {
    return '高优先级'
  }
  return activeTask.value.priority >= 5 ? '高优先级' : activeTask.value.priority >= 3 ? '中优先级' : '低优先级'
})
const estimatedFinish = computed(() => {
  if (!plannedMinutes.value) {
    return '--'
  }
  const remainingMinutes = Math.max(0, plannedMinutes.value - Math.round(elapsedSeconds.value / 60))
  const target = new Date()
  target.setMinutes(target.getMinutes() + remainingMinutes)
  return `${String(target.getHours()).padStart(2, '0')}:${String(target.getMinutes()).padStart(2, '0')}`
})

async function loadActiveTask(): Promise<void> {
  await timerStore.loadCurrentTimer()
  if (!timerStore.currentTimer?.task_id) {
    activeTask.value = null
    return
  }
  activeTask.value = await fetchDailyTask(timerStore.currentTimer.task_id)
}

async function handleComplete(): Promise<void> {
  await stopAndOpenDialog(true)
  await loadActiveTask()
}

async function handleSave(note: string): Promise<void> {
  await saveNote(note)
  await loadActiveTask()
}

async function handleContinue(note: string): Promise<void> {
  await continueTiming(note)
  await loadActiveTask()
}

function handleBack(): void {
  void router.push('/today')
}

onMounted(async () => {
  await loadActiveTask()
  intervalId = window.setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onBeforeUnmount(() => {
  if (intervalId) {
    window.clearInterval(intervalId)
  }
})
</script>

<style scoped>
.focus-mode-frame {
  max-width: 1040px;
  margin: 0 auto;
}

.focus-mode-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 24px;
}

.focus-mode-card {
  min-height: calc(100vh - 140px);
}

.focus-mode-card-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 22px;
  text-align: center;
}

.focus-mode-tags {
  display: flex;
  gap: 12px;
}

.focus-mode-card-body h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.15;
  font-weight: 800;
}

.focus-ring {
  position: relative;
  width: 320px;
  height: 320px;
}

.focus-ring-inner {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  z-index: 1;
}

.focus-ring-inner strong {
  font-size: 86px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.06em;
}

.focus-ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.focus-ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 10;
}

.focus-ring-progress {
  fill: none;
  stroke: #dce6ff;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.4s ease;
}

.focus-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(160px, 1fr));
  gap: 40px;
}

.focus-meta label {
  display: block;
  margin-bottom: 10px;
  color: rgba(248, 249, 251, 0.68);
  font-size: 14px;
}

.focus-meta strong {
  font-size: 28px;
}

.focus-actions {
  display: grid;
  grid-template-columns: repeat(3, 84px);
  gap: 20px;
  margin-top: 12px;
}

.focus-actions :deep(.el-button) {
  width: 84px;
  height: 84px;
  border-radius: 20px !important;
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
}

.focus-actions :deep(.el-button--primary) {
  background: var(--app-primary) !important;
}

.focus-empty-card {
  max-width: 640px;
  margin: 80px auto 0;
}

@media (max-width: 760px) {
  .focus-mode-card-body h1 {
    font-size: 32px;
  }

  .focus-ring {
    width: 260px;
    height: 260px;
  }

  .focus-ring-inner strong {
    font-size: 64px;
  }

  .focus-meta {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
