import type { AiConfig, AiConfigUpdatePayload } from '@/types/settings'

export type AiProviderPresetKey = 'deepseek' | 'openai_compatible' | 'local'

export interface AiProviderPreset {
  key: AiProviderPresetKey
  title: string
  description: string
  provider: string
  base_url: string
  model_name: string
  plan_model_name: string
}

export const AI_PROVIDER_PRESETS: AiProviderPreset[] = [
  {
    key: 'deepseek',
    title: 'DeepSeek 官方',
    description: '默认推荐，解析使用 deepseek-chat，规划使用 deepseek-reasoner。',
    provider: 'deepseek',
    base_url: 'https://api.deepseek.com/v1',
    model_name: 'deepseek-chat',
    plan_model_name: 'deepseek-reasoner',
  },
  {
    key: 'openai_compatible',
    title: 'OpenAI 兼容',
    description: '适用于 OpenAI、OpenRouter 等兼容 /chat/completions 的服务。',
    provider: 'openai_compatible',
    base_url: 'https://api.openai.com/v1',
    model_name: 'gpt-4.1-mini',
    plan_model_name: 'gpt-4.1-mini',
  },
  {
    key: 'local',
    title: '本地兼容服务',
    description: '适用于 LM Studio、Ollama 网关或其他本地 OpenAI 兼容服务。',
    provider: 'local',
    base_url: 'http://127.0.0.1:1234/v1',
    model_name: 'qwen2.5',
    plan_model_name: 'qwen2.5',
  },
]

export function buildAiConfigFormSeed(
  overrides: Partial<AiConfigUpdatePayload> = {},
): AiConfigUpdatePayload {
  return {
    enabled: false,
    provider: 'deepseek',
    base_url: 'https://api.deepseek.com/v1',
    api_key: '',
    model_name: 'deepseek-chat',
    plan_model_name: 'deepseek-reasoner',
    timeout: 60,
    temperature: 0.2,
    ...overrides,
  }
}

export function getAiProviderPreset(key: AiProviderPresetKey): AiProviderPreset {
  return AI_PROVIDER_PRESETS.find((preset) => preset.key === key) ?? AI_PROVIDER_PRESETS[0]
}

export function getPresetKeyFromConfig(
  config: Pick<AiConfigUpdatePayload, 'provider' | 'base_url'> | null | undefined,
): AiProviderPresetKey | null {
  if (!config) {
    return null
  }

  const normalizedProvider = config.provider.trim().replace(/-/g, '_')
  const normalizedBaseUrl = config.base_url.trim().replace(/\/$/, '')

  const matched = AI_PROVIDER_PRESETS.find(
    (preset) =>
      preset.provider === normalizedProvider &&
      preset.base_url.replace(/\/$/, '') === normalizedBaseUrl,
  )
  return matched?.key ?? null
}

export function applyAiProviderPreset(
  target: AiConfigUpdatePayload,
  presetKey: AiProviderPresetKey,
): void {
  const preset = getAiProviderPreset(presetKey)
  Object.assign(target, {
    provider: preset.provider,
    base_url: preset.base_url,
    model_name: preset.model_name,
    plan_model_name: preset.plan_model_name,
  })
}

export function resolveAiModelUsage(config: AiConfig | null | undefined): {
  parseModel: string
  planModel: string
} {
  return {
    parseModel: config?.model_name || '--',
    planModel: config?.plan_model_name || config?.model_name || '--',
  }
}
