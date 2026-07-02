import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "main-container" };
const _hoisted_2 = { class: "scroll-content" };
const _hoisted_3 = { class: "summary-item" };
const _hoisted_4 = { class: "summary-item" };
const _hoisted_5 = { class: "summary-item" };
const _hoisted_6 = { class: "summary-item" };
const _hoisted_7 = { class: "result-title" };
const _hoisted_8 = { class: "text-subtitle-1" };
const _hoisted_9 = { class: "text-caption text-medium-emphasis" };
const _hoisted_10 = { class: "episode-line" };
const _hoisted_11 = { class: "text-caption text-medium-emphasis mb-2" };
const _hoisted_12 = { class: "text-caption path-line" };
const _hoisted_13 = { class: "candidate-title" };
const _hoisted_14 = { class: "text-right" };
const _hoisted_15 = {
  key: 1,
  class: "empty-panel"
};
const _hoisted_16 = {
  key: 1,
  class: "preview-box"
};

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
const scanning = ref(false);
const error = ref('');
const status = ref({});
const items = ref([]);
const ruleRecords = ref([]);
const previewDialog = ref(false);
const preview = ref(null);
const previewError = ref('');

const reasonCount = computed(() => {
  return items.value.reduce((acc, item) => {
    acc[item.reason] = (acc[item.reason] || 0) + 1;
    return acc
  }, {})
});

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
}

function reasonText(reason) {
  return {
    no_pt_resource: '暂无资源',
    recognition_issue: '疑似识别',
    rule_blocked: '规则拦截',
    downloadable: '可下载',
    search_failed: '搜索失败',
  }[reason] || reason || '未知'
}

function reasonColor(reason) {
  return {
    no_pt_resource: 'grey',
    recognition_issue: 'warning',
    rule_blocked: 'info',
    downloadable: 'success',
    search_failed: 'error',
  }[reason] || 'grey'
}

async function loadData() {
  loading.value = true;
  error.value = '';
  try {
    const [statusResponse, resultsResponse] = await Promise.all([
      props.api.get('plugin/SubscribePlus/status'),
      props.api.get('plugin/SubscribePlus/results'),
    ]);
    status.value = unwrap(statusResponse);
    const data = unwrap(resultsResponse);
    items.value = data.items || [];
    ruleRecords.value = data.rule_records || status.value.rule_records || [];
    emit('action');
  } catch (err) {
    error.value = err?.message || '读取诊断结果失败';
  } finally {
    loading.value = false;
  }
}

async function runScan() {
  scanning.value = true;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/scan', {});
    await loadData();
  } catch (err) {
    error.value = err?.message || '手动扫描失败';
  } finally {
    scanning.value = false;
  }
}

async function previewRule(item, candidate) {
  previewDialog.value = true;
  preview.value = null;
  previewError.value = '';
  try {
    const pattern = candidate.site || candidate.site_name || '';
    const response = await props.api.post('plugin/SubscribePlus/rule_preview', {
      subscribe_id: item.subscribe_id,
      pattern,
    });
    const body = response?.data ?? response ?? {};
    const data = body?.data ?? body;
    if (body.success === false || data.success === false) {
      previewError.value = body.message || data.message || '生成预览失败';
      return
    }
    preview.value = data;
  } catch (err) {
    previewError.value = err?.message || '生成预览失败';
  }
}

