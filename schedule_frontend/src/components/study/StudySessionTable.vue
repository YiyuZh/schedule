<template>
  <el-card class="panel-card">
    <template #header>
      <div class="inline-actions" style="justify-content: space-between; width: 100%;">
        <strong>学习记录</strong>
        <span class="muted-text">共 {{ total }} 条</span>
      </div>
    </template>

    <el-table :data="sessions" v-loading="Boolean(loading)" border>
      <el-table-column prop="session_date" label="日期" min-width="120" />
      <el-table-column prop="task_title_snapshot" label="任务" min-width="180" />
      <el-table-column prop="category_snapshot" label="分类" min-width="120" />
      <el-table-column label="起止时间" min-width="200">
        <template #default="{ row }">
          {{ row.start_at }} 至 {{ row.end_at }}
        </template>
      </el-table-column>
      <el-table-column label="时长" min-width="120">
        <template #default="{ row }">
          {{ formatDurationMinutes(row.duration_minutes) }}
        </template>
      </el-table-column>
      <el-table-column prop="source" label="来源" min-width="100" />
      <el-table-column label="备注" min-width="180">
        <template #default="{ row }">
          <span class="soft-text">{{ row.note || '--' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="emit('remove', row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="table-footer">
      <div class="muted-text">每页 {{ pageSize }} 条</div>
      <el-pagination
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="emit('pageChange', $event)"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { StudySession } from '@/types/study'
import { formatDurationMinutes } from '@/utils/format'

defineProps<{
  sessions: StudySession[]
  total: number
  page: number
  pageSize: number
  loading?: boolean
}>()

const emit = defineEmits<{
  pageChange: [number]
  remove: [number]
}>()
</script>
