<template>
  <div class="cip-config">
    <VCard flat class="cip-card">
      <VCardItem class="cip-header">
        <template #prepend>
          <VAvatar color="primary" variant="tonal" size="44" rounded="lg">
            <VIcon icon="mdi-delete-sweep" size="24" />
          </VAvatar>
        </template>
        <VCardTitle class="text-h6">清理无效插件</VCardTitle>
        <VCardSubtitle class="text-caption">{{ currentMain.desc }}</VCardSubtitle>
        <template #append>
          <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" aria-label="刷新" @click="loadInvalidPlugins" />
        </template>
      </VCardItem>
      <VDivider />

      <div class="cip-body">
        <nav class="cip-nav">
          <VList density="comfortable" nav class="py-2 cip-nav-list">
            <VListItem
              v-for="item in mainTabs"
              :key="item.key"
              :active="activeMain === item.key"
              color="primary"
              rounded="lg"
              class="cip-nav-item"
              @click="activeMain = item.key"
            >
              <template #prepend><VIcon :icon="item.icon" class="cip-nav-icon" /></template>
              <VListItemTitle class="cip-nav-title">{{ item.title }}</VListItemTitle>
            </VListItem>
          </VList>
        </nav>

        <section class="cip-content">
          <VAlert v-if="error" type="error" density="compact" variant="tonal" class="ma-3 mb-0 text-caption" closable @click:close="error = ''">
            {{ error }}
          </VAlert>
          <VAlert v-else-if="!loading && invalidItems.length === 0" type="success" density="compact" variant="tonal" class="ma-3 mb-0 text-caption">
            当前没有需要处理的无效插件。
          </VAlert>

          <div class="cip-window">
            <div class="cip-stat-grid ma-4 mb-0">
              <div class="cip-stat">
                <div class="d-flex align-center ga-2 mb-1">
                  <VAvatar color="error" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-alert-circle-outline" size="17" /></VAvatar>
                  <div class="text-caption text-medium-emphasis">无效插件</div>
                </div>
                <div class="text-subtitle-1 font-weight-bold">{{ invalidItems.length }}</div>
              </div>
              <div class="cip-stat">
                <div class="d-flex align-center ga-2 mb-1">
                  <VAvatar color="primary" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-checkbox-marked-circle-outline" size="17" /></VAvatar>
                  <div class="text-caption text-medium-emphasis">已选择</div>
                </div>
                <div class="text-subtitle-1 font-weight-bold">{{ selectedCount }}</div>
              </div>
              <div class="cip-stat">
                <div class="d-flex align-center ga-2 mb-1">
                  <VAvatar color="success" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-source-branch-check" size="17" /></VAvatar>
                  <div class="text-caption text-medium-emphasis">本地源</div>
                </div>
                <div class="text-subtitle-1 font-weight-bold">{{ localSourceCount }}</div>
              </div>
            </div>

            <div v-show="activeMain === 'target'" class="cip-pane">
              <div class="cip-section-title">处理对象</div>
              <VSelect
                v-model="config.invalid_plugin_ids"
                :items="invalidItems"
                item-title="title"
                item-value="id"
                label="插件"
                variant="outlined"
                density="compact"
                multiple
                chips
                closable-chips
                clearable
                :loading="loading"
                :disabled="loading || invalidItems.length === 0"
                hide-details="auto"
              >
                <template #item="{ props: itemProps, item }">
                  <VListItem v-bind="itemProps">
                    <template #append>
                      <VChip :color="item.raw.local_source_path ? 'success' : 'warning'" size="small" variant="tonal">
                        {{ item.raw.local_source_path ? '可重装' : '需清理' }}
                      </VChip>
                    </template>
                  </VListItem>
                </template>
              </VSelect>

              <div class="cip-plugin-list mt-3">
                <VList v-if="invalidItems.length" lines="two" density="compact">
                  <VListItem
                    v-for="plugin in invalidItems"
                    :key="plugin.id"
                    :title="plugin.id"
                    :subtitle="plugin.status"
                  >
                    <template #prepend>
                      <VCheckboxBtn :model-value="config.invalid_plugin_ids.includes(plugin.id)" @update:model-value="togglePlugin(plugin.id)" />
                    </template>
                    <template #append>
                      <VChip :color="plugin.runtime_exists ? 'warning' : 'error'" size="small" variant="tonal">
                        {{ plugin.runtime_exists ? '目录异常' : '目录缺失' }}
                      </VChip>
                    </template>
                  </VListItem>
                </VList>
                <div v-else class="cip-empty">
                  <VIcon icon="mdi-check-circle-outline" size="36" color="success" />
                  <span>没有待处理记录</span>
                </div>
              </div>
            </div>

            <div v-show="activeMain === 'action'" class="cip-pane">
              <div class="cip-section-title">操作方式</div>
              <VRow align="center">
                <VCol cols="12" md="7">
                  <VRadioGroup v-model="config.action_mode" inline density="compact" hide-details :disabled="invalidItems.length === 0">
                    <VRadio label="清理记录" value="clean" color="error" />
                    <VRadio label="重新安装" value="reinstall" color="primary" />
                  </VRadioGroup>
                </VCol>
                <VCol cols="12" md="5" class="d-flex justify-end ga-2 flex-wrap">
                  <VBtn color="primary" variant="text" size="small" prepend-icon="mdi-check-all" :disabled="invalidItems.length === 0" @click="selectAll">全选</VBtn>
                  <VBtn color="secondary" variant="text" size="small" prepend-icon="mdi-close" :disabled="selectedCount === 0" @click="clearSelection">清空</VBtn>
                </VCol>
              </VRow>
              <VAlert :type="config.action_mode === 'reinstall' ? 'warning' : 'info'" variant="tonal" density="compact" icon="mdi-information" class="text-caption mt-3">
                {{ actionHint }}
              </VAlert>
            </div>
          </div>

          <VDivider />
          <div class="cip-actions d-flex align-center flex-wrap ga-1">
            <VBtn color="info" prepend-icon="mdi-view-dashboard" variant="text" size="small" @click="emit('switch')">数据页</VBtn>
            <VSpacer class="cip-action-spacer" />
            <VBtn color="grey" prepend-icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadInvalidPlugins">刷新</VBtn>
            <VBtn color="primary" prepend-icon="mdi-content-save" variant="text" size="small" :disabled="selectedCount === 0" @click="saveConfig">保存并执行</VBtn>
            <VBtn color="grey" prepend-icon="mdi-close" variant="text" size="small" @click="emit('close')">关闭</VBtn>
          </div>
        </section>
      </div>
    </VCard>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
  api: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['save', 'close', 'switch'])

