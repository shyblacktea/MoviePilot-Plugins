import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';
import { P as PluginTabs } from './PluginTabs-cpJDdtfb.js';

const {createElementVNode:_createElementVNode$3,resolveComponent:_resolveComponent$3,openBlock:_openBlock$3,createBlock:_createBlock$2,createCommentVNode:_createCommentVNode$3,withModifiers:_withModifiers,createElementBlock:_createElementBlock$3,createVNode:_createVNode$3,toDisplayString:_toDisplayString$3,createTextVNode:_createTextVNode$2,normalizeStyle:_normalizeStyle,renderList:_renderList$3,Fragment:_Fragment$3,renderSlot:_renderSlot,withCtx:_withCtx$2,normalizeClass:_normalizeClass$2} = await importShared('vue');


const _hoisted_1$3 = ["checked"];
const _hoisted_2$3 = { class: "mc__checkbox" };
const _hoisted_3$3 = { class: "mc__poster" };
const _hoisted_4$3 = ["src", "alt"];
const _hoisted_5$3 = {
  key: 1,
  class: "mc__ph"
};
const _hoisted_6$3 = { class: "mc__body" };
const _hoisted_7$3 = ["title"];
const _hoisted_8$2 = { class: "mc__meta" };
const _hoisted_9$2 = ["title"];
const _hoisted_10$2 = { class: "mc__row-k" };
const _hoisted_11$2 = { class: "mc__row-v" };

const {ref: ref$3} = await importShared('vue');



const _sfc_main$3 = {
  __name: 'MediaCard',
  props: {
  poster: { type: String, default: '' },
  name: { type: String, default: '' },
  // 元数据行：[{ icon, label, value }]，value 已由父级填好（缺失为「未知」）
  lines: { type: Array, default: () => [] },
  // 状态徽标：{ label, color, icon }
  status: { type: Object, default: null },
  selectable: { type: Boolean, default: false },
  selected: { type: Boolean, default: false },
  // 「更多」菜单按钮的无障碍名（父级按语言传入）
  moreLabel: { type: String, default: '更多' },
},
  emits: ['toggle'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;
const imgFailed = ref$3(false);

function onCardClick() {
  // 多选模式下，点整卡即切换选择（操作按钮区已 stop）
  if (props.selectable) emit('toggle');
}

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent$3("v-icon");
  const _component_v_btn = _resolveComponent$3("v-btn");
  const _component_v_list = _resolveComponent$3("v-list");
  const _component_v_menu = _resolveComponent$3("v-menu");

  return (_openBlock$3(), _createElementBlock$3("article", {
    class: _normalizeClass$2(['mc', { 'mc--selectable': __props.selectable, 'mc--selected': __props.selected }]),
    onClick: onCardClick
  }, [
    (__props.selectable)
      ? (_openBlock$3(), _createElementBlock$3("label", {
          key: 0,
          class: "mc__check",
          onClick: _cache[1] || (_cache[1] = _withModifiers(() => {}, ["stop"]))
        }, [
          _createElementVNode$3("input", {
            type: "checkbox",
            checked: __props.selected,
            onChange: _cache[0] || (_cache[0] = $event => (emit('toggle')))
          }, null, 40, _hoisted_1$3),
          _createElementVNode$3("span", _hoisted_2$3, [
            (__props.selected)
              ? (_openBlock$3(), _createBlock$2(_component_v_icon, {
                  key: 0,
                  icon: "mdi-check",
                  size: "13"
                }))
              : _createCommentVNode$3("", true)
          ])
        ]))
      : _createCommentVNode$3("", true),
    _createElementVNode$3("div", _hoisted_3$3, [
      (__props.poster && !imgFailed.value)
        ? (_openBlock$3(), _createElementBlock$3("img", {
            key: 0,
            src: __props.poster,
            alt: __props.name,
            class: "mc__img",
            loading: "lazy",
            onError: _cache[2] || (_cache[2] = $event => (imgFailed.value = true))
          }, null, 40, _hoisted_4$3))
        : (_openBlock$3(), _createElementBlock$3("div", _hoisted_5$3, [
            _createVNode$3(_component_v_icon, {
              icon: "mdi-movie-open-outline",
              size: "26"
            })
          ])),
      (__props.status)
        ? (_openBlock$3(), _createElementBlock$3("span", {
            key: 2,
            class: "mc__badge",
            style: _normalizeStyle({ background: __props.status.color })
          }, [
            _createVNode$3(_component_v_icon, {
              icon: __props.status.icon,
              size: "11"
            }, null, 8, ["icon"]),
            _createTextVNode$2(" " + _toDisplayString$3(__props.status.label), 1)
          ], 4))
        : _createCommentVNode$3("", true)
    ]),
    _createElementVNode$3("div", _hoisted_6$3, [
      _createElementVNode$3("div", {
        class: "mc__title",
        title: __props.name
      }, _toDisplayString$3(__props.name), 9, _hoisted_7$3),
      _createElementVNode$3("ul", _hoisted_8$2, [
        (_openBlock$3(true), _createElementBlock$3(_Fragment$3, null, _renderList$3(__props.lines, (ln, i) => {
          return (_openBlock$3(), _createElementBlock$3("li", {
            key: i,
            class: "mc__row",
            title: `${ln.label}：${ln.value}`
          }, [
            _createVNode$3(_component_v_icon, {
              icon: ln.icon,
              size: "13",
              class: "mc__row-ico"
            }, null, 8, ["icon"]),
            _createElementVNode$3("span", _hoisted_10$2, _toDisplayString$3(ln.label), 1),
            _createElementVNode$3("span", _hoisted_11$2, _toDisplayString$3(ln.value), 1)
          ], 8, _hoisted_9$2))
        }), 128))
      ])
    ]),
    (_ctx.$slots.actions && !__props.selectable)
      ? (_openBlock$3(), _createElementBlock$3("div", {
          key: 1,
          class: "mc__more",
          onClick: _cache[3] || (_cache[3] = _withModifiers(() => {}, ["stop"]))
        }, [
          _createVNode$3(_component_v_btn, {
            "aria-label": __props.moreLabel,
            class: "mc__more-btn",
            icon: "mdi-dots-horizontal",
            size: "small",
            variant: "text"
          }, null, 8, ["aria-label"]),
          _createVNode$3(_component_v_menu, {
            activator: "parent",
            location: "top end",
            "close-on-content-click": true
          }, {
            default: _withCtx$2(() => [
              _createVNode$3(_component_v_list, {
                class: "mc__more-list",
                density: "compact",
                nav: ""
              }, {
                default: _withCtx$2(() => [
                  _renderSlot(_ctx.$slots, "actions", {}, undefined, true)
                ]),
                _: 3
              })
            ]),
            _: 3
          })
        ]))
      : _createCommentVNode$3("", true)
  ], 2))
}
}

};
const MediaCard = /*#__PURE__*/_export_sfc(_sfc_main$3, [['__scopeId',"data-v-5c942846"]]);

const {renderList:_renderList$2,Fragment:_Fragment$2,openBlock:_openBlock$2,createElementBlock:_createElementBlock$2,toDisplayString:_toDisplayString$2,createCommentVNode:_createCommentVNode$2,resolveComponent:_resolveComponent$2,createVNode:_createVNode$2,createElementVNode:_createElementVNode$2,normalizeClass:_normalizeClass$1} = await importShared('vue');


const _hoisted_1$2 = {
  key: 0,
  class: "fp-item fp-item--search"
};
const _hoisted_2$2 = ["for"];
const _hoisted_3$2 = {
  key: 1,
  class: "fp-item fp-item--year"
};
const _hoisted_4$2 = ["for"];
const _hoisted_5$2 = { class: "fp-year" };
const _hoisted_6$2 = {
  key: 2,
  class: "fp-item fp-item--select"
};
const _hoisted_7$2 = ["for"];

const {useId} = await importShared('vue');

/**
 * 通用筛选面板（内联横排 / 弹窗堆叠两种布局）。
 *
 * 设计约定：`state` 是父级拥有的**响应式对象**，本组件按 `fields` 配置对其字段做
 * 就地赋值（单一数据源，避免 draft 拷贝在多层来回同步）；每次变更后 `emit('change', field)`，
 * 由父级决定副作用（历史→防抖重取；管理→客户端 computed 自动响应 + 复位页码）。
 * 「留空即不过滤（全部）」：搜索='' / 年份=null / 多选=[] / 单选=null。
 */

