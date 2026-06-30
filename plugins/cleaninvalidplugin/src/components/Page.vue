<template>
  <div class="main-container">
    <div ref="container" class="scroll-content">
      <v-card flat class="rounded border mb-3">
        <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
          <v-icon icon="mdi-puzzle-remove" class="mr-2" color="primary" size="small" />
          <span>无效插件概览</span>
          <v-spacer />
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            :loading="loading"
            aria-label="刷新"
            @click="loadData"
          />
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

          <v-row>
            <v-col cols="12" md="4">
              <div class="setting-item summary-item">
                <v-icon icon="mdi-alert-circle-outline" size="small" color="error" class="mr-3" />
                <span class="text-subtitle-2">无效记录</span>
                <strong>{{ invalidItems.length }}</strong>
              </div>
            </v-col>
            <v-col cols="12" md="4">
              <div class="setting-item summary-item">
                <v-icon icon="mdi-source-branch-check" size="small" color="success" class="mr-3" />
                <span class="text-subtitle-2">本地源可用</span>
                <strong>{{ localSourceCount }}</strong>
              </div>
            </v-col>
            <v-col cols="12" md="4">
              <div class="setting-item summary-item">
                <v-icon icon="mdi-folder-check-outline" size="small" color="primary" class="mr-3" />
                <span class="text-subtitle-2">运行目录存在</span>
                <strong>{{ runtimeExistsCount }}</strong>
              </div>
            </v-col>
          </v-row>

          <v-alert
            :type="invalidItems.length ? 'warning' : 'success'"
            variant="tonal"
            density="compact"
            icon="mdi-information"
            class="text-caption mt-2"
          >
            {{ invalidItems.length ? '存在无法加载的插件记录，可切到配置页选择处理方式。' : '已安装插件记录与当前加载状态一致。' }}
          </v-alert>

          <v-alert
            v-if="lastResult.message"
            :type="lastResult.success ? 'success' : 'warning'"
            variant="tonal"
            density="compact"
            icon="mdi-history"
            class="text-caption mt-2"
          >
            {{ lastResult.message }}
          </v-alert>
        </v-card-text>
      </v-card>

      <div v-if="invalidItems.length" class="grid grid-cols-1 gap-3">
        <v-card
          v-for="plugin in invalidItems"
          :key="plugin.id"
          elevation="2"
          hover
          class="transition-all duration-300 plugin-card"
        >
          <v-card-title class="px-3 pt-2 pb-1">
            <div class="font-bold text-lg break-words leading-tight">
              {{ plugin.id }}
            </div>
          </v-card-title>
          <div class="plugin-row px-3 pb-2">
            <div class="plugin-meta">
              <div class="text-sm break-all">状态: {{ plugin.status }}</div>
              <div class="path-line">{{ plugin.runtime_path }}</div>
            </div>
            <v-chip
              :color="plugin.runtime_exists ? 'warning' : 'error'"
              size="small"
              variant="tonal"
              class="status-chip"
            >
              {{ plugin.runtime_exists ? '需检查' : '缺失' }}
            </v-chip>
          </div>
          <v-card-actions class="px-3 pt-0 pb-2">
            <v-chip
              :color="plugin.local_source_path ? 'success' : 'warning'"
              size="small"
              variant="tonal"
            >
              {{ plugin.local_source_path ? '本地源可重装' : '缺少本地源' }}
            </v-chip>
          </v-card-actions>
        </v-card>
      </div>

      <div v-else-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate color="primary" />
        <div class="mt-2 text-gray-600">正在刷新状态...</div>
      </div>

      <div v-else class="text-center py-8">
        <v-icon size="48" color="success">mdi-check-circle-outline</v-icon>
        <div class="mt-2 text-gray-600">没有无效插件</div>
        <div class="text-caption text-medium-emphasis mt-1">当前无需清理。</div>
      </div>
    </div>

    <v-footer class="footer-bar">
      <v-container class="d-flex flex-column">
        <div class="d-flex align-center mb-2">
          <v-alert
            :type="invalidItems.length ? 'warning' : 'success'"
            variant="tonal"
            density="compact"
            class="flex-grow-1 text-caption"
          >
            {{ summaryText }}
          </v-alert>
        </div>
        <v-card-actions class="px-2 py-1 d-flex justify-space-between action-bar">
          <v-btn
            color="info"
            prepend-icon="mdi-cog-outline"
            variant="text"
            size="small"
            @click="emit('switch')"
          >
            配置页
          </v-btn>
          <v-spacer class="action-spacer" />
          <v-btn
            color="grey"
            prepend-icon="mdi-refresh"
            variant="text"
            size="small"
            :loading="loading"
            @click="loadData"
          >
            刷新
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
      </v-container>
    </v-footer>
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
const container = ref(null)

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
.main-container {
  height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scroll-content {
  height: 75vh;
  overflow-y: auto;
  padding: 16px;
}

.footer-bar {
  flex-shrink: 0;
  padding: 0 5px;
  display: flex;
  flex-direction: column;
}

.bg-primary-lighten-5 {
  background-color: rgba(var(--v-theme-primary), 0.07);
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: minmax(0, 1fr);
}

.gap-3 {
  gap: 0.75rem;
}

.font-bold {
  font-weight: 700;
}

.text-lg {
  font-size: 1.125rem;
}

.text-sm {
  font-size: 0.875rem;
}

.break-words {
  overflow-wrap: anywhere;
}

.break-all {
  word-break: break-all;
}

.leading-tight {
  line-height: 1.25;
}

.transition-all {
  transition-property: all;
}

.duration-300 {
  transition-duration: 0.3s;
}

.text-center {
  text-align: center;
}

.py-4 {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.py-8 {
  padding-top: 2rem;
  padding-bottom: 2rem;
}

.mt-1 {
  margin-top: 0.25rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.text-gray-600 {
  color: rgba(var(--v-theme-on-surface), 0.68);
}

.setting-item {
  border-radius: 8px;
  transition: all 0.2s ease;
  padding: 0.5rem;
  height: 100%;
  display: flex;
  align-items: center;
}

.setting-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.summary-item {
  gap: 0.25rem;
}

.summary-item strong {
  margin-left: auto;
  font-size: 1.25rem;
  line-height: 1;
}

.text-subtitle-2 {
  font-size: 0.875rem !important;
  font-weight: 500;
  white-space: nowrap;
  margin-right: 0.5rem;
}

.plugin-card {
  overflow: hidden;
}

.plugin-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.plugin-meta {
  min-width: 0;
  flex: 1;
}

.path-line {
  margin-top: 3px;
  color: rgba(var(--v-theme-on-surface), 0.62);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.status-chip {
  flex-shrink: 0;
}

.action-bar {
  gap: 0.25rem;
  flex-wrap: wrap;
}

@media (max-width: 600px) {
  .main-container {
    height: 88vh;
  }

  .scroll-content {
    height: 68vh;
    padding: 8px;
  }

  .plugin-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .status-chip {
    align-self: flex-start;
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
