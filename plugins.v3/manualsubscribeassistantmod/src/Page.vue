<template>
  <div class="page-wrap">
    <v-card variant="outlined" class="mb-4">
      <v-card-title>手动订阅助手魔改版</v-card-title>
      <v-card-subtitle>只在你点击时创建订阅，不会后台自动订阅</v-card-subtitle>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3"><v-text-field v-model.number="form.year" label="年份（0=当前年）" type="number" /></v-col>
          <v-col cols="12" md="3"><v-select v-model="form.season" :items="seasons" label="季度" /></v-col>
          <v-col cols="12" md="6" class="d-flex align-center"><v-switch v-model="form.resolve_bangumi" label="识别 Bangumi/TMDB" /></v-col>
        </v-row>
        <v-btn color="primary" :loading="loading" @click="loadCandidates">抓取候选</v-btn>
        <v-alert v-if="message" class="mt-3" :type="error ? 'error' : 'info'" density="compact">{{ message }}</v-alert>
      </v-card-text>
    </v-card>

    <v-card variant="outlined">
      <v-card-title>候选列表（{{ candidates.length }}）</v-card-title>
      <v-card-text>
        <v-alert v-if="!candidates.length" type="info" variant="tonal">点击“抓取候选”后在这里查看季度番剧。</v-alert>
        <v-row v-else>
          <v-col v-for="item in candidates" :key="`${item.mikan_id}-${item.bangumi_id || ''}`" cols="12" md="6" xl="4">
            <v-card variant="tonal" class="candidate-card">
              <v-img v-if="item.cover" :src="item.cover" height="180" cover />
              <v-card-title class="text-wrap">{{ item.title }}</v-card-title>
              <v-card-subtitle>{{ item.year }} · {{ item.week || '季度新番' }}</v-card-subtitle>
              <v-card-actions>
                <v-btn v-if="item.bangumi_url" size="small" variant="text" :href="item.bangumi_url" target="_blank">打开 Bangumi</v-btn>
                <v-btn v-if="item.tmdb_url" size="small" variant="text" :href="item.tmdb_url" target="_blank">打开 TMDB</v-btn>
                <v-spacer />
                <v-btn color="primary" size="small" :loading="subscribing === item" @click="subscribe(item)">创建订阅</v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
const props = defineProps({ api: { type: Object, default: null }, pluginId: { type: String, default: 'ManualSubscribeAssistantMod' }, initialConfig: { type: Object, default: () => ({}) } })
const form = reactive({ year: 0, season: '当前', resolve_bangumi: true, proxy: false, ...props.initialConfig })
const seasons = ['当前', '春', '夏', '秋', '冬']
const candidates = ref([])
const loading = ref(false)
const subscribing = ref(null)
const message = ref('')
const error = ref(false)

function call(method, path, payload) {
  return props.api?.[method]?.(`plugin/${props.pluginId}/${path}`, payload)
}
async function loadCandidates() {
  loading.value = true; message.value = ''; error.value = false
  try {
    const result = await call('post', 'candidates', form)
    const data = result?.data || result
    if (data?.code) throw new Error(data.message)
    candidates.value = data?.list || []
    message.value = `已读取 ${candidates.value.length} 条候选`
  } catch (e) { error.value = true; message.value = e.message || '抓取失败' }
  finally { loading.value = false }
}
async function subscribe(item) {
  subscribing.value = item; message.value = ''; error.value = false
  try {
    const result = await call('post', 'subscribe', { candidate: item })
    const data = result?.data || result
    if (data?.code) throw new Error(data.message)
    message.value = `${item.title} 已创建订阅（ID ${data.subscribe_id}）`
  } catch (e) { error.value = true; message.value = e.message || '创建订阅失败' }
  finally { subscribing.value = null }
}
defineExpose({ loadCandidates })
</script>

<style scoped>
.page-wrap { padding: 16px; }
.text-wrap { white-space: normal; line-height: 1.35; }
.candidate-card { height: 100%; }
</style>
