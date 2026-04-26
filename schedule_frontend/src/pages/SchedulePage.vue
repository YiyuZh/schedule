<template>
  <section class="page-grid">
    <PageHeader
      title="日程规划"
      :description="`查看 ${selectedDate} 的时间线、事件安排、课程实例与 AI 规划建议。`"
      eyebrow="Schedule"
    >
      <template #actions>
        <el-button class="topbar-button" @click="shiftSelectedDate(-1)">前一天</el-button>
        <el-button class="topbar-button" @click="resetToday">回到今天</el-button>
        <el-date-picker
          v-model="selectedDate"
          type="date"
          value-format="YYYY-MM-DD"
          format="YYYY-MM-DD"
          @change="handleDateChange"
        />
        <el-button class="topbar-button" @click="router.push('/ai-workspace')">AI 工作区</el-button>
        <el-button type="primary" class="topbar-button" @click="openCreateDialog">新建事件</el-button>
      </template>
    </PageHeader>

    <div class="summary-grid">
      <div class="summary-tile">
        <span class="summary-title">时间线项目</span>
        <strong>{{ scheduleStore.timelineItems.length }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">事件数量</span>
        <strong>{{ scheduleStore.events.length }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">课程实例</span>
        <strong>{{ scheduleStore.courseOccurrences.length }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">冲突提醒</span>
        <strong>{{ scheduleStore.conflictResult?.conflict_items.length ?? 0 }}</strong>
      </div>
    </div>

    <el-alert
      v-if="scheduleStore.conflictResult?.has_conflict"
      type="warning"
      show-icon
      :closable="false"
      class="conflict-alert"
    >
      <template #title>
        检测到 {{ scheduleStore.conflictResult.conflict_items.length }} 个时间冲突，请在保存前确认安排。
      </template>
      <template #default>
        <div class="conflict-list">
          <div
            v-for="(item, index) in scheduleStore.conflictResult.conflict_items"
            :key="`${item.item_type}-${item.id}-${index}`"
            class="conflict-item"
          >
            <strong>{{ item.title }}</strong>
            <span>{{ item.start_time }} - {{ item.end_time }}</span>
            <span class="muted-text">{{ item.item_type }} / {{ item.detail || item.source }}</span>
          </div>
        </div>
      </template>
    </el-alert>

    <div class="page-grid grid-two schedule-main-grid">
      <div class="section-stack">
        <TimelineView :items="scheduleStore.timelineItems" :loading="scheduleStore.loading" />

        <el-card class="panel-card">
          <template #header>
            <div class="inline-actions" style="justify-content: space-between; width: 100%;">
              <strong>当日事件</strong>
              <span class="muted-text">{{ scheduleStore.events.length }} 项</span>
            </div>
          </template>

          <el-table :data="scheduleStore.events" v-loading="scheduleStore.loading" border>
            <el-table-column prop="title" label="标题" min-width="160" />
            <el-table-column label="时间" min-width="150">
              <template #default="{ row }">
                {{ formatTimeRange(row.start_time, row.end_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="location" label="地点" min-width="120" />
            <el-table-column label="状态" min-width="110">
              <template #default="{ row }">
                <span class="status-pill">{{ formatEventStatusLabel(row.status) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="inline-actions">
                  <el-button link @click="handleEdit(row)">编辑</el-button>
                  <el-button link type="danger" @click="handleRemove(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <div class="inline-actions" style="justify-content: space-between; width: 100%;">
              <strong>课程实例</strong>
              <span class="muted-text">{{ scheduleStore.courseOccurrences.length }} 项</span>
            </div>
          </template>

          <el-table :data="scheduleStore.courseOccurrences" v-loading="scheduleStore.loading" border>
            <el-table-column prop="course_name" label="课程" min-width="160" />
            <el-table-column label="时间" min-width="140">
              <template #default="{ row }">
                {{ row.start_time }} - {{ row.end_time }}
              </template>
            </el-table-column>
            <el-table-column prop="location" label="地点" min-width="120" />
            <el-table-column prop="teacher" label="教师" min-width="120" />
            <el-table-column prop="week_index" label="周次" min-width="90" />
          </el-table>
        </el-card>
      </div>

      <AiPlanPanel :date="selectedDate" @applied="loadSchedule" />
    </div>

    <EventEditorDialog
      v-model="dialogVisible"
      :event="editingEvent"
      :date="selectedDate"
      @save="handleSave"
    />
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import PageHeader from '@/components/common/PageHeader.vue'
import AiPlanPanel from '@/components/schedule/AiPlanPanel.vue'
import EventEditorDialog from '@/components/schedule/EventEditorDialog.vue'
import TimelineView from '@/components/schedule/TimelineView.vue'
import { useAppStore } from '@/stores/app'
import { useScheduleStore } from '@/stores/schedule'
import type { EventItem, EventPayload } from '@/types/event'
import { shiftDate, todayDateString } from '@/utils/date'
import { formatEventStatusLabel, formatTimeRange } from '@/utils/format'
import { confirmAction } from '@/utils/message'
import { listenPageRefresh } from '@/utils/pageEvents'

const router = useRouter()
const appStore = useAppStore()
const scheduleStore = useScheduleStore()

const selectedDate = ref(appStore.currentDate)
const dialogVisible = ref(false)
const editingEvent = ref<EventItem | null>(null)
let removeRefreshListener: (() => void) | null = null

async function loadSchedule(): Promise<void> {
  appStore.setCurrentDate(selectedDate.value)
  await scheduleStore.loadSchedule(selectedDate.value)
}

async function handleDateChange(): Promise<void> {
  await loadSchedule()
}

async function shiftSelectedDate(offsetDays: number): Promise<void> {
  selectedDate.value = shiftDate(selectedDate.value, offsetDays)
  await loadSchedule()
}

async function resetToday(): Promise<void> {
  selectedDate.value = todayDateString()
  await loadSchedule()
}

function openCreateDialog(): void {
  editingEvent.value = null
  dialogVisible.value = true
}

function handleEdit(event: EventItem): void {
  editingEvent.value = event
  dialogVisible.value = true
}

async function handleSave(payload: EventPayload, eventId?: number): Promise<void> {
  if (payload.start_time && payload.end_time) {
    const result = await scheduleStore.detectConflict({
      event_date: payload.event_date,
      start_time: payload.start_time,
      end_time: payload.end_time,
      exclude_event_id: eventId ?? null,
    })

    if (result.has_conflict) {
      const confirmed = await confirmAction('该时间段存在冲突，仍然继续保存吗？')
      if (!confirmed) {
        return
      }
    }
  }

  await scheduleStore.saveEvent(payload, eventId)
}

async function handleRemove(event: EventItem): Promise<void> {
  const confirmed = await confirmAction(`确定删除事件“${event.title}”吗？`)
  if (!confirmed) {
    return
  }

  await scheduleStore.removeEvent(event)
}

watch(
  () => appStore.currentDate,
  (value) => {
    if (value && value !== selectedDate.value) {
      selectedDate.value = value
    }
  },
)

onMounted(async () => {
  await loadSchedule()
  removeRefreshListener = listenPageRefresh(loadSchedule)
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>

<style scoped>
.schedule-main-grid {
  align-items: start;
}

.conflict-alert {
  margin-top: -4px;
}

.conflict-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.conflict-item {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.56);
}
</style>
