<template>
  <el-card class="panel-card">
    <template #header>
      <div class="inline-actions" style="justify-content: space-between; width: 100%;">
        <div>
          <strong>云同步</strong>
          <p class="muted-text panel-subtitle">本地数据优先保存，后台同步到你的云服务器账号。</p>
        </div>
        <el-tag :type="statusTagType">{{ syncStore.statusLabel }}</el-tag>
      </div>
    </template>

    <div class="section-stack">
      <div class="sync-metrics">
        <div class="metric-card">
          <span>待上传</span>
          <strong>{{ status?.pending_count ?? 0 }}</strong>
        </div>
        <div class="metric-card">
          <span>冲突</span>
          <strong>{{ status?.conflict_count ?? 0 }}</strong>
        </div>
        <div class="metric-card wide">
          <span>最近同步</span>
          <strong>{{ syncStore.lastSyncText }}</strong>
        </div>
      </div>

      <el-alert
        v-if="status?.last_error"
        type="error"
        :closable="false"
        show-icon
        :title="status.last_error"
      />

      <el-form label-position="top">
        <div class="field-row">
          <el-form-item label="云服务器地址">
            <el-input v-model="configForm.server_url" placeholder="例如：https://schedule-sync.zenithy.art" />
          </el-form-item>
          <el-form-item label="当前设备名">
            <el-input v-model="configForm.device_name" placeholder="例如：Windows 台式机" />
          </el-form-item>
          <el-form-item label="启用同步">
            <el-switch v-model="configForm.enabled" />
          </el-form-item>
        </div>

        <div class="inline-actions">
          <el-button :loading="syncStore.loading" @click="syncStore.loadStatus()">刷新状态</el-button>
          <el-button type="primary" :loading="syncStore.loading" @click="saveConfig">保存配置</el-button>
          <el-button :loading="syncStore.syncing" :disabled="!status?.configured" @click="syncStore.runManualSync()">
            手动同步
          </el-button>
        </div>
      </el-form>

      <el-divider />

      <div v-if="status?.logged_in && !reloginMode" class="logged-in-card">
        <div>
          <span class="muted-text">当前已登录账号</span>
          <strong>{{ status.user_email || '已登录' }}</strong>
        </div>
        <div class="inline-actions">
          <el-button @click="reloginMode = true">重新登录 / 切换账号</el-button>
          <el-button :disabled="!status?.logged_in" @click="syncStore.logout()">退出登录</el-button>
        </div>
      </div>

      <el-form v-else label-position="top">
        <div class="field-row">
          <el-form-item label="登录邮箱">
            <el-input v-model="loginForm.email" placeholder="你的云同步账号邮箱" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="loginForm.password" type="password" show-password placeholder="账号密码" />
          </el-form-item>
        </div>

        <div class="inline-actions">
          <el-button type="primary" :loading="syncStore.loading" @click="login">登录云同步</el-button>
          <el-button :loading="syncStore.loading" @click="register">注册并登录</el-button>
          <el-button :disabled="!status?.logged_in" @click="syncStore.logout()">退出登录</el-button>
        </div>
      </el-form>

      <div class="sync-state-grid">
        <span>账号：{{ status?.user_email || '未登录' }}</span>
        <span>设备 ID：{{ status?.device_id || '--' }}</span>
        <span>最近 Push：{{ formatMaybeTime(status?.last_push_at) }}</span>
        <span>最近 Pull：{{ formatMaybeTime(status?.last_pull_at) }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { useSyncStore } from '@/stores/sync'
import { formatDateTime } from '@/utils/format'
import { notifyError } from '@/utils/message'

const syncStore = useSyncStore()
const status = computed(() => syncStore.status)
const DEFAULT_SYNC_SERVER_URL = 'https://schedule-sync.zenithy.art'

const configForm = reactive({
  server_url: DEFAULT_SYNC_SERVER_URL,
  device_name: '',
  enabled: false,
})

const loginForm = reactive({
  email: '',
  password: '',
})
const reloginMode = ref(false)

const statusTagType = computed(() => {
  if (!status.value?.configured) return 'info'
  if (status.value.last_error) return 'danger'
  if (status.value.pending_count > 0) return 'warning'
  if (status.value.logged_in) return 'success'
  return 'info'
})

watch(
  status,
  (value) => {
    if (!value) return
    configForm.server_url = value.server_url || DEFAULT_SYNC_SERVER_URL
    configForm.device_name = value.device_name || ''
    configForm.enabled = value.enabled
    loginForm.email = value.user_email || loginForm.email
  },
  { immediate: true },
)

function formatMaybeTime(value?: string | null): string {
  return value ? formatDateTime(value) : '--'
}

async function saveConfig(): Promise<void> {
  await syncStore.saveConfig({
    server_url: configForm.server_url || null,
    device_name: configForm.device_name || null,
    enabled: configForm.enabled,
  })
}

async function login(): Promise<void> {
  if (!loginForm.email || !loginForm.password) {
    notifyError('请填写登录邮箱和密码')
    return
  }

  await syncStore.login({
    email: loginForm.email,
    password: loginForm.password,
    server_url: configForm.server_url || null,
    device_name: configForm.device_name || null,
  })
  loginForm.password = ''
  reloginMode.value = false
}

async function register(): Promise<void> {
  if (!loginForm.email || !loginForm.password) {
    notifyError('请填写注册邮箱和密码')
    return
  }
  await syncStore.register({
    email: loginForm.email,
    password: loginForm.password,
    display_name: loginForm.email.split('@')[0],
    server_url: configForm.server_url || null,
    device_name: configForm.device_name || null,
  })
  loginForm.password = ''
  reloginMode.value = false
}

onMounted(() => {
  void syncStore.loadStatus()
})
</script>

<style scoped>
.panel-subtitle {
  margin-top: 4px;
}

.sync-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 12px;
  background: var(--app-card-subtle);
}

.metric-card span,
.sync-state-grid span {
  color: var(--app-text-muted);
  font-size: 12px;
}

.metric-card strong {
  display: block;
  margin-top: 6px;
  color: var(--app-text);
  font-size: 18px;
}

.sync-state-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 16px;
  padding-top: 4px;
}

.logged-in-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 14px;
  background: var(--app-card-subtle);
}

.logged-in-card strong {
  display: block;
  margin-top: 4px;
}

@media (max-width: 900px) {
  .sync-metrics,
  .sync-state-grid {
    grid-template-columns: 1fr;
  }
}
</style>
