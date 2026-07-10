import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, g as getPluginApi, p as postPluginApi } from './_plugin-vue_export-helper-DGGBqqkU.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,createElementBlock:_createElementBlock,renderList:_renderList,Fragment:_Fragment,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "ptb-page" };
const _hoisted_2 = { class: "pa-4" };
const _hoisted_3 = { class: "d-flex align-center mb-4" };
const _hoisted_4 = { class: "text-caption text-medium-emphasis" };
const _hoisted_5 = { class: "d-flex align-center mb-2" };
const _hoisted_6 = {
  key: 0,
  class: "text-body-2 font-weight-medium mb-2"
};
const _hoisted_7 = { class: "text-caption" };
const _hoisted_8 = {
  key: 0,
  class: "text-caption text-error ml-2"
};
const _hoisted_9 = { class: "d-flex align-center mt-5 mb-2" };
const _hoisted_10 = { class: "ptb-block-title mb-0" };
const _hoisted_11 = ["onClick"];
const _hoisted_12 = { style: {"width":"28px"} };
const _hoisted_13 = { class: "text-caption" };
const _hoisted_14 = { class: "text-caption" };
const _hoisted_15 = { class: "text-right" };
const _hoisted_16 = { class: "text-right text-green" };
const _hoisted_17 = { class: "text-right text-success" };
const _hoisted_18 = { key: 0 };
const _hoisted_19 = {
  colspan: "7",
  class: "ptb-detail-cell"
};
const _hoisted_20 = { class: "text-caption flex-grow-1" };
const _hoisted_21 = {
  key: 0,
  class: "text-caption text-error ml-2"
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
const status = ref({});
const lastPlay = ref(null);
const history = ref([]);
const expanded = ref(-1);
const clearing = ref('');

async function clearData(target) {
  clearing.value = target === 'play_history' ? 'history' : 'last';
  error.value = '';
  try {
    const res = await postPluginApi(props.api, 'clear_completion_data', { target });
    if (!res?.success) throw new Error(res?.error || '清理失败')
    if (target === 'play_history') history.value = [];
    else lastPlay.value = null;
    expanded.value = -1;
  } catch (e) {
    error.value = String(e);
  } finally {
    clearing.value = '';
  }
}

function statusLabel(s) {
  return ({ written: '已写入', resolved: '已解析', unresolved: '未命中', write_failed: '写入失败', busy: 'Plex忙' })[s] || (s || '-')
}

function statusColor(s) {
  return ({ written: 'success', resolved: 'teal', unresolved: 'orange', write_failed: 'error', busy: 'warning' })[s] || 'grey'
}

const StatCard = (p) => h('div', { class: 'ptb-stat', style: `border-left: 3px solid var(--v-theme-${p.color}, #888)` }, [
  h('div', { class: 'ptb-stat-value' }, String(p.value ?? '-')),
  h('div', { class: 'ptb-stat-label' }, p.label),
]);

function fmtTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts * 1000);
  const p = (n) => String(n).padStart(2, '0');
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function sourceLabel(s) {
  return ({ play_stop: '播放停止', webhook: 'Webhook', schedule: '定时', api: '手动' })[s] || (s || '-')
}

