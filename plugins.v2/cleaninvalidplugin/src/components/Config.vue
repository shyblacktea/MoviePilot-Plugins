<template>
  <div class="cip-config">
    <VCard flat class="cip-card">
      <VCardItem class="cip-header">
        <template #prepend>
          <VAvatar color="primary" variant="tonal" size="44" rounded="lg">
            <VIcon icon="mdi-delete-sweep-outline" size="24" />
          </VAvatar>
        </template>
        <VCardTitle class="cip-header-title">清理无效插件</VCardTitle>
        <VCardSubtitle class="cip-header-subtitle">{{ currentTab.description }}</VCardSubtitle>
        <template #append>
          <div class="cip-header-actions">
            <VChip v-if="jobRunning" color="primary" variant="tonal" size="small" class="cip-job-chip">
              后台 {{ jobCompleted }}/{{ jobTotal }}
            </VChip>
            <VBtn
              icon="mdi-refresh"
              variant="text"
              size="small"
              :loading="loading"
              aria-label="刷新"
              @click="loadInvalidPlugins"
            />
            <VBtn
              v-if="showSwitch"
              icon="mdi-view-dashboard-outline"
              variant="text"
              size="small"
              aria-label="数据页"
              @click="emit('switch')"
            />
            <VBtn icon="mdi-close" variant="text" size="small" aria-label="关闭" @click="emit('close')" />
          </div>
        </template>
      </VCardItem>

      <VDivider />

      <div class="cip-body">
        <nav class="cip-nav" aria-label="插件操作">
          <VList density="comfortable" nav class="py-2">
            <VListItem
              v-for="tab in actionTabs"
              :key="tab.value"
              :active="config.action_mode === tab.value"
              color="primary"
              rounded="lg"
              class="cip-nav-item"
              @click="config.action_mode = tab.value"
            >
              <template #prepend><VIcon :icon="tab.icon" /></template>
              <VListItemTitle>{{ tab.title }}</VListItemTitle>
              <VListItemSubtitle>{{ tab.navDescription }}</VListItemSubtitle>
              <template #append>
                <VChip v-if="invalidItems.length" size="x-small" variant="tonal">
                  {{ invalidItems.length }}
                </VChip>
              </template>
            </VListItem>
          </VList>
        </nav>

        <section class="cip-content">
          <div class="cip-mobile-tabbar">
            <div class="cip-mobile-tabinfo">
              <div class="font-weight-medium">{{ currentTab.title }}</div>
              <div class="text-caption text-medium-emphasis">{{ currentTab.navDescription }}</div>
            </div>
            <VBtn icon="mdi-menu-down" variant="tonal" size="small" @click="mobileTabSheet = true" />
          </div>

          <VAlert
            v-if="error"
            type="error"
            variant="tonal"
            density="compact"
            closable
            class="ma-3 mb-0 text-caption"
            @click:close="error = ''"
          >
            {{ error }}
          </VAlert>

          <div class="cip-workspace">
            <div class="cip-window">
              <div
                v-for="tab in actionTabs"
                v-show="config.action_mode === tab.value"
                :key="tab.value"
                class="cip-pane"
              >
                <div class="cip-pane-heading">
                  <div class="cip-pane-title-wrap">
                    <VAvatar :color="tab.color" variant="tonal" size="38" rounded="lg">
                      <VIcon :icon="tab.icon" size="21" />
                    </VAvatar>
                    <div>
                      <div class="cip-section-title">{{ tab.title }}</div>
                      <div class="cip-section-desc">{{ tab.description }}</div>
                    </div>
                  </div>
                  <VChip size="small" variant="tonal" :color="selectedCount ? tab.color : 'default'">
                    已选 {{ selectedCount }}
                  </VChip>
                </div>

                <VAlert
                  :type="tab.alertType"
                  variant="tonal"
                  density="compact"
                  icon="mdi-information-outline"
                  class="mb-4 text-caption"
                >
                  {{ tab.hint }}
                </VAlert>

                <section v-if="jobRunning" class="cip-progress-panel" aria-live="polite">
                  <div class="cip-progress-heading">
                    <div class="cip-progress-title">
                      <VIcon icon="mdi-progress-clock" color="primary" size="20" />
                      <div>
                        <strong>正在后台重新安装</strong>
                        <span>{{ jobStatusText }}</span>
                      </div>
                    </div>
                    <strong class="cip-progress-percent">{{ jobProgress }}%</strong>
                  </div>
                  <VProgressLinear
                    :model-value="jobProgress"
                    color="primary"
                    height="8"
                    rounded
                    striped
                    class="my-3"
                  />
                  <div class="cip-progress-metrics">
                    <span>完成 {{ jobCompleted }}/{{ jobTotal }}</span>
                    <span>成功 {{ lastResult.reinstalled_count || 0 }}</span>
                    <span>跳过 {{ lastResult.skipped_count || 0 }}</span>
                    <span :class="{ 'text-warning': lastResult.failed_count }">失败 {{ lastResult.failed_count || 0 }}</span>
                  </div>
                  <div class="cip-progress-note">后台任务运行期间可以关闭页面，重新打开后会继续显示进度。</div>
                </section>

                <div class="cip-selection-toolbar">
                  <div class="cip-block-title">选择插件</div>
                  <VSpacer />
                  <VBtn
                    color="primary"
                    variant="text"
                    size="small"
                    prepend-icon="mdi-check-all"
                    :disabled="!invalidItems.length"
                    @click="selectAll"
                  >
                    全选
                  </VBtn>
                  <VBtn
                    color="secondary"
                    variant="text"
                    size="small"
                    prepend-icon="mdi-close"
                    :disabled="!selectedCount"
                    @click="clearSelection"
                  >
                    清空
                  </VBtn>
                </div>

                <VSelect
                  v-model="config.invalid_plugin_ids"
                  :items="invalidItems"
                  item-title="title"
                  item-value="id"
                  :label="tab.selectLabel"
                  variant="outlined"
                  density="compact"
                  multiple
                  chips
                  closable-chips
                  clearable
                  :loading="loading"
                  :disabled="loading || !invalidItems.length"
                  hide-details="auto"
                  class="mb-3"
                />

                <VList v-if="invalidItems.length" lines="two" density="compact" class="cip-plugin-list">
                  <VListItem
                    v-for="plugin in invalidItems"
                    :key="plugin.id"
                    :title="plugin.id"
                    :subtitle="plugin.status"
                    class="cip-plugin-row"
                    @click="togglePlugin(plugin.id)"
                  >
                    <template #prepend>
                      <VCheckboxBtn
                        :model-value="config.invalid_plugin_ids.includes(plugin.id)"
                        @click.stop
                        @update:model-value="togglePlugin(plugin.id)"
                      />
                    </template>
                    <template #append>
                      <VChip
                        :color="tab.value === 'reinstall'
                          ? (plugin.source_type === 'local' ? 'success' : (plugin.source_type === 'online' ? 'info' : 'warning'))
                          : (plugin.runtime_exists ? 'warning' : 'error')"
                        size="small"
                        variant="tonal"
                      >
                        {{ tab.value === 'reinstall'
                          ? (plugin.source_type === 'local' ? '本地源' : (plugin.source_type === 'online' ? '在线源' : '无可用源'))
                          : (plugin.runtime_exists ? '目录异常' : '目录缺失') }}
                      </VChip>
                    </template>
                  </VListItem>
                </VList>

                <div v-else-if="loading" class="cip-empty">
                  <VProgressCircular indeterminate color="primary" size="32" />
                  <span>正在读取插件状态...</span>
                </div>

                <div v-else class="cip-empty">
                  <VIcon icon="mdi-check-circle-outline" size="42" color="success" />
                  <strong>没有无效插件</strong>
                  <span>当前无需执行{{ tab.title }}。</span>
                </div>

                <VAlert
                  v-if="lastResult.message && !jobRunning"
                  :type="lastResult.success ? 'success' : 'warning'"
                  variant="tonal"
                  density="compact"
                  icon="mdi-history"
                  class="mt-4 text-caption"
                >
                  {{ lastResult.message }}
                </VAlert>

                <div class="cip-action-dock">
                  <div class="cip-action-copy">
                    <strong>{{ jobRunning ? `后台重装 ${jobCompleted}/${jobTotal}` : (selectedCount ? `将处理 ${selectedCount} 个插件` : '请选择插件') }}</strong>
                    <span>{{ jobRunning ? '任务已交给后台，当前页面可以正常关闭。' : tab.actionDescription }}</span>
                  </div>
                  <VBtn
                    :color="tab.color"
                    :prepend-icon="tab.buttonIcon"
                    variant="flat"
                    size="small"
                    :loading="submitting"
                    :disabled="!selectedCount || jobRunning || submitting"
                    @click="runAction"
                  >
                    {{ jobRunning ? '后台重装中' : tab.buttonLabel }}
                  </VBtn>
                </div>
              </div>
            </div>

            <aside class="cip-dashboard" aria-label="插件状态">
              <section>
                <div class="cip-dashboard-title">
                  <VIcon icon="mdi-chart-box-outline" color="primary" size="20" />
                  当前状态
                </div>
                <div class="cip-dashboard-row"><VIcon icon="mdi-alert-circle-outline" /><span>无效记录</span><strong>{{ invalidItems.length }}</strong></div>
                <div class="cip-dashboard-row"><VIcon icon="mdi-source-branch-check" /><span>本地源可用</span><strong>{{ localSourceCount }}</strong></div>
                <div class="cip-dashboard-row"><VIcon icon="mdi-cloud-download-outline" /><span>在线源可用</span><strong>{{ onlineSourceCount }}</strong></div>
                <div class="cip-dashboard-row"><VIcon icon="mdi-folder-alert-outline" /><span>运行目录存在</span><strong>{{ runtimeExistsCount }}</strong></div>
                <div class="cip-dashboard-row"><VIcon icon="mdi-checkbox-marked-circle-outline" /><span>当前选择</span><strong>{{ selectedCount }}</strong></div>
              </section>
              <VDivider class="my-3" />
              <section>
                <div class="cip-dashboard-title">
                  <VIcon :icon="currentTab.icon" :color="currentTab.color" size="20" />
                  {{ currentTab.title }}
                </div>
                <p class="cip-dashboard-note">{{ currentTab.hint }}</p>
              </section>
            </aside>
          </div>
        </section>
      </div>
    </VCard>

    <VBottomSheet v-model="mobileTabSheet">
      <VCard rounded="t-xl" class="cip-sheet">
        <VCardTitle class="text-subtitle-1 font-weight-bold px-4 pt-4">选择操作</VCardTitle>
        <VCardText class="px-3 pb-4">
          <VList density="comfortable" nav>
            <VListItem
              v-for="tab in actionTabs"
              :key="tab.value"
              :active="config.action_mode === tab.value"
              color="primary"
              rounded="lg"
              :title="tab.title"
              :subtitle="tab.description"
              @click="config.action_mode = tab.value; mobileTabSheet = false"
            >
              <template #prepend><VIcon :icon="tab.icon" /></template>
              <template #append><VIcon v-if="config.action_mode === tab.value" icon="mdi-check" color="primary" /></template>
            </VListItem>
          </VList>
        </VCardText>
      </VCard>
    </VBottomSheet>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
  showSwitch: { type: Boolean, default: true },
})

