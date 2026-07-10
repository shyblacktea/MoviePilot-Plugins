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
              <VCol cols="12" md="6"><VSwitch v-model="config.use_emby" color="primary" hide-details inset label="数据源 Emby MediaStreams" /></VCol>
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
              <VCol cols="12"><VDivider class="my-1" /></VCol>
              <VCol cols="12" class="text-caption text-medium-emphasis">自动触发（播放停止后自动增量补全本集+后N集，默认常开）</VCol>
              <VCol cols="12" md="6"><VSwitch v-model="config.webhook_enabled" color="primary" hide-details inset label="启用 Plex Webhook 触发（需 Plex Pass）" /></VCol>
              <VCol cols="12" md="6"><VTextField v-model.number="config.dedup_window" type="number" min="0" label="同条目去重窗口（秒）" placeholder="300" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol cols="12" md="6"><VTextField v-model.number="config.forward_episodes" type="number" min="0" label="剧集向后预取集数（含当前集后N集）" placeholder="5" variant="outlined" density="compact" hide-details="auto" /></VCol>
              <VCol v-if="config.webhook_enabled" cols="12">
                <VAlert type="info" variant="tonal" density="compact" class="text-caption">
                  Webhook 地址填到 Plex 设置 → Webhooks：<code>{{ webhookUrl }}</code>
                </VAlert>
              </VCol>
            </VRow>
            <VAlert v-if="helperInfo" type="success" variant="tonal" density="compact" class="mt-2 text-caption">
              helper 正常，数据库：{{ helperInfo }}
            </VAlert>
          </div>

          <!-- 目录匹配 / 刮削 -->
          <div v-show="activeTab === 'scrape'" class="ptb-pane">
            <div class="ptb-section-title">目录匹配 / 刮削</div>
            <VAlert type="info" variant="tonal" density="compact" class="mb-3 text-caption">
              本栏为按需手动操作：取消匹配让条目按当前 NFO 代理重读；扫描缺封面条目并交给 MoviePilot 刮削生成 NFO+封面。操作前请先选择目标媒体库。
            </VAlert>
            <VRow>
              <VCol cols="12" md="8">
                <VSelect v-model="scrapeSection" :items="sectionOptions" item-title="title" item-value="value"
                  label="目标 Plex 媒体库" variant="outlined" density="compact" hide-details="auto" :loading="loadingSections">
                  <template #append-inner>
                    <VBtn icon="mdi-refresh" size="x-small" variant="text" @click.stop="loadSections" />
                  </template>
                </VSelect>
              </VCol>
              <VCol cols="12" md="4"><VTextField v-model.number="scrapeLimit" type="number" min="0" label="限制条数（0=不限）" variant="outlined" density="compact" hide-details="auto" /></VCol>

              <VCol cols="12"><VDivider class="my-1" /></VCol>
              <VCol cols="12" class="text-caption text-medium-emphasis">① 一键取消匹配（取消后自动刷新重读 NFO）</VCol>
              <VCol cols="12" class="d-flex align-center gap-2">
                <VBtn color="info" variant="tonal" size="small" :loading="busyKey==='unmatch_preview'" :disabled="!!busyKey" prepend-icon="mdi-magnify" @click="doUnmatch(true)">预览影响</VBtn>
                <VBtn color="warning" variant="flat" size="small" :loading="busyKey==='unmatch_run'" :disabled="!!busyKey" prepend-icon="mdi-link-off" @click="doUnmatch(false)">执行取消匹配</VBtn>
              </VCol>

              <VCol cols="12"><VDivider class="my-1" /></VCol>
              <VCol cols="12" class="text-caption text-medium-emphasis">② 缺封面刮削（Plex 无封面 / 目录只有 strm）</VCol>
              <VCol cols="12" class="d-flex align-center gap-2 flex-wrap">
                <VBtn color="info" variant="tonal" size="small" :loading="busyKey==='scan_cover'" :disabled="!!busyKey" prepend-icon="mdi-image-off-outline" @click="doScanCover">扫描缺封面</VBtn>
                <VBtn color="info" variant="tonal" size="small" :loading="busyKey==='scrape_preview'" :disabled="!!busyKey" prepend-icon="mdi-magnify" @click="doScrape(true)">预览刮削目录</VBtn>
                <VBtn color="success" variant="flat" size="small" :loading="busyKey==='scrape_run'" :disabled="!!busyKey" prepend-icon="mdi-auto-fix" @click="doScrape(false)">执行刮削</VBtn>
              </VCol>

              <VCol cols="12"><VDivider class="my-1" /></VCol>
              <VCol cols="12" class="text-caption text-medium-emphasis">③ 缺 poster.jpg 精准补全（已刮削但独缺海报：剧集先复制季内海报，电影/无季海报走 TMDB，修复后自动刷新）</VCol>
              <VCol cols="12" class="d-flex align-center gap-2 flex-wrap">
                <VBtn color="info" variant="tonal" size="small" :loading="busyKey==='poster_preview'" :disabled="!!busyKey" prepend-icon="mdi-magnify" @click="doFixPoster(true)">预览缺 poster</VBtn>
                <VBtn color="success" variant="flat" size="small" :loading="busyKey==='poster_run'" :disabled="!!busyKey" prepend-icon="mdi-image-plus" @click="doFixPoster(false)">执行补全</VBtn>
              </VCol>

              <VCol v-if="scrapeResult" cols="12">
                <VAlert :type="scrapeResult.type" variant="tonal" density="compact" class="text-caption" style="white-space:pre-wrap">{{ scrapeResult.text }}</VAlert>
              </VCol>
            </VRow>
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
  { key: 'scrape', title: '目录匹配/刮削', icon: 'mdi-image-search-outline', desc: '一键取消匹配重读 NFO、缺封面交给 MP 刮削' },
]
const currentTab = computed(() => tabs.find(t => t.key === activeTab.value) || tabs[0])

