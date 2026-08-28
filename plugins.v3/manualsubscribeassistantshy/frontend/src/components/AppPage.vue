<script setup>
import Page from './Page.vue'

/**
 * 侧栏全页：在主应用 #/plugin-app/:pluginId/:navKey 中渲染，占据主内容区。
 * 需在插件后端实现 get_sidebar_nav 才会出现在侧栏。
 */
const props = defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
  navKey: {
    type: String,
    default: 'main',
  },
  pluginId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['action'])
</script>

<template>
  <Page :api="api" :show_switch="false" @action="emit('action')" />
</template>