const emit = defineEmits(['save', 'close', 'switch', 'layout', 'action'])
const layoutRequest = { maxWidth: '70rem' }
emit('layout', layoutRequest)

const loading = ref(false)
const submitting = ref(false)
const error = ref('')
const invalidItems = ref([])
const lastResult = ref({})
const mobileTabSheet = ref(false)

const config = reactive({
  invalid_plugin_ids: [],
  action_mode: 'clean',
})

const actionTabs = [
  {
    value: 'clean',
    title: '清理记录',
    icon: 'mdi-delete-outline',
    color: 'error',
    alertType: 'info',
    navDescription: '移除失效安装记录',
    description: '清理数据库中的失效安装记录和异常运行目录。',
    hint: '只处理已选择的无效记录和运行目录，不会删除插件原有配置。',
    actionDescription: '执行后将从已安装列表移除所选无效记录。',
    selectLabel: '选择要清理的插件',
    buttonLabel: '执行清理',
    buttonIcon: 'mdi-delete-sweep-outline',
  },
  {
    value: 'reinstall',
    title: '重新安装',
    icon: 'mdi-package-down',
    color: 'primary',
    alertType: 'warning',
    navDescription: '恢复插件运行文件',
    description: '从本地插件源或插件市场恢复缺失的运行文件。',
    hint: '优先使用本地插件源，否则尝试插件市场；安装记录和原插件配置会保留。',
    actionDescription: '执行后将重新获取所选插件的运行文件。',
    selectLabel: '选择要重新安装的插件',
    buttonLabel: '开始重装',
    buttonIcon: 'mdi-package-down',
  },
]

