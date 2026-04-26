<template>
  <el-dialog
    :model-value="modelValue"
    width="760px"
    :title="subtask ? '编辑子任务' : '新建子任务'"
    @close="emit('update:modelValue', false)"
  >
    <el-form :model="form" label-position="top" class="section-stack">
      <el-form-item label="子任务标题" required>
        <el-input v-model="form.title" placeholder="例如：初步完成 PRD 设计" />
      </el-form-item>

      <div class="field-row">
        <el-form-item :label="form.is_study ? '学习科目' : '分类'">
          <el-input v-model="form.category" :placeholder="form.is_study ? '例如：数学 / Python / 英语' : '例如：设计 / 开发 / 联调'" />
        </el-form-item>
        <el-form-item label="学习任务">
          <el-switch v-model="form.is_study" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="截止日期">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" class="full-width" />
        </el-form-item>
        <el-form-item label="计划时长（分钟）">
          <el-input-number v-model="form.planned_duration_minutes" :min="0" class="full-width" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="状态">
          <el-select v-model="form.status" class="full-width">
            <el-option label="待办" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已跳过" value="skipped" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio-button :label="1">低</el-radio-button>
            <el-radio-button :label="3">中</el-radio-button>
            <el-radio-button :label="5">高</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </div>

      <el-form-item label="说明">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="补充交付标准、参考资料或拆解说明..."
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="inline-actions" style="justify-content: flex-end;">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存子任务</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

import type { LongTermSubtask, LongTermSubtaskPayload } from '@/types/longTermTask'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  modelValue: boolean
  subtask?: LongTermSubtask | null
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [LongTermSubtaskPayload, number | undefined]
}>()

const createDefaultForm = (): LongTermSubtaskPayload => ({
  title: '',
  category: '项目',
  is_study: false,
  description: '',
  due_date: null,
  planned_duration_minutes: 30,
  status: 'pending',
  priority: 3,
  sort_order: 0,
})

const form = reactive<LongTermSubtaskPayload>(createDefaultForm())

function syncForm(): void {
  Object.assign(form, createDefaultForm())
  if (props.subtask) {
    Object.assign(form, {
      title: props.subtask.title,
      category: props.subtask.category,
      is_study: props.subtask.is_study,
      description: props.subtask.description ?? '',
      due_date: props.subtask.due_date ?? null,
      planned_duration_minutes: props.subtask.planned_duration_minutes,
      status: props.subtask.status,
      priority: props.subtask.priority,
      sort_order: props.subtask.sort_order,
    })
  }
}

watch(() => [props.modelValue, props.subtask], syncForm, { immediate: true })

function handleSubmit(): void {
  if (!form.title.trim()) {
    notifyError('子任务标题不能为空')
    return
  }

  emit(
    'save',
    {
      ...form,
      title: form.title.trim(),
      category: form.category.trim() || (form.is_study ? '学习' : '项目'),
      description: form.description?.trim() || '',
    },
    props.subtask?.id,
  )
  emit('update:modelValue', false)
}
</script>
