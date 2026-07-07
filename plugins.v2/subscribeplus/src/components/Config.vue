<template>
  <div class="sp-config">
    <VCard flat class="sp-card">
      <VCardItem class="sp-header">
        <template #prepend>
          <VAvatar color="primary" variant="tonal" size="44" rounded="lg" class="sp-header-avatar">
            <VIcon icon="mdi-playlist-star" size="24" />
          </VAvatar>
        </template>
        <VCardTitle class="text-h6 sp-header-title">订阅下载增强</VCardTitle>
        <VCardSubtitle class="text-caption sp-header-subtitle">{{ currentMain.desc }}</VCardSubtitle>
        <template #append>
          <VSwitch v-model="config.enabled" color="success" hide-details inset class="sp-enable-switch" :label="config.enabled ? '已启用' : '已停用'" />
        </template>
      </VCardItem>
      <VDivider />

      <div class="sp-body">
        <nav class="sp-nav">
          <VList density="comfortable" nav class="py-2 sp-nav-list">
            <VListItem
              v-for="item in mainTabs"
              :key="item.key"
              :active="activeMain === item.key"
              color="primary"
              rounded="lg"
              class="sp-nav-item"
              @click="activeMain = item.key"
            >
              <template #prepend><VIcon :icon="item.icon" class="sp-nav-icon" /></template>
              <VListItemTitle class="sp-nav-title">{{ item.title }}</VListItemTitle>
            </VListItem>
          </VList>
        </nav>

        <section class="sp-content">
          <VAlert v-if="error" type="error" variant="tonal" density="compact" class="ma-3 mb-0 text-caption" closable @click:close="error = ''">
            {{ error }}
          </VAlert>

          <div class="sp-window">
            <div v-show="activeMain === 'scan'" class="sp-pane">
              <div class="sp-section-title">扫描设置</div>
              <VRow>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="config.delay_days" type="number" min="0" label="宽限天数" variant="outlined" density="compact" hide-details="auto" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model="config.cron" label="Cron" variant="outlined" density="compact" hide-details="auto" :error-messages="cronError" hint="每 6 小时建议写 0 */6 * * *" persistent-hint />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="config.max_scan_subscribes" type="number" min="1" label="订阅部数通知上限" variant="outlined" density="compact" hide-details="auto" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="config.selected_categories" :items="categories" item-title="title" item-value="value" label="二级分类" variant="outlined" density="compact" multiple chips closable-chips hide-details="auto" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="config.search_sites" :items="siteOptions" item-title="title" item-value="value" label="PT搜索范围" variant="outlined" density="compact" multiple chips closable-chips clearable hide-details="auto" />
                </VCol>
              </VRow>
            </div>

            <div v-show="activeMain === 'notify'" class="sp-pane">
              <div class="sp-section-title">通知权限</div>
              <VRow>
                <VCol cols="12" md="6">
                  <VSwitch v-model="config.notify_tg" color="primary" inset hide-details label="Telegram 独立通知" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSwitch v-model="config.allow_tg_rule_update" color="warning" inset hide-details label="允许 TG 修改订阅规则" />
                </VCol>
              </VRow>
              <VAlert class="mt-3" type="info" variant="tonal" density="compact" text="开启「允许 TG 修改订阅规则」后，可通过 Telegram 交互直接调整订阅过滤规则，请谨慎授权。" />
            </div>

            <div v-show="activeMain === 'cleanup'" class="sp-pane">
              <div class="sp-section-title">全集包清理</div>
              <VRow>
                <VCol cols="12" md="6">
                  <VSelect v-model="config.season_pack_cleanup" :items="seasonPackCleanupOptions" item-title="title" item-value="value" label="最终集整季包清理" variant="outlined" density="compact" hide-details="auto" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSwitch v-model="config.season_pack_full_download" color="warning" inset hide-details label="qB 整季包全选下载" />
                </VCol>
              </VRow>
              <VAlert class="mt-3" type="info" variant="tonal" density="compact" text="当整季包下载到最终集时，可按策略清理旧的分集转移记录或源文件，避免媒体库重复。" />
            </div>

            <div v-show="activeMain === 'candidate'" class="sp-pane">
              <div class="sp-section-title">候选下载</div>
              <VRow>
                <VCol cols="12" md="6">
                  <VTextField v-model.number="config.candidate_cache_days" type="number" min="0" label="候选缓存天数" hint="候选下载信息本地缓存有效期，0 关闭；重载/重启后仍可直接下载候选" persistent-hint variant="outlined" density="compact" hide-details="auto" />
                </VCol>
              </VRow>
            </div>
          </div>

          <VDivider />
          <div class="sp-actions d-flex align-center flex-wrap ga-1">
            <VBtn color="info" prepend-icon="mdi-view-dashboard-outline" variant="text" size="small" @click="emit('switch')">数据页</VBtn>
            <VSpacer class="sp-action-spacer" />
            <VBtn color="grey" prepend-icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadOptions">刷新</VBtn>
            <VBtn color="primary" prepend-icon="mdi-content-save" variant="text" size="small" @click="saveConfig">保存</VBtn>
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
const categories = ref([])
const siteOptions = ref([])
const cronError = ref('')
const activeMain = ref('scan')

