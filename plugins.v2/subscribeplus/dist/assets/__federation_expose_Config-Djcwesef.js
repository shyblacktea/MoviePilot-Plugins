import { importShared } from './__federation_fn_import-JrT3xvdd.js';

/**
 * SubscribePlus 配置字段元数据。
 *
 * 每个字段声明渲染类型与归属 tab，Config.vue 据此自动渲染表单，
 * 新增配置项只需在此追加声明，无需改模板。
 */

/** tab 分组定义：key 与 Config.vue 的导航一一对应 */
const groups = [
  { key: 'overview', title: '运行概览', icon: 'mdi-view-dashboard-outline', desc: '扫描状态、待处理诊断与快捷操作。' },
  { key: 'identifier', title: '识别词工具', icon: 'mdi-tag-plus-outline', desc: '自动/手动写入自定义识别词。' },
  { key: 'rules', title: '规则记录', icon: 'mdi-history', desc: '订阅规则修改历史。' },
  { key: 'scan', title: '扫描设置', icon: 'mdi-tune-variant', desc: '订阅扫描周期、宽限天数与站点范围。' },
  { key: 'notify', title: '通知权限', icon: 'mdi-message-badge-outline', desc: 'Telegram 通知与规则修改授权。' },
  { key: 'cleanup', title: '清理与候选', icon: 'mdi-broom', desc: '整季包清理策略与候选缓存。' },
];

/**
 * 配置字段声明。
 * type: switch | number | text | select | multiselect
 * group: 归属 tab；section: tab 内小节标题
 * 其余属性透传给对应 Vuetify 组件。
 */
const fields = [
  // ---- 扫描设置 ----
  {
    key: 'delay_days', group: 'scan', section: '扫描窗口', type: 'number',
    label: '宽限天数', min: 0, cols: { md: 4 },
    hint: '单集播出超过 N 天仍未入库才触发诊断',
  },
  {
    key: 'cron', group: 'scan', section: '扫描窗口', type: 'text',
    label: 'Cron', cols: { md: 4 },
    hint: '每 6 小时建议写 0 */6 * * *', validate: 'cron',
  },
  {
    key: 'max_scan_subscribes', group: 'scan', section: '扫描窗口', type: 'number',
    label: '订阅部数通知上限', min: 1, cols: { md: 4 },
  },
  {
    key: 'selected_categories', group: 'scan', section: '扫描范围', type: 'multiselect',
    label: '二级分类', optionsKey: 'categories', cols: { md: 6 },
  },
  {
    key: 'search_sites', group: 'scan', section: '扫描范围', type: 'multiselect',
    label: 'PT搜索范围', optionsKey: 'sites', clearable: true, cols: { md: 6 },
  },

  // ---- 通知权限 ----
  {
    key: 'notify_tg', group: 'notify', section: '通知渠道', type: 'switch',
    label: 'Telegram 独立通知', color: 'primary', cols: { md: 6 },
  },
  {
    key: 'allow_tg_rule_update', group: 'notify', section: '授权', type: 'switch',
    label: '允许 TG 修改订阅规则', color: 'warning', cols: { md: 6 },
    alert: '开启后可通过 Telegram 交互直接调整订阅过滤规则，请谨慎授权。',
  },

  // ---- 清理与候选 ----
  {
    key: 'season_pack_cleanup', group: 'cleanup', section: '全集包清理', type: 'select',
    label: '最终集整季包清理', cols: { md: 6 },
    options: [
      { title: '关闭', value: 'off' },
      { title: '仅删转移记录', value: 'record' },
      { title: '删转移记录+源文件', value: 'source' },
    ],
    alert: '当整季包下载到最终集时，可按策略清理旧的分集转移记录或源文件，避免媒体库重复。',
  },
  {
    key: 'season_pack_full_download', group: 'cleanup', section: '全集包清理', type: 'switch',
    label: 'qB 整季包全选下载', color: 'warning', cols: { md: 6 },
  },
  {
    key: 'candidate_cache_days', group: 'cleanup', section: '候选下载', type: 'number',
    label: '候选缓存天数', min: 0, cols: { md: 6 },
    hint: '候选下载信息本地缓存有效期，0 关闭；重载/重启后仍可直接下载候选',
  },
];

/** 配置默认值（与后端 PluginConfig 对齐） */
const defaults = {
  enabled: false,
  delay_days: 1,
  cron: '0 9 * * *',
  selected_categories: [],
  search_sites: [],
  max_scan_subscribes: 20,
  notify_tg: true,
  allow_tg_rule_update: false,
  season_pack_cleanup: 'off',
  season_pack_full_download: false,
  candidate_cache_days: 3,
};

/**
 * 校验 Cron 表达式（5 段）。
 * @param {string} value Cron 字符串
 * @returns {string} 错误信息，合法返回空串
 */
function validateCron(value) {
  const parts = String(value || '').trim().split(/\s+/);
  if (parts.length !== 5) return 'Cron 需要 5 段，例如 0 */6 * * *'
  const ranges = [59, 23, 31, 12, 7];
  const invalid = parts.find((part, index) => {
    const match = part.match(/^\*\/(\d+)$/);
    return match && Number(match[1]) > ranges[index]
  });
  if (invalid) return `${invalid} 超出该 Cron 字段范围`
  return ''
}

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,unref:_unref,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,createSlots:_createSlots,createBlock:_createBlock,createElementVNode:_createElementVNode,createCommentVNode:_createCommentVNode,vShow:_vShow,withDirectives:_withDirectives} = await importShared('vue');


