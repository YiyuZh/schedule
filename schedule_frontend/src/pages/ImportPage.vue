<template>
  <section class="page-grid">
    <PageHeader
      title="导入中心"
      description="支持课程 JSON 校验、导入与批次管理，适合本地桌面环境快速导入课表。"
      eyebrow="Import"
    >
      <template #actions>
        <el-button class="topbar-button" @click="loadBatches">刷新批次</el-button>
      </template>
    </PageHeader>

    <div class="summary-grid">
      <div class="summary-tile">
        <span class="summary-title">导入批次</span>
        <strong>{{ batches.length }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">成功批次</span>
        <strong>{{ successBatchCount }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">失败批次</span>
        <strong>{{ failedBatchCount }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">累计解析课程数</span>
        <strong>{{ parsedCourseCount }}</strong>
      </div>
    </div>

    <CourseImportPanel @imported="handleImported" />

    <el-card class="panel-card">
      <template #header>
        <div class="inline-actions" style="justify-content: space-between; width: 100%;">
          <strong>导入历史</strong>
          <span class="muted-text">支持按批次删除对应课程</span>
        </div>
      </template>

      <el-table :data="batches" v-loading="loading" border>
        <el-table-column prop="id" label="批次 ID" min-width="100" />
        <el-table-column prop="file_name" label="文件名" min-width="180" />
        <el-table-column prop="import_type" label="类型" min-width="100" />
        <el-table-column prop="parsed_count" label="解析条数" min-width="120" />
        <el-table-column label="状态" min-width="110">
          <template #default="{ row }">
            <span
              :class="[
                'status-pill',
                row.status === 'success' ? 'is-success' : row.status === 'failed' ? 'is-danger' : 'is-warning',
              ]"
            >
              {{ row.status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="错误信息" min-width="220">
          <template #default="{ row }">
            <span class="soft-text">{{ row.error_message || '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDeleteBatch(row.id)">删除本批次课程</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import PageHeader from '@/components/common/PageHeader.vue'
import CourseImportPanel from '@/components/imports/CourseImportPanel.vue'
import { deleteImportBatchCourses, fetchImportBatches } from '@/api/imports'
import type { ImportBatch } from '@/types/course'
import { confirmAction, notifySuccess } from '@/utils/message'
import { listenPageRefresh } from '@/utils/pageEvents'

const loading = ref(false)
const batches = ref<ImportBatch[]>([])
let removeRefreshListener: (() => void) | null = null

const successBatchCount = computed(() => batches.value.filter((item) => item.status === 'success').length)
const failedBatchCount = computed(() => batches.value.filter((item) => item.status === 'failed').length)
const parsedCourseCount = computed(() => batches.value.reduce((sum, item) => sum + item.parsed_count, 0))

async function loadBatches(): Promise<void> {
  loading.value = true
  try {
    batches.value = await fetchImportBatches()
  } finally {
    loading.value = false
  }
}

async function handleImported(): Promise<void> {
  await loadBatches()
}

async function handleDeleteBatch(batchId: number): Promise<void> {
  const confirmed = await confirmAction(`确定删除批次 ${batchId} 对应的全部课程吗？`)
  if (!confirmed) {
    return
  }

  const result = await deleteImportBatchCourses(batchId)
  notifySuccess(`已删除 ${result.deleted_count} 条课程记录`)
  await loadBatches()
}

onMounted(async () => {
  await loadBatches()
  removeRefreshListener = listenPageRefresh(loadBatches)
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>
