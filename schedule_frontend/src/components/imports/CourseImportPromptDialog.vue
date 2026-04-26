<template>
  <el-dialog
    :model-value="modelValue"
    width="760px"
    title="AI 转课表"
    @close="emit('update:modelValue', false)"
  >
    <div class="section-stack">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="复制下面的 Prompt，把它和课表图片、上课时间补充说明一起发给外部 AI，再把返回 JSON 粘贴回导入页。"
      />

      <div class="prompt-steps surface-card">
        <strong>推荐步骤</strong>
        <ol>
          <li>准备课表截图或照片。</li>
          <li>填写学期信息和补充说明。</li>
          <li>点击“复制 Prompt”，把 Prompt 和课表图片一起发给 AI。</li>
          <li>把 AI 返回的 JSON 直接粘贴回导入页，先校验再导入。</li>
        </ol>
      </div>

      <el-form label-position="top" class="section-stack">
        <div class="field-row">
          <el-form-item label="学期名称">
            <el-input v-model="semesterName" placeholder="例如：2026 春季学期" />
          </el-form-item>
          <el-form-item label="学期开始日期">
            <el-date-picker
              v-model="termStartDate"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              class="full-width"
            />
          </el-form-item>
          <el-form-item label="学期结束日期">
            <el-date-picker
              v-model="termEndDate"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              class="full-width"
            />
          </el-form-item>
        </div>

        <el-form-item label="上课时间补充说明">
          <el-input
            v-model="scheduleHints"
            type="textarea"
            :rows="4"
            placeholder="例如：第1-16周；上午1-2节=08:00-09:35；下午5-6节=14:30-16:05；图片里看不清的教室可留空。"
          />
        </el-form-item>
      </el-form>

      <div class="inline-actions">
        <el-button type="primary" @click="handleCopyPrompt">复制 Prompt</el-button>
        <el-button @click="handleCopyExample">复制 JSON 示例</el-button>
      </div>

      <div class="section-stack">
        <strong>Prompt 预览</strong>
        <el-input :model-value="promptText" type="textarea" :rows="16" readonly />
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { buildCourseImportAiPrompt, buildCourseImportJsonExample } from '@/utils/courseImportPrompt'
import { copyText } from '@/utils/share'
import { notifySuccess } from '@/utils/message'

defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
}>()

const semesterName = ref('')
const termStartDate = ref('')
const termEndDate = ref('')
const scheduleHints = ref('')

const promptText = computed(() =>
  buildCourseImportAiPrompt({
    semesterName: semesterName.value,
    termStartDate: termStartDate.value,
    termEndDate: termEndDate.value,
    scheduleHints: scheduleHints.value,
  }),
)

async function handleCopyPrompt(): Promise<void> {
  await copyText(promptText.value)
  notifySuccess('Prompt 已复制')
}

async function handleCopyExample(): Promise<void> {
  await copyText(JSON.stringify(buildCourseImportJsonExample(), null, 2))
  notifySuccess('JSON 示例已复制')
}
</script>

<style scoped>
.prompt-steps {
  padding: 16px 18px;
}

.prompt-steps ol {
  margin: 10px 0 0;
  padding-left: 18px;
  color: var(--app-text-muted);
}
</style>
