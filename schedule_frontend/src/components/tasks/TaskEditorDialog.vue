<template>
  <el-dialog
    :model-value="modelValue"
    width="760px"
    :title="task ? '编辑任务' : '新建任务'"
    @close="emit('update:modelValue', false)"
  >
    <el-form :model="form" label-position="top">
      <el-form-item label="任务标题" required>
        <el-input
          v-model="form.title"
          placeholder="例如：完成《数据结构》第三章课后习题"
          @blur="handleAiSuggestion"
        />
      </el-form-item>

      <div class="field-row">
        <el-form-item :label="form.is_study ? '学习科目' : '分类'">
          <el-input
            v-model="form.category"
            :placeholder="form.is_study ? '例如：数学 / Python / 英语' : '例如：健身 / 生活 / 工作'"
          />
        </el-form-item>

        <el-form-item label="任务属性">
          <div class="task-attribute-row">
            <span>学习任务</span>
            <el-switch v-model="form.is_study" />
          </div>
        </el-form-item>
      </div>

      <el-alert
        v-if="aiSuggestion"
        class="task-ai-suggestion"
        type="info"
        :closable="false"
        show-icon
      >
        <template #title>
          <div class="task-ai-suggestion-title">AI 建议</div>
        </template>

        <div class="section-stack">
          <div class="muted-text">
            根据标题，建议设置为
            {{ aiSuggestion.planned_duration_minutes || form.planned_duration_minutes }} 分钟
            <template v-if="aiSuggestion.start_time">
              ，开始时间 {{ aiSuggestion.start_time }}
            </template>
            <template v-if="aiSuggestion.category">
              ，分类 {{ aiSuggestion.category }}
            </template>
          </div>
          <div>
            <el-button link type="primary" @click="applyAiSuggestion">应用 AI 建议</el-button>
          </div>
        </div>
      </el-alert>

      <div class="field-row">
        <el-form-item label="日期">
          <el-date-picker
            v-model="form.task_date"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            class="full-width"
          />
        </el-form-item>

        <el-form-item label="计划时长（分钟）">
          <el-input-number v-model="form.planned_duration_minutes" :min="0" class="full-width" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="开始时间">
          <el-time-picker
            v-model="form.start_time"
            class="full-width"
            value-format="HH:mm"
            format="HH:mm"
            placeholder="可选"
          />
        </el-form-item>

        <el-form-item label="结束时间">
          <el-time-picker
            v-model="form.end_time"
            class="full-width"
            value-format="HH:mm"
            format="HH:mm"
            placeholder="可选"
          />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority" class="priority-radio-group">
            <el-radio-button :label="1">低</el-radio-button>
            <el-radio-button :label="3">中</el-radio-button>
            <el-radio-button :label="5">高</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="form.status" class="full-width">
            <el-option label="待办" value="pending" />
            <el-option label="进行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="已跳过" value="skipped" />
          </el-select>
        </el-form-item>
      </div>

      <el-form-item label="备注">
        <el-input
          v-model="form.notes"
          type="textarea"
          :rows="4"
          placeholder="添加任务相关链接、参考资料或备注..."
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="inline-actions" style="justify-content: flex-end;">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存修改</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

import { parseAiInput } from '@/api/ai'
import { useAppStore } from '@/stores/app'
import type { AiParseAction } from '@/types/ai'
import type { DailyTask, DailyTaskPayload } from '@/types/dailyTask'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  modelValue: boolean
  task?: DailyTask | null
  date: string
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [DailyTaskPayload, number | undefined]
}>()

const appStore = useAppStore()
const aiSuggestion = ref<AiParseAction | null>(null)
const suggesting = ref(false)

const createDefaultForm = (): DailyTaskPayload => ({
  template_id: null,
  title: '',
  category: '其他',
  is_study: false,
  task_date: props.date,
  start_time: null,
  end_time: null,
  planned_duration_minutes: 30,
  priority: 3,
  status: 'pending',
  source: 'manual',
  sort_order: 0,
  notes: '',
})

const form = reactive<DailyTaskPayload>(createDefaultForm())

function syncForm(): void {
  Object.assign(form, createDefaultForm())
  aiSuggestion.value = null

  if (props.task) {
    Object.assign(form, {
      template_id: props.task.template_id ?? null,
      title: props.task.title,
      category: props.task.category,
      is_study: props.task.is_study,
      task_date: props.task.task_date,
      start_time: props.task.start_time ?? null,
      end_time: props.task.end_time ?? null,
      planned_duration_minutes: props.task.planned_duration_minutes,
      priority: props.task.priority,
      status: props.task.status,
      source: props.task.source,
      sort_order: props.task.sort_order,
      notes: props.task.notes ?? '',
    })
  }
}

watch(() => [props.modelValue, props.task, props.date], syncForm, { immediate: true })

async function handleAiSuggestion(): Promise<void> {
  if (!appStore.systemInfo?.ai_enabled || !form.title.trim() || suggesting.value) {
    return
  }

  suggesting.value = true
  try {
    const result = await parseAiInput({
      text: form.title.trim(),
      date_context: form.task_date,
    })
    aiSuggestion.value = result.actions.find((item) => item.action_type === 'add_task') || null
  } catch {
    aiSuggestion.value = null
  } finally {
    suggesting.value = false
  }
}

function applyAiSuggestion(): void {
  if (!aiSuggestion.value) {
    return
  }

  form.planned_duration_minutes = aiSuggestion.value.planned_duration_minutes || form.planned_duration_minutes
  form.category = aiSuggestion.value.category || form.category
  form.is_study = aiSuggestion.value.is_study ?? form.is_study
  form.start_time = aiSuggestion.value.start_time ?? form.start_time
  form.end_time = aiSuggestion.value.end_time ?? form.end_time
}

function handleSubmit(): void {
  if (!form.title.trim()) {
    notifyError('任务标题不能为空')
    return
  }

  if ((form.start_time && !form.end_time) || (!form.start_time && form.end_time)) {
    notifyError('开始时间和结束时间需要同时填写')
    return
  }

  emit(
    'save',
    {
      ...form,
      title: form.title.trim(),
      notes: form.notes?.trim() || '',
    },
    props.task?.id,
  )
  emit('update:modelValue', false)
}
</script>

<style scoped>
.task-attribute-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--app-border);
  border-radius: 4px;
}

.task-ai-suggestion {
  margin-bottom: 18px;
}

.task-ai-suggestion-title {
  font-weight: 700;
}

.priority-radio-group {
  display: flex;
}
</style>
