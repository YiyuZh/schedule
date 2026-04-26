<template>
  <el-card class="panel-card">
    <template #header>
      <div class="inline-actions" style="justify-content: space-between; width: 100%;">
        <strong>当日时间线</strong>
        <span class="muted-text">{{ items.length }} 项</span>
      </div>
    </template>

    <LoadingBlock v-if="loading" text="正在整理时间线..." />
    <EmptyState
      v-else-if="items.length === 0"
      title="这一天还没有安排"
      description="可以先新建事件，或导入课程后再查看完整时间线。"
      icon="时间"
    />
    <div v-else class="timeline-stack">
      <div
        v-for="item in normalizedItems"
        :key="`${item.item_type}-${item.id}-${item.start_time}`"
        class="timeline-row"
      >
        <div class="timeline-time">
          <strong>{{ item.start_time }}</strong>
          <span>{{ item.end_time }}</span>
        </div>
        <div class="timeline-line">
          <span />
        </div>
        <div class="timeline-card">
          <div class="inline-actions" style="justify-content: space-between; width: 100%;">
            <strong>{{ item.title }}</strong>
            <span
              :class="[
                'status-pill',
                item.item_type === 'event' ? 'is-primary' : item.item_type === 'course' ? 'is-success' : 'is-warning',
              ]"
            >
              {{ itemTypeLabelMap[item.item_type] }}
            </span>
          </div>
          <div class="muted-text">{{ item.category || item.source }}</div>
          <div v-if="item.detail" class="soft-text">{{ item.detail }}</div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import EmptyState from '@/components/common/EmptyState.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import type { TimelineItem } from '@/types/event'

const props = defineProps<{
  items: TimelineItem[]
  loading?: boolean
}>()

const itemTypeLabelMap = {
  event: '事件',
  task: '任务',
  course: '课程',
}

const normalizedItems = computed(() =>
  [...props.items].sort((left, right) => `${left.start_time}${left.end_time}`.localeCompare(`${right.start_time}${right.end_time}`)),
)
</script>

<style scoped>
.timeline-stack {
  display: grid;
  gap: 16px;
}

.timeline-row {
  display: grid;
  grid-template-columns: 96px 20px minmax(0, 1fr);
  gap: 14px;
}

.timeline-time {
  display: grid;
  gap: 4px;
  justify-items: end;
  padding-top: 6px;
}

.timeline-time strong {
  font-size: 16px;
}

.timeline-time span {
  color: var(--app-text-muted);
  font-size: 13px;
}

.timeline-line {
  display: flex;
  justify-content: center;
}

.timeline-line span {
  width: 2px;
  border-radius: 999px;
  background: linear-gradient(180deg, #b7c7da, #d9e3ee);
}

.timeline-card {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-card-subtle);
}

@media (max-width: 760px) {
  .timeline-row {
    grid-template-columns: 1fr;
  }

  .timeline-time {
    justify-items: start;
    padding-top: 0;
  }

  .timeline-line {
    display: none;
  }
}
</style>
