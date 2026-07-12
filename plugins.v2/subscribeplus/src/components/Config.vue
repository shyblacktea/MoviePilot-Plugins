<template>
  <div class="sp-config">
    <VCard flat class="sp-card">
      <VCardItem class="sp-header">
        <template #prepend>
          <img :src="subscribePlusLogo" alt="" class="sp-header-logo" />
        </template>
        <VCardTitle class="text-h6 sp-header-title">订阅下载增强</VCardTitle>
        <VCardSubtitle class="text-caption sp-header-subtitle">{{ currentGroup.desc }}</VCardSubtitle>
        <template #append>
          <div class="d-flex align-center ga-2">
            <div v-if="changedCount" class="sp-dirty-hint">
              <VIcon icon="mdi-circle-medium" color="warning" size="18" />
              <span class="text-caption text-warning font-weight-medium">{{ changedCount }} 项待保存</span>
            </div>
            <VBtn v-if="changedCount" color="primary" variant="flat" size="small" prepend-icon="mdi-content-save" rounded="lg" :loading="saving" @click="saveConfig">保存修改</VBtn>
            <VBtn icon="mdi-close" variant="text" size="small" @click="emit('close')" />
          </div>
        </template>
      </VCardItem>
      <VDivider />

      <div class="sp-body">
        <nav class="sp-nav">
          <VList density="comfortable" nav class="py-2 sp-nav-list">
            <VListItem
              v-for="item in groups"
              :key="item.key"
              :active="activeGroup === item.key"
              color="primary"
              rounded="lg"
              class="sp-nav-item"
              @click="activeGroup = item.key"
            >
              <template #prepend><VIcon :icon="item.icon" class="sp-nav-icon" /></template>
              <VListItemTitle class="sp-nav-title">{{ item.title }}</VListItemTitle>
              <template v-if="item.key === 'overview' && items.length" #append>
                <VChip size="x-small" color="warning" variant="tonal">{{ items.length }}</VChip>
              </template>
            </VListItem>
          </VList>
        </nav>

        <section class="sp-content">
          <!-- 移动端：当前分组栏 + 底部弹出分组选择 -->
          <div class="sp-mobile-groupbar">
            <VIcon :icon="currentGroup.icon" color="primary" size="20" />
            <div class="sp-mobile-groupinfo">
              <div class="sp-mobile-group-title">{{ currentGroup.title }}</div>
              <div class="sp-mobile-group-desc">{{ currentGroup.desc }}</div>
            </div>
            <VBtn icon="mdi-format-list-bulleted" variant="tonal" size="small" rounded="lg" @click="mobileGroupSheet = true" />
          </div>

          <VAlert v-if="error" type="error" variant="tonal" density="compact" class="ma-3 mb-0 text-caption" closable @click:close="error = ''">
            {{ error }}
          </VAlert>

          <div class="sp-workspace">
            <div class="sp-window">
            <!-- ===== 运行概览 ===== -->
            <div v-show="activeGroup === 'overview'" class="sp-pane">
              <div class="d-flex align-center flex-wrap ga-1 mb-3">
                <div class="sp-section-title mb-0">运行概览</div>
                <VSpacer />
                <VBtn color="primary" prepend-icon="mdi-radar" variant="tonal" size="small" :loading="scanning" @click="runScan">手动扫描</VBtn>
                <VBtn color="warning" prepend-icon="mdi-delete-sweep-outline" variant="text" size="small" :loading="clearing" @click="clearResults">清除诊断</VBtn>
                <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="loadData" />
              </div>

              <div class="sp-stat-grid mb-4">
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

              <template v-if="items.length">
                <VCard v-for="item in items" :key="item.result_id || (item.subscribe_id + '-' + item.created_at)" flat class="sp-inner-card mb-3">
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
                          <tr><th>站点</th><th>标题</th><th>做种</th><th class="text-right">操作</th></tr>
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
              </template>
              <div v-else class="sp-empty">暂无待处理诊断</div>
            </div>

            <!-- ===== 识别词工具 ===== -->
            <div v-show="activeGroup === 'identifier'" class="sp-pane">
              <div class="d-flex align-center mb-3">
                <div class="sp-section-title mb-0">自定义识别词</div>
                <VSpacer />
                <VChip size="small" variant="tonal">{{ identifierRecords.length }}</VChip>
              </div>
              <VAlert v-if="identifierError" type="error" density="compact" variant="tonal" class="mb-3 text-caption" closable @click:close="identifierError = ''">{{ identifierError }}</VAlert>
              <VAlert v-if="identifierMessage" type="success" density="compact" variant="tonal" class="mb-3 text-caption" closable @click:close="identifierMessage = ''">{{ identifierMessage }}</VAlert>

              <div class="sp-subsection-title">自动处理</div>
              <VRow class="sp-id-row" align="center">
                <VCol cols="12" md="8"><VTextField v-model="identifierAutoTitle" label="媒体文件名" density="compact" variant="outlined" hide-details clearable /></VCol>
                <VCol cols="12" md="4" class="sp-id-action">
                  <VBtn color="primary" prepend-icon="mdi-auto-fix" variant="tonal" size="small" :loading="identifierBusy === 'auto'" @click="runIdentifierAuto">自动处理</VBtn>
                </VCol>
              </VRow>
              <VDivider class="my-3" />
              <div class="sp-subsection-title">手动处理</div>
              <VRow class="sp-id-row" align="center">
                <VCol cols="12" md="5"><VTextField v-model="identifierManualTitle" label="媒体文件名" density="compact" variant="outlined" hide-details clearable /></VCol>
                <VCol cols="6" md="2"><VSelect v-model="identifierManualType" :items="mediaTypeOptions" label="类型" density="compact" variant="outlined" hide-details /></VCol>
                <VCol cols="6" md="3"><VTextField v-model="identifierManualTmdbid" label="TMDB ID" placeholder="填写 TMDB 的 ID" density="compact" variant="outlined" hide-details clearable /></VCol>
                <VCol cols="12" md="2" class="sp-id-action">
                  <VBtn color="primary" prepend-icon="mdi-pencil-plus-outline" variant="tonal" size="small" :loading="identifierBusy === 'manual'" @click="runIdentifierManual">手动处理</VBtn>
                </VCol>
              </VRow>

              <VList v-if="identifierRecords.length" density="compact" lines="two" class="mt-2">
                <VListItem
                  v-for="record in identifierRecords"
                  :key="record.mode + '-' + record.candidate_title + '-' + record.created_at"
                  :title="identifierModeText(record.mode) + '：' + (record.candidate_title || record.title || '-')"
                  :subtitle="(record.message || '-') + ' / ' + (record.created_at || '-')"
                >
                  <template #append>
                    <VChip :color="identifierStatusColor(record.status)" size="small" variant="tonal">{{ identifierStatusText(record.status) }}</VChip>
                  </template>
                </VListItem>
              </VList>
              <div v-else class="sp-empty">暂无识别词记录</div>
            </div>

            <!-- ===== 规则记录 ===== -->
            <div v-show="activeGroup === 'rules'" class="sp-pane">
              <div class="d-flex align-center mb-3">
                <div class="sp-section-title mb-0">规则修改记录</div>
                <VSpacer />
                <VBtn v-if="ruleRecords.length" color="warning" variant="text" size="small" prepend-icon="mdi-delete-sweep-outline" :loading="clearingRules" @click="clearRuleRecords">清空</VBtn>
              </div>
              <VList v-if="ruleRecords.length" density="compact" lines="two">
                <VListItem
                  v-for="record in ruleRecords"
                  :key="record.record_id || (record.subscribe_id + '-' + record.created_at)"
                  :title="'【' + (record.subscribe_name || ('订阅#' + record.subscribe_id)) + '】' + (record.change_type || record.field)"
                  :subtitle="(record.old_value || '-') + ' → ' + (record.new_value || '-') + '（' + (record.source || '-') + ' / ' + (record.created_at || '-') + '）'"
                >
                  <template #append>
                    <VBtn icon="mdi-delete-outline" color="error" variant="text" size="small" :loading="deletingRuleId === record.record_id" @click="deleteRuleRecord(record)" />
                  </template>
                </VListItem>
              </VList>
              <div v-else class="sp-empty">暂无记录</div>
            </div>

            <!-- ===== 元数据驱动的配置 tab（scan/notify/cleanup）===== -->
            <div v-for="groupKey in configGroupKeys" v-show="activeGroup === groupKey" :key="groupKey" class="sp-pane">
              <section v-for="(section, sIdx) in sectionsOf(groupKey)" :key="section.title" class="sp-config-section">
                <div class="sp-section-title">{{ (sIdx + 1) + '. ' + section.title }}</div>
                <div class="sp-field-rows">
                  <div v-for="field in section.fields" :key="field.key" class="sp-field-row">
                    <div class="sp-field-info">
                      <div class="sp-field-label">{{ field.label }}</div>
                      <div v-if="field.hint" class="sp-field-hint">{{ field.hint }}</div>
                    </div>
                    <div class="sp-field-control" :class="'sp-ctl-' + field.type">
                      <VSwitch v-if="field.type === 'switch'" v-model="config[field.key]" :color="field.color || 'primary'" inset hide-details density="compact" />
                      <VTextField v-else-if="field.type === 'number'" v-model.number="config[field.key]" type="number" :min="field.min" variant="outlined" density="compact" hide-details rounded="lg" />
                      <VTextField v-else-if="field.type === 'text'" v-model="config[field.key]" variant="outlined" density="compact" hide-details="auto" rounded="lg" :error-messages="field.validate === 'cron' ? cronError : ''" />
                      <VSelect v-else-if="field.type === 'select'" v-model="config[field.key]" :items="field.options" item-title="title" item-value="value" variant="outlined" density="compact" hide-details rounded="lg" />
                      <VSelect v-else-if="field.type === 'multiselect'" v-model="config[field.key]" :items="optionsFor(field)" item-title="title" item-value="value" variant="outlined" density="compact" multiple chips closable-chips :clearable="field.clearable" hide-details rounded="lg" />
                    </div>
                  </div>
                </div>
                <template v-for="field in section.fields" :key="field.key + '-alert'">
                  <VAlert v-if="field.alert" class="mt-3" type="info" variant="tonal" density="compact" :text="field.alert" />
                </template>
              </section>
            </div>
            </div>

            <aside class="sp-dashboard" aria-label="运行表盘">
              <section class="sp-dashboard-section">
                <div class="sp-dashboard-title"><VIcon icon="mdi-clock-outline" color="primary" size="20" />运行节奏</div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-calendar-sync-outline" /><span>定时扫描</span><strong>{{ scanScheduleText }}</strong></div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-calendar-alert-outline" /><span>超期检测</span><strong>播出后 {{ config.delay_days }} 天</strong></div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-message-processing-outline" /><span>通知方式</span><strong>队列逐条</strong></div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-database-clock-outline" /><span>候选缓存</span><strong>{{ candidateCacheText }}</strong></div>
              </section>

              <VDivider class="my-3" />

              <section class="sp-dashboard-section">
                <div class="sp-dashboard-title"><VIcon icon="mdi-chart-box-outline" color="primary" size="20" />运行概况</div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-history" /><span>最近扫描</span><strong>{{ lastScanText }}</strong></div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-timer-sand" /><span>待处理</span><strong>{{ items.length }}</strong></div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-download-box-outline" /><span>候选资源</span><strong>{{ candidateTotal }}</strong></div>
                <div class="sp-dashboard-row"><VIcon icon="mdi-toggle-switch-outline" /><span>已启用功能</span><strong>{{ enabledFeatureCount }}/6</strong></div>
              </section>
            </aside>
          </div>

        </section>
      </div>
    </VCard>

    <!-- 移动端底部弹出：选择配置分组 -->
    <VBottomSheet v-model="mobileGroupSheet">
      <VCard rounded="t-xl" class="sp-sheet">
        <VCardTitle class="text-subtitle-1 font-weight-bold px-4 pt-4">选择配置分组</VCardTitle>
        <VCardText class="px-3 pb-4">
          <VList density="comfortable" nav>
            <VListItem
              v-for="item in groups"
              :key="item.key"
              :active="activeGroup === item.key"
              color="primary"
              rounded="lg"
              class="sp-sheet-item"
              @click="activeGroup = item.key; mobileGroupSheet = false"
            >
              <template #prepend><VIcon :icon="item.icon" /></template>
              <VListItemTitle class="font-weight-medium">{{ item.title }}</VListItemTitle>
              <VListItemSubtitle class="text-caption">{{ item.desc }}</VListItemSubtitle>
              <template #append>
                <VIcon v-if="activeGroup === item.key" icon="mdi-check" color="primary" />
                <VChip v-else-if="item.key === 'overview' && items.length" size="x-small" color="warning" variant="tonal">{{ items.length }}</VChip>
              </template>
            </VListItem>
          </VList>
        </VCardText>
      </VCard>
    </VBottomSheet>

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
              color="primary" variant="tonal" size="small" class="mr-2 mb-2"
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

    <VSnackbar v-model="saveSnackbar" color="success" location="top" :timeout="2200">
      {{ saveMessage }}
    </VSnackbar>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import subscribePlusLogo from '../assets/subscribeplus-logo.svg'
