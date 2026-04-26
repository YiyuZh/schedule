<template>
  <div class="ai-quick-panel section-stack">
    <div class="ai-input-row surface-card">
      <div class="ai-input-prefix">
        <span>+</span>
      </div>
      <el-input
        v-model="text"
        class="ai-inline-input"
        placeholder="输入自然语言，例如：明天下午 3 点开需求评审会，或今晚学习 Python 60 分钟"
        @keyup.enter="handleParse"
      />
      <el-button type="primary" :loading="parsing" @click="handleParse">AI 解析</el-button>
    </div>

    <AiParseActionDialog
      v-model="dialogVisible"
      :result="parseResult"
      :default-date="date"
      :loading="applying"
      @apply="handleApply"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { applyAiParse, parseAiInput } from '@/api/ai'
import AiParseActionDialog from '@/components/ai/AiParseActionDialog.vue'
import type { AiParseAction, AiParseResult } from '@/types/ai'
import { notifyError, notifySuccess } from '@/utils/message'

const props = defineProps<{
  date: string
}>()

const emit = defineEmits<{
  applied: []
}>()

const text = ref('')
const parsing = ref(false)
const applying = ref(false)
const parseResult = ref<AiParseResult | null>(null)
const dialogVisible = ref(false)

async function handleParse(): Promise<void> {
  if (!text.value.trim()) {
    notifyError('请输入要解析的自然语言内容')
    return
  }

  parsing.value = true
  try {
    parseResult.value = await parseAiInput({
      text: text.value.trim(),
      date_context: props.date,
    })
    dialogVisible.value = true
  } finally {
    parsing.value = false
  }
}

function clearResult(): void {
  parseResult.value = null
  text.value = ''
}

async function handleApply(actions: AiParseAction[]): Promise<void> {
  if (!parseResult.value) {
    return
  }

  applying.value = true
  try {
    await applyAiParse({
      log_id: parseResult.value.raw_log_id,
      actions,
    })
    notifySuccess('AI 解析结果已写入')
    dialogVisible.value = false
    emit('applied')
    clearResult()
  } finally {
    applying.value = false
  }
}
</script>

<style scoped>
.ai-input-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 10px 14px;
}

.ai-input-prefix {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  color: var(--app-primary);
  font-size: 18px;
}

.ai-inline-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: none !important;
  padding-left: 0;
  padding-right: 0;
}
</style>
