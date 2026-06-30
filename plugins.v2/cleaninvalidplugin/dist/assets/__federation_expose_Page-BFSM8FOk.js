import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "main-container" };
const _hoisted_2 = { class: "setting-item summary-item" };
const _hoisted_3 = { class: "setting-item summary-item" };
const _hoisted_4 = { class: "setting-item summary-item" };
const _hoisted_5 = {
  key: 0,
  class: "grid grid-cols-1 gap-3"
};
const _hoisted_6 = { class: "font-bold text-lg break-words leading-tight" };
const _hoisted_7 = { class: "plugin-row px-3 pb-2" };
const _hoisted_8 = { class: "plugin-meta" };
const _hoisted_9 = { class: "text-sm break-all" };
const _hoisted_10 = { class: "path-line" };
const _hoisted_11 = {
  key: 1,
  class: "text-center py-4"
};
const _hoisted_12 = {
  key: 2,
  class: "text-center py-8"
};
const _hoisted_13 = { class: "d-flex align-center mb-2" };

const {computed,onMounted,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: {
    type: Object,
    default: () => ({}),
  },
},
  emits: ['action', 'switch', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

const loading = ref(false);
const error = ref('');
const invalidItems = ref([]);
const lastResult = ref({});
const container = ref(null);

const localSourceCount = computed(() => invalidItems.value.filter(item => item.local_source_path).length);
const runtimeExistsCount = computed(() => invalidItems.value.filter(item => item.runtime_exists).length);
const summaryText = computed(() => {
  if (loading.value) {
    return '正在刷新状态'
  }
  return invalidItems.value.length ? `发现 ${invalidItems.value.length} 个无效插件` : '插件状态正常'
});

async function loadData() {
  loading.value = true;
  error.value = '';
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/invalid_plugins');
    const data = response?.data || response || {};
    invalidItems.value = data.items || [];
    lastResult.value = data.last_result || {};
    emit('action');
  } catch (err) {
    error.value = err?.message || '读取插件状态失败';
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_container = _resolveComponent("v-container");
  const _component_v_footer = _resolveComponent("v-footer");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", {
      ref_key: "container",
      ref: container,
      class: "scroll-content"
    }, [
      _createVNode(_component_v_card, {
        flat: "",
        class: "rounded border mb-3"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                icon: "mdi-puzzle-remove",
                class: "mr-2",
                color: "primary",
                size: "small"
              }),
              _cache[2] || (_cache[2] = _createElementVNode("span", null, "无效插件概览", -1)),
              _createVNode(_component_v_spacer),
              _createVNode(_component_v_btn, {
                icon: "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                "aria-label": "刷新",
                onClick: loadData
              }, null, 8, ["loading"])
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
                : _createCommentVNode("", true),
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
                        _cache[3] || (_cache[3] = _createElementVNode("span", { class: "text-subtitle-2" }, "无效记录", -1)),
                        _createElementVNode("strong", null, _toDisplayString(invalidItems.value.length), 1)
                      ])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_3, [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-source-branch-check",
                          size: "small",
                          color: "success",
                          class: "mr-3"
                        }),
                        _cache[4] || (_cache[4] = _createElementVNode("span", { class: "text-subtitle-2" }, "本地源可用", -1)),
                        _createElementVNode("strong", null, _toDisplayString(localSourceCount.value), 1)
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
                          icon: "mdi-folder-check-outline",
                          size: "small",
                          color: "primary",
                          class: "mr-3"
                        }),
                        _cache[5] || (_cache[5] = _createElementVNode("span", { class: "text-subtitle-2" }, "运行目录存在", -1)),
                        _createElementVNode("strong", null, _toDisplayString(runtimeExistsCount.value), 1)
                      ])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_alert, {
                type: invalidItems.value.length ? 'warning' : 'success',
                variant: "tonal",
                density: "compact",
                icon: "mdi-information",
                class: "text-caption mt-2"
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(invalidItems.value.length ? '存在无法加载的插件记录，可切到配置页选择处理方式。' : '已安装插件记录与当前加载状态一致。'), 1)
                ]),
                _: 1
              }, 8, ["type"]),
              (lastResult.value.message)
                ? (_openBlock(), _createBlock(_component_v_alert, {
                    key: 1,
                    type: lastResult.value.success ? 'success' : 'warning',
                    variant: "tonal",
                    density: "compact",
                    icon: "mdi-history",
                    class: "text-caption mt-2"
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(lastResult.value.message), 1)
                    ]),
                    _: 1
                  }, 8, ["type"]))
                : _createCommentVNode("", true)
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      (invalidItems.value.length)
        ? (_openBlock(), _createElementBlock("div", _hoisted_5, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(invalidItems.value, (plugin) => {
              return (_openBlock(), _createBlock(_component_v_card, {
                key: plugin.id,
                elevation: "2",
                hover: "",
                class: "transition-all duration-300 plugin-card"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card_title, { class: "px-3 pt-2 pb-1" }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_6, _toDisplayString(plugin.id), 1)
                    ]),
                    _: 2
                  }, 1024),
                  _createElementVNode("div", _hoisted_7, [
                    _createElementVNode("div", _hoisted_8, [
                      _createElementVNode("div", _hoisted_9, "状态: " + _toDisplayString(plugin.status), 1),
                      _createElementVNode("div", _hoisted_10, _toDisplayString(plugin.runtime_path), 1)
                    ]),
                    _createVNode(_component_v_chip, {
                      color: plugin.runtime_exists ? 'warning' : 'error',
                      size: "small",
                      variant: "tonal",
                      class: "status-chip"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(plugin.runtime_exists ? '需检查' : '缺失'), 1)
                      ]),
                      _: 2
                    }, 1032, ["color"])
                  ]),
                  _createVNode(_component_v_card_actions, { class: "px-3 pt-0 pb-2" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_chip, {
                        color: plugin.local_source_path ? 'success' : 'warning',
                        size: "small",
                        variant: "tonal"
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(plugin.local_source_path ? '本地源可重装' : '缺少本地源'), 1)
                        ]),
                        _: 2
                      }, 1032, ["color"])
                    ]),
                    _: 2
                  }, 1024)
                ]),
                _: 2
              }, 1024))
            }), 128))
          ]))
        : (loading.value)
          ? (_openBlock(), _createElementBlock("div", _hoisted_11, [
              _createVNode(_component_v_progress_circular, {
                indeterminate: "",
                color: "primary"
              }),
              _cache[6] || (_cache[6] = _createElementVNode("div", { class: "mt-2 text-gray-600" }, "正在刷新状态...", -1))
            ]))
          : (_openBlock(), _createElementBlock("div", _hoisted_12, [
              _createVNode(_component_v_icon, {
                size: "48",
                color: "success"
              }, {
                default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                  _createTextVNode("mdi-check-circle-outline", -1)
                ]))]),
                _: 1
              }),
              _cache[8] || (_cache[8] = _createElementVNode("div", { class: "mt-2 text-gray-600" }, "没有无效插件", -1)),
              _cache[9] || (_cache[9] = _createElementVNode("div", { class: "text-caption text-medium-emphasis mt-1" }, "当前无需清理。", -1))
            ]))
    ], 512),
    _createVNode(_component_v_footer, { class: "footer-bar" }, {
      default: _withCtx(() => [
        _createVNode(_component_v_container, { class: "d-flex flex-column" }, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_13, [
              _createVNode(_component_v_alert, {
                type: invalidItems.value.length ? 'warning' : 'success',
                variant: "tonal",
                density: "compact",
                class: "flex-grow-1 text-caption"
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(summaryText.value), 1)
                ]),
                _: 1
              }, 8, ["type"])
            ]),
            _createVNode(_component_v_card_actions, { class: "px-2 py-1 d-flex justify-space-between action-bar" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_btn, {
                  color: "info",
                  "prepend-icon": "mdi-cog-outline",
                  variant: "text",
                  size: "small",
                  onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
                }, {
                  default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
                    _createTextVNode(" 配置页 ", -1)
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
                  onClick: loadData
                }, {
                  default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                    _createTextVNode(" 刷新 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"]),
                _createVNode(_component_v_btn, {
                  color: "grey",
                  "prepend-icon": "mdi-close",
                  variant: "text",
                  size: "small",
                  onClick: _cache[1] || (_cache[1] = $event => (emit('close')))
                }, {
                  default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
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
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-c8209aad"]]);

export { Page as default };
