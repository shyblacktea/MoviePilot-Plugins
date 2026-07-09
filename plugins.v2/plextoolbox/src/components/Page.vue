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
        <VCardSubtitle class="text-caption">媒体信息补全</VCardSubtitle>
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

        <div class="d-flex align-center mb-4" style="gap: 8px;">
          <VBtn color="primary" :loading="running" prepend-icon="mdi-play" @click="runComplete">
            开始补全
          </VBtn>
          <VCheckbox v-model="force" label="忽略 Plex 繁忙强制写入" hide-details density="compact" />
          <VSpacer />
          <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadAll" />
        </div>

        <VRow v-if="result && result.strm_parts !== undefined">
          <VCol cols="6" md="3"><StatCard label="STRM 条目" :value="result.strm_parts" color="blue" /></VCol>
          <VCol cols="6" md="3"><StatCard label="已解析" :value="result.resolved" color="teal" /></VCol>
          <VCol cols="6" md="3"><StatCard label="Emby 命中" :value="result.emby_hits" color="green" /></VCol>
          <VCol cols="6" md="3"><StatCard label="ffprobe 命中" :value="result.ffprobe_hits" color="cyan" /></VCol>
          <VCol cols="6" md="3"><StatCard label="写入成功" :value="result.written_ok" color="success" /></VCol>
          <VCol cols="6" md="3"><StatCard label="写入失败" :value="result.write_failed" color="error" /></VCol>
          <VCol cols="6" md="3"><StatCard label="未解析" :value="result.unresolved" color="orange" /></VCol>
          <VCol cols="6" md="3"><StatCard label="来源" :value="result.source || '-'" color="grey" /></VCol>
        </VRow>
        <VAlert v-else type="info" variant="tonal" density="compact" class="text-caption">
          暂无补全记录，点击「开始补全」执行一次。
        </VAlert>

        <VAlert v-if="result && result.helper_busy" type="warning" variant="tonal" density="compact" class="mt-3 text-caption">
          Plex 当前繁忙（播放/扫描中），本次未写入。可勾选强制写入或稍后重试。
        </VAlert>
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
const running = ref(false)
const force = ref(false)
const status = ref({})
const result = ref(null)

const StatCard = (p) => h('div', { class: 'ptb-stat', style: `border-left: 3px solid var(--v-theme-${p.color}, #888)` }, [
  h('div', { class: 'ptb-stat-value' }, String(p.value ?? '-')),
  h('div', { class: 'ptb-stat-label' }, p.label),
])

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [st, res] = await Promise.all([
      getPluginApi(props.api, 'status'),
      getPluginApi(props.api, 'result'),
    ])
    status.value = st || {}
    result.value = res?.result || null
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

async function runComplete() {
  running.value = true
  error.value = ''
  try {
    const res = await postPluginApi(props.api, 'complete', { force: force.value })
    if (res?.success) {
      result.value = res
      emit('action')
    } else {
      error.value = res?.error || '补全失败'
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    running.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.ptb-stat { padding: 10px 14px; background: rgba(var(--v-theme-on-surface), 0.03); border-radius: 8px; }
.ptb-stat-value { font-size: 1.4rem; font-weight: 700; line-height: 1.2; }
.ptb-stat-label { font-size: 0.75rem; opacity: 0.7; }
</style>