const selectedCount = computed(() => config.invalid_plugin_ids.length)
const localSourceCount = computed(() => invalidItems.value.filter(item => item.local_source_path).length)
const onlineSourceCount = computed(() => invalidItems.value.filter(item => item.source_type === 'online').length)
const runtimeExistsCount = computed(() => invalidItems.value.filter(item => item.runtime_exists).length)
const currentTab = computed(() => actionTabs.find(tab => tab.value === config.action_mode) || actionTabs[0])
const jobRunning = computed(() => ['queued', 'running'].includes(lastResult.value?.status))
const jobProgress = computed(() => Math.max(0, Math.min(100, Number(lastResult.value?.progress) || 0)))
const jobCompleted = computed(() => Number(lastResult.value?.completed) || 0)
const jobTotal = computed(() => Number(lastResult.value?.total) || 0)
const jobStatusText = computed(() => {
  if (lastResult.value?.current) {
    return `正在处理：${lastResult.value.current}`
  }
  return lastResult.value?.message || '任务已进入后台队列'
})

let pollTimer = null

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

function applyInitialConfig(value = props.initialConfig) {
  config.invalid_plugin_ids = Array.isArray(value?.invalid_plugin_ids)
    ? [...value.invalid_plugin_ids]
    : []
  config.action_mode = value?.action_mode || 'clean'
}

