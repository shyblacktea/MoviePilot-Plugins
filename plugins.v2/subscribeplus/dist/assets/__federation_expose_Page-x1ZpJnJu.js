import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "main-container" };
const _hoisted_2 = { class: "scroll-content" };
const _hoisted_3 = { class: "summary-item" };
const _hoisted_4 = { class: "summary-item" };
const _hoisted_5 = { class: "summary-item" };
const _hoisted_6 = { class: "summary-item" };
const _hoisted_7 = {
  key: 3,
  class: "empty-panel"
};
const _hoisted_8 = {
  key: 1,
  class: "empty-panel"
};
const _hoisted_9 = { class: "result-title" };
const _hoisted_10 = { class: "text-subtitle-1" };
const _hoisted_11 = { class: "text-caption text-medium-emphasis" };
const _hoisted_12 = { class: "episode-line" };
const _hoisted_13 = { class: "text-caption text-medium-emphasis mb-2" };
const _hoisted_14 = {
  key: 0,
  class: "candidate-table-wrap mt-2"
};
const _hoisted_15 = { class: "candidate-site" };
const _hoisted_16 = { class: "candidate-title" };
const _hoisted_17 = { class: "candidate-seeders" };
const _hoisted_18 = { class: "text-right candidate-actions" };
const _hoisted_19 = {
  key: 1,
  class: "suggestion-panel"
};
const _hoisted_20 = {
  key: 2,
  class: "preview-box"
};
const _hoisted_21 = { key: 0 };

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
const clearing = ref(false);
const clearingRules = ref(false);
const deletingRuleId = ref('');
const deletingResultId = ref('');
const error = ref('');
const status = ref({});
const items = ref([]);
const ruleRecords = ref([]);
const identifierRecords = ref([]);
const identifierAutoTitle = ref('');
const identifierManualTitle = ref('');
const identifierManualType = ref('tv');
const identifierManualTmdbid = ref('');
const identifierBusy = ref('');
const identifierError = ref('');
const identifierMessage = ref('');
const previewDialog = ref(false);
const preview = ref(null);
const previewError = ref('');
const previewContext = ref(null);
const previewLoading = ref('');
const ruleSuggestions = ref([]);

const mediaTypeOptions = [
  { title: 'TV', value: 'tv' },
  { title: 'Movie', value: 'movie' },
];

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

function formatPreviewSites(value, emptyText = '-') {
  const items = Array.isArray(value) ? value : [];
  const text = items.filter(item => item !== undefined && item !== null && String(item).trim()).map(item => String(item)).join(', ');
  return text || emptyText
}

function identifierModeText(mode) {
  return mode === 'manual' ? '手动' : '自动'
}

function identifierStatusText(statusValue) {
  return statusValue === 'success' ? '成功' : '失败'
}

function identifierStatusColor(statusValue) {
  return statusValue === 'success' ? 'success' : 'error'
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
    identifierRecords.value = data.identifier_records || status.value.identifier_records || [];
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

async function clearResults() {
  clearing.value = true;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/results/clear', {});
    await loadData();
  } catch (err) {
    error.value = err?.message || '清除诊断结果失败';
  } finally {
    clearing.value = false;
  }
}

async function deleteResult(item) {
  if (!item?.result_id) {
    error.value = '该诊断结果缺少标识，无法删除，请先刷新';
    return
  }
  deletingResultId.value = item.result_id;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/results/delete', { result_id: item.result_id });
    await loadData();
  } catch (err) {
    error.value = err?.message || '删除诊断结果失败';
  } finally {
    deletingResultId.value = '';
  }
}

async function clearRuleRecords() {
  clearingRules.value = true;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/rule_records/clear', {});
    await loadData();
  } catch (err) {
    error.value = err?.message || '清空规则修改记录失败';
  } finally {
    clearingRules.value = false;
  }
}

async function deleteRuleRecord(record) {
  if (!record?.record_id) {
    error.value = '该规则记录缺少标识，无法删除，请先刷新';
    return
  }
  deletingRuleId.value = record.record_id;
  error.value = '';
  try {
    await props.api.post('plugin/SubscribePlus/rule_records/delete', { record_id: record.record_id });
    await loadData();
  } catch (err) {
    error.value = err?.message || '删除规则记录失败';
  } finally {
    deletingRuleId.value = '';
  }
}

function readActionResponse(response, fallback) {
  const body = response?.data ?? response ?? {};
  const data = body?.data ?? body;
  if (body.success === false || data.success === false) {
    return { success: false, message: body.message || data.message || fallback }
  }
  return { success: true, message: body.message || data.message || fallback }
}

