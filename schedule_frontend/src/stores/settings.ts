import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchAiConfig,
  fetchSettings,
  testAiConnection,
  updateAiConfig,
  updateSetting,
  updateSettingsBatch,
} from '@/api/settings'
import type {
  AiConfig,
  AiConfigUpdatePayload,
  AiTestConnectionResult,
  AppSetting,
  BatchSettingValuePayload,
  SettingValue,
} from '@/types/settings'
import { notifyError, notifySuccess } from '@/utils/message'

export const useSettingsStore = defineStore('settings', () => {
  const loading = ref(false)
  const settings = ref<AppSetting[]>([])
  const aiConfig = ref<AiConfig | null>(null)

  const settingsMap = computed<Record<string, AppSetting>>(() =>
    settings.value.reduce<Record<string, AppSetting>>((accumulator, item) => {
      accumulator[item.key] = item
      return accumulator
    }, {}),
  )

  async function loadSettings(): Promise<void> {
    loading.value = true
    try {
      settings.value = await fetchSettings()
    } finally {
      loading.value = false
    }
  }

  async function loadAiConfig(): Promise<void> {
    aiConfig.value = await fetchAiConfig()
  }

  async function loadAll(): Promise<void> {
    await Promise.all([loadSettings(), loadAiConfig()])
  }

  async function saveSetting(key: string, payload: { value: SettingValue; value_type: AppSetting['value_type']; description?: string | null }): Promise<void> {
    await updateSetting(key, payload)
    await loadSettings()
    notifySuccess('设置已保存')
  }

  async function saveSettingsBatch(items: BatchSettingValuePayload[]): Promise<void> {
    await updateSettingsBatch({ items })
    await loadSettings()
    notifySuccess('设置已批量保存')
  }

  async function saveAiConfig(payload: AiConfigUpdatePayload): Promise<void> {
    aiConfig.value = await updateAiConfig(payload)
    notifySuccess('AI 配置已保存')
  }

  async function runAiConnectionTest(): Promise<AiTestConnectionResult> {
    const result = await testAiConnection()
    if (result.ok) {
      notifySuccess(result.message)
    } else {
      notifyError(result.message)
    }
    return result
  }

  return {
    loading,
    settings,
    aiConfig,
    settingsMap,
    loadSettings,
    loadAiConfig,
    loadAll,
    saveSetting,
    saveSettingsBatch,
    saveAiConfig,
    runAiConnectionTest,
  }
})
