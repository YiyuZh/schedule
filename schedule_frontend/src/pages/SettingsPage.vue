<template>
  <section class="page-grid">
    <PageHeader
      title="设置"
      description="管理基础行为、AI 连接方式、云同步入口以及当前本地配置的原始 JSON 视图。"
      eyebrow="Settings"
    >
      <template #actions>
        <el-button class="topbar-button" @click="settingsStore.loadAll()">刷新设置</el-button>
        <el-button class="topbar-button" @click="router.push('/ai-workspace')">AI 工作区</el-button>
        <el-button type="primary" class="topbar-button" @click="saveBasicSettings">保存基础设置</el-button>
      </template>
    </PageHeader>

    <div class="page-grid grid-two">
      <el-card class="panel-card">
        <template #header>
          <div class="inline-actions" style="justify-content: space-between; width: 100%;">
            <strong>基础设置</strong>
            <span class="muted-text">影响默认任务行为与专注流程</span>
          </div>
        </template>

        <el-form label-position="top" class="section-stack">
          <div class="field-row">
            <el-form-item label="默认任务时长（分钟）">
              <el-input-number v-model="basicSettings.default_task_duration" :min="0" class="full-width" />
            </el-form-item>
            <el-form-item label="自动继承未完成任务">
              <el-switch v-model="basicSettings.auto_inherit_unfinished" />
            </el-form-item>
            <el-form-item label="完成任务时自动结束计时">
              <el-switch v-model="basicSettings.complete_task_auto_stop_timer" />
            </el-form-item>
          </div>
        </el-form>
      </el-card>

      <AiConfigPanel
        :config="settingsStore.aiConfig"
        :loading="settingsStore.loading"
        @save="settingsStore.saveAiConfig"
        @test="settingsStore.runAiConnectionTest"
      />

      <SyncConfigPanel />
    </div>

    <el-card class="panel-card">
      <template #header>
        <div class="inline-actions" style="justify-content: space-between; width: 100%;">
          <strong>原始设置 JSON</strong>
          <span class="muted-text">用于快速核对当前 app_settings 映射结果</span>
        </div>
      </template>

      <pre class="code-block settings-json-block">{{ settingsJsonText }}</pre>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'

import PageHeader from '@/components/common/PageHeader.vue'
import AiConfigPanel from '@/components/settings/AiConfigPanel.vue'
import SyncConfigPanel from '@/components/settings/SyncConfigPanel.vue'
import { useSettingsStore } from '@/stores/settings'
import type { BatchSettingValuePayload } from '@/types/settings'
import { formatJsonString } from '@/utils/format'
import { listenPageRefresh } from '@/utils/pageEvents'

const router = useRouter()
const settingsStore = useSettingsStore()
let removeRefreshListener: (() => void) | null = null

const basicSettings = reactive({
  default_task_duration: 30,
  auto_inherit_unfinished: false,
  complete_task_auto_stop_timer: false,
})

const settingsJsonText = computed(() =>
  formatJsonString(
    settingsStore.settings.reduce<Record<string, unknown>>((result, item) => {
      result[item.key] = {
        value: item.value,
        value_type: item.value_type,
        description: item.description || '',
      }
      return result
    }, {}),
  ),
)

watch(
  () => settingsStore.settingsMap,
  (map) => {
    basicSettings.default_task_duration = Number(map.default_task_duration?.value ?? 30)
    basicSettings.auto_inherit_unfinished = Boolean(map.auto_inherit_unfinished?.value ?? false)
    basicSettings.complete_task_auto_stop_timer = Boolean(map.complete_task_auto_stop_timer?.value ?? false)
  },
  { immediate: true },
)

async function saveBasicSettings(): Promise<void> {
  const items: BatchSettingValuePayload[] = [
    {
      key: 'default_task_duration',
      value: basicSettings.default_task_duration,
      value_type: 'int',
      description: 'Default planned duration in minutes for new tasks',
    },
    {
      key: 'auto_inherit_unfinished',
      value: basicSettings.auto_inherit_unfinished,
      value_type: 'bool',
      description: 'Whether unfinished tasks should be inherited automatically',
    },
    {
      key: 'complete_task_auto_stop_timer',
      value: basicSettings.complete_task_auto_stop_timer,
      value_type: 'bool',
      description: 'Stop timer automatically when task is completed',
    },
  ]

  await settingsStore.saveSettingsBatch(items)
}

onMounted(async () => {
  await settingsStore.loadAll()
  removeRefreshListener = listenPageRefresh(settingsStore.loadAll)
})

onBeforeUnmount(() => {
  removeRefreshListener?.()
})
</script>

<style scoped>
.settings-json-block {
  max-height: 520px;
  overflow: auto;
}
</style>
