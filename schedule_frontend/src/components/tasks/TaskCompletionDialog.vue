<template>
  <el-dialog
    :model-value="modelValue"
    width="520px"
    title="完成任务"
    @close="emit('update:modelValue', false)"
  >
    <div class="section-stack">
      <div class="completion-task-summary">
        <strong>{{ taskTitle }}</strong>
        <span class="muted-text">计划时长：{{ plannedMinutes }} 分钟</span>
      </div>

      <el-form label-position="top" class="section-stack">
        <el-form-item label="实际时长（分钟）">
          <el-input-number v-model="actualDuration" :min="0" :max="1440" class="full-width" />
        </el-form-item>

        <div class="quick-fill-row">
          <el-button @click="actualDuration = plannedMinutes">等于计划时长</el-button>
          <el-button
            v-for="value in TASK_COMPLETION_QUICK_FILL_VALUES"
            :key="value"
            @click="actualDuration = value"
          >
            {{ value }}
          </el-button>
        </div>

        <el-form-item v-if="isStudy" label="同步到学习记录">
          <el-switch v-model="syncStudySession" />
        </el-form-item>

        <el-alert
          v-if="isStudy"
          type="info"
          :closable="false"
          show-icon
          :title="syncStudySession ? '将同时创建一条手动学习记录。' : '只完成任务，不写入学习记录。'"
        />
      </el-form>
    </div>

    <template #footer>
      <div class="inline-actions" style="justify-content: flex-end; width: 100%;">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="handleSave">完成任务</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

import type { DailyTaskCompletePayload } from '@/types/dailyTask'
import { buildTaskCompletionDraft, TASK_COMPLETION_QUICK_FILL_VALUES } from '@/utils/taskCompletion'

const props = defineProps<{
  modelValue: boolean
  taskTitle: string
  plannedMinutes: number
  isStudy: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [DailyTaskCompletePayload]
}>()

const actualDuration = ref(0)
const syncStudySession = ref(false)

function resetDraft(): void {
  const draft = buildTaskCompletionDraft(props.plannedMinutes, props.isStudy)
  actualDuration.value = draft.actual_duration_minutes ?? 0
  syncStudySession.value = draft.sync_study_session ?? false
}

watch(
  () => [props.modelValue, props.plannedMinutes, props.isStudy],
  resetDraft,
  { immediate: true },
)

function handleSave(): void {
  emit('save', {
    actual_duration_minutes: actualDuration.value,
    sync_study_session: props.isStudy ? syncStudySession.value : false,
  })
}
</script>

<style scoped>
.completion-task-summary {
  display: grid;
  gap: 6px;
}

.quick-fill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
