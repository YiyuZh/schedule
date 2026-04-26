import { isTauri } from '@tauri-apps/api/core'

import type { RuntimeMode } from '@/types/common'

export function detectRuntimeMode(): RuntimeMode {
  try {
    return isTauri() ? 'tauri' : 'web'
  } catch {
    return 'web'
  }
}

export function formatRuntimeModeLabel(mode: RuntimeMode): string {
  return mode === 'tauri' ? '桌面模式' : 'Web 模式'
}

export function formatRuntimeModeShortLabel(mode: RuntimeMode): string {
  return mode === 'tauri' ? 'Tauri' : 'Web'
}
