import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,createElementVNode:_createElementVNode,createBlock:_createBlock,createCommentVNode:_createCommentVNode,vShow:_vShow,withDirectives:_withDirectives} = await importShared('vue');


const _hoisted_1 = { class: "sp-config" };
const _hoisted_2 = { class: "sp-body" };
const _hoisted_3 = { class: "sp-nav" };
const _hoisted_4 = { class: "sp-content" };
const _hoisted_5 = { class: "sp-window" };
const _hoisted_6 = { class: "sp-pane" };
const _hoisted_7 = { class: "sp-pane" };
const _hoisted_8 = { class: "sp-pane" };
const _hoisted_9 = { class: "sp-pane" };
const _hoisted_10 = { class: "sp-actions d-flex align-center flex-wrap ga-1" };

const {computed,onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
  api: {
    type: Object,
    default: () => ({}),
  },
},
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

const loading = ref(false);
const error = ref('');
const categories = ref([]);
const siteOptions = ref([]);
const cronError = ref('');
const activeMain = ref('scan');

const mainTabs = [
  { key: 'scan', title: '扫描设置', icon: 'mdi-tune-variant', desc: '订阅扫描周期、宽限天数与站点范围。' },
  { key: 'notify', title: '通知权限', icon: 'mdi-message-badge-outline', desc: 'Telegram 通知与规则修改授权。' },
  { key: 'cleanup', title: '全集包清理', icon: 'mdi-broom', desc: '整季包下载完成后的清理策略。' },
  { key: 'candidate', title: '候选下载', icon: 'mdi-download-box-outline', desc: '候选资源本地缓存有效期。' },
];

const currentMain = computed(() => mainTabs.find(i => i.key === activeMain.value) || mainTabs[0]);

const seasonPackCleanupOptions = [
  { title: '关闭', value: 'off' },
  { title: '仅删转移记录', value: 'record' },
  { title: '删转移记录+源文件', value: 'source' },
];

const config = reactive({
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
});

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
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
  loading.value = true;
  error.value = '';
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
  } finally {
    loading.value = false;
  }
}

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

function saveConfig() {
  cronError.value = validateCron(config.cron);
  if (cronError.value) {
    activeMain.value = 'scan';
    return
  }
  emit('save', {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    candidate_cache_days: Number(config.candidate_cache_days),
    search_sites: Array.isArray(config.search_sites) ? [...config.search_sites] : [],
  });
}

