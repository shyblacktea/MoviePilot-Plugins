import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,normalizeProps:_normalizeProps,guardReactiveProps:_guardReactiveProps,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "clean-invalid-plugin" };
const _hoisted_2 = { class: "stats-grid mb-4" };
const _hoisted_3 = { class: "stat-panel" };
const _hoisted_4 = { class: "stat-value" };
const _hoisted_5 = { class: "stat-panel" };
const _hoisted_6 = { class: "stat-value" };
const _hoisted_7 = { class: "stat-panel" };
const _hoisted_8 = { class: "stat-value" };
const _hoisted_9 = { class: "plugin-list" };

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
    return '重新安装会优先使用本地插件源；找不到来源时会保留记录。'
  }
  return '清理记录会从已安装列表移除选中项，适合已经不再使用的插件。'
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
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_radio = _resolveComponent("v-radio");
  const _component_v_radio_group = _resolveComponent("v-radio-group");
  const _component_v_checkbox_btn = _resolveComponent("v-checkbox-btn");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_form = _resolveComponent("v-form");
  const _component_v_card = _resolveComponent("v-card");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      variant: "flat",
      class: "surface"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_item, { class: "px-0 pt-0" }, {
          prepend: _withCtx(() => [
            _createVNode(_component_v_avatar, {
              color: "error",
              variant: "tonal",
              rounded: "lg"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, { icon: "mdi-delete-sweep" })
              ]),
              _: 1
            })
          ]),
          append: _withCtx(() => [
            _createVNode(_component_v_btn, {
              icon: "mdi-refresh",
              variant: "text",
              loading: loading.value,
              onClick: loadInvalidPlugins
            }, null, 8, ["loading"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-h6" }, {
              default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
                _createTextVNode("清理无效插件", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_subtitle, null, {
              default: _withCtx(() => [
                _createTextVNode("发现 " + _toDisplayString(invalidItems.value.length) + " 个无效记录", 1)
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        (error.value)
          ? (_openBlock(), _createBlock(_component_v_alert, {
              key: 0,
              type: "error",
              variant: "tonal",
              density: "comfortable",
              class: "mb-4"
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
                variant: "tonal",
                density: "comfortable",
                class: "mb-4"
              }, {
                default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                  _createTextVNode(" 当前没有需要处理的无效插件。 ", -1)
                ]))]),
                _: 1
              }))
            : _createCommentVNode("", true),
        _createElementVNode("div", _hoisted_2, [
          _createElementVNode("div", _hoisted_3, [
            _cache[5] || (_cache[5] = _createElementVNode("div", { class: "stat-label" }, "无效插件", -1)),
            _createElementVNode("div", _hoisted_4, _toDisplayString(invalidItems.value.length), 1)
          ]),
          _createElementVNode("div", _hoisted_5, [
            _cache[6] || (_cache[6] = _createElementVNode("div", { class: "stat-label" }, "已选择", -1)),
            _createElementVNode("div", _hoisted_6, _toDisplayString(selectedCount.value), 1)
          ]),
          _createElementVNode("div", _hoisted_7, [
            _cache[7] || (_cache[7] = _createElementVNode("div", { class: "stat-label" }, "本地源", -1)),
            _createElementVNode("div", _hoisted_8, _toDisplayString(localSourceCount.value), 1)
          ])
        ]),
        _createVNode(_component_v_form, {
          onSubmit: _withModifiers(saveConfig, ["prevent"])
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_select, {
              modelValue: config.invalid_plugin_ids,
              "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((config.invalid_plugin_ids) = $event)),
              items: invalidItems.value,
              "item-title": "title",
              "item-value": "id",
              label: "插件",
              variant: "outlined",
              density: "comfortable",
              multiple: "",
              chips: "",
              "closable-chips": "",
              clearable: "",
              loading: loading.value,
              disabled: loading.value || invalidItems.value.length === 0,
              class: "mb-4"
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
            }, 8, ["modelValue", "items", "loading", "disabled"]),
            _createVNode(_component_v_radio_group, {
              modelValue: config.action_mode,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.action_mode) = $event)),
              inline: "",
              label: "操作方式",
              disabled: invalidItems.value.length === 0,
              class: "mode-group"
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
            }, 8, ["modelValue", "disabled"]),
            _createVNode(_component_v_alert, {
              type: config.action_mode === 'reinstall' ? 'warning' : 'info',
              variant: "tonal",
              density: "comfortable",
              class: "my-4"
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(actionHint.value), 1)
              ]),
              _: 1
            }, 8, ["type"]),
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
                : _createCommentVNode("", true)
            ]),
            _createVNode(_component_v_card_actions, { class: "px-0" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_btn, {
                  "prepend-icon": "mdi-check-all",
                  variant: "tonal",
                  disabled: invalidItems.value.length === 0,
                  onClick: selectAll
                }, {
                  default: _withCtx(() => [...(_cache[8] || (_cache[8] = [
                    _createTextVNode(" 全选 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"]),
                _createVNode(_component_v_btn, {
                  "prepend-icon": "mdi-close",
                  variant: "text",
                  disabled: selectedCount.value === 0,
                  onClick: clearSelection
                }, {
                  default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                    _createTextVNode(" 清空 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"]),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[2] || (_cache[2] = $event => (emit('switch')))
                }, {
                  default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
                    _createTextVNode("详情", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  "prepend-icon": "mdi-content-save",
                  disabled: selectedCount.value === 0,
                  onClick: saveConfig
                }, {
                  default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                    _createTextVNode(" 保存并执行 ", -1)
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
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-79391d0d"]]);

export { Config as default };
