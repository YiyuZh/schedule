<template>
  <section class="page-grid">
    <PageHeader
      title="任务模板"
      description="管理会自动生成到每日任务中的固定模板，可按分类检索与启停。"
      eyebrow="Templates"
    >
      <template #actions>
        <el-button class="topbar-button" @click="tasksStore.loadTemplates()">刷新列表</el-button>
        <el-button type="primary" class="topbar-button" @click="openCreateDialog">新建模板</el-button>
      </template>
    </PageHeader>

    <div class="summary-grid">
      <div class="summary-tile">
        <span class="summary-title">模板总数</span>
        <strong>{{ tasksStore.templates.length }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">启用中</span>
        <strong>{{ enabledCount }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">学习模板</span>
        <strong>{{ studyCount }}</strong>
      </div>
      <div class="summary-tile">
        <span class="summary-title">当前筛选结果</span>
        <strong>{{ filteredTemplates.length }}</strong>
      </div>
    </div>

    <el-card class="panel-card">
      <div class="table-toolbar">
        <el-input
          v-model="searchKeyword"
          clearable
          placeholder="搜索标题、分类或备注"
          class="table-toolbar-search"
        />
        <el-select v-model="enabledFilter" class="table-toolbar-select">
          <el-option label="全部状态" value="all" />
          <el-option label="仅启用" value="enabled" />
          <el-option label="仅停用" value="disabled" />
        </el-select>
        <el-select v-model="studyFilter" class="table-toolbar-select">
          <el-option label="全部类型" value="all" />
          <el-option label="学习模板" value="study" />
          <el-option label="非学习模板" value="normal" />
        </el-select>
      </div>

      <el-table :data="pagedTemplates" v-loading="tasksStore.templatesLoading" border>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="category" label="分类" min-width="120" />
        <el-table-column label="学习任务" min-width="100">
          <template #default="{ row }">
            <span :class="['status-pill', row.is_study ? 'is-primary' : '']">
              {{ row.is_study ? '学习' : '普通' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="默认时长" min-width="120">
          <template #default="{ row }">
            {{ formatDurationMinutes(row.default_duration_minutes) }}
          </template>
        </el-table-column>
        <el-table-column label="时间范围" min-width="150">
          <template #default="{ row }">
            {{ formatTimeRange(row.default_start_time, row.default_end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="时间偏好" min-width="110">
          <template #default="{ row }">
            {{ formatTimePreferenceLabel(row.time_preference) }}
          </template>
        </el-table-column>
        <el-table-column label="优先级" min-width="110">
          <template #default="{ row }">
            <span :class="['status-pill', row.priority >= 5 ? 'is-danger' : row.priority >= 3 ? 'is-warning' : 'is-success']">
              {{ formatPriorityLabel(row.priority) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="启用" min-width="90">
          <template #default="{ row }">
            <el-switch :model-value="row.is_enabled" @change="tasksStore.switchTemplateEnabled(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="inline-actions">
              <el-button link @click="handleEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="handleRemove(row.id, row.title)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <div class="muted-text">每页 {{ pageSize }} 条，共 {{ filteredTemplates.length }} 条</div>
        <el-pagination
          layout="prev, pager, next"
          :total="filteredTemplates.length"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="currentPage = $event"
        />
      </div>
    </el-card>

    <TemplateEditorDialog
      v-model="dialogVisible"
      :template="editingTemplate"
      @save="handleSave"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import PageHeader from '@/components/common/PageHeader.vue'
import TemplateEditorDialog from '@/components/templates/TemplateEditorDialog.vue'
import { useTasksStore } from '@/stores/tasks'
import type { TaskTemplate, TaskTemplatePayload } from '@/types/taskTemplate'
import { formatDurationMinutes, formatPriorityLabel, formatTimePreferenceLabel, formatTimeRange } from '@/utils/format'
import { confirmAction } from '@/utils/message'
import { listenPageRefresh } from '@/utils/pageEvents'

const tasksStore = useTasksStore()
const dialogVisible = ref(false)
const editingTemplate = ref<TaskTemplate | null>(null)
const searchKeyword = ref('')
const enabledFilter = ref<'all' | 'enabled' | 'disabled'>('all')
const studyFilter = ref<'all' | 'study' | 'normal'>('all')
const currentPage = ref(1)
const pageSize = 8
let removeRefreshListener: (() => void) | null = null

const enabledCount = computed(() => tasksStore.templates.filter((item) => item.is_enabled).length)
const studyCount = computed(() => tasksStore.templates.filter((item) => item.is_study).length)

const filteredTemplates = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return [...tasksStore.templates]
    .filter((item) => {
      if (enabledFilter.value === 'enabled' && !item.is_enabled) return false
      if (enabledFilter.value === 'disabled' && item.is_enabled) return false
      if (studyFilter.value === 'study' && !item.is_study) return false
      if (studyFilter.value === 'normal' && item.is_study) return false

      if (!keyword) return true

      return [item.title, item.category, item.notes || '']
        .join(' ')
        .toLowerCase()
        .includes(keyword)
    })
    .sort((left, right) => Number(right.is_enabled) - Number(left.is_enabled) || right.priority - left.priority)
})

const pagedTemplates = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredTemplates.value.slice(start, start + pageSize)
})

watch([searchKeyword, enabledFilter, studyFilter], () => {
  currentPage.value = 1
})

function openCreateDialog(): void {
  editingTemplate.value = null
  dialogVisible.value = true
}

function handleEdit(template: TaskTemplate): void {
  editingTemplate.value = template
  dialogVisible.value = true
}

async function handleSave(payload: TaskTemplatePayload, templateId?: number): Promise<void> {
  await tasksStore.saveTemplate(payload, templateId)
}

async function handleRemove(templateId: number, title: string): Promise<void> {
  const confirmed = await confirmAction(`确定删除模板“${title}”吗？`)
  if (!confirmed) {
    return
  }
  await tasksStore.removeTemplate(templateId)
}

onMounted(async () => {
  await tasksStore.loadTemplates()
  removeRefreshListener = listenPageRefresh(tasksStore.loadTemplates)
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>
