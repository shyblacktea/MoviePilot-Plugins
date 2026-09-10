import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const subscribePlusLogo = "data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%20512%20512'%20role='img'%20aria-label='SubscribePlus'%3e%3crect%20width='512'%20height='512'%20rx='112'%20fill='%236f45d8'/%3e%3crect%20x='76'%20y='92'%20width='360'%20height='328'%20rx='64'%20fill='%234e2ca9'%20stroke='%23ffffff'%20stroke-opacity='0.9'%20stroke-width='20'/%3e%3ccircle%20cx='142'%20cy='178'%20r='18'%20fill='%23ffffff'/%3e%3crect%20x='184'%20y='160'%20width='148'%20height='36'%20rx='18'%20fill='%23ffffff'/%3e%3ccircle%20cx='142'%20cy='250'%20r='18'%20fill='%23ffffff'/%3e%3crect%20x='184'%20y='232'%20width='104'%20height='36'%20rx='18'%20fill='%23ffffff'/%3e%3ccircle%20cx='142'%20cy='322'%20r='18'%20fill='%23ffffff'/%3e%3crect%20x='184'%20y='304'%20width='82'%20height='36'%20rx='18'%20fill='%23ffffff'/%3e%3ccircle%20cx='350'%20cy='326'%20r='78'%20fill='%232ac89a'/%3e%3cpath%20d='M350%20278v76m-34-28%2034%2034%2034-34'%20fill='none'%20stroke='%23ffffff'%20stroke-linecap='round'%20stroke-linejoin='round'%20stroke-width='24'/%3e%3cpath%20d='M392%2082l9%2024%2024%209-24%209-9%2024-9-24-24-9%2024-9z'%20fill='%23ffc857'/%3e%3c/svg%3e";

/**
 * SubscribePlus 配置字段元数据。
 *
 * 每个字段声明渲染类型与归属 tab，Config.vue 据此自动渲染表单，
 * 新增配置项只需在此追加声明，无需改模板。
 */

