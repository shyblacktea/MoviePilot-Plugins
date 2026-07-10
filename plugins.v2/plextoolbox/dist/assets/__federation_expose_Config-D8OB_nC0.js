import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, g as getPluginApi, p as postPluginApi } from './_plugin-vue_export-helper-DGGBqqkU.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,createElementVNode:_createElementVNode,createBlock:_createBlock,createCommentVNode:_createCommentVNode,vShow:_vShow,withDirectives:_withDirectives,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "ptb-config" };
const _hoisted_2 = { class: "ptb-body" };
const _hoisted_3 = { class: "ptb-nav" };
const _hoisted_4 = { class: "ptb-content" };
const _hoisted_5 = { class: "ptb-pane" };
const _hoisted_6 = { class: "ptb-pane" };
const _hoisted_7 = { class: "ptb-pane" };

const {computed,reactive,ref,onMounted} = await importShared('vue');

const helperDocUrl = 'https://github.com/shyblacktea/MoviePilot-Plugins/blob/main/plugins.v2/plextoolbox/helper/README.md';


const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: [Object, Function], default: null },
},
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const error = ref('');
const checking = ref(false);
const loadingSections = ref(false);
const helperInfo = ref('');
const sectionOptions = ref([]);
const activeTab = ref('proxy');

const tabs = [
  { key: 'proxy', title: '反向代理', icon: 'mdi-swap-horizontal-bold', desc: 'Plex 播放流 302 直链跳转' },
  { key: 'mediainfo', title: '媒体信息补全', icon: 'mdi-information-outline', desc: '为 STRM 条目补全编码/分辨率/音轨等媒体流信息' },
  { key: 'scrape', title: '目录匹配/刮削', icon: 'mdi-image-search-outline', desc: '一键取消匹配重读 NFO、缺封面交给 MP 刮削' },
];
const currentTab = computed(() => tabs.find(t => t.key === activeTab.value) || tabs[0]);

const config = reactive({
  enabled: false, proxy_enabled: false, plex_host: '', plex_token: '',
  host: '0.0.0.0', port: 32401, pin_rules: '', force_direct_play: true,
  mediainfo_enabled: false, plex_direct_host: '', helper_url: '', helper_token: '',
  emby_url: '', emby_apikey: '', use_emby: true,
  overwrite_streams: true, only_missing: true, concurrency: 3, sections: '', cron: '',
  webhook_enabled: false, dedup_window: 300, forward_episodes: 5,
  ...props.initialConfig,
});

const selectedSections = computed({
  get: () => (config.sections ? String(config.sections).split(',').map(s => s.trim()).filter(Boolean) : []),
  set: v => { config.sections = (v || []).join(','); },
});

const webhookUrl = computed(() => {
  const origin = (typeof window !== 'undefined' && window.location ? window.location.origin : '');
  return `${origin}/api/v1/plugin/PlexToolbox/webhook?apikey=<你的API_TOKEN>`
});

// ---- 目录匹配/刮削栏状态 ----
const scrapeSection = ref('');
const scrapeLimit = ref(0);
const busyKey = ref('');
const scrapeResult = ref(null);

function showScrape(type, text) {
  scrapeResult.value = { type, text };
}

async function doUnmatch(dryRun) {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  if (!dryRun && !window.confirm('确认对该媒体库执行取消匹配？条目将被打回未匹配并按当前 NFO 代理重读。')) return
  busyKey.value = dryRun ? 'unmatch_preview' : 'unmatch_run';
  scrapeResult.value = null;
  try {
    const res = await postPluginApi(props.api, 'unmatch', {
      section: scrapeSection.value, dry_run: dryRun,
      rematch: true, limit: Number(scrapeLimit.value) || 0,
    });
    if (!res?.success) { showScrape('error', res?.error || '操作失败'); return }
    if (dryRun) {
      showScrape('info', `预览：该库共 ${res.total_items} 个条目，将影响 ${res.will_affect} 个`);
    } else {
      showScrape('success', `已取消匹配 ${res.unmatched} 个，刷新重读 ${res.refreshed} 个，失败 ${res.failed} 个`);
    }
  } catch (e) {
    showScrape('error', String(e));
  } finally {
    busyKey.value = '';
  }
}

