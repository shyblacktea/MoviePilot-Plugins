import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, g as getPluginApi } from './_plugin-vue_export-helper-DGGBqqkU.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,createElementVNode:_createElementVNode,createBlock:_createBlock,createCommentVNode:_createCommentVNode,vShow:_vShow,withDirectives:_withDirectives,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "ptb-config" };
const _hoisted_2 = { class: "ptb-body" };
const _hoisted_3 = { class: "ptb-nav" };
const _hoisted_4 = { class: "ptb-content" };
const _hoisted_5 = { class: "ptb-pane" };
const _hoisted_6 = { class: "ptb-pane" };

const {computed,reactive,ref,onMounted} = await importShared('vue');


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
];
const currentTab = computed(() => tabs.find(t => t.key === activeTab.value) || tabs[0]);

const config = reactive({
  enabled: false, proxy_enabled: false, plex_host: '', plex_token: '',
  host: '0.0.0.0', port: 32401, pin_rules: '', force_direct_play: true,
  mediainfo_enabled: false, plex_direct_host: '', helper_url: '', helper_token: '',
  emby_url: '', emby_apikey: '', use_emby: true, use_ffprobe: true,
  overwrite_streams: true, only_missing: true, concurrency: 3, sections: '', cron: '',
  ...props.initialConfig,
});

const selectedSections = computed({
  get: () => (config.sections ? String(config.sections).split(',').map(s => s.trim()).filter(Boolean) : []),
  set: v => { config.sections = (v || []).join(','); },
});

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
              default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
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
              _cache[25] || (_cache[25] = _createElementVNode("div", { class: "ptb-section-title" }, "302 反向代理", -1)),
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
              _cache[27] || (_cache[27] = _createElementVNode("div", { class: "ptb-section-title" }, "STRM 媒体流信息补全", -1)),
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
                        default: _withCtx(() => [...(_cache[26] || (_cache[26] = [
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
                        label: "数据源① Emby MediaStreams"
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
                        modelValue: config.use_ffprobe,
                        "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.use_ffprobe) = $event)),
                        color: "primary",
                        "hide-details": "",
                        inset: "",
                        label: "数据源② ffprobe 探测直链"
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
                        "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.emby_url) = $event)),
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
                        "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((config.emby_apikey) = $event)),
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
                        "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((selectedSections).value = $event)),
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
                        "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((config.concurrency) = $event)),
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
                        "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((config.only_missing) = $event)),
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
                        "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((config.overwrite_streams) = $event)),
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
                        "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((config.cron) = $event)),
                        label: "定时补全 Cron（留空不定时）",
                        placeholder: "0 4 * * *",
                        variant: "outlined",
                        density: "compact",
                        "hide-details": "auto"
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  })
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
              onClick: _cache[22] || (_cache[22] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
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
              default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
                _createTextVNode("保存", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VBtn, {
              color: "grey",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-close",
              onClick: _cache[23] || (_cache[23] = $event => (emit('close')))
            }, {
              default: _withCtx(() => [...(_cache[30] || (_cache[30] = [
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-efe1af3e"]]);

export { Config as default };
