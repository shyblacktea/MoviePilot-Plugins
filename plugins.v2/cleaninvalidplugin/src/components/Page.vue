<template>
  <div class="cip-page">
    <div class="cip-scroll">
      <VCard flat class="cip-card mb-3">
        <VCardItem class="cip-header">
          <template #prepend>
            <VAvatar color="primary" variant="tonal" size="42" rounded="lg">
              <VIcon icon="mdi-puzzle-remove" size="23" />
            </VAvatar>
          </template>
          <VCardTitle class="text-h6">无效插件概览</VCardTitle>
          <VCardSubtitle class="text-caption">残留但无法加载的插件记录状态</VCardSubtitle>
          <template #append>
            <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" aria-label="刷新" @click="loadData" />
          </template>
        </VCardItem>
        <VDivider />
        <VCardText class="pa-3">
          <VAlert v-if="error" type="error" density="compact" variant="tonal" class="mb-3 text-caption" closable @click:close="error = ''">
            {{ error }}
          </VAlert>
          <div class="cip-stat-grid">
            <div class="cip-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="error" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-alert-circle-outline" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">无效记录</div>
              </div>
              <div class="text-subtitle-1 font-weight-bold">{{ invalidItems.length }}</div>
            </div>
            <div class="cip-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="success" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-source-branch-check" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">本地源可用</div>
              </div>
              <div class="text-subtitle-1 font-weight-bold">{{ localSourceCount }}</div>
            </div>
            <div class="cip-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="primary" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-folder-check-outline" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">运行目录存在</div>
              </div>
              <div class="text-subtitle-1 font-weight-bold">{{ runtimeExistsCount }}</div>
            </div>
          </div>
          <VAlert :type="invalidItems.length ? 'warning' : 'success'" variant="tonal" density="compact" icon="mdi-information" class="text-caption mt-3">
            {{ invalidItems.length ? '存在无法加载的插件记录，可切到配置页选择处理方式。' : '已安装插件记录与当前加载状态一致。' }}
          </VAlert>
          <VAlert v-if="lastResult.message" :type="lastResult.success ? 'success' : 'warning'" variant="tonal" density="compact" icon="mdi-history" class="text-caption mt-2">
            {{ lastResult.message }}
          </VAlert>
        </VCardText>
      </VCard>

      <div v-if="invalidItems.length" class="d-flex flex-column ga-3">
        <VCard v-for="plugin in invalidItems" :key="plugin.id" flat class="cip-card cip-plugin-card">
          <VCardItem class="py-2 px-3">
            <VCardTitle class="text-subtitle-1 cip-break">{{ plugin.id }}</VCardTitle>
            <template #append>
              <VChip :color="plugin.runtime_exists ? 'warning' : 'error'" size="small" variant="tonal">
                {{ plugin.runtime_exists ? '需检查' : '缺失' }}
              </VChip>
            </template>
          </VCardItem>
          <VDivider />
          <VCardText class="py-2 px-3">
            <div class="text-body-2 cip-break">状态：{{ plugin.status }}</div>
            <div class="cip-path">{{ plugin.runtime_path }}</div>
            <VChip :color="plugin.local_source_path ? 'success' : 'warning'" size="small" variant="tonal" class="mt-2">
              {{ plugin.local_source_path ? '本地源可重装' : '缺少本地源' }}
            </VChip>
          </VCardText>
        </VCard>
      </div>

      <div v-else-if="loading" class="text-center py-4">
        <VProgressCircular indeterminate color="primary" />
        <div class="mt-2 text-medium-emphasis">正在刷新状态...</div>
      </div>

      <div v-else class="text-center py-8">
        <VIcon size="48" color="success">mdi-check-circle-outline</VIcon>
        <div class="mt-2 text-medium-emphasis">没有无效插件</div>
        <div class="text-caption text-medium-emphasis mt-1">当前无需清理。</div>
      </div>
    </div>

    <VFooter class="cip-footer">
      <VContainer class="pa-0">
        <VAlert :type="invalidItems.length ? 'warning' : 'success'" variant="tonal" density="compact" class="text-caption mb-2">
          {{ summaryText }}
        </VAlert>
        <div class="d-flex align-center flex-wrap ga-1">
          <VBtn color="info" prepend-icon="mdi-cog-outline" variant="text" size="small" @click="emit('switch')">配置页</VBtn>
          <VSpacer class="cip-footer-spacer" />
          <VBtn color="grey" prepend-icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadData">刷新</VBtn>
          <VBtn color="grey" prepend-icon="mdi-close" variant="text" size="small" @click="emit('close')">关闭</VBtn>
        </div>
      </VContainer>
    </VFooter>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['action', 'switch', 'close'])

const loading = ref(false)
const error = ref('')
const invalidItems = ref([])
const lastResult = ref({})

const localSourceCount = computed(() => invalidItems.value.filter(item => item.local_source_path).length)
const runtimeExistsCount = computed(() => invalidItems.value.filter(item => item.runtime_exists).length)
const summaryText = computed(() => {
  if (loading.value) {
    return '正在刷新状态'
  }
  return invalidItems.value.length ? `发现 ${invalidItems.value.length} 个无效插件` : '插件状态正常'
})

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/invalid_plugins')
    const data = response?.data || response || {}
    invalidItems.value = data.items || []
    lastResult.value = data.last_result || {}
    emit('action')
  } catch (err) {
    error.value = err?.message || '读取插件状态失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.cip-page { height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.cip-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 16px; width: min(1120px, 100%); margin: 0 auto; }
.cip-card { border-radius: 14px; overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.cip-header { padding: 12px 16px; }
.cip-stat-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.cip-stat { border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; padding: 10px; min-width: 0; }
.cip-break { overflow-wrap: anywhere; }
.cip-path { margin-top: 3px; color: rgba(var(--v-theme-on-surface), 0.62); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }
.cip-footer { flex-shrink: 0; padding: 6px 12px; border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
@media (max-width: 760px) {
  .cip-page { height: 100dvh; }
  .cip-scroll { padding: 8px; }
  .cip-card { border-radius: 10px; }
  .cip-stat-grid { grid-template-columns: 1fr; }
  .cip-footer-spacer { display: none; }
  .cip-footer :deep(.v-btn) { flex: 1 1 auto; min-width: max-content; }
}
</style>