import { groups, fields, defaults, validateCron } from '../config/fields.js'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close', 'switch', 'layout'])
const layoutRequest = { maxWidth: '70rem' }

// ===== 通用状态 =====
const activeGroup = ref('overview')
const mobileGroupSheet = ref(false)
const error = ref('')
const loading = ref(false)
const saving = ref(false)
const saveMessage = ref('')
const saveSnackbar = ref(false)
const cronError = ref('')

// ===== 配置（元数据驱动）=====
const config = reactive({ ...defaults })
// 已保存基线快照：与 config 逐键对比得出待保存项数
const savedBaseline = ref(JSON.parse(JSON.stringify(defaults)))

function normalizeValue(value) {
  if (Array.isArray(value)) return JSON.stringify([...value].sort())
  if (value === undefined || value === null) return ''
  return String(value)
}

const changedCount = computed(() => {
  let count = 0
  for (const key of Object.keys(defaults)) {
    if (normalizeValue(config[key]) !== normalizeValue(savedBaseline.value[key])) count++
  }
  return count
})

function snapshotBaseline() {
  savedBaseline.value = JSON.parse(JSON.stringify({ ...defaults, ...config }))
}

// ===== 概览数据 =====
const status = ref({})
const items = ref([])
const ruleRecords = ref([])
const identifierRecords = ref([])
const scanning = ref(false)
const clearing = ref(false)
const clearingRules = ref(false)
const deletingRuleId = ref('')
const deletingResultId = ref('')