async function loadInvalidPlugins() {
  loading.value = true
  error.value = ''
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/invalid_plugins')
    const data = unwrap(response)
    invalidItems.value = data.items || []
    lastResult.value = data.last_result || {}
    const validIds = new Set(invalidItems.value.map(item => item.id))
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => validIds.has(id))
    scheduleJobPoll()
  } catch (err) {
    error.value = err?.message || '读取无效插件列表失败'
  } finally {
    loading.value = false
  }
}

function togglePlugin(pluginId) {
  if (config.invalid_plugin_ids.includes(pluginId)) {
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => id !== pluginId)
  } else {
    config.invalid_plugin_ids = [...config.invalid_plugin_ids, pluginId]
  }
}

function selectAll() {
  config.invalid_plugin_ids = invalidItems.value.map(item => item.id)
}

function clearSelection() {
  config.invalid_plugin_ids = []
}

function stopJobPoll() {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

function scheduleJobPoll() {
  if (!jobRunning.value || pollTimer) return
  pollTimer = setTimeout(async () => {
    pollTimer = null
    await pollJobState()
  }, 1000)
}

async function pollJobState() {
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/last_result')
    lastResult.value = unwrap(response) || {}
    if (jobRunning.value) {
      scheduleJobPoll()
      return
    }
    await loadInvalidPlugins()
    emit('action')
  } catch (err) {
    error.value = err?.message || '读取后台任务进度失败'
    scheduleJobPoll()
  }
}

