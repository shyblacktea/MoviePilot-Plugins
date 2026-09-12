<template>
  <div class="notify-root">
    <VCard flat class="notify-card">
      <VCardItem class="notify-header">
        <template #prepend>
          <VAvatar color="primary" variant="tonal" rounded="lg" size="44">
            <VIcon icon="mdi-bell-cog-outline" size="25" />
          </VAvatar>
        </template>
        <VCardTitle class="text-h6 notify-title">我就想通知到群组！</VCardTitle>
        <VCardSubtitle class="text-caption">系统通知目标与订阅用户通知映射</VCardSubtitle>
        <template #append>
          <div class="d-flex align-center ga-2">
            <VChip v-if="dirty" color="warning" size="small" variant="tonal">有修改未保存</VChip>
            <VBtn color="primary" variant="flat" size="small" prepend-icon="mdi-content-save" :loading="saving" :disabled="!dirty" @click="save">保存修改</VBtn>
            <VBtn icon="mdi-refresh" variant="text" size="small" :loading="loading" @click="load" />
            <VBtn icon="mdi-close" variant="text" size="small" aria-label="关闭" title="关闭" @click="emit('close')" />
          </div>
        </template>
      </VCardItem>
      <VDivider />

      <VAlert v-if="error" type="error" variant="tonal" density="compact" class="ma-4 mb-0 text-caption" closable @click:close="error = ''">{{ error }}</VAlert>
      <VAlert v-if="hint" type="success" variant="tonal" density="compact" class="ma-4 mb-0 text-caption" closable @click:close="hint = ''">{{ hint }}</VAlert>

      <div class="notify-body">
        <main class="notify-content">
          <section class="config-section">
            <div class="section-title">1. 系统通知目标（资源入库 / 资源下载 / 添加订阅/订阅完成）</div>
            <div class="section-hint">控制 MoviePilot 对应类型系统通知的投递目标；“发群组”按各通知渠道的群组配置发送。</div>
            <div class="field-list">
              <div v-for="row in actionRows" :key="row.key" class="field-row">
                <div class="field-info">
                  <div class="field-label">{{ row.label }}</div>
                  <div class="field-hint">{{ row.hint }}</div>
                </div>
                <VSelect
                  v-model="actions[row.key]"
                  :items="actionOptions"
                  item-title="title"
                  item-value="value"
                  label="通知目标"
                  density="compact"
                  variant="outlined"
                  hide-details
                  rounded="lg"
                  class="field-control"
                />
              </div>
            </div>
          </section>

          <section class="config-section">
            <div class="section-title">2. 订阅用户通知映射</div>
            <div class="section-hint">未单独配置的订阅用户使用默认目标。每个用户可以同时选择多个群组、用户或管理员目标。</div>
            <div class="field-row default-row">
              <div class="field-info">
                <div class="field-label">未单独配置的订阅用户默认目标</div>
                <div class="field-hint">留空时回退到通知渠道的默认群组。</div>
              </div>
              <VSelect
                v-model="defaultTargets"
                :items="targetOptions"
                item-title="title"
                item-value="value"
                label="默认通知目标"
                placeholder="默认：群组"
                density="compact"
                variant="outlined"
                hide-details
                rounded="lg"
                multiple
                chips
                closable-chips
                clearable
                class="field-control"
                no-data-text="无可用通知目标"
              />
            </div>
            <div v-if="!rows.length" class="empty-state">
              <VIcon icon="mdi-account-multiple-outline" size="30" color="primary" />
              <div class="text-body-2 mt-2">暂无单独配置的订阅用户</div>
              <div class="text-caption text-medium-emphasis">点击“添加映射”后，为订阅归属用户选择通知目标。</div>
            </div>
            <div v-for="(row, index) in rows" :key="row.uid" class="field-row mapping-row">
              <VSelect v-model="row.username" :items="availableUsers(row.username)" label="用户订阅" placeholder="选择订阅归属用户" density="compact" variant="outlined" hide-details rounded="lg" clearable class="user-control" no-data-text="无可用订阅用户" />
              <VSelect v-model="row.targets" :items="targetOptions" item-title="title" item-value="value" label="通知目标" placeholder="选择一个或多个目标" density="compact" variant="outlined" hide-details rounded="lg" multiple chips closable-chips clearable class="target-control" no-data-text="无可用通知目标" />
              <VBtn icon="mdi-delete-outline" color="error" variant="text" size="small" @click="removeRow(index)" />
            </div>
            <div class="section-actions">
              <VBtn color="primary" variant="tonal" size="small" prepend-icon="mdi-plus" :disabled="!availableUsers('').length" @click="addRow">添加映射</VBtn>
              <span v-if="!availableUsers('').length && usernames.length" class="text-caption text-medium-emphasis">所有订阅用户均已配置</span>
            </div>
          </section>
        </main>
      </div>
    </VCard>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close'])

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const hint = ref('')
const usernames = ref([])
const targetOptions = ref([])
const actionOptions = ref([])
const actions = reactive({ download_action: 'all', organize_action: 'all', subscribe_action: 'all' })
const defaultTargets = ref([])
const rows = ref([])
const savedSnapshot = ref('')
let rowUid = 0

const actionRows = [
  { key: 'organize_action', label: '资源入库', hint: '整理完成并写入媒体库时的通知。' },
  { key: 'download_action', label: '资源下载', hint: '添加下载任务成功时的通知。' },
  { key: 'subscribe_action', label: '添加订阅 / 订阅完成', hint: '添加订阅成功和订阅完成时的通知。' },
]

function unwrap(response) {
  const body = response?.data ?? response ?? {}
  return body?.data ?? body
}

