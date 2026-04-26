<template>
  <div class="page-grid grid-two">
    <el-card class="panel-card">
      <template #header>
        <strong>按学习科目统计</strong>
      </template>

      <LoadingBlock v-if="loading" text="正在绘制学习科目统计..." />
      <EmptyState
        v-else-if="!categoryStats.length"
        title="暂无科目数据"
        description="当前筛选区间内还没有可统计的学习科目。"
        icon="图表"
      />
      <div v-else class="chart-shell chart-shell-wide">
        <div class="donut-layout">
          <div class="donut-chart" :style="{ background: categoryChart.gradient }">
            <div class="donut-center">
              <strong>{{ formatDurationMinutes(categoryChart.totalMinutes) }}</strong>
              <span class="muted-text">总时长</span>
            </div>
          </div>

          <div class="legend-list">
            <div v-for="item in categoryChart.items" :key="item.label" class="legend-item">
              <span class="legend-dot" :style="{ backgroundColor: item.color }" />
              <div class="legend-copy">
                <strong>{{ item.label }}</strong>
                <span class="muted-text">
                  {{ formatDurationMinutes(item.minutes) }} · {{ formatPercent(item.percent) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <strong>按日趋势</strong>
      </template>

      <LoadingBlock v-if="loading" text="正在绘制学习趋势..." />
      <EmptyState
        v-else-if="!dayStats.length"
        title="暂无趋势数据"
        description="当前筛选区间内还没有按日累计的学习记录。"
        icon="折线"
      />
      <div v-else class="chart-shell">
        <div class="bars-layout">
          <div v-for="item in dayChart.items" :key="item.sessionDate" class="bar-column">
            <span class="bar-value">{{ formatDurationCompact(item.minutes) }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{
                  height: `${item.heightPercent}%`,
                  backgroundColor: item.color,
                }"
              />
            </div>
            <span class="bar-label">{{ item.displayLabel }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import EmptyState from '@/components/common/EmptyState.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import type { StudyCategoryStat, StudyDayStat } from '@/types/study'
import { formatDurationCompact, formatDurationMinutes, formatPercent } from '@/utils/format'
import { buildStudyCategoryChart, buildStudyDayBars } from '@/utils/studyCharts'

const props = defineProps<{
  categoryStats: StudyCategoryStat[]
  dayStats: StudyDayStat[]
  loading?: boolean
}>()

const categoryChart = computed(() => buildStudyCategoryChart(props.categoryStats))
const dayChart = computed(() => buildStudyDayBars(props.dayStats))
</script>

<style scoped>
.chart-shell {
  width: 100%;
  min-height: 320px;
}

.chart-shell-wide {
  display: flex;
  align-items: center;
}

.donut-layout {
  display: grid;
  grid-template-columns: minmax(220px, 260px) 1fr;
  gap: 24px;
  align-items: center;
  width: 100%;
}

.donut-chart {
  width: 240px;
  height: 240px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin: 0 auto;
}

.donut-center {
  width: 138px;
  height: 138px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid #d6e0ea;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  display: grid;
  place-items: center;
  text-align: center;
  padding: 18px;
}

.donut-center strong {
  font-size: 18px;
  color: var(--app-text-color);
}

.legend-list {
  display: grid;
  gap: 12px;
}

.legend-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fbfd;
  border: 1px solid #d6e0ea;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  margin-top: 4px;
  flex-shrink: 0;
}

.legend-copy {
  display: grid;
  gap: 4px;
}

.bars-layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(56px, 1fr));
  gap: 14px;
  align-items: end;
  min-height: 320px;
}

.bar-column {
  display: grid;
  gap: 10px;
  justify-items: center;
}

.bar-value {
  font-size: 12px;
  color: var(--app-text-muted);
}

.bar-track {
  width: 100%;
  max-width: 42px;
  height: 220px;
  border-radius: 999px;
  background: linear-gradient(180deg, #edf3f8 0%, #dfe9f1 100%);
  display: flex;
  align-items: flex-end;
  padding: 4px;
}

.bar-fill {
  width: 100%;
  border-radius: 999px;
  min-height: 10px;
  box-shadow: 0 8px 18px rgba(0, 95, 184, 0.18);
}

.bar-label {
  font-size: 12px;
  color: var(--app-text-color);
}

@media (max-width: 1100px) {
  .donut-layout {
    grid-template-columns: 1fr;
  }

  .legend-list {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}
</style>
