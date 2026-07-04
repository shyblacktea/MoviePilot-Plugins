<template>
  <div class="plugin-config">
    <v-card flat class="rounded border">
      <v-card-title class="title-bar">
        <v-icon icon="mdi-playlist-star" color="primary" size="small" />
        <span>订阅下载增强</span>
        <v-spacer />
        <v-btn icon="mdi-refresh" variant="text" size="small" :loading="loading" aria-label="刷新" @click="loadOptions" />
      </v-card-title>

      <v-card-text class="content">
        <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-3 text-caption" closable>
          {{ error }}
        </v-alert>

        <v-form @submit.prevent="saveConfig">
          <section class="config-section">
            <div class="section-title">
              <v-icon icon="mdi-tune-variant" color="primary" size="small" />
              <span>扫描设置</span>
            </div>
            <v-row>
              <v-col cols="12" md="4">
                <v-switch v-model="config.enabled" color="primary" label="启用" density="compact" hide-details />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model.number="config.delay_days"
                  type="number"
                  min="0"
                  label="宽限天数"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="config.cron"
                  label="Cron"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :error-messages="cronError"
                  hint="每 6 小时建议写 0 */6 * * *"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="config.selected_categories"
                  :items="categories"
                  item-title="title"
                  item-value="value"
                  label="二级分类"
                  variant="outlined"
                  density="compact"
                  multiple
                  chips
                  closable-chips
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="config.search_sites"
                  :items="siteOptions"
                  item-title="title"
                  item-value="value"
                  label="PT搜索范围"
                  variant="outlined"
                  density="compact"
                  multiple
                  chips
                  closable-chips
                  clearable
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model.number="config.max_scan_subscribes"
                  type="number"
                  min="1"
                  label="订阅部数通知上限"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                />
              </v-col>
            </v-row>
          </section>

          <section class="config-section">
            <div class="section-title">
              <v-icon icon="mdi-message-badge-outline" color="primary" size="small" />
              <span>通知权限</span>
            </div>
            <v-row>
              <v-col cols="12" md="6">
                <v-switch v-model="config.notify_tg" color="primary" label="Telegram 独立通知" density="compact" hide-details />
              </v-col>
              <v-col cols="12" md="6">
                <v-switch
                  v-model="config.allow_tg_rule_update"
                  color="warning"
                  label="允许 TG 修改订阅规则"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>
          </section>

          <section class="config-section">
            <div class="section-title">
              <v-icon icon="mdi-broom" color="warning" size="small" />
              <span>全集包清理</span>
            </div>
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="config.season_pack_cleanup"
                  :items="seasonPackCleanupOptions"
                  item-title="title"
                  item-value="value"
                  label="最终集整季包清理"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-switch
                  v-model="config.season_pack_full_download"
                  color="warning"
                  label="qB 整季包全选下载"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>
          </section>

          <v-card-actions class="action-bar">
            <v-btn color="info" prepend-icon="mdi-view-dashboard-outline" variant="text" size="small" @click="emit('switch')">数据页</v-btn>
            <v-spacer class="action-spacer" />
            <v-btn color="grey" prepend-icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadOptions">刷新</v-btn>
            <v-btn color="primary" prepend-icon="mdi-content-save" variant="text" size="small" @click="saveConfig">保存</v-btn>
            <v-btn color="grey" prepend-icon="mdi-close" variant="text" size="small" @click="emit('close')">关闭</v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

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
const categories = ref([])
const siteOptions = ref([])
const cronError = ref('')
const seasonPackCleanupOptions = [
  { title: '关闭', value: 'off' },
  { title: '仅删转移记录', value: 'record' },
  { title: '删转移记录+源文件', value: 'source' },
]

const config = reactive({
  enabled: false,
  delay_days: 1,
  cron: '0 9 * * *',
  selected_categories: [],
  search_sites: [],
  max_scan_subscribes: 20,
  notify_tg: true,
  allow_tg_rule_update: false,
  season_pack_cleanup: 'off',
  season_pack_full_download: false,
})

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

function applyInitialConfig() {
  Object.assign(config, {
    ...config,
    ...props.initialConfig,
    selected_categories: Array.isArray(props.initialConfig.selected_categories)
      ? [...props.initialConfig.selected_categories]
      : [],
    search_sites: Array.isArray(props.initialConfig.search_sites)
      ? [...props.initialConfig.search_sites]
      : [],
    season_pack_cleanup: props.initialConfig.season_pack_cleanup || 'off',
    season_pack_full_download: Boolean(props.initialConfig.season_pack_full_download),
  })
}

async function loadOptions() {
  loading.value = true
  error.value = ''
  try {
    const [categoryResponse, siteResponse] = await Promise.all([
      props.api.get('plugin/SubscribePlus/categories'),
      props.api.get('plugin/SubscribePlus/sites'),
    ])
    categories.value = unwrap(categoryResponse).items || []
    siteOptions.value = (unwrap(siteResponse).items || []).map(item => ({
      title: item.name || item.title || item.id || item.value,
      value: String(item.id ?? item.value ?? ''),
    })).filter(item => item.value)
    const staleUncategorizedOnly =
      config.selected_categories.length === 1 &&
      config.selected_categories[0] === '未分类' &&
      categories.value.some(item => item.value !== '未分类')
    if (!config.selected_categories.length || staleUncategorizedOnly) {
      config.selected_categories = categories.value.map(item => item.value)
    }
  } catch (err) {
    error.value = err?.message || '读取配置选项失败'
  } finally {
    loading.value = false
  }
}

function validateCron(value) {
  const parts = String(value || '').trim().split(/\s+/)
  if (parts.length !== 5) return 'Cron 需要 5 段，例如 0 */6 * * *'
  const ranges = [59, 23, 31, 12, 7]
  const invalid = parts.find((part, index) => {
    const match = part.match(/^\*\/(\d+)$/)
    return match && Number(match[1]) > ranges[index]
  })
  if (invalid) return `${invalid} 超出该 Cron 字段范围`
  return ''
}

function saveConfig() {
  cronError.value = validateCron(config.cron)
  if (cronError.value) return
  emit('save', {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    search_sites: Array.isArray(config.search_sites) ? [...config.search_sites] : [],
  })
}

onMounted(() => {
  applyInitialConfig()
  loadOptions()
})
</script>

<style scoped>
.plugin-config {
  max-width: 80rem;
  margin: 0 auto;
  padding: 0.5rem;
}

.title-bar,
.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-bar {
  padding: 0.5rem 0.75rem;
  background-color: rgba(var(--v-theme-primary), 0.07);
  font-size: 1rem;
}

.content {
  padding: 0.75rem;
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.config-section {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.section-title {
  min-height: 32px;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  padding: 0.25rem 0;
}

.plugin-config :deep(.v-field__input),
.plugin-config :deep(.v-select__selection) {
  min-width: 0;
}

@media (max-width: 600px) {
  .plugin-config {
    padding: 0.25rem;
  }

  .action-spacer {
    display: none;
  }

  .action-bar :deep(.v-btn) {
    flex: 1 1 auto;
    min-width: max-content;
  }

  .plugin-config :deep(.v-chip) {
    max-width: 100%;
  }
}
</style>