async function confirmRule() {
  if (!preview.value?.token) return
  try {
    await props.api.post('plugin/SubscribePlus/rule_confirm', { token: preview.value.token });
    previewDialog.value = false;
    await loadData();
  } catch (err) {
    previewError.value = err?.message || '确认修改失败';
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
  const _component_v_table = _resolveComponent("v-table");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_container = _resolveComponent("v-container");
  const _component_v_footer = _resolveComponent("v-footer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createVNode(_component_v_card, {
        flat: "",
        class: "rounded border mb-3"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "title-bar" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                icon: "mdi-television-play",
                color: "primary",
                size: "small"
              }),
              _cache[4] || (_cache[4] = _createElementVNode("span", null, "订阅下载增强", -1)),
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
          _createVNode(_component_v_card_text, { class: "content" }, {
            default: _withCtx(() => [
              (error.value)
                ? (_openBlock(), _createBlock(_component_v_alert, {
                    key: 0,
                    type: "error",
                    density: "compact",
                    variant: "tonal",
                    class: "mb-3 text-caption",
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
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_3, [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-calendar-clock",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[5] || (_cache[5] = _createElementVNode("span", null, "最近扫描", -1)),
                        _createElementVNode("strong", null, _toDisplayString(status.value.last_scan || '-'), 1)
                      ])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_4, [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-alert-decagram-outline",
                          color: "warning",
                          size: "small"
                        }),
                        _cache[6] || (_cache[6] = _createElementVNode("span", null, "待处理", -1)),
                        _createElementVNode("strong", null, _toDisplayString(items.value.length), 1)
                      ])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_5, [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-download-circle-outline",
                          color: "success",
                          size: "small"
                        }),
                        _cache[7] || (_cache[7] = _createElementVNode("span", null, "可下载", -1)),
                        _createElementVNode("strong", null, _toDisplayString(reasonCount.value.downloadable || 0), 1)
                      ])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_6, [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-file-document-edit-outline",
                          color: "info",
                          size: "small"
                        }),
                        _cache[8] || (_cache[8] = _createElementVNode("span", null, "规则记录", -1)),
                        _createElementVNode("strong", null, _toDisplayString(ruleRecords.value.length), 1)
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
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(items.value, (item) => {
        return (_openBlock(), _createBlock(_component_v_card, {
          key: `${item.subscribe_id}-${item.created_at}`,
          flat: "",
          class: "rounded border mb-3 result-card"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "result-header" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_7, [
                  _createElementVNode("div", _hoisted_8, _toDisplayString(item.title), 1),
                  _createElementVNode("div", _hoisted_9, "TMDB " + _toDisplayString(item.tmdbid) + " / S" + _toDisplayString(item.season) + " / " + _toDisplayString(item.category), 1)
                ]),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_chip, {
                  color: reasonColor(item.reason),
                  size: "small",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(reasonText(item.reason)), 1)
                  ]),
                  _: 2
                }, 1032, ["color"])
              ]),
              _: 2
            }, 1024),
            _createVNode(_component_v_card_text, { class: "content" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_10, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(item.episodes || [], (episode) => {
                    return (_openBlock(), _createBlock(_component_v_chip, {
                      key: episode.episode,
                      size: "small",
                      variant: "tonal",
                      class: "mr-1 mb-1"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(" E" + _toDisplayString(episode.episode) + " / " + _toDisplayString(episode.air_date), 1)
                      ]),
                      _: 2
                    }, 1024))
                  }), 128))
                ]),
                _createElementVNode("div", _hoisted_11, _toDisplayString(item.message), 1),
                _createElementVNode("div", _hoisted_12, "站点：" + _toDisplayString((item.sites || []).join(', ') || 'MP 默认搜索站点'), 1),
                (item.candidates?.length)
                  ? (_openBlock(), _createBlock(_component_v_table, {
                      key: 0,
                      density: "compact",
                      class: "mt-2"
                    }, {
                      default: _withCtx(() => [
                        _cache[10] || (_cache[10] = _createElementVNode("thead", null, [
                          _createElementVNode("tr", null, [
                            _createElementVNode("th", null, "站点"),
                            _createElementVNode("th", null, "标题"),
                            _createElementVNode("th", null, "做种"),
                            _createElementVNode("th", { class: "text-right" }, "操作")
                          ])
                        ], -1)),
                        _createElementVNode("tbody", null, [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(item.candidates.slice(0, 8), (candidate) => {
                            return (_openBlock(), _createElementBlock("tr", {
                              key: candidate.candidate_id || candidate.title
                            }, [
                              _createElementVNode("td", null, _toDisplayString(candidate.site_name || candidate.site), 1),
                              _createElementVNode("td", _hoisted_13, _toDisplayString(candidate.title), 1),
                              _createElementVNode("td", null, _toDisplayString(candidate.seeders || 0), 1),
                              _createElementVNode("td", _hoisted_14, [
                                _createVNode(_component_v_btn, {
                                  color: "primary",
                                  variant: "text",
                                  size: "small",
                                  "prepend-icon": "mdi-file-eye-outline",
                                  onClick: $event => (previewRule(item, candidate))
                                }, {
                                  default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                                    _createTextVNode(" 规则预览 ", -1)
                                  ]))]),
                                  _: 1
                                }, 8, ["onClick"])
                              ])
                            ]))
                          }), 128))
                        ])
                      ]),
                      _: 2
                    }, 1024))
                  : _createCommentVNode("", true)
              ]),
              _: 2
            }, 1024)
          ]),
          _: 2
        }, 1024))
      }), 128)),
      _createVNode(_component_v_card, {
        flat: "",
        class: "rounded border mb-3"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "small-title" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                icon: "mdi-history",
                color: "primary",
                size: "small"
              }),
              _cache[11] || (_cache[11] = _createElementVNode("span", null, "规则修改记录", -1))
            ]),
            _: 1
          }),
          _createVNode(_component_v_card_text, { class: "content" }, {
            default: _withCtx(() => [
              (ruleRecords.value.length)
                ? (_openBlock(), _createBlock(_component_v_list, {
                    key: 0,
                    density: "compact",
                    lines: "two"
                  }, {
                    default: _withCtx(() => [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(ruleRecords.value, (record) => {
                        return (_openBlock(), _createBlock(_component_v_list_item, {
                          key: `${record.subscribe_id}-${record.created_at}`,
                          title: `${record.field}: ${record.old_value || '-'} -> ${record.new_value || '-'}`,
                          subtitle: `${record.source || '-'} / ${record.created_at || '-'}`
                        }, null, 8, ["title", "subtitle"]))
                      }), 128))
                    ]),
                    _: 1
                  }))
                : (_openBlock(), _createElementBlock("div", _hoisted_15, "暂无记录"))
            ]),
            _: 1
          })
        ]),
        _: 1
      })
    ]),
    _createVNode(_component_v_footer, { class: "footer-bar" }, {
      default: _withCtx(() => [
        _createVNode(_component_v_container, { class: "d-flex align-center action-bar" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "info",
              "prepend-icon": "mdi-cog-outline",
              variant: "text",
              size: "small",
              onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                _createTextVNode("配置页", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_spacer, { class: "action-spacer" }),
            _createVNode(_component_v_btn, {
              color: "primary",
              "prepend-icon": "mdi-radar",
              variant: "text",
              size: "small",
              loading: scanning.value,
              onClick: runScan
            }, {
              default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                _createTextVNode("手动扫描", -1)
              ]))]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "grey",
              "prepend-icon": "mdi-refresh",
              variant: "text",
              size: "small",
              loading: loading.value,
              onClick: loadData
            }, {
              default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                _createTextVNode("刷新", -1)
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
              default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
                _createTextVNode("关闭", -1)
              ]))]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_dialog, {
      modelValue: previewDialog.value,
      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((previewDialog).value = $event)),
      "max-width": "720"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
                _createTextVNode("规则修改预览", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                (previewError.value)
                  ? (_openBlock(), _createBlock(_component_v_alert, {
                      key: 0,
                      type: "error",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-2"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(previewError.value), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                (preview.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
                      _createElementVNode("div", null, "旧 include：" + _toDisplayString(preview.value.old_include || '-'), 1),
                      _createElementVNode("div", null, "新 include：" + _toDisplayString(preview.value.new_include || '-'), 1)
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[2] || (_cache[2] = $event => (previewDialog.value = false))
                }, {
                  default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
                    _createTextVNode("返回", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  variant: "text",
                  disabled: !preview.value?.token,
                  onClick: confirmRule
                }, {
                  default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
                    _createTextVNode("确认修改", -1)
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
    }, 8, ["modelValue"])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-a75b59d5"]]);

export { Page as default };