const _hoisted_1 = { class: "sp-config" };
const _hoisted_2 = { class: "sp-body" };
const _hoisted_3 = { class: "sp-nav" };
const _hoisted_4 = { class: "sp-content" };
const _hoisted_5 = { class: "sp-window" };
const _hoisted_6 = { class: "sp-pane" };
const _hoisted_7 = { class: "d-flex align-center flex-wrap ga-1 mb-3" };
const _hoisted_8 = { class: "sp-stat-grid mb-4" };
const _hoisted_9 = { class: "sp-stat" };
const _hoisted_10 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_11 = { class: "text-subtitle-2 font-weight-bold sp-stat-value" };
const _hoisted_12 = { class: "sp-stat" };
const _hoisted_13 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_14 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_15 = { class: "sp-stat" };
const _hoisted_16 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_17 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_18 = { class: "sp-stat" };
const _hoisted_19 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_20 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_21 = { class: "mb-2" };
const _hoisted_22 = { class: "text-caption text-medium-emphasis mb-2" };
const _hoisted_23 = {
  key: 0,
  class: "sp-candidate-wrap mt-2"
};
const _hoisted_24 = { class: "sp-cand-site" };
const _hoisted_25 = { class: "sp-cand-title" };
const _hoisted_26 = { class: "sp-cand-seed" };
const _hoisted_27 = { class: "text-right sp-cand-act" };
const _hoisted_28 = {
  key: 1,
  class: "sp-empty"
};
const _hoisted_29 = { class: "sp-pane" };
const _hoisted_30 = { class: "d-flex align-center mb-3" };
const _hoisted_31 = {
  key: 3,
  class: "sp-empty"
};
const _hoisted_32 = { class: "sp-pane" };
const _hoisted_33 = { class: "d-flex align-center mb-3" };
const _hoisted_34 = {
  key: 1,
  class: "sp-empty"
};
const _hoisted_35 = { class: "sp-section-title" };
const _hoisted_36 = { class: "sp-actions d-flex align-center flex-wrap ga-1" };
const _hoisted_37 = {
  key: 1,
  class: "sp-suggestion"
};
const _hoisted_38 = {
  key: 2,
  class: "sp-preview-box"
};
const _hoisted_39 = { key: 0 };

const {computed,onMounted,reactive,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
},
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

// ===== 通用状态 =====
const activeGroup = ref('overview');
const error = ref('');
const loading = ref(false);
const cronError = ref('');

// ===== 配置（元数据驱动）=====
const config = reactive({ ...defaults });

// ===== 概览数据 =====
const status = ref({});
const items = ref([]);
const ruleRecords = ref([]);
const identifierRecords = ref([]);
const scanning = ref(false);
const clearing = ref(false);
const clearingRules = ref(false);
const deletingRuleId = ref('');
const deletingResultId = ref('');

// ===== 识别词 =====
const identifierAutoTitle = ref('');
const identifierManualTitle = ref('');
const identifierManualType = ref('tv');
const identifierManualTmdbid = ref('');
const identifierBusy = ref('');
const identifierError = ref('');
const identifierMessage = ref('');
const mediaTypeOptions = [
  { title: 'TV', value: 'tv' },
  { title: 'Movie', value: 'movie' },
];

// ===== 规则预览对话框 =====
const previewDialog = ref(false);
const preview = ref(null);
const previewError = ref('');
const previewContext = ref(null);
const previewLoading = ref('');
const ruleSuggestions = ref([]);

// ===== 选项 =====
const categories = ref([]);
const siteOptions = ref([]);

const currentGroup = computed(() => groups.find(g => g.key === activeGroup.value) || groups[0]);
const configGroupKeys = ['scan', 'notify', 'cleanup'];

const reasonCount = computed(() => items.value.reduce((acc, item) => {
  acc[item.reason] = (acc[item.reason] || 0) + 1;
  return acc
}, {}));

/**
 * 按元数据取某 tab 下的小节列表（含各自字段）。
 */
