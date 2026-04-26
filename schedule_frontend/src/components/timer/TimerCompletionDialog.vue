<template>
  <el-dialog
    :model-value="modelValue"
    width="640px"
    title="专注完成反馈"
    @close="emit('update:modelValue', false)"
  >
    <div class="completion-shell">
      <div class="completion-hero">
        <div class="completion-icon">✓</div>
        <h3>太棒了，你已完成本次专注</h3>
        <div class="completion-task-pill">
          任务：{{ taskTitle }}
        </div>
      </div>

      <div class="completion-summary surface-card">
        <div class="completion-ring">
          <strong>{{ actualMinutes }}</strong>
          <span>分钟</span>
        </div>

        <div class="completion-metrics">
          <div>
            <label>实际专注时长</label>
            <strong>{{ actualMinutes }} 分钟</strong>
          </div>
          <div>
            <label>计划时长</label>
            <strong>{{ plannedMinutes }} 分钟</strong>
          </div>
        </div>
      </div>

      <div class="section-stack">
        <label class="completion-label">本次记录备注（选填）</label>
        <el-input v-model="note" type="textarea" :rows="4" placeholder="记录一下这次专注中的想法、困难或结论..." />
      </div>
    </div>

    <template #footer>
      <div class="completion-footer">
        <el-button @click="emit('continue', note)">继续计时</el-button>
        <el-button @click="emit('newTask', note)">开启新任务</el-button>
        <el-button type="primary" @click="emit('save', note)">完成并记录</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  taskTitle: string
  actualMinutes: number
  plannedMinutes: number
  initialNote?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [string]
  continue: [string]
  newTask: [string]
}>()

const note = ref('')

watch(
  () => [props.modelValue, props.initialNote],
  () => {
    note.value = props.initialNote || ''
  },
  { immediate: true },
)
</script>

<style scoped>
.completion-shell {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.completion-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.completion-icon {
  display: grid;
  place-items: center;
  width: 82px;
  height: 82px;
  border-radius: 16px;
  background: #d6e9f7;
  color: var(--app-primary);
  font-size: 34px;
  font-weight: 800;
}

.completion-hero h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
}

.completion-task-pill {
  padding: 10px 18px;
  border-radius: 999px;
  border: 1px solid var(--app-border);
  background: var(--app-card-subtle);
  color: var(--app-text-muted);
}

.completion-summary {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  align-items: center;
  padding: 24px;
}

.completion-ring {
  display: grid;
  place-items: center;
  width: 140px;
  height: 140px;
  margin: 0 auto;
  border-radius: 50%;
  border: 10px solid var(--app-primary);
  color: var(--app-primary);
}

.completion-ring strong {
  font-size: 28px;
  line-height: 1;
}

.completion-ring span {
  color: var(--app-text-muted);
  font-size: 14px;
}

.completion-metrics {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.completion-metrics label {
  display: block;
  margin-bottom: 8px;
  color: var(--app-text-muted);
  font-size: 14px;
  font-weight: 600;
}

.completion-metrics strong {
  font-size: 28px;
}

.completion-label {
  font-size: 14px;
  font-weight: 700;
}

.completion-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 760px) {
  .completion-summary {
    grid-template-columns: 1fr;
  }

  .completion-footer {
    flex-direction: column;
  }
}
</style>
