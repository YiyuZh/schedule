import { get, post, put } from '@/api/client'
import type {
  AiConfig,
  AiConfigUpdatePayload,
  AiTestConnectionResult,
  AppSetting,
  BatchSettingsPayload,
  SettingValuePayload,
  SettingsListData,
} from '@/types/settings'

export async function fetchSettings(): Promise<AppSetting[]> {
  const data = await get<SettingsListData>('/api/settings')
  return data.settings
}

export function fetchSetting(key: string): Promise<AppSetting> {
  return get<AppSetting>(`/api/settings/${key}`)
}

export function updateSetting(key: string, payload: SettingValuePayload): Promise<AppSetting> {
  return put<AppSetting>(`/api/settings/${key}`, { body: payload })
}

export async function updateSettingsBatch(payload: BatchSettingsPayload): Promise<AppSetting[]> {
  const data = await put<{ settings: AppSetting[]; updated_keys: string[] }>('/api/settings', { body: payload })
  return data.settings
}

export function fetchAiConfig(): Promise<AiConfig> {
  return get<AiConfig>('/api/ai/config')
}

export function updateAiConfig(payload: AiConfigUpdatePayload): Promise<AiConfig> {
  return put<AiConfig>('/api/ai/config', { body: payload })
}

export function testAiConnection(): Promise<AiTestConnectionResult> {
  return post<AiTestConnectionResult>('/api/ai/test-connection')
}
