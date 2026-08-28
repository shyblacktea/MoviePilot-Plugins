import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {toDisplayString:_toDisplayString,createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,resolveComponent:_resolveComponent,createBlock:_createBlock,createVNode:_createVNode,normalizeStyle:_normalizeStyle,renderList:_renderList,Fragment:_Fragment,createTextVNode:_createTextVNode,normalizeClass:_normalizeClass,createStaticVNode:_createStaticVNode} = await importShared('vue');


const _hoisted_1 = { class: "asa-dash" };
const _hoisted_2 = {
  key: 0,
  class: "asa-dash__head"
};
const _hoisted_3 = { class: "asa-dash__head-copy" };
const _hoisted_4 = { class: "asa-dash__title" };
const _hoisted_5 = {
  key: 0,
  class: "asa-dash__subtitle"
};
const _hoisted_6 = {
  key: 1,
  class: "asa-dash__body"
};
const _hoisted_7 = {
  key: 2,
  class: "asa-dash__state"
};
const _hoisted_8 = { class: "asa-state-ico asa-state-ico--error" };
const _hoisted_9 = { class: "asa-state__text" };
const _hoisted_10 = {
  key: 3,
  class: "asa-dash__state"
};
const _hoisted_11 = { class: "asa-state-ico" };
const _hoisted_12 = { class: "asa-state__text" };
const _hoisted_13 = { class: "asa-state__hint" };
const _hoisted_14 = {
  key: 4,
  class: "asa-dash__body"
};
const _hoisted_15 = { class: "asa-donut" };
const _hoisted_16 = { class: "asa-donut__hole" };
const _hoisted_17 = { class: "asa-donut__num" };
const _hoisted_18 = { class: "asa-donut__cap" };
const _hoisted_19 = { class: "asa-legend" };
const _hoisted_20 = { class: "asa-legend__label" };
const _hoisted_21 = { class: "asa-legend__val" };
const _hoisted_22 = { class: "asa-sources" };
const _hoisted_23 = { class: "asa-sources__head" };
const _hoisted_24 = { class: "asa-sources__title" };
const _hoisted_25 = { class: "asa-sources__count" };
const _hoisted_26 = { class: "asa-sources__chips" };
const _hoisted_27 = {
  key: 1,
  class: "asa-sources__empty"
};
const _hoisted_28 = {
  key: 0,
  class: "asa-recent"
};
const _hoisted_29 = { class: "asa-recent__head" };
const _hoisted_30 = { class: "asa-recent__list" };
const _hoisted_31 = ["src", "onError"];
const _hoisted_32 = {
  key: 1,
  class: "asa-recent__poster asa-recent__poster--ph"
};
const _hoisted_33 = { class: "asa-recent__meta" };
const _hoisted_34 = ["title"];
const _hoisted_35 = { class: "asa-recent__sub" };

const {computed,getCurrentInstance,onMounted,onUnmounted,reactive,ref} = await importShared('vue');


// --- 状态展示（color 内联，label 走 i18n）---
const PLUGIN = 'plugin/ManualSubscribeAssistantShy';