function sectionsOf(groupKey) {
  const result = [];
  for (const field of fields) {
    if (field.group !== groupKey) continue
    let section = result.find(s => s.title === field.section);
    if (!section) {
      section = { title: field.section, fields: [] };
      result.push(section);
    }
    section.fields.push(field);
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
  const body = response?.data ?? response ?? {};
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
  const arr = Array.isArray(value) ? value : [];
  const text = arr.filter(item => item !== undefined && item !== null && String(item).trim()).map(String).join(', ');
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

function applyInitialConfig() {
  Object.assign(config, {
    ...config,
    ...props.initialConfig,
    selected_categories: Array.isArray(props.initialConfig.selected_categories)
      ? [...props.initialConfig.selected_categories]
      : [],
    search_sites: Array.isArray(props.initialConfig.search_sites)
      ? [...props.initialConfig.search_sites]
      : [],
    season_pack_cleanup: props.initialConfig.season_pack_cleanup || 'off',
    season_pack_full_download: Boolean(props.initialConfig.season_pack_full_download),
    candidate_cache_days:
      props.initialConfig.candidate_cache_days === undefined || props.initialConfig.candidate_cache_days === null
        ? 3
        : Number(props.initialConfig.candidate_cache_days),
  });
}

async function loadOptions() {
  try {
    const [categoryResponse, siteResponse] = await Promise.all([
      props.api.get('plugin/SubscribePlus/categories'),
      props.api.get('plugin/SubscribePlus/sites'),
    ]);
    categories.value = unwrap(categoryResponse).items || [];
    siteOptions.value = (unwrap(siteResponse).items || []).map(item => ({
      title: item.name || item.title || item.id || item.value,
      value: String(item.id ?? item.value ?? ''),
    })).filter(item => item.value);
    const staleUncategorizedOnly =
      config.selected_categories.length === 1 &&
      config.selected_categories[0] === '未分类' &&
      categories.value.some(item => item.value !== '未分类');
    if (!config.selected_categories.length || staleUncategorizedOnly) {
      config.selected_categories = categories.value.map(item => item.value);
    }
  } catch (err) {
    error.value = err?.message || '读取配置选项失败';
  }
}

async function loadData() {
  loading.value = true;
  error.value = '';
  try {
    const [statusResponse, resultsResponse] = await Promise.all([
      props.api.get('plugin/SubscribePlus/status'),
      props.api.get('plugin/SubscribePlus/results'),
    ]);
    status.value = unwrap(statusResponse);
    const data = unwrap(resultsResponse);
    items.value = data.items || [];
    ruleRecords.value = data.rule_records || status.value.rule_records || [];
    identifierRecords.value = data.identifier_records || status.value.identifier_records || [];
  } catch (err) {
    error.value = err?.message || '读取诊断结果失败';
  } finally {
    loading.value = false;
  }
}

async function reloadAll() {
  await Promise.all([loadData(), loadOptions()]);
}

async function runScan() {
  scanning.value = true;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/scan', {});
    await loadData();
  } catch (err) {
    error.value = err?.message || '手动扫描失败';
  } finally {
    scanning.value = false;
  }
}

async function clearResults() {
  clearing.value = true;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/results/clear', {});
    await loadData();
  } catch (err) {
    error.value = err?.message || '清除诊断结果失败';
  } finally {
    clearing.value = false;
  }
}

async function deleteResult(item) {
  if (!item?.result_id) {
    error.value = '该诊断结果缺少标识，无法删除，请先刷新';
    return
  }
  deletingResultId.value = item.result_id;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/results/delete', { result_id: item.result_id });
    await loadData();
  } catch (err) {
    error.value = err?.message || '删除诊断结果失败';
  } finally {
    deletingResultId.value = '';
  }
}

async function clearRuleRecords() {
  clearingRules.value = true;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/rule_records/clear', {});
    await loadData();
  } catch (err) {
    error.value = err?.message || '清空规则修改记录失败';
  } finally {
    clearingRules.value = false;
  }
}

async function deleteRuleRecord(record) {
  if (!record?.record_id) {
    error.value = '该规则记录缺少标识，无法删除，请先刷新';
    return
  }
  deletingRuleId.value = record.record_id;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/rule_records/delete', { record_id: record.record_id });
    await loadData();
  } catch (err) {
    error.value = err?.message || '删除规则记录失败';
  } finally {
    deletingRuleId.value = '';
  }
}

function readActionResponse(response, fallback) {
  const body = response?.data ?? response ?? {};
  const data = body?.data ?? body;
  if (body.success === false || data.success === false) {
    return { success: false, message: body.message || data.message || fallback }
  }
  return { success: true, message: body.message || data.message || fallback }
}

async function runIdentifierAuto() {
  const title = identifierAutoTitle.value.trim();
  identifierError.value = '';
  identifierMessage.value = '';
  if (!title) {
    identifierError.value = '请填写媒体文件名';
    return
  }
  identifierBusy.value = 'auto';
  try {
    const response = await props.api.post('plugin/SubscribePlus/identifier_auto', { title });
    const result = readActionResponse(response, '已提交自动处理');
    if (!result.success) {
      identifierError.value = result.message;
      return
    }
    identifierMessage.value = result.message;
    await loadData();
  } catch (err) {
    identifierError.value = err?.message || '自动处理失败';
  } finally {
    identifierBusy.value = '';
  }
}

async function runIdentifierManual() {
  const title = identifierManualTitle.value.trim();
  const tmdbid = identifierManualTmdbid.value.trim();
  identifierError.value = '';
  identifierMessage.value = '';
  if (!title || !tmdbid) {
    identifierError.value = '请填写媒体文件名和 TMDB ID';
    return
  }
  identifierBusy.value = 'manual';
  try {
    const response = await props.api.post('plugin/SubscribePlus/identifier_manual', {
      title,
      media_type: identifierManualType.value,
      tmdbid,
    });
    const result = readActionResponse(response, '已提交手动处理');
    if (!result.success) {
      identifierError.value = result.message;
      return
    }
    identifierMessage.value = result.message;
    await loadData();
  } catch (err) {
    identifierError.value = err?.message || '手动处理失败';
  } finally {
    identifierBusy.value = '';
  }
}

async function previewRule(item, candidate) {
  previewDialog.value = true;
  preview.value = null;
  previewError.value = '';
  previewContext.value = { item, candidate };
  previewLoading.value = '';
  ruleSuggestions.value = [];
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_suggestions', {
      diagnosis: item,
      candidate,
    });
    const body = response?.data ?? response ?? {};
    const data = body?.data ?? body;
    if (body.success === false || data.success === false) {
      previewError.value = body.message || data.message || '生成规则建议失败';
      return
    }
    ruleSuggestions.value = data.items || [];
    if (!ruleSuggestions.value.length) {
      previewError.value = '没有可添加的官组、平台或 PT 站点建议';
    } else if (ruleSuggestions.value.length === 1) {
      await previewRuleSuggestion(ruleSuggestions.value[0]);
    }
  } catch (err) {
    previewError.value = err?.message || '生成规则建议失败';
  }
}

