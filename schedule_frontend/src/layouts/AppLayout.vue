<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><Calendar /></el-icon>
        </div>
        <div>
          <h1>{{ appStore.appName }}</h1>
          <p>本地桌面效率工具</p>
        </div>
      </div>

      <el-dropdown trigger="click" placement="bottom-start" @command="handleQuickCreate">
        <el-button class="sidebar-create-button" type="primary">
          <el-icon><Plus /></el-icon>
          <span>新建日程</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="task">新建任务</el-dropdown-item>
            <el-dropdown-item command="event">新建事件</el-dropdown-item>
            <el-dropdown-item command="long-term">新建长期任务</el-dropdown-item>
            <el-dropdown-item command="template">新建模板</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-menu
        class="nav-menu"
        :default-active="route.path"
        background-color="transparent"
        active-text-color="var(--app-primary)"
        text-color="var(--app-text-muted)"
        @select="handleNavigate"
      >
        <el-menu-item v-for="item in NAV_ITEMS" :key="item.path" :index="item.path">
          <el-icon>
            <component :is="resolveIcon(item.icon)" />
          </el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-status-panel">
        <div class="sidebar-status-row">
          <div class="sidebar-status-title">
            <el-icon><Connection /></el-icon>
            <span>系统状态</span>
          </div>
          <span
            :class="[
              'status-badge',
              appStore.healthStatus === 'ok' ? 'is-success' : appStore.healthStatus === 'error' ? 'is-danger' : '',
            ]"
          >
            {{ healthLabel }}
          </span>
        </div>

        <div class="sidebar-status-grid">
          <div class="sidebar-status-card">
            <span class="sidebar-status-caption">运行模式</span>
            <strong class="sidebar-status-emphasis">{{ appStore.runtimeModeLabel }}</strong>
          </div>
          <div class="sidebar-status-card">
            <span class="sidebar-status-caption">AI 能力</span>
            <strong class="sidebar-status-emphasis">{{ appStore.aiStatusLabel }}</strong>
          </div>
          <div class="sidebar-status-card">
            <span class="sidebar-status-caption">云同步</span>
            <strong class="sidebar-status-emphasis">{{ syncStore.statusLabel }}</strong>
          </div>
        </div>

        <div class="sidebar-status-text">数据库：{{ appStore.databaseStatusText }}</div>
        <div class="sidebar-status-text">版本：{{ appStore.systemInfo?.app_version || APP_VERSION }}</div>
        <div class="sidebar-status-text">最近同步：{{ syncStore.lastSyncText }}</div>
        <div class="sidebar-status-text">健康检查：{{ appStore.lastHealthCheckedText }}</div>
      </div>
    </aside>

    <div class="app-main">
      <header class="app-topbar">
        <div class="topbar-breadcrumb">
          <span>{{ currentTitle }}</span>
          <small>{{ appStore.currentDate }}</small>
        </div>

        <div class="topbar-actions">
          <el-button v-if="showSyncButton" class="topbar-button" :loading="syncStore.syncing" @click="handleTopbarSync">
            同步数据
          </el-button>
          <el-button v-if="showExportButton" class="topbar-button" @click="emitPageExport()">
            导出报告
          </el-button>
        </div>
      </header>

      <main class="app-content">
        <router-view />
      </main>
    </div>

    <TaskEditorDialog
      v-model="taskDialogVisible"
      :date="appStore.currentDate"
      @save="handleSaveTask"
    />
    <EventEditorDialog
      v-model="eventDialogVisible"
      :date="appStore.currentDate"
      @save="handleSaveEvent"
    />
    <TemplateEditorDialog
      v-model="templateDialogVisible"
      @save="handleSaveTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Calendar,
  Clock,
  Connection,
  Flag,
  MagicStick,
  Memo,
  Plus,
  Setting,
  TrendCharts,
  UploadFilled,
} from '@element-plus/icons-vue'