const _sfc_main = {
  __name: 'Dashboard',
  props: {
  config: { type: Object, default: () => ({}) },
  allowRefresh: { type: Boolean, default: true },
  api: { type: Object, default: () => ({}) },
},
  setup(__props) {

const STATUS_META = {
  subscribed: { color: 'success' },
  media_exists: { color: 'info' },
  subscription_exists: { color: 'primary' },
  filtered: { color: 'warning' },
  unrecognized: { color: 'blue-grey' },
  already_handled: { color: 'grey' },
  error: { color: 'error' },
};
const STAT_ORDER = ['subscribed', 'media_exists', 'subscription_exists', 'filtered', 'unrecognized', 'error'];

// --- i18n（内联，保持联邦块自包含）---
const MSG = {
  'zh-CN': {
    title: '手动订阅助手', subtitle: '订阅概览', cap: '累计处理', sources: '来源',
    enabledOf: '{a} / {b} 启用', noSources: '无可用来源', recent: '最近订阅',
    emptyText: '暂无订阅记录', emptyHint: '启用来源并运行后，这里会展示订阅统计',
    retry: '重试', refresh: '刷新', apiUnavailable: 'API 不可用', loadError: '数据加载失败：',
    'st.subscribed': '已订阅', 'st.media_exists': '媒体库已存在', 'st.subscription_exists': '订阅已存在',
    'st.filtered': '被过滤', 'st.unrecognized': '未识别', 'st.already_handled': '已处理', 'st.error': '异常',
  },
  'zh-TW': {
    title: '手動訂閱助手', subtitle: '訂閱概覽', cap: '累計處理', sources: '來源',
    enabledOf: '{a} / {b} 啟用', noSources: '無可用來源', recent: '最近訂閱',
    emptyText: '暫無訂閱記錄', emptyHint: '啟用來源並執行後，這裡會顯示訂閱統計',
    retry: '重試', refresh: '重新整理', apiUnavailable: 'API 不可用', loadError: '資料載入失敗：',
    'st.subscribed': '已訂閱', 'st.media_exists': '媒體庫已存在', 'st.subscription_exists': '訂閱已存在',
    'st.filtered': '被過濾', 'st.unrecognized': '未識別', 'st.already_handled': '已處理', 'st.error': '異常',
  },
  'en-US': {
    title: 'Manual Subscribe Assistant', subtitle: 'Overview', cap: 'Handled', sources: 'Sources',
    enabledOf: '{a} / {b} enabled', noSources: 'No sources', recent: 'Recent',
    emptyText: 'No subscriptions yet', emptyHint: 'Stats appear here once sources are enabled and run',
    retry: 'Retry', refresh: 'Refresh', apiUnavailable: 'API unavailable', loadError: 'Failed to load data: ',
    'st.subscribed': 'Subscribed', 'st.media_exists': 'In library', 'st.subscription_exists': 'Already subscribed',
    'st.filtered': 'Filtered', 'st.unrecognized': 'Unrecognized', 'st.already_handled': 'Handled', 'st.error': 'Error',
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

const props = __props;

const THEME_COLORS = { primary: 1, secondary: 1, success: 1, info: 1, warning: 1, error: 1 };

const loading = ref(true);
const error = ref('');
const byStatus = ref({});
const providers = ref([]);
const totalHandled = ref(0);
const recent = ref([]);
const failed = reactive({});
let timer = null;

const bordered = computed(() => props.config?.attrs?.border !== false);
// 仪表盘为固定部件，标题/子标题跟随语言（忽略后端 attrs 文本，仅沿用 border）
const title = computed(() => t('title'));
const subtitle = computed(() => t('subtitle'));
const refreshSecs = computed(() => {
  const v = Number(props.config?.attrs?.refresh);
  return Number.isFinite(v) && v > 0 ? v : 0
});

const enabledProviders = computed(() => providers.value.filter(p => p.enabled));

const segments = computed(() => {
  const src = byStatus.value || {};
  const rows = STAT_ORDER
    .map(key => ({ key, count: Number(src[key]) || 0, color: STATUS_META[key].color, label: t('st.' + key) }))
    .filter(r => r.count > 0);
  const sum = rows.reduce((acc, r) => acc + r.count, 0);
  return { rows, sum }
});

const donutStyle = computed(() => {
  const { rows, sum } = segments.value;
  if (!sum) return { background: 'rgba(var(--v-theme-on-surface), 0.08)' }
  let acc = 0;
  const stops = rows.map(r => {
    const start = (acc / sum) * 100;
    acc += r.count;
    const end = (acc / sum) * 100;
    return `${cssColor(r.color)} ${start}% ${end}%`
  });
  return { background: `conic-gradient(${stops.join(', ')})` }
});

function pct(count) {
  const sum = segments.value.sum;
  return sum ? Math.round((count / sum) * 100) : 0
}
function cssColor(name) {
  if (THEME_COLORS[name]) return `rgb(var(--v-theme-${name}))`
  if (name === 'blue-grey') return 'rgba(var(--v-theme-on-surface), 0.5)'
  return 'rgba(var(--v-theme-on-surface), 0.32)'
}
function qs(params) {
  return Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
    .join('&')
}

async function fetchData() {
  if (!props.api || typeof props.api.get !== 'function') {
    error.value = t('apiUnavailable');
    loading.value = false;
    return
  }
  loading.value = true;
  error.value = '';
  try {
    const [statusRes, historyRes] = await Promise.allSettled([
      props.api.get(`${PLUGIN}/status?${qs({ lang: locale.value })}`),
      props.api.get(`${PLUGIN}/subscribes`),
    ]);
    if (statusRes.status === 'fulfilled') {
      const s = statusRes.value || {};
      byStatus.value = s.stats?.by_status || {};
      totalHandled.value = Number(s.stats?.total) || 0;
      providers.value = Array.isArray(s.providers) ? s.providers : [];
    } else {
      throw statusRes.reason || new Error('status failed')
    }
    recent.value = historyRes.status === 'fulfilled' ? normalizeList(historyRes.value) : [];
  } catch (e) {
    error.value = t('loadError') + (e?.message || e);
  } finally {
    loading.value = false;
  }
}
function normalizeList(res) {
  if (Array.isArray(res)) return res
  if (res && Array.isArray(res.list)) return res.list
  if (res && Array.isArray(res.items)) return res.items
  return []
}
function refresh() { if (!loading.value) fetchData(); }
function setupTimer() {
  if (props.allowRefresh && refreshSecs.value) timer = setInterval(fetchData, refreshSecs.value * 1000);
}
onMounted(() => { fetchData(); setupTimer(); });
onUnmounted(() => timer && clearInterval(timer));

return (_ctx, _cache) => {
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_icon = _resolveComponent("v-icon");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", {
      class: _normalizeClass(["asa-dash__surface", { 'asa-dash__surface--flat': !bordered.value }])
    }, [
      (bordered.value)
        ? (_openBlock(), _createElementBlock("header", _hoisted_2, [
            _createElementVNode("div", _hoisted_3, [
              _createElementVNode("h3", _hoisted_4, _toDisplayString(title.value), 1),
              (subtitle.value)
                ? (_openBlock(), _createElementBlock("p", _hoisted_5, _toDisplayString(subtitle.value), 1))
                : _createCommentVNode("", true)
            ]),
            (__props.allowRefresh)
              ? (_openBlock(), _createBlock(_component_v_btn, {
                  key: 0,
                  loading: loading.value,
                  "aria-label": t('refresh'),
                  class: "asa-dash__refresh",
                  density: "comfortable",
                  icon: "mdi-refresh",
                  size: "small",
                  variant: "text",
                  onClick: refresh
                }, null, 8, ["loading", "aria-label"]))
              : _createCommentVNode("", true)
          ]))
        : _createCommentVNode("", true),
      (loading.value && !totalHandled.value && !error.value)
        ? (_openBlock(), _createElementBlock("div", _hoisted_6, _cache[0] || (_cache[0] = [
            _createStaticVNode("<div class=\"asa-skel asa-skel--ring\" data-v-1df59dc2></div><div class=\"asa-skel-lines\" data-v-1df59dc2><div class=\"asa-skel asa-skel--line\" data-v-1df59dc2></div><div class=\"asa-skel asa-skel--line\" data-v-1df59dc2></div><div class=\"asa-skel asa-skel--line short\" data-v-1df59dc2></div></div>", 2)
          ])))
        : (error.value)
          ? (_openBlock(), _createElementBlock("div", _hoisted_7, [
              _createElementVNode("div", _hoisted_8, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-alert-circle-outline",
                  size: "22"
                })
              ]),
              _createElementVNode("p", _hoisted_9, _toDisplayString(error.value), 1),
              _createElementVNode("button", {
                class: "asa-state__btn",
                type: "button",
                onClick: refresh
              }, _toDisplayString(t('retry')), 1)
            ]))
          : (!totalHandled.value)
            ? (_openBlock(), _createElementBlock("div", _hoisted_10, [
                _createElementVNode("div", _hoisted_11, [
                  _createVNode(_component_v_icon, {
                    icon: "mdi-playlist-star",
                    size: "22"
                  })
                ]),
                _createElementVNode("p", _hoisted_12, _toDisplayString(t('emptyText')), 1),
                _createElementVNode("p", _hoisted_13, _toDisplayString(t('emptyHint')), 1)
              ]))
            : (_openBlock(), _createElementBlock("div", _hoisted_14, [
                _createElementVNode("div", _hoisted_15, [
                  _createElementVNode("div", {
                    class: "asa-donut__ring",
                    style: _normalizeStyle(donutStyle.value)
                  }, [
                    _createElementVNode("div", _hoisted_16, [
                      _createElementVNode("span", _hoisted_17, _toDisplayString(totalHandled.value), 1),
                      _createElementVNode("span", _hoisted_18, _toDisplayString(t('cap')), 1)
                    ])
                  ], 4),
                  _createElementVNode("ul", _hoisted_19, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(segments.value.rows, (r) => {
                      return (_openBlock(), _createElementBlock("li", {
                        key: r.key,
                        class: "asa-legend__item"
                      }, [
                        _createElementVNode("span", {
                          class: "asa-legend__dot",
                          style: _normalizeStyle({ background: cssColor(r.color) })
                        }, null, 4),
                        _createElementVNode("span", _hoisted_20, _toDisplayString(r.label), 1),
                        _createElementVNode("span", _hoisted_21, _toDisplayString(r.count) + " · " + _toDisplayString(pct(r.count)) + "%", 1)
                      ]))
                    }), 128))
                  ])
                ]),
                _createElementVNode("div", _hoisted_22, [
                  _createElementVNode("div", _hoisted_23, [
                    _createElementVNode("span", _hoisted_24, _toDisplayString(t('sources')), 1),
                    _createElementVNode("span", _hoisted_25, _toDisplayString(t('enabledOf', { a: enabledProviders.value.length, b: providers.value.length })), 1)
                  ]),
                  _createElementVNode("div", _hoisted_26, [
                    (providers.value.length)
                      ? (_openBlock(true), _createElementBlock(_Fragment, { key: 0 }, _renderList(providers.value, (p) => {
                          return (_openBlock(), _createElementBlock("span", {
                            key: p.provider_id,
                            class: _normalizeClass(["asa-chip", { 'asa-chip--on': p.enabled }])
                          }, [
                            _createVNode(_component_v_icon, {
                              icon: p.enabled ? 'mdi-check-circle' : 'mdi-circle-outline',
                              size: "13"
                            }, null, 8, ["icon"]),
                            _createTextVNode(" " + _toDisplayString(p.provider_name || p.provider_id), 1)
                          ], 2))
                        }), 128))
                      : (_openBlock(), _createElementBlock("span", _hoisted_27, _toDisplayString(t('noSources')), 1))
                  ])
                ]),
                (recent.value.length)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_28, [
                      _createElementVNode("div", _hoisted_29, _toDisplayString(t('recent')), 1),
                      _createElementVNode("ul", _hoisted_30, [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(recent.value.slice(0, 5), (it) => {
                          return (_openBlock(), _createElementBlock("li", {
                            key: it.unique,
                            class: "asa-recent__item"
                          }, [
                            (it.poster && !failed[it.unique])
                              ? (_openBlock(), _createElementBlock("img", {
                                  key: 0,
                                  class: "asa-recent__poster",
                                  src: it.poster,
                                  alt: "",
                                  loading: "lazy",
                                  onError: $event => (failed[it.unique] = true)
                                }, null, 40, _hoisted_31))
                              : (_openBlock(), _createElementBlock("span", _hoisted_32, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-movie-open-outline",
                                    size: "16"
                                  })
                                ])),
                            _createElementVNode("div", _hoisted_33, [
                              _createElementVNode("span", {
                                class: "asa-recent__name",
                                title: it.title
                              }, _toDisplayString(it.title), 9, _hoisted_34),
                              _createElementVNode("span", _hoisted_35, _toDisplayString([it.year, it.type].filter(Boolean).join(' · ') || '—'), 1)
                            ])
                          ]))
                        }), 128))
                      ])
                    ]))
                  : _createCommentVNode("", true)
              ]))
    ], 2)
  ]))
}
}

};
const DashboardComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-1df59dc2"]]);

export { DashboardComponent as default };