function normalizedTargets(value) {
  const list = Array.isArray(value) ? value : String(value || '').split(',')
  return [...new Set(list.map(item => String(item || '').trim()).filter(Boolean))]
}

function snapshot() {
  savedSnapshot.value = JSON.stringify({
    actions: { ...actions },
    defaultTargets: [...defaultTargets.value].sort(),
    rows: rows.value
      .filter(row => String(row.username || '').trim())
      .map(row => ({ username: String(row.username).trim(), targets: normalizedTargets(row.targets).sort() }))
      .sort((a, b) => a.username.localeCompare(b.username)),
  })
}

const dirty = computed(() => {
  const current = {
    actions: { ...actions },
    defaultTargets: [...defaultTargets.value].sort(),
    rows: rows.value
      .filter(row => String(row.username || '').trim())
      .map(row => ({ username: String(row.username).trim(), targets: normalizedTargets(row.targets).sort() }))
      .sort((a, b) => a.username.localeCompare(b.username)),
  }
  return JSON.stringify(current) !== savedSnapshot.value
})

function availableUsers(current) {
  const used = new Set(rows.value.map(row => String(row.username || '').trim()).filter(name => name && name !== current))
  return usernames.value.filter(name => !used.has(name))
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = unwrap(await props.api.get('plugin/NotifyToGroupShy/options')) || {}
    const nextActions = data.actions || {}
    for (const key of Object.keys(actions)) actions[key] = String(nextActions[key] || 'all')
    actionOptions.value = Array.isArray(data.options) && data.options.length ? data.options : [
      { title: '发群组', value: 'all' },
      { title: '用户+管理员', value: 'user,admin' },
      { title: '仅用户', value: 'user' },
      { title: '仅管理员', value: 'admin' },
    ]
    usernames.value = Array.isArray(data.usernames) ? data.usernames.map(String) : []
    targetOptions.value = (Array.isArray(data.targets) ? data.targets : []).map(item => ({
      title: item.title || String(item.id),
      value: String(item.id),
    }))
    const rules = data.rules && typeof data.rules === 'object' ? data.rules : {}
      rows.value = Object.entries(rules).map(([username, targets]) => ({
      uid: `row-${++rowUid}`,
      username,
      targets: normalizedTargets(targets),
    }))
    defaultTargets.value = normalizedTargets(data.default_target)
    snapshot()
  } catch (err) {
    error.value = err?.message || '读取通知目标配置失败'
  } finally {
    loading.value = false
  }
}

function addRow() {
  rows.value.push({ uid: `row-${++rowUid}`, username: availableUsers('').at(0) || '', targets: [] })
}

function removeRow(index) {
  rows.value.splice(index, 1)
}

async function save() {
  const rules = {}
  for (const row of rows.value) {
    const username = String(row.username || '').trim()
    const targets = normalizedTargets(row.targets)
    if (username && targets.length) rules[username] = targets.join(',')
  }
  saving.value = true
  error.value = ''
  hint.value = ''
  try {
    const result = unwrap(await props.api.post('plugin/NotifyToGroupShy/save', {
      actions: { ...actions },
      rules,
      default_target: normalizedTargets(defaultTargets.value).join(','),
    })) || {}
    if (result.success === false) {
      error.value = result.message || '保存失败'
      return
    }
    await load()
    hint.value = result.message || '通知目标配置已保存'
  } catch (err) {
    error.value = err?.message || '保存通知目标配置失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.notify-root { width: min(1180px, calc(100vw - 32px)); max-width: 100%; margin: 0 auto; padding: 8px; }
.notify-card { overflow: hidden; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 14px; }
.notify-header { padding: 16px 20px; }
.notify-title { font-weight: 700; }
.notify-body { display: flex; min-height: 620px; }
.notify-content { flex: 1 1 auto; min-width: 0; padding: 22px 24px; background: rgba(var(--v-theme-on-surface), .008); }
.section-hint, .field-hint { color: rgba(var(--v-theme-on-surface), .6); font-size: 12px; line-height: 1.6; }
.config-section { padding: 16px 18px 10px; margin-bottom: 16px; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 10px; background: rgba(var(--v-theme-on-surface), .015); }
.section-title { margin-bottom: 4px; color: rgb(var(--v-theme-primary)); font-size: 14px; font-weight: 700; }
.field-list { display: flex; flex-direction: column; margin-top: 10px; }
.field-row { display: flex; align-items: center; gap: 18px; padding: 13px 2px; border-bottom: 1px solid rgba(var(--v-border-color), .45); }
.field-row:last-child { border-bottom: none; }
.field-info { flex: 1 1 auto; min-width: 0; }
.field-label { margin-bottom: 2px; font-size: 13px; font-weight: 600; }
.field-control { width: min(390px, 42%); flex: 0 0 min(390px, 42%); }
.default-row { margin-top: 8px; }
.mapping-row { align-items: flex-start; }
.user-control { min-width: 180px; flex: 0 0 28%; }
.target-control { min-width: 240px; flex: 1 1 auto; }
.section-actions { display: flex; align-items: center; gap: 12px; padding-top: 12px; }
.empty-state { padding: 24px 12px 18px; text-align: center; }
@media (max-width: 760px) {
  .notify-root { width: 100%; padding: 0; }
  .notify-card { border-radius: 0; border: none; }
  .notify-header { padding: 10px 12px; }
  .notify-header :deep(.v-card-title) { font-size: 15px !important; }
  .notify-header :deep(.v-card-subtitle) { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .notify-body { min-height: 0; }
  .notify-content { padding: 14px 12px; }
  .field-row, .mapping-row { flex-direction: column; align-items: stretch; gap: 8px; }
  .field-control, .user-control, .target-control { width: 100%; min-width: 0; flex-basis: auto; }
}
</style>
