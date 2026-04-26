import { describe, expect, it } from 'vitest'

import {
  AI_PROVIDER_PRESETS,
  applyAiProviderPreset,
  buildAiConfigFormSeed,
  resolveAiModelUsage,
} from '@/utils/aiConfig'

describe('AI config presets', () => {
  it('fills the DeepSeek preset with dual-model defaults', () => {
    const form = buildAiConfigFormSeed({
      provider: 'openai_compatible',
      base_url: 'https://api.openai.com/v1',
      model_name: 'gpt-4.1-mini',
      plan_model_name: 'gpt-4.1-mini',
    })

    applyAiProviderPreset(form, 'deepseek')

    expect(form.provider).toBe('deepseek')
    expect(form.base_url).toBe('https://api.deepseek.com/v1')
    expect(form.model_name).toBe('deepseek-chat')
    expect(form.plan_model_name).toBe('deepseek-reasoner')
  })

  it('keeps DeepSeek as the first and recommended preset', () => {
    expect(AI_PROVIDER_PRESETS[0].key).toBe('deepseek')
    expect(AI_PROVIDER_PRESETS[0].model_name).toBe('deepseek-chat')
    expect(AI_PROVIDER_PRESETS[0].plan_model_name).toBe('deepseek-reasoner')
  })

  it('resolves parse and plan models for workspace diagnostics', () => {
    expect(
      resolveAiModelUsage({
        enabled: true,
        provider: 'deepseek',
        model_name: 'deepseek-chat',
        plan_model_name: 'deepseek-reasoner',
        base_url: 'https://api.deepseek.com/v1',
        has_api_key: true,
        timeout: 60,
        temperature: 0.2,
      }),
    ).toEqual({
      parseModel: 'deepseek-chat',
      planModel: 'deepseek-reasoner',
    })
  })
})