async function previewRuleSuggestion(suggestion) {
  if (!previewContext.value?.item || !suggestion?.pattern) return
  preview.value = null;
  previewError.value = '';
  previewLoading.value = suggestion.pattern;
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_preview', {
      subscribe_id: previewContext.value.item.subscribe_id,
      pattern: suggestion.pattern,
      selected_text: suggestion.text,
    });
    const body = response?.data ?? response ?? {};
    const data = body?.data ?? body;
    if (body.success === false || data.success === false) {
      previewError.value = body.message || data.message || '生成预览失败';
      return
    }
    preview.value = data;
  } catch (err) {
    previewError.value = err?.message || '生成预览失败';
  } finally {
    previewLoading.value = '';
  }
}

async function confirmRule() {
  if (!preview.value?.token) return
  try {
    await props.api.post('plugin/SubscribePlus/rule_confirm', { token: preview.value.token });
    previewDialog.value = false;
    await loadData();
  } catch (err) {
    previewError.value = err?.message || '确认修改失败';
  }
}

function saveConfig() {
  cronError.value = validateCron(config.cron);
  if (cronError.value) {
    activeGroup.value = 'scan';
    return
  }
  emit('save', {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    candidate_cache_days: Number(config.candidate_cache_days),
    search_sites: Array.isArray(config.search_sites) ? [...config.search_sites] : [],
    selected_categories: Array.isArray(config.selected_categories) ? [...config.selected_categories] : [],
  });
}