const _sfc_main$2 = {
  __name: 'FilterPanel',
  props: {
  // 响应式筛选状态对象（父级 reactive），本组件就地写入其字段
  state: { type: Object, required: true },
  // 字段配置：
  //  { type:'search',     key, label, placeholder }
  //  { type:'year-range', keyMin, keyMax, label, minText, maxText }
  //  { type:'select',     key, label, items:[{title,value}], multi, icon, allText }
  fields: { type: Array, default: () => [] },
  // 堆叠布局（弹窗内每字段独占一行并带标题），否则内联横排
  stacked: { type: Boolean, default: false },
},
  emits: ['change'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

// 为控件生成稳定唯一 id，供可见 <label for> 关联（无障碍：每个筛选控件有可区分的可访问名）
const uid = useId();
const fid = k => `${uid}-${k}`;

function set(key, value, field) {
  props.state[key] = value;
  emit('change', field);
}

// 空串/NaN → null（不过滤）；否则取整年份
function toYear(v) {
  if (v === null || v === undefined || v === '') return null
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : null
}

// 多选：v-select 清空时可能给 null，统一规整为数组；单选清空给 null
function normalize(v, field) {
  if (field.multi) return Array.isArray(v) ? v : (v == null ? [] : [v])
  return v ?? null
}

return (_ctx, _cache) => {
  const _component_v_text_field = _resolveComponent$2("v-text-field");
  const _component_v_select = _resolveComponent$2("v-select");

  return (_openBlock$2(), _createElementBlock$2("div", {
    class: _normalizeClass$1(["fp", { 'fp--stacked': __props.stacked }])
  }, [
    (_openBlock$2(true), _createElementBlock$2(_Fragment$2, null, _renderList$2(__props.fields, (field) => {
      return (_openBlock$2(), _createElementBlock$2(_Fragment$2, {
        key: field.key || field.keyMin
      }, [
        (field.type === 'search')
          ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_1$2, [
              (__props.stacked)
                ? (_openBlock$2(), _createElementBlock$2("label", {
                    key: 0,
                    class: "fp-label",
                    for: fid(field.key)
                  }, _toDisplayString$2(field.label), 9, _hoisted_2$2))
                : _createCommentVNode$2("", true),
              _createVNode$2(_component_v_text_field, {
                id: fid(field.key),
                "model-value": __props.state[field.key],
                "aria-label": field.label || field.placeholder,
                class: "fp-ctl",
                clearable: "",
                density: "compact",
                "hide-details": "",
                placeholder: field.placeholder,
                "prepend-inner-icon": "mdi-magnify",
                variant: "outlined",
                "onUpdate:modelValue": v => set(field.key, v || '', field)
              }, null, 8, ["id", "model-value", "aria-label", "placeholder", "onUpdate:modelValue"])
            ]))
          : (field.type === 'year-range')
            ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_3$2, [
                (__props.stacked)
                  ? (_openBlock$2(), _createElementBlock$2("label", {
                      key: 0,
                      class: "fp-label",
                      for: fid(field.keyMin)
                    }, _toDisplayString$2(field.label), 9, _hoisted_4$2))
                  : _createCommentVNode$2("", true),
                _createElementVNode$2("div", _hoisted_5$2, [
                  _createVNode$2(_component_v_text_field, {
                    id: fid(field.keyMin),
                    "model-value": __props.state[field.keyMin],
                    "aria-label": `${field.label} ${field.minText}`,
                    class: "fp-ctl fp-year__in",
                    clearable: "",
                    density: "compact",
                    "hide-details": "",
                    inputmode: "numeric",
                    placeholder: field.minText,
                    type: "number",
                    variant: "outlined",
                    "onUpdate:modelValue": v => set(field.keyMin, toYear(v), field)
                  }, null, 8, ["id", "model-value", "aria-label", "placeholder", "onUpdate:modelValue"]),
                  _cache[0] || (_cache[0] = _createElementVNode$2("span", { class: "fp-year__sep" }, "–", -1)),
                  _createVNode$2(_component_v_text_field, {
                    id: fid(field.keyMax),
                    "model-value": __props.state[field.keyMax],
                    "aria-label": `${field.label} ${field.maxText}`,
                    class: "fp-ctl fp-year__in",
                    clearable: "",
                    density: "compact",
                    "hide-details": "",
                    inputmode: "numeric",
                    placeholder: field.maxText,
                    type: "number",
                    variant: "outlined",
                    "onUpdate:modelValue": v => set(field.keyMax, toYear(v), field)
                  }, null, 8, ["id", "model-value", "aria-label", "placeholder", "onUpdate:modelValue"])
                ])
              ]))
            : (field.type === 'select')
              ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_6$2, [
                  (__props.stacked)
                    ? (_openBlock$2(), _createElementBlock$2("label", {
                        key: 0,
                        class: "fp-label",
                        for: fid(field.key)
                      }, _toDisplayString$2(field.label), 9, _hoisted_7$2))
                    : _createCommentVNode$2("", true),
                  _createVNode$2(_component_v_select, {
                    id: fid(field.key),
                    "model-value": __props.state[field.key],
                    "aria-label": field.label,
                    class: "fp-ctl",
                    chips: !!field.multi,
                    clearable: "",
                    "closable-chips": !!field.multi,
                    density: "compact",
                    "hide-details": "",
                    items: field.items,
                    "item-title": "title",
                    "item-value": "value",
                    label: __props.stacked ? undefined : field.label,
                    multiple: !!field.multi,
                    placeholder: field.allText,
                    "prepend-inner-icon": field.icon,
                    variant: "outlined",
                    "onUpdate:modelValue": v => set(field.key, normalize(v, field), field)
                  }, null, 8, ["id", "model-value", "aria-label", "chips", "closable-chips", "items", "label", "multiple", "placeholder", "prepend-inner-icon", "onUpdate:modelValue"])
                ]))
              : _createCommentVNode$2("", true)
      ], 64))
    }), 128))
  ], 2))
}
}

};
const FilterPanel = /*#__PURE__*/_export_sfc(_sfc_main$2, [['__scopeId',"data-v-f4f4c49b"]]);

const {toDisplayString:_toDisplayString$1,openBlock:_openBlock$1,createElementBlock:_createElementBlock$1,createCommentVNode:_createCommentVNode$1,createTextVNode:_createTextVNode$1,resolveComponent:_resolveComponent$1,withCtx:_withCtx$1,createVNode:_createVNode$1,createBlock:_createBlock$1,createElementVNode:_createElementVNode$1,renderList:_renderList$1,Fragment:_Fragment$1} = await importShared('vue');


const _hoisted_1$1 = { class: "sv" };
const _hoisted_2$1 = { class: "sv-tools" };
const _hoisted_3$1 = {
  key: 0,
  class: "sv-tools__badge"
};
const _hoisted_4$1 = {
  key: 0,
  class: "sv-batch"
};
const _hoisted_5$1 = { class: "sv-batch__count" };
const _hoisted_6$1 = {
  key: 2,
  class: "asa-grid"
};
const _hoisted_7$1 = {
  key: 3,
  class: "sv-empty"
};
const _hoisted_8$1 = { class: "sv-empty__ico" };
const _hoisted_9$1 = { class: "sv-empty__text" };
const _hoisted_10$1 = { class: "sv-empty__hint" };
const _hoisted_11$1 = {
  key: 4,
  class: "asa-grid"
};

const {computed: computed$1,getCurrentInstance: getCurrentInstance$1,onMounted: onMounted$2,reactive: reactive$1,ref: ref$2,watch: watch$1} = await importShared('vue');

const PLUGIN$1 = 'plugin/ManualSubscribeAssistantShy';

