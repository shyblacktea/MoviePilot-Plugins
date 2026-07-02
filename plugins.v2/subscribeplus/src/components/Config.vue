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
                <v-text-field v-model="config.cron" label="Cron" variant="outlined" density="compact" hide-details="auto" />
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
              <v-col cols="12" md="3">
                <v-text-field
                  v-model.number="config.max_scan_subscribes"
                  type="number"
                  min="1"
                  label="单次最多诊断"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                />
              </v-col>
            </v-row>
          </section>

          <section class="config-section">
            <div class="section-title">
              <v-icon icon="mdi-server-network" color="primary" size="small" />
              <span>分类站点范围</span>
            </div>
            <v-row>
              <v-col v-for="category in selectedCategoryItems" :key="category.value" cols="12" md="6">
                <v-select
                  v-model="config.category_sites[category.value]"
                  :items="sites"
                  item-title="name"
                  item-value="id"
                  :label="category.title"
                  variant="outlined"
                  density="compact"
                  multiple
                  chips
                  closable-chips
                  clearable
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
import { computed, onMounted, reactive, ref, watch } from 'vue'

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
const sites = ref([])

const config = reactive({
  enabled: false,
  delay_days: 1,
  cron: '0 9 * * *',
  selected_categories: [],
  use_moviepilot_search_sites: true,
  category_sites: {},
  max_scan_subscribes: 20,
  notify_tg: true,
  allow_tg_rule_update: false,
})

const selectedCategoryItems = computed(() => {
  const selected = new Set(config.selected_categories)
  return categories.value.filter(item => selected.has(item.value))
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
    category_sites: props.initialConfig.category_sites
      ? { ...props.initialConfig.category_sites }
      : {},
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
    sites.value = unwrap(siteResponse).items || []
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

function saveConfig() {
  const selected = new Set(config.selected_categories)
  const categorySites = Object.fromEntries(
    Object.entries(config.category_sites || {}).filter(([category]) => selected.has(category))
  )
  emit('save', {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    category_sites: categorySites,
  })
}

watch(
  () => config.selected_categories,
  categoriesValue => {
    for (const category of categoriesValue) {
      if (!Array.isArray(config.category_sites[category])) {
        config.category_sites[category] = []
      }
    }
  },
  { deep: true }
)

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
}
</style>
