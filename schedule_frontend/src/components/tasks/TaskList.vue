<template>
  <el-card class="panel-card">
    <template #header>
      <div class="task-list-header">
        <strong>任务清单</strong>
        <div class="task-list-controls">
          <el-select v-model="statusFilter" size="small" style="width: 128px;">
            <el-option label="全部状态" value="all" />
            <el-option label="待办" value="pending" />
            <el-option label="进行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="已跳过" value="skipped" />
          </el-select>

          <el-select v-model="sortMode" size="small" style="width: 144px;">
            <el-option label="默认排序" value="default" />
            <el-option label="优先级优先" value="priority" />
            <el-option label="截止时间优先" value="deadline" />
          </el-select>
        </div>
      </div>
    </template>

    <LoadingBlock v-if="loading" />

    <EmptyState
      v-else-if="filteredTasks.length === 0"
      title="当前没有任务"
      description="可以通过顶部新建任务，或使用 AI 快速输入生成结构化安排。"
      icon="任务"
    />

    <div v-else class="task-list-surface">
      <TaskItem
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
        :is-active-timer-task="activeTimerTaskId === task.id"
        @edit="emit('edit', $event)"
        @remove="emit('remove', $event)"
        @toggle="emit('toggle', $event)"
        @start-timer="emit('startTimer', $event)"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import EmptyState from '@/components/common/EmptyState.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import TaskItem from '@/components/tasks/TaskItem.vue'
import type { DailyTask, TaskStatus } from '@/types/dailyTask'

const props = defineProps<{
  tasks: DailyTask[]
  loading?: boolean
  activeTimerTaskId?: number | null
}>()

const emit = defineEmits<{
  edit: [DailyTask]
  remove: [DailyTask]
  toggle: [DailyTask]
  startTimer: [DailyTask]
}>()

const statusFilter = ref<'all' | TaskStatus>('all')
const sortMode = ref<'default' | 'priority' | 'deadline'>('default')

const filteredTasks = computed(() => {
  let nextTasks = [...props.tasks]

  if (statusFilter.value !== 'all') {
    nextTasks = nextTasks.filter((task) => task.status === statusFilter.value)
  }

  if (sortMode.value === 'priority') {
    nextTasks.sort((left, right) => right.priority - left.priority || left.sort_order - right.sort_order)
    return nextTasks
  }

  if (sortMode.value === 'deadline') {
    nextTasks.sort((left, right) => {
      const leftTime = left.end_time || '99:99'
      const rightTime = right.end_time || '99:99'
      return leftTime.localeCompare(rightTime) || left.sort_order - right.sort_order
    })
    return nextTasks
  }

  nextTasks.sort((left, right) => left.sort_order - right.sort_order || left.id - right.id)
  return nextTasks
})
</script>

<style scoped>
.task-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-list-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.task-list-surface {
  border: 1px solid var(--app-border);
  border-radius: 4px;
  overflow: hidden;
}

@media (max-width: 900px) {
  .task-list-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