const _sfc_main$1 = {
  __name: 'SubscribeView',
  props: {
  api: { type: Object, default: () => ({}) },
  pageSize: { type: Number, default: 12 },
  page: { type: Number, default: 1 },
},
  emits: ['changed', 'update:page', 'update:pageCount'],
  setup(__props, { expose: __expose, emit: __emit }) {

const props = __props;
const emit = __emit;
const THEME_COLORS = { primary: 1, secondary: 1, success: 1, info: 1, warning: 1, error: 1 };

const STATE_META = {
  R: { color: 'success', icon: 'mdi-bell-ring-outline' },
  N: { color: 'info', icon: 'mdi-bell-plus-outline' },
  P: { color: 'warning', icon: 'mdi-bell-sleep-outline' },
  S: { color: 'grey', icon: 'mdi-pause-circle-outline' },
};

const MSG = {
  'zh-CN': {
    select: '多选', exitSelect: '退出多选', selectedN: '已选 {n} 项', searchPh: '搜索名称…',
    selPage: '选本页', selAll: '选全部（{n}）', selClear: '清除选择',
    resume: '恢复', pause: '暂停', unsub: '退订', cancel: '取消', ok: '确定', unknown: '未知', more: '更多',
    all: '全部', 'st.R': '订阅中', 'st.N': '新建', 'st.P': '待定', 'st.S': '已暂停',
    filter: '筛选', filterTitle: '筛选与搜索', filterType: '类型', filterStatus: '状态', filterYear: '发行年份',
    yearFrom: '起始年', yearTo: '结束年', filterAll: '全部', searchLabel: '搜索', applyFilter: '应用', resetFilter: '重置',
    clearFilters: '清除筛选', 'mt.movie': '电影', 'mt.tv': '电视剧',
    kType: '类型', kSource: '来源', kTime: '订阅时间', kYear: '发行年份', source: '手动订阅助手魔改版',
    emptyNone: '暂无本插件创建的订阅', emptyFiltered: '没有符合条件的订阅', emptyHint: '启用来源运行后，订阅会出现在这里',
    error: '获取订阅失败：', actionFailed: '操作失败：',
    confirmDelete: '确认退订选中的 {n} 个订阅？此操作不可撤销。',
    confirmPause: '确认暂停选中的 {n} 个订阅？', confirmResume: '确认恢复选中的 {n} 个订阅？',
    titleDelete: '退订确认', titlePause: '暂停确认', titleResume: '恢复确认',
  },
  'zh-TW': {
    select: '多選', exitSelect: '退出多選', selectedN: '已選 {n} 項', searchPh: '搜尋名稱…',
    selPage: '選本頁', selAll: '選全部（{n}）', selClear: '清除選擇',
    resume: '恢復', pause: '暫停', unsub: '退訂', cancel: '取消', ok: '確定', unknown: '未知', more: '更多',
    all: '全部', 'st.R': '訂閱中', 'st.N': '新建', 'st.P': '待定', 'st.S': '已暫停',
    filter: '篩選', filterTitle: '篩選與搜尋', filterType: '類型', filterStatus: '狀態', filterYear: '發行年份',
    yearFrom: '起始年', yearTo: '結束年', filterAll: '全部', searchLabel: '搜尋', applyFilter: '套用', resetFilter: '重設',
    clearFilters: '清除篩選', 'mt.movie': '電影', 'mt.tv': '電視劇',
    kType: '類型', kSource: '來源', kTime: '訂閱時間', kYear: '發行年份', source: '手動訂閱助手魔改版',
    emptyNone: '暫無本外掛建立的訂閱', emptyFiltered: '沒有符合條件的訂閱', emptyHint: '啟用來源執行後，訂閱會出現在這裡',
    error: '取得訂閱失敗：', actionFailed: '操作失敗：',
    confirmDelete: '確認退訂選中的 {n} 個訂閱？此操作不可復原。',
    confirmPause: '確認暫停選中的 {n} 個訂閱？', confirmResume: '確認恢復選中的 {n} 個訂閱？',
    titleDelete: '退訂確認', titlePause: '暫停確認', titleResume: '恢復確認',
  },
  'en-US': {
    select: 'Select', exitSelect: 'Done', selectedN: '{n} selected', searchPh: 'Search name…',
    selPage: 'This page', selAll: 'All ({n})', selClear: 'Clear',
    resume: 'Resume', pause: 'Pause', unsub: 'Unsubscribe', cancel: 'Cancel', ok: 'OK', unknown: 'Unknown', more: 'More',
    all: 'All', 'st.R': 'Active', 'st.N': 'New', 'st.P': 'Pending', 'st.S': 'Paused',
    filter: 'Filters', filterTitle: 'Filter & search', filterType: 'Type', filterStatus: 'Status', filterYear: 'Release year',
    yearFrom: 'From', yearTo: 'To', filterAll: 'All', searchLabel: 'Search', applyFilter: 'Apply', resetFilter: 'Reset',
    clearFilters: 'Clear filters', 'mt.movie': 'Movies', 'mt.tv': 'TV series',
    kType: 'Type', kSource: 'Source', kTime: 'Added', kYear: 'Year', source: 'Manual Subscribe Assistant',
    emptyNone: 'No subscriptions created by this plugin', emptyFiltered: 'No subscriptions match', emptyHint: 'Subscriptions appear here after sources run',
    error: 'Failed to load subscriptions: ', actionFailed: 'Action failed: ',
    confirmDelete: 'Unsubscribe {n} selected subscription(s)? This cannot be undone.',
    confirmPause: 'Pause {n} selected subscription(s)?', confirmResume: 'Resume {n} selected subscription(s)?',
    titleDelete: 'Confirm unsubscribe', titlePause: 'Confirm pause', titleResume: 'Confirm resume',
  },
};
const inst = getCurrentInstance$1();
const locale = computed$1(() => normLocale(inst?.appContext?.config?.globalProperties?.$i18n?.locale));
function normLocale(src) {
  const v = src && typeof src === 'object' && 'value' in src ? src.value : src;
  const s = String(v || '').toLowerCase();
  if (s.startsWith('en')) return 'en-US'
  if (s.includes('tw') || s.includes('hant') || s.includes('hk')) return 'zh-TW'
  return 'zh-CN'
}
function t(k, p) {
  let s = (MSG[locale.value] || MSG['zh-CN'])[k] ?? MSG['zh-CN'][k] ?? k;
  if (p) for (const key in p) s = s.replaceAll(`{${key}}`, p[key]);
  return s
}

const loading = ref$2(true);
const error = ref$2('');
const rows = ref$2([]);
// 统一筛选模型（管理）：关键词 / 发行年份范围 / 类型(单选) / 状态(多选)。
// 「留空即不过滤（全部）」：keyword='' / year=null / mtype=null / statuses=[]。桌面内联、移动弹窗共用；
// 弹窗编辑 draft 副本，点「应用」整体拷回（管理为客户端筛选，拷回即时生效）。
const emptyFilters = () => ({ keyword: '', yearMin: null, yearMax: null, mtype: null, statuses: [] });
function cloneFilters(s) {
  return { keyword: s.keyword, yearMin: s.yearMin, yearMax: s.yearMax, mtype: s.mtype, statuses: [...s.statuses] }
}
const filters = reactive$1(emptyFilters());
const draft = reactive$1(emptyFilters());
const filterDialog = ref$2(false);
const selectMode = ref$2(false);
const selected = reactive$1(new Set());
const acting = ref$2(false);
const confirm = reactive$1({ open: false, kind: 'delete', ids: [] });

const filtered = computed$1(() => {
  const kw = (filters.keyword || '').trim().toLowerCase();
  const { yearMin, yearMax, mtype, statuses } = filters;
  return rows.value.filter(r => {
    if (kw && !String(r.name || '').toLowerCase().includes(kw)) return false
    if (mtype && r.type !== mtype) return false
    if (statuses.length && !statuses.includes(r.state)) return false
    if (yearMin != null || yearMax != null) {
      const y = parseInt(r.year, 10);
      if (!Number.isFinite(y)) return false
      if (yearMin != null && y < yearMin) return false
      if (yearMax != null && y > yearMax) return false
    }
    return true
  })
});
const pageCount = computed$1(() => Math.max(1, Math.ceil(filtered.value.length / props.pageSize)));
const paged = computed$1(() => {
  const start = (props.page - 1) * props.pageSize;
  return filtered.value.slice(start, start + props.pageSize)
});
// 状态多选项：始终列出 4 态，带当前计数。
const stateItems = computed$1(() => {
  const counts = {};
  rows.value.forEach(r => { counts[r.state] = (counts[r.state] || 0) + 1; });
  return ['R', 'S', 'P', 'N'].map(k => ({ title: `${t('st.' + k)}${counts[k] ? ` (${counts[k]})` : ''}`, value: k }))
});
const typeItems = computed$1(() => [
  { title: t('mt.movie'), value: '电影' },
  { title: t('mt.tv'), value: '电视剧' },
]);
// FilterPanel 字段配置（管理）：类型单选、状态多选 + 发行年份范围 + 搜索。
const filterFields = computed$1(() => [
  { type: 'search', key: 'keyword', label: t('searchLabel'), placeholder: t('searchPh') },
  { type: 'year-range', keyMin: 'yearMin', keyMax: 'yearMax', label: t('filterYear'), minText: t('yearFrom'), maxText: t('yearTo') },
  { type: 'select', key: 'mtype', multi: false, items: typeItems.value, label: t('filterType'), icon: 'mdi-shape-outline', allText: t('filterAll') },
  { type: 'select', key: 'statuses', multi: true, items: stateItems.value, label: t('filterStatus'), icon: 'mdi-flag-outline', allText: t('filterAll') },
]);
const activeFilterCount = computed$1(() =>
  (filters.keyword ? 1 : 0) +
  (filters.yearMin != null || filters.yearMax != null ? 1 : 0) +
  (filters.mtype ? 1 : 0) + (filters.statuses.length ? 1 : 0));
const hasFilter = computed$1(() => activeFilterCount.value > 0);
const confirmTitle = computed$1(() => t({ delete: 'titleDelete', pause: 'titlePause', resume: 'titleResume' }[confirm.kind]));
const confirmText = computed$1(() => t({ delete: 'confirmDelete', pause: 'confirmPause', resume: 'confirmResume' }[confirm.kind], { n: confirm.ids.length }));

function cssColor(name) {
  if (THEME_COLORS[name]) return `rgb(var(--v-theme-${name}))`
  return 'rgba(var(--v-theme-on-surface), 0.45)'
}
function stateBadge(state) {
  const m = STATE_META[state] || { color: 'grey', icon: 'mdi-bell-outline' };
  const label = MSG['zh-CN']['st.' + state] ? t('st.' + state) : (state || t('unknown'));
  return { label, color: cssColor(m.color), icon: m.icon }
}
function cardLines(item) {
  return [
    { icon: 'mdi-shape-outline', label: t('kType'), value: item.type || t('unknown') },
    { icon: 'mdi-robot-outline', label: t('kSource'), value: t('source') },
    { icon: 'mdi-clock-outline', label: t('kTime'), value: item.date || t('unknown') },
    { icon: 'mdi-calendar', label: t('kYear'), value: item.year || t('unknown') },
  ]
}

function clearFilters() { Object.assign(filters, emptyFilters()); }
// 移动端筛选弹窗：打开拷入 draft，「应用」拷回，「重置」清空 draft。
function openFilterDialog() { Object.assign(draft, cloneFilters(filters)); filterDialog.value = true; }
function applyFilterDialog() { Object.assign(filters, cloneFilters(draft)); filterDialog.value = false; }
function resetDraft() { Object.assign(draft, emptyFilters()); }
function toggleSelectMode() { selectMode.value = !selectMode.value; if (!selectMode.value) selected.clear(); }
function toggleOne(id) { selected.has(id) ? selected.delete(id) : selected.add(id); }
function selectCurrentPage() { paged.value.forEach(r => selected.add(r.id)); }
function selectAll() { filtered.value.forEach(r => selected.add(r.id)); }
function askBatch(kind) { if (selected.size) { confirm.kind = kind; confirm.ids = [...selected]; confirm.open = true; } }
function askOne(kind, item) { confirm.kind = kind; confirm.ids = [item.id]; confirm.open = true; }

async function runConfirm() {
  acting.value = true;
  error.value = '';
  try {
    if (!props.api || typeof props.api.post !== 'function') throw new Error('API')
    if (confirm.kind === 'delete') {
      await props.api.post(`${PLUGIN$1}/subscribes/delete`, { ids: confirm.ids });
    } else {
      await props.api.post(`${PLUGIN$1}/subscribes/state`, { ids: confirm.ids, state: confirm.kind === 'pause' ? 'S' : 'R' });
    }
    confirm.ids.forEach(id => selected.delete(id));
    confirm.open = false;
    await fetchSubs();
    emit('changed');
  } catch (e) {
    error.value = t('actionFailed') + (e?.message || e);
  } finally {
    acting.value = false;
  }
}

async function fetchSubs() {
  loading.value = true;
  error.value = '';
  try {
    if (!props.api || typeof props.api.get !== 'function') throw new Error('API')
    const res = await props.api.get(`${PLUGIN$1}/subscribes`);
    rows.value = Array.isArray(res?.list) ? res.list : [];
  } catch (e) {
    error.value = t('error') + (e?.message || e);
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

// 向父级同步页数；筛选变化（含弹窗「应用」拷回）时请求父级复位到第 1 页。
watch$1(pageCount, v => emit('update:pageCount', v), { immediate: true });
watch$1(filters, () => emit('update:page', 1), { deep: true });

__expose({ reload: fetchSubs });
onMounted$2(fetchSubs);

return (_ctx, _cache) => {
  const _component_v_btn = _resolveComponent$1("v-btn");
  const _component_v_spacer = _resolveComponent$1("v-spacer");
  const _component_v_icon = _resolveComponent$1("v-icon");
  const _component_v_alert = _resolveComponent$1("v-alert");
  const _component_v_list_item = _resolveComponent$1("v-list-item");
  const _component_v_card_title = _resolveComponent$1("v-card-title");
  const _component_v_card_text = _resolveComponent$1("v-card-text");
  const _component_v_card_actions = _resolveComponent$1("v-card-actions");
  const _component_v_card = _resolveComponent$1("v-card");
  const _component_v_dialog = _resolveComponent$1("v-dialog");

  return (_openBlock$1(), _createElementBlock$1("div", _hoisted_1$1, [
    _createElementVNode$1("div", _hoisted_2$1, [
      _createVNode$1(_component_v_btn, {
        class: "sv-tools__trigger",
        color: hasFilter.value ? 'primary' : undefined,
        "prepend-icon": "mdi-filter-variant",
        size: "small",
        variant: hasFilter.value ? 'tonal' : 'outlined',
        onClick: openFilterDialog
      }, {
        default: _withCtx$1(() => [
          _createTextVNode$1(_toDisplayString$1(t('filter')) + " ", 1),
          (activeFilterCount.value)
            ? (_openBlock$1(), _createElementBlock$1("span", _hoisted_3$1, _toDisplayString$1(activeFilterCount.value), 1))
            : _createCommentVNode$1("", true)
        ]),
        _: 1
      }, 8, ["color", "variant"]),
      _createVNode$1(_component_v_spacer),
      (hasFilter.value)
        ? (_openBlock$1(), _createBlock$1(_component_v_btn, {
            key: 0,
            size: "small",
            variant: "text",
            onClick: clearFilters
          }, {
            default: _withCtx$1(() => [
              _createVNode$1(_component_v_icon, {
                icon: "mdi-filter-off-outline",
                start: ""
              }),
              _createTextVNode$1(_toDisplayString$1(t('clearFilters')), 1)
            ]),
            _: 1
          }))
        : _createCommentVNode$1("", true),
      _createVNode$1(_component_v_btn, {
        color: selectMode.value ? 'primary' : undefined,
        variant: selectMode.value ? 'flat' : 'tonal',
        size: "small",
        "prepend-icon": "mdi-checkbox-multiple-marked-outline",
        onClick: toggleSelectMode
      }, {
        default: _withCtx$1(() => [
          _createTextVNode$1(_toDisplayString$1(selectMode.value ? t('exitSelect') : t('select')), 1)
        ]),
        _: 1
      }, 8, ["color", "variant"])
    ]),
    (selectMode.value)
      ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_4$1, [
          _createElementVNode$1("span", _hoisted_5$1, _toDisplayString$1(t('selectedN', { n: selected.size })), 1),
          _createVNode$1(_component_v_btn, {
            size: "small",
            variant: "text",
            "prepend-icon": "mdi-checkbox-marked-outline",
            onClick: selectCurrentPage
          }, {
            default: _withCtx$1(() => [
              _createTextVNode$1(_toDisplayString$1(t('selPage')), 1)
            ]),
            _: 1
          }),
          _createVNode$1(_component_v_btn, {
            size: "small",
            variant: "text",
            "prepend-icon": "mdi-select-all",
            onClick: selectAll
          }, {
            default: _withCtx$1(() => [
              _createTextVNode$1(_toDisplayString$1(t('selAll', { n: filtered.value.length })), 1)
            ]),
            _: 1
          }),
          (selected.size)
            ? (_openBlock$1(), _createBlock$1(_component_v_btn, {
                key: 0,
                size: "small",
                variant: "text",
                onClick: _cache[0] || (_cache[0] = $event => (selected.clear()))
              }, {
                default: _withCtx$1(() => [
                  _createTextVNode$1(_toDisplayString$1(t('selClear')), 1)
                ]),
                _: 1
              }))
            : _createCommentVNode$1("", true),
          _createVNode$1(_component_v_spacer),
          _createVNode$1(_component_v_btn, {
            disabled: !selected.size,
            color: "success",
            size: "small",
            variant: "tonal",
            "prepend-icon": "mdi-play",
            onClick: _cache[1] || (_cache[1] = $event => (askBatch('resume')))
          }, {
            default: _withCtx$1(() => [
              _createTextVNode$1(_toDisplayString$1(t('resume')), 1)
            ]),
            _: 1
          }, 8, ["disabled"]),
          _createVNode$1(_component_v_btn, {
            disabled: !selected.size,
            color: "warning",
            size: "small",
            variant: "tonal",
            "prepend-icon": "mdi-pause",
            onClick: _cache[2] || (_cache[2] = $event => (askBatch('pause')))
          }, {
            default: _withCtx$1(() => [
              _createTextVNode$1(_toDisplayString$1(t('pause')), 1)
            ]),
            _: 1
          }, 8, ["disabled"]),
          _createVNode$1(_component_v_btn, {
            disabled: !selected.size,
            color: "error",
            size: "small",
            variant: "tonal",
            "prepend-icon": "mdi-bell-off-outline",
            onClick: _cache[3] || (_cache[3] = $event => (askBatch('delete')))
          }, {
            default: _withCtx$1(() => [
              _createTextVNode$1(_toDisplayString$1(t('unsub')), 1)
            ]),
            _: 1
          }, 8, ["disabled"])
        ]))
      : _createCommentVNode$1("", true),
    (error.value)
      ? (_openBlock$1(), _createBlock$1(_component_v_alert, {
          key: 1,
          class: "mb-3",
          density: "compact",
          type: "warning",
          variant: "tonal"
        }, {
          default: _withCtx$1(() => [
            _createTextVNode$1(_toDisplayString$1(error.value), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode$1("", true),
    (loading.value)
      ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_6$1, [
          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(__props.pageSize, (n) => {
            return (_openBlock$1(), _createElementBlock$1("div", {
              key: n,
              class: "asa-skel-card"
            }))
          }), 128))
        ]))
      : (!filtered.value.length)
        ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_7$1, [
            _createElementVNode$1("div", _hoisted_8$1, [
              _createVNode$1(_component_v_icon, {
                icon: "mdi-bell-outline",
                size: "30"
              })
            ]),
            _createElementVNode$1("p", _hoisted_9$1, _toDisplayString$1(hasFilter.value ? t('emptyFiltered') : t('emptyNone')), 1),
            _createElementVNode$1("p", _hoisted_10$1, _toDisplayString$1(t('emptyHint')), 1)
          ]))
        : (_openBlock$1(), _createElementBlock$1("div", _hoisted_11$1, [
            (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(paged.value, (item) => {
              return (_openBlock$1(), _createBlock$1(MediaCard, {
                key: item.id,
                poster: item.poster || '',
                name: item.name || t('unknown'),
                lines: cardLines(item),
                status: stateBadge(item.state),
                selectable: selectMode.value,
                selected: selected.has(item.id),
                "more-label": t('more'),
                onToggle: $event => (toggleOne(item.id))
              }, {
                actions: _withCtx$1(() => [
                  (item.state === 'S')
                    ? (_openBlock$1(), _createBlock$1(_component_v_list_item, {
                        key: 0,
                        "base-color": "success",
                        "prepend-icon": "mdi-play",
                        title: t('resume'),
                        onClick: $event => (askOne('resume', item))
                      }, null, 8, ["title", "onClick"]))
                    : (_openBlock$1(), _createBlock$1(_component_v_list_item, {
                        key: 1,
                        "base-color": "warning",
                        "prepend-icon": "mdi-pause",
                        title: t('pause'),
                        onClick: $event => (askOne('pause', item))
                      }, null, 8, ["title", "onClick"])),
                  _createVNode$1(_component_v_list_item, {
                    "base-color": "error",
                    "prepend-icon": "mdi-bell-off-outline",
                    title: t('unsub'),
                    onClick: $event => (askOne('delete', item))
                  }, null, 8, ["title", "onClick"])
                ]),
                _: 2
              }, 1032, ["poster", "name", "lines", "status", "selectable", "selected", "more-label", "onToggle"]))
            }), 128))
          ])),
    _createVNode$1(_component_v_dialog, {
      modelValue: confirm.open,
      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((confirm.open) = $event)),
      "max-width": "380"
    }, {
      default: _withCtx$1(() => [
        _createVNode$1(_component_v_card, null, {
          default: _withCtx$1(() => [
            _createVNode$1(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx$1(() => [
                _createTextVNode$1(_toDisplayString$1(confirmTitle.value), 1)
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_text, { class: "text-body-2" }, {
              default: _withCtx$1(() => [
                _createTextVNode$1(_toDisplayString$1(confirmText.value), 1)
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_actions, null, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_spacer),
                _createVNode$1(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[4] || (_cache[4] = $event => (confirm.open = false))
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode$1(_toDisplayString$1(t('cancel')), 1)
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_btn, {
                  color: confirm.kind === 'delete' ? 'error' : 'primary',
                  loading: acting.value,
                  variant: "flat",
                  onClick: runConfirm
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode$1(_toDisplayString$1(t('ok')), 1)
                  ]),
                  _: 1
                }, 8, ["color", "loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode$1(_component_v_dialog, {
      modelValue: filterDialog.value,
      "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((filterDialog).value = $event)),
      "max-width": "440",
      scrollable: ""
    }, {
      default: _withCtx$1(() => [
        _createVNode$1(_component_v_card, { class: "sv-filter-dlg" }, {
          default: _withCtx$1(() => [
            _createVNode$1(_component_v_card_title, { class: "sv-filter-dlg__title" }, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_icon, {
                  icon: "mdi-filter-variant",
                  size: "20"
                }),
                _createTextVNode$1(_toDisplayString$1(t('filterTitle')), 1)
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_text, { class: "sv-filter-dlg__body" }, {
              default: _withCtx$1(() => [
                _createVNode$1(FilterPanel, {
                  state: draft,
                  fields: filterFields.value,
                  stacked: ""
                }, null, 8, ["state", "fields"])
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_actions, null, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_btn, {
                  variant: "text",
                  onClick: resetDraft
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode$1(_toDisplayString$1(t('resetFilter')), 1)
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_spacer),
                _createVNode$1(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[6] || (_cache[6] = $event => (filterDialog.value = false))
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode$1(_toDisplayString$1(t('cancel')), 1)
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_btn, {
                  color: "primary",
                  variant: "flat",
                  onClick: applyFilterDialog
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode$1(_toDisplayString$1(t('applyFilter')), 1)
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
    }, 8, ["modelValue"])
  ]))
}
}

};
const SubscribeView = /*#__PURE__*/_export_sfc(_sfc_main$1, [['__scopeId',"data-v-107e9a60"]]);

const {onBeforeUnmount,onMounted: onMounted$1,ref: ref$1} = await importShared('vue');

function useMediaGrid({ gridSelector = ".asa-grid" } = {}) {
  const containerRef = ref$1(null);
  const cols = ref$1(1);
  let ro = null;
  let raf = 0;
  const timers = /* @__PURE__ */ new Set();
  function countColumns() {
    const c = containerRef.value;
    if (!c) return cols.value;
    const grid = c.querySelector(gridSelector);
    if (!grid) return cols.value;
    const tpl = getComputedStyle(grid).gridTemplateColumns || "";
    const n = tpl.split(" ").map((s) => s.trim()).filter((s) => s && s !== "0px" && s !== "none").length;
    return n || 1;
  }
  function measure() {
    cols.value = countColumns();
  }
  function scheduleMeasure() {
    if (typeof window === "undefined") return;
    if (raf) window.cancelAnimationFrame(raf);
    raf = window.requestAnimationFrame(() => {
      raf = 0;
      measure();
    });
  }
  onMounted$1(() => {
    if (typeof window === "undefined" || typeof ResizeObserver === "undefined") {
      measure();
      return;
    }
    ro = new ResizeObserver(() => scheduleMeasure());
    if (containerRef.value) ro.observe(containerRef.value);
    scheduleMeasure();
    for (const d of [120, 360, 800]) {
      const id = window.setTimeout(() => {
        timers.delete(id);
        measure();
      }, d);
      timers.add(id);
    }
  });
  onBeforeUnmount(() => {
    if (ro) {
      ro.disconnect();
      ro = null;
    }
    if (raf && typeof window !== "undefined") window.cancelAnimationFrame(raf);
    timers.forEach((id) => window.clearTimeout(id));
    timers.clear();
  });
  return { containerRef, cols, measure };
}

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,withCtx:_withCtx,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass,withKeys:_withKeys} = await importShared('vue');


const _hoisted_1 = { class: "asa-page" };
const _hoisted_2 = { class: "asa-pg-head" };
const _hoisted_3 = { class: "asa-pg-head__brand" };
const _hoisted_4 = { class: "asa-pg-head__logo" };
const _hoisted_5 = { class: "asa-pg-head__identity" };
const _hoisted_6 = { class: "asa-pg-head__crumbs" };
const _hoisted_7 = { class: "asa-pg-head__title" };
const _hoisted_8 = { class: "asa-pg-head__actions" };
const _hoisted_9 = {
  key: 0,
  class: "asa-pg-body"
};
const _hoisted_10 = { class: "asa-stats" };
const _hoisted_11 = ["onClick"];
const _hoisted_12 = { class: "asa-stat__num" };
const _hoisted_13 = { class: "asa-stat__label" };
const _hoisted_14 = { class: "asa-filters" };
const _hoisted_15 = {
  key: 0,
  class: "asa-filters__badge"
};
const _hoisted_16 = {
  key: 1,
  class: "asa-batch"
};
const _hoisted_17 = { class: "asa-batch__count" };
const _hoisted_18 = {
  key: 2,
  class: "asa-grid"
};
const _hoisted_19 = {
  key: 3,
  class: "asa-empty"
};
const _hoisted_20 = { class: "asa-empty__ico" };
const _hoisted_21 = { class: "asa-empty__text" };
const _hoisted_22 = { class: "asa-empty__hint" };
const _hoisted_23 = {
  key: 4,
  class: "asa-grid"
};
const _hoisted_24 = {
  key: 0,
  class: "asa-pg-foot__spacer",
  "aria-hidden": "true"
};
const _hoisted_25 = {
  key: 1,
  class: "asa-pg-foot__nav"
};
const _hoisted_26 = {
  key: 3,
  class: "asa-pg-foot__jump"
};
const _hoisted_27 = { class: "asa-foot-dlg__field" };
const _hoisted_28 = { class: "asa-foot-dlg__label" };
const _hoisted_29 = {
  key: 0,
  class: "asa-foot-dlg__field"
};
const _hoisted_30 = { class: "asa-foot-dlg__label" };
const _hoisted_31 = { class: "asa-foot-dlg__jump" };

const {computed,getCurrentInstance,nextTick,onMounted,reactive,ref,watch} = await importShared('vue');

const PLUGIN = 'plugin/ManualSubscribeAssistantShy';
const VIEW_KEY = 'asa.pageView';
const ROWS_KEY = 'asa.mobileRows';

const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  show_switch: { type: Boolean, default: true },
},
  emits: ['switch', 'close', 'action'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const THEME_COLORS = { primary: 1, secondary: 1, success: 1, info: 1, warning: 1, error: 1 };

const STATUS_META = {
  candidate: { color: 'primary', icon: 'mdi-movie-search-outline' },
  subscribed: { color: 'success', icon: 'mdi-check-circle' },
  filtered: { color: 'warning', icon: 'mdi-filter-remove-outline' },
  unrecognized: { color: 'error', icon: 'mdi-help-circle-outline' },
};
const STAT_ORDER = ['candidate', 'subscribed', 'filtered', 'unrecognized'];

const MSG = {
  'zh-CN': {
    plugin: '插件', appTitle: '手动订阅助手魔改版', title: '订阅管理', manageTitle: '订阅历史', config: '订阅配置',
    records: '共 {n} 条记录', refresh: '刷新', close: '关闭', searchPh: '搜索名称…',
    filterSource: '来源', filterStatus: '状态', filterType: '类型', clearFilters: '清除筛选',
    filter: '筛选', filterTitle: '筛选与搜索', filterYear: '发行年份', yearFrom: '起始年', yearTo: '结束年',
    filterAll: '全部', searchLabel: '搜索', applyFilter: '应用', resetFilter: '重置',
    'mt.movie': '电影', 'mt.tv': '剧集',
    select: '多选', exitSelect: '退出多选', selectedN: '已选 {n} 项', batchDelete: '批量删除',
    selPage: '选本页', selAll: '选全部（{n}）', selClear: '清除选择',
    emptyFiltered: '没有符合筛选条件的记录', emptyFilteredHint: '试试调整搜索或筛选条件',
    emptyNone: '暂无待处理候选', emptyNoneHint: '抓取来源后，候选会显示在这里，由你确认后创建订阅',
    confirmTitle: '删除确认', confirmDeleteN: '确认删除选中的 {n} 条记录？', cancel: '取消', delete: '删除',
    unknown: '未知', go: '跳转', perPage: '每页行数', pageOptions: '每页行数与跳转', jumpLabel: '跳转到第几页（共 {n} 页）',
    kType: '类型', kSource: '来源', kTime: '订阅时间', kYear: '发行年份',
    historyError: '获取历史记录失败：', deleteFailed: '删除失败：', apiUnavailable: 'API 不可用',
    subscribe: '手动订阅', subscribeFailed: '订阅失败：', deleteCandidate: '删除候选',
    'st.candidate': '待确认', 'st.subscribed': '已订阅', 'st.filtered': '被过滤', 'st.unrecognized': '未识别',
  },
  'zh-TW': {
    plugin: '外掛', appTitle: '手動訂閱助手魔改版', title: '訂閱管理', manageTitle: '訂閱歷史', config: '訂閱設定',
    records: '共 {n} 筆記錄', refresh: '重新整理', close: '關閉', searchPh: '搜尋名稱…',
    filterSource: '來源', filterStatus: '狀態', filterType: '類型', clearFilters: '清除篩選',
    filter: '篩選', filterTitle: '篩選與搜尋', filterYear: '發行年份', yearFrom: '起始年', yearTo: '結束年',
    filterAll: '全部', searchLabel: '搜尋', applyFilter: '套用', resetFilter: '重設',
    'mt.movie': '電影', 'mt.tv': '劇集',
    select: '多選', exitSelect: '退出多選', selectedN: '已選 {n} 項', batchDelete: '批量刪除',
    selPage: '選本頁', selAll: '選全部（{n}）', selClear: '清除選擇',
    emptyFiltered: '沒有符合篩選條件的記錄', emptyFilteredHint: '試試調整搜尋或篩選條件',
    emptyNone: '暫無待處理候選', emptyNoneHint: '抓取來源後，候選會顯示在這裡，由你確認後建立訂閱',
    confirmTitle: '刪除確認', confirmDeleteN: '確認刪除選中的 {n} 筆記錄？', cancel: '取消', delete: '刪除',
    unknown: '未知', go: '跳轉', perPage: '每頁筆數', pageOptions: '每頁筆數與跳轉', jumpLabel: '跳轉到第幾頁（共 {n} 頁）',
    kType: '類型', kSource: '來源', kTime: '訂閱時間', kYear: '發行年份',
    historyError: '取得歷史記錄失敗：', deleteFailed: '刪除失敗：', apiUnavailable: 'API 不可用',
    subscribe: '手動訂閱', subscribeFailed: '訂閱失敗：', deleteCandidate: '刪除候選',
    'st.candidate': '待確認', 'st.subscribed': '已訂閱', 'st.filtered': '被過濾', 'st.unrecognized': '未識別',
  },
  'en-US': {
    plugin: 'Plugin', appTitle: 'Manual Subscribe Assistant', title: 'Manage', manageTitle: 'History', config: 'Settings',
    records: '{n} records', refresh: 'Refresh', close: 'Close', searchPh: 'Search name…',
    filterSource: 'Source', filterStatus: 'Status', filterType: 'Type', clearFilters: 'Clear filters',
    filter: 'Filters', filterTitle: 'Filter & search', filterYear: 'Release year', yearFrom: 'From', yearTo: 'To',
    filterAll: 'All', searchLabel: 'Search', applyFilter: 'Apply', resetFilter: 'Reset',
    'mt.movie': 'Movies', 'mt.tv': 'TV series',
    select: 'Select', exitSelect: 'Done', selectedN: '{n} selected', batchDelete: 'Delete',
    selPage: 'This page', selAll: 'All ({n})', selClear: 'Clear',
    emptyFiltered: 'No records match the filters', emptyFilteredHint: 'Try adjusting the search or filters',
    emptyNone: 'No pending candidates', emptyNoneHint: 'Run a source, then confirm candidates here before subscribing',
    confirmTitle: 'Confirm delete', confirmDeleteN: 'Delete {n} selected record(s)?', cancel: 'Cancel', delete: 'Delete',
    unknown: 'Unknown', go: 'Go', perPage: 'Rows per page', pageOptions: 'Rows & jump', jumpLabel: 'Jump to page (of {n})',
    kType: 'Type', kSource: 'Source', kTime: 'Time', kYear: 'Year',
    historyError: 'Failed to load history: ', deleteFailed: 'Delete failed: ', apiUnavailable: 'API unavailable',
    subscribe: 'Subscribe', subscribeFailed: 'Subscribe failed: ', deleteCandidate: 'Delete candidate',
    'st.candidate': 'Pending', 'st.subscribed': 'Subscribed', 'st.filtered': 'Filtered', 'st.unrecognized': 'Unrecognized',
  },
};
const inst = getCurrentInstance();
const locale = computed(() => normLocale(inst?.appContext?.config?.globalProperties?.$i18n?.locale));
function normLocale(src) {
  const v = src && typeof src === 'object' && 'value' in src ? src.value : src;
  const s = String(v || '').toLowerCase();
  if (s.startsWith('en')) return 'en-US'
  if (s.includes('tw') || s.includes('hant') || s.includes('hk')) return 'zh-TW'
  return 'zh-CN'
}
function t(k, p) {
  let s = (MSG[locale.value] || MSG['zh-CN'])[k] ?? MSG['zh-CN'][k] ?? k;
  if (p) for (const key in p) s = s.replaceAll(`{${key}}`, p[key]);
  return s
}
function statusMeta(status) { return STATUS_META[status] || { color: 'grey', icon: 'mdi-help-circle-outline' } }
function statusLabel(status) { return STATUS_META[status] ? t('st.' + status) : (status || t('unknown')) }

const view = ref(readInitialView());
const loading = ref(true);
const error = ref('');
const items = ref([]);
const total = ref(0);
const page = ref(1);
const managePage = ref(1);
const manageCount = ref(1);
const jumpTo = ref(1);
const footDialog = ref(false);  // 移动端页脚「每页行数 + 跳转」弹窗
const statusCounts = ref({});
const providerNames = reactive({});
const providerList = ref([]);
// 统一筛选模型（历史）：关键词 / 发行年份范围 / 类型(多) / 状态(多) / 来源(多)。
// 「留空即不过滤（全部）」：keyword='' / year=null / 多选=[]。桌面内联、移动弹窗共用此对象；
// 弹窗编辑 draft 副本，点「应用」后整体拷回 filters，避免弹窗内每次输入都触发服务端重取。
const EMPTY_FILTERS = () => ({ keyword: '', yearMin: null, yearMax: null, mtypes: [], statuses: [], providers: [] });
function cloneFilters(s) {
  return { keyword: s.keyword, yearMin: s.yearMin, yearMax: s.yearMax,
    mtypes: [...s.mtypes], statuses: [...s.statuses], providers: [...s.providers] }
}
const filters = reactive(EMPTY_FILTERS());
const draft = reactive(EMPTY_FILTERS());
const filterDialog = ref(false);
const selectMode = ref(false);
const selected = reactive(new Set());
const selectingAll = ref(false);
const recognizing = reactive(new Set());  // 正在「重新识别」的记录 unique 集合（按钮 loading）
const confirm = reactive({ open: false, ids: [] });
const deletingBatch = ref(false);

// 一次性读取目标视图：仅当由「订阅配置」标签跳回时携带；读后即清，保证下次打开始终默认订阅历史。
function readInitialView() {
  try {
    const v = localStorage.getItem(VIEW_KEY);
    if (v === 'manage' || v === 'history') { localStorage.removeItem(VIEW_KEY); return v }
  } catch { /* ignore */ }
  return 'history'
}

const ROW_OPTIONS = [10, 25, 50, 100];
function readRows() {
  try { const n = parseInt(localStorage.getItem(ROWS_KEY), 10); return ROW_OPTIONS.includes(n) ? n : 10 } catch { return 10 }
}
const mobileRows = ref(readRows());

const { containerRef, cols, measure } = useMediaGrid();
// 单列（移动端）按用户所选行数分页；多列（桌面）锁 3 行、列数自适应。
const isSingleCol = computed(() => cols.value <= 1);
const pageSize = computed(() => (isSingleCol.value ? mobileRows.value : Math.max(cols.value * 3, 1)));

const showSwitch = computed(() => props.show_switch);
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));
const activePageCount = computed(() => (view.value === 'history' ? pageCount.value : manageCount.value));
// 移动端不锁死 total-visible → v-pagination 依据自身容器宽度自动截断（永远含首尾页）；桌面维持 5。
// 固定可见页码数（不依赖 ResizeObserver 自动截断，避免真机测量不准导致页码数字消失）；
// 每页行数/跳转已移入弹窗，页脚仅页码 + 设置按钮，空间充裕，固定 5 个不会溢出。
const paginationVisible = computed(() => 5);
const paginationSize = computed(() => (isSingleCol.value ? 'x-small' : 'small'));
const activeFilterCount = computed(() =>
  (filters.keyword ? 1 : 0) +
  (filters.yearMin != null || filters.yearMax != null ? 1 : 0) +
  (filters.mtypes.length ? 1 : 0) + (filters.statuses.length ? 1 : 0) + (filters.providers.length ? 1 : 0));
const hasFilter = computed(() => activeFilterCount.value > 0);
const tabDefs = computed(() => {
  const base = [
    { key: 'history', label: t('title'), icon: 'mdi-history' },
    { key: 'manage', label: t('manageTitle'), icon: 'mdi-bell-cog-outline' },
  ];
  if (showSwitch.value) base.push({ key: 'config', label: t('config'), icon: 'mdi-cog-outline' });
  return base
});
const statCards = computed(() =>
  STAT_ORDER.map(key => ({ key, label: t('st.' + key), color: STATUS_META[key].color, count: statusCounts.value[key] || 0 })));
const providerOptions = computed(() =>
  providerList.value.map(p => ({ title: p.provider_name || p.provider_id, value: p.provider_id })));
const statusSelectItems = computed(() => STAT_ORDER.map(key => ({ title: t('st.' + key), value: key })));
const typeSelectItems = computed(() => [
  { title: t('mt.movie'), value: '电影' },
  { title: t('mt.tv'), value: '电视剧' },
]);
// FilterPanel 字段配置（历史）：类型多选、状态多选、来源多选 + 发行年份范围 + 搜索。
const historyFilterFields = computed(() => [
  { type: 'search', key: 'keyword', label: t('searchLabel'), placeholder: t('searchPh') },
  { type: 'year-range', keyMin: 'yearMin', keyMax: 'yearMax', label: t('filterYear'), minText: t('yearFrom'), maxText: t('yearTo') },
  { type: 'select', key: 'mtypes', multi: true, items: typeSelectItems.value, label: t('filterType'), icon: 'mdi-shape-outline', allText: t('filterAll') },
  { type: 'select', key: 'statuses', multi: true, items: statusSelectItems.value, label: t('filterStatus'), icon: 'mdi-flag-outline', allText: t('filterAll') },
  { type: 'select', key: 'providers', multi: true, items: providerOptions.value, label: t('filterSource'), icon: 'mdi-filter-variant', allText: t('filterAll') },
]);

function providerName(pid) { return providerNames[pid] || pid || t('unknown') }
function cssColor(name) {
  if (THEME_COLORS[name]) return `rgb(var(--v-theme-${name}))`
  if (name === 'blue-grey') return 'rgba(var(--v-theme-on-surface), 0.55)'
  return 'rgba(var(--v-theme-on-surface), 0.4)'
}
function statusBadge(item) {
  const m = statusMeta(item.status);
  return { label: statusLabel(item.status), color: cssColor(m.color), icon: m.icon }
}
function cardLines(item) {
  return [
    { icon: 'mdi-shape-outline', label: t('kType'), value: item.type || t('unknown') },
    { icon: 'mdi-rss', label: t('kSource'), value: providerName(item.provider) },
    { icon: 'mdi-clock-outline', label: t('kTime'), value: item.time || t('unknown') },
    { icon: 'mdi-calendar', label: t('kYear'), value: item.year || t('unknown') },
  ]
}

function qs(params) {
  return Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
    .join('&')
}
function normalizeList(res) {
  if (Array.isArray(res)) return res
  if (res && Array.isArray(res.list)) return res.list
  if (res && Array.isArray(res.items)) return res.items
  if (res && Array.isArray(res.data)) return res.data
  return []
}

// 历史筛选 → 查询参数：多选以逗号连接（后端按逗号切分，向后兼容单值）；空数组/空值经 qs 过滤丢弃。
function historyQuery() {
  return {
    keyword: filters.keyword,
    provider: filters.providers.join(','),
    status: filters.statuses.join(','),
    mtype: filters.mtypes.join(','),
    year_min: filters.yearMin,
    year_max: filters.yearMax,
  }
}

let fetchSeq = 0;
async function fetchHistory(silent = false) {
  // 请求时序守卫：列数测量稳定/翻页会触发多次取数（不同 count/page），
  // 仅采纳最新一次的响应，丢弃过期响应（否则小 count 的旧响应可能覆盖大 count → 只剩 2 行）。
  const seq = ++fetchSeq;
  if (!silent) loading.value = true;
  error.value = '';
  try {
    if (!props.api || typeof props.api.get !== 'function') throw new Error(t('apiUnavailable'))
    const query = qs({ ...historyQuery(), page: page.value, count: pageSize.value });
    const res = await props.api.get(`${PLUGIN}/candidates?${query}`);
    if (seq !== fetchSeq) return
    items.value = normalizeList(res);
    total.value = Number(res?.total) || items.value.length;
    if (page.value > pageCount.value) { page.value = pageCount.value; }
  } catch (e) {
    if (seq !== fetchSeq) return
    error.value = t('historyError') + (e?.message || e);
    items.value = [];
    total.value = 0;
  } finally {
    if (seq === fetchSeq) { loading.value = false; emit('action'); }
  }
}

async function fetchStatus() {
  try {
    if (!props.api || typeof props.api.get !== 'function') return
    const res = await props.api.get(`${PLUGIN}/status?lang=${encodeURIComponent(locale.value)}`);
    statusCounts.value = res?.stats?.by_status || {};
    const list = Array.isArray(res?.providers) ? res.providers : [];
    providerList.value = list;
    list.forEach(p => { providerNames[p.provider_id] = p.provider_name || p.provider_id; });
  } catch {
    statusCounts.value = {};
  }
}

function onTab(key) {
  if (key === 'config') {
    try { localStorage.setItem(VIEW_KEY, view.value); } catch { /* ignore */ }
    emit('switch');
    return
  }
  view.value = key;
}
function reloadCurrent() {
  fetchStatus();
  if (view.value === 'history') fetchHistory();
}
function applyFilters() { page.value = 1; fetchHistory(); }
// 统计卡片点击：切换该状态在多选集合中的存在。
function toggleStatus(key) {
  const i = filters.statuses.indexOf(key);
  if (i >= 0) filters.statuses.splice(i, 1);
  else filters.statuses.push(key);
  applyFilters();
}
function clearFilters() { Object.assign(filters, EMPTY_FILTERS()); applyFilters(); }
// 移动端筛选弹窗：打开拷入 draft，「应用」拷回并重取，「重置」清空 draft。
function openFilterDialog() { Object.assign(draft, cloneFilters(filters)); filterDialog.value = true; }
function applyFilterDialog() { Object.assign(filters, cloneFilters(draft)); filterDialog.value = false; applyFilters(); }
function resetDraft() { Object.assign(draft, EMPTY_FILTERS()); }
function onPageChange() {
  fetchHistory(true);  // 静默翻页：不切换到骨架屏，避免容器闪烁/高度变形
  if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
}
function doJump() {
  const n = Math.min(Math.max(parseInt(jumpTo.value, 10) || 1, 1), activePageCount.value);
  if (view.value === 'history') {
    if (n !== page.value) { page.value = n; onPageChange(); }
  } else {
    managePage.value = n;
  }
}
function doJumpClose() { doJump(); footDialog.value = false; }

function toggleSelectMode() { selectMode.value = !selectMode.value; if (!selectMode.value) selected.clear(); }
function toggleOne(u) { selected.has(u) ? selected.delete(u) : selected.add(u); }
function selectCurrentPage() { items.value.forEach(it => it.candidate_id && selected.add(it.candidate_id)); }
async function selectAll() {
  // 选全部：拉取当前筛选下的所有 unique（大页量一次取回）后全选。
  selectingAll.value = true;
  try {
    if (!props.api || typeof props.api.get !== 'function') throw new Error(t('apiUnavailable'))
    const query = qs({ ...historyQuery(), page: 1, count: 100000 });
    const res = await props.api.get(`${PLUGIN}/candidates?${query}`);
    normalizeList(res).forEach(r => r.candidate_id && selected.add(r.candidate_id));
  } catch (e) {
    error.value = t('historyError') + (e?.message || e);
  } finally {
    selectingAll.value = false;
  }
}
function askDelete(ids) { if (ids && ids.length) { confirm.ids = [...ids]; confirm.open = true; } }

async function runDelete() {
  deletingBatch.value = true;
  error.value = '';
  try {
    if (!props.api || typeof props.api.post !== 'function') throw new Error(t('apiUnavailable'))
    await props.api.post(`${PLUGIN}/candidates/batch-delete`, { candidate_ids: confirm.ids });
    confirm.ids.forEach(u => selected.delete(u));
    confirm.open = false;
    await fetchStatus();
    await fetchHistory(true);
  } catch (e) {
    error.value = t('deleteFailed') + (e?.message || e);
  } finally {
    deletingBatch.value = false;
  }
}

function onRowsChange() {
  try { localStorage.setItem(ROWS_KEY, String(mobileRows.value)); } catch { /* ignore */ }
  page.value = 1; managePage.value = 1;
}

// 手动订阅候选：仅在用户点击后调用后端写入 MoviePilot 订阅。
async function subscribeCandidate(item) {
  if (!item || !item.candidate_id || recognizing.has(item.candidate_id)) return
  recognizing.add(item.candidate_id);
  error.value = '';
  try {
    if (!props.api || typeof props.api.post !== 'function') throw new Error(t('apiUnavailable'))
    const res = await props.api.post(`${PLUGIN}/candidates/subscribe`, { candidate: item });
    if (res && res.code === 0) {
      await fetchStatus();
      await fetchHistory(true);
    } else {
      error.value = t('subscribeFailed') + ((res && res.message) || '');
    }
  } catch (e) {
    error.value = t('subscribeFailed') + (e?.message || e);
  } finally {
    recognizing.delete(item.candidate_id);
  }
}

// 每页条数变化（列数变化或移动端改行数）→ 历史静默重取；订阅管理由 pageSize prop 响应式重切。
watch(pageSize, () => { if (view.value === 'history') fetchHistory(true); });
// 订阅管理页数变化时收敛当前页；切换视图后清空选择并重新测量网格列数。
watch(manageCount, c => { if (managePage.value > c) managePage.value = c; });
watch(view, () => { selectMode.value = false; selected.clear(); nextTick(() => measure()); });

onMounted(() => { fetchStatus(); fetchHistory(); });

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_pagination = _resolveComponent("v-pagination");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock("section", _hoisted_1, [
    _createElementVNode("header", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-rss",
            size: "20"
          })
        ]),
        _createElementVNode("div", _hoisted_5, [
          _createElementVNode("div", _hoisted_6, [
            _cache[17] || (_cache[17] = _createElementVNode("span", null, "MoviePilot", -1)),
            _createVNode(_component_v_icon, {
              icon: "mdi-chevron-right",
              size: "13"
            }),
            _createElementVNode("span", null, _toDisplayString(t('plugin')), 1)
          ]),
          _createElementVNode("h1", _hoisted_7, _toDisplayString(t('appTitle')), 1)
        ])
      ]),
      _createElementVNode("div", _hoisted_8, [
        _createVNode(_component_v_btn, {
          loading: loading.value,
          "aria-label": t('refresh'),
          icon: "mdi-refresh",
          size: "small",
          variant: "text",
          onClick: reloadCurrent
        }, null, 8, ["loading", "aria-label"]),
        _createVNode(_component_v_btn, {
          "aria-label": t('close'),
          icon: "mdi-close",
          size: "small",
          variant: "text",
          onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
        }, null, 8, ["aria-label"])
      ])
    ]),
    _createVNode(PluginTabs, {
      active: view.value,
      tabs: tabDefs.value,
      onSelect: onTab
    }, null, 8, ["active", "tabs"]),
    _createElementVNode("div", {
      class: "asa-pg-scroll",
      ref_key: "containerRef",
      ref: containerRef
    }, [
      (view.value === 'history')
        ? (_openBlock(), _createElementBlock("div", _hoisted_9, [
            (error.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  class: "mb-3",
                  density: "compact",
                  type: "warning",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createElementVNode("div", _hoisted_10, [
              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(statCards.value, (s) => {
                return (_openBlock(), _createElementBlock("button", {
                  key: s.key,
                  type: "button",
                  class: _normalizeClass(['asa-stat', `asa-stat--${s.color}`, { 'asa-stat--active': filters.statuses.includes(s.key) }]),
                  onClick: $event => (toggleStatus(s.key))
                }, [
                  _createElementVNode("span", _hoisted_12, _toDisplayString(s.count), 1),
                  _createElementVNode("span", _hoisted_13, _toDisplayString(s.label), 1)
                ], 10, _hoisted_11))
              }), 128))
            ]),
            _createElementVNode("div", _hoisted_14, [
              _createVNode(_component_v_btn, {
                class: "asa-filters__trigger",
                color: hasFilter.value ? 'primary' : undefined,
                "prepend-icon": "mdi-filter-variant",
                size: "small",
                variant: hasFilter.value ? 'tonal' : 'outlined',
                onClick: openFilterDialog
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(t('filter')) + " ", 1),
                  (activeFilterCount.value)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_15, _toDisplayString(activeFilterCount.value), 1))
                    : _createCommentVNode("", true)
                ]),
                _: 1
              }, 8, ["color", "variant"]),
              _createVNode(_component_v_spacer),
              (hasFilter.value)
                ? (_openBlock(), _createBlock(_component_v_btn, {
                    key: 0,
                    class: "asa-filters__clear",
                    size: "small",
                    variant: "text",
                    onClick: clearFilters
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_icon, {
                        icon: "mdi-filter-off-outline",
                        start: ""
                      }),
                      _createTextVNode(_toDisplayString(t('clearFilters')), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              _createVNode(_component_v_btn, {
                color: selectMode.value ? 'primary' : undefined,
                variant: selectMode.value ? 'flat' : 'tonal',
                size: "small",
                "prepend-icon": "mdi-checkbox-multiple-marked-outline",
                onClick: toggleSelectMode
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(selectMode.value ? t('exitSelect') : t('select')), 1)
                ]),
                _: 1
              }, 8, ["color", "variant"])
            ]),
            (selectMode.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
                  _createElementVNode("span", _hoisted_17, _toDisplayString(t('selectedN', { n: selected.size })), 1),
                  _createVNode(_component_v_btn, {
                    size: "small",
                    variant: "text",
                    "prepend-icon": "mdi-checkbox-marked-outline",
                    onClick: selectCurrentPage
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(t('selPage')), 1)
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_btn, {
                    size: "small",
                    variant: "text",
                    "prepend-icon": "mdi-select-all",
                    loading: selectingAll.value,
                    onClick: selectAll
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(t('selAll', { n: total.value })), 1)
                    ]),
                    _: 1
                  }, 8, ["loading"]),
                  (selected.size)
                    ? (_openBlock(), _createBlock(_component_v_btn, {
                        key: 0,
                        size: "small",
                        variant: "text",
                        onClick: _cache[1] || (_cache[1] = $event => (selected.clear()))
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(t('selClear')), 1)
                        ]),
                        _: 1
                      }))
                    : _createCommentVNode("", true),
                  _createVNode(_component_v_spacer),
                  _createVNode(_component_v_btn, {
                    disabled: !selected.size,
                    color: "error",
                    size: "small",
                    variant: "tonal",
                    "prepend-icon": "mdi-trash-can-outline",
                    onClick: _cache[2] || (_cache[2] = $event => (askDelete([...selected])))
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(t('batchDelete')), 1)
                    ]),
                    _: 1
                  }, 8, ["disabled"])
                ]))
              : _createCommentVNode("", true),
            (loading.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_18, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(pageSize.value, (n) => {
                    return (_openBlock(), _createElementBlock("div", {
                      key: n,
                      class: "asa-skel-card"
                    }))
                  }), 128))
                ]))
              : (!items.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
                    _createElementVNode("div", _hoisted_20, [
                      _createVNode(_component_v_icon, {
                        icon: hasFilter.value ? 'mdi-filter-off-outline' : 'mdi-playlist-star',
                        size: "30"
                      }, null, 8, ["icon"])
                    ]),
                    _createElementVNode("p", _hoisted_21, _toDisplayString(hasFilter.value ? t('emptyFiltered') : t('emptyNone')), 1),
                    _createElementVNode("p", _hoisted_22, _toDisplayString(hasFilter.value ? t('emptyFilteredHint') : t('emptyNoneHint')), 1),
                    (hasFilter.value)
                      ? (_openBlock(), _createBlock(_component_v_btn, {
                          key: 0,
                          size: "small",
                          variant: "tonal",
                          onClick: clearFilters
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(t('clearFilters')), 1)
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true)
                  ]))
                : (_openBlock(), _createElementBlock("div", _hoisted_23, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(items.value, (item) => {
                      return (_openBlock(), _createBlock(MediaCard, {
                        key: item.candidate_id,
                        poster: item.poster || '',
                        name: item.title || t('unknown'),
                        lines: cardLines(item),
                        status: statusBadge(item),
                        selectable: selectMode.value,
                        selected: selected.has(item.candidate_id),
                        "more-label": t('more'),
                        onToggle: $event => (toggleOne(item.candidate_id))
                      }, {
                        actions: _withCtx(() => [
                          (item.tmdb_url)
                            ? (_openBlock(), _createBlock(_component_v_list_item, {
                                key: 0,
                                "prepend-icon": "mdi-open-in-new",
                                title: "TMDB",
                                href: item.tmdb_url,
                                target: "_blank"
                              }, null, 8, ["href"]))
                            : _createCommentVNode("", true),
                          (item.bangumi_url)
                            ? (_openBlock(), _createBlock(_component_v_list_item, {
                                key: 1,
                                "prepend-icon": "mdi-open-in-new",
                                title: "Bangumi",
                                href: item.bangumi_url,
                                target: "_blank"
                              }, null, 8, ["href"]))
                            : _createCommentVNode("", true),
                          (item.status === 'candidate' && item.media_source && item.media_id)
                            ? (_openBlock(), _createBlock(_component_v_list_item, {
                                key: 2,
                                "base-color": "primary",
                                "prepend-icon": "mdi-bell-plus-outline",
                                title: t('subscribe'),
                                disabled: recognizing.has(item.candidate_id),
                                onClick: $event => (subscribeCandidate(item))
                              }, null, 8, ["title", "disabled", "onClick"]))
                            : _createCommentVNode("", true),
                          _createVNode(_component_v_list_item, {
                            "base-color": "error",
                            "prepend-icon": "mdi-trash-can-outline",
                            title: t('delete'),
                            onClick: $event => (askDelete([item.candidate_id]))
                          }, null, 8, ["title", "onClick"])
                        ]),
                        _: 2
                      }, 1032, ["poster", "name", "lines", "status", "selectable", "selected", "more-label", "onToggle"]))
                    }), 128))
                  ]))
          ]))
        : (_openBlock(), _createBlock(SubscribeView, {
            key: 1,
            class: "asa-pg-body",
            api: __props.api,
            "page-size": pageSize.value,
            page: managePage.value,
            "onUpdate:page": _cache[3] || (_cache[3] = $event => ((managePage).value = $event)),
            "onUpdate:pageCount": _cache[4] || (_cache[4] = v => manageCount.value = v),
            onChanged: fetchStatus
          }, null, 8, ["api", "page-size", "page"]))
    ], 512),
    (activePageCount.value > 1 || isSingleCol.value)
      ? (_openBlock(), _createElementBlock("footer", {
          key: 0,
          class: _normalizeClass(["asa-pg-foot", { 'asa-pg-foot--mobile': isSingleCol.value }])
        }, [
          (isSingleCol.value && activePageCount.value > 1)
            ? (_openBlock(), _createElementBlock("div", _hoisted_24))
            : _createCommentVNode("", true),
          (activePageCount.value > 1)
            ? (_openBlock(), _createElementBlock("div", _hoisted_25, [
                (view.value === 'history')
                  ? (_openBlock(), _createBlock(_component_v_pagination, {
                      key: 0,
                      modelValue: page.value,
                      "onUpdate:modelValue": [
                        _cache[5] || (_cache[5] = $event => ((page).value = $event)),
                        onPageChange
                      ],
                      "active-color": "primary",
                      density: "comfortable",
                      length: pageCount.value,
                      "total-visible": paginationVisible.value,
                      size: paginationSize.value
                    }, null, 8, ["modelValue", "length", "total-visible", "size"]))
                  : (_openBlock(), _createBlock(_component_v_pagination, {
                      key: 1,
                      modelValue: managePage.value,
                      "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((managePage).value = $event)),
                      "active-color": "primary",
                      density: "comfortable",
                      length: manageCount.value,
                      "total-visible": paginationVisible.value,
                      size: paginationSize.value
                    }, null, 8, ["modelValue", "length", "total-visible", "size"]))
              ]))
            : _createCommentVNode("", true),
          (isSingleCol.value)
            ? (_openBlock(), _createBlock(_component_v_btn, {
                key: 2,
                class: "asa-pg-foot__more",
                "aria-label": t('pageOptions'),
                icon: "mdi-tune-variant",
                size: "small",
                variant: "tonal",
                onClick: _cache[7] || (_cache[7] = $event => (footDialog.value = true))
              }, null, 8, ["aria-label"]))
            : _createCommentVNode("", true),
          (!isSingleCol.value && activePageCount.value > 10)
            ? (_openBlock(), _createElementBlock("div", _hoisted_26, [
                _createVNode(_component_v_text_field, {
                  modelValue: jumpTo.value,
                  "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((jumpTo).value = $event)),
                  modelModifiers: { number: true },
                  density: "compact",
                  "hide-details": "",
                  type: "number",
                  min: 1,
                  max: activePageCount.value,
                  variant: "outlined",
                  class: "asa-pg-foot__jf",
                  onKeyup: _withKeys(doJump, ["enter"])
                }, null, 8, ["modelValue", "max"]),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "tonal",
                  onClick: doJump
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('go')), 1)
                  ]),
                  _: 1
                })
              ]))
            : _createCommentVNode("", true),
          (!isSingleCol.value)
            ? (_openBlock(), _createBlock(_component_v_spacer, { key: 4 }))
            : _createCommentVNode("", true)
        ], 2))
      : _createCommentVNode("", true),
    _createVNode(_component_v_dialog, {
      modelValue: footDialog.value,
      "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((footDialog).value = $event)),
      "max-width": "340"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, { class: "asa-foot-dlg" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "asa-foot-dlg__title" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-tune-variant",
                  size: "20"
                }),
                _createTextVNode(_toDisplayString(t('pageOptions')), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, { class: "asa-foot-dlg__body" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_27, [
                  _createElementVNode("label", _hoisted_28, _toDisplayString(t('perPage')), 1),
                  _createVNode(_component_v_select, {
                    modelValue: mobileRows.value,
                    "onUpdate:modelValue": [
                      _cache[9] || (_cache[9] = $event => ((mobileRows).value = $event)),
                      onRowsChange
                    ],
                    items: ROW_OPTIONS,
                    density: "compact",
                    "hide-details": "",
                    variant: "outlined"
                  }, null, 8, ["modelValue"])
                ]),
                (activePageCount.value > 10)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_29, [
                      _createElementVNode("label", _hoisted_30, _toDisplayString(t('jumpLabel', { n: activePageCount.value })), 1),
                      _createElementVNode("div", _hoisted_31, [
                        _createVNode(_component_v_text_field, {
                          modelValue: jumpTo.value,
                          "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((jumpTo).value = $event)),
                          modelModifiers: { number: true },
                          class: "asa-foot-dlg__jf",
                          density: "compact",
                          "hide-details": "",
                          type: "number",
                          min: 1,
                          max: activePageCount.value,
                          variant: "outlined",
                          onKeyup: _withKeys(doJumpClose, ["enter"])
                        }, null, 8, ["modelValue", "max"]),
                        _createVNode(_component_v_btn, {
                          color: "primary",
                          variant: "flat",
                          onClick: doJumpClose
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(t('go')), 1)
                          ]),
                          _: 1
                        })
                      ])
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[11] || (_cache[11] = $event => (footDialog.value = false))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('close')), 1)
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
    _createVNode(_component_v_dialog, {
      modelValue: confirm.open,
      "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((confirm.open) = $event)),
      "max-width": "380"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(t('confirmTitle')), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, { class: "text-body-2" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(t('confirmDeleteN', { n: confirm.ids.length })), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[13] || (_cache[13] = $event => (confirm.open = false))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('cancel')), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "error",
                  loading: deletingBatch.value,
                  variant: "flat",
                  onClick: runDelete
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('delete')), 1)
                  ]),
                  _: 1
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: filterDialog.value,
      "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((filterDialog).value = $event)),
      "max-width": "440",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, { class: "asa-filter-dlg" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "asa-filter-dlg__title" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-filter-variant",
                  size: "20"
                }),
                _createTextVNode(_toDisplayString(t('filterTitle')), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, { class: "asa-filter-dlg__body" }, {
              default: _withCtx(() => [
                _createVNode(FilterPanel, {
                  state: draft,
                  fields: historyFilterFields.value,
                  stacked: ""
                }, null, 8, ["state", "fields"])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: resetDraft
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('resetFilter')), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[15] || (_cache[15] = $event => (filterDialog.value = false))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('cancel')), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  variant: "flat",
                  onClick: applyFilterDialog
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(t('applyFilter')), 1)
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
    }, 8, ["modelValue"])
  ]))
}
}

};
const PageComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-c1dc3878"]]);

export { PageComponent as default };
