<template>
  <el-dialog
    :model-value="modelValue"
    width="720px"
    :title="event ? '编辑事件' : '新建事件'"
    @close="emit('update:modelValue', false)"
  >
    <el-form :model="form" label-position="top" class="section-stack">
      <el-form-item label="事件标题" required>
        <el-input v-model="form.title" placeholder="例如：项目复盘会 / 去医院 / 朋友聚餐" />
      </el-form-item>

      <div class="field-row">
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="例如：工作 / 生活 / 出行" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="form.event_date"
            type="date"
            class="full-width"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
          />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="开始时间">
          <el-time-picker v-model="form.start_time" value-format="HH:mm" format="HH:mm" class="full-width" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-time-picker v-model="form.end_time" value-format="HH:mm" format="HH:mm" class="full-width" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="例如：A 会议室 / 图书馆" />
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
        <el-form-item label="状态">
          <el-select v-model="form.status" class="full-width">
            <el-option label="已安排" value="scheduled" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="form.source" class="full-width">
            <el-option label="手动" value="manual" />
            <el-option label="AI" value="ai" />
            <el-option label="导入" value="import" />
          </el-select>
        </el-form-item>
      </div>

      <el-form-item label="备注">
        <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="记录补充说明、参会信息或携带物品..." />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="inline-actions" style="justify-content: flex-end;">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存事件</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

import type { EventItem, EventPayload } from '@/types/event'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  modelValue: boolean
  event?: EventItem | null
  date: string
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [EventPayload, number | undefined]
}>()

const createDefaultForm = (): EventPayload => ({
  title: '',
  category: '其他',
  event_date: props.date,
  start_time: null,
  end_time: null,
  location: '',
  priority: 3,
  status: 'scheduled',
  source: 'manual',
  linked_task_id: null,
  notes: '',
})

const form = reactive<EventPayload>(createDefaultForm())

function syncForm(): void {
  Object.assign(form, createDefaultForm())
  if (props.event) {
    Object.assign(form, {
      title: props.event.title,
      category: props.event.category,
      event_date: props.event.event_date,
      start_time: props.event.start_time ?? null,
      end_time: props.event.end_time ?? null,
      location: props.event.location ?? '',
      priority: props.event.priority,
      status: props.event.status,
      source: props.event.source,
      linked_task_id: props.event.linked_task_id ?? null,
      notes: props.event.notes ?? '',
    })
  }
}

watch(() => [props.modelValue, props.event, props.date], syncForm, { immediate: true })

function handleSubmit(): void {
  if (!form.title.trim()) {
    notifyError('事件标题不能为空')
    return
  }

  if ((form.start_time && !form.end_time) || (!form.start_time && form.end_time)) {
    notifyError('开始时间和结束时间需要同时填写')
    return
  }

  emit('save', { ...form, title: form.title.trim(), notes: form.notes?.trim() || '' }, props.event?.id)
  emit('update:modelValue', false)
}
</script>
