<template>
  <el-dialog
    :model-value="modelValue"
    width="880px"
    title="确认 AI 解析内容"
    @close="emit('update:modelValue', false)"
  >
    <div class="section-stack">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="请勾选要写入的条目。缺少时间或地点时会留空，不会阻止写入。"
      />

      <el-empty v-if="rows.length === 0" description="暂无可应用的解析结果" />

      <div v-for="(row, index) in rows" v-else :key="index" class="page-card ai-action-row">
        <div class="inline-actions ai-action-row-header">
          <el-checkbox v-model="row.selected">应用</el-checkbox>
          <el-select v-model="row.action.action_type" style="width: 140px;">
            <el-option label="任务" value="add_task" />
            <el-option label="日程事件" value="add_event" />
          </el-select>
        </div>

        <div class="ai-action-grid">
          <el-form-item label="标题">
            <el-input v-model="row.action.title" placeholder="例如：学习 Python / 项目会议" />
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker
              v-model="row.action.date"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              class="full-width"
            />
          </el-form-item>
          <el-form-item label="开始时间">
            <el-time-picker
              v-model="row.action.start_time"
              value-format="HH:mm"
              format="HH:mm"
              class="full-width"
              placeholder="可留空"
            />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-time-picker
              v-model="row.action.end_time"
              value-format="HH:mm"
              format="HH:mm"
              class="full-width"
              placeholder="可留空"
            />
          </el-form-item>
          <el-form-item :label="row.action.action_type === 'add_task' && row.action.is_study ? '学习科目' : '分类'">
            <el-input v-model="row.action.category" placeholder="例如：学习 / 工作 / 生活" />
          </el-form-item>
          <el-form-item v-if="row.action.action_type === 'add_event'" label="地点">
            <el-input v-model="row.action.location" placeholder="可留空" />
          </el-form-item>
          <el-form-item v-if="row.action.action_type === 'add_task'" label="计划时长">
            <el-input-number v-model="row.action.planned_duration_minutes" :min="0" :max="1440" class="full-width" />
          </el-form-item>
          <el-form-item v-if="row.action.action_type === 'add_task'" label="学习任务">
            <el-switch v-model="row.action.is_study" />
          </el-form-item>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="inline-actions ai-action-footer">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" :loading="loading" :disabled="selectedActions.length === 0" @click="handleApply">
          应用选中内容
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { AiParseAction, AiParseResult } from '@/types/ai'
import { notifyError } from '@/utils/message'

interface EditableParseAction extends Omit<AiParseAction, 'is_study' | 'planned_duration_minutes'> {
  is_study: boolean
  planned_duration_minutes: number | null
}

interface EditableRow {
  selected: boolean
  action: EditableParseAction
}

const props = defineProps<{
  modelValue: boolean
  result: AiParseResult | null
  defaultDate: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  apply: [AiParseAction[]]
}>()

const rows = ref<EditableRow[]>([])

const selectedActions = computed(() =>
  rows.value
    .filter((row) => row.selected)
    .map((row) => normalizeAction(row.action, props.defaultDate)),
)

function normalizeAction(action: EditableParseAction, defaultDate: string): AiParseAction {
  const startTime = action.start_time || null
  const endTime = action.end_time || null
  const actionType = action.action_type === 'add_event' ? 'add_event' : 'add_task'

  return {
    ...action,
    action_type: actionType,
    title: action.title?.trim() || null,
    date: action.date || defaultDate,
    start_time: startTime && endTime ? startTime : null,
    end_time: startTime && endTime ? endTime : null,
    category: action.category?.trim() || null,
    location: action.location?.trim() || null,
    planned_duration_minutes: actionType === 'add_task' ? Number(action.planned_duration_minutes || 30) : null,
    is_study: actionType === 'add_task' ? Boolean(action.is_study) : null,
  }
}

function resetRows(): void {
  rows.value = (props.result?.actions ?? [])
    .filter((action) => action.action_type === 'add_task' || action.action_type === 'add_event')
    .map((action) => ({
      selected: true,
      action: {
        ...action,
        action_type: action.action_type === 'add_event' ? 'add_event' : 'add_task',
        date: action.date || props.defaultDate,
        planned_duration_minutes: action.planned_duration_minutes ?? 30,
        is_study: Boolean(action.is_study),
      },
    }))
}

function handleApply(): void {
  if (selectedActions.value.some((action) => !action.title?.trim())) {
    notifyError('请先补全选中条目的标题')
    return
  }
  emit('apply', selectedActions.value)
}

watch(
  () => [props.result, props.modelValue],
  resetRows,
  { immediate: true },
)
</script>

<style scoped>
.ai-action-row {
  display: grid;
  gap: 16px;
}

.ai-action-row-header,
.ai-action-footer {
  justify-content: space-between;
  width: 100%;
}

.ai-action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
}

@media (max-width: 760px) {
  .ai-action-grid {
    grid-template-columns: 1fr;
  }
}
</style>
