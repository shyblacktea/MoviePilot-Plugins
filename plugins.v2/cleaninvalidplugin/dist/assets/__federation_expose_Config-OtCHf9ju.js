import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,createElementVNode:_createElementVNode,createBlock:_createBlock,createCommentVNode:_createCommentVNode,normalizeProps:_normalizeProps,guardReactiveProps:_guardReactiveProps,vShow:_vShow,withDirectives:_withDirectives} = await importShared('vue');


const _hoisted_1 = { class: "cip-config" };
const _hoisted_2 = { class: "cip-body" };
const _hoisted_3 = { class: "cip-nav" };
const _hoisted_4 = { class: "cip-content" };
const _hoisted_5 = { class: "cip-window" };
const _hoisted_6 = { class: "cip-stat-grid ma-4 mb-0" };
const _hoisted_7 = { class: "cip-stat" };
const _hoisted_8 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_9 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_10 = { class: "cip-stat" };
const _hoisted_11 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_12 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_13 = { class: "cip-stat" };
const _hoisted_14 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_15 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_16 = { class: "cip-pane" };
const _hoisted_17 = { class: "cip-plugin-list mt-3" };
const _hoisted_18 = {
  key: 1,
  class: "cip-empty"
};
const _hoisted_19 = { class: "cip-pane" };
const _hoisted_20 = { class: "cip-actions d-flex align-center flex-wrap ga-1" };

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
const invalidItems = ref([]);
const activeMain = ref('target');

const mainTabs = [
  { key: 'target', title: '处理对象', icon: 'mdi-playlist-check', desc: '选择需要清理或重装的无效插件。' },
  { key: 'action', title: '操作方式', icon: 'mdi-tune', desc: '清理记录或从本地源重新安装。' },
];

const currentMain = computed(() => mainTabs.find(i => i.key === activeMain.value) || mainTabs[0]);

const config = reactive({
  invalid_plugin_ids: [],
  action_mode: 'clean',
});

const selectedCount = computed(() => config.invalid_plugin_ids.length);
const localSourceCount = computed(() => invalidItems.value.filter(item => item.local_source_path).length);
const actionHint = computed(() => {
  if (config.action_mode === 'reinstall') {
    return '重新安装会优先使用本地插件源；找不到来源时会保留记录，并保留原插件配置。'
  }
  return '清理记录只移除已安装列表中的选中项和无效运行目录，不删除原插件配置。'
});

function applyInitialConfig() {
  config.invalid_plugin_ids = Array.isArray(props.initialConfig.invalid_plugin_ids)
    ? [...props.initialConfig.invalid_plugin_ids]
    : [];
  config.action_mode = props.initialConfig.action_mode || 'clean';
}

async function loadInvalidPlugins() {
  loading.value = true;
  error.value = '';
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/invalid_plugins');
    const data = response?.data || response || {};
    invalidItems.value = data.items || [];
    const validIds = new Set(invalidItems.value.map(item => item.id));
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => validIds.has(id));
  } catch (err) {
    error.value = err?.message || '读取无效插件列表失败';
  } finally {
    loading.value = false;
  }
}

function togglePlugin(pluginId) {
  if (config.invalid_plugin_ids.includes(pluginId)) {
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => id !== pluginId);
    return
  }
  config.invalid_plugin_ids = [...config.invalid_plugin_ids, pluginId];
}

function selectAll() {
  config.invalid_plugin_ids = invalidItems.value.map(item => item.id);
}

function clearSelection() {
  config.invalid_plugin_ids = [];
}

function saveConfig() {
  emit('save', {
    invalid_plugin_ids: [...config.invalid_plugin_ids],
    action_mode: config.action_mode,
  });
}

