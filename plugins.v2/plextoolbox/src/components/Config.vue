<template>
  <div class="ptb-config">
    <VCard flat class="ptb-card">
      <VCardItem class="ptb-header">
        <template #prepend>
          <VAvatar color="primary" variant="tonal" size="44" rounded="lg">
            <VIcon icon="mdi-plex" size="24" />
          </VAvatar>
        </template>
        <VCardTitle class="text-h6">PLEX 工具箱</VCardTitle>
        <VCardSubtitle class="text-caption">{{ currentTab.desc }}</VCardSubtitle>
        <template #append>
          <VSwitch v-model="config.enabled" color="success" hide-details inset
            :label="config.enabled ? '已启用' : '已停用'" />
        </template>
      </VCardItem>
      <VDivider />

      <div class="ptb-body">
        <nav class="ptb-nav">
          <VList density="comfortable" nav class="py-2">
            <VListItem v-for="item in tabs" :key="item.key" :active="activeTab === item.key"
              color="primary" rounded="lg" @click="activeTab = item.key">
              <template #prepend><VIcon :icon="item.icon" /></template>
              <VListItemTitle>{{ item.title }}</VListItemTitle>
            </VListItem>
          </VList>
        </nav>

        <section class="ptb-content">
          <VAlert v-if="error" type="error" variant="tonal" density="compact" class="ma-3 mb-0 text-caption"
            closable @click:close="error = ''">{{ error }}</VAlert>

          <!-- 反向代理 -->
          <div v-show="activeTab === 'proxy'" class="ptb-pane">
            <div class="ptb-section-title">302 反向代理</div>
            <VRow>
              <VCol cols="12"><VSwitch v-model="config.proxy_enabled" color="primary" hide-details inset label="启用 302 反向代理" /></VCol>
              <VCol cols="12" md="8"><VTextField v-model="config.plex_host" label="Plex 服务器地址" placeholder="http://192.168.0.122:32400" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="4"><VTextField v-model="config.plex_token" label="X-Plex-Token" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="6"><VTextField v-model="config.host" label="代理监听地址" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="6"><VTextField v-model.number="config.port" type="number" label="代理监听端口" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12"><VSwitch v-model="config.force_direct_play" color="primary" hide-details inset label="强制 DirectPlay（避免转码使直链失效）" /></VCol>
              <VCol cols="12"><VTextarea v-model="config.pin_rules" label="顶置路径规则（每行：路径前缀 => 目标URL）" variant="outlined" density="compact" rows="3" hide-details="auto" /></VCol>
            </VRow>
          </div>

          <!-- 媒体信息补全 -->
          <div v-show="activeTab === 'mediainfo'" class="ptb-pane">
            <div class="ptb-section-title">STRM 媒体流信息补全</div>
            <VAlert type="info" variant="tonal" density="compact" class="mb-3 text-caption">
              媒体信息补全需先在 Plex 主机部署 helper 写库服务。
              <a :href="helperDocUrl" target="_blank" rel="noopener" class="ptb-doc-link">查看部署说明</a>
              <VIcon icon="mdi-open-in-new" size="12" class="ml-1" />
            </VAlert>
            <VRow>
              <VCol cols="12"><VSwitch v-model="config.mediainfo_enabled" color="primary" hide-details inset label="启用媒体信息补全" /></VCol>
              <VCol cols="12" md="8"><VTextField v-model="config.plex_direct_host" label="Plex 直连地址（写库/枚举用，留空则用反代地址）" placeholder="http://192.168.0.122:32400" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="4">
                <VBtn color="info" variant="tonal" size="small" :loading="checking" @click="checkHelper" prepend-icon="mdi-lan-connect">检查 helper</VBtn>
              </VCol>
              <VCol cols="12" md="8"><VTextField v-model="config.helper_url" label="helper 地址（122 上的写库服务）" placeholder="http://192.168.0.122:9001" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="4"><VTextField v-model="config.helper_token" label="helper Token" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12"><VDivider class="my-1" /></VCol>
              <VCol cols="12" md="6"><VSwitch v-model="config.use_emby" color="primary" hide-details inset label="数据源① Emby MediaStreams" /></VCol>
              <VCol cols="12" md="6"><VSwitch v-model="config.use_ffprobe" color="primary" hide-details inset label="数据源② ffprobe 探测直链" /></VCol>
              <VCol cols="12" md="8"><VTextField v-model="config.emby_url" label="Emby 地址" placeholder="http://192.168.0.121:8096" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="4"><VTextField v-model="config.emby_apikey" label="Emby API Key" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12"><VDivider class="my-1" /></VCol>
              <VCol cols="12" md="8">
                <VSelect v-model="selectedSections" :items="sectionOptions" item-title="title" item-value="value"
                  label="要补全的 Plex 媒体库" variant="outlined" density="compact" multiple chips closable-chips
                  hide-details="auto" :loading="loadingSections">
                  <template #append-inner>
                    <VBtn icon="mdi-refresh" size="x-small" variant="text" @click.stop="loadSections" />
                  </template>
                </VSelect>
              </VCol>
              <VCol cols="12" md="4"><VTextField v-model.number="config.concurrency" type="number" min="1" max="10" label="探测并发数" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="6"><VSwitch v-model="config.only_missing" color="primary" hide-details inset label="仅处理缺失媒体信息的条目" /></VCol>
              <VCol cols="12" md="6"><VSwitch v-model="config.overwrite_streams" color="primary" hide-details inset label="写入前清空旧流" /></VCol>
              <VCol cols="12" md="6"><VTextField v-model="config.cron" label="定时补全 Cron（留空不定时）" placeholder="0 4 * * *" variant="outlined" density="compact" hide-details="auto" /></VCol>
            </VRow>
            <VAlert v-if="helperInfo" type="success" variant="tonal" density="compact" class="mt-2 text-caption">
              helper 正常，数据库：{{ helperInfo }}
            </VAlert>
          </div>
        </section>
      </div>

      <VDivider />
      <VCardActions class="ptb-actions">
        <VBtn color="info" variant="text" size="small" prepend-icon="mdi-view-dashboard-outline" @click="emit('switch')">数据页</VBtn>
        <VSpacer />
        <VBtn color="primary" variant="text" size="small" prepend-icon="mdi-content-save" @click="saveConfig">保存</VBtn>
        <VBtn color="grey" variant="text" size="small" prepend-icon="mdi-close" @click="emit('close')">关闭</VBtn>
      </VCardActions>
    </VCard>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { getPluginApi, postPluginApi } from './api.js'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: [Object, Function], default: null },
})
const emit = defineEmits(['save', 'close', 'switch'])

