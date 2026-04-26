<template>
  <div class="empty-state">
    <el-empty :description="description">
      <template #image>
        <div class="empty-icon">{{ icon }}</div>
      </template>
      <template #description>
        <div>
          <strong>{{ title }}</strong>
          <p class="muted-text">{{ description }}</p>
        </div>
      </template>
      <slot />
    </el-empty>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description: string
    icon?: string
  }>(),
  {
    icon: '·',
  },
)
</script>

<style scoped>
.empty-state {
  padding: 20px 0;
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: linear-gradient(180deg, #eef4fb, #dde8f5);
  color: var(--app-primary);
  display: grid;
  place-items: center;
  font-size: 32px;
  font-weight: 800;
}

p {
  margin: 8px 0 0;
}
</style>