/** tab 分组定义：key 与 Config.vue 的导航一一对应 */
const groups = [
  { key: 'overview', title: '运行概览', icon: 'mdi-view-dashboard-outline', desc: '扫描状态、待处理诊断与快捷操作。' },
  { key: 'identifier', title: '识别词工具', icon: 'mdi-tag-plus-outline', desc: '按 TMDB 强制绑定媒体或修正年份。' },
  { key: 'rules', title: '规则记录', icon: 'mdi-history', desc: '订阅规则修改历史。' },
  { key: 'scan', title: '扫描设置', icon: 'mdi-tune-variant', desc: '订阅扫描周期、宽限天数与站点范围。' },
  { key: 'notify', title: '通知权限', icon: 'mdi-message-badge-outline', desc: 'Telegram 通知、重复提醒抑制与规则修改授权。' },
  { key: 'notify_rules', title: 'F4通知目标面板', icon: 'mdi-bell-cog-outline', desc: '系统通知(入库/下载/订阅)目标 + 订阅用户映射。' },
  { key: 'cleanup', title: '清理与候选', icon: 'mdi-broom', desc: '整季包清理与候选下载缓存。' },
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
    key: 'enabled', group: 'scan', section: '运行状态', type: 'switch',
    label: '启用插件', color: 'success',
    hint: '开启后插件将处于激活状态',
  },
  {
    key: 'delay_days', group: 'scan', section: '扫描窗口', type: 'number',
    label: '宽限天数', min: 0, unit: '天', cols: { md: 4 },
    hint: '单集播出超过 N 天仍未入库才触发诊断',
  },
  {
    key: 'cron', group: 'scan', section: '扫描窗口', type: 'text',
    label: 'Cron', cols: { md: 4 },
    hint: '每 6 小时建议写 0 */6 * * *', validate: 'cron',
  },
  {
    key: 'max_scan_subscribes', group: 'scan', section: '扫描窗口', type: 'number',
    label: '订阅部数通知上限', min: 1, unit: '部', cols: { md: 4 },
    hint: '单次扫描最多通知的订阅部数',
  },
  {
    key: 'selected_categories', group: 'scan', section: '扫描范围', type: 'multiselect',
    label: '二级分类', optionsKey: 'categories', cols: { md: 6 },
    hint: '仅检测所选二级分类下的电视剧订阅',
  },
  {
    key: 'search_sites', group: 'scan', section: '扫描范围', type: 'multiselect',
    label: 'PT搜索范围', optionsKey: 'sites', clearable: true, cols: { md: 6 },
    hint: '插件诊断搜索的站点，留空用 MP 默认搜索站点',
  },

  // ---- 通知权限 ----
  {
    key: 'notify_tg', group: 'notify', section: '通知渠道', type: 'switch',
    label: 'Telegram 独立通知', color: 'primary', cols: { md: 6 },
    hint: '每部剧单独发送 Telegram 诊断通知',
  },
  {
    key: 'allow_tg_rule_update', group: 'notify', section: '授权', type: 'switch',
    label: '允许 TG 修改订阅规则', color: 'warning', cols: { md: 6 },
    hint: '开启后可在 Telegram 交互中直接写入订阅过滤规则',
    alert: '开启后可通过 Telegram 交互直接调整订阅过滤规则，请谨慎授权。',
  },
  {
    key: 'notification_suppression_days', group: 'notify', section: '重复提醒抑制', type: 'number',
    label: '不通知天数', min: 0, unit: '天', cols: { md: 6 },
    hint: '同一诊断选择“不通知”后，在此期限内不再重复提醒；0 表示关闭',
  },

  // ---- 清理与候选 ----
  {
    key: 'season_pack_cleanup', group: 'cleanup', section: '全集包清理', type: 'select',
    label: '最终集整季包清理', cols: { md: 6 },
    hint: '最终集来自整季包时清理旧拆包记录或源文件',
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
    hint: '最终集命中整季包时，把 qB 种子全部文件设为下载',
  },
  {
    key: 'candidate_cache_days', group: 'cleanup', section: '候选下载', type: 'number',
    label: '候选缓存天数', min: 0, unit: '天', cols: { md: 6 },
    hint: '候选种子下载信息缓存有效期；TG 选择条使用同一个天数，0 关闭',
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
  notification_suppression_days: 3,
  custom_release_groups: [],
  custom_platforms: [],
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

const {unref:_unref,createElementVNode:_createElementVNode,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createBlock:_createBlock,renderList:_renderList,Fragment:_Fragment,createSlots:_createSlots,vShow:_vShow,withDirectives:_withDirectives,mergeProps:_mergeProps,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "sp-config" };
const _hoisted_2 = ["src"];
const _hoisted_3 = { class: "d-flex align-center ga-2" };
const _hoisted_4 = {
  key: 0,
  class: "sp-dirty-hint"
};
const _hoisted_5 = { class: "text-caption text-warning font-weight-medium" };
const _hoisted_6 = { class: "sp-body" };
const _hoisted_7 = { class: "sp-nav" };
const _hoisted_8 = { class: "sp-content" };
const _hoisted_9 = { class: "sp-mobile-groupbar" };
const _hoisted_10 = { class: "sp-mobile-groupinfo" };
const _hoisted_11 = { class: "sp-mobile-group-title" };
const _hoisted_12 = { class: "sp-mobile-group-desc" };
const _hoisted_13 = { class: "sp-workspace" };
const _hoisted_14 = { class: "sp-window" };
const _hoisted_15 = { class: "sp-pane" };
const _hoisted_16 = { class: "d-flex align-center flex-wrap ga-1 mb-3" };
const _hoisted_17 = { class: "sp-stat-grid mb-4" };
const _hoisted_18 = { class: "sp-stat" };
const _hoisted_19 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_20 = { class: "text-subtitle-2 font-weight-bold sp-stat-value" };
const _hoisted_21 = { class: "sp-stat" };
const _hoisted_22 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_23 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_24 = { class: "sp-stat" };
const _hoisted_25 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_26 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_27 = { class: "sp-stat" };
const _hoisted_28 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_29 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_30 = { class: "mb-2" };
const _hoisted_31 = { class: "text-caption text-medium-emphasis mb-2" };
const _hoisted_32 = {
  key: 0,
  class: "sp-candidate-wrap mt-2"
};
const _hoisted_33 = { class: "sp-cand-site" };
const _hoisted_34 = { class: "sp-cand-title" };
const _hoisted_35 = { class: "sp-cand-seed" };
const _hoisted_36 = { class: "text-right sp-cand-act" };
const _hoisted_37 = {
  key: 1,
  class: "sp-empty"
};
const _hoisted_38 = { class: "sp-pane" };
const _hoisted_39 = { class: "d-flex align-center mb-3" };
const _hoisted_40 = { class: "sp-identifier-record-body" };
const _hoisted_41 = { class: "sp-identifier-record-title" };
const _hoisted_42 = { class: "sp-identifier-record-meta" };
const _hoisted_43 = {
  key: 0,
  class: "sp-identifier-record-rule"
};
const _hoisted_44 = {
  key: 3,
  class: "sp-empty"
};
const _hoisted_45 = { class: "sp-pane" };
const _hoisted_46 = { class: "d-flex align-center mb-3" };
const _hoisted_47 = {
  key: 1,
  class: "sp-empty"
};
const _hoisted_48 = { class: "sp-config-section mt-3" };
const _hoisted_49 = { class: "d-flex align-center mb-2" };
const _hoisted_50 = { class: "sp-field-rows" };
const _hoisted_51 = { class: "sp-field-row" };
const _hoisted_52 = { class: "sp-field-control sp-ctl-multiselect" };
const _hoisted_53 = { class: "sp-field-row" };
const _hoisted_54 = { class: "sp-field-control sp-ctl-multiselect" };
const _hoisted_55 = { class: "sp-pane" };
const _hoisted_56 = { class: "d-flex align-center mb-2" };
const _hoisted_57 = { class: "sp-config-section" };
const _hoisted_58 = { class: "sp-field-rows" };
const _hoisted_59 = { class: "sp-field-info" };
const _hoisted_60 = { class: "sp-field-label" };
const _hoisted_61 = { class: "sp-field-control sp-ctl-select" };
const _hoisted_62 = { class: "sp-config-section mt-3" };
const _hoisted_63 = { class: "sp-field-rows" };
const _hoisted_64 = { class: "sp-field-row" };
const _hoisted_65 = { class: "sp-field-control sp-ctl-select" };
const _hoisted_66 = { class: "sp-field-info" };
const _hoisted_67 = { class: "sp-field-control sp-ctl-select" };
const _hoisted_68 = { class: "sp-field-actions" };
const _hoisted_69 = { class: "d-flex align-center mt-2" };
const _hoisted_70 = {
  key: 0,
  class: "text-caption text-medium-emphasis ml-3"
};
const _hoisted_71 = { class: "sp-section-title" };
const _hoisted_72 = { class: "sp-field-rows" };
const _hoisted_73 = { class: "sp-field-info" };
const _hoisted_74 = { class: "sp-field-label" };
const _hoisted_75 = {
  key: 0,
  class: "sp-field-hint"
};
const _hoisted_76 = {
  class: "sp-dashboard",
  "aria-label": "运行表盘"
};
const _hoisted_77 = { class: "sp-dashboard-section" };
const _hoisted_78 = { class: "sp-dashboard-title" };
const _hoisted_79 = { class: "sp-dashboard-row" };
const _hoisted_80 = { class: "sp-dashboard-row" };
const _hoisted_81 = { class: "sp-dashboard-row" };
const _hoisted_82 = { class: "sp-dashboard-row" };
const _hoisted_83 = { class: "sp-dashboard-section" };
const _hoisted_84 = { class: "sp-dashboard-title" };
const _hoisted_85 = { class: "sp-dashboard-row" };
const _hoisted_86 = { class: "sp-dashboard-row" };
const _hoisted_87 = { class: "sp-dashboard-row" };
const _hoisted_88 = { class: "sp-dashboard-row" };
const _hoisted_89 = {
  key: 1,
  class: "sp-suggestion"
};
const _hoisted_90 = {
  key: 2,
  class: "sp-preview-box"
};
const _hoisted_91 = { key: 0 };

const {computed,onMounted,reactive,ref,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
},
  emits: ['save', 'close', 'switch', 'layout'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const layoutRequest = { maxWidth: '70rem' };

// ===== 通用状态 =====
const activeGroup = ref('overview');
const mobileGroupSheet = ref(false);
const error = ref('');
const loading = ref(false);
const saving = ref(false);
const saveMessage = ref('');
const saveSnackbar = ref(false);
const cronError = ref('');

// ===== 配置（元数据驱动）=====
const config = reactive({ ...defaults });
// 已保存基线快照：与 config 逐键对比得出待保存项数
const savedBaseline = ref(JSON.parse(JSON.stringify(defaults)));

function normalizeValue(value) {
  if (Array.isArray(value)) return JSON.stringify([...value].sort())
  if (value === undefined || value === null) return ''
  return String(value)
}

const changedCount = computed(() => {
  let count = 0;
  for (const key of Object.keys(defaults)) {
    if (normalizeValue(config[key]) !== normalizeValue(savedBaseline.value[key])) count++;
  }
  return count
});

function snapshotBaseline() {
  savedBaseline.value = JSON.parse(JSON.stringify({ ...defaults, ...config }));
}

// ===== 概览数据 =====
const status = ref({});
const items = ref([]);
const ruleRecords = ref([]);
const identifierRecords = ref([]);
const scanning = ref(false);
const clearing = ref(false);
const clearingRules = ref(false);
const clearingIdentifiers = ref(false);
const deletingRuleId = ref('');
const deletingResultId = ref('');

// ===== 识别词 =====
const identifierTitle = ref('');
const identifierType = ref('tv');
const identifierTmdbid = ref('');
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
const ruleDictionaryLoading = ref(false);
const savingRuleDictionary = ref(false);
const ruleDictionaryError = ref('');
const ruleDictionaryHint = ref('');
const ruleDictionarySavedJson = ref('');

function normalizedDictionaryList(value) {
  const source = Array.isArray(value) ? value : String(value || '').split(/[,，\n]/);
  const result = [];
  const seen = new Set();
  for (const item of source) {
    const text = String(item || '').trim().replace(/\s+/g, ' ');
    const key = text.toLocaleLowerCase();
    if (!text || seen.has(key)) continue
    seen.add(key);
    result.push(text);
  }
  return result
}

const ruleDictionaryDirty = computed(() => JSON.stringify({
  release_groups: normalizedDictionaryList(config.custom_release_groups),
  platforms: normalizedDictionaryList(config.custom_platforms),
}) !== ruleDictionarySavedJson.value);

function snapshotRuleDictionary() {
  ruleDictionarySavedJson.value = JSON.stringify({
    release_groups: normalizedDictionaryList(config.custom_release_groups),
    platforms: normalizedDictionaryList(config.custom_platforms),
  });
}

// ===== 选项 =====
const categories = ref([]);
const siteOptions = ref([]);

// ===== F4 通知目标面板 =====
const f4Loading = ref(false);
const savingF4 = ref(false);
const f4Error = ref('');
const f4Hint = ref('');
const f4TypeLabels = { '资源下载': '资源下载', '整理入库': '资源入库', '订阅': '订阅' };
const f4Rows = ref([]);
const f4OptionItems = ref([
  { title: '发群组', value: 'all' },
  { title: '用户+管理员', value: 'user,admin' },
  { title: '仅用户', value: 'user' },
  { title: '仅管理员', value: 'admin' },
]);
const f4SavedJson = ref('');

const f4Dirty = computed(() => {
  const current = f4Rows.value
    .filter(row => String(row.type || '').trim())
    .map(row => `${String(row.type).trim()}\u0000${String(row.action || '').trim()}`)
    .sort();
  return JSON.stringify(current) !== f4SavedJson.value
});

// ===== 订阅通知管理 =====
const notifyRulesLoading = ref(false);
const savingNotifyRules = ref(false);
const notifyRulesError = ref('');
const notifyRulesHint = ref('');
const notifyMeta = ref({ channelKind: '', channelPrefix: '', hasChannel: false });
const notifyUsernameOptions = ref([]);
const notifyTargetOptions = ref([]);
const notifyRuleRows = ref([]);
const notifyRulesSavedJson = ref('');
const defaultNotifyTargets = ref([]);
let notifyRowUid = 0;
let notifyRulesLoadedOnce = false;

const notifyRulesDirty = computed(() => {
  const current = notifyRuleRows.value
    .filter(row => String(row.username || '').trim() && (Array.isArray(row.targets) ? row.targets.length : String(row.target || '').trim()))
    .map(row => `${String(row.username).trim()}\u0000${(Array.isArray(row.targets) ? [...row.targets].sort().join('|') : String(row.target || '').trim())}`)
    .sort();
  const currentWithDefault = {
    default: (Array.isArray(defaultNotifyTargets.value) ? [...defaultNotifyTargets.value].sort().join('|') : String(defaultNotifyTargets.value || '').trim()),
    rows: current,
  };
  return JSON.stringify(currentWithDefault) !== notifyRulesSavedJson.value
});

const availableNotifyUsernames = computed(() => {
  const used = new Set(
    notifyRuleRows.value
      .map(row => String(row.username || '').trim())
      .filter(Boolean),
  );
  return notifyUsernameOptions.value.filter(name => !used.has(name))
});

const currentGroup = computed(() => groups.find(g => g.key === activeGroup.value) || groups[0]);
const configGroupKeys = ['scan', 'notify', 'cleanup'];

const reasonCount = computed(() => items.value.reduce((acc, item) => {
  acc[item.reason] = (acc[item.reason] || 0) + 1;
  return acc
}, {}));

const candidateTotal = computed(() => items.value.reduce(
  (total, item) => total + (Array.isArray(item.candidates) ? item.candidates.length : 0),
  0,
));

const enabledFeatureCount = computed(() => [
  Boolean(config.enabled),
  Boolean(config.notify_tg),
  Boolean(config.allow_tg_rule_update),
  config.season_pack_cleanup !== 'off',
  Boolean(config.season_pack_full_download),
  Number(config.candidate_cache_days) > 0,
].filter(Boolean).length);

const scanScheduleText = computed(() => describeCron(config.cron));
const candidateCacheText = computed(() => Number(config.candidate_cache_days) > 0 ? `${config.candidate_cache_days} 天` : '已关闭');
const lastScanText = computed(() => formatCompactDateTime(status.value.last_scan));

function describeCron(value) {
  const cron = String(value || '').trim();
  const parts = cron.split(/\s+/);
  if (parts.length !== 5) return cron || '-'
  const [minute, hour, day, month, weekday] = parts;
  if (day === '*' && month === '*' && weekday === '*') {
    if (/^\d+$/.test(minute) && /^\d+$/.test(hour)) {
      return `每天 ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
    }
    const hourStep = hour.match(/^\*\/(\d+)$/);
    if (minute === '0' && hourStep) return `每 ${hourStep[1]} 小时`
    const minuteStep = minute.match(/^\*\/(\d+)$/);
    if (hour === '*' && minuteStep) return `每 ${minuteStep[1]} 分钟`
  }
  return cron
}

function formatCompactDateTime(value) {
  if (!value) return '-'
  const text = String(value).replace('T', ' ');
  return text.length >= 16 ? text.slice(5, 16) : text
}

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
  const arr = Array.isArray(value) ? value : [];
  const text = arr.filter(item => item !== undefined && item !== null && String(item).trim()).map(String).join(', ');
  return text || emptyText
}

function identifierModeText(mode) {
  return { force: '强制绑定', manual: '强制绑定', year: '年份修正', auto: 'AI识别' }[mode] || '识别记录'
}

function identifierStatusText(statusValue) {
  return statusValue === 'success' ? '成功' : '失败'
}

function identifierStatusColor(statusValue) {
  return statusValue === 'success' ? 'success' : 'error'
}

function applyInitialConfig(source = props.initialConfig) {
  const initial = source && typeof source === 'object' ? source : {};
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
    notification_suppression_days:
      initial.notification_suppression_days === undefined || initial.notification_suppression_days === null
        ? 3
        : Number(initial.notification_suppression_days),
    custom_release_groups: normalizedDictionaryList(initial.custom_release_groups),
    custom_platforms: normalizedDictionaryList(initial.custom_platforms),
  });
  snapshotRuleDictionary();
}

async function loadRuleDictionary() {
  ruleDictionaryLoading.value = true;
  ruleDictionaryError.value = '';
  try {
    const data = unwrap(await props.api.get('plugin/SubscribePlus/rule_dictionary')) || {};
    config.custom_release_groups = normalizedDictionaryList(data.release_groups);
    config.custom_platforms = normalizedDictionaryList(data.platforms);
    snapshotRuleDictionary();
    savedBaseline.value.custom_release_groups = [...config.custom_release_groups];
    savedBaseline.value.custom_platforms = [...config.custom_platforms];
  } catch (err) {
    ruleDictionaryError.value = err?.message || '读取自定义官组和平台失败';
  } finally {
    ruleDictionaryLoading.value = false;
  }
}

async function saveRuleDictionary() {
  savingRuleDictionary.value = true;
  ruleDictionaryError.value = '';
  ruleDictionaryHint.value = '';
  const payload = {
    release_groups: normalizedDictionaryList(config.custom_release_groups),
    platforms: normalizedDictionaryList(config.custom_platforms),
  };
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_dictionary', payload);
    const body = response?.data ?? response ?? {};
    const data = body?.data ?? body;
    if (body.success === false || data.success === false) {
      ruleDictionaryError.value = body.message || data.message || '保存自定义官组和平台失败';
      return
    }
    config.custom_release_groups = normalizedDictionaryList(data.release_groups ?? payload.release_groups);
    config.custom_platforms = normalizedDictionaryList(data.platforms ?? payload.platforms);
    snapshotRuleDictionary();
    savedBaseline.value.custom_release_groups = [...config.custom_release_groups];
    savedBaseline.value.custom_platforms = [...config.custom_platforms];
    ruleDictionaryHint.value = body.message || data.message || '自定义官组和平台已同步到网页与 Telegram';
  } catch (err) {
    ruleDictionaryError.value = err?.message || '保存自定义官组和平台失败';
  } finally {
    savingRuleDictionary.value = false;
  }
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
      // 自动填充不算用户改动，同步进基线避免误报待保存
      savedBaseline.value.selected_categories = [...config.selected_categories];
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

// ===== F4 通知目标面板 =====
async function loadF4Options() {
  f4Loading.value = true;
  f4Error.value = '';
  try {
    const data = unwrap(await props.api.get('plugin/SubscribePlus/f4_options')) || {};
    const types = Array.isArray(data.types) ? data.types : [];
    const current = data.current || {};
    f4Rows.value = types.map(type => ({
      type,
      label: f4TypeLabels[type] || type,
      action: String(current[type] || 'all'),
    }));
    const opts = Array.isArray(data.options) ? data.options : [];
    if (opts.length) f4OptionItems.value = opts;
    snapshotF4();
  } catch (err) {
    f4Error.value = err?.message || '读取系统通知目标配置失败';
  } finally {
    f4Loading.value = false;
  }
}

function snapshotF4() {
  const current = f4Rows.value
    .filter(row => String(row.type || '').trim())
    .map(row => `${String(row.type).trim()}\u0000${String(row.action || '').trim()}`)
    .sort();
  f4SavedJson.value = JSON.stringify(current);
}

async function saveF4Actions() {
  const actions = {};
  for (const row of f4Rows.value) {
    const type = String(row.type || '').trim();
    const action = String(row.action || '').trim();
    if (type && action) actions[type] = action;
  }
  savingF4.value = true;
  f4Error.value = '';
  f4Hint.value = '';
  try {
    const result = unwrap(await props.api.post('plugin/SubscribePlus/f4_actions', { actions })) || {};
    if (result.success === false) {
      f4Error.value = result.message || '保存失败';
      return
    }
    snapshotF4();
    f4Hint.value = result.message || `已保存 ${Object.keys(actions).length} 项系统通知目标`;
  } catch (err) {
    f4Error.value = err?.message || '保存系统通知目标失败';
  } finally {
    savingF4.value = false;
  }
}

// ===== 订阅通知管理 =====
async function loadNotifyRules() {
  notifyRulesLoading.value = true;
  notifyRulesError.value = '';
  try {
    const data = unwrap(await props.api.get('plugin/SubscribePlus/notify_options')) || {};
    notifyMeta.value = {
      channelKind: data.channel_kind || '',
      channelPrefix: data.channel_prefix || '',
      channelCount: data.channel_count || (data.channel_kind ? 1 : 0),
      hasChannel: Boolean(data.channel_kind),
    };
    notifyUsernameOptions.value = Array.isArray(data.usernames) ? [...data.usernames] : [];
    notifyTargetOptions.value = (Array.isArray(data.targets) ? data.targets : []).map(target => ({
      title: target.title || String(target.id),
      value: String(target.id),
      source: target.source || '',
      channel: target.channel || '',
    }));
    if (!data.channel_kind) {
      notifyRulesError.value = '未检测到启用的消息通知渠道（Telegram/QQ），请先在系统设置中配置通知渠道';
    }
    const rules = data.rules || {};
    notifyRuleRows.value = Object.keys(rules).map(username => {
      const raw = rules[username];
      const targetList = Array.isArray(raw) ? raw.map(String) : String(raw || '').split(',').filter(Boolean);
      return {
        uid: `row-${++notifyRowUid}`,
        username,
        targets: [...new Set(targetList)],
      }
    });
    // 已配置映射但当前渠道选项缺失的用户也要保留展示
    notifyRuleRows.value = notifyRuleRows.value.map(row => ({ ...row, uid: `row-${++notifyRowUid}` }));
    const defaultRaw = data.default_target;
    defaultNotifyTargets.value = Array.isArray(defaultRaw)
      ? [...new Set(defaultRaw.map(String).filter(Boolean))]
      : String(defaultRaw || '').split(',').filter(Boolean);
    snapshotNotifyRules();
  } catch (err) {
    notifyRulesError.value = err?.message || '读取订阅通知管理选项失败';
  } finally {
    notifyRulesLoading.value = false;
  }
}

function snapshotNotifyRules() {
  const rows = notifyRuleRows.value
    .filter(row => String(row.username || '').trim() && (Array.isArray(row.targets) ? row.targets.length : String(row.target || '').trim()))
    .map(row => `${String(row.username).trim()}\u0000${(Array.isArray(row.targets) ? [...row.targets].sort().join('|') : String(row.target || '').trim())}`)
    .sort();
  notifyRulesSavedJson.value = JSON.stringify({
    default: (Array.isArray(defaultNotifyTargets.value) ? [...defaultNotifyTargets.value].sort().join('|') : String(defaultNotifyTargets.value || '').trim()),
    rows,
  });
}

function addNotifyRuleRow() {
  const candidate = availableNotifyUsernames.value[0] || '';
  notifyRuleRows.value.push({
    uid: `row-${++notifyRowUid}`,
    username: candidate,
    targets: [],
  });
}

function removeNotifyRuleRow(index) {
  notifyRuleRows.value.splice(index, 1);
}

async function saveNotifyRules() {
  const rules = {};
  for (const row of notifyRuleRows.value) {
    const username = String(row.username || '').trim();
    const targets = Array.isArray(row.targets) ? row.targets : (String(row.target || '').split(',').filter(Boolean));
    const targetList = [...new Set(targets.map(t => String(t).trim()).filter(Boolean))];
    if (username && targetList.length) rules[username] = targetList.join(',');
  }
  const defaultTargetList = [...new Set((Array.isArray(defaultNotifyTargets.value) ? defaultNotifyTargets.value : []).map(t => String(t).trim()).filter(Boolean))];
  const defaultTarget = defaultTargetList.join(',');
  savingNotifyRules.value = true;
  notifyRulesError.value = '';
  notifyRulesHint.value = '';
  try {
    const result = unwrap(await props.api.post('plugin/SubscribePlus/notify_rules', { rules, default_target: defaultTarget })) || {};
    if (result.success === false) {
      notifyRulesError.value = result.message || '保存失败';
      return
    }
    snapshotNotifyRules();
    notifyRulesHint.value = result.message || `已保存 ${Object.keys(rules).length} 条订阅通知映射`;
    // 让配置页基线同步，避免把 notify_rules 当待保存项
    if (typeof config !== 'undefined' && config) {
      config.notify_rules = { ...rules };
      config.default_notify_target = defaultTarget;
    }
  } catch (err) {
    notifyRulesError.value = err?.message || '保存订阅通知映射失败';
  } finally {
    savingNotifyRules.value = false;
  }
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

async function clearIdentifierRecords() {
  clearingIdentifiers.value = true;
  identifierError.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/identifier_records/clear', {});
    identifierMessage.value = '识别历史已清空，已写入的自定义识别词不会被删除';
    await loadData();
  } catch (err) {
    identifierError.value = err?.message || '清空识别历史失败';
  } finally {
    clearingIdentifiers.value = false;
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

async function runIdentifierAction(action) {
  const title = identifierTitle.value.trim();
  const tmdbid = identifierTmdbid.value.trim();
  identifierError.value = '';
  identifierMessage.value = '';
  if (!title || (action !== 'auto' && !tmdbid)) {
    identifierError.value = action === 'auto' ? '请填写媒体文件名' : '请填写媒体文件名和 TMDB ID';
    return
  }
  identifierBusy.value = action;
  try {
    const endpoint = action === 'auto' ? 'identifier_auto' : (action === 'year' ? 'identifier_year' : 'identifier_manual');
    const payload = { title };
    if (action !== 'auto') {
      payload.media_type = identifierType.value;
      payload.tmdbid = tmdbid;
    }
    const response = await props.api.post(`plugin/SubscribePlus/${endpoint}`, payload);
    const fallback = action === 'auto' ? 'AI 识别处理完成' : (action === 'year' ? '已提交年份修正' : '已提交强制绑定');
    const result = readActionResponse(response, fallback);
    if (!result.success) {
      identifierError.value = result.message;
      return
    }
    identifierMessage.value = result.message;
    await loadData();
  } catch (err) {
    identifierError.value = err?.message || (action === 'year' ? '年份修正失败' : '强制绑定失败');
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
    const response = await props.api.post('plugin/SubscribePlus/rule_confirm', { token: preview.value.token });
    const result = readActionResponse(response, '确认修改失败');
    if (!result.success) {
      previewError.value = result.message;
      return
    }
    previewDialog.value = false;
    await loadData();
  } catch (err) {
    previewError.value = err?.message || '确认修改失败';
  }
}

function buildConfigPayload() {
  return {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    candidate_cache_days: Number(config.candidate_cache_days),
    notification_suppression_days: Number(config.notification_suppression_days),
    search_sites: Array.isArray(config.search_sites) ? [...config.search_sites] : [],
    selected_categories: Array.isArray(config.selected_categories) ? [...config.selected_categories] : [],
    custom_release_groups: normalizedDictionaryList(config.custom_release_groups),
    custom_platforms: normalizedDictionaryList(config.custom_platforms),
  }
}

async function saveConfig() {
  cronError.value = validateCron(config.cron);
  if (cronError.value) {
    activeGroup.value = 'scan';
    return
  }
  const payload = buildConfigPayload();
  error.value = '';
  saving.value = true;
  try {
    if (typeof props.api?.post === 'function') {
      const response = await props.api.post('plugin/SubscribePlus/config', payload);
      const body = response?.data ?? response ?? {};
      const data = body?.data ?? body;
      if (body.success === false || data.success === false) {
        throw new Error(body.message || data.message || '配置保存失败')
      }

      const verifyResponse = await props.api.get('plugin/SubscribePlus/config');
      const persisted = unwrap(verifyResponse);
      applyInitialConfig(persisted);
      snapshotBaseline();
    snapshotRuleDictionary();
      saveMessage.value = body.message || data.message || '配置已保存并生效';
      saveSnackbar.value = true;
      return
    }

    emit('save', payload);
    snapshotBaseline();
  } catch (err) {
    error.value = err?.message || '配置保存失败';
  } finally {
    saving.value = false;
  }
}

watch(
  () => props.initialConfig,
  value => {
    if (!value || typeof value !== 'object' || !Object.keys(value).length) return
    applyInitialConfig(value);
    snapshotBaseline();
  },
  { deep: true },
);

// 首次切到「F4通知目标面板」时加载系统通知目标与订阅用户映射
watch(activeGroup, async value => {
  if (value !== 'notify_rules') return
  if (notifyRulesLoadedOnce) return
  notifyRulesLoadedOnce = true;
  await Promise.all([loadF4Options(), loadNotifyRules()]);
});

onMounted(() => {
  emit('layout', layoutRequest);
  applyInitialConfig();
  snapshotBaseline();
  reloadAll();
  loadRuleDictionary();
});

return (_ctx, _cache) => {
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VListItemTitle = _resolveComponent("VListItemTitle");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VListItem = _resolveComponent("VListItem");
  const _component_VList = _resolveComponent("VList");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VTable = _resolveComponent("VTable");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VTooltip = _resolveComponent("VTooltip");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VCombobox = _resolveComponent("VCombobox");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VListItemSubtitle = _resolveComponent("VListItemSubtitle");
  const _component_VBottomSheet = _resolveComponent("VBottomSheet");
  const _component_VCardActions = _resolveComponent("VCardActions");
  const _component_VDialog = _resolveComponent("VDialog");
  const _component_VSnackbar = _resolveComponent("VSnackbar");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VCard, {
      flat: "",
      class: "sp-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardItem, { class: "sp-header" }, {
          prepend: _withCtx(() => [
            _createElementVNode("img", {
              src: _unref(subscribePlusLogo),
              alt: "",
              class: "sp-header-logo"
            }, null, 8, _hoisted_2)
          ]),
          append: _withCtx(() => [
            _createElementVNode("div", _hoisted_3, [
              (changedCount.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_4, [
                    _createVNode(_component_VIcon, {
                      icon: "mdi-circle-medium",
                      color: "warning",
                      size: "18"
                    }),
                    _createElementVNode("span", _hoisted_5, _toDisplayString(changedCount.value) + " 项待保存", 1)
                  ]))
                : _createCommentVNode("", true),
              (changedCount.value)
                ? (_openBlock(), _createBlock(_component_VBtn, {
                    key: 1,
                    color: "primary",
                    variant: "flat",
                    size: "small",
                    "prepend-icon": "mdi-content-save",
                    rounded: "lg",
                    loading: saving.value,
                    onClick: saveConfig
                  }, {
                    default: _withCtx(() => [...(_cache[23] || (_cache[23] = [
                      _createTextVNode("保存修改", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"]))
                : _createCommentVNode("", true),
              _createVNode(_component_VBtn, {
                icon: "mdi-close",
                variant: "text",
                size: "small",
                onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
              })
            ])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-h6 sp-header-title" }, {
              default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
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
        _createElementVNode("div", _hoisted_6, [
          _createElementVNode("nav", _hoisted_7, [
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
          _createElementVNode("section", _hoisted_8, [
            _createElementVNode("div", _hoisted_9, [
              _createVNode(_component_VIcon, {
                icon: currentGroup.value.icon,
                color: "primary",
                size: "20"
              }, null, 8, ["icon"]),
              _createElementVNode("div", _hoisted_10, [
                _createElementVNode("div", _hoisted_11, _toDisplayString(currentGroup.value.title), 1),
                _createElementVNode("div", _hoisted_12, _toDisplayString(currentGroup.value.desc), 1)
              ]),
              _createVNode(_component_VBtn, {
                icon: "mdi-format-list-bulleted",
                variant: "tonal",
                size: "small",
                rounded: "lg",
                onClick: _cache[1] || (_cache[1] = $event => (mobileGroupSheet.value = true))
              })
            ]),
            (error.value)
              ? (_openBlock(), _createBlock(_component_VAlert, {
                  key: 0,
                  type: "error",
                  variant: "tonal",
                  density: "compact",
                  class: "ma-3 mb-0 text-caption",
                  closable: "",
                  "onClick:close": _cache[2] || (_cache[2] = $event => (error.value = ''))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createElementVNode("div", _hoisted_13, [
              _createElementVNode("div", _hoisted_14, [
                _withDirectives(_createElementVNode("div", _hoisted_15, [
                  _createElementVNode("div", _hoisted_16, [
                    _cache[26] || (_cache[26] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "运行概览", -1)),
                    _createVNode(_component_VSpacer),
                    _createVNode(_component_VBtn, {
                      color: "primary",
                      "prepend-icon": "mdi-radar",
                      variant: "tonal",
                      size: "small",
                      loading: scanning.value,
                      onClick: runScan
                    }, {
                      default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
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
                      default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
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
                  _createElementVNode("div", _hoisted_17, [
                    _createElementVNode("div", _hoisted_18, [
                      _createElementVNode("div", _hoisted_19, [
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
                        _cache[27] || (_cache[27] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "最近扫描", -1))
                      ]),
                      _createElementVNode("div", _hoisted_20, _toDisplayString(status.value.last_scan || '-'), 1)
                    ]),
                    _createElementVNode("div", _hoisted_21, [
                      _createElementVNode("div", _hoisted_22, [
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
                        _cache[28] || (_cache[28] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "待处理", -1))
                      ]),
                      _createElementVNode("div", _hoisted_23, _toDisplayString(items.value.length), 1)
                    ]),
                    _createElementVNode("div", _hoisted_24, [
                      _createElementVNode("div", _hoisted_25, [
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
                        _cache[29] || (_cache[29] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "可下载", -1))
                      ]),
                      _createElementVNode("div", _hoisted_26, _toDisplayString(reasonCount.value.downloadable || 0), 1)
                    ]),
                    _createElementVNode("div", _hoisted_27, [
                      _createElementVNode("div", _hoisted_28, [
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
                        _cache[30] || (_cache[30] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "规则修改", -1))
                      ]),
                      _createElementVNode("div", _hoisted_29, _toDisplayString(ruleRecords.value.length), 1)
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
                                _createElementVNode("div", _hoisted_30, [
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
                                _createElementVNode("div", _hoisted_31, _toDisplayString(item.message), 1),
                                (item.candidates?.length)
                                  ? (_openBlock(), _createElementBlock("div", _hoisted_32, [
                                      _createVNode(_component_VTable, {
                                        density: "compact",
                                        class: "sp-candidate-table"
                                      }, {
                                        default: _withCtx(() => [
                                          _cache[32] || (_cache[32] = _createElementVNode("thead", null, [
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
                                                _createElementVNode("td", _hoisted_33, _toDisplayString(candidate.site_name || candidate.site), 1),
                                                _createElementVNode("td", _hoisted_34, _toDisplayString(candidate.title), 1),
                                                _createElementVNode("td", _hoisted_35, _toDisplayString(candidate.seeders || 0), 1),
                                                _createElementVNode("td", _hoisted_36, [
                                                  _createVNode(_component_VBtn, {
                                                    color: "primary",
                                                    variant: "text",
                                                    size: "small",
                                                    "prepend-icon": "mdi-file-eye-outline",
                                                    onClick: $event => (previewRule(item, candidate))
                                                  }, {
                                                    default: _withCtx(() => [...(_cache[31] || (_cache[31] = [
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
                    : (_openBlock(), _createElementBlock("div", _hoisted_37, "暂无待处理诊断"))
                ], 512), [
                  [_vShow, activeGroup.value === 'overview']
                ]),
                _withDirectives(_createElementVNode("div", _hoisted_38, [
                  _createElementVNode("div", _hoisted_39, [
                    _cache[33] || (_cache[33] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "自定义识别词", -1)),
                    _createVNode(_component_VSpacer),
                    _createVNode(_component_VChip, {
                      size: "small",
                      variant: "tonal"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(identifierRecords.value.length), 1)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VTooltip, {
                      text: "清空识别历史",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tooltipProps }) => [
                        _createVNode(_component_VBtn, _mergeProps(tooltipProps, {
                          class: "ml-1",
                          icon: "mdi-delete-sweep-outline",
                          color: "error",
                          variant: "text",
                          size: "small",
                          loading: clearingIdentifiers.value,
                          disabled: !identifierRecords.value.length,
                          onClick: clearIdentifierRecords
                        }), null, 16, ["loading", "disabled"])
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
                        "onClick:close": _cache[3] || (_cache[3] = $event => (identifierError.value = ''))
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
                        "onClick:close": _cache[4] || (_cache[4] = $event => (identifierMessage.value = ''))
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(identifierMessage.value), 1)
                        ]),
                        _: 1
                      }))
                    : _createCommentVNode("", true),
                  _createVNode(_component_VAlert, {
                    type: "info",
                    density: "compact",
                    variant: "tonal",
                    class: "mb-3 text-caption"
                  }, {
                    default: _withCtx(() => [...(_cache[34] || (_cache[34] = [
                      _createTextVNode(" AI 识别会调用 MoviePilot 当前配置的 AI，根据媒体文件名判断目标 TMDB，并自动写入识别词；不需要填写 TMDB ID。 ", -1)
                    ]))]),
                    _: 1
                  }),
                  _createVNode(_component_VRow, {
                    class: "sp-id-row",
                    align: "center"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCol, { cols: "12" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VTextField, {
                            modelValue: identifierTitle.value,
                            "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((identifierTitle).value = $event)),
                            label: "媒体文件名",
                            placeholder: "填写完整文件名或发布标题",
                            density: "compact",
                            variant: "outlined",
                            "hide-details": "",
                            clearable: ""
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_VCol, {
                        cols: "5",
                        md: "3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VSelect, {
                            modelValue: identifierType.value,
                            "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((identifierType).value = $event)),
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
                        cols: "7",
                        md: "4"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VTextField, {
                            modelValue: identifierTmdbid.value,
                            "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((identifierTmdbid).value = $event)),
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
                        md: "5",
                        class: "sp-id-actions"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VBtn, {
                            color: "primary",
                            "prepend-icon": "mdi-brain",
                            variant: "flat",
                            size: "small",
                            loading: identifierBusy.value === 'auto',
                            disabled: Boolean(identifierBusy.value),
                            onClick: _cache[8] || (_cache[8] = $event => (runIdentifierAction('auto')))
                          }, {
                            default: _withCtx(() => [...(_cache[35] || (_cache[35] = [
                              _createTextVNode("AI 识别并写入", -1)
                            ]))]),
                            _: 1
                          }, 8, ["loading", "disabled"]),
                          _createVNode(_component_VBtn, {
                            color: "primary",
                            "prepend-icon": "mdi-link-variant-plus",
                            variant: "tonal",
                            size: "small",
                            loading: identifierBusy.value === 'force',
                            disabled: Boolean(identifierBusy.value),
                            onClick: _cache[9] || (_cache[9] = $event => (runIdentifierAction('force')))
                          }, {
                            default: _withCtx(() => [...(_cache[36] || (_cache[36] = [
                              _createTextVNode("强制绑定", -1)
                            ]))]),
                            _: 1
                          }, 8, ["loading", "disabled"]),
                          _createVNode(_component_VBtn, {
                            color: "warning",
                            "prepend-icon": "mdi-calendar-edit",
                            variant: "tonal",
                            size: "small",
                            loading: identifierBusy.value === 'year',
                            disabled: Boolean(identifierBusy.value),
                            onClick: _cache[10] || (_cache[10] = $event => (runIdentifierAction('year')))
                          }, {
                            default: _withCtx(() => [...(_cache[37] || (_cache[37] = [
                              _createTextVNode("修正年份", -1)
                            ]))]),
                            _: 1
                          }, 8, ["loading", "disabled"])
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
                        class: "mt-2 sp-identifier-history"
                      }, {
                        default: _withCtx(() => [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(identifierRecords.value, (record) => {
                            return (_openBlock(), _createBlock(_component_VListItem, {
                              key: record.mode + '-' + record.candidate_title + '-' + record.created_at,
                              class: "sp-identifier-record"
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
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_40, [
                                  _createElementVNode("div", _hoisted_41, [
                                    _createElementVNode("strong", null, _toDisplayString(identifierModeText(record.mode)) + "：", 1),
                                    _createTextVNode(_toDisplayString(record.candidate_title || record.title || '-'), 1)
                                  ]),
                                  _createElementVNode("div", _hoisted_42, _toDisplayString(record.message || '-') + " / " + _toDisplayString(record.created_at || '-'), 1),
                                  (record.rule)
                                    ? (_openBlock(), _createElementBlock("code", _hoisted_43, _toDisplayString(record.rule), 1))
                                    : _createCommentVNode("", true)
                                ])
                              ]),
                              _: 2
                            }, 1024))
                          }), 128))
                        ]),
                        _: 1
                      }))
                    : (_openBlock(), _createElementBlock("div", _hoisted_44, "暂无识别词记录"))
                ], 512), [
                  [_vShow, activeGroup.value === 'identifier']
                ]),
                _withDirectives(_createElementVNode("div", _hoisted_45, [
                  _createElementVNode("div", _hoisted_46, [
                    _cache[39] || (_cache[39] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "规则修改记录", -1)),
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
                          default: _withCtx(() => [...(_cache[38] || (_cache[38] = [
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
                    : (_openBlock(), _createElementBlock("div", _hoisted_47, "暂无记录")),
                  _createElementVNode("section", _hoisted_48, [
                    _createElementVNode("div", _hoisted_49, [
                      _cache[41] || (_cache[41] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "自定义官组与平台", -1)),
                      _createVNode(_component_VSpacer),
                      _createVNode(_component_VBtn, {
                        color: "primary",
                        "prepend-icon": "mdi-content-save",
                        variant: "flat",
                        size: "small",
                        loading: savingRuleDictionary.value,
                        disabled: !ruleDictionaryDirty.value,
                        onClick: saveRuleDictionary
                      }, {
                        default: _withCtx(() => [...(_cache[40] || (_cache[40] = [
                          _createTextVNode(" 保存词表 ", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      _createVNode(_component_VBtn, {
                        icon: "mdi-refresh",
                        variant: "text",
                        size: "small",
                        loading: ruleDictionaryLoading.value,
                        onClick: loadRuleDictionary
                      }, null, 8, ["loading"])
                    ]),
                    (ruleDictionaryError.value)
                      ? (_openBlock(), _createBlock(_component_VAlert, {
                          key: 0,
                          type: "error",
                          density: "compact",
                          variant: "tonal",
                          class: "mb-3 text-caption",
                          closable: "",
                          "onClick:close": _cache[11] || (_cache[11] = $event => (ruleDictionaryError.value = ''))
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(ruleDictionaryError.value), 1)
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true),
                    (ruleDictionaryHint.value)
                      ? (_openBlock(), _createBlock(_component_VAlert, {
                          key: 1,
                          type: "success",
                          density: "compact",
                          variant: "tonal",
                          class: "mb-3 text-caption",
                          closable: "",
                          "onClick:close": _cache[12] || (_cache[12] = $event => (ruleDictionaryHint.value = ''))
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(ruleDictionaryHint.value), 1)
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true),
                    _createElementVNode("div", _hoisted_50, [
                      _createElementVNode("div", _hoisted_51, [
                        _cache[42] || (_cache[42] = _createElementVNode("div", { class: "sp-field-info" }, [
                          _createElementVNode("div", { class: "sp-field-label" }, "自定义官组"),
                          _createElementVNode("div", { class: "sp-field-hint" }, "每行或逗号分隔；候选标题命中后，在网页与 Telegram 的调整规则中显示“添加官组”。")
                        ], -1)),
                        _createElementVNode("div", _hoisted_52, [
                          _createVNode(_component_VCombobox, {
                            modelValue: config.custom_release_groups,
                            "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.custom_release_groups) = $event)),
                            label: "官组关键词",
                            variant: "outlined",
                            density: "compact",
                            multiple: "",
                            chips: "",
                            "closable-chips": "",
                            clearable: "",
                            "hide-details": "",
                            rounded: "lg"
                          }, null, 8, ["modelValue"])
                        ])
                      ]),
                      _createElementVNode("div", _hoisted_53, [
                        _cache[43] || (_cache[43] = _createElementVNode("div", { class: "sp-field-info" }, [
                          _createElementVNode("div", { class: "sp-field-label" }, "自定义平台"),
                          _createElementVNode("div", { class: "sp-field-hint" }, "每行或逗号分隔；候选标题命中后，在网页与 Telegram 的调整规则中显示“添加平台”。")
                        ], -1)),
                        _createElementVNode("div", _hoisted_54, [
                          _createVNode(_component_VCombobox, {
                            modelValue: config.custom_platforms,
                            "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.custom_platforms) = $event)),
                            label: "平台关键词",
                            variant: "outlined",
                            density: "compact",
                            multiple: "",
                            chips: "",
                            "closable-chips": "",
                            clearable: "",
                            "hide-details": "",
                            rounded: "lg"
                          }, null, 8, ["modelValue"])
                        ])
                      ])
                    ])
                  ])
                ], 512), [
                  [_vShow, activeGroup.value === 'rules']
                ]),
                _withDirectives(_createElementVNode("div", _hoisted_55, [
                  _createElementVNode("div", _hoisted_56, [
                    _cache[45] || (_cache[45] = _createElementVNode("div", { class: "sp-section-title mb-0" }, "F4通知目标面板", -1)),
                    _createVNode(_component_VSpacer),
                    _createVNode(_component_VBtn, {
                      color: "primary",
                      "prepend-icon": "mdi-content-save",
                      variant: "flat",
                      size: "small",
                      loading: savingF4.value,
                      disabled: !f4Dirty.value,
                      onClick: saveF4Actions
                    }, {
                      default: _withCtx(() => [...(_cache[44] || (_cache[44] = [
                        _createTextVNode("保存系统通知目标", -1)
                      ]))]),
                      _: 1
                    }, 8, ["loading", "disabled"]),
                    _createVNode(_component_VBtn, {
                      icon: "mdi-refresh",
                      variant: "text",
                      size: "small",
                      loading: f4Loading.value,
                      onClick: loadF4Options
                    }, null, 8, ["loading"])
                  ]),
                  (f4Error.value)
                    ? (_openBlock(), _createBlock(_component_VAlert, {
                        key: 0,
                        type: "error",
                        density: "compact",
                        variant: "tonal",
                        class: "mb-3 text-caption",
                        closable: "",
                        "onClick:close": _cache[15] || (_cache[15] = $event => (f4Error.value = ''))
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(f4Error.value), 1)
                        ]),
                        _: 1
                      }))
                    : _createCommentVNode("", true),
                  (f4Hint.value)
                    ? (_openBlock(), _createBlock(_component_VAlert, {
                        key: 1,
                        type: "info",
                        density: "compact",
                        variant: "tonal",
                        class: "mb-3 text-caption",
                        closable: "",
                        "onClick:close": _cache[16] || (_cache[16] = $event => (f4Hint.value = ''))
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(f4Hint.value), 1)
                        ]),
                        _: 1
                      }))
                    : _createCommentVNode("", true),
                  _createElementVNode("section", _hoisted_57, [
                    _cache[47] || (_cache[47] = _createElementVNode("div", { class: "sp-section-title" }, "1. 系统通知目标（资源入库 / 资源下载 / 订阅）", -1)),
                    _createElementVNode("div", _hoisted_58, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(f4Rows.value, (row) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: row.type,
                          class: "sp-field-row"
                        }, [
                          _createElementVNode("div", _hoisted_59, [
                            _createElementVNode("div", _hoisted_60, _toDisplayString(row.label), 1),
                            _cache[46] || (_cache[46] = _createElementVNode("div", { class: "sp-field-hint" }, "控制 MoviePilot 该类型系统通知的投递目标；发群组表示按各通知渠道开关发送到群。", -1))
                          ]),
                          _createElementVNode("div", _hoisted_61, [
                            _createVNode(_component_VSelect, {
                              modelValue: row.action,
                              "onUpdate:modelValue": $event => ((row.action) = $event),
                              items: f4OptionItems.value,
                              label: "通知目标",
                              "item-title": "title",
                              "item-value": "value",
                              density: "compact",
                              variant: "outlined",
                              "hide-details": "",
                              rounded: "lg",
                              "no-data-text": "无可用选项"
                            }, null, 8, ["modelValue", "onUpdate:modelValue", "items"])
                          ])
                        ]))
                      }), 128))
                    ])
                  ]),
                  _createElementVNode("section", _hoisted_62, [
                    _cache[51] || (_cache[51] = _createElementVNode("div", { class: "sp-section-title" }, "2. 订阅用户通知映射（SubscribePlus 诊断通知）", -1)),
                    _createElementVNode("div", _hoisted_63, [
                      _createElementVNode("div", _hoisted_64, [
                        _cache[48] || (_cache[48] = _createElementVNode("div", { class: "sp-field-info" }, [
                          _createElementVNode("div", { class: "sp-field-label" }, "未单独配置的订阅用户默认目标"),
                          _createElementVNode("div", { class: "sp-field-hint" }, "所有未在下方映射表中指定目标的订阅通知，发往此处选择的目标；留空则发到默认群组。")
                        ], -1)),
                        _createElementVNode("div", _hoisted_65, [
                          _createVNode(_component_VSelect, {
                            modelValue: defaultNotifyTargets.value,
                            "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((defaultNotifyTargets).value = $event)),
                            items: notifyTargetOptions.value,
                            label: "默认通知目标",
                            "item-title": "title",
                            "item-value": "value",
                            placeholder: "默认：群组",
                            density: "compact",
                            variant: "outlined",
                            "hide-details": "",
                            rounded: "lg",
                            multiple: "",
                            chips: "",
                            "closable-chips": "",
                            clearable: "",
                            "no-data-text": "无可用通知目标"
                          }, null, 8, ["modelValue", "items"])
                        ])
                      ]),
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(notifyRuleRows.value, (row, index) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: row.uid,
                          class: "sp-field-row"
                        }, [
                          _createElementVNode("div", _hoisted_66, [
                            _createVNode(_component_VSelect, {
                              modelValue: row.username,
                              "onUpdate:modelValue": $event => ((row.username) = $event),
                              items: notifyUsernameOptions.value,
                              label: "用户订阅",
                              placeholder: "选择订阅归属用户",
                              density: "compact",
                              variant: "outlined",
                              "hide-details": "",
                              rounded: "lg",
                              clearable: "",
                              "no-data-text": "无可用订阅用户"
                            }, null, 8, ["modelValue", "onUpdate:modelValue", "items"])
                          ]),
                          _createElementVNode("div", _hoisted_67, [
                            _createVNode(_component_VSelect, {
                              modelValue: row.targets,
                              "onUpdate:modelValue": $event => ((row.targets) = $event),
                              items: notifyTargetOptions.value,
                              label: "通知目标",
                              "item-title": "title",
                              "item-value": "value",
                              placeholder: "默认：群组",
                              density: "compact",
                              variant: "outlined",
                              "hide-details": "",
                              rounded: "lg",
                              multiple: "",
                              chips: "",
                              "closable-chips": "",
                              clearable: "",
                              "no-data-text": "无可用通知目标"
                            }, null, 8, ["modelValue", "onUpdate:modelValue", "items"])
                          ]),
                          _createElementVNode("div", _hoisted_68, [
                            _createVNode(_component_VBtn, {
                              icon: "mdi-delete-outline",
                              color: "error",
                              variant: "text",
                              size: "small",
                              onClick: $event => (removeNotifyRuleRow(index))
                            }, null, 8, ["onClick"])
                          ])
                        ]))
                      }), 128))
                    ]),
                    _createElementVNode("div", _hoisted_69, [
                      _createVNode(_component_VBtn, {
                        color: "primary",
                        "prepend-icon": "mdi-plus",
                        variant: "tonal",
                        size: "small",
                        disabled: !availableNotifyUsernames.value.length,
                        onClick: addNotifyRuleRow
                      }, {
                        default: _withCtx(() => [...(_cache[49] || (_cache[49] = [
                          _createTextVNode(" 添加映射 ", -1)
                        ]))]),
                        _: 1
                      }, 8, ["disabled"]),
                      _createVNode(_component_VBtn, {
                        color: "primary",
                        "prepend-icon": "mdi-content-save",
                        variant: "flat",
                        size: "small",
                        loading: savingNotifyRules.value,
                        disabled: !notifyRulesDirty.value,
                        onClick: saveNotifyRules
                      }, {
                        default: _withCtx(() => [...(_cache[50] || (_cache[50] = [
                          _createTextVNode("保存映射", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      (!availableNotifyUsernames.value.length && notifyUsernameOptions.value.length)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_70, " 所有订阅用户均已配置 "))
                        : _createCommentVNode("", true)
                    ])
                  ])
                ], 512), [
                  [_vShow, activeGroup.value === 'notify_rules']
                ]),
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(configGroupKeys, (groupKey) => {
                  return _withDirectives(_createElementVNode("div", {
                    key: groupKey,
                    class: "sp-pane"
                  }, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(sectionsOf(groupKey), (section, sIdx) => {
                      return (_openBlock(), _createElementBlock("section", {
                        key: section.title,
                        class: "sp-config-section"
                      }, [
                        _createElementVNode("div", _hoisted_71, _toDisplayString((sIdx + 1) + '. ' + section.title), 1),
                        _createElementVNode("div", _hoisted_72, [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(section.fields, (field) => {
                            return (_openBlock(), _createElementBlock("div", {
                              key: field.key,
                              class: "sp-field-row"
                            }, [
                              _createElementVNode("div", _hoisted_73, [
                                _createElementVNode("div", _hoisted_74, _toDisplayString(field.label), 1),
                                (field.hint)
                                  ? (_openBlock(), _createElementBlock("div", _hoisted_75, _toDisplayString(field.hint), 1))
                                  : _createCommentVNode("", true)
                              ]),
                              _createElementVNode("div", {
                                class: _normalizeClass(["sp-field-control", 'sp-ctl-' + field.type])
                              }, [
                                (field.type === 'switch')
                                  ? (_openBlock(), _createBlock(_component_VSwitch, {
                                      key: 0,
                                      modelValue: config[field.key],
                                      "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                      color: field.color || 'primary',
                                      inset: "",
                                      "hide-details": "",
                                      density: "compact"
                                    }, null, 8, ["modelValue", "onUpdate:modelValue", "color"]))
                                  : (field.type === 'number')
                                    ? (_openBlock(), _createBlock(_component_VTextField, {
                                        key: 1,
                                        modelValue: config[field.key],
                                        "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                        modelModifiers: { number: true },
                                        type: "number",
                                        min: field.min,
                                        variant: "outlined",
                                        density: "compact",
                                        "hide-details": "",
                                        rounded: "lg"
                                      }, null, 8, ["modelValue", "onUpdate:modelValue", "min"]))
                                    : (field.type === 'text')
                                      ? (_openBlock(), _createBlock(_component_VTextField, {
                                          key: 2,
                                          modelValue: config[field.key],
                                          "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                          variant: "outlined",
                                          density: "compact",
                                          "hide-details": "auto",
                                          rounded: "lg",
                                          "error-messages": field.validate === 'cron' ? cronError.value : ''
                                        }, null, 8, ["modelValue", "onUpdate:modelValue", "error-messages"]))
                                      : (field.type === 'select')
                                        ? (_openBlock(), _createBlock(_component_VSelect, {
                                            key: 3,
                                            modelValue: config[field.key],
                                            "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                            items: field.options,
                                            "item-title": "title",
                                            "item-value": "value",
                                            variant: "outlined",
                                            density: "compact",
                                            "hide-details": "",
                                            rounded: "lg"
                                          }, null, 8, ["modelValue", "onUpdate:modelValue", "items"]))
                                        : (field.type === 'multiselect')
                                          ? (_openBlock(), _createBlock(_component_VSelect, {
                                              key: 4,
                                              modelValue: config[field.key],
                                              "onUpdate:modelValue": $event => ((config[field.key]) = $event),
                                              items: optionsFor(field),
                                              "item-title": "title",
                                              "item-value": "value",
                                              variant: "outlined",
                                              density: "compact",
                                              multiple: "",
                                              chips: "",
                                              "closable-chips": "",
                                              clearable: field.clearable,
                                              "hide-details": "",
                                              rounded: "lg"
                                            }, null, 8, ["modelValue", "onUpdate:modelValue", "items", "clearable"]))
                                          : _createCommentVNode("", true)
                              ], 2)
                            ]))
                          }), 128))
                        ]),
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
                      ]))
                    }), 128))
                  ]), [
                    [_vShow, activeGroup.value === groupKey]
                  ])
                }), 64))
              ]),
              _createElementVNode("aside", _hoisted_76, [
                _createElementVNode("section", _hoisted_77, [
                  _createElementVNode("div", _hoisted_78, [
                    _createVNode(_component_VIcon, {
                      icon: "mdi-clock-outline",
                      color: "primary",
                      size: "20"
                    }),
                    _cache[52] || (_cache[52] = _createTextVNode("运行节奏", -1))
                  ]),
                  _createElementVNode("div", _hoisted_79, [
                    _createVNode(_component_VIcon, { icon: "mdi-calendar-sync-outline" }),
                    _cache[53] || (_cache[53] = _createElementVNode("span", null, "定时扫描", -1)),
                    _createElementVNode("strong", null, _toDisplayString(scanScheduleText.value), 1)
                  ]),
                  _createElementVNode("div", _hoisted_80, [
                    _createVNode(_component_VIcon, { icon: "mdi-calendar-alert-outline" }),
                    _cache[54] || (_cache[54] = _createElementVNode("span", null, "超期检测", -1)),
                    _createElementVNode("strong", null, "播出后 " + _toDisplayString(config.delay_days) + " 天", 1)
                  ]),
                  _createElementVNode("div", _hoisted_81, [
                    _createVNode(_component_VIcon, { icon: "mdi-message-processing-outline" }),
                    _cache[55] || (_cache[55] = _createElementVNode("span", null, "通知方式", -1)),
                    _cache[56] || (_cache[56] = _createElementVNode("strong", null, "队列逐条", -1))
                  ]),
                  _createElementVNode("div", _hoisted_82, [
                    _createVNode(_component_VIcon, { icon: "mdi-database-clock-outline" }),
                    _cache[57] || (_cache[57] = _createElementVNode("span", null, "候选缓存", -1)),
                    _createElementVNode("strong", null, _toDisplayString(candidateCacheText.value), 1)
                  ])
                ]),
                _createVNode(_component_VDivider, { class: "my-3" }),
                _createElementVNode("section", _hoisted_83, [
                  _createElementVNode("div", _hoisted_84, [
                    _createVNode(_component_VIcon, {
                      icon: "mdi-chart-box-outline",
                      color: "primary",
                      size: "20"
                    }),
                    _cache[58] || (_cache[58] = _createTextVNode("运行概况", -1))
                  ]),
                  _createElementVNode("div", _hoisted_85, [
                    _createVNode(_component_VIcon, { icon: "mdi-history" }),
                    _cache[59] || (_cache[59] = _createElementVNode("span", null, "最近扫描", -1)),
                    _createElementVNode("strong", null, _toDisplayString(lastScanText.value), 1)
                  ]),
                  _createElementVNode("div", _hoisted_86, [
                    _createVNode(_component_VIcon, { icon: "mdi-timer-sand" }),
                    _cache[60] || (_cache[60] = _createElementVNode("span", null, "待处理", -1)),
                    _createElementVNode("strong", null, _toDisplayString(items.value.length), 1)
                  ]),
                  _createElementVNode("div", _hoisted_87, [
                    _createVNode(_component_VIcon, { icon: "mdi-download-box-outline" }),
                    _cache[61] || (_cache[61] = _createElementVNode("span", null, "候选资源", -1)),
                    _createElementVNode("strong", null, _toDisplayString(candidateTotal.value), 1)
                  ]),
                  _createElementVNode("div", _hoisted_88, [
                    _createVNode(_component_VIcon, { icon: "mdi-toggle-switch-outline" }),
                    _cache[62] || (_cache[62] = _createElementVNode("span", null, "已启用功能", -1)),
                    _createElementVNode("strong", null, _toDisplayString(enabledFeatureCount.value) + "/6", 1)
                  ])
                ])
              ])
            ])
          ])
        ])
      ]),
      _: 1
    }),
    _createVNode(_component_VBottomSheet, {
      modelValue: mobileGroupSheet.value,
      "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((mobileGroupSheet).value = $event))
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCard, {
          rounded: "t-xl",
          class: "sp-sheet"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-subtitle-1 font-weight-bold px-4 pt-4" }, {
              default: _withCtx(() => [...(_cache[63] || (_cache[63] = [
                _createTextVNode("选择配置分组", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardText, { class: "px-3 pb-4" }, {
              default: _withCtx(() => [
                _createVNode(_component_VList, {
                  density: "comfortable",
                  nav: ""
                }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_unref(groups), (item) => {
                      return (_openBlock(), _createBlock(_component_VListItem, {
                        key: item.key,
                        active: activeGroup.value === item.key,
                        color: "primary",
                        rounded: "lg",
                        class: "sp-sheet-item",
                        onClick: $event => {activeGroup.value = item.key; mobileGroupSheet.value = false;}
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_VIcon, {
                            icon: item.icon
                          }, null, 8, ["icon"])
                        ]),
                        append: _withCtx(() => [
                          (activeGroup.value === item.key)
                            ? (_openBlock(), _createBlock(_component_VIcon, {
                                key: 0,
                                icon: "mdi-check",
                                color: "primary"
                              }))
                            : (item.key === 'overview' && items.value.length)
                              ? (_openBlock(), _createBlock(_component_VChip, {
                                  key: 1,
                                  size: "x-small",
                                  color: "warning",
                                  variant: "tonal"
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(items.value.length), 1)
                                  ]),
                                  _: 1
                                }))
                              : _createCommentVNode("", true)
                        ]),
                        default: _withCtx(() => [
                          _createVNode(_component_VListItemTitle, { class: "font-weight-medium" }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.title), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_VListItemSubtitle, { class: "text-caption" }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.desc), 1)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        _: 2
                      }, 1032, ["active", "onClick"]))
                    }), 128))
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_VDialog, {
      modelValue: previewDialog.value,
      "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((previewDialog).value = $event)),
      "max-width": "720"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCard, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [...(_cache[64] || (_cache[64] = [
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
                  ? (_openBlock(), _createElementBlock("div", _hoisted_89, [
                      _cache[65] || (_cache[65] = _createElementVNode("div", { class: "text-caption text-medium-emphasis mb-2" }, "请选择要添加的官组、平台关键词或 PT 站点", -1)),
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
                  ? (_openBlock(), _createElementBlock("div", _hoisted_90, [
                      (preview.value.selected_text)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_91, "已选择：" + _toDisplayString(preview.value.selected_text), 1))
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
                  onClick: _cache[19] || (_cache[19] = $event => (previewDialog.value = false))
                }, {
                  default: _withCtx(() => [...(_cache[66] || (_cache[66] = [
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
                  default: _withCtx(() => [...(_cache[67] || (_cache[67] = [
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
    }, 8, ["modelValue"]),
    _createVNode(_component_VSnackbar, {
      modelValue: saveSnackbar.value,
      "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((saveSnackbar).value = $event)),
      color: "success",
      location: "top",
      timeout: 2200
    }, {
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(saveMessage.value), 1)
      ]),
      _: 1
    }, 8, ["modelValue"])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-c840a16c"]]);

export { Config as default };
