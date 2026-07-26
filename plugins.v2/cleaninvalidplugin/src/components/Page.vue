<template>
  <div class="page-shell">
    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      density="compact"
      closable
      class="ma-2"
      @click:close="error = ''"
    >
      {{ error }}
    </v-alert>

    <div v-if="loading" class="loading-state">
      <v-progress-circular indeterminate color="primary" />
      <span>正在读取插件状态...</span>
    </div>

    <Config
      v-else
      :initial-config="initialConfig"
      :api="api"
      :show-switch="false"
      @action="emit('action')"
      @close="emit('close')"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Config from './Config.vue'

const props = defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['action', 'switch', 'close'])

const loading = ref(true)
const error = ref('')
const initialConfig = ref({})

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

async function loadConfig() {
  const response = await props.api.get('plugin/CleanInvalidPlugin')
  initialConfig.value = unwrap(response) || {}
}

onMounted(async () => {
  try {
    await loadConfig()
  } catch (err) {
    error.value = err?.message || '读取插件配置失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-shell {
  min-height: min(86vh, 760px);
}

.loading-state {
  min-height: 18rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.68);
}
</style>