async function runAction() {
  if (!selectedCount.value || submitting.value || jobRunning.value) return

  const payload = {
    invalid_plugin_ids: [...config.invalid_plugin_ids],
    action_mode: config.action_mode,
  }
  submitting.value = true
  error.value = ''
  try {
    if (typeof props.api?.put !== 'function') {
      emit('save', payload)
      return
    }

    const response = await props.api.put('plugin/CleanInvalidPlugin', payload)
    const result = unwrap(response) || {}
    if (result.success === false) {
      throw new Error(result.message || '操作执行失败')
    }

    emit('action')
    if (payload.action_mode === 'reinstall') {
      const statusResponse = await props.api.get('plugin/CleanInvalidPlugin/last_result')
      lastResult.value = unwrap(statusResponse) || {}
      scheduleJobPoll()
    } else {
      await loadInvalidPlugins()
    }
  } catch (err) {
    error.value = err?.message || '操作执行失败'
  } finally {
    submitting.value = false
  }
}

watch(() => props.initialConfig, value => applyInitialConfig(value), { deep: true })
watch(() => config.action_mode, () => emit('layout', layoutRequest))

onMounted(() => {
  applyInitialConfig()
  loadInvalidPlugins()
})

onBeforeUnmount(stopJobPoll)
</script>

<style scoped>
.cip-config { width: min(70rem, 100%); margin: 0 auto; container-type: inline-size; color: rgb(var(--v-theme-on-surface)); letter-spacing: 0; }
.cip-config, .cip-config * { box-sizing: border-box; }
.cip-card { display: flex; flex-direction: column; height: min(90dvh, 820px); overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; }
.cip-header { flex: 0 0 auto; min-height: 72px; padding: 10px 16px; }
.cip-header-title { overflow-wrap: anywhere; font-size: 1.0625rem; font-weight: 700; letter-spacing: 0; line-height: 1.4rem; }
.cip-header-subtitle { margin-top: 2px; overflow-wrap: anywhere; white-space: normal; }
.cip-header-actions { display: flex; align-items: center; gap: 4px; }
.cip-body { display: flex; flex: 1 1 auto; min-height: 0; }
.cip-nav { flex: 0 0 188px; min-width: 0; padding: 6px; border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.cip-nav-item { min-height: 60px; margin: 4px 0; }
.cip-nav-item :deep(.v-list-item-subtitle) { margin-top: 2px; font-size: 0.6875rem; line-height: 1rem; }
.cip-content { display: flex; flex: 1 1 auto; flex-direction: column; min-width: 0; min-height: 0; }
.cip-mobile-tabbar { display: none; }
.cip-workspace { display: flex; flex: 1 1 auto; min-width: 0; min-height: 0; }
.cip-window { flex: 1 1 auto; min-width: 0; min-height: 0; overflow-y: auto; }
.cip-pane { min-width: 0; padding: 18px; }
.cip-pane-heading { display: flex; align-items: center; justify-content: space-between; min-width: 0; margin-bottom: 14px; gap: 12px; }
.cip-pane-title-wrap { display: flex; align-items: center; min-width: 0; gap: 10px; }
.cip-section-title { font-size: 1rem; font-weight: 700; line-height: 1.25rem; }
.cip-section-desc { margin-top: 3px; color: rgba(var(--v-theme-on-surface), .62); font-size: .75rem; line-height: 1.05rem; }
.cip-selection-toolbar { display: flex; align-items: center; flex-wrap: wrap; min-height: 40px; margin-bottom: 6px; gap: 4px; }
.cip-block-title { font-size: .875rem; font-weight: 700; }
.cip-plugin-list { padding: 0; overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; background: transparent; }
.cip-plugin-row { min-height: 58px; border-top: 1px solid rgba(var(--v-border-color), calc(var(--v-border-opacity) * .72)); cursor: pointer; }
.cip-plugin-row:first-child { border-top: 0; }
.cip-progress-panel { padding: 14px 16px; margin-bottom: 16px; border: 1px solid rgba(var(--v-theme-primary), .24); border-radius: 8px; background: rgba(var(--v-theme-primary), .055); }
.cip-progress-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.cip-progress-title { display: flex; align-items: flex-start; min-width: 0; gap: 9px; }
.cip-progress-title > div { display: flex; min-width: 0; flex-direction: column; }
.cip-progress-title strong { font-size: .875rem; }
.cip-progress-title span { margin-top: 2px; overflow-wrap: anywhere; color: rgba(var(--v-theme-on-surface), .62); font-size: .75rem; }
.cip-progress-percent { flex: 0 0 auto; color: rgb(var(--v-theme-primary)); font-size: 1rem; }
.cip-progress-metrics { display: flex; align-items: center; flex-wrap: wrap; color: rgba(var(--v-theme-on-surface), .7); font-size: .75rem; gap: 8px 16px; }
.cip-progress-note { margin-top: 9px; color: rgba(var(--v-theme-on-surface), .56); font-size: .6875rem; line-height: 1rem; }
.cip-empty { display: flex; min-height: 220px; align-items: center; justify-content: center; flex-direction: column; color: rgba(var(--v-theme-on-surface), .62); text-align: center; gap: 8px; }
.cip-empty strong { color: rgb(var(--v-theme-on-surface)); font-size: .9375rem; }
.cip-empty span { font-size: .75rem; }
.cip-action-dock { display: flex; position: sticky; bottom: -18px; align-items: center; justify-content: space-between; min-height: 66px; padding: 10px 12px; margin: 18px -18px -18px; border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); background: rgba(var(--v-theme-surface), .96); gap: 14px; }
.cip-action-copy { display: flex; min-width: 0; flex-direction: column; }
.cip-action-copy strong { font-size: .8125rem; }
.cip-action-copy span { margin-top: 2px; color: rgba(var(--v-theme-on-surface), .58); font-size: .6875rem; line-height: 1rem; }
.cip-dashboard { flex: 0 0 244px; min-width: 0; padding: 18px 16px; overflow-y: auto; border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); background: rgba(var(--v-theme-on-surface), .015); }
.cip-dashboard-title { display: flex; align-items: center; margin-bottom: 8px; font-size: .875rem; font-weight: 700; gap: 8px; }
.cip-dashboard-row { display: grid; min-height: 38px; align-items: center; color: rgba(var(--v-theme-on-surface), .68); font-size: .8125rem; gap: 8px; grid-template-columns: 24px minmax(0, 1fr) auto; }
.cip-dashboard-row strong { color: rgb(var(--v-theme-on-surface)); text-align: right; }
.cip-dashboard-note { margin: 0; color: rgba(var(--v-theme-on-surface), .65); font-size: .75rem; line-height: 1.15rem; }

