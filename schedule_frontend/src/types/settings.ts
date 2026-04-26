export type SettingValueType = 'string' | 'int' | 'bool' | 'json' | 'float'

export type SettingValue = string | number | boolean | Record<string, unknown> | unknown[] | null

export interface AppSetting {
  key: string
  value: SettingValue
  value_type: SettingValueType
  description?: string | null
  created_at: string
  updated_at: string
}

export interface SettingValuePayload {
  value: SettingValue
  value_type: SettingValueType
  description?: string | null
}

export interface BatchSettingValuePayload extends SettingValuePayload {
  key: string
}

export interface BatchSettingsPayload {
  items: BatchSettingValuePayload[]
}

export interface SettingsListData {
  settings: AppSetting[]
}

export interface AiConfig {
  enabled: boolean
  provider: string
  model_name: string
  plan_model_name: string
  base_url: string
  has_api_key: boolean
  timeout: number
  temperature: number
}

export interface AiConfigUpdatePayload {
  enabled: boolean
  provider: string
  base_url: string
  api_key?: string | null
  model_name: string
  plan_model_name: string
  timeout: number
  temperature: number
}

export interface AiTestConnectionResult {
  ok: boolean
  message: string
}
