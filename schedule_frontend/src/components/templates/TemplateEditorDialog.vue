<template>
  <el-dialog
    :model-value="modelValue"
    width="760px"
    :title="template ? '编辑模板' : '新建模板'"
    @close="emit('update:modelValue', false)"
  >
    <el-form :model="form" label-position="top" class="section-stack">
      <el-form-item label="模板标题" required>
        <el-input v-model="form.title" placeholder="例如：英语学习 / 晚间健身 / 每日复盘" />
      </el-form-item>

      <div class="field-row">
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="例如：学习 / 生活 / 健康" />
        </el-form-item>
        <el-form-item label="时间偏好">
          <el-select v-model="form.time_preference" class="full-width">
            <el-option label="不限" value="none" />
            <el-option label="上午" value="morning" />
            <el-option label="下午" value="afternoon" />
            <el-option label="晚上" value="evening" />
            <el-option label="夜间" value="night" />
          </el-select>
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="默认开始时间">
          <el-time-picker v-model="form.default_start_time" value-format="HH:mm" format="HH:mm" class="full-width" />
        </el-form-item>
        <el-form-item label="默认结束时间">
          <el-time-picker v-model="form.default_end_time" value-format="HH:mm" format="HH:mm" class="full-width" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="默认时长（分钟）">
          <el-input-number v-model="form.default_duration_minutes" :min="0" class="full-width" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio-button :label="1">低</el-radio-button>
            <el-radio-button :label="3">中</el-radio-button>
            <el-radio-button :label="5">高</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="学习任务">
          <el-switch v-model="form.is_study" />
        </el-form-item>
        <el-form-item label="启用模板">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
        <el-form-item label="继承未完成任务">
          <el-switch v-model="form.inherit_unfinished" />
        </el-form-item>
      </div>

      <el-form-item label="备注">
        <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="补充模板说明、执行建议或固定材料..." />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="inline-actions" style="justify-content: flex-end;">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存模板</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

import type { TaskTemplate, TaskTemplatePayload } from '@/types/taskTemplate'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  modelValue: boolean
  template?: TaskTemplate | null
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [TaskTemplatePayload, number | undefined]
}>()

const createDefaultForm = (): TaskTemplatePayload => ({
  title: '',
  category: '其他',
  is_study: false,
  default_duration_minutes: 30,
  default_start_time: null,
  default_end_time: null,
  time_preference: 'none',
  priority: 3,
  is_enabled: true,
  inherit_unfinished: false,
  notes: '',
})

const form = reactive<TaskTemplatePayload>(createDefaultForm())

function syncForm(): void {
  Object.assign(form, createDefaultForm())
  if (props.template) {
    Object.assign(form, {
      title: props.template.title,
      category: props.template.category,
      is_study: props.template.is_study,
      default_duration_minutes: props.template.default_duration_minutes,
      default_start_time: props.template.default_start_time ?? null,
      default_end_time: props.template.default_end_time ?? null,
      time_preference: props.template.time_preference,
      priority: props.template.priority,
      is_enabled: props.template.is_enabled,
      inherit_unfinished: props.template.inherit_unfinished,
      notes: props.template.notes ?? '',
    })
  }
}

watch(() => [props.modelValue, props.template], syncForm, { immediate: true })

function handleSubmit(): void {
  if (!form.title.trim()) {
    notifyError('模板标题不能为空')
    return
  }

  if ((form.default_start_time && !form.default_end_time) || (!form.default_start_time && form.default_end_time)) {
    notifyError('默认开始时间和结束时间需要同时填写')
    return
  }

  emit('save', { ...form, title: form.title.trim(), notes: form.notes?.trim() || '' }, props.template?.id)
  emit('update:modelValue', false)
}
</script>