const config = reactive({
  enabled: false, proxy_enabled: false, plex_host: '', plex_token: '',
  host: '0.0.0.0', port: 32401, pin_rules: '', force_direct_play: true,
  mediainfo_enabled: false, plex_direct_host: '', helper_url: '', helper_token: '',
  emby_url: '', emby_apikey: '', use_emby: true,
  overwrite_streams: true, only_missing: true, concurrency: 3, sections: '', cron: '',
  webhook_enabled: false, dedup_window: 300, forward_episodes: 5,
  ...props.initialConfig,
})

const selectedSections = computed({
  get: () => (config.sections ? String(config.sections).split(',').map(s => s.trim()).filter(Boolean) : []),
  set: v => { config.sections = (v || []).join(',') },
})

const webhookUrl = computed(() => {
  const origin = (typeof window !== 'undefined' && window.location ? window.location.origin : '')
  return `${origin}/api/v1/plugin/PlexToolbox/webhook?apikey=<你的API_TOKEN>`
})

// ---- 目录匹配/刮削栏状态 ----
const scrapeSection = ref('')
const scrapeLimit = ref(0)
const busyKey = ref('')
const scrapeResult = ref(null)

function showScrape(type, text) {
  scrapeResult.value = { type, text }
}

async function doUnmatch(dryRun) {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  if (!dryRun && !window.confirm('确认对该媒体库执行取消匹配？条目将被打回未匹配并按当前 NFO 代理重读。')) return
  busyKey.value = dryRun ? 'unmatch_preview' : 'unmatch_run'
  scrapeResult.value = null
  try {
    const res = await postPluginApi(props.api, 'unmatch', {
      section: scrapeSection.value, dry_run: dryRun,
      rematch: true, limit: Number(scrapeLimit.value) || 0,
    })
    if (!res?.success) { showScrape('error', res?.error || '操作失败'); return }
    if (dryRun) {
      showScrape('info', `预览：该库共 ${res.total_items} 个条目，将影响 ${res.will_affect} 个`)
    } else {
      showScrape('success', `已取消匹配 ${res.unmatched} 个，刷新重读 ${res.refreshed} 个，失败 ${res.failed} 个`)
    }
  } catch (e) {
    showScrape('error', String(e))
  } finally {
    busyKey.value = ''
  }
}

async function doScanCover() {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  busyKey.value = 'scan_cover'
  scrapeResult.value = null
  try {
    const res = await postPluginApi(props.api, 'scan_cover', { section: scrapeSection.value })
    if (!res?.success) { showScrape('error', res?.error || '扫描失败'); return }
    const list = (res.missing || []).slice(0, 20).map(m => `· ${m.title}（${m.reason}）`).join('\n')
    showScrape('info', `已检查 ${res.checked} 个条目，缺封面 ${res.total} 个${list ? '：\n' + list : ''}`)
  } catch (e) {
    showScrape('error', String(e))
  } finally {
    busyKey.value = ''
  }
}

async function doScrape(dryRun) {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  if (!dryRun && !window.confirm('确认对缺封面条目执行 MoviePilot 刮削？将生成 NFO+封面文件。')) return
  busyKey.value = dryRun ? 'scrape_preview' : 'scrape_run'
  scrapeResult.value = null
  try {
    const res = await postPluginApi(props.api, 'scrape', {
      section: scrapeSection.value, dry_run: dryRun,
      limit: Number(scrapeLimit.value) || 0, unmatch_after: false,
    })
    if (!res?.success) { showScrape('error', res?.error || '刮削失败'); return }
    if (dryRun) {
      const list = (res.targets || []).slice(0, 20).map(t => `· ${t.title} → ${t.dir}`).join('\n')
      showScrape('info', `待刮削 ${res.candidates} 个目录${list ? '：\n' + list : ''}`)
    } else {
      showScrape('success', `刮削成功 ${res.scraped} 个，已刷新 ${res.refreshed ?? 0} 个，失败 ${res.failed} 个`)
    }
  } catch (e) {
    showScrape('error', String(e))
  } finally {
    busyKey.value = ''
  }
}

async function doFixPoster(dryRun) {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  if (!dryRun && !window.confirm('确认为缺 poster.jpg 的条目执行补全？剧集优先复制季内海报，其余从 TMDB 下载。')) return
  busyKey.value = dryRun ? 'poster_preview' : 'poster_run'
  scrapeResult.value = null
  try {
    const res = await postPluginApi(props.api, 'fix_poster', {
      section: scrapeSection.value, dry_run: dryRun,
      limit: Number(scrapeLimit.value) || 0,
    })
    if (!res?.success) { showScrape('error', res?.error || '操作失败'); return }
    if (dryRun) {
      const list = (res.targets || []).slice(0, 20).map(t => `· ${t.title}${t.tmdbid ? '' : '（无tmdbid）'} → ${t.dir}`).join('\n')
      showScrape('info', `已检查 ${res.checked} 个条目，缺 poster ${res.candidates} 个${list ? '：\n' + list : ''}`)
    } else {
      const fails = (res.details || []).filter(x => !x.ok).slice(0, 10).map(x => `· ${x.title}: ${x.error}`).join('\n')
      showScrape(res.failed ? 'warning' : 'success',
        `补全成功 ${res.fixed} 个（已刷新 ${res.refreshed}），失败 ${res.failed} 个${fails ? '：\n' + fails : ''}`)
    }
  } catch (e) {
    showScrape('error', String(e))
  } finally {
    busyKey.value = ''
  }
}

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