onMounted(() => {
  applyInitialConfig();
  loadInvalidPlugins();
});

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VListItemTitle = _resolveComponent("VListItemTitle");
  const _component_VListItem = _resolveComponent("VListItem");
  const _component_VList = _resolveComponent("VList");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VCheckboxBtn = _resolveComponent("VCheckboxBtn");
  const _component_VRadio = _resolveComponent("VRadio");
  const _component_VRadioGroup = _resolveComponent("VRadioGroup");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VCard = _resolveComponent("VCard");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VCard, {
      flat: "",
      class: "cip-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardItem, { class: "cip-header" }, {
          prepend: _withCtx(() => [
            _createVNode(_component_VAvatar, {
              color: "primary",
              variant: "tonal",
              size: "44",
              rounded: "lg"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-delete-sweep",
                  size: "24"
                })
              ]),
              _: 1
            })
          ]),
          append: _withCtx(() => [
            _createVNode(_component_VBtn, {
              icon: "mdi-refresh",
              variant: "text",
              size: "small",
              loading: loading.value,
              "aria-label": "刷新",
              onClick: loadInvalidPlugins
            }, null, 8, ["loading"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-h6" }, {
              default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                _createTextVNode("清理无效插件", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
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
              class: "py-2 cip-nav-list"
            }, {
              default: _withCtx(() => [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(mainTabs, (item) => {
                  return _createVNode(_component_VListItem, {
                    key: item.key,
                    active: activeMain.value === item.key,
                    color: "primary",
                    rounded: "lg",
                    class: "cip-nav-item",
                    onClick: $event => (activeMain.value = item.key)
                  }, {
                    prepend: _withCtx(() => [
                      _createVNode(_component_VIcon, {
                        icon: item.icon,
                        class: "cip-nav-icon"
                      }, null, 8, ["icon"])
                    ]),
                    default: _withCtx(() => [
                      _createVNode(_component_VListItemTitle, { class: "cip-nav-title" }, {
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
                  density: "compact",
                  variant: "tonal",
                  class: "ma-3 mb-0 text-caption",
                  closable: "",
                  "onClick:close": _cache[0] || (_cache[0] = $event => (error.value = ''))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : (!loading.value && invalidItems.value.length === 0)
                ? (_openBlock(), _createBlock(_component_VAlert, {
                    key: 1,
                    type: "success",
                    density: "compact",
                    variant: "tonal",
                    class: "ma-3 mb-0 text-caption"
                  }, {
                    default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                      _createTextVNode(" 当前没有需要处理的无效插件。 ", -1)
                    ]))]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
            _createElementVNode("div", _hoisted_5, [
              _createElementVNode("div", _hoisted_6, [
                _createElementVNode("div", _hoisted_7, [
                  _createElementVNode("div", _hoisted_8, [
                    _createVNode(_component_VAvatar, {
                      color: "error",
                      variant: "tonal",
                      size: "28",
                      rounded: "lg"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VIcon, {
                          icon: "mdi-alert-circle-outline",
                          size: "17"
                        })
                      ]),
                      _: 1
                    }),
                    _cache[7] || (_cache[7] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "无效插件", -1))
                  ]),
                  _createElementVNode("div", _hoisted_9, _toDisplayString(invalidItems.value.length), 1)
                ]),
                _createElementVNode("div", _hoisted_10, [
                  _createElementVNode("div", _hoisted_11, [
                    _createVNode(_component_VAvatar, {
                      color: "primary",
                      variant: "tonal",
                      size: "28",
                      rounded: "lg"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VIcon, {
                          icon: "mdi-checkbox-marked-circle-outline",
                          size: "17"
                        })
                      ]),
                      _: 1
                    }),
                    _cache[8] || (_cache[8] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "已选择", -1))
                  ]),
                  _createElementVNode("div", _hoisted_12, _toDisplayString(selectedCount.value), 1)
                ]),
                _createElementVNode("div", _hoisted_13, [
                  _createElementVNode("div", _hoisted_14, [
                    _createVNode(_component_VAvatar, {
                      color: "success",
                      variant: "tonal",
                      size: "28",
                      rounded: "lg"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VIcon, {
                          icon: "mdi-source-branch-check",
                          size: "17"
                        })
                      ]),
                      _: 1
                    }),
                    _cache[9] || (_cache[9] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "本地源", -1))
                  ]),
                  _createElementVNode("div", _hoisted_15, _toDisplayString(localSourceCount.value), 1)
                ])
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_16, [
                _cache[11] || (_cache[11] = _createElementVNode("div", { class: "cip-section-title" }, "处理对象", -1)),
                _createVNode(_component_VSelect, {
                  modelValue: config.invalid_plugin_ids,
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.invalid_plugin_ids) = $event)),
                  items: invalidItems.value,
                  "item-title": "title",
                  "item-value": "id",
                  label: "插件",
                  variant: "outlined",
                  density: "compact",
                  multiple: "",
                  chips: "",
                  "closable-chips": "",
                  clearable: "",
                  loading: loading.value,
                  disabled: loading.value || invalidItems.value.length === 0,
                  "hide-details": "auto"
                }, {
                  item: _withCtx(({ props: itemProps, item }) => [
                    _createVNode(_component_VListItem, _normalizeProps(_guardReactiveProps(itemProps)), {
                      append: _withCtx(() => [
                        _createVNode(_component_VChip, {
                          color: item.raw.local_source_path ? 'success' : 'warning',
                          size: "small",
                          variant: "tonal"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(item.raw.local_source_path ? '可重装' : '需清理'), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"])
                      ]),
                      _: 2
                    }, 1040)
                  ]),
                  _: 1
                }, 8, ["modelValue", "items", "loading", "disabled"]),
                _createElementVNode("div", _hoisted_17, [
                  (invalidItems.value.length)
                    ? (_openBlock(), _createBlock(_component_VList, {
                        key: 0,
                        lines: "two",
                        density: "compact"
                      }, {
                        default: _withCtx(() => [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(invalidItems.value, (plugin) => {
                            return (_openBlock(), _createBlock(_component_VListItem, {
                              key: plugin.id,
                              title: plugin.id,
                              subtitle: plugin.status
                            }, {
                              prepend: _withCtx(() => [
                                _createVNode(_component_VCheckboxBtn, {
                                  "model-value": config.invalid_plugin_ids.includes(plugin.id),
                                  "onUpdate:modelValue": $event => (togglePlugin(plugin.id))
                                }, null, 8, ["model-value", "onUpdate:modelValue"])
                              ]),
                              append: _withCtx(() => [
                                _createVNode(_component_VChip, {
                                  color: plugin.runtime_exists ? 'warning' : 'error',
                                  size: "small",
                                  variant: "tonal"
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(plugin.runtime_exists ? '目录异常' : '目录缺失'), 1)
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
                    : (_openBlock(), _createElementBlock("div", _hoisted_18, [
                        _createVNode(_component_VIcon, {
                          icon: "mdi-check-circle-outline",
                          size: "36",
                          color: "success"
                        }),
                        _cache[10] || (_cache[10] = _createElementVNode("span", null, "没有待处理记录", -1))
                      ]))
                ])
              ], 512), [
                [_vShow, activeMain.value === 'target']
              ]),
              _withDirectives(_createElementVNode("div", _hoisted_19, [
                _cache[14] || (_cache[14] = _createElementVNode("div", { class: "cip-section-title" }, "操作方式", -1)),
                _createVNode(_component_VRow, { align: "center" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "7"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VRadioGroup, {
                          modelValue: config.action_mode,
                          "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.action_mode) = $event)),
                          inline: "",
                          density: "compact",
                          "hide-details": "",
                          disabled: invalidItems.value.length === 0
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_VRadio, {
                              label: "清理记录",
                              value: "clean",
                              color: "error"
                            }),
                            _createVNode(_component_VRadio, {
                              label: "重新安装",
                              value: "reinstall",
                              color: "primary"
                            })
                          ]),
                          _: 1
                        }, 8, ["modelValue", "disabled"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_VCol, {
                      cols: "12",
                      md: "5",
                      class: "d-flex justify-end ga-2 flex-wrap"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VBtn, {
                          color: "primary",
                          variant: "text",
                          size: "small",
                          "prepend-icon": "mdi-check-all",
                          disabled: invalidItems.value.length === 0,
                          onClick: selectAll
                        }, {
                          default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                            _createTextVNode("全选", -1)
                          ]))]),
                          _: 1
                        }, 8, ["disabled"]),
                        _createVNode(_component_VBtn, {
                          color: "secondary",
                          variant: "text",
                          size: "small",
                          "prepend-icon": "mdi-close",
                          disabled: selectedCount.value === 0,
                          onClick: clearSelection
                        }, {
                          default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                            _createTextVNode("清空", -1)
                          ]))]),
                          _: 1
                        }, 8, ["disabled"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_VAlert, {
                  type: config.action_mode === 'reinstall' ? 'warning' : 'info',
                  variant: "tonal",
                  density: "compact",
                  icon: "mdi-information",
                  class: "text-caption mt-3"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(actionHint.value), 1)
                  ]),
                  _: 1
                }, 8, ["type"])
              ], 512), [
                [_vShow, activeMain.value === 'action']
              ])
            ]),
            _createVNode(_component_VDivider),
            _createElementVNode("div", _hoisted_20, [
              _createVNode(_component_VBtn, {
                color: "info",
                "prepend-icon": "mdi-view-dashboard",
                variant: "text",
                size: "small",
                onClick: _cache[3] || (_cache[3] = $event => (emit('switch')))
              }, {
                default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
                  _createTextVNode("数据页", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VSpacer, { class: "cip-action-spacer" }),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                onClick: loadInvalidPlugins
              }, {
                default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
                  _createTextVNode("刷新", -1)
                ]))]),
                _: 1
              }, 8, ["loading"]),
              _createVNode(_component_VBtn, {
                color: "primary",
                "prepend-icon": "mdi-content-save",
                variant: "text",
                size: "small",
                disabled: selectedCount.value === 0,
                onClick: saveConfig
              }, {
                default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
                  _createTextVNode("保存并执行", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-close",
                variant: "text",
                size: "small",
                onClick: _cache[4] || (_cache[4] = $event => (emit('close')))
              }, {
                default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-27f332d6"]]);

export { Config as default };