// ===== 识别词 =====
const identifierAutoTitle = ref('')
const identifierManualTitle = ref('')
const identifierManualType = ref('tv')
const identifierManualTmdbid = ref('')
const identifierBusy = ref('')
const identifierError = ref('')
const identifierMessage = ref('')
const mediaTypeOptions = [
  { title: 'TV', value: 'tv' },
  { title: 'Movie', value: 'movie' },
]

// ===== 规则预览对话框 =====
const previewDialog = ref(false)
const preview = ref(null)
const previewError = ref('')
const previewContext = ref(null)
const previewLoading = ref('')
const ruleSuggestions = ref([])

// ===== 选项 =====
const categories = ref([])
const siteOptions = ref([])

const currentGroup = computed(() => groups.find(g => g.key === activeGroup.value) || groups[0])
const configGroupKeys = ['scan', 'notify', 'cleanup']

const reasonCount = computed(() => items.value.reduce((acc, item) => {
  acc[item.reason] = (acc[item.reason] || 0) + 1
  return acc
}, {}))

const candidateTotal = computed(() => items.value.reduce(
  (total, item) => total + (Array.isArray(item.candidates) ? item.candidates.length : 0),
  0,
))

const enabledFeatureCount = computed(() => [
  Boolean(config.enabled),
  Boolean(config.notify_tg),
  Boolean(config.allow_tg_rule_update),
  config.season_pack_cleanup !== 'off',
  Boolean(config.season_pack_full_download),
  Number(config.candidate_cache_days) > 0,
].filter(Boolean).length)