const loading = ref(false)
const error = ref('')
const invalidItems = ref([])
const activeMain = ref('target')

const mainTabs = [
  { key: 'target', title: '处理对象', icon: 'mdi-playlist-check', desc: '选择需要清理或重装的无效插件。' },
  { key: 'action', title: '操作方式', icon: 'mdi-tune', desc: '清理记录或从本地源重新安装。' },
]

const currentMain = computed(() => mainTabs.find(i => i.key === activeMain.value) || mainTabs[0])

const config = reactive({
  invalid_plugin_ids: [],
  action_mode: 'clean',
})

const selectedCount = computed(() => config.invalid_plugin_ids.length)
const localSourceCount = computed(() => invalidItems.value.filter(item => item.local_source_path).length)
const actionHint = computed(() => {
  if (config.action_mode === 'reinstall') {
    return '重新安装会优先使用本地插件源；找不到来源时会保留记录，并保留原插件配置。'
  }
  return '清理记录只移除已安装列表中的选中项和无效运行目录，不删除原插件配置。'
})

function applyInitialConfig() {
  config.invalid_plugin_ids = Array.isArray(props.initialConfig.invalid_plugin_ids)
    ? [...props.initialConfig.invalid_plugin_ids]
    : []
  config.action_mode = props.initialConfig.action_mode || 'clean'
}

async function loadInvalidPlugins() {
  loading.value = true
  error.value = ''
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/invalid_plugins')
    const data = response?.data || response || {}
    invalidItems.value = data.items || []
    const validIds = new Set(invalidItems.value.map(item => item.id))
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => validIds.has(id))
  } catch (err) {
    error.value = err?.message || '读取无效插件列表失败'
  } finally {
    loading.value = false
  }
}

function togglePlugin(pluginId) {
  if (config.invalid_plugin_ids.includes(pluginId)) {
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => id !== pluginId)
    return
  }
  config.invalid_plugin_ids = [...config.invalid_plugin_ids, pluginId]
}

function selectAll() {
  config.invalid_plugin_ids = invalidItems.value.map(item => item.id)
}

function clearSelection() {
  config.invalid_plugin_ids = []
}

function saveConfig() {
  emit('save', {
    invalid_plugin_ids: [...config.invalid_plugin_ids],
    action_mode: config.action_mode,
  })
}

onMounted(() => {
  applyInitialConfig()
  loadInvalidPlugins()
})
</script>

<style scoped>
.cip-config { width: min(1120px, calc(100vw - 48px)); max-width: 100%; padding: 8px; margin: 0 auto; }
.cip-card { width: 100%; display: flex; flex-direction: column; border-radius: 14px; overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.cip-header { padding: 14px 18px; }
.cip-body { flex: 1 1 auto; min-height: 0; display: flex; }
.cip-nav { width: 160px; flex: 0 0 160px; border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); background: rgba(var(--v-theme-on-surface), .02); }
.cip-nav-item { margin: 2px 8px; }
.cip-content { flex: 1 1 auto; min-width: 0; min-height: 0; display: flex; flex-direction: column; }
.cip-window { flex: 1 1 auto; min-height: 0; overflow-y: auto; }
.cip-pane { padding: 16px 20px; }
.cip-section-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: rgb(var(--v-theme-primary)); }
.cip-stat-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.cip-stat { border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; padding: 10px; min-width: 0; }
.cip-plugin-list { max-height: 320px; overflow-y: auto; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; }
.cip-empty { min-height: 112px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem; color: rgba(var(--v-theme-on-surface), 0.68); font-size: 0.875rem; }
.cip-actions { padding: 10px 18px; }
@media (max-width: 760px) {
  .cip-config { width: 100%; padding: 0; }
  .cip-card { border-radius: 0; border: none; }
  .cip-header { padding: 8px 10px; }
  .cip-body { flex-direction: column; }
  .cip-nav { width: 100%; flex: 0 0 auto; border-right: none; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); overflow-x: auto; overflow-y: hidden; scrollbar-width: none; }
  .cip-nav::-webkit-scrollbar { display: none; }
  .cip-nav-list { display: flex; flex-wrap: nowrap; gap: 4px; min-width: max-content; padding: 5px 8px !important; }
  .cip-nav-item { flex: 0 0 auto; min-width: 96px; min-height: 34px !important; margin: 0; padding-inline: 8px; }
  .cip-nav-title { font-size: 12px; white-space: nowrap; }
  .cip-stat-grid { grid-template-columns: 1fr; }
  .cip-pane { padding: 12px 12px; }
  .cip-action-spacer { display: none; }
  .cip-actions :deep(.v-btn) { flex: 1 1 auto; min-width: max-content; }
}
</style>
