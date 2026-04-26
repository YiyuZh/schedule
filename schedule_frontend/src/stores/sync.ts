import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchSyncConflicts,
  fetchSyncStatus,
  loginSync,
  logoutSync,
  registerSync,
  runSync as requestRunSync,
  saveSyncConfig,
} from '@/api/sync'
import type { SyncConfigPayload, SyncConflict, SyncLoginPayload, SyncRegisterPayload, SyncRunResult, SyncStatus } from '@/types/sync'
import { formatDateTime } from '@/utils/format'
import { notifyError, notifyInfo, notifySuccess } from '@/utils/message'

export const useSyncStore = defineStore('sync', () => {
  const loading = ref(false)
  const syncing = ref(false)
  const status = ref<SyncStatus | null>(null)
  const conflicts = ref<SyncConflict[]>([])
  const lastRunResult = ref<SyncRunResult | null>(null)

  const enabled = computed(() => Boolean(status.value?.enabled))
  const loggedIn = computed(() => Boolean(status.value?.logged_in))
  const canAutoRun = computed(() => Boolean(status.value?.enabled && status.value?.configured && status.value?.logged_in))
  const hasPendingChanges = computed(() => Number(status.value?.pending_count || 0) > 0)

  const statusLabel = computed(() => {
    if (syncing.value) return '自动同步中'
    if (!status.value) return '检测中'
    if (!status.value.configured) return '未配置'
    if (!status.value.logged_in) return '未登录'
    if (status.value.last_error) return '同步失败'
    if (status.value.pending_count > 0) return `待上传 ${status.value.pending_count}`
    return '已登录'
  })

  const lastSyncText = computed(() => {
    const time = status.value?.last_push_at || status.value?.last_pull_at
    return time ? formatDateTime(time) : '--'
  })

  async function loadStatus(): Promise<void> {
    loading.value = true
    try {
      status.value = await fetchSyncStatus()
    } finally {
      loading.value = false
    }
  }

  async function saveConfig(payload: SyncConfigPayload): Promise<void> {
    status.value = await saveSyncConfig(payload)
    notifySuccess('云同步配置已保存')
  }

  async function login(payload: SyncLoginPayload): Promise<void> {
    status.value = await loginSync(payload)
    notifySuccess('云同步登录成功')
  }

  async function register(payload: SyncRegisterPayload): Promise<void> {
    status.value = await registerSync(payload)
    notifySuccess('云同步账号已注册并登录')
  }

  async function logout(): Promise<void> {
    status.value = await logoutSync()
    notifySuccess('已退出云同步账号')
  }

  async function runManualSync(options: { silent?: boolean } = {}): Promise<SyncRunResult | null> {
    syncing.value = true
    try {
      const result = await requestRunSync()
      lastRunResult.value = result
      await loadStatus()
      if (!options.silent) {
        if (result.error_count > 0) {
          notifyError(result.message)
        } else {
          notifySuccess(result.message || '同步完成')
        }
      }
      return result
    } catch (error) {
      await loadStatus().catch(() => undefined)
      if (!options.silent) {
        notifyError(error instanceof Error ? error.message : '同步失败')
      }
      return null
    } finally {
      syncing.value = false
    }
  }

  async function runTopbarSync(): Promise<void> {
    if (!enabled.value) {
      return
    }
    if (!canAutoRun.value) {
      notifyInfo(statusLabel.value)
      return
    }
    await runManualSync({ silent: false })
  }

  async function loadConflicts(): Promise<void> {
    conflicts.value = await fetchSyncConflicts()
  }

  return {
    loading,
    syncing,
    status,
    conflicts,
    lastRunResult,
    enabled,
    loggedIn,
    canAutoRun,
    hasPendingChanges,
    statusLabel,
    lastSyncText,
    loadStatus,
    saveConfig,
    login,
    register,
    logout,
    runManualSync,
    runTopbarSync,
    loadConflicts,
  }
})
