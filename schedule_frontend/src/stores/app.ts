import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { get } from '@/api/client'
import { APP_NAME } from '@/config/app'
import type { HealthStatus, RuntimeMode, SystemInfo } from '@/types/common'
import { todayDateString } from '@/utils/date'
import { formatDateTime } from '@/utils/format'
import { detectRuntimeMode, formatRuntimeModeLabel } from '@/utils/runtime'

export const useAppStore = defineStore('app', () => {
  const appName = ref(APP_NAME)
  const currentDate = ref(todayDateString())
  const healthStatus = ref<'idle' | 'ok' | 'error'>('idle')
  const systemInfo = ref<SystemInfo | null>(null)
  const globalLoading = ref(false)
  const runtimeMode = ref<RuntimeMode>(detectRuntimeMode())
  const lastHealthCheckedAt = ref<string | null>(null)
  const lastSystemSyncAt = ref<string | null>(null)
  let refreshTimer: number | null = null

  const databaseStatusText = computed(() => systemInfo.value?.database_status || '--')
  const runtimeModeLabel = computed(() => formatRuntimeModeLabel(runtimeMode.value))
  const aiEnabled = computed(() => Boolean(systemInfo.value?.ai_enabled))
  const aiStatusLabel = computed(() => (aiEnabled.value ? '已启用' : '未启用'))
  const lastHealthCheckedText = computed(() => (lastHealthCheckedAt.value ? formatDateTime(lastHealthCheckedAt.value) : '--'))
  const lastSystemSyncText = computed(() => (lastSystemSyncAt.value ? formatDateTime(lastSystemSyncAt.value) : '--'))

  function setCurrentDate(date: string): void {
    currentDate.value = date
  }

  async function checkHealth(): Promise<void> {
    lastHealthCheckedAt.value = new Date().toISOString()
    try {
      await get<HealthStatus>('/api/health')
      healthStatus.value = 'ok'
    } catch {
      healthStatus.value = 'error'
    }
  }

  async function loadSystemInfo(): Promise<void> {
    globalLoading.value = true
    try {
      systemInfo.value = await get<SystemInfo>('/api/system/info')
      runtimeMode.value = detectRuntimeMode()
      lastSystemSyncAt.value = new Date().toISOString()
      if (systemInfo.value?.app_name) {
        appName.value = systemInfo.value.app_name
      }
    } finally {
      globalLoading.value = false
    }
  }

  async function refreshRuntimeState(): Promise<void> {
    await Promise.allSettled([checkHealth(), loadSystemInfo()])
  }

  function startAutoRefresh(intervalMs = 60000): void {
    if (typeof window === 'undefined') {
      return
    }

    stopAutoRefresh()
    refreshTimer = window.setInterval(() => {
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
        return
      }
      void refreshRuntimeState()
    }, intervalMs)
  }

  function stopAutoRefresh(): void {
    if (refreshTimer === null) {
      return
    }
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }

  return {
    appName,
    currentDate,
    healthStatus,
    systemInfo,
    globalLoading,
    runtimeMode,
    runtimeModeLabel,
    aiEnabled,
    aiStatusLabel,
    databaseStatusText,
    lastHealthCheckedAt,
    lastHealthCheckedText,
    lastSystemSyncAt,
    lastSystemSyncText,
    setCurrentDate,
    checkHealth,
    loadSystemInfo,
    refreshRuntimeState,
    startAutoRefresh,
    stopAutoRefresh,
  }
})
