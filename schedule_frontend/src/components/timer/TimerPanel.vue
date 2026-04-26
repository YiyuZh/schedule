<template>
  <el-card class="panel-card timer-panel-card">
    <template #header>
      <div class="inline-actions" style="justify-content: space-between; width: 100%;">
        <strong>当前专注</strong>
        <span v-if="timerStore.currentTimer?.has_active_timer" class="status-pill is-primary">
          {{ formatTimerStatusLabel(timerStore.currentTimer.status) }}
        </span>
      </div>
    </template>

    <EmptyState
      v-if="!timerStore.currentTimer?.has_active_timer"
      title="当前没有进行中的专注"
      description="从今日任务中选择一个学习任务开始，或在这里快速启动。"
      icon="计时"
    >
      <div class="section-stack">
        <el-select v-model="selectedTaskId" class="full-width" placeholder="选择一个学习任务">
          <el-option v-for="task in studyTasks" :key="task.id" :label="task.title" :value="task.id" />
        </el-select>

        <div class="inline-actions">
          <el-button type="primary" :disabled="!selectedTaskId" :loading="timerStore.loading" @click="handleStart">
            开始专注
          </el-button>
          <el-button :disabled="!selectedTaskId" @click="emit('enterFocus')">进入专注模式</el-button>
        </div>
      </div>
    </EmptyState>

    <template v-else>
      <div class="timer-panel-body">
        <div class="timer-panel-title">{{ timerStore.currentTimer.task_title }}</div>
        <div class="timer-panel-meta">{{ activeTaskMeta }}</div>
        <div class="timer-panel-clock">{{ elapsedText }}</div>

        <div class="timer-progress">
          <div class="timer-progress-bar">
            <span :style="{ width: `${progress}%` }" />
          </div>
          <div class="timer-progress-meta">
            <span>{{ formatDurationCompact(elapsedMinutes) }}</span>
            <span>{{ plannedDurationText }}</span>
          </div>
        </div>

        <div class="timer-panel-actions">
          <el-button circle @click="timerStore.discardTimer()">
            <el-icon><Close /></el-icon>
          </el-button>

          <el-button
            v-if="timerStore.currentTimer.status === 'running'"
            circle
            type="primary"
            :loading="timerStore.loading"
            @click="timerStore.pauseTimer()"
          >
            <el-icon><VideoPause /></el-icon>
          </el-button>
          <el-button
            v-else
            circle
            type="primary"
            :loading="timerStore.loading"
            @click="timerStore.resumeTimer()"
          >
            <el-icon><VideoPlay /></el-icon>
          </el-button>

          <el-button circle @click="emit('complete')">
            <el-icon><Check /></el-icon>
          </el-button>
        </div>

        <div class="timer-panel-action-labels">
          <span>停止</span>
          <span>{{ timerStore.currentTimer.status === 'running' ? '暂停' : '恢复' }}</span>
          <span>完成</span>
        </div>

        <div class="inline-actions" style="justify-content: center;">
          <el-button link type="primary" @click="emit('enterFocus')">进入专注模式</el-button>
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Check, Close, VideoPause, VideoPlay } from '@element-plus/icons-vue'

import EmptyState from '@/components/common/EmptyState.vue'
import { useTimerStore } from '@/stores/timer'
import type { DailyTask } from '@/types/dailyTask'
import { formatDurationCompact, formatSeconds, formatTimerStatusLabel } from '@/utils/format'

const props = defineProps<{
  studyTasks: DailyTask[]
}>()

const emit = defineEmits<{
  complete: []
  enterFocus: []
}>()

const timerStore = useTimerStore()
const selectedTaskId = ref<number | null>(null)
const now = ref(Date.now())
let intervalId: number | null = null

const activeTask = computed(() => props.studyTasks.find((task) => task.id === timerStore.currentTimer?.task_id) || null)

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
  const dynamicSeconds = Math.max(0, Math.floor((now.value - startedAt) / 1000))
  return baseSeconds + dynamicSeconds
})

const elapsedText = computed(() => formatSeconds(elapsedSeconds.value))
const elapsedMinutes = computed(() => Math.max(0, Math.round(elapsedSeconds.value / 60)))
const progress = computed(() => {
  const planned = activeTask.value?.planned_duration_minutes || 0
  if (!planned) {
    return elapsedMinutes.value > 0 ? 100 : 0
  }
  return Math.min(100, Math.round((elapsedMinutes.value / planned) * 100))
})
const plannedDurationText = computed(() => `${activeTask.value?.planned_duration_minutes || 0}m 目标`)
const activeTaskMeta = computed(() => {
  if (!activeTask.value) {
    return '学习任务'
  }
  return `${activeTask.value.category || '未分类'} / ${activeTask.value.priority >= 5 ? '高优先级' : activeTask.value.priority >= 3 ? '中优先级' : '低优先级'}`
})

async function handleStart(): Promise<void> {
  if (!selectedTaskId.value) {
    return
  }
  await timerStore.startTimer(selectedTaskId.value)
}

onMounted(() => {
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
.timer-panel-card {
  min-height: 420px;
}

.timer-panel-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: center;
  text-align: center;
}

.timer-panel-title {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.3;
}

.timer-panel-meta {
  color: var(--app-text-muted);
  font-size: 15px;
}

.timer-panel-clock {
  font-size: 64px;
  line-height: 1;
  font-weight: 800;
  color: var(--app-primary);
  letter-spacing: -0.04em;
}

.timer-progress {
  width: 100%;
}

.timer-progress-bar {
  height: 8px;
  background: #e8edf3;
  border-radius: 999px;
  overflow: hidden;
}

.timer-progress-bar span {
  display: block;
  height: 100%;
  background: var(--app-primary);
  border-radius: 999px;
}

.timer-progress-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  color: var(--app-text-muted);
  font-size: 14px;
}

.timer-panel-actions {
  display: grid;
  grid-template-columns: repeat(3, 64px);
  gap: 18px;
}

.timer-panel-actions :deep(.el-button) {
  width: 64px;
  height: 64px;
}

.timer-panel-action-labels {
  display: grid;
  grid-template-columns: repeat(3, 64px);
  gap: 18px;
  color: var(--app-text-muted);
  font-size: 14px;
}
</style>
