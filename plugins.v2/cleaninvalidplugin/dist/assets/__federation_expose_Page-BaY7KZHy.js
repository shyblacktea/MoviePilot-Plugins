import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "cip-page" };
const _hoisted_2 = { class: "cip-scroll" };
const _hoisted_3 = { class: "cip-stat-grid" };
const _hoisted_4 = { class: "cip-stat" };
const _hoisted_5 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_6 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_7 = { class: "cip-stat" };
const _hoisted_8 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_9 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_10 = { class: "cip-stat" };
const _hoisted_11 = { class: "d-flex align-center ga-2 mb-1" };
const _hoisted_12 = { class: "text-subtitle-1 font-weight-bold" };
const _hoisted_13 = {
  key: 0,
  class: "d-flex flex-column ga-3"
};
const _hoisted_14 = { class: "text-body-2 cip-break" };
const _hoisted_15 = { class: "cip-path" };
const _hoisted_16 = {
  key: 1,
  class: "text-center py-4"
};
const _hoisted_17 = {
  key: 2,
  class: "text-center py-8"
};
const _hoisted_18 = { class: "d-flex align-center flex-wrap ga-1" };

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
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VProgressCircular = _resolveComponent("VProgressCircular");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VContainer = _resolveComponent("VContainer");
  const _component_VFooter = _resolveComponent("VFooter");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createVNode(_component_VCard, {
        flat: "",
        class: "cip-card mb-3"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_VCardItem, { class: "cip-header" }, {
            prepend: _withCtx(() => [
              _createVNode(_component_VAvatar, {
                color: "primary",
                variant: "tonal",
                size: "42",
                rounded: "lg"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VIcon, {
                    icon: "mdi-puzzle-remove",
                    size: "23"
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
                onClick: loadData
              }, null, 8, ["loading"])
            ]),
            default: _withCtx(() => [
              _createVNode(_component_VCardTitle, { class: "text-h6" }, {
                default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
                  _createTextVNode("无效插件概览", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
                default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                  _createTextVNode("残留但无法加载的插件记录状态", -1)
                ]))]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createVNode(_component_VDivider),
          _createVNode(_component_VCardText, { class: "pa-3" }, {
            default: _withCtx(() => [
              (error.value)
                ? (_openBlock(), _createBlock(_component_VAlert, {
                    key: 0,
                    type: "error",
                    density: "compact",
                    variant: "tonal",
                    class: "mb-3 text-caption",
                    closable: "",
                    "onClick:close": _cache[0] || (_cache[0] = $event => (error.value = ''))
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(error.value), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              _createElementVNode("div", _hoisted_3, [
                _createElementVNode("div", _hoisted_4, [
                  _createElementVNode("div", _hoisted_5, [
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
                    _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "无效记录", -1))
                  ]),
                  _createElementVNode("div", _hoisted_6, _toDisplayString(invalidItems.value.length), 1)
                ]),
                _createElementVNode("div", _hoisted_7, [
                  _createElementVNode("div", _hoisted_8, [
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
                    _cache[6] || (_cache[6] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "本地源可用", -1))
                  ]),
                  _createElementVNode("div", _hoisted_9, _toDisplayString(localSourceCount.value), 1)
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
                          icon: "mdi-folder-check-outline",
                          size: "17"
                        })
                      ]),
                      _: 1
                    }),
                    _cache[7] || (_cache[7] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "运行目录存在", -1))
                  ]),
                  _createElementVNode("div", _hoisted_12, _toDisplayString(runtimeExistsCount.value), 1)
                ])
              ]),
              _createVNode(_component_VAlert, {
                type: invalidItems.value.length ? 'warning' : 'success',
                variant: "tonal",
                density: "compact",
                icon: "mdi-information",
                class: "text-caption mt-3"
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(invalidItems.value.length ? '存在无法加载的插件记录，可切到配置页选择处理方式。' : '已安装插件记录与当前加载状态一致。'), 1)
                ]),
                _: 1
              }, 8, ["type"]),
              (lastResult.value.message)
                ? (_openBlock(), _createBlock(_component_VAlert, {
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
        ? (_openBlock(), _createElementBlock("div", _hoisted_13, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(invalidItems.value, (plugin) => {
              return (_openBlock(), _createBlock(_component_VCard, {
                key: plugin.id,
                flat: "",
                class: "cip-card cip-plugin-card"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCardItem, { class: "py-2 px-3" }, {
                    append: _withCtx(() => [
                      _createVNode(_component_VChip, {
                        color: plugin.runtime_exists ? 'warning' : 'error',
                        size: "small",
                        variant: "tonal"
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(plugin.runtime_exists ? '需检查' : '缺失'), 1)
                        ]),
                        _: 2
                      }, 1032, ["color"])
                    ]),
                    default: _withCtx(() => [
                      _createVNode(_component_VCardTitle, { class: "text-subtitle-1 cip-break" }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(plugin.id), 1)
                        ]),
                        _: 2
                      }, 1024)
                    ]),
                    _: 2
                  }, 1024),
                  _createVNode(_component_VDivider),
                  _createVNode(_component_VCardText, { class: "py-2 px-3" }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_14, "状态：" + _toDisplayString(plugin.status), 1),
                      _createElementVNode("div", _hoisted_15, _toDisplayString(plugin.runtime_path), 1),
                      _createVNode(_component_VChip, {
                        color: plugin.local_source_path ? 'success' : 'warning',
                        size: "small",
                        variant: "tonal",
                        class: "mt-2"
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
          ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
              _createVNode(_component_VProgressCircular, {
                indeterminate: "",
                color: "primary"
              }),
              _cache[8] || (_cache[8] = _createElementVNode("div", { class: "mt-2 text-medium-emphasis" }, "正在刷新状态...", -1))
            ]))
          : (_openBlock(), _createElementBlock("div", _hoisted_17, [
              _createVNode(_component_VIcon, {
                size: "48",
                color: "success"
              }, {
                default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                  _createTextVNode("mdi-check-circle-outline", -1)
                ]))]),
                _: 1
              }),
              _cache[10] || (_cache[10] = _createElementVNode("div", { class: "mt-2 text-medium-emphasis" }, "没有无效插件", -1)),
              _cache[11] || (_cache[11] = _createElementVNode("div", { class: "text-caption text-medium-emphasis mt-1" }, "当前无需清理。", -1))
            ]))
    ]),
    _createVNode(_component_VFooter, { class: "cip-footer" }, {
      default: _withCtx(() => [
        _createVNode(_component_VContainer, { class: "pa-0" }, {
          default: _withCtx(() => [
            _createVNode(_component_VAlert, {
              type: invalidItems.value.length ? 'warning' : 'success',
              variant: "tonal",
              density: "compact",
              class: "text-caption mb-2"
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(summaryText.value), 1)
              ]),
              _: 1
            }, 8, ["type"]),
            _createElementVNode("div", _hoisted_18, [
              _createVNode(_component_VBtn, {
                color: "info",
                "prepend-icon": "mdi-cog-outline",
                variant: "text",
                size: "small",
                onClick: _cache[1] || (_cache[1] = $event => (emit('switch')))
              }, {
                default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                  _createTextVNode("配置页", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_VSpacer, { class: "cip-footer-spacer" }),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                onClick: loadData
              }, {
                default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                  _createTextVNode("刷新", -1)
                ]))]),
                _: 1
              }, 8, ["loading"]),
              _createVNode(_component_VBtn, {
                color: "grey",
                "prepend-icon": "mdi-close",
                variant: "text",
                size: "small",
                onClick: _cache[2] || (_cache[2] = $event => (emit('close')))
              }, {
                default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                  _createTextVNode("关闭", -1)
                ]))]),
                _: 1
              })
            ])
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-009a7710"]]);

export { Page as default };
