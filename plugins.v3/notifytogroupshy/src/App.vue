<template>
  <Page :api="props.api" @close="emit('close')" />
</template>

<script setup>
import Page from './components/Page.vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close'])
</script>
