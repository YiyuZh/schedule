<template>
  <div class="page-grid grid-two import-workspace">
    <el-card class="panel-card section-stack">
      <div>
        <div class="page-heading-eyebrow">Course Import</div>
        <h3 class="import-title">课表导入工作区</h3>
        <p class="muted-text">仅支持 JSON。你可以先下载模板、打开 AI 转课表弹窗生成 Prompt，或直接选择本地 JSON 再进行校验和导入。</p>
      </div>

      <div class="inline-actions">
        <el-button @click="promptDialogVisible = true">AI 转课表</el-button>
        <el-button :loading="selectingFile" @click="handlePickFile">选择本地 JSON</el-button>
        <el-button @click="handleDownloadTemplate">下载模板</el-button>
        <el-tag v-if="selectedFileName" type="info">{{ selectedFileName }}</el-tag>
      </div>

      <el-input
        v-model="jsonText"
        type="textarea"
        :rows="18"
        placeholder="请粘贴完整课程 JSON 内容"
      />

      <div class="inline-actions">
        <el-button :loading="validating" @click="handleValidate">校验内容</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入课程</el-button>
      </div>
    </el-card>

    <el-card class="panel-card section-stack">
      <div>
        <div class="page-heading-eyebrow">Preview</div>
        <h3 class="import-title">校验结果与预览</h3>
      </div>

      <EmptyState
        v-if="!validationResult"
        title="等待校验结果"
        description="点击“校验内容”后，这里会显示课程条目预览和格式错误提示。"
        icon="预览"
      />

      <template v-else>
        <el-alert
          :type="validationResult.valid ? 'success' : 'error'"
          :title="validationResult.valid ? `校验通过，可导入 ${validationResult.parsed_count} 条课程` : '校验失败'"
          :closable="false"
          show-icon
        />

        <div v-if="validationResult.errors.length" class="section-stack">
          <strong>错误信息</strong>
          <div v-for="(error, index) in validationResult.errors" :key="index" class="import-error-item">
            {{ error }}
          </div>
        </div>

        <el-table :data="validationResult.preview_items" border max-height="480">
          <el-table-column prop="course_name" label="课程" min-width="160" />
          <el-table-column prop="weekday" label="星期" min-width="90" />
          <el-table-column label="时间" min-width="140">
            <template #default="{ row }">
              {{ row.start_time }} - {{ row.end_time }}
            </template>
          </el-table-column>
          <el-table-column prop="location" label="地点" min-width="120" />
          <el-table-column prop="teacher" label="教师" min-width="120" />
          <el-table-column label="周次" min-width="150">
            <template #default="{ row }">
              {{ row.week_list.join(', ') }}
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-card>
  </div>

  <CourseImportPromptDialog v-model="promptDialogVisible" />
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { importCourses, validateCourseImport } from '@/api/imports'
import EmptyState from '@/components/common/EmptyState.vue'
import CourseImportPromptDialog from '@/components/imports/CourseImportPromptDialog.vue'
import type { CourseImportPayload, CourseImportValidateResult } from '@/types/course'
import { pickJsonTextFile } from '@/utils/desktop'
import { notifyError, notifySuccess } from '@/utils/message'

const emit = defineEmits<{
  imported: []
}>()

const jsonText = ref('')
const selectedFileName = ref('')
const validationResult = ref<CourseImportValidateResult | null>(null)
const validating = ref(false)
const importing = ref(false)
const selectingFile = ref(false)
const promptDialogVisible = ref(false)

function parseJsonPayload(): CourseImportPayload | null {
  if (!jsonText.value.trim()) {
    notifyError('请先粘贴或选择 JSON 内容')
    return null
  }

  try {
    const payload = JSON.parse(jsonText.value) as CourseImportPayload
    if (!payload.file_name && selectedFileName.value) {
      payload.file_name = selectedFileName.value
    }
    return payload
  } catch {
    notifyError('JSON 格式不正确，请检查后重试')
    return null
  }
}

async function handlePickFile(): Promise<void> {
  selectingFile.value = true
  try {
    const file = await pickJsonTextFile()
    if (!file) {
      return
    }

    jsonText.value = file.content
    selectedFileName.value = file.fileName
    validationResult.value = null
    notifySuccess(`已加载 ${file.fileName}`)
  } catch (error) {
    notifyError(error instanceof Error ? error.message : '读取文件失败')
  } finally {
    selectingFile.value = false
  }
}

function handleDownloadTemplate(): void {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}course-import-template.json`
  link.download = 'course-import-template.json'
  link.click()
}

async function handleValidate(): Promise<void> {
  const payload = parseJsonPayload()
  if (!payload) {
    return
  }

  validating.value = true
  try {
    validationResult.value = await validateCourseImport(payload)
  } finally {
    validating.value = false
  }
}

async function handleImport(): Promise<void> {
  const payload = parseJsonPayload()
  if (!payload) {
    return
  }

  importing.value = true
  try {
    const result = await importCourses(payload)
    notifySuccess(`课程导入成功，共写入 ${result.parsed_count} 条记录`)
    emit('imported')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.import-workspace {
  align-items: start;
}

.import-title {
  margin: 6px 0;
  font-size: 20px;
}

.import-error-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff4f4;
  color: #b42318;
  border: 1px solid #f3d0d0;
}

p {
  margin: 0;
}
</style>