const mainTabs = [
  { key: 'scan', title: '扫描设置', icon: 'mdi-tune-variant', desc: '订阅扫描周期、宽限天数与站点范围。' },
  { key: 'notify', title: '通知权限', icon: 'mdi-message-badge-outline', desc: 'Telegram 通知与规则修改授权。' },
  { key: 'cleanup', title: '全集包清理', icon: 'mdi-broom', desc: '整季包下载完成后的清理策略。' },
  { key: 'candidate', title: '候选下载', icon: 'mdi-download-box-outline', desc: '候选资源本地缓存有效期。' },
]

const currentMain = computed(() => mainTabs.find(i => i.key === activeMain.value) || mainTabs[0])

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
  candidate_cache_days: 3,
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
    candidate_cache_days:
      props.initialConfig.candidate_cache_days === undefined || props.initialConfig.candidate_cache_days === null
        ? 3
        : Number(props.initialConfig.candidate_cache_days),
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
  if (cronError.value) {
    activeMain.value = 'scan'
    return
  }
  emit('save', {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    candidate_cache_days: Number(config.candidate_cache_days),
    search_sites: Array.isArray(config.search_sites) ? [...config.search_sites] : [],
  })
}

onMounted(() => {
  applyInitialConfig()
  loadOptions()
})
</script>

<style scoped>
.sp-config { width: min(1120px, calc(100vw - 48px)); max-width: 100%; padding: 8px; margin: 0 auto; }
.sp-card { width: 100%; display: flex; flex-direction: column; border-radius: 14px; overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.sp-header { padding: 14px 18px; }
.sp-header-subtitle { max-width: min(560px, 52vw); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-body { flex: 1 1 auto; min-height: 0; display: flex; }
.sp-nav { width: 160px; flex: 0 0 160px; border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); background: rgba(var(--v-theme-on-surface), .02); }
.sp-nav-item { margin: 2px 8px; }
.sp-content { flex: 1 1 auto; min-width: 0; min-height: 0; display: flex; flex-direction: column; }
.sp-window { flex: 1 1 auto; min-height: 0; overflow-y: auto; }
.sp-pane { padding: 18px 20px; }
.sp-section-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: rgb(var(--v-theme-primary)); }
.sp-actions { padding: 10px 18px; }
@media (max-width: 760px) {
  .sp-config { width: 100%; padding: 0; }
  .sp-card { border-radius: 0; border: none; }
  .sp-header { padding: 8px 10px; }
  .sp-header-avatar { width: 34px !important; height: 34px !important; }
  .sp-header-title { font-size: 15px; line-height: 1.25; }
  .sp-header-subtitle { max-width: 100%; }
  .sp-enable-switch { flex: 0 0 46px; width: 46px; min-width: 46px; overflow: hidden; }
  .sp-body { flex-direction: column; }
  .sp-nav { width: 100%; flex: 0 0 auto; border-right: none; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); overflow-x: auto; overflow-y: hidden; scrollbar-width: none; }
  .sp-nav::-webkit-scrollbar { display: none; }
  .sp-nav-list { display: flex; flex-wrap: nowrap; gap: 4px; min-width: max-content; padding: 5px 8px !important; }
  .sp-nav-item { flex: 0 0 auto; min-width: 86px; min-height: 34px !important; margin: 0; padding-inline: 8px; }
  .sp-nav-title { font-size: 12px; white-space: nowrap; }
  .sp-nav-icon { font-size: 17px; }
  .sp-pane { padding: 12px 12px; }
  .sp-section-title { margin-bottom: 8px; }
  .sp-actions { padding: 6px 10px; }
  .sp-action-spacer { display: none; }
  .sp-actions :deep(.v-btn) { flex: 1 1 auto; min-width: max-content; }
}
</style>
