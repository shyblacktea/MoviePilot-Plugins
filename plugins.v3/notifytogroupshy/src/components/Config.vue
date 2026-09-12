<template>
  <Page :api="props.api" :initial-config="props.initialConfig" @close="emit('close')" />
</template>

<script setup>
import Page from './Page.vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  initialConfig: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close'])
</script>
