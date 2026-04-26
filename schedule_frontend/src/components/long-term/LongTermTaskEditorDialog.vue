<template>
  <el-dialog
    :model-value="modelValue"
    width="760px"
    :title="task ? '编辑长期任务' : '新建长期任务'"
    @close="emit('update:modelValue', false)"
  >
    <el-form :model="form" label-position="top" class="section-stack">
      <el-form-item label="任务标题" required>
        <el-input v-model="form.title" placeholder="例如：本月完成项目升级" />
      </el-form-item>

      <div class="field-row">
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="例如：项目 / 学习 / 工作" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" class="full-width">
            <el-option label="进行中" value="active" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" class="full-width" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" class="full-width" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio-button :label="1">低</el-radio-button>
            <el-radio-button :label="3">中</el-radio-button>
            <el-radio-button :label="5">高</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" class="full-width" />
        </el-form-item>
      </div>

      <el-form-item label="说明">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="写下目标范围、交付标准或阶段说明..."
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="inline-actions" style="justify-content: flex-end;">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存长期任务</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

import type { LongTermTask, LongTermTaskPayload } from '@/types/longTermTask'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  modelValue: boolean
  task?: LongTermTask | null
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [LongTermTaskPayload, number | undefined]
}>()

const createDefaultForm = (): LongTermTaskPayload => ({
  title: '',
  category: '项目',
  description: '',
  start_date: null,
  due_date: null,
  status: 'active',
  priority: 3,
  sort_order: 0,
})

const form = reactive<LongTermTaskPayload>(createDefaultForm())

function syncForm(): void {
  Object.assign(form, createDefaultForm())
  if (props.task) {
    Object.assign(form, {
      title: props.task.title,
      category: props.task.category,
      description: props.task.description ?? '',
      start_date: props.task.start_date ?? null,
      due_date: props.task.due_date ?? null,
      status: props.task.status,
      priority: props.task.priority,
      sort_order: props.task.sort_order,
    })
  }
}

watch(() => [props.modelValue, props.task], syncForm, { immediate: true })

function handleSubmit(): void {
  if (!form.title.trim()) {
    notifyError('长期任务标题不能为空')
    return
  }
  if (form.start_date && form.due_date && form.start_date > form.due_date) {
    notifyError('开始日期不能晚于截止日期')
    return
  }

  emit(
    'save',
    {
      ...form,
      title: form.title.trim(),
      category: form.category.trim() || '项目',
      description: form.description?.trim() || '',
    },
    props.task?.id,
  )
  emit('update:modelValue', false)
}
</script>