async function doScanCover() {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  busyKey.value = 'scan_cover';
  scrapeResult.value = null;
  try {
    const res = await postPluginApi(props.api, 'scan_cover', { section: scrapeSection.value });
    if (!res?.success) { showScrape('error', res?.error || '扫描失败'); return }
    const list = (res.missing || []).slice(0, 20).map(m => `· ${m.title}（${m.reason}）`).join('\n');
    showScrape('info', `已检查 ${res.checked} 个条目，缺封面 ${res.total} 个${list ? '：\n' + list : ''}`);
  } catch (e) {
    showScrape('error', String(e));
  } finally {
    busyKey.value = '';
  }
}

async function doScrape(dryRun) {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  if (!dryRun && !window.confirm('确认对缺封面条目执行 MoviePilot 刮削？将生成 NFO+封面文件。')) return
  busyKey.value = dryRun ? 'scrape_preview' : 'scrape_run';
  scrapeResult.value = null;
  try {
    const res = await postPluginApi(props.api, 'scrape', {
      section: scrapeSection.value, dry_run: dryRun,
      limit: Number(scrapeLimit.value) || 0, unmatch_after: false,
    });
    if (!res?.success) { showScrape('error', res?.error || '刮削失败'); return }
    if (dryRun) {
      const list = (res.targets || []).slice(0, 20).map(t => `· ${t.title} → ${t.dir}`).join('\n');
      showScrape('info', `待刮削 ${res.candidates} 个目录${list ? '：\n' + list : ''}`);
    } else {
      showScrape('success', `刮削成功 ${res.scraped} 个，已刷新 ${res.refreshed ?? 0} 个，失败 ${res.failed} 个`);
    }
  } catch (e) {
    showScrape('error', String(e));
  } finally {
    busyKey.value = '';
  }
}

async function doFixPoster(dryRun) {
  if (!scrapeSection.value) { showScrape('warning', '请先选择目标媒体库'); return }
  if (!dryRun && !window.confirm('确认为缺 poster.jpg 的条目执行补全？剧集优先复制季内海报，其余从 TMDB 下载。')) return
  busyKey.value = dryRun ? 'poster_preview' : 'poster_run';
  scrapeResult.value = null;
  try {
    const res = await postPluginApi(props.api, 'fix_poster', {
      section: scrapeSection.value, dry_run: dryRun,
      limit: Number(scrapeLimit.value) || 0,
    });
    if (!res?.success) { showScrape('error', res?.error || '操作失败'); return }
    if (dryRun) {
      const list = (res.targets || []).slice(0, 20).map(t => `· ${t.title}${t.tmdbid ? '' : '（无tmdbid）'} → ${t.dir}`).join('\n');
      showScrape('info', `已检查 ${res.checked} 个条目，缺 poster ${res.candidates} 个${list ? '：\n' + list : ''}`);
    } else {
      const fails = (res.details || []).filter(x => !x.ok).slice(0, 10).map(x => `· ${x.title}: ${x.error}`).join('\n');
      showScrape(res.failed ? 'warning' : 'success',
        `补全成功 ${res.fixed} 个（已刷新 ${res.refreshed}），失败 ${res.failed} 个${fails ? '：\n' + fails : ''}`);
    }
  } catch (e) {
    showScrape('error', String(e));
  } finally {
    busyKey.value = '';
  }
}

async function loadSections() {
  loadingSections.value = true;
  error.value = '';
  try {
    const res = await getPluginApi(props.api, 'sections');
    if (res?.success) {
      sectionOptions.value = (res.sections || []).map(s => ({ title: `${s.title}（${s.type}）`, value: String(s.key) }));
    } else {
      error.value = res?.error || '获取媒体库失败';
    }
  } catch (e) {
    error.value = String(e);
  } finally {
    loadingSections.value = false;
  }
}