async function loadAll() {
  loading.value = true;
  error.value = '';
  try {
    const [st, res] = await Promise.all([
      getPluginApi(props.api, 'status'),
      getPluginApi(props.api, 'result'),
    ]);
    status.value = st || {};
    lastPlay.value = res?.last_play_result || null;
    history.value = Array.isArray(res?.play_history) ? res.play_history : [];
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
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
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VTable = _resolveComponent("VTable");
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
              default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                _createTextVNode("PLEX 工具箱", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
              default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                _createTextVNode("STRM 媒体信息补全 · 播放驱动增量", -1)
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
            _createElementVNode("div", _hoisted_4, " 播放停止后自动对本集 + 后 " + _toDisplayString(__props.config.forward_episodes ?? 5) + " 集做增量补全，已补全的自动跳过。 ", 1),
            _createVNode(_component_VSpacer),
            _createVNode(_component_VBtn, {
              icon: "mdi-refresh",
              variant: "text",
              size: "small",
              loading: loading.value,
              onClick: loadAll
            }, null, 8, ["loading"])
          ]),
          _createElementVNode("div", _hoisted_5, [
            _cache[8] || (_cache[8] = _createElementVNode("div", { class: "ptb-block-title mb-0" }, "最近一次补全", -1)),
            _createVNode(_component_VSpacer),
            (lastPlay.value && lastPlay.value.strm_parts !== undefined)
              ? (_openBlock(), _createBlock(_component_VBtn, {
                  key: 0,
                  color: "grey",
                  variant: "text",
                  size: "x-small",
                  "prepend-icon": "mdi-broom",
                  loading: clearing.value === 'last',
                  onClick: _cache[1] || (_cache[1] = $event => (clearData('last_play_result')))
                }, {
                  default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                    _createTextVNode("清理", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"]))
              : _createCommentVNode("", true)
          ]),
          (lastPlay.value && lastPlay.value.strm_parts !== undefined)
            ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                (lastPlay.value.label)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_6, [
                      _createVNode(_component_VIcon, {
                        icon: "mdi-motion-play-outline",
                        size: "16",
                        class: "mr-1"
                      }),
                      _createTextVNode(_toDisplayString(lastPlay.value.label), 1)
                    ]))
                  : _createCommentVNode("", true),
                _createVNode(_component_VRow, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCol, {
                      cols: "6",
                      md: "3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(StatCard, {
                          label: "本次条目数",
                          value: lastPlay.value.strm_parts,
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
                          value: lastPlay.value.resolved,
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
                          value: lastPlay.value.emby_hits,
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
                          label: "写入成功",
                          value: lastPlay.value.written_ok,
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
                          value: lastPlay.value.write_failed,
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
                          value: lastPlay.value.unresolved,
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
                          value: sourceLabel(lastPlay.value.source),
                          color: "grey"
                        }, null, 8, ["value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (lastPlay.value.items && lastPlay.value.items.length)
                  ? (_openBlock(), _createBlock(_component_VTable, {
                      key: 1,
                      density: "compact",
                      class: "ptb-history mt-3"
                    }, {
                      default: _withCtx(() => [
                        _cache[9] || (_cache[9] = _createElementVNode("thead", null, [
                          _createElementVNode("tr", null, [
                            _createElementVNode("th", null, "条目"),
                            _createElementVNode("th", null, "状态")
                          ])
                        ], -1)),
                        _createElementVNode("tbody", null, [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(lastPlay.value.items, (it, i) => {
                            return (_openBlock(), _createElementBlock("tr", { key: i }, [
                              _createElementVNode("td", _hoisted_7, _toDisplayString(it.label || ('part ' + it.part_id)), 1),
                              _createElementVNode("td", null, [
                                _createVNode(_component_VChip, {
                                  color: statusColor(it.status),
                                  size: "x-small",
                                  variant: "tonal"
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(statusLabel(it.status)), 1)
                                  ]),
                                  _: 2
                                }, 1032, ["color"]),
                                (it.error)
                                  ? (_openBlock(), _createElementBlock("span", _hoisted_8, _toDisplayString(it.error), 1))
                                  : _createCommentVNode("", true)
                              ])
                            ]))
                          }), 128))
                        ])
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ], 64))
            : (_openBlock(), _createBlock(_component_VAlert, {
                key: 2,
                type: "info",
                variant: "tonal",
                density: "compact",
                class: "text-caption"
              }, {
                default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
                  _createTextVNode(" 暂无补全记录。播放任意 STRM 剧集/电影并停止后，会自动触发一次增量补全。 ", -1)
                ]))]),
                _: 1
              })),
          (lastPlay.value && lastPlay.value.helper_busy)
            ? (_openBlock(), _createBlock(_component_VAlert, {
                key: 3,
                type: "warning",
                variant: "tonal",
                density: "compact",
                class: "mt-3 text-caption"
              }, {
                default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                  _createTextVNode(" Plex 当前繁忙（播放/扫描中），本次未写入，稍后重试。 ", -1)
                ]))]),
                _: 1
              }))
            : _createCommentVNode("", true),
          _createElementVNode("div", _hoisted_9, [
            _createElementVNode("div", _hoisted_10, "补全历史（最近 " + _toDisplayString(history.value.length) + " 条）", 1),
            _createVNode(_component_VSpacer),
            (history.value.length)
              ? (_openBlock(), _createBlock(_component_VBtn, {
                  key: 0,
                  color: "grey",
                  variant: "text",
                  size: "x-small",
                  "prepend-icon": "mdi-broom",
                  loading: clearing.value === 'history',
                  onClick: _cache[2] || (_cache[2] = $event => (clearData('play_history')))
                }, {
                  default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                    _createTextVNode("清空历史", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"]))
              : _createCommentVNode("", true)
          ]),
          (history.value.length)
            ? (_openBlock(), _createBlock(_component_VTable, {
                key: 4,
                density: "compact",
                class: "ptb-history"
              }, {
                default: _withCtx(() => [
                  _cache[13] || (_cache[13] = _createElementVNode("thead", null, [
                    _createElementVNode("tr", null, [
                      _createElementVNode("th"),
                      _createElementVNode("th", null, "时间"),
                      _createElementVNode("th", null, "条目"),
                      _createElementVNode("th", { class: "text-right" }, "处理"),
                      _createElementVNode("th", { class: "text-right" }, "命中"),
                      _createElementVNode("th", { class: "text-right" }, "写入"),
                      _createElementVNode("th", { class: "text-right" }, "失败")
                    ])
                  ], -1)),
                  _createElementVNode("tbody", null, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(history.value, (h, i) => {
                      return (_openBlock(), _createElementBlock(_Fragment, { key: i }, [
                        _createElementVNode("tr", {
                          class: "ptb-row",
                          onClick: $event => (expanded.value = expanded.value === i ? -1 : i)
                        }, [
                          _createElementVNode("td", _hoisted_12, [
                            (h.items && h.items.length)
                              ? (_openBlock(), _createBlock(_component_VIcon, {
                                  key: 0,
                                  size: "14",
                                  icon: expanded.value === i ? 'mdi-chevron-down' : 'mdi-chevron-right'
                                }, null, 8, ["icon"]))
                              : _createCommentVNode("", true)
                          ]),
                          _createElementVNode("td", _hoisted_13, _toDisplayString(fmtTime(h.ts)), 1),
                          _createElementVNode("td", _hoisted_14, _toDisplayString(h.label || ('rk=' + h.rating_key)), 1),
                          _createElementVNode("td", _hoisted_15, _toDisplayString(h.strm_parts), 1),
                          _createElementVNode("td", _hoisted_16, _toDisplayString(h.emby_hits), 1),
                          _createElementVNode("td", _hoisted_17, _toDisplayString(h.written_ok), 1),
                          _createElementVNode("td", {
                            class: _normalizeClass(["text-right", h.write_failed ? 'text-error' : ''])
                          }, _toDisplayString(h.write_failed), 3)
                        ], 8, _hoisted_11),
                        (expanded.value === i && h.items && h.items.length)
                          ? (_openBlock(), _createElementBlock("tr", _hoisted_18, [
                              _createElementVNode("td", _hoisted_19, [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(h.items, (it, j) => {
                                  return (_openBlock(), _createElementBlock("div", {
                                    key: j,
                                    class: "d-flex align-center py-1"
                                  }, [
                                    _createElementVNode("span", _hoisted_20, _toDisplayString(it.label || ('part ' + it.part_id)), 1),
                                    _createVNode(_component_VChip, {
                                      color: statusColor(it.status),
                                      size: "x-small",
                                      variant: "tonal"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(statusLabel(it.status)), 1)
                                      ]),
                                      _: 2
                                    }, 1032, ["color"]),
                                    (it.error)
                                      ? (_openBlock(), _createElementBlock("span", _hoisted_21, _toDisplayString(it.error), 1))
                                      : _createCommentVNode("", true)
                                  ]))
                                }), 128))
                              ])
                            ]))
                          : _createCommentVNode("", true)
                      ], 64))
                    }), 128))
                  ])
                ]),
                _: 1
              }))
            : (_openBlock(), _createBlock(_component_VAlert, {
                key: 5,
                type: "info",
                variant: "tonal",
                density: "compact",
                class: "text-caption"
              }, {
                default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                  _createTextVNode("暂无历史记录。", -1)
                ]))]),
                _: 1
              }))
        ]),
        _createVNode(_component_VDivider),
        _createVNode(_component_VCardActions, { class: "px-4 py-2" }, {
          default: _withCtx(() => [
            _createVNode(_component_VBtn, {
              color: "info",
              variant: "text",
              size: "small",
              "prepend-icon": "mdi-cog-outline",
              onClick: _cache[3] || (_cache[3] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
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
              onClick: _cache[4] || (_cache[4] = $event => (emit('close')))
            }, {
              default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-498954a6"]]);

export { Page as default };
