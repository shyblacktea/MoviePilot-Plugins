import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, g as getPluginApi, p as postPluginApi } from './_plugin-vue_export-helper-DGGBqqkU.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "ptb-page" };
const _hoisted_2 = { class: "pa-4" };
const _hoisted_3 = {
  class: "d-flex align-center mb-4",
  style: {"gap":"8px"}
};

const {h,ref,onMounted} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: [Object, Function], default: null },
  config: { type: Object, default: () => ({}) },
},
  emits: ['action', 'switch', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const error = ref('');
const loading = ref(false);
const running = ref(false);
const force = ref(false);
const status = ref({});
const result = ref(null);

const StatCard = (p) => h('div', { class: 'ptb-stat', style: `border-left: 3px solid var(--v-theme-${p.color}, #888)` }, [
  h('div', { class: 'ptb-stat-value' }, String(p.value ?? '-')),
  h('div', { class: 'ptb-stat-label' }, p.label),
]);

async function loadAll() {
  loading.value = true;
  error.value = '';
  try {
    const [st, res] = await Promise.all([
      getPluginApi(props.api, 'status'),
      getPluginApi(props.api, 'result'),
    ]);
    status.value = st || {};
    result.value = res?.result || null;
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
}

async function runComplete() {
  running.value = true;
  error.value = '';
  try {
    const res = await postPluginApi(props.api, 'complete', { force: force.value });
    if (res?.success) {
      result.value = res;
      emit('action');
    } else {
      error.value = res?.error || '补全失败';
    }
  } catch (e) {
    error.value = String(e);
  } finally {
    running.value = false;
  }
}

onMounted(loadAll);

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCheckbox = _resolveComponent("VCheckbox");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VCardActions = _resolveComponent("VCardActions");
  const _component_VCard = _resolveComponent("VCard");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VCard, {
      flat: "",
      class: "ptb-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardItem, null, {
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
            _createVNode(_component_VChip, {
              color: status.value.proxy_running ? 'success' : 'grey',
              size: "small",
              variant: "tonal",
              class: "mr-2"
            }, {
              default: _withCtx(() => [
                _createTextVNode(" 代理 " + _toDisplayString(status.value.proxy_running ? '运行中' : '未运行'), 1)
              ]),
              _: 1
            }, 8, ["color"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-h6" }, {
              default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                _createTextVNode("PLEX 工具箱", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
              default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                _createTextVNode("媒体信息补全", -1)
              ]))]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VDivider),
        _createElementVNode("div", _hoisted_2, [
          (error.value)
            ? (_openBlock(), _createBlock(_component_VAlert, {
                key: 0,
                type: "error",
                variant: "tonal",
                density: "compact",
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
            _createVNode(_component_VBtn, {
              color: "primary",
              loading: running.value,
              "prepend-icon": "mdi-play",
              onClick: runComplete
            }, {
              default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                _createTextVNode(" 开始补全 ", -1)
              ]))]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_VCheckbox, {
              modelValue: force.value,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((force).value = $event)),
              label: "忽略 Plex 繁忙强制写入",
              "hide-details": "",
              density: "compact"
            }, null, 8, ["modelValue"]),
            _createVNode(_component_VSpacer),
            _createVNode(_component_VBtn, {
              icon: "mdi-refresh",
              variant: "text",
              size: "small",
              loading: loading.value,
              onClick: loadAll
            }, null, 8, ["loading"])
          ]),
          (result.value && result.value.strm_parts !== undefined)
            ? (_openBlock(), _createBlock(_component_VRow, { key: 1 }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "STRM 条目",
                        value: result.value.strm_parts,
                        color: "blue"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "已解析",
                        value: result.value.resolved,
                        color: "teal"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "Emby 命中",
                        value: result.value.emby_hits,
                        color: "green"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "ffprobe 命中",
                        value: result.value.ffprobe_hits,
                        color: "cyan"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "写入成功",
                        value: result.value.written_ok,
                        color: "success"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "写入失败",
                        value: result.value.write_failed,
                        color: "error"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "未解析",
                        value: result.value.unresolved,
                        color: "orange"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_VCol, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(StatCard, {
                        label: "来源",
                        value: result.value.source || '-',
                        color: "grey"
                      }, null, 8, ["value"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }))
            : (_openBlock(), _createBlock(_component_VAlert, {
                key: 2,
                type: "info",
                variant: "tonal",
                density: "compact",
                class: "text-caption"
              }, {
                default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                  _createTextVNode(" 暂无补全记录，点击「开始补全」执行一次。 ", -1)
                ]))]),
                _: 1
              })),
          (result.value && result.value.helper_busy)
            ? (_openBlock(), _createBlock(_component_VAlert, {
                key: 3,
                type: "warning",
                variant: "tonal",
                density: "compact",
                class: "mt-3 text-caption"
              }, {
                default: _withCtx(() => [...(_cache[8] || (_cache[8] = [
                  _createTextVNode(" Plex 当前繁忙（播放/扫描中），本次未写入。可勾选强制写入或稍后重试。 ", -1)
                ]))]),
                _: 1
              }))
            : _createCommentVNode("", true)
        ]),
        _createVNode(_component_VDivider),
        _createVNode(_component_VCardActions, { class: "px-4 py-2" }, {
          default: _withCtx(() => [
            _createVNode(_component_VBtn, {
              color: "info",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-cog-outline",
              onClick: _cache[2] || (_cache[2] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                _createTextVNode("配置页", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VSpacer),
            _createVNode(_component_VBtn, {
              color: "grey",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-close",
              onClick: _cache[3] || (_cache[3] = $event => (emit('close')))
            }, {
              default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-356704f2"]]);

export { Page as default };