onMounted(() => {
  applyInitialConfig();
  reloadAll();
});

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VListItemTitle = _resolveComponent("VListItemTitle");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VListItem = _resolveComponent("VListItem");
  const _component_VList = _resolveComponent("VList");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VTable = _resolveComponent("VTable");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VCardActions = _resolveComponent("VCardActions");
  const _component_VDialog = _resolveComponent("VDialog");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VCard, {
      flat: "",
      class: "sp-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardItem, { class: "sp-header" }, {
          prepend: _withCtx(() => [
            _createVNode(_component_VAvatar, {
              color: "primary",
              variant: "tonal",
              size: "44",
              rounded: "lg",
              class: "sp-header-avatar"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-playlist-star",
                  size: "24"
                })
              ]),
              _: 1
            })
          ]),
          append: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.enabled,
              "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((config.enabled) = $event)),
              color: "success",
              "hide-details": "",
              inset: "",
              class: "sp-enable-switch",
              label: config.enabled ? '已启用' : '已停用'
            }, null, 8, ["modelValue", "label"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-h6 sp-header-title" }, {
              default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                _createTextVNode("订阅下载增强", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption sp-header-subtitle" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(currentGroup.value.desc), 1)
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VDivider),
        _createElementVNode("div", _hoisted_2, [
          _createElementVNode("nav", _hoisted_3, [
            _createVNode(_component_VList, {
              density: "comfortable",
              nav: "",
              class: "py-2 sp-nav-list"
            }, {
              default: _withCtx(() => [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_unref(groups), (item) => {
                  return (_openBlock(), _createBlock(_component_VListItem, {
                    key: item.key,
                    active: activeGroup.value === item.key,
                    color: "primary",
                    rounded: "lg",
                    class: "sp-nav-item",
                    onClick: $event => (activeGroup.value = item.key)
                  }, _createSlots({
                    prepend: _withCtx(() => [
                      _createVNode(_component_VIcon, {
                        icon: item.icon,
                        class: "sp-nav-icon"
                      }, null, 8, ["icon"])
                    ]),
                    default: _withCtx(() => [
                      _createVNode(_component_VListItemTitle, { class: "sp-nav-title" }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(item.title), 1)
                        ]),
                        _: 2
                      }, 1024)
                    ]),
                    _: 2
                  }, [
                    (item.key === 'overview' && items.value.length)
                      ? {
                          name: "append",
                          fn: _withCtx(() => [
                            _createVNode(_component_VChip, {
                              size: "x-small",
                              color: "warning",
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(items.value.length), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          key: "0"
                        }
                      : undefined
                  ]), 1032, ["active", "onClick"]))
                }), 128))
              ]),
              _: 1
            })
          ]),
          _createElementVNode("section", _hoisted_4, [
            (error.value)
              ? (_openBlock(), _createBlock(_component_VAlert, {
                  key: 0,
                  type: "error",
                  variant: "tonal",
                  density: "compact",
                  class: "ma-3 mb-0 text-caption",
                  closable: "",
                  "onClick:close": _cache[1] || (_cache[1] = $event => (error.value = ''))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createElementVNode("div", _hoisted_5, [
              _withDirectives(_createElementVNode("div", _hoisted_6, [
                _createElementVNode("div", _hoisted_7, [
                  _cache[14] || (_cache[14] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "运行概览", -1)),
                  _createVNode(_component_VSpacer),
                  _createVNode(_component_VBtn, {
                    color: "primary",
                    "prepend-icon": "mdi-radar",
                    variant: "tonal",
                    size: "small",
                    loading: scanning.value,
                    onClick: runScan
                  }, {
                    default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                      _createTextVNode("手动扫描", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"]),
                  _createVNode(_component_VBtn, {
                    color: "warning",
                    "prepend-icon": "mdi-delete-sweep-outline",
                    variant: "text",
                    size: "small",
                    loading: clearing.value,
                    onClick: clearResults
                  }, {
                    default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                      _createTextVNode("清除诊断", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"]),
                  _createVNode(_component_VBtn, {
                    icon: "mdi-refresh",
                    variant: "text",
                    size: "small",
                    loading: loading.value,
                    onClick: loadData
                  }, null, 8, ["loading"])
                ]),
                _createElementVNode("div", _hoisted_8, [
                  _createElementVNode("div", _hoisted_9, [
                    _createElementVNode("div", _hoisted_10, [
                      _createVNode(_component_VAvatar, {
                        color: "primary",
                        variant: "tonal",
                        size: "28",
                        rounded: "lg"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VIcon, {
                            icon: "mdi-calendar-clock",
                            size: "17"
                          })
                        ]),
                        _: 1
                      }),
                      _cache[15] || (_cache[15] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "最近扫描", -1))
                    ]),
                    _createElementVNode("div", _hoisted_11, _toDisplayString(status.value.last_scan || '-'), 1)
                  ]),
                  _createElementVNode("div", _hoisted_12, [
                    _createElementVNode("div", _hoisted_13, [
                      _createVNode(_component_VAvatar, {
                        color: "warning",
                        variant: "tonal",
                        size: "28",
                        rounded: "lg"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VIcon, {
                            icon: "mdi-alert-decagram-outline",
                            size: "17"
                          })
                        ]),
                        _: 1
                      }),
                      _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "待处理", -1))
                    ]),
                    _createElementVNode("div", _hoisted_14, _toDisplayString(items.value.length), 1)
                  ]),
                  _createElementVNode("div", _hoisted_15, [
                    _createElementVNode("div", _hoisted_16, [
                      _createVNode(_component_VAvatar, {
                        color: "success",
                        variant: "tonal",
                        size: "28",
                        rounded: "lg"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VIcon, {
                            icon: "mdi-download-circle-outline",
                            size: "17"
                          })
                        ]),
                        _: 1
                      }),
                      _cache[17] || (_cache[17] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "可下载", -1))
                    ]),
                    _createElementVNode("div", _hoisted_17, _toDisplayString(reasonCount.value.downloadable || 0), 1)
                  ]),
                  _createElementVNode("div", _hoisted_18, [
                    _createElementVNode("div", _hoisted_19, [
                      _createVNode(_component_VAvatar, {
                        color: "info",
                        variant: "tonal",
                        size: "28",
                        rounded: "lg"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VIcon, {
                            icon: "mdi-file-document-edit-outline",
                            size: "17"
                          })
                        ]),
                        _: 1
                      }),
                      _cache[18] || (_cache[18] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "规则修改", -1))
                    ]),
                    _createElementVNode("div", _hoisted_20, _toDisplayString(ruleRecords.value.length), 1)
                  ])
                ]),
                (items.value.length)
                  ? (_openBlock(true), _createElementBlock(_Fragment, { key: 0 }, _renderList(items.value, (item) => {
                      return (_openBlock(), _createBlock(_component_VCard, {
                        key: item.result_id || (item.subscribe_id + '-' + item.created_at),
                        flat: "",
                        class: "sp-inner-card mb-3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VCardItem, { class: "sp-result-header" }, {
                            append: _withCtx(() => [
                              _createVNode(_component_VChip, {
                                color: reasonColor(item.reason),
                                size: "small",
                                variant: "tonal",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(reasonText(item.reason)), 1)
                                ]),
                                _: 2
                              }, 1032, ["color"]),
                              _createVNode(_component_VBtn, {
                                icon: "mdi-delete-outline",
                                color: "error",
                                variant: "text",
                                size: "small",
                                loading: deletingResultId.value === item.result_id,
                                onClick: $event => (deleteResult(item))
                              }, null, 8, ["loading", "onClick"])
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(item.title), 1)
                                ]),
                                _: 2
                              }, 1024),
                              _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
                                default: _withCtx(() => [
                                  _createTextVNode("TMDB " + _toDisplayString(item.tmdbid) + " / S" + _toDisplayString(item.season) + " / " + _toDisplayString(item.category), 1)
                                ]),
                                _: 2
                              }, 1024)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_VDivider),
                          _createVNode(_component_VCardText, { class: "pa-3" }, {
                            default: _withCtx(() => [
                              _createElementVNode("div", _hoisted_21, [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(item.episodes || [], (episode) => {
                                  return (_openBlock(), _createBlock(_component_VChip, {
                                    key: episode.episode,
                                    size: "small",
                                    variant: "tonal",
                                    class: "mr-1 mb-1"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(" E" + _toDisplayString(episode.episode) + " / " + _toDisplayString(episode.air_date), 1)
                                    ]),
                                    _: 2
                                  }, 1024))
                                }), 128))
                              ]),
                              _createElementVNode("div", _hoisted_22, _toDisplayString(item.message), 1),
                              (item.candidates?.length)
                                ? (_openBlock(), _createElementBlock("div", _hoisted_23, [
                                    _createVNode(_component_VTable, {
                                      density: "compact",
                                      class: "sp-candidate-table"
                                    }, {
                                      default: _withCtx(() => [
                                        _cache[20] || (_cache[20] = _createElementVNode("thead", null, [
                                          _createElementVNode("tr", null, [
                                            _createElementVNode("th", null, "站点"),
                                            _createElementVNode("th", null, "标题"),
                                            _createElementVNode("th", null, "做种"),
                                            _createElementVNode("th", { class: "text-right" }, "操作")
                                          ])
                                        ], -1)),
                                        _createElementVNode("tbody", null, [
                                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(item.candidates.slice(0, 8), (candidate) => {
                                            return (_openBlock(), _createElementBlock("tr", {
                                              key: candidate.candidate_id || candidate.title
                                            }, [
                                              _createElementVNode("td", _hoisted_24, _toDisplayString(candidate.site_name || candidate.site), 1),
                                              _createElementVNode("td", _hoisted_25, _toDisplayString(candidate.title), 1),
                                              _createElementVNode("td", _hoisted_26, _toDisplayString(candidate.seeders || 0), 1),
                                              _createElementVNode("td", _hoisted_27, [
                                                _createVNode(_component_VBtn, {
                                                  color: "primary",
                                                  variant: "text",
                                                  size: "small",
                                                  "prepend-icon": "mdi-file-eye-outline",
                                                  onClick: $event => (previewRule(item, candidate))
                                                }, {
                                                  default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
                                                    _createTextVNode("规则预览", -1)
                                                  ]))]),
                                                  _: 1
                                                }, 8, ["onClick"])
                                              ])
                                            ]))
                                          }), 128))
                                        ])
                                      ]),
                                      _: 2
                                    }, 1024)
                                  ]))
                                : _createCommentVNode("", true)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        _: 2
                      }, 1024))
                    }), 128))
                  : (_openBlock(), _createElementBlock("div", _hoisted_28, "暂无待处理诊断"))
              ], 512), [
                [_vShow, activeGroup.value === 'overview']
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_29, [
                _createElementVNode("div", _hoisted_30, [
                  _cache[21] || (_cache[21] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "自定义识别词", -1)),
                  _createVNode(_component_VSpacer),
                  _createVNode(_component_VChip, {
                    size: "small",
                    variant: "tonal"
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(identifierRecords.value.length), 1)
                    ]),
                    _: 1
                  })
                ]),
                (identifierError.value)
                  ? (_openBlock(), _createBlock(_component_VAlert, {
                      key: 0,
                      type: "error",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-3 text-caption",
                      closable: "",
                      "onClick:close": _cache[2] || (_cache[2] = $event => (identifierError.value = ''))
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(identifierError.value), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                (identifierMessage.value)
                  ? (_openBlock(), _createBlock(_component_VAlert, {
                      key: 1,
                      type: "success",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-3 text-caption",
                      closable: "",
                      "onClick:close": _cache[3] || (_cache[3] = $event => (identifierMessage.value = ''))
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(identifierMessage.value), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                _cache[24] || (_cache[24] = _createElementVNode("div", { class: "sp-subsection-title" }, "自动处理", -1)),
                _createVNode(_component_VRow, {
                  class: "sp-id-row",
                  align: "center"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "8"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VTextField, {
                          modelValue: identifierAutoTitle.value,
                          "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((identifierAutoTitle).value = $event)),
                          label: "媒体文件名",
                          density: "compact",
                          variant: "outlined",
                          "hide-details": "",
                          clearable: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "4",
                      class: "sp-id-action"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VBtn, {
                          color: "primary",
                          "prepend-icon": "mdi-auto-fix",
                          variant: "tonal",
                          size: "small",
                          loading: identifierBusy.value === 'auto',
                          onClick: runIdentifierAuto
                        }, {
                          default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
                            _createTextVNode("自动处理", -1)
                          ]))]),
                          _: 1
                        }, 8, ["loading"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_VDivider, { class: "my-3" }),
                _cache[25] || (_cache[25] = _createElementVNode("div", { class: "sp-subsection-title" }, "手动处理", -1)),
                _createVNode(_component_VRow, {
                  class: "sp-id-row",
                  align: "center"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "5"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VTextField, {
                          modelValue: identifierManualTitle.value,
                          "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((identifierManualTitle).value = $event)),
                          label: "媒体文件名",
                          density: "compact",
                          variant: "outlined",
                          "hide-details": "",
                          clearable: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "6",
                      md: "2"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VSelect, {
                          modelValue: identifierManualType.value,
                          "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((identifierManualType).value = $event)),
                          items: mediaTypeOptions,
                          label: "类型",
                          density: "compact",
                          variant: "outlined",
                          "hide-details": ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "6",
                      md: "3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VTextField, {
                          modelValue: identifierManualTmdbid.value,
                          "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((identifierManualTmdbid).value = $event)),
                          label: "TMDB ID",
                          placeholder: "填写 TMDB 的 ID",
                          density: "compact",
                          variant: "outlined",
                          "hide-details": "",
                          clearable: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "2",
                      class: "sp-id-action"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VBtn, {
                          color: "primary",
                          "prepend-icon": "mdi-pencil-plus-outline",
                          variant: "tonal",
                          size: "small",
                          loading: identifierBusy.value === 'manual',
                          onClick: runIdentifierManual
                        }, {
                          default: _withCtx(() => [...(_cache[23] || (_cache[23] = [
                            _createTextVNode("手动处理", -1)
                          ]))]),
                          _: 1
                        }, 8, ["loading"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (identifierRecords.value.length)
                  ? (_openBlock(), _createBlock(_component_VList, {
                      key: 2,
                      density: "compact",
                      lines: "two",
                      class: "mt-2"
                    }, {
                      default: _withCtx(() => [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(identifierRecords.value, (record) => {
                          return (_openBlock(), _createBlock(_component_VListItem, {
                            key: record.mode + '-' + record.candidate_title + '-' + record.created_at,
                            title: identifierModeText(record.mode) + '：' + (record.candidate_title || record.title || '-'),
                            subtitle: (record.message || '-') + ' / ' + (record.created_at || '-')
                          }, {
                            append: _withCtx(() => [
                              _createVNode(_component_VChip, {
                                color: identifierStatusColor(record.status),
                                size: "small",
                                variant: "tonal"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(identifierStatusText(record.status)), 1)
                                ]),
                                _: 2
                              }, 1032, ["color"])
                            ]),
                            _: 2
                          }, 1032, ["title", "subtitle"]))
                        }), 128))
                      ]),
                      _: 1
                    }))
                  : (_openBlock(), _createElementBlock("div", _hoisted_31, "暂无识别词记录"))
              ], 512), [
                [_vShow, activeGroup.value === 'identifier']
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_32, [
                _createElementVNode("div", _hoisted_33, [
                  _cache[27] || (_cache[27] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "规则修改记录", -1)),
                  _createVNode(_component_VSpacer),
                  (ruleRecords.value.length)
                    ? (_openBlock(), _createBlock(_component_VBtn, {
                        key: 0,
                        color: "warning",
                        variant: "text",
                        size: "small",
                        "prepend-icon": "mdi-delete-sweep-outline",
                        loading: clearingRules.value,
                        onClick: clearRuleRecords
                      }, {
                        default: _withCtx(() => [...(_cache[26] || (_cache[26] = [
                          _createTextVNode("清空", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading"]))
                    : _createCommentVNode("", true)
                ]),
                (ruleRecords.value.length)
                  ? (_openBlock(), _createBlock(_component_VList, {
                      key: 0,
                      density: "compact",
                      lines: "two"
                    }, {
                      default: _withCtx(() => [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(ruleRecords.value, (record) => {
                          return (_openBlock(), _createBlock(_component_VListItem, {
                            key: record.record_id || (record.subscribe_id + '-' + record.created_at),
                            title: '【' + (record.subscribe_name || ('订阅#' + record.subscribe_id)) + '】' + (record.change_type || record.field),
                            subtitle: (record.old_value || '-') + ' → ' + (record.new_value || '-') + '（' + (record.source || '-') + ' / ' + (record.created_at || '-') + '）'
                          }, {
                            append: _withCtx(() => [
                              _createVNode(_component_VBtn, {
                                icon: "mdi-delete-outline",
                                color: "error",
                                variant: "text",
                                size: "small",
                                loading: deletingRuleId.value === record.record_id,
                                onClick: $event => (deleteRuleRecord(record))
                              }, null, 8, ["loading", "onClick"])
                            ]),
                            _: 2
                          }, 1032, ["title", "subtitle"]))
                        }), 128))
                      ]),
                      _: 1
                    }))
                  : (_openBlock(), _createElementBlock("div", _hoisted_34, "暂无记录"))
              ], 512), [
                [_vShow, activeGroup.value === 'rules']
              ]),
              (_openBlock(), _createElementBlock(_Fragment, null, _renderList(configGroupKeys, (groupKey) => {
                return _withDirectives(_createElementVNode("div", {
                  key: groupKey,
                  class: "sp-pane"
                }, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(sectionsOf(groupKey), (section, sIdx) => {
                    return (_openBlock(), _createElementBlock(_Fragment, {
                      key: section.title
                    }, [
                      (sIdx > 0)
                        ? (_openBlock(), _createBlock(_component_VDivider, {
                            key: 0,
                            class: "my-3"
                          }))
                        : _createCommentVNode("", true),
                      _createElementVNode("div", _hoisted_35, _toDisplayString(section.title), 1),
                      _createVNode(_component_VRow, null, {
                        default: _withCtx(() => [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(section.fields, (field) => {
                            return (_openBlock(), _createBlock(_component_VCol, {
                              key: field.key,
                              cols: "12",
                              md: field.cols?.md || 6
                            }, {
                              default: _withCtx(() => [
                                (field.type === 'switch')
                                  ? (_openBlock(), _createBlock(_component_VSwitch, {
                                      key: 0,
                                      modelValue: config[field.key],
                                      "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                      color: field.color || 'primary',
                                      inset: "",
                                      "hide-details": "",
                                      label: field.label
                                    }, null, 8, ["modelValue", "onUpdate:modelValue", "color", "label"]))
                                  : (field.type === 'number')
                                    ? (_openBlock(), _createBlock(_component_VTextField, {
                                        key: 1,
                                        modelValue: config[field.key],
                                        "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                        modelModifiers: { number: true },
                                        type: "number",
                                        min: field.min,
                                        label: field.label,
                                        variant: "outlined",
                                        density: "compact",
                                        "hide-details": "auto",
                                        hint: field.hint,
                                        "persistent-hint": !!field.hint
                                      }, null, 8, ["modelValue", "onUpdate:modelValue", "min", "label", "hint", "persistent-hint"]))
                                    : (field.type === 'text')
                                      ? (_openBlock(), _createBlock(_component_VTextField, {
                                          key: 2,
                                          modelValue: config[field.key],
                                          "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                          label: field.label,
                                          variant: "outlined",
                                          density: "compact",
                                          "hide-details": "auto",
                                          hint: field.hint,
                                          "persistent-hint": !!field.hint,
                                          "error-messages": field.validate === 'cron' ? cronError.value : ''
                                        }, null, 8, ["modelValue", "onUpdate:modelValue", "label", "hint", "persistent-hint", "error-messages"]))
                                      : (field.type === 'select')
                                        ? (_openBlock(), _createBlock(_component_VSelect, {
                                            key: 3,
                                            modelValue: config[field.key],
                                            "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                            items: field.options,
                                            "item-title": "title",
                                            "item-value": "value",
                                            label: field.label,
                                            variant: "outlined",
                                            density: "compact",
                                            "hide-details": "auto"
                                          }, null, 8, ["modelValue", "onUpdate:modelValue", "items", "label"]))
                                        : (field.type === 'multiselect')
                                          ? (_openBlock(), _createBlock(_component_VSelect, {
                                              key: 4,
                                              modelValue: config[field.key],
                                              "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                              items: optionsFor(field),
                                              "item-title": "title",
                                              "item-value": "value",
                                              label: field.label,
                                              variant: "outlined",
                                              density: "compact",
                                              multiple: "",
                                              chips: "",
                                              "closable-chips": "",
                                              clearable: field.clearable,
                                              "hide-details": "auto"
                                            }, null, 8, ["modelValue", "onUpdate:modelValue", "items", "label", "clearable"]))
                                          : _createCommentVNode("", true)
                              ]),
                              _: 2
                            }, 1032, ["md"]))
                          }), 128))
                        ]),
                        _: 2
                      }, 1024),
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(section.fields, (field) => {
                        return (_openBlock(), _createElementBlock(_Fragment, {
                          key: field.key + '-alert'
                        }, [
                          (field.alert)
                            ? (_openBlock(), _createBlock(_component_VAlert, {
                                key: 0,
                                class: "mt-3",
                                type: "info",
                                variant: "tonal",
                                density: "compact",
                                text: field.alert
                              }, null, 8, ["text"]))
                            : _createCommentVNode("", true)
                        ], 64))
                      }), 128))
                    ], 64))
                  }), 128))
                ]), [
                  [_vShow, activeGroup.value === groupKey]
                ])
              }), 64))
            ]),
            _createVNode(_component_VDivider),
            _createElementVNode("div", _hoisted_36, [
              _createVNode(_component_VSpacer, { class: "sp-action-spacer" }),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                onClick: reloadAll
              }, {
                default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
                  _createTextVNode("刷新", -1)
                ]))]),
                _: 1
              }, 8, ["loading"]),
              _createVNode(_component_VBtn, {
                color: "primary",
                "prepend-icon": "mdi-content-save",
                variant: "text",
                size: "small",
                onClick: saveConfig
              }, {
                default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
                  _createTextVNode("保存", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-close",
                variant: "text",
                size: "small",
                onClick: _cache[8] || (_cache[8] = $event => (emit('close')))
              }, {
                default: _withCtx(() => [...(_cache[30] || (_cache[30] = [
                  _createTextVNode("关闭", -1)
                ]))]),
                _: 1
              })
            ])
          ])
        ])
      ]),
      _: 1
    }),
    _createVNode(_component_VDialog, {
      modelValue: previewDialog.value,
      "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((previewDialog).value = $event)),
      "max-width": "720"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCard, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [...(_cache[31] || (_cache[31] = [
                _createTextVNode("规则修改预览", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardText, null, {
              default: _withCtx(() => [
                (previewError.value)
                  ? (_openBlock(), _createBlock(_component_VAlert, {
                      key: 0,
                      type: "error",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-2"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(previewError.value), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                (ruleSuggestions.value.length && !preview.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_37, [
                      _cache[32] || (_cache[32] = _createElementVNode("div", { class: "text-caption text-medium-emphasis mb-2" }, "请选择要添加的官组、平台关键词或 PT 站点", -1)),
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(ruleSuggestions.value, (suggestion) => {
                        return (_openBlock(), _createBlock(_component_VBtn, {
                          key: suggestion.pattern,
                          color: "primary",
                          variant: "tonal",
                          size: "small",
                          class: "mr-2 mb-2",
                          loading: previewLoading.value === suggestion.pattern,
                          onClick: $event => (previewRuleSuggestion(suggestion))
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(suggestion.text), 1)
                          ]),
                          _: 2
                        }, 1032, ["loading", "onClick"]))
                      }), 128))
                    ]))
                  : _createCommentVNode("", true),
                (preview.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_38, [
                      (preview.value.selected_text)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_39, "已选择：" + _toDisplayString(preview.value.selected_text), 1))
                        : _createCommentVNode("", true),
                      (preview.value.field === 'sites')
                        ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                            _createElementVNode("div", null, "旧订阅站点：" + _toDisplayString(formatPreviewSites(preview.value.old_site_names || preview.value.old_sites, 'MP 默认搜索站点')), 1),
                            _createElementVNode("div", null, "新订阅站点：" + _toDisplayString(formatPreviewSites(preview.value.new_site_names || preview.value.new_sites)), 1)
                          ], 64))
                        : (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                            _createElementVNode("div", null, "旧 include：" + _toDisplayString(preview.value.old_include || '-'), 1),
                            _createElementVNode("div", null, "新 include：" + _toDisplayString(preview.value.new_include || '-'), 1)
                          ], 64))
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_VCardActions, null, {
              default: _withCtx(() => [
                _createVNode(_component_VSpacer),
                _createVNode(_component_VBtn, {
                  variant: "text",
                  onClick: _cache[9] || (_cache[9] = $event => (previewDialog.value = false))
                }, {
                  default: _withCtx(() => [...(_cache[33] || (_cache[33] = [
                    _createTextVNode("返回", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_VBtn, {
                  color: "primary",
                  variant: "text",
                  disabled: !preview.value?.token,
                  onClick: confirmRule
                }, {
                  default: _withCtx(() => [...(_cache[34] || (_cache[34] = [
                    _createTextVNode("确认修改", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-3dffd840"]]);

export { Config as default };
