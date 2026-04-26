<template>
  <el-card class="panel-card">
    <div class="quick-add-box">
      <div class="quick-add-box__content">
        <el-input
          v-model="title"
          placeholder="快速添加今日任务，回车即可创建"
          @keyup.enter="handleSubmit"
        />
        <el-input v-model="category" placeholder="分类" />
        <el-switch v-model="isStudy" active-text="学习任务" inactive-text="普通任务" />
      </div>
      <el-button type="primary" @click="handleSubmit">添加</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import type { DailyTaskPayload } from '@/types/dailyTask'
import { notifyError } from '@/utils/message'

const props = defineProps<{
  date: string
}>()

const emit = defineEmits<{
  submit: [DailyTaskPayload]
}>()

const title = ref('')
const category = ref('other')
const isStudy = ref(false)

function handleSubmit(): void {
  if (!title.value.trim()) {
    notifyError('请先输入任务标题')
    return
  }

  emit('submit', {
    template_id: null,
    title: title.value.trim(),
    category: category.value.trim() || 'other',
    is_study: isStudy.value,
    task_date: props.date,
    start_time: null,
    end_time: null,
    planned_duration_minutes: isStudy.value ? 60 : 30,
    priority: 3,
    status: 'pending',
    source: 'manual',
    sort_order: 0,
    notes: '',
  })

  title.value = ''
  category.value = 'other'
  isStudy.value = false
}
</script>

<style scoped>
.quick-add-box {
  display: flex;
  gap: 16px;
  align-items: center;
}

.quick-add-box__content {
  display: grid;
  gap: 12px;
  flex: 1;
  grid-template-columns: minmax(0, 1.6fr) minmax(120px, 0.6fr) minmax(180px, 0.6fr);
}

@media (max-width: 900px) {
  .quick-add-box {
    flex-direction: column;
    align-items: stretch;
  }

  .quick-add-box__content {
    grid-template-columns: 1fr;
  }
}
</style>
