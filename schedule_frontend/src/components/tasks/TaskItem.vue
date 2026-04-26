<template>
  <div class="task-row" :class="{ 'is-active': isActiveTimerTask, 'is-dimmed': task.status === 'completed' || task.status === 'skipped' }">
    <div class="task-row-main">
      <el-checkbox :model-value="task.status === 'completed'" @change="emit('toggle', task)" />

      <div class="task-row-content" @click="emit('edit', task)">
        <div class="task-row-title">{{ task.title }}</div>
        <div class="task-row-subtitle">
          <span>{{ task.category || '未分类' }}</span>
          <span> / </span>
          <span>{{ task.is_study ? '需要专注' : '普通任务' }}</span>
          <template v-if="task.end_time">
            <span> / </span>
            <span>{{ task.end_time }} 截止</span>
          </template>
          <template v-if="isFromLongTermTask">
            <span> / </span>
            <span>来自长期任务</span>
          </template>
        </div>
      </div>
    </div>

    <div class="task-row-meta">
      <el-tag v-if="isFromLongTermTask" class="task-chip-source" size="small">长期任务</el-tag>
      <el-tag v-if="task.is_study" class="task-chip task-chip-study">学习</el-tag>
      <span :class="['status-pill', `is-${getTaskStatusTone(task.status)}`]">{{ formatTaskStatusLabel(task.status) }}</span>
      <span :class="['task-chip', `is-${getPriorityTone(task.priority)}`]">{{ formatPriorityLabel(task.priority) }}</span>
      <span class="task-progress-text">{{ formatDurationCompact(task.actual_duration_minutes) }} / {{ formatDurationCompact(task.planned_duration_minutes) }}</span>
    </div>

    <div class="task-row-actions">
      <el-button
        v-if="task.is_study && task.status !== 'completed' && task.status !== 'skipped'"
        circle
        :type="isActiveTimerTask ? 'primary' : undefined"
        @click.stop="emit('startTimer', task)"
      >
        <el-icon><VideoPlay /></el-icon>
      </el-button>
      <el-button circle @click.stop="emit('edit', task)">
        <el-icon><Edit /></el-icon>
      </el-button>
      <el-button circle @click.stop="emit('remove', task)">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete, Edit, VideoPlay } from '@element-plus/icons-vue'

import type { DailyTask } from '@/types/dailyTask'
import {
  formatDurationCompact,
  formatPriorityLabel,
  formatTaskStatusLabel,
  getPriorityTone,
  getTaskStatusTone,
} from '@/utils/format'

const props = defineProps<{
  task: DailyTask
  isActiveTimerTask?: boolean
}>()

const isFromLongTermTask = computed(() => props.task.notes?.includes('来自长期任务子任务') ?? false)

const emit = defineEmits<{
  edit: [DailyTask]
  remove: [DailyTask]
  toggle: [DailyTask]
  startTimer: [DailyTask]
}>()
</script>

<style scoped>
.task-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 16px;
  align-items: center;
  min-height: 78px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--app-border);
  background: #fff;
}

.task-row.is-active {
  box-shadow: inset 3px 0 0 var(--app-primary);
}

.task-row.is-dimmed {
  color: var(--app-text-soft);
}

.task-row-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.task-row-content {
  min-width: 0;
  cursor: pointer;
}

.task-row-title {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}

.task-row-subtitle {
  margin-top: 6px;
  color: var(--app-text-muted);
  font-size: 14px;
}

.task-row-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.task-row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-progress-text {
  color: var(--app-text-muted);
  font-family:
    'Work Sans',
    'Segoe UI',
    sans-serif;
  font-size: 15px;
  min-width: 88px;
  text-align: right;
}

.task-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  min-width: 36px;
  padding: 0 10px;
  border-radius: 4px;
  border: 1px solid var(--app-border);
  color: var(--app-text-muted);
  font-size: 13px;
  font-weight: 700;
}

.task-chip-study {
  background: #d9edf7;
  color: #415d69;
  border-color: #d9edf7;
}

.task-chip-source {
  border-color: #d6e6f8;
  color: var(--app-primary-strong);
  background: var(--app-primary-soft);
  font-weight: 700;
}

.task-chip.is-danger {
  color: #b84d4d;
  background: #ffe8e8;
}

.task-chip.is-warning {
  color: #a66d2b;
  background: #fff2df;
}

.task-chip.is-success {
  color: #5f6974;
  background: #f1f3f5;
}

@media (max-width: 1100px) {
  .task-row {
    grid-template-columns: 1fr;
  }

  .task-row-meta,
  .task-row-actions {
    justify-content: flex-start;
  }

  .task-progress-text {
    text-align: left;
  }
}
</style>
