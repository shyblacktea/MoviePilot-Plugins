<template>
  <div class="main-container">
    <div class="scroll-content">
      <v-card flat class="rounded border mb-3">
        <v-card-title class="title-bar">
          <v-icon icon="mdi-television-play" color="primary" size="small" />
          <span>订阅下载增强</span>
          <v-spacer />
          <v-btn icon="mdi-refresh" variant="text" size="small" :loading="loading" aria-label="刷新" @click="loadData" />
        </v-card-title>

        <v-card-text class="content">
          <v-alert v-if="error" type="error" density="compact" variant="tonal" class="mb-3 text-caption" closable>
            {{ error }}
          </v-alert>

          <v-row>
            <v-col cols="12" md="3">
              <div class="summary-item">
                <v-icon icon="mdi-calendar-clock" color="primary" size="small" />
                <span>最近扫描</span>
                <strong>{{ status.last_scan || '-' }}</strong>
              </div>
            </v-col>
            <v-col cols="12" md="3">
              <div class="summary-item">
                <v-icon icon="mdi-alert-decagram-outline" color="warning" size="small" />
                <span>待处理</span>
                <strong>{{ items.length }}</strong>
              </div>
            </v-col>
            <v-col cols="12" md="3">
              <div class="summary-item">
                <v-icon icon="mdi-download-circle-outline" color="success" size="small" />
                <span>可下载</span>
                <strong>{{ reasonCount.downloadable || 0 }}</strong>
              </div>
            </v-col>
            <v-col cols="12" md="3">
              <div class="summary-item">
                <v-icon icon="mdi-file-document-edit-outline" color="info" size="small" />
                <span>规则记录</span>
                <strong>{{ ruleRecords.length }}</strong>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card v-for="item in items" :key="`${item.subscribe_id}-${item.created_at}`" flat class="rounded border mb-3 result-card">
        <v-card-title class="result-header">
          <div class="result-title">
            <div class="text-subtitle-1">{{ item.title }}</div>
            <div class="text-caption text-medium-emphasis">TMDB {{ item.tmdbid }} / S{{ item.season }} / {{ item.category }}</div>
          </div>
          <v-spacer />
          <v-chip :color="reasonColor(item.reason)" size="small" variant="tonal">{{ reasonText(item.reason) }}</v-chip>
        </v-card-title>
        <v-card-text class="content">
          <div class="episode-line">
            <v-chip v-for="episode in item.episodes || []" :key="episode.episode" size="small" variant="tonal" class="mr-1 mb-1">
              E{{ episode.episode }} / {{ episode.air_date }}
            </v-chip>
          </div>
          <div class="text-caption text-medium-emphasis mb-2">{{ item.message }}</div>
          <v-table v-if="item.candidates?.length" density="compact" class="mt-2">
            <thead>
              <tr>
                <th>站点</th>
                <th>标题</th>
                <th>做种</th>
                <th class="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="candidate in item.candidates.slice(0, 8)" :key="candidate.candidate_id || candidate.title">
                <td>{{ candidate.site_name || candidate.site }}</td>
                <td class="candidate-title">{{ candidate.title }}</td>
                <td>{{ candidate.seeders || 0 }}</td>
                <td class="text-right">
                  <v-btn color="primary" variant="text" size="small" prepend-icon="mdi-file-eye-outline" @click="previewRule(item, candidate)">
                    规则预览
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>

      <v-card flat class="rounded border mb-3">
        <v-card-title class="small-title">
          <v-icon icon="mdi-history" color="primary" size="small" />
          <span>规则修改记录</span>
        </v-card-title>
        <v-card-text class="content">
          <v-list v-if="ruleRecords.length" density="compact" lines="two">
            <v-list-item
              v-for="record in ruleRecords"
              :key="`${record.subscribe_id}-${record.created_at}`"
              :title="`${record.field}: ${record.old_value || '-'} -> ${record.new_value || '-'}`"
              :subtitle="`${record.source || '-'} / ${record.created_at || '-'}`"
            />
          </v-list>
          <div v-else class="empty-panel">暂无记录</div>
        </v-card-text>
      </v-card>
    </div>

    <v-footer class="footer-bar">
      <v-container class="d-flex align-center action-bar">
        <v-btn color="info" prepend-icon="mdi-cog-outline" variant="text" size="small" @click="emit('switch')">配置页</v-btn>
        <v-spacer class="action-spacer" />
        <v-btn color="primary" prepend-icon="mdi-radar" variant="text" size="small" :loading="scanning" @click="runScan">手动扫描</v-btn>
        <v-btn color="warning" prepend-icon="mdi-delete-sweep-outline" variant="text" size="small" :loading="clearing" @click="clearResults">清除</v-btn>
        <v-btn color="grey" prepend-icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadData">刷新</v-btn>
        <v-btn color="grey" prepend-icon="mdi-close" variant="text" size="small" @click="emit('close')">关闭</v-btn>
      </v-container>
    </v-footer>

    <v-dialog v-model="previewDialog" max-width="720">
      <v-card>
        <v-card-title class="text-subtitle-1">规则修改预览</v-card-title>
        <v-card-text>
          <v-alert v-if="previewError" type="error" density="compact" variant="tonal" class="mb-2">{{ previewError }}</v-alert>
          <div v-if="preview" class="preview-box">
            <div>旧 include：{{ preview.old_include || '-' }}</div>
            <div>新 include：{{ preview.new_include || '-' }}</div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="previewDialog = false">返回</v-btn>
          <v-btn color="primary" variant="text" :disabled="!preview?.token" @click="confirmRule">确认修改</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
