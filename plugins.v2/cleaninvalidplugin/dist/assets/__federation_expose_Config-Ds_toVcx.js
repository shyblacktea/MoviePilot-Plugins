import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass,withModifiers:_withModifiers,vShow:_vShow,withDirectives:_withDirectives} = await importShared('vue');


const _hoisted_1 = { class: "cip-config" };
const _hoisted_2 = { class: "cip-header-actions" };
const _hoisted_3 = { class: "cip-body" };
const _hoisted_4 = {
  class: "cip-nav",
  "aria-label": "插件操作"
};
const _hoisted_5 = { class: "cip-content" };
const _hoisted_6 = { class: "cip-mobile-tabbar" };
const _hoisted_7 = { class: "cip-mobile-tabinfo" };
const _hoisted_8 = { class: "font-weight-medium" };
const _hoisted_9 = { class: "text-caption text-medium-emphasis" };
const _hoisted_10 = { class: "cip-workspace" };
const _hoisted_11 = { class: "cip-window" };
const _hoisted_12 = { class: "cip-pane-heading" };
const _hoisted_13 = { class: "cip-pane-title-wrap" };
const _hoisted_14 = { class: "cip-section-title" };
const _hoisted_15 = { class: "cip-section-desc" };
const _hoisted_16 = {
  key: 0,
  class: "cip-progress-panel",
  "aria-live": "polite"
};
const _hoisted_17 = { class: "cip-progress-heading" };
const _hoisted_18 = { class: "cip-progress-title" };
const _hoisted_19 = { class: "cip-progress-percent" };
const _hoisted_20 = { class: "cip-progress-metrics" };
const _hoisted_21 = { class: "cip-selection-toolbar" };
const _hoisted_22 = {
  key: 2,
  class: "cip-empty"
};
const _hoisted_23 = {
  key: 3,
  class: "cip-empty"
};
const _hoisted_24 = { class: "cip-action-dock" };
const _hoisted_25 = { class: "cip-action-copy" };
const _hoisted_26 = {
  class: "cip-dashboard",
  "aria-label": "插件状态"
};
const _hoisted_27 = { class: "cip-dashboard-title" };
const _hoisted_28 = { class: "cip-dashboard-row" };
const _hoisted_29 = { class: "cip-dashboard-row" };
const _hoisted_30 = { class: "cip-dashboard-row" };
const _hoisted_31 = { class: "cip-dashboard-row" };
const _hoisted_32 = { class: "cip-dashboard-row" };
const _hoisted_33 = { class: "cip-dashboard-title" };
const _hoisted_34 = { class: "cip-dashboard-note" };

const {computed,onBeforeUnmount,onMounted,reactive,ref,watch} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
  showSwitch: { type: Boolean, default: true },
},
  emits: ['save', 'close', 'switch', 'layout', 'action'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const layoutRequest = { maxWidth: '70rem' };
emit('layout', layoutRequest);

const loading = ref(false);
const submitting = ref(false);
const error = ref('');
const invalidItems = ref([]);
const lastResult = ref({});
const mobileTabSheet = ref(false);

const config = reactive({
  invalid_plugin_ids: [],
  action_mode: 'clean',
});

const actionTabs = [
  {
    value: 'clean',
    title: '清理记录',
    icon: 'mdi-delete-outline',
    color: 'error',
    alertType: 'info',
    navDescription: '移除失效安装记录',
    description: '清理数据库中的失效安装记录和异常运行目录。',
    hint: '只处理已选择的无效记录和运行目录，不会删除插件原有配置。',
    actionDescription: '执行后将从已安装列表移除所选无效记录。',
    selectLabel: '选择要清理的插件',
    buttonLabel: '执行清理',
    buttonIcon: 'mdi-delete-sweep-outline',
  },
  {
    value: 'reinstall',
    title: '重新安装',
    icon: 'mdi-package-down',
    color: 'primary',
    alertType: 'warning',
    navDescription: '恢复插件运行文件',
    description: '从本地插件源或插件市场恢复缺失的运行文件。',
    hint: '优先使用本地插件源，否则尝试插件市场；安装记录和原插件配置会保留。',
    actionDescription: '执行后将重新获取所选插件的运行文件。',
    selectLabel: '选择要重新安装的插件',
    buttonLabel: '开始重装',
    buttonIcon: 'mdi-package-down',
  },
];

const selectedCount = computed(() => config.invalid_plugin_ids.length);
const localSourceCount = computed(() => invalidItems.value.filter(item => item.local_source_path).length);
const onlineSourceCount = computed(() => invalidItems.value.filter(item => item.source_type === 'online').length);
const runtimeExistsCount = computed(() => invalidItems.value.filter(item => item.runtime_exists).length);
const currentTab = computed(() => actionTabs.find(tab => tab.value === config.action_mode) || actionTabs[0]);
const jobRunning = computed(() => ['queued', 'running'].includes(lastResult.value?.status));
const jobProgress = computed(() => Math.max(0, Math.min(100, Number(lastResult.value?.progress) || 0)));
const jobCompleted = computed(() => Number(lastResult.value?.completed) || 0);
const jobTotal = computed(() => Number(lastResult.value?.total) || 0);
const jobStatusText = computed(() => {
  if (lastResult.value?.current) {
    return `正在处理：${lastResult.value.current}`
  }
  return lastResult.value?.message || '任务已进入后台队列'
});

let pollTimer = null;

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
}