async function runIdentifierAuto() {
  const title = identifierAutoTitle.value.trim();
  identifierError.value = '';
  identifierMessage.value = '';
  if (!title) {
    identifierError.value = '请填写媒体文件名';
    return
  }
  identifierBusy.value = 'auto';
  try {
    const response = await props.api.post('plugin/SubscribePlus/identifier_auto', { title });
    const result = readActionResponse(response, '已提交自动处理');
    if (!result.success) {
      identifierError.value = result.message;
      return
    }
    identifierMessage.value = result.message;
    await loadData();
  } catch (err) {
    identifierError.value = err?.message || '自动处理失败';
  } finally {
    identifierBusy.value = '';
  }
}

async function runIdentifierManual() {
  const title = identifierManualTitle.value.trim();
  const tmdbid = identifierManualTmdbid.value.trim();
  identifierError.value = '';
  identifierMessage.value = '';
  if (!title || !tmdbid) {
    identifierError.value = '请填写媒体文件名和 TMDB ID';
    return
  }
  identifierBusy.value = 'manual';
  try {
    const response = await props.api.post('plugin/SubscribePlus/identifier_manual', {
      title,
      media_type: identifierManualType.value,
      tmdbid,
    });
    const result = readActionResponse(response, '已提交手动处理');
    if (!result.success) {
      identifierError.value = result.message;
      return
    }
    identifierMessage.value = result.message;
    await loadData();
  } catch (err) {
    identifierError.value = err?.message || '手动处理失败';
  } finally {
    identifierBusy.value = '';
  }
}

async function previewRule(item, candidate) {
  previewDialog.value = true;
  preview.value = null;
  previewError.value = '';
  previewContext.value = { item, candidate };
  previewLoading.value = '';
  ruleSuggestions.value = [];
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_suggestions', {
      diagnosis: item,
      candidate,
    });
    const body = response?.data ?? response ?? {};
    const data = body?.data ?? body;
    if (body.success === false || data.success === false) {
      previewError.value = body.message || data.message || '生成规则建议失败';
      return
    }
    ruleSuggestions.value = data.items || [];
    if (!ruleSuggestions.value.length) {
      previewError.value = '没有可添加的官组、平台或 PT 站点建议';
    } else if (ruleSuggestions.value.length === 1) {
      await previewRuleSuggestion(ruleSuggestions.value[0]);
    }
  } catch (err) {
    previewError.value = err?.message || '生成规则建议失败';
  }
}