const scanning = ref(false)
const clearing = ref(false)
const error = ref('')
const status = ref({})
const items = ref([])
const ruleRecords = ref([])
const previewDialog = ref(false)
const preview = ref(null)
const previewError = ref('')

const reasonCount = computed(() => {
  return items.value.reduce((acc, item) => {
    acc[item.reason] = (acc[item.reason] || 0) + 1
    return acc
  }, {})
})

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

function reasonText(reason) {
  return {
    no_pt_resource: '暂无资源',
    recognition_issue: '疑似识别',
    rule_blocked: '规则拦截',
    downloadable: '可下载',
    search_failed: '搜索失败',
  }[reason] || reason || '未知'
}

function reasonColor(reason) {
  return {
    no_pt_resource: 'grey',
    recognition_issue: 'warning',
    rule_blocked: 'info',
    downloadable: 'success',
    search_failed: 'error',
  }[reason] || 'grey'
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [statusResponse, resultsResponse] = await Promise.all([
      props.api.get('plugin/SubscribePlus/status'),
      props.api.get('plugin/SubscribePlus/results'),
    ])
    status.value = unwrap(statusResponse)
    const data = unwrap(resultsResponse)
    items.value = data.items || []
    ruleRecords.value = data.rule_records || status.value.rule_records || []
    emit('action')
  } catch (err) {
    error.value = err?.message || '读取诊断结果失败'
  } finally {
    loading.value = false
  }
}

async function runScan() {
  scanning.value = true
  error.value = ''
  try {
    await props.api.post('plugin/SubscribePlus/scan', {})
    await loadData()
  } catch (err) {
    error.value = err?.message || '手动扫描失败'
  } finally {
    scanning.value = false
  }
}

async function clearResults() {
  clearing.value = true
  error.value = ''
  try {
    await props.api.post('plugin/SubscribePlus/results/clear', {})
    await loadData()
  } catch (err) {
    error.value = err?.message || '清除诊断结果失败'
  } finally {
    clearing.value = false
  }
}

async function previewRule(item, candidate) {
  previewDialog.value = true
  preview.value = null
  previewError.value = ''
  try {
    const pattern = candidate.site || candidate.site_name || ''
    const response = await props.api.post('plugin/SubscribePlus/rule_preview', {
      subscribe_id: item.subscribe_id,
      pattern,
    })
    const body = response?.data ?? response ?? {}
    const data = body?.data ?? body
    if (body.success === false || data.success === false) {
      previewError.value = body.message || data.message || '生成预览失败'
      return
    }
    preview.value = data
  } catch (err) {
    previewError.value = err?.message || '生成预览失败'
  }
}

async function confirmRule() {
  if (!preview.value?.token) return
  try {
    await props.api.post('plugin/SubscribePlus/rule_confirm', { token: preview.value.token })
    previewDialog.value = false
    await loadData()
  } catch (err) {
    previewError.value = err?.message || '确认修改失败'
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
}

.title-bar,
.small-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: rgba(var(--v-theme-primary), 0.07);
}

.title-bar {
  font-size: 1rem;
}

.small-title {
  font-size: 0.875rem;
}

.content {
  padding: 0.75rem;
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.summary-item {
  border-radius: 8px;
  min-height: 56px;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.summary-item strong {
  margin-left: auto;
  font-size: 0.875rem;
  overflow-wrap: anywhere;
  text-align: right;
}

.result-card {
  overflow: hidden;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
}

.result-title {
  min-width: 0;
  overflow-wrap: anywhere;
}

.candidate-title,
.path-line {
  overflow-wrap: anywhere;
}

.empty-panel {
  min-height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.62);
}

.preview-box {
  display: grid;
  gap: 0.5rem;
  overflow-wrap: anywhere;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.875rem;
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

  .action-spacer {
    display: none;
  }

  .action-bar :deep(.v-btn) {
    flex: 1 1 auto;
    min-width: max-content;
  }
}
</style>
