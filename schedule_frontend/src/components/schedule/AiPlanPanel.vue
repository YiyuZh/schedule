<template>
  <el-card class="panel-card section-stack">
    <div>
      <div class="page-heading-eyebrow">AI Planning</div>
      <h3 class="plan-title">AI 日程规划</h3>
      <p class="muted-text">结合当天任务、事件和课程实例，生成可直接应用的候选安排方案。</p>
    </div>

    <el-input
      v-model="userInput"
      type="textarea"
      :rows="4"
      placeholder="例如：今晚想补完高数作业，再留一点时间做英语听力，最好 23:00 前结束。"
    />

    <div class="field-row">
      <el-form-item label="方案数量">
        <el-input-number v-model="optionCount" :min="1" :max="5" class="full-width" />
      </el-form-item>
      <el-form-item label="包含习惯建议">
        <el-switch v-model="includeHabits" />
      </el-form-item>
    </div>

    <div class="inline-actions">
      <el-button type="primary" :loading="loading" @click="handleGenerate">生成方案</el-button>
      <el-button @click="clearPlan">清空</el-button>
    </div>

    <EmptyState
      v-if="!scheduleStore.aiPlan"
      title="还没有规划结果"
      description="输入一句自然语言需求，AI 会基于当前日程生成若干候选安排。"
      icon="AI"
    />

    <div v-else class="section-stack">
      <el-card
        v-for="(option, index) in scheduleStore.aiPlan.plan_options"
        :key="`${scheduleStore.aiPlan.raw_log_id}-${index}`"
        class="page-card"
      >
        <template #header>
          <div class="inline-actions" style="justify-content: space-between; width: 100%;">
            <div>
              <strong>{{ option.name }}</strong>
              <div class="muted-text">{{ option.reason }}</div>
            </div>
            <el-button
              size="small"
              type="primary"
              :loading="applyingIndex === index"
              @click="handleApply(index)"
            >
              应用方案
            </el-button>
          </div>
        </template>

        <div class="section-stack">
          <div
            v-for="item in option.items"
            :key="`${item.item_type}-${item.title}-${item.start_time}`"
            class="plan-item"
          >
            <div class="inline-actions" style="justify-content: space-between; width: 100%;">
              <strong>{{ item.title }}</strong>
              <span :class="['status-pill', item.item_type === 'event' ? 'is-primary' : 'is-warning']">
                {{ item.item_type === 'event' ? '事件' : '任务排程' }}
              </span>
            </div>
            <div class="muted-text">{{ item.date }} · {{ item.start_time }} - {{ item.end_time }}</div>
            <div class="soft-text">{{ item.category || '未分类' }}</div>
          </div>
        </div>
      </el-card>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import EmptyState from '@/components/common/EmptyState.vue'
import { useScheduleStore } from '@/stores/schedule'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  date: string
}>()

const emit = defineEmits<{
  applied: []
}>()

const scheduleStore = useScheduleStore()
const userInput = ref('')
const loading = ref(false)
const includeHabits = ref(true)
const optionCount = ref(3)
const applyingIndex = ref<number | null>(null)

async function handleGenerate(): Promise<void> {
  if (!userInput.value.trim()) {
    notifyError('请输入要规划的内容')
    return
  }

  loading.value = true
  try {
    await scheduleStore.createPlan(props.date, userInput.value.trim(), includeHabits.value, optionCount.value)
  } finally {
    loading.value = false
  }
}

async function handleApply(index: number): Promise<void> {
  applyingIndex.value = index
  try {
    await scheduleStore.applyPlan(index)
    emit('applied')
  } finally {
    applyingIndex.value = null
  }
}

function clearPlan(): void {
  userInput.value = ''
  scheduleStore.aiPlan = null
}
</script>

<style scoped>
.plan-title {
  margin: 6px 0;
  font-size: 20px;
}

.plan-item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-card-subtle);
}

p {
  margin: 0;
}
</style>
