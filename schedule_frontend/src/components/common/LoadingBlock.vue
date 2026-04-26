<template>
  <el-card class="panel-card">
    <div class="loading-block">
      <el-skeleton :rows="rows" animated />
      <div class="muted-text">{{ text }}</div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string
    rows?: number
  }>(),
  {
    text: '正在加载数据...',
    rows: 4,
  },
)
</script>

<style scoped>
.loading-block {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
