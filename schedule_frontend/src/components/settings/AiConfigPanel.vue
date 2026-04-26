<template>
  <el-card class="panel-card">
    <template #header>
      <div class="inline-actions panel-header-actions">
        <div>
          <strong>AI 配置</strong>
          <div class="muted-text">DeepSeek 现已作为默认 AI 路线，仍保留 OpenAI 兼容与本地兼容服务支持。</div>
        </div>
        <el-button :loading="loading" @click="emit('test')">测试连接</el-button>
      </div>
    </template>

    <el-form :model="form" label-position="top" class="section-stack">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="后端统一使用 OpenAI 兼容协议，DeepSeek 默认采用 deepseek-chat + deepseek-reasoner 双模型分工。"
      />

      <div class="preset-grid">
        <button
          v-for="preset in AI_PROVIDER_PRESETS"
          :key="preset.key"
          type="button"
          :class="['preset-card', { 'is-active': selectedPresetKey === preset.key }]"
          @click="handleApplyPreset(preset.key)"
        >
          <strong>{{ preset.title }}</strong>
          <span>{{ preset.description }}</span>
        </button>
      </div>

      <div class="field-row">
        <el-form-item label="启用 AI">
          <el-switch v-model="form.enabled" />
        </el-form-item>
        <el-form-item label="Provider 标识">
          <el-input v-model="form.provider" placeholder="例如：deepseek / openai_compatible / local" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="聊天 / 解析模型">
          <el-input v-model="form.model_name" placeholder="例如：deepseek-chat / gpt-4.1-mini" />
        </el-form-item>
        <el-form-item label="规划 / 推理模型">
          <el-input v-model="form.plan_model_name" placeholder="例如：deepseek-reasoner / gpt-4.1-mini" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="例如：https://api.deepseek.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            show-password
            placeholder="输入新值后保存；留空则保持当前 Key 不变"
          />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="超时（秒）">
          <el-input-number v-model="form.timeout" :min="1" :max="600" class="full-width" />
        </el-form-item>
        <el-form-item label="Temperature">
          <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" class="full-width" />
        </el-form-item>
      </div>

      <div class="field-row">
        <el-form-item label="当前 Key 状态">
          <div class="settings-inline-value">
            {{ props.config?.has_api_key ? '已配置' : '未配置' }}
          </div>
        </el-form-item>
        <el-form-item label="当前双模型策略">
          <div class="settings-inline-value">
            {{ form.model_name || '--' }} → {{ form.plan_model_name || '--' }}
          </div>
        </el-form-item>
      </div>

      <div class="inline-actions">
        <el-button type="primary" :loading="loading" @click="handleSave">保存 AI 配置</el-button>
      </div>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import type { AiConfig, AiConfigUpdatePayload } from '@/types/settings'
import {
  AI_PROVIDER_PRESETS,
  applyAiProviderPreset,
  buildAiConfigFormSeed,
  getPresetKeyFromConfig,
  type AiProviderPresetKey,
} from '@/utils/aiConfig'

const props = defineProps<{
  config: AiConfig | null
  loading?: boolean
}>()

const emit = defineEmits<{
  save: [AiConfigUpdatePayload]
  test: []
}>()

const form = reactive<AiConfigUpdatePayload>(buildAiConfigFormSeed())

const selectedPresetKey = computed(() => getPresetKeyFromConfig(form))

function handleApplyPreset(presetKey: AiProviderPresetKey): void {
  applyAiProviderPreset(form, presetKey)
}

function handleSave(): void {
  emit('save', {
    ...form,
    provider: form.provider.trim(),
    base_url: form.base_url.trim(),
    model_name: form.model_name.trim(),
    plan_model_name: form.plan_model_name.trim(),
    api_key: form.api_key?.trim() ? form.api_key.trim() : undefined,
  })
}

watch(
  () => props.config,
  (value) => {
    if (!value) {
      Object.assign(form, buildAiConfigFormSeed())
      return
    }

    Object.assign(
      form,
      buildAiConfigFormSeed({
        enabled: value.enabled,
        provider: value.provider,
        base_url: value.base_url,
        api_key: '',
        model_name: value.model_name,
        plan_model_name: value.plan_model_name,
        timeout: value.timeout,
        temperature: value.temperature,
      }),
    )
  },
  { immediate: true },
)
</script>

<style scoped>
.panel-header-actions {
  justify-content: space-between;
  width: 100%;
}

.preset-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.preset-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-card-subtle);
  color: var(--app-text);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease, transform 0.2s ease;
}

.preset-card span {
  color: var(--app-text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.preset-card:hover {
  border-color: var(--app-primary);
  transform: translateY(-1px);
}

.preset-card.is-active {
  border-color: var(--app-primary);
  background: color-mix(in srgb, var(--app-primary) 10%, var(--app-card));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--app-primary) 28%, transparent);
}

.settings-inline-value {
  display: flex;
  align-items: center;
  min-height: 32px;
  color: var(--app-text-muted);
  font-weight: 600;
}

@media (max-width: 1080px) {
  .preset-grid {
    grid-template-columns: 1fr;
  }
}
</style>