async function checkHelper() {
  checking.value = true;
  error.value = '';
  helperInfo.value = '';
  try {
    const res = await getPluginApi(props.api, 'helper_check');
    if (res?.success) {
      helperInfo.value = res?.dbinfo?.db_path || '已连接';
    } else {
      error.value = res?.error || 'helper 检查失败';
    }
  } catch (e) {
    error.value = String(e);
  } finally {
    checking.value = false;
  }
}

function saveConfig() {
  emit('save', { ...config });
}

onMounted(() => {
  if (config.plex_token && (config.plex_direct_host || config.plex_host)) loadSections();
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
  const _component_VListItem = _resolveComponent("VListItem");
  const _component_VList = _resolveComponent("VList");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VTextarea = _resolveComponent("VTextarea");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VCardActions = _resolveComponent("VCardActions");
  const _component_VCard = _resolveComponent("VCard");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VCard, {
      flat: "",
      class: "ptb-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardItem, { class: "ptb-header" }, {
          prepend: _withCtx(() => [
            _createVNode(_component_VAvatar, {
              color: "primary",
              variant: "tonal",
              size: "44",
              rounded: "lg"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-plex",
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
              label: config.enabled ? '已启用' : '已停用'
            }, null, 8, ["modelValue", "label"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-h6" }, {
              default: _withCtx(() => [...(_cache[34] || (_cache[34] = [
                _createTextVNode("PLEX 工具箱", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(currentTab.value.desc), 1)
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
              class: "py-2"
            }, {
              default: _withCtx(() => [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(tabs, (item) => {
                  return _createVNode(_component_VListItem, {
                    key: item.key,
                    active: activeTab.value === item.key,
                    color: "primary",
                    rounded: "lg",
                    onClick: $event => (activeTab.value = item.key)
                  }, {
                    prepend: _withCtx(() => [
                      _createVNode(_component_VIcon, {
                        icon: item.icon
                      }, null, 8, ["icon"])
                    ]),
                    default: _withCtx(() => [
                      _createVNode(_component_VListItemTitle, null, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(item.title), 1)
                        ]),
                        _: 2
                      }, 1024)
                    ]),
                    _: 2
                  }, 1032, ["active", "onClick"])
                }), 64))
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
            _withDirectives(_createElementVNode("div", _hoisted_5, [
              _cache[35] || (_cache[35] = _createElementVNode("div", { class: "ptb-section-title" }, "302 反向代理", -1)),
              _createVNode(_component_VRow, null, {
                default: _withCtx(() => [
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.proxy_enabled,
                        "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.proxy_enabled) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "启用 302 反向代理"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.plex_host,
                        "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.plex_host) = $event)),
                        label: "Plex 服务器地址",
                        placeholder: "http://192.168.0.122:32400",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.plex_token,
                        "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.plex_token) = $event)),
                        label: "X-Plex-Token",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.host,
                        "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.host) = $event)),
                        label: "代理监听地址",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.port,
                        "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.port) = $event)),
                        modelModifiers: { number: true },
                        type: "number",
                        label: "代理监听端口",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.force_direct_play,
                        "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.force_direct_play) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "强制 DirectPlay（避免转码使直链失效）"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextarea, {
                        modelValue: config.pin_rules,
                        "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.pin_rules) = $event)),
                        label: "顶置路径规则（每行：路径前缀 => 目标URL）",
                        variant: "outlined",
                        density: "compact",
                        rows: "3",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              })
            ], 512), [
              [_vShow, activeTab.value === 'proxy']
            ]),
            _withDirectives(_createElementVNode("div", _hoisted_6, [
              _cache[40] || (_cache[40] = _createElementVNode("div", { class: "ptb-section-title" }, "STRM 媒体流信息补全", -1)),
              _createVNode(_component_VAlert, {
                type: "info",
                variant: "tonal",
                density: "compact",
                class: "mb-3 text-caption"
              }, {
                default: _withCtx(() => [
                  _cache[36] || (_cache[36] = _createTextVNode(" 媒体信息补全需先在 Plex 主机部署 helper 写库服务。 ", -1)),
                  _createElementVNode("a", {
                    href: helperDocUrl,
                    target: "_blank",
                    rel: "noopener",
                    class: "ptb-doc-link"
                  }, "查看部署说明"),
                  _createVNode(_component_VIcon, {
                    icon: "mdi-open-in-new",
                    size: "12",
                    class: "ml-1"
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_VRow, null, {
                default: _withCtx(() => [
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.mediainfo_enabled,
                        "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.mediainfo_enabled) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "启用媒体信息补全"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.plex_direct_host,
                        "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.plex_direct_host) = $event)),
                        label: "Plex 直连地址（写库/枚举用，留空则用反代地址）",
                        placeholder: "http://192.168.0.122:32400",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VBtn, {
                        color: "info",
                        variant: "tonal",
                        size: "small",
                        loading: checking.value,
                        onClick: checkHelper,
                        "prepend-icon": "mdi-lan-connect"
                      }, {
                        default: _withCtx(() => [...(_cache[37] || (_cache[37] = [
                          _createTextVNode("检查 helper", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.helper_url,
                        "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.helper_url) = $event)),
                        label: "helper 地址（122 上的写库服务）",
                        placeholder: "http://192.168.0.122:9001",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.helper_token,
                        "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.helper_token) = $event)),
                        label: "helper Token",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VDivider, { class: "my-1" })
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.use_emby,
                        "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.use_emby) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "数据源 Emby MediaStreams"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.emby_url,
                        "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.emby_url) = $event)),
                        label: "Emby 地址",
                        placeholder: "http://192.168.0.121:8096",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.emby_apikey,
                        "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.emby_apikey) = $event)),
                        label: "Emby API Key",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VDivider, { class: "my-1" })
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSelect, {
                        modelValue: selectedSections.value,
                        "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((selectedSections).value = $event)),
                        items: sectionOptions.value,
                        "item-title": "title",
                        "item-value": "value",
                        label: "要补全的 Plex 媒体库",
                        variant: "outlined",
                        density: "compact",
                        multiple: "",
                        chips: "",
                        "closable-chips": "",
                        "hide-details": "auto",
                        loading: loadingSections.value
                      }, {
                        "append-inner": _withCtx(() => [
                          _createVNode(_component_VBtn, {
                            icon: "mdi-refresh",
                            size: "x-small",
                            variant: "text",
                            onClick: _withModifiers(loadSections, ["stop"])
                          })
                        ]),
                        _: 1
                      }, 8, ["modelValue", "items", "loading"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.concurrency,
                        "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((config.concurrency) = $event)),
                        modelModifiers: { number: true },
                        type: "number",
                        min: "1",
                        max: "10",
                        label: "探测并发数",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.only_missing,
                        "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((config.only_missing) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "仅处理缺失媒体信息的条目"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.overwrite_streams,
                        "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((config.overwrite_streams) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "写入前清空旧流"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.cron,
                        "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((config.cron) = $event)),
                        label: "定时补全 Cron（留空不定时）",
                        placeholder: "0 4 * * *",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VDivider, { class: "my-1" })
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "text-caption text-medium-emphasis"
                  }, {
                    default: _withCtx(() => [...(_cache[38] || (_cache[38] = [
                      _createTextVNode("自动触发（播放停止后自动增量补全本集+后N集，默认常开）", -1)
                    ]))]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config.webhook_enabled,
                        "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((config.webhook_enabled) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "启用 Plex Webhook 触发（需 Plex Pass）"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.dedup_window,
                        "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((config.dedup_window) = $event)),
                        modelModifiers: { number: true },
                        type: "number",
                        min: "0",
                        label: "同条目去重窗口（秒）",
                        placeholder: "300",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: config.forward_episodes,
                        "onUpdate:modelValue": _cache[23] || (_cache[23] = $event => ((config.forward_episodes) = $event)),
                        modelModifiers: { number: true },
                        type: "number",
                        min: "0",
                        label: "剧集向后预取集数（含当前集后N集）",
                        placeholder: "5",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  (config.webhook_enabled)
                    ? (_openBlock(), _createBlock(_component_VCol, {
                        key: 0,
                        cols: "12"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VAlert, {
                            type: "info",
                            variant: "tonal",
                            density: "compact",
                            class: "text-caption"
                          }, {
                            default: _withCtx(() => [
                              _cache[39] || (_cache[39] = _createTextVNode(" Webhook 地址填到 Plex 设置 → Webhooks：", -1)),
                              _createElementVNode("code", null, _toDisplayString(webhookUrl.value), 1)
                            ]),
                            _: 1
                          })
                        ]),
                        _: 1
                      }))
                    : _createCommentVNode("", true)
                ]),
                _: 1
              }),
              (helperInfo.value)
                ? (_openBlock(), _createBlock(_component_VAlert, {
                    key: 0,
                    type: "success",
                    variant: "tonal",
                    density: "compact",
                    class: "mt-2 text-caption"
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(" helper 正常，数据库：" + _toDisplayString(helperInfo.value), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true)
            ], 512), [
              [_vShow, activeTab.value === 'mediainfo']
            ]),
            _withDirectives(_createElementVNode("div", _hoisted_7, [
              _cache[52] || (_cache[52] = _createElementVNode("div", { class: "ptb-section-title" }, "目录匹配 / 刮削", -1)),
              _createVNode(_component_VAlert, {
                type: "info",
                variant: "tonal",
                density: "compact",
                class: "mb-3 text-caption"
              }, {
                default: _withCtx(() => [...(_cache[41] || (_cache[41] = [
                  _createTextVNode(" 本栏为按需手动操作：取消匹配让条目按当前 NFO 代理重读；扫描缺封面条目并交给 MoviePilot 刮削生成 NFO+封面。操作前请先选择目标媒体库。 ", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VRow, null, {
                default: _withCtx(() => [
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSelect, {
                        modelValue: scrapeSection.value,
                        "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => ((scrapeSection).value = $event)),
                        items: sectionOptions.value,
                        "item-title": "title",
                        "item-value": "value",
                        label: "目标 Plex 媒体库",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto",
                        loading: loadingSections.value
                      }, {
                        "append-inner": _withCtx(() => [
                          _createVNode(_component_VBtn, {
                            icon: "mdi-refresh",
                            size: "x-small",
                            variant: "text",
                            onClick: _withModifiers(loadSections, ["stop"])
                          })
                        ]),
                        _: 1
                      }, 8, ["modelValue", "items", "loading"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VTextField, {
                        modelValue: scrapeLimit.value,
                        "onUpdate:modelValue": _cache[25] || (_cache[25] = $event => ((scrapeLimit).value = $event)),
                        modelModifiers: { number: true },
                        type: "number",
                        min: "0",
                        label: "限制条数（0=不限）",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VDivider, { class: "my-1" })
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "text-caption text-medium-emphasis"
                  }, {
                    default: _withCtx(() => [...(_cache[42] || (_cache[42] = [
                      _createTextVNode("① 一键取消匹配（取消后自动刷新重读 NFO）", -1)
                    ]))]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "d-flex align-center gap-2"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VBtn, {
                        color: "info",
                        variant: "tonal",
                        size: "small",
                        loading: busyKey.value==='unmatch_preview',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-magnify",
                        onClick: _cache[26] || (_cache[26] = $event => (doUnmatch(true)))
                      }, {
                        default: _withCtx(() => [...(_cache[43] || (_cache[43] = [
                          _createTextVNode("预览影响", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      _createVNode(_component_VBtn, {
                        color: "warning",
                        variant: "flat",
                        size: "small",
                        loading: busyKey.value==='unmatch_run',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-link-off",
                        onClick: _cache[27] || (_cache[27] = $event => (doUnmatch(false)))
                      }, {
                        default: _withCtx(() => [...(_cache[44] || (_cache[44] = [
                          _createTextVNode("执行取消匹配", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VDivider, { class: "my-1" })
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "text-caption text-medium-emphasis"
                  }, {
                    default: _withCtx(() => [...(_cache[45] || (_cache[45] = [
                      _createTextVNode("② 缺封面刮削（Plex 无封面 / 目录只有 strm）", -1)
                    ]))]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "d-flex align-center gap-2 flex-wrap"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VBtn, {
                        color: "info",
                        variant: "tonal",
                        size: "small",
                        loading: busyKey.value==='scan_cover',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-image-off-outline",
                        onClick: doScanCover
                      }, {
                        default: _withCtx(() => [...(_cache[46] || (_cache[46] = [
                          _createTextVNode("扫描缺封面", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      _createVNode(_component_VBtn, {
                        color: "info",
                        variant: "tonal",
                        size: "small",
                        loading: busyKey.value==='scrape_preview',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-magnify",
                        onClick: _cache[28] || (_cache[28] = $event => (doScrape(true)))
                      }, {
                        default: _withCtx(() => [...(_cache[47] || (_cache[47] = [
                          _createTextVNode("预览刮削目录", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      _createVNode(_component_VBtn, {
                        color: "success",
                        variant: "flat",
                        size: "small",
                        loading: busyKey.value==='scrape_run',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-auto-fix",
                        onClick: _cache[29] || (_cache[29] = $event => (doScrape(false)))
                      }, {
                        default: _withCtx(() => [...(_cache[48] || (_cache[48] = [
                          _createTextVNode("执行刮削", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VDivider, { class: "my-1" })
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "text-caption text-medium-emphasis"
                  }, {
                    default: _withCtx(() => [...(_cache[49] || (_cache[49] = [
                      _createTextVNode("③ 缺 poster.jpg 精准补全（已刮削但独缺海报：剧集先复制季内海报，电影/无季海报走 TMDB，修复后自动刷新）", -1)
                    ]))]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "12",
                    class: "d-flex align-center gap-2 flex-wrap"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VBtn, {
                        color: "info",
                        variant: "tonal",
                        size: "small",
                        loading: busyKey.value==='poster_preview',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-magnify",
                        onClick: _cache[30] || (_cache[30] = $event => (doFixPoster(true)))
                      }, {
                        default: _withCtx(() => [...(_cache[50] || (_cache[50] = [
                          _createTextVNode("预览缺 poster", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      _createVNode(_component_VBtn, {
                        color: "success",
                        variant: "flat",
                        size: "small",
                        loading: busyKey.value==='poster_run',
                        disabled: !!busyKey.value,
                        "prepend-icon": "mdi-image-plus",
                        onClick: _cache[31] || (_cache[31] = $event => (doFixPoster(false)))
                      }, {
                        default: _withCtx(() => [...(_cache[51] || (_cache[51] = [
                          _createTextVNode("执行补全", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading", "disabled"])
                    ]),
                    _: 1
                  }),
                  (scrapeResult.value)
                    ? (_openBlock(), _createBlock(_component_VCol, {
                        key: 0,
                        cols: "12"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_VAlert, {
                            type: scrapeResult.value.type,
                            variant: "tonal",
                            density: "compact",
                            class: "text-caption",
                            style: {"white-space":"pre-wrap"}
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(scrapeResult.value.text), 1)
                            ]),
                            _: 1
                          }, 8, ["type"])
                        ]),
                        _: 1
                      }))
                    : _createCommentVNode("", true)
                ]),
                _: 1
              })
            ], 512), [
              [_vShow, activeTab.value === 'scrape']
            ])
          ])
        ]),
        _createVNode(_component_VDivider),
        _createVNode(_component_VCardActions, { class: "ptb-actions" }, {
          default: _withCtx(() => [
            _createVNode(_component_VBtn, {
              color: "info",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-view-dashboard-outline",
              onClick: _cache[32] || (_cache[32] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[53] || (_cache[53] = [
                _createTextVNode("数据页", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VSpacer),
            _createVNode(_component_VBtn, {
              color: "primary",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-content-save",
              onClick: saveConfig
            }, {
              default: _withCtx(() => [...(_cache[54] || (_cache[54] = [
                _createTextVNode("保存", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VBtn, {
              color: "grey",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-close",
              onClick: _cache[33] || (_cache[33] = $event => (emit('close')))
            }, {
              default: _withCtx(() => [...(_cache[55] || (_cache[55] = [
                _createTextVNode("关闭", -1)
              ]))]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-e6d3af3e"]]);

export { Config as default };
