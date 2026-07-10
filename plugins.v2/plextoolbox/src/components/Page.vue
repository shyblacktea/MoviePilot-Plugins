<template>
  <div class="ptb-page">
    <VCard flat class="ptb-card">
      <VCardItem>
        <template #prepend>
          <VAvatar color="primary" variant="tonal" size="44" rounded="lg">
            <VIcon icon="mdi-plex" size="24" />
          </VAvatar>
        </template>
        <VCardTitle class="text-h6">PLEX 工具箱</VCardTitle>
        <VCardSubtitle class="text-caption">STRM 媒体信息补全 · 播放驱动增量</VCardSubtitle>
        <template #append>
          <VChip :color="status.proxy_running ? 'success' : 'grey'" size="small" variant="tonal" class="mr-2">
            代理 {{ status.proxy_running ? '运行中' : '未运行' }}
          </VChip>
        </template>
      </VCardItem>
      <VDivider />

      <div class="pa-4">
        <VAlert v-if="error" type="error" variant="tonal" density="compact" class="mb-3 text-caption"
          closable @click:close="error = ''">{{ error }}</VAlert>

        <div class="d-flex align-center mb-4">
          <div class="text-caption text-medium-emphasis">
            播放停止后自动对本集 + 后 {{ config.forward_episodes ?? 5 }} 集做增量补全，已补全的自动跳过。
          </div>
          <VSpacer />
          <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadAll" />
        </div>

        <!-- 最近一次增量补全 -->
        <div class="d-flex align-center mb-2">
          <div class="ptb-block-title mb-0">最近一次补全</div>
          <VSpacer />
          <VBtn v-if="lastPlay && lastPlay.strm_parts !== undefined" color="grey" variant="text" size="x-small"
            prepend-icon="mdi-broom" :loading="clearing === 'last'" @click="clearData('last_play_result')">清理</VBtn>
        </div>
        <template v-if="lastPlay && lastPlay.strm_parts !== undefined">
          <div v-if="lastPlay.label" class="text-body-2 font-weight-medium mb-2">
            <VIcon icon="mdi-motion-play-outline" size="16" class="mr-1" />{{ lastPlay.label }}
          </div>
          <VRow>
            <VCol cols="6" md="3"><StatCard label="本次条目数" :value="lastPlay.strm_parts" color="blue" /></VCol>
            <VCol cols="6" md="3"><StatCard label="已解析" :value="lastPlay.resolved" color="teal" /></VCol>
            <VCol cols="6" md="3"><StatCard label="Emby 命中" :value="lastPlay.emby_hits" color="green" /></VCol>
            <VCol cols="6" md="3"><StatCard label="写入成功" :value="lastPlay.written_ok" color="success" /></VCol>
            <VCol cols="6" md="3"><StatCard label="写入失败" :value="lastPlay.write_failed" color="error" /></VCol>
            <VCol cols="6" md="3"><StatCard label="未解析" :value="lastPlay.unresolved" color="orange" /></VCol>
            <VCol cols="6" md="3"><StatCard label="来源" :value="sourceLabel(lastPlay.source)" color="grey" /></VCol>
          </VRow>
          <!-- 本次逐条明细 -->
          <VTable v-if="lastPlay.items && lastPlay.items.length" density="compact" class="ptb-history mt-3">
            <thead>
              <tr><th>条目</th><th>状态</th></tr>
            </thead>
            <tbody>
              <tr v-for="(it, i) in lastPlay.items" :key="i">
                <td class="text-caption">{{ it.label || ('part ' + it.part_id) }}</td>
                <td>
                  <VChip :color="statusColor(it.status)" size="x-small" variant="tonal">{{ statusLabel(it.status) }}</VChip>
                  <span v-if="it.error" class="text-caption text-error ml-2">{{ it.error }}</span>
                </td>
              </tr>
            </tbody>
          </VTable>
        </template>
        <VAlert v-else type="info" variant="tonal" density="compact" class="text-caption">
          暂无补全记录。播放任意 STRM 剧集/电影并停止后，会自动触发一次增量补全。
        </VAlert>

        <VAlert v-if="lastPlay && lastPlay.helper_busy" type="warning" variant="tonal" density="compact" class="mt-3 text-caption">
          Plex 当前繁忙（播放/扫描中），本次未写入，稍后重试。
        </VAlert>

        <!-- 历史 -->
        <div class="d-flex align-center mt-5 mb-2">
          <div class="ptb-block-title mb-0">补全历史（最近 {{ history.length }} 条）</div>
          <VSpacer />
          <VBtn v-if="history.length" color="grey" variant="text" size="x-small"
            prepend-icon="mdi-broom" :loading="clearing === 'history'" @click="clearData('play_history')">清空历史</VBtn>
        </div>
        <VTable v-if="history.length" density="compact" class="ptb-history">
          <thead>
            <tr>
              <th></th>
              <th>时间</th><th>条目</th><th class="text-right">处理</th>
              <th class="text-right">命中</th><th class="text-right">写入</th><th class="text-right">失败</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(h, i) in history" :key="i">
              <tr class="ptb-row" @click="expanded = expanded === i ? -1 : i">
                <td style="width:28px">
                  <VIcon size="14" :icon="expanded === i ? 'mdi-chevron-down' : 'mdi-chevron-right'"
                    v-if="h.items && h.items.length" />
                </td>
                <td class="text-caption">{{ fmtTime(h.ts) }}</td>
                <td class="text-caption">{{ h.label || ('rk=' + h.rating_key) }}</td>
                <td class="text-right">{{ h.strm_parts }}</td>
                <td class="text-right text-green">{{ h.emby_hits }}</td>
                <td class="text-right text-success">{{ h.written_ok }}</td>
                <td class="text-right" :class="h.write_failed ? 'text-error' : ''">{{ h.write_failed }}</td>
              </tr>
              <tr v-if="expanded === i && h.items && h.items.length">
                <td colspan="7" class="ptb-detail-cell">
                  <div v-for="(it, j) in h.items" :key="j" class="d-flex align-center py-1">
                    <span class="text-caption flex-grow-1">{{ it.label || ('part ' + it.part_id) }}</span>
                    <VChip :color="statusColor(it.status)" size="x-small" variant="tonal">{{ statusLabel(it.status) }}</VChip>
                    <span v-if="it.error" class="text-caption text-error ml-2">{{ it.error }}</span>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </VTable>
        <VAlert v-else type="info" variant="tonal" density="compact" class="text-caption">暂无历史记录。</VAlert>
      </div>

      <VDivider />
      <VCardActions class="px-4 py-2">
        <VBtn color="info" variant="text" size="small" prepend-icon="mdi-cog-outline" @click="emit('switch')">配置页</VBtn>
        <VSpacer />
        <VBtn color="grey" variant="text" size="small" prepend-icon="mdi-close" @click="emit('close')">关闭</VBtn>
      </VCardActions>
    </VCard>
  </div>