async function previewRuleSuggestion(suggestion) {
  if (!previewContext.value?.item || !suggestion?.pattern) return
  preview.value = null;
  previewError.value = '';
  previewLoading.value = suggestion.pattern;
  try {
    const response = await props.api.post('plugin/SubscribePlus/rule_preview', {
      subscribe_id: previewContext.value.item.subscribe_id,
      pattern: suggestion.pattern,
      selected_text: suggestion.text,
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
  } finally {
    previewLoading.value = '';
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
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_table = _resolveComponent("v-table");
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
              _cache[8] || (_cache[8] = _createElementVNode("span", null, "订阅下载增强", -1)),
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
                        _cache[9] || (_cache[9] = _createElementVNode("span", null, "最近扫描", -1)),
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
                        _cache[10] || (_cache[10] = _createElementVNode("span", null, "待处理", -1)),
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
                        _cache[11] || (_cache[11] = _createElementVNode("span", null, "可下载", -1)),
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
                        _cache[12] || (_cache[12] = _createElementVNode("span", null, "规则修改", -1)),
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
      _createVNode(_component_v_card, {
        flat: "",
        class: "rounded border mb-3"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "small-title" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                icon: "mdi-tag-plus-outline",
                color: "primary",
                size: "small"
              }),
              _cache[13] || (_cache[13] = _createElementVNode("span", null, "自定义识别词", -1)),
              _createVNode(_component_v_spacer),
              _createVNode(_component_v_chip, {
                size: "small",
                variant: "tonal"
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(identifierRecords.value.length), 1)
                ]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createVNode(_component_v_card_text, { class: "content" }, {
            default: _withCtx(() => [
              (identifierError.value)
                ? (_openBlock(), _createBlock(_component_v_alert, {
                    key: 0,
                    type: "error",
                    density: "compact",
                    variant: "tonal",
                    class: "mb-3 text-caption",
                    closable: ""
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(identifierError.value), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              (identifierMessage.value)
                ? (_openBlock(), _createBlock(_component_v_alert, {
                    key: 1,
                    type: "success",
                    density: "compact",
                    variant: "tonal",
                    class: "mb-3 text-caption",
                    closable: ""
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(identifierMessage.value), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              _createVNode(_component_v_row, {
                class: "identifier-row",
                align: "center"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "8"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: identifierAutoTitle.value,
                        "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((identifierAutoTitle).value = $event)),
                        label: "媒体文件名",
                        density: "compact",
                        variant: "outlined",
                        "hide-details": "",
                        clearable: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "4",
                    class: "identifier-action-col"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_btn, {
                        color: "primary",
                        "prepend-icon": "mdi-auto-fix",
                        variant: "text",
                        size: "small",
                        loading: identifierBusy.value === 'auto',
                        onClick: runIdentifierAuto
                      }, {
                        default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                          _createTextVNode(" 自动处理 ", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_divider, { class: "my-3" }),
              _createVNode(_component_v_row, {
                class: "identifier-row",
                align: "center"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "5"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: identifierManualTitle.value,
                        "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((identifierManualTitle).value = $event)),
                        label: "媒体文件名",
                        density: "compact",
                        variant: "outlined",
                        "hide-details": "",
                        clearable: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "6",
                    md: "2"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_select, {
                        modelValue: identifierManualType.value,
                        "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((identifierManualType).value = $event)),
                        items: mediaTypeOptions,
                        label: "类型",
                        density: "compact",
                        variant: "outlined",
                        "hide-details": ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "6",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: identifierManualTmdbid.value,
                        "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((identifierManualTmdbid).value = $event)),
                        label: "TMDB ID",
                        placeholder: "填写 TMDB 的 ID",
                        density: "compact",
                        variant: "outlined",
                        "hide-details": "",
                        clearable: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "2",
                    class: "identifier-action-col"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_btn, {
                        color: "primary",
                        "prepend-icon": "mdi-pencil-plus-outline",
                        variant: "text",
                        size: "small",
                        loading: identifierBusy.value === 'manual',
                        onClick: runIdentifierManual
                      }, {
                        default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
                          _createTextVNode(" 手动处理 ", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              (identifierRecords.value.length)
                ? (_openBlock(), _createBlock(_component_v_list, {
                    key: 2,
                    density: "compact",
                    lines: "two",
                    class: "mt-2"
                  }, {
                    default: _withCtx(() => [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(identifierRecords.value, (record) => {
                        return (_openBlock(), _createBlock(_component_v_list_item, {
                          key: `${record.mode}-${record.candidate_title}-${record.created_at}`,
                          title: `${identifierModeText(record.mode)}：${record.candidate_title || record.title || '-'}`,
                          subtitle: `${record.message || '-'} / ${record.created_at || '-'}`
                        }, {
                          append: _withCtx(() => [
                            _createVNode(_component_v_chip, {
                              color: identifierStatusColor(record.status),
                              size: "small",
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(identifierStatusText(record.status)), 1)
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
                : (_openBlock(), _createElementBlock("div", _hoisted_7, "暂无识别词记录"))
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
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
              _cache[17] || (_cache[17] = _createElementVNode("span", null, "规则修改记录", -1)),
              _createVNode(_component_v_spacer),
              (ruleRecords.value.length)
                ? (_openBlock(), _createBlock(_component_v_btn, {
                    key: 0,
                    color: "warning",
                    variant: "text",
                    size: "small",
                    "prepend-icon": "mdi-delete-sweep-outline",
                    loading: clearingRules.value,
                    onClick: clearRuleRecords
                  }, {
                    default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
                      _createTextVNode(" 清空 ", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"]))
                : _createCommentVNode("", true)
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
                          key: record.record_id || `${record.subscribe_id}-${record.created_at}`,
                          title: `【${record.subscribe_name || ('订阅#' + record.subscribe_id)}】${record.change_type || record.field}`,
                          subtitle: `${record.old_value || '-'} → ${record.new_value || '-'} （${record.source || '-'} / ${record.created_at || '-'}）`
                        }, {
                          append: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              icon: "mdi-delete-outline",
                              color: "error",
                              variant: "text",
                              size: "small",
                              loading: deletingRuleId.value === record.record_id,
                              onClick: $event => (deleteRuleRecord(record))
                            }, null, 8, ["loading", "onClick"])
                          ]),
                          _: 2
                        }, 1032, ["title", "subtitle"]))
                      }), 128))
                    ]),
                    _: 1
                  }))
                : (_openBlock(), _createElementBlock("div", _hoisted_8, "暂无记录"))
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(items.value, (item) => {
        return (_openBlock(), _createBlock(_component_v_card, {
          key: item.result_id || `${item.subscribe_id}-${item.created_at}`,
          flat: "",
          class: "rounded border mb-3 result-card"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "result-header" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_9, [
                  _createElementVNode("div", _hoisted_10, _toDisplayString(item.title), 1),
                  _createElementVNode("div", _hoisted_11, "TMDB " + _toDisplayString(item.tmdbid) + " / S" + _toDisplayString(item.season) + " / " + _toDisplayString(item.category), 1)
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
                }, 1032, ["color"]),
                _createVNode(_component_v_btn, {
                  icon: "mdi-delete-outline",
                  color: "error",
                  variant: "text",
                  size: "small",
                  class: "ml-2",
                  loading: deletingResultId.value === item.result_id,
                  onClick: $event => (deleteResult(item))
                }, null, 8, ["loading", "onClick"])
              ]),
              _: 2
            }, 1024),
            _createVNode(_component_v_card_text, { class: "content" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_12, [
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
                _createElementVNode("div", _hoisted_13, _toDisplayString(item.message), 1),
                (item.candidates?.length)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_14, [
                      _createVNode(_component_v_table, {
                        density: "compact",
                        class: "candidate-table"
                      }, {
                        default: _withCtx(() => [
                          _cache[19] || (_cache[19] = _createElementVNode("thead", null, [
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
                                _createElementVNode("td", _hoisted_15, _toDisplayString(candidate.site_name || candidate.site), 1),
                                _createElementVNode("td", _hoisted_16, _toDisplayString(candidate.title), 1),
                                _createElementVNode("td", _hoisted_17, _toDisplayString(candidate.seeders || 0), 1),
                                _createElementVNode("td", _hoisted_18, [
                                  _createVNode(_component_v_btn, {
                                    color: "primary",
                                    variant: "text",
                                    size: "small",
                                    "prepend-icon": "mdi-file-eye-outline",
                                    onClick: $event => (previewRule(item, candidate))
                                  }, {
                                    default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
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
                      }, 1024)
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 2
            }, 1024)
          ]),
          _: 2
        }, 1024))
      }), 128))
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
              onClick: _cache[4] || (_cache[4] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[20] || (_cache[20] = [
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
              default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                _createTextVNode("手动扫描", -1)
              ]))]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "warning",
              "prepend-icon": "mdi-delete-sweep-outline",
              variant: "text",
              size: "small",
              loading: clearing.value,
              onClick: clearResults
            }, {
              default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
                _createTextVNode("诊断结果清除", -1)
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
              default: _withCtx(() => [...(_cache[23] || (_cache[23] = [
                _createTextVNode("刷新", -1)
              ]))]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "grey",
              "prepend-icon": "mdi-close",
              variant: "text",
              size: "small",
              onClick: _cache[5] || (_cache[5] = $event => (emit('close')))
            }, {
              default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
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
      "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((previewDialog).value = $event)),
      "max-width": "720"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
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
                (ruleSuggestions.value.length && !preview.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
                      _cache[26] || (_cache[26] = _createElementVNode("div", { class: "text-caption text-medium-emphasis mb-2" }, "请选择要添加的官组、平台关键词或 PT 站点", -1)),
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(ruleSuggestions.value, (suggestion) => {
                        return (_openBlock(), _createBlock(_component_v_btn, {
                          key: suggestion.pattern,
                          color: "primary",
                          variant: "tonal",
                          size: "small",
                          class: "mr-2 mb-2",
                          loading: previewLoading.value === suggestion.pattern,
                          onClick: $event => (previewRuleSuggestion(suggestion))
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(suggestion.text), 1)
                          ]),
                          _: 2
                        }, 1032, ["loading", "onClick"]))
                      }), 128))
                    ]))
                  : _createCommentVNode("", true),
                (preview.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_20, [
                      (preview.value.selected_text)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_21, "已选择：" + _toDisplayString(preview.value.selected_text), 1))
                        : _createCommentVNode("", true),
                      (preview.value.field === 'sites')
                        ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                            _createElementVNode("div", null, "旧订阅站点：" + _toDisplayString(formatPreviewSites(preview.value.old_site_names || preview.value.old_sites, 'MP 默认搜索站点')), 1),
                            _createElementVNode("div", null, "新订阅站点：" + _toDisplayString(formatPreviewSites(preview.value.new_site_names || preview.value.new_sites)), 1)
                          ], 64))
                        : (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                            _createElementVNode("div", null, "旧 include：" + _toDisplayString(preview.value.old_include || '-'), 1),
                            _createElementVNode("div", null, "新 include：" + _toDisplayString(preview.value.new_include || '-'), 1)
                          ], 64))
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
                  onClick: _cache[6] || (_cache[6] = $event => (previewDialog.value = false))
                }, {
                  default: _withCtx(() => [...(_cache[27] || (_cache[27] = [
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
                  default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-30c55013"]]);

export { Page as default };
