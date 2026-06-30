<template>
  <div class="plugin-config">
    <v-card flat class="rounded border">
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-delete-sweep" class="mr-2" color="primary" size="small" />
        <span>清理无效插件配置</span>
      </v-card-title>

      <v-card-text class="px-3 py-2">
        <v-alert
          v-if="error"
          type="error"
          density="compact"
          class="mb-2 text-caption"
          variant="tonal"
          closable
        >
          {{ error }}
        </v-alert>

        <v-alert
          v-else-if="!loading && invalidItems.length === 0"
          type="success"
          density="compact"
          class="mb-2 text-caption"
          variant="tonal"
        >
          当前没有需要处理的无效插件。
        </v-alert>

        <v-form @submit.prevent="saveConfig">
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-chart-box-outline" class="mr-2" color="primary" size="small" />
              <span>状态概览</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12" md="4">
                  <div class="setting-item stat-item">
                    <v-icon icon="mdi-alert-circle-outline" size="small" color="error" class="mr-3" />
                    <div class="stat-copy">
                      <span class="text-subtitle-2">无效插件</span>
                      <strong>{{ invalidItems.length }}</strong>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="4">
                  <div class="setting-item stat-item">
                    <v-icon icon="mdi-checkbox-marked-circle-outline" size="small" color="primary" class="mr-3" />
                    <div class="stat-copy">
                      <span class="text-subtitle-2">已选择</span>
                      <strong>{{ selectedCount }}</strong>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="4">
                  <div class="setting-item stat-item">
                    <v-icon icon="mdi-source-branch-check" size="small" color="success" class="mr-3" />
                    <div class="stat-copy">
                      <span class="text-subtitle-2">本地源</span>
                      <strong>{{ localSourceCount }}</strong>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-playlist-check" class="mr-2" color="primary" size="small" />
              <span>处理对象</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12">
                  <div class="setting-item select-item">
                    <v-select
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
                        <v-list-item v-bind="itemProps">
                          <template #append>
                            <v-chip
                              :color="item.raw.local_source_path ? 'success' : 'warning'"
                              size="small"
                              variant="tonal"
                            >
                              {{ item.raw.local_source_path ? '可重装' : '需清理' }}
                            </v-chip>
                          </template>
                        </v-list-item>
                      </template>
                    </v-select>
                  </div>
                </v-col>
              </v-row>

              <div class="plugin-list mt-2">
                <v-list v-if="invalidItems.length" lines="two" density="compact">
                  <v-list-item
                    v-for="plugin in invalidItems"
                    :key="plugin.id"
                    :title="plugin.id"
                    :subtitle="plugin.status"
                  >
                    <template #prepend>
                      <v-checkbox-btn
                        :model-value="config.invalid_plugin_ids.includes(plugin.id)"
                        @update:model-value="togglePlugin(plugin.id)"
                      />
                    </template>
                    <template #append>
                      <v-chip
                        :color="plugin.runtime_exists ? 'warning' : 'error'"
                        size="small"
                        variant="tonal"
                      >
                        {{ plugin.runtime_exists ? '目录异常' : '目录缺失' }}
                      </v-chip>
                    </template>
                  </v-list-item>
                </v-list>
                <div v-else class="empty-panel">
                  <v-icon icon="mdi-check-circle-outline" size="36" color="success" />
                  <span>没有待处理记录</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-tune" class="mr-2" color="primary" size="small" />
              <span>操作方式</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12" md="7">
                  <div class="setting-item mode-item">
                    <v-radio-group
                      v-model="config.action_mode"
                      inline
                      density="compact"
                      hide-details
                      :disabled="invalidItems.length === 0"
                    >
                      <v-radio label="清理记录" value="clean" color="error" />
                      <v-radio label="重新安装" value="reinstall" color="primary" />
                    </v-radio-group>
                  </div>
                </v-col>
                <v-col cols="12" md="5">
                  <div class="setting-item quick-actions">
                    <v-btn
                      color="primary"
                      variant="text"
                      size="small"
                      prepend-icon="mdi-check-all"
                      :disabled="invalidItems.length === 0"
                      @click="selectAll"
                    >
                      全选
                    </v-btn>
                    <v-btn
                      color="secondary"
                      variant="text"
                      size="small"
                      prepend-icon="mdi-close"
                      :disabled="selectedCount === 0"
                      @click="clearSelection"
                    >
                      清空
                    </v-btn>
                  </div>
                </v-col>
              </v-row>

              <v-alert
                :type="config.action_mode === 'reinstall' ? 'warning' : 'info'"
                variant="tonal"
                density="compact"
                icon="mdi-information"
                class="text-caption"
              >
                {{ actionHint }}
              </v-alert>
            </v-card-text>
          </v-card>

          <v-card-actions class="px-2 py-1 action-bar">
            <v-btn
              color="info"
              prepend-icon="mdi-view-dashboard"
              variant="text"
              size="small"
              @click="emit('switch')"
            >
              数据页
            </v-btn>
            <v-spacer class="action-spacer" />
            <v-btn
              color="grey"
              prepend-icon="mdi-refresh"
              variant="text"
              size="small"
              :loading="loading"
              @click="loadInvalidPlugins"
            >
              刷新
            </v-btn>
            <v-btn
              color="primary"
              prepend-icon="mdi-content-save"
              variant="text"
              size="small"
              :disabled="selectedCount === 0"
              @click="saveConfig"
            >
              保存并执行
            </v-btn>
            <v-btn
              color="grey"
              prepend-icon="mdi-close"
              variant="text"
              size="small"
              @click="emit('close')"
            >
              关闭
            </v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
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
.plugin-config {
  max-width: 80rem;
  margin: 0 auto;
  padding: 0.5rem;
}

