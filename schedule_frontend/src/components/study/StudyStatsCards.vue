<template>
  <div class="summary-grid">
    <div class="summary-tile">
      <span class="summary-title">今日学习</span>
      <strong>{{ formatDurationMinutes(overview?.today_minutes ?? 0) }}</strong>
    </div>
    <div class="summary-tile">
      <span class="summary-title">本周学习</span>
      <strong>{{ formatDurationMinutes(overview?.week_minutes ?? 0) }}</strong>
    </div>
    <div class="summary-tile">
      <span class="summary-title">本月学习</span>
      <strong>{{ formatDurationMinutes(overview?.month_minutes ?? 0) }}</strong>
    </div>
    <div class="summary-tile">
      <span class="summary-title">筛选区间总时长</span>
      <strong>{{ formatDurationMinutes(overview?.query_total_minutes ?? 0) }}</strong>
    </div>
    <div class="summary-tile">
      <span class="summary-title">累计学习</span>
      <strong>{{ formatDurationMinutes(overview?.total_minutes ?? 0) }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StudyStatsOverview } from '@/types/study'
import { formatDurationMinutes } from '@/utils/format'

defineProps<{
  overview: StudyStatsOverview | null
}>()
</script>