function applyInitialConfig(value = props.initialConfig) {
  config.invalid_plugin_ids = Array.isArray(value?.invalid_plugin_ids)
    ? [...value.invalid_plugin_ids]
    : [];
  config.action_mode = value?.action_mode || 'clean';
}

async function loadInvalidPlugins() {
  loading.value = true;
  error.value = '';
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/invalid_plugins');
    const data = unwrap(response);
    invalidItems.value = data.items || [];
    lastResult.value = data.last_result || {};
    const validIds = new Set(invalidItems.value.map(item => item.id));
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => validIds.has(id));
    scheduleJobPoll();
  } catch (err) {
    error.value = err?.message || '读取无效插件列表失败';
  } finally {
    loading.value = false;
  }
}

function togglePlugin(pluginId) {
  if (config.invalid_plugin_ids.includes(pluginId)) {
    config.invalid_plugin_ids = config.invalid_plugin_ids.filter(id => id !== pluginId);
  } else {
    config.invalid_plugin_ids = [...config.invalid_plugin_ids, pluginId];
  }
}

function selectAll() {
  config.invalid_plugin_ids = invalidItems.value.map(item => item.id);
}

function clearSelection() {
  config.invalid_plugin_ids = [];
}

function stopJobPoll() {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function scheduleJobPoll() {
  if (!jobRunning.value || pollTimer) return
  pollTimer = setTimeout(async () => {
    pollTimer = null;
    await pollJobState();
  }, 1000);
}

async function pollJobState() {
  try {
    const response = await props.api.get('plugin/CleanInvalidPlugin/last_result');
    lastResult.value = unwrap(response) || {};
    if (jobRunning.value) {
      scheduleJobPoll();
      return
    }
    await loadInvalidPlugins();
    emit('action');
  } catch (err) {
    error.value = err?.message || '读取后台任务进度失败';
    scheduleJobPoll();
  }
}

async function runAction() {
  if (!selectedCount.value || submitting.value || jobRunning.value) return

  const payload = {
    invalid_plugin_ids: [...config.invalid_plugin_ids],
    action_mode: config.action_mode,
  };
  submitting.value = true;
  error.value = '';
  try {
    if (typeof props.api?.put !== 'function') {
      emit('save', payload);
      return
    }

    const response = await props.api.put('plugin/CleanInvalidPlugin', payload);
    const result = unwrap(response) || {};
    if (result.success === false) {
      throw new Error(result.message || '操作执行失败')
    }

    emit('action');
    if (payload.action_mode === 'reinstall') {
      const statusResponse = await props.api.get('plugin/CleanInvalidPlugin/last_result');
      lastResult.value = unwrap(statusResponse) || {};
      scheduleJobPoll();
    } else {
      await loadInvalidPlugins();
    }
  } catch (err) {
    error.value = err?.message || '操作执行失败';
  } finally {
    submitting.value = false;
  }
}

watch(() => props.initialConfig, value => applyInitialConfig(value), { deep: true });
watch(() => config.action_mode, () => emit('layout', layoutRequest));

onMounted(() => {
  applyInitialConfig();
  loadInvalidPlugins();
});

onBeforeUnmount(stopJobPoll);

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VListItemTitle = _resolveComponent("VListItemTitle");
  const _component_VListItemSubtitle = _resolveComponent("VListItemSubtitle");
  const _component_VListItem = _resolveComponent("VListItem");
  const _component_VList = _resolveComponent("VList");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VProgressLinear = _resolveComponent("VProgressLinear");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VCheckboxBtn = _resolveComponent("VCheckboxBtn");
  const _component_VProgressCircular = _resolveComponent("VProgressCircular");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VBottomSheet = _resolveComponent("VBottomSheet");

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
                  icon: "mdi-delete-sweep-outline",
                  size: "24"
                })
              ]),
              _: 1
            })
          ]),
          append: _withCtx(() => [
            _createElementVNode("div", _hoisted_2, [
              (jobRunning.value)
                ? (_openBlock(), _createBlock(_component_VChip, {
                    key: 0,
                    color: "primary",
                    variant: "tonal",
                    size: "small",
                    class: "cip-job-chip"
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(" 后台 " + _toDisplayString(jobCompleted.value) + "/" + _toDisplayString(jobTotal.value), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              _createVNode(_component_VBtn, {
                icon: "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                "aria-label": "刷新",
                onClick: loadInvalidPlugins
              }, null, 8, ["loading"]),
              (__props.showSwitch)
                ? (_openBlock(), _createBlock(_component_VBtn, {
                    key: 1,
                    icon: "mdi-view-dashboard-outline",
                    variant: "text",
                    size: "small",
                    "aria-label": "数据页",
                    onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
                  }))
                : _createCommentVNode("", true),
              _createVNode(_component_VBtn, {
                icon: "mdi-close",
                variant: "text",
                size: "small",
                "aria-label": "关闭",
                onClick: _cache[1] || (_cache[1] = $event => (emit('close')))
              })
            ])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "cip-header-title" }, {
              default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                _createTextVNode("清理无效插件", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "cip-header-subtitle" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(currentTab.value.description), 1)
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VDivider),
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("nav", _hoisted_4, [
            _createVNode(_component_VList, {
              density: "comfortable",
              nav: "",
              class: "py-2"
            }, {
              default: _withCtx(() => [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(actionTabs, (tab) => {
                  return _createVNode(_component_VListItem, {
                    key: tab.value,
                    active: config.action_mode === tab.value,
                    color: "primary",
                    rounded: "lg",
                    class: "cip-nav-item",
                    onClick: $event => (config.action_mode = tab.value)
                  }, {
                    prepend: _withCtx(() => [
                      _createVNode(_component_VIcon, {
                        icon: tab.icon
                      }, null, 8, ["icon"])
                    ]),
                    append: _withCtx(() => [
                      (invalidItems.value.length)
                        ? (_openBlock(), _createBlock(_component_VChip, {
                            key: 0,
                            size: "x-small",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(invalidItems.value.length), 1)
                            ]),
                            _: 1
                          }))
                        : _createCommentVNode("", true)
                    ]),
                    default: _withCtx(() => [
                      _createVNode(_component_VListItemTitle, null, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(tab.title), 1)
                        ]),
                        _: 2
                      }, 1024),
                      _createVNode(_component_VListItemSubtitle, null, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(tab.navDescription), 1)
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
          _createElementVNode("section", _hoisted_5, [
            _createElementVNode("div", _hoisted_6, [
              _createElementVNode("div", _hoisted_7, [
                _createElementVNode("div", _hoisted_8, _toDisplayString(currentTab.value.title), 1),
                _createElementVNode("div", _hoisted_9, _toDisplayString(currentTab.value.navDescription), 1)
              ]),
              _createVNode(_component_VBtn, {
                icon: "mdi-menu-down",
                variant: "tonal",
                size: "small",
                onClick: _cache[2] || (_cache[2] = $event => (mobileTabSheet.value = true))
              })
            ]),
            (error.value)
              ? (_openBlock(), _createBlock(_component_VAlert, {
                  key: 0,
                  type: "error",
                  variant: "tonal",
                  density: "compact",
                  closable: "",
                  class: "ma-3 mb-0 text-caption",
                  "onClick:close": _cache[3] || (_cache[3] = $event => (error.value = ''))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createElementVNode("div", _hoisted_10, [
              _createElementVNode("div", _hoisted_11, [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(actionTabs, (tab) => {
                  return _withDirectives(_createElementVNode("div", {
                    key: tab.value,
                    class: "cip-pane"
                  }, [
                    _createElementVNode("div", _hoisted_12, [
                      _createElementVNode("div", _hoisted_13, [
                        _createVNode(_component_VAvatar, {
                          color: tab.color,
                          variant: "tonal",
                          size: "38",
                          rounded: "lg"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_VIcon, {
                              icon: tab.icon,
                              size: "21"
                            }, null, 8, ["icon"])
                          ]),
                          _: 2
                        }, 1032, ["color"]),
                        _createElementVNode("div", null, [
                          _createElementVNode("div", _hoisted_14, _toDisplayString(tab.title), 1),
                          _createElementVNode("div", _hoisted_15, _toDisplayString(tab.description), 1)
                        ])
                      ]),
                      _createVNode(_component_VChip, {
                        size: "small",
                        variant: "tonal",
                        color: selectedCount.value ? tab.color : 'default'
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(" 已选 " + _toDisplayString(selectedCount.value), 1)
                        ]),
                        _: 1
                      }, 8, ["color"])
                    ]),
                    _createVNode(_component_VAlert, {
                      type: tab.alertType,
                      variant: "tonal",
                      density: "compact",
                      icon: "mdi-information-outline",
                      class: "mb-4 text-caption"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(tab.hint), 1)
                      ]),
                      _: 2
                    }, 1032, ["type"]),
                    (jobRunning.value)
                      ? (_openBlock(), _createElementBlock("section", _hoisted_16, [
                          _createElementVNode("div", _hoisted_17, [
                            _createElementVNode("div", _hoisted_18, [
                              _createVNode(_component_VIcon, {
                                icon: "mdi-progress-clock",
                                color: "primary",
                                size: "20"
                              }),
                              _createElementVNode("div", null, [
                                _cache[8] || (_cache[8] = _createElementVNode("strong", null, "正在后台重新安装", -1)),
                                _createElementVNode("span", null, _toDisplayString(jobStatusText.value), 1)
                              ])
                            ]),
                            _createElementVNode("strong", _hoisted_19, _toDisplayString(jobProgress.value) + "%", 1)
                          ]),
                          _createVNode(_component_VProgressLinear, {
                            "model-value": jobProgress.value,
                            color: "primary",
                            height: "8",
                            rounded: "",
                            striped: "",
                            class: "my-3"
                          }, null, 8, ["model-value"]),
                          _createElementVNode("div", _hoisted_20, [
                            _createElementVNode("span", null, "完成 " + _toDisplayString(jobCompleted.value) + "/" + _toDisplayString(jobTotal.value), 1),
                            _createElementVNode("span", null, "成功 " + _toDisplayString(lastResult.value.reinstalled_count || 0), 1),
                            _createElementVNode("span", null, "跳过 " + _toDisplayString(lastResult.value.skipped_count || 0), 1),
                            _createElementVNode("span", {
                              class: _normalizeClass({ 'text-warning': lastResult.value.failed_count })
                            }, "失败 " + _toDisplayString(lastResult.value.failed_count || 0), 3)
                          ]),
                          _cache[9] || (_cache[9] = _createElementVNode("div", { class: "cip-progress-note" }, "后台任务运行期间可以关闭页面，重新打开后会继续显示进度。", -1))
                        ]))
                      : _createCommentVNode("", true),
                    _createElementVNode("div", _hoisted_21, [
                      _cache[12] || (_cache[12] = _createElementVNode("div", { class: "cip-block-title" }, "选择插件", -1)),
                      _createVNode(_component_VSpacer),
                      _createVNode(_component_VBtn, {
                        color: "primary",
                        variant: "text",
                        size: "small",
                        "prepend-icon": "mdi-check-all",
                        disabled: !invalidItems.value.length,
                        onClick: selectAll
                      }, {
                        default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
                          _createTextVNode(" 全选 ", -1)
                        ]))]),
                        _: 1
                      }, 8, ["disabled"]),
                      _createVNode(_component_VBtn, {
                        color: "secondary",
                        variant: "text",
                        size: "small",
                        "prepend-icon": "mdi-close",
                        disabled: !selectedCount.value,
                        onClick: clearSelection
                      }, {
                        default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                          _createTextVNode(" 清空 ", -1)
                        ]))]),
                        _: 1
                      }, 8, ["disabled"])
                    ]),
                    _createVNode(_component_VSelect, {
                      modelValue: config.invalid_plugin_ids,
                      "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.invalid_plugin_ids) = $event)),
                      items: invalidItems.value,
                      "item-title": "title",
                      "item-value": "id",
                      label: tab.selectLabel,
                      variant: "outlined",
                      density: "compact",
                      multiple: "",
                      chips: "",
                      "closable-chips": "",
                      clearable: "",
                      loading: loading.value,
                      disabled: loading.value || !invalidItems.value.length,
                      "hide-details": "auto",
                      class: "mb-3"
                    }, null, 8, ["modelValue", "items", "label", "loading", "disabled"]),
                    (invalidItems.value.length)
                      ? (_openBlock(), _createBlock(_component_VList, {
                          key: 1,
                          lines: "two",
                          density: "compact",
                          class: "cip-plugin-list"
                        }, {
                          default: _withCtx(() => [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(invalidItems.value, (plugin) => {
                              return (_openBlock(), _createBlock(_component_VListItem, {
                                key: plugin.id,
                                title: plugin.id,
                                subtitle: plugin.status,
                                class: "cip-plugin-row",
                                onClick: $event => (togglePlugin(plugin.id))
                              }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_VCheckboxBtn, {
                                    "model-value": config.invalid_plugin_ids.includes(plugin.id),
                                    onClick: _cache[5] || (_cache[5] = _withModifiers(() => {}, ["stop"])),
                                    "onUpdate:modelValue": $event => (togglePlugin(plugin.id))
                                  }, null, 8, ["model-value", "onUpdate:modelValue"])
                                ]),
                                append: _withCtx(() => [
                                  _createVNode(_component_VChip, {
                                    color: tab.value === 'reinstall'
                          ? (plugin.source_type === 'local' ? 'success' : (plugin.source_type === 'online' ? 'info' : 'warning'))
                          : (plugin.runtime_exists ? 'warning' : 'error'),
                                    size: "small",
                                    variant: "tonal"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(tab.value === 'reinstall'
                          ? (plugin.source_type === 'local' ? '本地源' : (plugin.source_type === 'online' ? '在线源' : '无可用源'))
                          : (plugin.runtime_exists ? '目录异常' : '目录缺失')), 1)
                                    ]),
                                    _: 2
                                  }, 1032, ["color"])
                                ]),
                                _: 2
                              }, 1032, ["title", "subtitle", "onClick"]))
                            }), 128))
                          ]),
                          _: 2
                        }, 1024))
                      : (loading.value)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_22, [
                            _createVNode(_component_VProgressCircular, {
                              indeterminate: "",
                              color: "primary",
                              size: "32"
                            }),
                            _cache[13] || (_cache[13] = _createElementVNode("span", null, "正在读取插件状态...", -1))
                          ]))
                        : (_openBlock(), _createElementBlock("div", _hoisted_23, [
                            _createVNode(_component_VIcon, {
                              icon: "mdi-check-circle-outline",
                              size: "42",
                              color: "success"
                            }),
                            _cache[14] || (_cache[14] = _createElementVNode("strong", null, "没有无效插件", -1)),
                            _createElementVNode("span", null, "当前无需执行" + _toDisplayString(tab.title) + "。", 1)
                          ])),
                    (lastResult.value.message && !jobRunning.value)
                      ? (_openBlock(), _createBlock(_component_VAlert, {
                          key: 4,
                          type: lastResult.value.success ? 'success' : 'warning',
                          variant: "tonal",
                          density: "compact",
                          icon: "mdi-history",
                          class: "mt-4 text-caption"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(lastResult.value.message), 1)
                          ]),
                          _: 1
                        }, 8, ["type"]))
                      : _createCommentVNode("", true),
                    _createElementVNode("div", _hoisted_24, [
                      _createElementVNode("div", _hoisted_25, [
                        _createElementVNode("strong", null, _toDisplayString(jobRunning.value ? `后台重装 ${jobCompleted.value}/${jobTotal.value}` : (selectedCount.value ? `将处理 ${selectedCount.value} 个插件` : '请选择插件')), 1),
                        _createElementVNode("span", null, _toDisplayString(jobRunning.value ? '任务已交给后台，当前页面可以正常关闭。' : tab.actionDescription), 1)
                      ]),
                      _createVNode(_component_VBtn, {
                        color: tab.color,
                        "prepend-icon": tab.buttonIcon,
                        variant: "flat",
                        size: "small",
                        loading: submitting.value,
                        disabled: !selectedCount.value || jobRunning.value || submitting.value,
                        onClick: runAction
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(jobRunning.value ? '后台重装中' : tab.buttonLabel), 1)
                        ]),
                        _: 2
                      }, 1032, ["color", "prepend-icon", "loading", "disabled"])
                    ])
                  ]), [
                    [_vShow, config.action_mode === tab.value]
                  ])
                }), 64))
              ]),
              _createElementVNode("aside", _hoisted_26, [
                _createElementVNode("section", null, [
                  _createElementVNode("div", _hoisted_27, [
                    _createVNode(_component_VIcon, {
                      icon: "mdi-chart-box-outline",
                      color: "primary",
                      size: "20"
                    }),
                    _cache[15] || (_cache[15] = _createTextVNode(" 当前状态 ", -1))
                  ]),
                  _createElementVNode("div", _hoisted_28, [
                    _createVNode(_component_VIcon, { icon: "mdi-alert-circle-outline" }),
                    _cache[16] || (_cache[16] = _createElementVNode("span", null, "无效记录", -1)),
                    _createElementVNode("strong", null, _toDisplayString(invalidItems.value.length), 1)
                  ]),
                  _createElementVNode("div", _hoisted_29, [
                    _createVNode(_component_VIcon, { icon: "mdi-source-branch-check" }),
                    _cache[17] || (_cache[17] = _createElementVNode("span", null, "本地源可用", -1)),
                    _createElementVNode("strong", null, _toDisplayString(localSourceCount.value), 1)
                  ]),
                  _createElementVNode("div", _hoisted_30, [
                    _createVNode(_component_VIcon, { icon: "mdi-cloud-download-outline" }),
                    _cache[18] || (_cache[18] = _createElementVNode("span", null, "在线源可用", -1)),
                    _createElementVNode("strong", null, _toDisplayString(onlineSourceCount.value), 1)
                  ]),
                  _createElementVNode("div", _hoisted_31, [
                    _createVNode(_component_VIcon, { icon: "mdi-folder-alert-outline" }),
                    _cache[19] || (_cache[19] = _createElementVNode("span", null, "运行目录存在", -1)),
                    _createElementVNode("strong", null, _toDisplayString(runtimeExistsCount.value), 1)
                  ]),
                  _createElementVNode("div", _hoisted_32, [
                    _createVNode(_component_VIcon, { icon: "mdi-checkbox-marked-circle-outline" }),
                    _cache[20] || (_cache[20] = _createElementVNode("span", null, "当前选择", -1)),
                    _createElementVNode("strong", null, _toDisplayString(selectedCount.value), 1)
                  ])
                ]),
                _createVNode(_component_VDivider, { class: "my-3" }),
                _createElementVNode("section", null, [
                  _createElementVNode("div", _hoisted_33, [
                    _createVNode(_component_VIcon, {
                      icon: currentTab.value.icon,
                      color: currentTab.value.color,
                      size: "20"
                    }, null, 8, ["icon", "color"]),
                    _createTextVNode(" " + _toDisplayString(currentTab.value.title), 1)
                  ]),
                  _createElementVNode("p", _hoisted_34, _toDisplayString(currentTab.value.hint), 1)
                ])
              ])
            ])
          ])
        ])
      ]),
      _: 1
    }),
    _createVNode(_component_VBottomSheet, {
      modelValue: mobileTabSheet.value,
      "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((mobileTabSheet).value = $event))
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCard, {
          rounded: "t-xl",
          class: "cip-sheet"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-subtitle-1 font-weight-bold px-4 pt-4" }, {
              default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                _createTextVNode("选择操作", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardText, { class: "px-3 pb-4" }, {
              default: _withCtx(() => [
                _createVNode(_component_VList, {
                  density: "comfortable",
                  nav: ""
                }, {
                  default: _withCtx(() => [
                    (_openBlock(), _createElementBlock(_Fragment, null, _renderList(actionTabs, (tab) => {
                      return _createVNode(_component_VListItem, {
                        key: tab.value,
                        active: config.action_mode === tab.value,
                        color: "primary",
                        rounded: "lg",
                        title: tab.title,
                        subtitle: tab.description,
                        onClick: $event => {config.action_mode = tab.value; mobileTabSheet.value = false;}
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_VIcon, {
                            icon: tab.icon
                          }, null, 8, ["icon"])
                        ]),
                        append: _withCtx(() => [
                          (config.action_mode === tab.value)
                            ? (_openBlock(), _createBlock(_component_VIcon, {
                                key: 0,
                                icon: "mdi-check",
                                color: "primary"
                              }))
                            : _createCommentVNode("", true)
                        ]),
                        _: 2
                      }, 1032, ["active", "title", "subtitle", "onClick"])
                    }), 64))
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
    }, 8, ["modelValue"])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-ae60ac95"]]);

export { _export_sfc as _, Config as default };