const scanScheduleText = computed(() => describeCron(config.cron))
const candidateCacheText = computed(() => Number(config.candidate_cache_days) > 0 ? `${config.candidate_cache_days} 天` : '已关闭')
const lastScanText = computed(() => formatCompactDateTime(status.value.last_scan))

function describeCron(value) {
  const cron = String(value || '').trim()
  const parts = cron.split(/\s+/)
  if (parts.length !== 5) return cron || '-'
  const [minute, hour, day, month, weekday] = parts
  if (day === '*' && month === '*' && weekday === '*') {
    if (/^\d+$/.test(minute) && /^\d+$/.test(hour)) {
      return `每天 ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
    }
    const hourStep = hour.match(/^\*\/(\d+)$/)
    if (minute === '0' && hourStep) return `每 ${hourStep[1]} 小时`
    const minuteStep = minute.match(/^\*\/(\d+)$/)
    if (hour === '*' && minuteStep) return `每 ${minuteStep[1]} 分钟`
  }
  return cron
}

function formatCompactDateTime(value) {
  if (!value) return '-'
  const text = String(value).replace('T', ' ')
  return text.length >= 16 ? text.slice(5, 16) : text
}

/**
 * 按元数据取某 tab 下的小节列表（含各自字段）。
 */
function sectionsOf(groupKey) {
  const result = []
  for (const field of fields) {
    if (field.group !== groupKey) continue
    let section = result.find(s => s.title === field.section)
    if (!section) {
      section = { title: field.section, fields: [] }
      result.push(section)
    }
    section.fields.push(field)
  }
  return result
}

/** 取多选字段的动态选项 */
function optionsFor(field) {
  if (field.optionsKey === 'categories') return categories.value
  if (field.optionsKey === 'sites') return siteOptions.value
  return field.options || []
}

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

function reasonText(reason) {
  return {
    no_pt_resource: '暂无资源',
    recognition_issue: '疑似识别',
    rule_blocked: '规则拦截',
    site_scope_blocked: '订阅站点无目标集',
    downloadable: '可下载',
    search_failed: '搜索失败',
  }[reason] || reason || '未知'
}

function reasonColor(reason) {
  return {
    no_pt_resource: 'grey',
    recognition_issue: 'warning',
    rule_blocked: 'info',
    site_scope_blocked: 'warning',
    downloadable: 'success',
    search_failed: 'error',
  }[reason] || 'grey'
}

function formatPreviewSites(value, emptyText = '-') {
  const arr = Array.isArray(value) ? value : []
  const text = arr.filter(item => item !== undefined && item !== null && String(item).trim()).map(String).join(', ')
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

function applyInitialConfig(source = props.initialConfig) {
  const initial = source && typeof source === 'object' ? source : {}
  Object.assign(config, {
    ...config,
    ...initial,
    selected_categories: Array.isArray(initial.selected_categories)
      ? [...initial.selected_categories]
      : [],
    search_sites: Array.isArray(initial.search_sites)
      ? [...initial.search_sites]
      : [],
    season_pack_cleanup: initial.season_pack_cleanup || 'off',
    season_pack_full_download: Boolean(initial.season_pack_full_download),
    candidate_cache_days:
      initial.candidate_cache_days === undefined || initial.candidate_cache_days === null
        ? 3
        : Number(initial.candidate_cache_days),
  })
}

async function loadOptions() {
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
      // 自动填充不算用户改动，同步进基线避免误报待保存
      savedBaseline.value.selected_categories = [...config.selected_categories]
    }
  } catch (err) {
    error.value = err?.message || '读取配置选项失败'
  }
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
  } catch (err) {
    error.value = err?.message || '读取诊断结果失败'
  } finally {
    loading.value = false
  }
}

async function reloadAll() {
  await Promise.all([loadData(), loadOptions()])
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

function buildConfigPayload() {
  return {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    candidate_cache_days: Number(config.candidate_cache_days),
    search_sites: Array.isArray(config.search_sites) ? [...config.search_sites] : [],
    selected_categories: Array.isArray(config.selected_categories) ? [...config.selected_categories] : [],
  }
}

async function saveConfig() {
  cronError.value = validateCron(config.cron)
  if (cronError.value) {
    activeGroup.value = 'scan'
    return
  }
  const payload = buildConfigPayload()
  error.value = ''
  saving.value = true
  try {
    if (typeof props.api?.post === 'function') {
      const response = await props.api.post('plugin/SubscribePlus/config', payload)
      const body = response?.data ?? response ?? {}
      const data = body?.data ?? body
      if (body.success === false || data.success === false) {
        throw new Error(body.message || data.message || '配置保存失败')
      }

      const verifyResponse = await props.api.get('plugin/SubscribePlus/config')
      const persisted = unwrap(verifyResponse)
      applyInitialConfig(persisted)
      snapshotBaseline()
      saveMessage.value = body.message || data.message || '配置已保存并生效'
      saveSnackbar.value = true
      return
    }

    emit('save', payload)
    snapshotBaseline()
  } catch (err) {
    error.value = err?.message || '配置保存失败'
  } finally {
    saving.value = false
  }
}

watch(
  () => props.initialConfig,
  value => {
    if (!value || typeof value !== 'object' || !Object.keys(value).length) return
    applyInitialConfig(value)
    snapshotBaseline()
  },
  { deep: true },
)

onMounted(() => {
  emit('layout', layoutRequest)
  applyInitialConfig()
  snapshotBaseline()
  reloadAll()
})
</script>

<style scoped>
.sp-config { container-type: inline-size; width: min(1120px, calc(100vw - 48px)); max-width: 100%; height: min(90dvh, 820px); max-height: calc(100dvh - 16px); padding: 8px; margin: 0 auto; display: flex; }
.sp-card { width: 100%; height: 100%; min-height: 0; display: flex; flex-direction: column; border-radius: 14px; overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.sp-header { padding: 14px 18px; }
.sp-header-logo { display: block; width: 44px; height: 44px; flex: 0 0 44px; }
.sp-header-subtitle { max-width: min(560px, 52vw); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-body { flex: 1 1 auto; min-height: 0; display: flex; }
.sp-nav { width: 168px; flex: 0 0 168px; border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); background: rgba(var(--v-theme-on-surface), .02); }
.sp-nav-item { margin: 2px 8px; }
.sp-content { flex: 1 1 auto; min-width: 0; min-height: 0; display: flex; flex-direction: column; }
.sp-workspace { flex: 1 1 auto; min-width: 0; min-height: 0; overflow-y: auto; }
.sp-mobile-groupbar { display: none; }
.sp-sheet-item { margin: 3px 4px; }
.sp-window { min-width: 0; min-height: 0; overflow: visible; }
.sp-pane { padding: 18px 20px; }
.sp-section-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: rgb(var(--v-theme-primary)); }
.sp-config-section { padding: 14px 16px 6px; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; background: rgba(var(--v-theme-on-surface), .015); }
.sp-config-section + .sp-config-section { margin-top: 14px; }
.sp-config-section .sp-section-title { margin-bottom: 8px; }
.sp-field-rows { display: flex; flex-direction: column; }
.sp-field-row { display: flex; align-items: center; gap: 16px; padding: 12px 2px; border-bottom: 1px solid rgba(var(--v-border-color), calc(var(--v-border-opacity) * .6)); }
.sp-field-row:last-child { border-bottom: none; }
.sp-field-info { flex: 1 1 auto; min-width: 0; }
.sp-field-label { font-size: 14px; font-weight: 600; line-height: 1.4; }
.sp-field-hint { font-size: 12px; opacity: .58; margin-top: 2px; line-height: 1.4; }
.sp-field-control { flex: 0 0 auto; display: flex; justify-content: flex-end; }
.sp-ctl-number { width: 170px; }
.sp-ctl-text { width: 220px; }
.sp-ctl-select { width: 220px; }
.sp-ctl-multiselect { width: min(360px, 42vw); }
.sp-ctl-switch { width: auto; }
.sp-subsection-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; opacity: .78; }
.sp-dirty-hint { display: flex; align-items: center; }
.sp-inner-card { border-radius: 10px; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); overflow: hidden; }
.sp-result-header { padding: 10px 16px; }
.sp-stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.sp-stat { border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; padding: 10px; min-width: 0; }
.sp-stat-value { overflow-wrap: anywhere; }
.sp-id-row { row-gap: .5rem; }
.sp-id-action { display: flex; justify-content: flex-end; }
.sp-empty { min-height: 88px; display: flex; align-items: center; justify-content: center; color: rgba(var(--v-theme-on-surface), .62); }
.sp-candidate-wrap { max-width: 100%; overflow-x: auto; }
.sp-candidate-table { min-width: 42rem; }
.sp-cand-site { width: 7rem; white-space: nowrap; }
.sp-cand-title { overflow-wrap: anywhere; }
.sp-cand-seed { width: 4.5rem; }
.sp-cand-act { width: 6.5rem; white-space: nowrap; }
.sp-suggestion { padding: .75rem; border: 1px solid rgba(var(--v-theme-primary), .16); border-radius: 8px; }
.sp-preview-box { display: grid; gap: .5rem; overflow-wrap: anywhere; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .875rem; }
.sp-dashboard { margin: 0 12px 12px; padding: 14px 16px; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; background: rgba(var(--v-theme-on-surface), .015); }
.sp-dashboard-section { min-width: 0; }
.sp-dashboard-title { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 14px; font-weight: 700; }
.sp-dashboard-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto; align-items: center; gap: 8px; min-height: 38px; color: rgba(var(--v-theme-on-surface), .68); font-size: 13px; }
.sp-dashboard-row > .v-icon { color: rgba(var(--v-theme-on-surface), .52); }
.sp-dashboard-row strong { min-width: 0; color: rgb(var(--v-theme-on-surface)); font-weight: 600; text-align: right; overflow-wrap: anywhere; }
@container (min-width: 980px) {
  .sp-workspace { display: grid; grid-template-columns: minmax(0, 1fr) 252px; overflow: hidden; }
  .sp-window { overflow-x: hidden; overflow-y: auto; }
  .sp-dashboard { margin: 0; padding: 18px 16px; border-width: 0 0 0 1px; border-radius: 0; overflow-y: auto; }
}
@media (max-width: 760px) {
  .sp-config { width: 100%; height: 100dvh; max-height: 100dvh; padding: 0; }
  .sp-card { border-radius: 0; border: none; }
  .sp-header { padding: 8px 10px; }
  .sp-header-logo { width: 34px; height: 34px; flex-basis: 34px; }
  .sp-header-title { font-size: 15px; line-height: 1.25; }
  .sp-header-subtitle { max-width: 100%; }
  .sp-dirty-hint { display: none; }
  .sp-body { flex-direction: column; }
  .sp-nav { display: none; }
  .sp-mobile-groupbar { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
  .sp-mobile-groupinfo { flex: 1 1 auto; min-width: 0; }
  .sp-mobile-group-title { font-size: 14px; font-weight: 600; line-height: 1.3; }
  .sp-mobile-group-desc { font-size: 11px; opacity: .6; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sp-window { max-height: none; }
  .sp-pane { padding: 12px 12px; }
  .sp-section-title { margin-bottom: 8px; }
  .sp-config-section { padding: 12px 12px 4px; }
  .sp-config-section + .sp-config-section { margin-top: 10px; }
  .sp-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sp-field-row { flex-direction: column; align-items: stretch; gap: 8px; }
  .sp-field-control { justify-content: stretch; }
  .sp-ctl-number, .sp-ctl-text, .sp-ctl-select, .sp-ctl-multiselect { width: 100%; }
  .sp-ctl-switch { justify-content: flex-end; }
  .sp-candidate-table { min-width: 36rem; }
  .sp-id-action { justify-content: stretch; }
  .sp-id-action :deep(.v-btn) { flex: 1 1 auto; }
}
@media (orientation: portrait) and (min-width: 761px) {
  .sp-config { height: calc(100dvh - 16px); }
}
@media (max-width: 480px) {
  .sp-stat-grid { grid-template-columns: 1fr; }
}
</style>
