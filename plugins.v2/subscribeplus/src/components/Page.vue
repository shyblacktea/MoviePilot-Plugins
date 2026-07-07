<template>
  <div class="sp-page">
    <div class="sp-scroll">
      <VCard flat class="sp-card mb-3">
        <VCardItem class="sp-header">
          <template #prepend>
            <VAvatar color="primary" variant="tonal" size="42" rounded="lg">
              <VIcon icon="mdi-television-play" size="23" />
            </VAvatar>
          </template>
          <VCardTitle class="text-h6">订阅下载增强</VCardTitle>
          <VCardSubtitle class="text-caption">已播出未入库订阅的诊断与处理</VCardSubtitle>
          <template #append>
            <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" aria-label="刷新" @click="loadData" />
          </template>
        </VCardItem>
        <VDivider />
        <VCardText class="pa-3">
          <VAlert v-if="error" type="error" density="compact" variant="tonal" class="mb-3 text-caption" closable @click:close="error = ''">
            {{ error }}
          </VAlert>
          <div class="sp-stat-grid">
            <div class="sp-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="primary" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-calendar-clock" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">最近扫描</div>
              </div>
              <div class="text-subtitle-2 font-weight-bold sp-stat-value">{{ status.last_scan || '-' }}</div>
            </div>
            <div class="sp-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="warning" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-alert-decagram-outline" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">待处理</div>
              </div>
              <div class="text-subtitle-1 font-weight-bold">{{ items.length }}</div>
            </div>
            <div class="sp-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="success" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-download-circle-outline" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">可下载</div>
              </div>
              <div class="text-subtitle-1 font-weight-bold">{{ reasonCount.downloadable || 0 }}</div>
            </div>
            <div class="sp-stat">
              <div class="d-flex align-center ga-2 mb-1">
                <VAvatar color="info" variant="tonal" size="28" rounded="lg"><VIcon icon="mdi-file-document-edit-outline" size="17" /></VAvatar>
                <div class="text-caption text-medium-emphasis">规则修改</div>
              </div>
              <div class="text-subtitle-1 font-weight-bold">{{ ruleRecords.length }}</div>
            </div>
          </div>
        </VCardText>
      </VCard>

      <VCard flat class="sp-card mb-3">
        <VCardItem class="sp-subheader">
          <template #prepend><VIcon icon="mdi-tag-plus-outline" color="primary" size="20" /></template>
          <VCardTitle class="text-subtitle-1">自定义识别词</VCardTitle>
          <template #append><VChip size="small" variant="tonal">{{ identifierRecords.length }}</VChip></template>
        </VCardItem>
        <VDivider />
        <VCardText class="pa-3">
          <VAlert v-if="identifierError" type="error" density="compact" variant="tonal" class="mb-3 text-caption" closable @click:close="identifierError = ''">
            {{ identifierError }}
          </VAlert>
          <VAlert v-if="identifierMessage" type="success" density="compact" variant="tonal" class="mb-3 text-caption" closable @click:close="identifierMessage = ''">
            {{ identifierMessage }}
          </VAlert>

          <VRow class="sp-id-row" align="center">
            <VCol cols="12" md="8">
              <VTextField v-model="identifierAutoTitle" label="媒体文件名" density="compact" variant="outlined" hide-details clearable />
            </VCol>
            <VCol cols="12" md="4" class="sp-id-action">
              <VBtn color="primary" prepend-icon="mdi-auto-fix" variant="text" size="small" :loading="identifierBusy === 'auto'" @click="runIdentifierAuto">自动处理</VBtn>
            </VCol>
          </VRow>

          <VDivider class="my-3" />

          <VRow class="sp-id-row" align="center">
            <VCol cols="12" md="5">
              <VTextField v-model="identifierManualTitle" label="媒体文件名" density="compact" variant="outlined" hide-details clearable />
            </VCol>
            <VCol cols="6" md="2">
              <VSelect v-model="identifierManualType" :items="mediaTypeOptions" label="类型" density="compact" variant="outlined" hide-details />
            </VCol>
            <VCol cols="6" md="3">
              <VTextField v-model="identifierManualTmdbid" label="TMDB ID" placeholder="填写 TMDB 的 ID" density="compact" variant="outlined" hide-details clearable />
            </VCol>
            <VCol cols="12" md="2" class="sp-id-action">
              <VBtn color="primary" prepend-icon="mdi-pencil-plus-outline" variant="text" size="small" :loading="identifierBusy === 'manual'" @click="runIdentifierManual">手动处理</VBtn>
            </VCol>
          </VRow>

          <VList v-if="identifierRecords.length" density="compact" lines="two" class="mt-2">
            <VListItem
              v-for="record in identifierRecords"
              :key="`${record.mode}-${record.candidate_title}-${record.created_at}`"
              :title="`${identifierModeText(record.mode)}：${record.candidate_title || record.title || '-'}`"
              :subtitle="`${record.message || '-'} / ${record.created_at || '-'}`"
            >
              <template #append>
                <VChip :color="identifierStatusColor(record.status)" size="small" variant="tonal">{{ identifierStatusText(record.status) }}</VChip>
              </template>
            </VListItem>
          </VList>
          <div v-else class="sp-empty">暂无识别词记录</div>
        </VCardText>
      </VCard>

      <VCard flat class="sp-card mb-3">
        <VCardItem class="sp-subheader">
          <template #prepend><VIcon icon="mdi-history" color="primary" size="20" /></template>
          <VCardTitle class="text-subtitle-1">规则修改记录</VCardTitle>
          <template #append>
            <VBtn v-if="ruleRecords.length" color="warning" variant="text" size="small" prepend-icon="mdi-delete-sweep-outline" :loading="clearingRules" @click="clearRuleRecords">清空</VBtn>
          </template>
        </VCardItem>
        <VDivider />
        <VCardText class="pa-3">
          <VList v-if="ruleRecords.length" density="compact" lines="two">
            <VListItem
              v-for="record in ruleRecords"
              :key="record.record_id || `${record.subscribe_id}-${record.created_at}`"
              :title="`【${record.subscribe_name || ('订阅#' + record.subscribe_id)}】${record.change_type || record.field}`"
              :subtitle="`${record.old_value || '-'} → ${record.new_value || '-'} （${record.source || '-'} / ${record.created_at || '-'}）`"
            >
              <template #append>
                <VBtn icon="mdi-delete-outline" color="error" variant="text" size="small" :loading="deletingRuleId === record.record_id" @click="deleteRuleRecord(record)" />
              </template>
            </VListItem>
          </VList>
          <div v-else class="sp-empty">暂无记录</div>
        </VCardText>
      </VCard>

      <VCard v-for="item in items" :key="item.result_id || `${item.subscribe_id}-${item.created_at}`" flat class="sp-card mb-3">
        <VCardItem class="sp-result-header">
          <VCardTitle class="text-subtitle-1">{{ item.title }}</VCardTitle>
          <VCardSubtitle class="text-caption">TMDB {{ item.tmdbid }} / S{{ item.season }} / {{ item.category }}</VCardSubtitle>
          <template #append>
            <VChip :color="reasonColor(item.reason)" size="small" variant="tonal" class="mr-2">{{ reasonText(item.reason) }}</VChip>
            <VBtn icon="mdi-delete-outline" color="error" variant="text" size="small" :loading="deletingResultId === item.result_id" @click="deleteResult(item)" />
          </template>
        </VCardItem>
        <VDivider />
        <VCardText class="pa-3">
          <div class="mb-2">
            <VChip v-for="episode in item.episodes || []" :key="episode.episode" size="small" variant="tonal" class="mr-1 mb-1">
              E{{ episode.episode }} / {{ episode.air_date }}
            </VChip>
          </div>
          <div class="text-caption text-medium-emphasis mb-2">{{ item.message }}</div>
          <div v-if="item.candidates?.length" class="sp-candidate-wrap mt-2">
            <VTable density="compact" class="sp-candidate-table">
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
                  <td class="sp-cand-site">{{ candidate.site_name || candidate.site }}</td>
                  <td class="sp-cand-title">{{ candidate.title }}</td>
                  <td class="sp-cand-seed">{{ candidate.seeders || 0 }}</td>
                  <td class="text-right sp-cand-act">
                    <VBtn color="primary" variant="text" size="small" prepend-icon="mdi-file-eye-outline" @click="previewRule(item, candidate)">规则预览</VBtn>
                  </td>
                </tr>
              </tbody>
            </VTable>
          </div>
        </VCardText>
      </VCard>
    </div>

    <VFooter class="sp-footer">
      <VContainer class="d-flex align-center flex-wrap ga-1 pa-0">
        <VBtn color="info" prepend-icon="mdi-cog-outline" variant="text" size="small" @click="emit('switch')">配置页</VBtn>
        <VSpacer class="sp-footer-spacer" />
        <VBtn color="primary" prepend-icon="mdi-radar" variant="text" size="small" :loading="scanning" @click="runScan">手动扫描</VBtn>
        <VBtn color="warning" prepend-icon="mdi-delete-sweep-outline" variant="text" size="small" :loading="clearing" @click="clearResults">诊断结果清除</VBtn>
        <VBtn color="grey" prepend-icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadData">刷新</VBtn>
        <VBtn color="grey" prepend-icon="mdi-close" variant="text" size="small" @click="emit('close')">关闭</VBtn>
      </VContainer>
    </VFooter>

    <VDialog v-model="previewDialog" max-width="720">
      <VCard>
        <VCardTitle class="text-subtitle-1">规则修改预览</VCardTitle>
        <VCardText>
          <VAlert v-if="previewError" type="error" density="compact" variant="tonal" class="mb-2">{{ previewError }}</VAlert>
          <div v-if="ruleSuggestions.length && !preview" class="sp-suggestion">
            <div class="text-caption text-medium-emphasis mb-2">请选择要添加的官组、平台关键词或 PT 站点</div>
            <VBtn
              v-for="suggestion in ruleSuggestions"
              :key="suggestion.pattern"
              color="primary"
              variant="tonal"
              size="small"
              class="mr-2 mb-2"
              :loading="previewLoading === suggestion.pattern"
              @click="previewRuleSuggestion(suggestion)"
            >
              {{ suggestion.text }}
            </VBtn>
          </div>
          <div v-if="preview" class="sp-preview-box">
            <div v-if="preview.selected_text">已选择：{{ preview.selected_text }}</div>
            <template v-if="preview.field === 'sites'">
              <div>旧订阅站点：{{ formatPreviewSites(preview.old_site_names || preview.old_sites, 'MP 默认搜索站点') }}</div>
              <div>新订阅站点：{{ formatPreviewSites(preview.new_site_names || preview.new_sites) }}</div>
            </template>
            <template v-else>
              <div>旧 include：{{ preview.old_include || '-' }}</div>
              <div>新 include：{{ preview.new_include || '-' }}</div>
            </template>
          </div>
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="previewDialog = false">返回</VBtn>
          <VBtn color="primary" variant="text" :disabled="!preview?.token" @click="confirmRule">确认修改</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
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
const clearingRules = ref(false)
const deletingRuleId = ref('')
const deletingResultId = ref('')
const error = ref('')
const status = ref({})
const items = ref([])
const ruleRecords = ref([])
const identifierRecords = ref([])
const identifierAutoTitle = ref('')
const identifierManualTitle = ref('')
const identifierManualType = ref('tv')
const identifierManualTmdbid = ref('')
const identifierBusy = ref('')
const identifierError = ref('')
const identifierMessage = ref('')
const previewDialog = ref(false)
const preview = ref(null)
const previewError = ref('')
const previewContext = ref(null)
const previewLoading = ref('')
const ruleSuggestions = ref([])