@container (width < 880px) {
  .cip-dashboard { display: none; }
}

@media (max-width: 640px) {
  .cip-config { width: 100%; height: 100dvh; max-height: 100dvh; }
  .cip-card { height: 100dvh; max-height: 100dvh; border: 0; border-radius: 0; }
  .cip-header { min-height: 64px; padding: 8px 10px; }
  .cip-header :deep(.v-avatar) { width: 36px !important; height: 36px !important; }
  .cip-header-title { font-size: .9375rem; }
  .cip-header-subtitle { display: none; }
  .cip-job-chip { display: none; }
  .cip-nav { display: none; }
  .cip-content { width: 100%; }
  .cip-mobile-tabbar { display: flex; align-items: center; padding: 10px 12px; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); gap: 10px; }
  .cip-mobile-tabinfo { flex: 1 1 auto; min-width: 0; }
  .cip-pane { padding: 12px; }
  .cip-pane-heading { align-items: flex-start; }
  .cip-progress-panel { padding: 12px; }
  .cip-pane-title-wrap > :deep(.v-avatar) { display: none; }
  .cip-action-dock { bottom: -12px; align-items: stretch; flex-direction: column; margin: 14px -12px -12px; padding: 10px 12px calc(10px + env(safe-area-inset-bottom)); }
  .cip-action-dock :deep(.v-btn) { width: 100%; min-height: 40px; }
  .cip-plugin-row :deep(.v-list-item__append) { align-self: flex-start; padding-top: 8px; }
}
</style>
