<template>
  <div class="page-heading">
    <div class="page-heading-text">
      <div class="page-heading-eyebrow">{{ eyebrow }}</div>
      <h2>{{ title }}</h2>
      <p v-if="description">{{ description }}</p>
    </div>

    <div v-if="$slots.actions" class="page-heading-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
    eyebrow?: string
  }>(),
  {
    description: '',
    eyebrow: 'Workspace',
  },
)
</script>
