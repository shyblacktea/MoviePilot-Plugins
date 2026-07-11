<template>
  <Config :initial-config="initialConfig" :api="api" @save="onSave" @close="emit('close')" @switch="emit('switch')" />
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Config from './Config.vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['action', 'switch', 'close'])

// 数据页与配置页共用同一 UI；数据页入口自行拉取当前配置作为初始值
const initialConfig = ref({})

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

async function onSave(payload) {
  try {
    await props.api.post('plugin/SubscribePlus/config', payload)
    emit('action')
  } catch (err) {
    console.error('保存配置失败', err)
  }
}

onMounted(async () => {
  try {
    const response = await props.api.get('plugin/SubscribePlus/config')
    initialConfig.value = unwrap(response) || {}
  } catch (err) {
    console.error('读取配置失败', err)
  }
})
</script>
