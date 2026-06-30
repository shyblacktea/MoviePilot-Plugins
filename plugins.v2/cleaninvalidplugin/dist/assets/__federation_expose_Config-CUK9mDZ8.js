import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,normalizeProps:_normalizeProps,guardReactiveProps:_guardReactiveProps,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "setting-item stat-item" };
const _hoisted_3 = { class: "stat-copy" };
const _hoisted_4 = { class: "setting-item stat-item" };
const _hoisted_5 = { class: "stat-copy" };
const _hoisted_6 = { class: "setting-item stat-item" };
const _hoisted_7 = { class: "stat-copy" };
const _hoisted_8 = { class: "setting-item select-item" };
const _hoisted_9 = { class: "plugin-list mt-2" };
const _hoisted_10 = {
  key: 1,
  class: "empty-panel"
};
const _hoisted_11 = { class: "setting-item mode-item" };
const _hoisted_12 = { class: "setting-item quick-actions" };

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
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_checkbox_btn = _resolveComponent("v-checkbox-btn");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_radio = _resolveComponent("v-radio");
  const _component_v_radio_group = _resolveComponent("v-radio-group");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_form = _resolveComponent("v-form");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              icon: "mdi-delete-sweep",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[4] || (_cache[4] = _createElementVNode("span", null, "清理无效插件配置", -1))
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
          default: _withCtx(() => [
            (error.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "error",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : (!loading.value && invalidItems.value.length === 0)
                ? (_openBlock(), _createBlock(_component_v_alert, {
                    key: 1,
                    type: "success",
                    density: "compact",
                    class: "mb-2 text-caption",
                    variant: "tonal"
                  }, {
                    default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                      _createTextVNode(" 当前没有需要处理的无效插件。 ", -1)
                    ]))]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
            _createVNode(_component_v_form, {
              onSubmit: _withModifiers(saveConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card, {
                  flat: "",
                  class: "rounded mb-3 border config-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-chart-box-outline",
                          class: "mr-2",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[6] || (_cache[6] = _createElementVNode("span", null, "状态概览", -1))
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "4"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_2, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-alert-circle-outline",
                                    size: "small",
                                    color: "error",
                                    class: "mr-3"
                                  }),
                                  _createElementVNode("div", _hoisted_3, [
                                    _cache[7] || (_cache[7] = _createElementVNode("span", { class: "text-subtitle-2" }, "无效插件", -1)),
                                    _createElementVNode("strong", null, _toDisplayString(invalidItems.value.length), 1)
                                  ])
                                ])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "4"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_4, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-checkbox-marked-circle-outline",
                                    size: "small",
                                    color: "primary",
                                    class: "mr-3"
                                  }),
                                  _createElementVNode("div", _hoisted_5, [
                                    _cache[8] || (_cache[8] = _createElementVNode("span", { class: "text-subtitle-2" }, "已选择", -1)),
                                    _createElementVNode("strong", null, _toDisplayString(selectedCount.value), 1)
                                  ])
                                ])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "4"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_6, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-source-branch-check",
                                    size: "small",
                                    color: "success",
                                    class: "mr-3"
                                  }),
                                  _createElementVNode("div", _hoisted_7, [
                                    _cache[9] || (_cache[9] = _createElementVNode("span", { class: "text-subtitle-2" }, "本地源", -1)),
                                    _createElementVNode("strong", null, _toDisplayString(localSourceCount.value), 1)
                                  ])
                                ])
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
                }),
                _createVNode(_component_v_card, {
                  flat: "",
                  class: "rounded mb-3 border config-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-playlist-check",
                          class: "mr-2",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[10] || (_cache[10] = _createElementVNode("span", null, "处理对象", -1))
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_8, [
                                  _createVNode(_component_v_select, {
                                    modelValue: config.invalid_plugin_ids,
                                    "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((config.invalid_plugin_ids) = $event)),
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
                                      _createVNode(_component_v_list_item, _normalizeProps(_guardReactiveProps(itemProps)), {
                                        append: _withCtx(() => [
                                          _createVNode(_component_v_chip, {
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
                                  }, 8, ["modelValue", "items", "loading", "disabled"])
                                ])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createElementVNode("div", _hoisted_9, [
                          (invalidItems.value.length)
                            ? (_openBlock(), _createBlock(_component_v_list, {
                                key: 0,
                                lines: "two",
                                density: "compact"
                              }, {
                                default: _withCtx(() => [
                                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(invalidItems.value, (plugin) => {
                                    return (_openBlock(), _createBlock(_component_v_list_item, {
                                      key: plugin.id,
                                      title: plugin.id,
                                      subtitle: plugin.status
                                    }, {
                                      prepend: _withCtx(() => [
                                        _createVNode(_component_v_checkbox_btn, {
                                          "model-value": config.invalid_plugin_ids.includes(plugin.id),
                                          "onUpdate:modelValue": $event => (togglePlugin(plugin.id))
                                        }, null, 8, ["model-value", "onUpdate:modelValue"])
                                      ]),
                                      append: _withCtx(() => [
                                        _createVNode(_component_v_chip, {
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
                            : (_openBlock(), _createElementBlock("div", _hoisted_10, [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-check-circle-outline",
                                  size: "36",
                                  color: "success"
                                }),
                                _cache[11] || (_cache[11] = _createElementVNode("span", null, "没有待处理记录", -1))
                              ]))
                        ])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card, {
                  flat: "",
                  class: "rounded mb-3 border config-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-tune",
                          class: "mr-2",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[12] || (_cache[12] = _createElementVNode("span", null, "操作方式", -1))
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "7"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_11, [
                                  _createVNode(_component_v_radio_group, {
                                    modelValue: config.action_mode,
                                    "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.action_mode) = $event)),
                                    inline: "",
                                    density: "compact",
                                    "hide-details": "",
                                    disabled: invalidItems.value.length === 0
                                  }, {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_radio, {
                                        label: "清理记录",
                                        value: "clean",
                                        color: "error"
                                      }),
                                      _createVNode(_component_v_radio, {
                                        label: "重新安装",
                                        value: "reinstall",
                                        color: "primary"
                                      })
                                    ]),
                                    _: 1
                                  }, 8, ["modelValue", "disabled"])
                                ])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "5"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_12, [
                                  _createVNode(_component_v_btn, {
                                    color: "primary",
                                    variant: "text",
                                    size: "small",
                                    "prepend-icon": "mdi-check-all",
                                    disabled: invalidItems.value.length === 0,
                                    onClick: selectAll
                                  }, {
                                    default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                                      _createTextVNode(" 全选 ", -1)
                                    ]))]),
                                    _: 1
                                  }, 8, ["disabled"]),
                                  _createVNode(_component_v_btn, {
                                    color: "secondary",
                                    variant: "text",
                                    size: "small",
                                    "prepend-icon": "mdi-close",
                                    disabled: selectedCount.value === 0,
                                    onClick: clearSelection
                                  }, {
                                    default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                                      _createTextVNode(" 清空 ", -1)
                                    ]))]),
                                    _: 1
                                  }, 8, ["disabled"])
                                ])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_alert, {
                          type: config.action_mode === 'reinstall' ? 'warning' : 'info',
                          variant: "tonal",
                          density: "compact",
                          icon: "mdi-information",
                          class: "text-caption"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(actionHint.value), 1)
                          ]),
                          _: 1
                        }, 8, ["type"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_actions, { class: "px-2 py-1 action-bar" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_btn, {
                      color: "info",
                      "prepend-icon": "mdi-view-dashboard",
                      variant: "text",
                      size: "small",
                      onClick: _cache[2] || (_cache[2] = $event => (emit('switch')))
                    }, {
                      default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
                        _createTextVNode(" 数据页 ", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_spacer, { class: "action-spacer" }),
                    _createVNode(_component_v_btn, {
                      color: "grey",
                      "prepend-icon": "mdi-refresh",
                      variant: "text",
                      size: "small",
                      loading: loading.value,
                      onClick: loadInvalidPlugins
                    }, {
                      default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
                        _createTextVNode(" 刷新 ", -1)
                      ]))]),
                      _: 1
                    }, 8, ["loading"]),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      "prepend-icon": "mdi-content-save",
                      variant: "text",
                      size: "small",
                      disabled: selectedCount.value === 0,
                      onClick: saveConfig
                    }, {
                      default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
                        _createTextVNode(" 保存并执行 ", -1)
                      ]))]),
                      _: 1
                    }, 8, ["disabled"]),
                    _createVNode(_component_v_btn, {
                      color: "grey",
                      "prepend-icon": "mdi-close",
                      variant: "text",
                      size: "small",
                      onClick: _cache[3] || (_cache[3] = $event => (emit('close')))
                    }, {
                      default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
                        _createTextVNode(" 关闭 ", -1)
                      ]))]),
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
        })
      ]),
      _: 1
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-1ca0636f"]]);

export { Config as default };