.bg-primary-lighten-5 {
  background-color: rgba(var(--v-theme-primary), 0.07);
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.config-card {
  background-image:
    linear-gradient(
      to right,
      rgba(var(--v-theme-surface), 0.98),
      rgba(var(--v-theme-surface), 0.95)
    ),
    repeating-linear-gradient(
      45deg,
      rgba(var(--v-theme-primary), 0.03),
      rgba(var(--v-theme-primary), 0.03) 10px,
      transparent 10px,
      transparent 20px
    );
  background-attachment: fixed;
  box-shadow: 0 1px 2px rgba(var(--v-border-color), 0.05) !important;
  transition: all 0.3s ease;
}

.config-card:hover {
  box-shadow: 0 3px 6px rgba(var(--v-border-color), 0.1) !important;
}

.setting-item {
  border-radius: 8px;
  transition: all 0.2s ease;
  padding: 0.5rem;
  min-height: 100%;
  display: flex;
  align-items: center;
}

.setting-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.stat-item {
  justify-content: flex-start;
}

.stat-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.stat-copy strong {
  font-size: 1.35rem;
  line-height: 1;
}

.text-subtitle-2 {
  font-size: 0.875rem !important;
  font-weight: 500;
  white-space: nowrap;
  margin-right: 0.5rem;
}

.select-item {
  display: block;
}

.plugin-list {
  max-height: 320px;
  overflow-y: auto;
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 8px;
}

.empty-panel {
  min-height: 112px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: rgba(var(--v-theme-on-surface), 0.68);
  font-size: 0.875rem;
}

.mode-item :deep(.v-selection-control-group) {
  gap: 1rem;
}

.quick-actions {
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

@media (max-width: 600px) {
  .plugin-config {
    padding: 0.25rem;
  }

  .stat-copy {
    justify-content: flex-start;
  }

  .quick-actions {
    justify-content: flex-start;
  }

  .action-spacer {
    display: none;
  }

  .action-bar :deep(.v-btn) {
    flex: 1 1 auto;
    min-width: max-content;
  }
}
</style>
