import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/sync', () => ({
  fetchSyncStatus: vi.fn(),
  saveSyncConfig: vi.fn(),
  loginSync: vi.fn(),
  registerSync: vi.fn(),
  logoutSync: vi.fn(),
  runSync: vi.fn(),
  fetchSyncConflicts: vi.fn(),
}))

vi.mock('@/utils/message', () => ({
  notifyError: vi.fn(),
  notifyInfo: vi.fn(),
  notifySuccess: vi.fn(),
}))

import { fetchSyncStatus, registerSync, runSync, saveSyncConfig } from '@/api/sync'
import { useSyncStore } from '@/stores/sync'
import { notifyError, notifyInfo, notifySuccess } from '@/utils/message'

const baseStatus = {
  enabled: false,
  configured: false,
  logged_in: false,
  server_url: null,
  user_email: null,
  device_id: 'device-1',
  device_name: 'Work PC',
  pending_count: 0,
  conflict_count: 0,
  last_push_at: null,
  last_pull_at: null,
  last_error: null,
}

describe('sync store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loads unconfigured status and exposes readable label', async () => {
    vi.mocked(fetchSyncStatus).mockResolvedValue(baseStatus)
    const store = useSyncStore()

    await store.loadStatus()

    expect(store.statusLabel).toBe('未配置')
    expect(store.canAutoRun).toBe(false)
  })

  it('saves config and refreshes status in memory', async () => {
    vi.mocked(saveSyncConfig).mockResolvedValue({
      ...baseStatus,
      enabled: true,
      configured: true,
      server_url: 'https://sync.example.com',
    })

    const store = useSyncStore()
    await store.saveConfig({ enabled: true, server_url: 'https://sync.example.com', device_name: 'Work PC' })

    expect(store.status?.server_url).toBe('https://sync.example.com')
    expect(vi.mocked(notifySuccess)).toHaveBeenCalledWith('云同步配置已保存')
  })

  it('does not run topbar sync when enabled but not logged in', async () => {
    vi.mocked(fetchSyncStatus).mockResolvedValue({ ...baseStatus, enabled: true, configured: true })
    const store = useSyncStore()
    await store.loadStatus()

    await store.runTopbarSync()

    expect(vi.mocked(runSync)).not.toHaveBeenCalled()
    expect(vi.mocked(notifyInfo)).toHaveBeenCalledWith('未登录')
  })

  it('reports manual sync errors without throwing', async () => {
    vi.mocked(runSync).mockResolvedValue({
      push_count: 0,
      pull_count: 0,
      conflict_count: 0,
      error_count: 1,
      message: '云同步未登录',
    })
    vi.mocked(fetchSyncStatus).mockResolvedValue(baseStatus)

    const store = useSyncStore()
    const result = await store.runManualSync()

    expect(result?.error_count).toBe(1)
    expect(vi.mocked(notifyError)).toHaveBeenCalledWith('云同步未登录')
  })

  it('registers cloud account and stores logged-in status', async () => {
    vi.mocked(registerSync).mockResolvedValue({
      ...baseStatus,
      enabled: true,
      configured: true,
      logged_in: true,
      server_url: 'https://sync.example.com',
      user_email: 'new@example.com',
    })

    const store = useSyncStore()
    await store.register({
      email: 'new@example.com',
      password: 'password123',
      server_url: 'https://sync.example.com',
      device_name: 'Work PC',
    })

    expect(store.status?.logged_in).toBe(true)
    expect(vi.mocked(notifySuccess)).toHaveBeenCalledWith('云同步账号已注册并登录')
  })
})