const mediaTypeOptions = [
  { title: 'TV', value: 'tv' },
  { title: 'Movie', value: 'movie' },
]

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

function formatPreviewSites(value, emptyText = '-') {
  const items = Array.isArray(value) ? value : []
  const text = items.filter(item => item !== undefined && item !== null && String(item).trim()).map(item => String(item)).join(', ')
  return text || emptyText
}

function identifierModeText(mode) {
  return mode === 'manual' ? '手动' : '自动'
}

function identifierStatusText(statusValue) {
  return statusValue === 'success' ? '成功' : '失败'
}

function identifierStatusColor(statusValue) {
  return statusValue === 'success' ? 'success' : 'error'
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
    identifierRecords.value = data.identifier_records || status.value.identifier_records || []
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

async function deleteResult(item) {
  if (!item?.result_id) {
    error.value = '该诊断结果缺少标识，无法删除，请先刷新'
    return
  }
  deletingResultId.value = item.result_id
  error.value = ''
  try {
    await props.api.post('plugin/SubscribePlus/results/delete', { result_id: item.result_id })
    await loadData()
  } catch (err) {
    error.value = err?.message || '删除诊断结果失败'
  } finally {
    deletingResultId.value = ''
  }
}

async function clearRuleRecords() {
  clearingRules.value = true
  error.value = ''
  try {
    await props.api.post('plugin/SubscribePlus/rule_records/clear', {})
    await loadData()
  } catch (err) {
    error.value = err?.message || '清空规则修改记录失败'
  } finally {
    clearingRules.value = false
  }
}

async function deleteRuleRecord(record) {
  if (!record?.record_id) {
    error.value = '该规则记录缺少标识，无法删除，请先刷新'
    return
  }
  deletingRuleId.value = record.record_id
  error.value = ''
  try {
    await props.api.post('plugin/SubscribePlus/rule_records/delete', { record_id: record.record_id })
    await loadData()
  } catch (err) {
    error.value = err?.message || '删除规则记录失败'
  } finally {
    deletingRuleId.value = ''
  }
}

function readActionResponse(response, fallback) {
  const body = response?.data ?? response ?? {}
  const data = body?.data ?? body
  if (body.success === false || data.success === false) {
    return { success: false, message: body.message || data.message || fallback }
  }
  return { success: true, message: body.message || data.message || fallback }
}

async function runIdentifierAuto() {
  const title = identifierAutoTitle.value.trim()
  identifierError.value = ''
  identifierMessage.value = ''
  if (!title) {
    identifierError.value = '请填写媒体文件名'
    return
  }
  identifierBusy.value = 'auto'
  try {
    const response = await props.api.post('plugin/SubscribePlus/identifier_auto', { title })
    const result = readActionResponse(response, '已提交自动处理')
    if (!result.success) {
      identifierError.value = result.message
      return
    }
    identifierMessage.value = result.message
    await loadData()
  } catch (err) {
    identifierError.value = err?.message || '自动处理失败'
  } finally {
    identifierBusy.value = ''
  }
}

async function runIdentifierManual() {
  const title = identifierManualTitle.value.trim()
  const tmdbid = identifierManualTmdbid.value.trim()
  identifierError.value = ''
  identifierMessage.value = ''
  if (!title || !tmdbid) {
    identifierError.value = '请填写媒体文件名和 TMDB ID'
    return
  }
  identifierBusy.value = 'manual'
  try {
    const response = await props.api.post('plugin/SubscribePlus/identifier_manual', {
      title,
      media_type: identifierManualType.value,
      tmdbid,
    })
    const result = readActionResponse(response, '已提交手动处理')
    if (!result.success) {
      identifierError.value = result.message
      return
    }
    identifierMessage.value = result.message
    await loadData()
  } catch (err) {
    identifierError.value = err?.message || '手动处理失败'
  } finally {
    identifierBusy.value = ''
  }
}

async function previewRule(item, candidate) {
  previewDialog.value = true
  preview.value = null
  previewError.value = ''
  previewContext.value = { item, candidate }
  previewLoading.value = ''
  ruleSuggestions.value = []
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_suggestions', {
      diagnosis: item,
      candidate,
    })
    const body = response?.data ?? response ?? {}
    const data = body?.data ?? body
    if (body.success === false || data.success === false) {
      previewError.value = body.message || data.message || '生成规则建议失败'
      return
    }
    ruleSuggestions.value = data.items || []
    if (!ruleSuggestions.value.length) {
      previewError.value = '没有可添加的官组、平台或 PT 站点建议'
    } else if (ruleSuggestions.value.length === 1) {
      await previewRuleSuggestion(ruleSuggestions.value[0])
    }
  } catch (err) {
    previewError.value = err?.message || '生成规则建议失败'
  }
}