import EventEditorDialog from '@/components/schedule/EventEditorDialog.vue'
import TaskEditorDialog from '@/components/tasks/TaskEditorDialog.vue'
import TemplateEditorDialog from '@/components/templates/TemplateEditorDialog.vue'
import { APP_VERSION, NAV_ITEMS, PAGE_TITLE_MAP } from '@/config/app'
import { useAppStore } from '@/stores/app'
import { useScheduleStore } from '@/stores/schedule'
import { useSettingsStore } from '@/stores/settings'
import { useSyncStore } from '@/stores/sync'
import { useTasksStore } from '@/stores/tasks'
import type { DailyTaskPayload } from '@/types/dailyTask'
import type { EventPayload } from '@/types/event'
import type { TaskTemplatePayload } from '@/types/taskTemplate'
import { emitPageExport, emitPageRefresh } from '@/utils/pageEvents'

const iconMap = {
  Calendar,
  Clock,
  Flag,
  MagicStick,
  Memo,
  Setting,
  TrendCharts,
  UploadFilled,
}

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const settingsStore = useSettingsStore()
const syncStore = useSyncStore()
const tasksStore = useTasksStore()
const scheduleStore = useScheduleStore()

const taskDialogVisible = ref(false)
const eventDialogVisible = ref(false)
const templateDialogVisible = ref(false)
let autoSyncTimer: ReturnType<typeof setInterval> | null = null

const currentTitle = computed(() => PAGE_TITLE_MAP[String(route.name || '')] || (route.meta.title as string) || '日程安排')
const showExportButton = computed(() => route.name === 'study-records')
const showSyncButton = computed(() => route.name !== 'focus-mode')
const healthLabel = computed(() => {
  if (appStore.healthStatus === 'ok') return '在线'
  if (appStore.healthStatus === 'error') return '异常'
  return '检测中'
})

function resolveIcon(iconName: string) {
  return iconMap[iconName as keyof typeof iconMap] || Calendar
}

function handleNavigate(path: string): void {
  void router.push(path)
}

function handleQuickCreate(command: 'task' | 'event' | 'long-term' | 'template'): void {
  if (command === 'task') {
    taskDialogVisible.value = true
    return
  }

  if (command === 'event') {
    eventDialogVisible.value = true
    return
  }

  if (command === 'long-term') {
    void router.push({ path: '/long-term-tasks', query: { create: '1' } })
    return
  }

  templateDialogVisible.value = true
}

async function handleSaveTask(payload: DailyTaskPayload): Promise<void> {
  await tasksStore.saveTask(payload)
  emitPageRefresh()
}

async function handleSaveEvent(payload: EventPayload): Promise<void> {
  await scheduleStore.saveEvent(payload)
  emitPageRefresh()
}

async function handleSaveTemplate(payload: TaskTemplatePayload): Promise<void> {
  await tasksStore.saveTemplate(payload)
  emitPageRefresh()
}

async function handleTopbarSync(): Promise<void> {
  emitPageRefresh()
  await syncStore.runTopbarSync()
  emitPageRefresh()
}

async function runAutoSync(): Promise<void> {
  if (document.hidden || syncStore.syncing || !syncStore.canAutoRun) return
  const result = await syncStore.runManualSync({ silent: true })
  if (result && result.error_count === 0) {
    emitPageRefresh()
  }
}

function handleVisibilityChange(): void {
  if (!document.hidden) {
    void runAutoSync()
  }
}

onMounted(async () => {
  await Promise.all([
    appStore.refreshRuntimeState(),
    settingsStore.loadSettings(),
    syncStore.loadStatus(),
  ])
  appStore.startAutoRefresh()
  autoSyncTimer = setInterval(() => {
    void runAutoSync()
  }, 45000)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  void runAutoSync()
})

onBeforeUnmount(() => {
  appStore.stopAutoRefresh()
  if (autoSyncTimer) clearInterval(autoSyncTimer)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>