const error = ref('')
const checking = ref(false)
const loadingSections = ref(false)
const helperInfo = ref('')
const sectionOptions = ref([])
const activeTab = ref('proxy')

const helperDocUrl = 'https://github.com/shyblacktea/MoviePilot-Plugins/blob/main/plugins.v2/plextoolbox/helper/README.md'

const tabs = [
  { key: 'proxy', title: '反向代理', icon: 'mdi-swap-horizontal-bold', desc: 'Plex 播放流 302 直链跳转' },
  { key: 'mediainfo', title: '媒体信息补全', icon: 'mdi-information-outline', desc: '为 STRM 条目补全编码/分辨率/音轨等媒体流信息' },
]
const currentTab = computed(() => tabs.find(t => t.key === activeTab.value) || tabs[0])

const config = reactive({
  enabled: false, proxy_enabled: false, plex_host: '', plex_token: '',
  host: '0.0.0.0', port: 32401, pin_rules: '', force_direct_play: true,
  mediainfo_enabled: false, plex_direct_host: '', helper_url: '', helper_token: '',
  emby_url: '', emby_apikey: '', use_emby: true, use_ffprobe: true,
  overwrite_streams: true, only_missing: true, concurrency: 3, sections: '', cron: '',
  ...props.initialConfig,
})

const selectedSections = computed({
  get: () => (config.sections ? String(config.sections).split(',').map(s => s.trim()).filter(Boolean) : []),
  set: v => { config.sections = (v || []).join(',') },
})

async function loadSections() {
  loadingSections.value = true
  error.value = ''
  try {
    const res = await getPluginApi(props.api, 'sections')
    if (res?.success) {
      sectionOptions.value = (res.sections || []).map(s => ({ title: `${s.title}（${s.type}）`, value: String(s.key) }))
    } else {
      error.value = res?.error || '获取媒体库失败'
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    loadingSections.value = false
  }
}

async function checkHelper() {
  checking.value = true
  error.value = ''
  helperInfo.value = ''
  try {
    const res = await getPluginApi(props.api, 'helper_check')
    if (res?.success) {
      helperInfo.value = res?.dbinfo?.db_path || '已连接'
    } else {
      error.value = res?.error || 'helper 检查失败'
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    checking.value = false
  }
}

function saveConfig() {
  emit('save', { ...config })
}

onMounted(() => {
  if (config.plex_token && (config.plex_direct_host || config.plex_host)) loadSections()
})
</script>

<style scoped>
.ptb-body { display: flex; min-height: 360px; }
.ptb-nav { flex: 0 0 160px; border-right: 1px solid rgba(var(--v-border-color), 0.12); }
.ptb-content { flex: 1 1 auto; min-width: 0; }
.ptb-pane { padding: 16px; }
.ptb-section-title { font-size: 0.9rem; font-weight: 600; margin-bottom: 12px; opacity: 0.8; }
.ptb-doc-link { color: rgb(var(--v-theme-primary)); text-decoration: underline; font-weight: 600; }
.ptb-actions { padding: 8px 16px; }
</style>