async function previewRuleSuggestion(suggestion) {
  if (!previewContext.value?.item || !suggestion?.pattern) return
  preview.value = null
  previewError.value = ''
  previewLoading.value = suggestion.pattern
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_preview', {
      subscribe_id: previewContext.value.item.subscribe_id,
      pattern: suggestion.pattern,
      selected_text: suggestion.text,
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
  } finally {
    previewLoading.value = ''
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
.sp-page { height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.sp-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 16px; width: min(1120px, 100%); margin: 0 auto; }
.sp-card { border-radius: 14px; overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.sp-header { padding: 12px 16px; }
.sp-subheader { padding: 10px 16px; }
.sp-result-header { padding: 10px 16px; }
.sp-stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.sp-stat { border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; padding: 10px; min-width: 0; }
.sp-stat-value { overflow-wrap: anywhere; }
.sp-id-row { row-gap: 0.5rem; }
.sp-id-action { display: flex; justify-content: flex-end; }
.sp-empty { min-height: 88px; display: flex; align-items: center; justify-content: center; color: rgba(var(--v-theme-on-surface), 0.62); }
.sp-candidate-wrap { max-width: 100%; overflow-x: auto; }
.sp-candidate-table { min-width: 42rem; }
.sp-cand-site { width: 7rem; white-space: nowrap; }
.sp-cand-title { overflow-wrap: anywhere; }
.sp-cand-seed { width: 4.5rem; }
.sp-cand-act { width: 6.5rem; white-space: nowrap; }
.sp-footer { flex-shrink: 0; padding: 6px 12px; border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.sp-suggestion { padding: 0.75rem; border: 1px solid rgba(var(--v-theme-primary), 0.16); border-radius: 8px; }
.sp-preview-box { display: grid; gap: 0.5rem; overflow-wrap: anywhere; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 0.875rem; }
@media (max-width: 760px) {
  .sp-page { height: 100dvh; }
  .sp-scroll { padding: 8px; }
  .sp-card { border-radius: 10px; }
  .sp-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sp-footer-spacer { display: none; }
  .sp-footer :deep(.v-btn) { flex: 1 1 auto; min-width: max-content; }
  .sp-candidate-table { min-width: 36rem; }
  .sp-id-action { justify-content: stretch; }
  .sp-id-action :deep(.v-btn) { flex: 1 1 auto; }
}
@media (max-width: 480px) {
  .sp-stat-grid { grid-template-columns: 1fr; }
}
</style>
