import { afterEach, describe, expect, it, vi } from 'vitest'

describe('runtime helpers', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.resetModules()
  })

  it('detects tauri runtime when isTauri returns true', async () => {
    vi.doMock('@tauri-apps/api/core', () => ({
      isTauri: () => true,
    }))

    const { detectRuntimeMode, formatRuntimeModeLabel } = await import('@/utils/runtime')
    expect(detectRuntimeMode()).toBe('tauri')
    expect(formatRuntimeModeLabel('tauri')).toBe('桌面模式')
  })

  it('falls back to web runtime when tauri api is unavailable', async () => {
    vi.doMock('@tauri-apps/api/core', () => ({
      isTauri: () => {
        throw new Error('tauri bridge unavailable')
      },
    }))

    const { detectRuntimeMode, formatRuntimeModeShortLabel } = await import('@/utils/runtime')
    expect(detectRuntimeMode()).toBe('web')
    expect(formatRuntimeModeShortLabel('web')).toBe('Web')
  })
})