onMounted(() => {
  applyInitialConfig();
  loadOptions();
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
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VCard = _resolveComponent("VCard");

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
              default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                _createTextVNode("订阅下载增强", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption sp-header-subtitle" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(currentMain.value.desc), 1)
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
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(mainTabs, (item) => {
                  return _createVNode(_component_VListItem, {
                    key: item.key,
                    active: activeMain.value === item.key,
                    color: "primary",
                    rounded: "lg",
                    class: "sp-nav-item",
                    onClick: $event => (activeMain.value = item.key)
                  }, {
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
            _createElementVNode("div", _hoisted_5, [
              _withDirectives(_createElementVNode("div", _hoisted_6, [
                _cache[15] || (_cache[15] = _createElementVNode("div", { class: "sp-section-title" }, "扫描设置", -1)),
                _createVNode(_component_VRow, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VTextField, {
                          modelValue: config.delay_days,
                          "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.delay_days) = $event)),
                          modelModifiers: { number: true },
                          type: "number",
                          min: "0",
                          label: "宽限天数",
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
                          modelValue: config.cron,
                          "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.cron) = $event)),
                          label: "Cron",
                          variant: "outlined",
                          density: "compact",
                          "hide-details": "auto",
                          "error-messages": cronError.value,
                          hint: "每 6 小时建议写 0 */6 * * *",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue", "error-messages"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VTextField, {
                          modelValue: config.max_scan_subscribes,
                          "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.max_scan_subscribes) = $event)),
                          modelModifiers: { number: true },
                          type: "number",
                          min: "1",
                          label: "订阅部数通知上限",
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
                        _createVNode(_component_VSelect, {
                          modelValue: config.selected_categories,
                          "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.selected_categories) = $event)),
                          items: categories.value,
                          "item-title": "title",
                          "item-value": "value",
                          label: "二级分类",
                          variant: "outlined",
                          density: "compact",
                          multiple: "",
                          chips: "",
                          "closable-chips": "",
                          "hide-details": "auto"
                        }, null, 8, ["modelValue", "items"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VSelect, {
                          modelValue: config.search_sites,
                          "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.search_sites) = $event)),
                          items: siteOptions.value,
                          "item-title": "title",
                          "item-value": "value",
                          label: "PT搜索范围",
                          variant: "outlined",
                          density: "compact",
                          multiple: "",
                          chips: "",
                          "closable-chips": "",
                          clearable: "",
                          "hide-details": "auto"
                        }, null, 8, ["modelValue", "items"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ], 512), [
                [_vShow, activeMain.value === 'scan']
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_7, [
                _cache[16] || (_cache[16] = _createElementVNode("div", { class: "sp-section-title" }, "通知权限", -1)),
                _createVNode(_component_VRow, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VSwitch, {
                          modelValue: config.notify_tg,
                          "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.notify_tg) = $event)),
                          color: "primary",
                          inset: "",
                          "hide-details": "",
                          label: "Telegram 独立通知"
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
                          modelValue: config.allow_tg_rule_update,
                          "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.allow_tg_rule_update) = $event)),
                          color: "warning",
                          inset: "",
                          "hide-details": "",
                          label: "允许 TG 修改订阅规则"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_VAlert, {
                  class: "mt-3",
                  type: "info",
                  variant: "tonal",
                  density: "compact",
                  text: "开启「允许 TG 修改订阅规则」后，可通过 Telegram 交互直接调整订阅过滤规则，请谨慎授权。"
                })
              ], 512), [
                [_vShow, activeMain.value === 'notify']
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_8, [
                _cache[17] || (_cache[17] = _createElementVNode("div", { class: "sp-section-title" }, "全集包清理", -1)),
                _createVNode(_component_VRow, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VSelect, {
                          modelValue: config.season_pack_cleanup,
                          "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.season_pack_cleanup) = $event)),
                          items: seasonPackCleanupOptions,
                          "item-title": "title",
                          "item-value": "value",
                          label: "最终集整季包清理",
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
                          modelValue: config.season_pack_full_download,
                          "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.season_pack_full_download) = $event)),
                          color: "warning",
                          inset: "",
                          "hide-details": "",
                          label: "qB 整季包全选下载"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_VAlert, {
                  class: "mt-3",
                  type: "info",
                  variant: "tonal",
                  density: "compact",
                  text: "当整季包下载到最终集时，可按策略清理旧的分集转移记录或源文件，避免媒体库重复。"
                })
              ], 512), [
                [_vShow, activeMain.value === 'cleanup']
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_9, [
                _cache[18] || (_cache[18] = _createElementVNode("div", { class: "sp-section-title" }, "候选下载", -1)),
                _createVNode(_component_VRow, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VTextField, {
                          modelValue: config.candidate_cache_days,
                          "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.candidate_cache_days) = $event)),
                          modelModifiers: { number: true },
                          type: "number",
                          min: "0",
                          label: "候选缓存天数",
                          hint: "候选下载信息本地缓存有效期，0 关闭；重载/重启后仍可直接下载候选",
                          "persistent-hint": "",
                          variant: "outlined",
                          density: "compact",
                          "hide-details": "auto"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ], 512), [
                [_vShow, activeMain.value === 'candidate']
              ])
            ]),
            _createVNode(_component_VDivider),
            _createElementVNode("div", _hoisted_10, [
              _createVNode(_component_VBtn, {
                color: "info",
                "prepend-icon": "mdi-view-dashboard-outline",
                variant: "text",
                size: "small",
                onClick: _cache[12] || (_cache[12] = $event => (emit('switch')))
              }, {
                default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
                  _createTextVNode("数据页", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VSpacer, { class: "sp-action-spacer" }),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                onClick: loadOptions
              }, {
                default: _withCtx(() => [...(_cache[20] || (_cache[20] = [
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
                default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                  _createTextVNode("保存", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-close",
                variant: "text",
                size: "small",
                onClick: _cache[13] || (_cache[13] = $event => (emit('close')))
              }, {
                default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
                  _createTextVNode("关闭", -1)
                ]))]),
                _: 1
              })
            ])
          ])
        ])
      ]),
      _: 1
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-51a9de61"]]);

export { Config as default };