</template>

<script setup>
import { h, ref, onMounted } from 'vue'
import { getPluginApi, postPluginApi } from './api.js'

const props = defineProps({
  api: { type: [Object, Function], default: null },
  config: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['action', 'switch', 'close'])

const error = ref('')
const loading = ref(false)
const status = ref({})
const lastPlay = ref(null)
const history = ref([])
const expanded = ref(-1)
const clearing = ref('')

async function clearData(target) {
  clearing.value = target === 'play_history' ? 'history' : 'last'
  error.value = ''
  try {
    const res = await postPluginApi(props.api, 'clear_completion_data', { target })
    if (!res?.success) throw new Error(res?.error || '清理失败')
    if (target === 'play_history') history.value = []
    else lastPlay.value = null
    expanded.value = -1
  } catch (e) {
    error.value = String(e)
  } finally {
    clearing.value = ''
  }
}

function statusLabel(s) {
  return ({ written: '已写入', resolved: '已解析', unresolved: '未命中', write_failed: '写入失败', busy: 'Plex忙' })[s] || (s || '-')
}

function statusColor(s) {
  return ({ written: 'success', resolved: 'teal', unresolved: 'orange', write_failed: 'error', busy: 'warning' })[s] || 'grey'
}

const StatCard = (p) => h('div', { class: 'ptb-stat', style: `border-left: 3px solid var(--v-theme-${p.color}, #888)` }, [
  h('div', { class: 'ptb-stat-value' }, String(p.value ?? '-')),
  h('div', { class: 'ptb-stat-label' }, p.label),
])

function fmtTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts * 1000)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function sourceLabel(s) {
  return ({ play_stop: '播放停止', webhook: 'Webhook', schedule: '定时', api: '手动' })[s] || (s || '-')
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [st, res] = await Promise.all([
      getPluginApi(props.api, 'status'),
      getPluginApi(props.api, 'result'),
    ])
    status.value = st || {}
    lastPlay.value = res?.last_play_result || null
    history.value = Array.isArray(res?.play_history) ? res.play_history : []
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.ptb-stat { padding: 10px 14px; background: rgba(var(--v-theme-on-surface), 0.03); border-radius: 8px; }
.ptb-stat-value { font-size: 1.4rem; font-weight: 700; line-height: 1.2; }
.ptb-stat-label { font-size: 0.75rem; opacity: 0.7; }
.ptb-block-title { font-size: 0.85rem; font-weight: 600; opacity: 0.8; margin-bottom: 10px; }
.ptb-history th { font-size: 0.72rem; opacity: 0.7; }
.ptb-row { cursor: pointer; }
.ptb-detail-cell { background: rgba(var(--v-theme-on-surface), 0.03); padding: 4px 16px !important; }
</style>
