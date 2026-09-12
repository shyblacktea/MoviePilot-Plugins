import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "notify-root" };
const _hoisted_2 = { class: "d-flex align-center ga-2" };
const _hoisted_3 = { class: "notify-body" };
const _hoisted_4 = { class: "notify-content" };
const _hoisted_5 = { class: "config-section" };
const _hoisted_6 = { class: "field-list" };
const _hoisted_7 = { class: "field-info" };
const _hoisted_8 = { class: "field-label" };
const _hoisted_9 = { class: "field-hint" };
const _hoisted_10 = { class: "config-section" };
const _hoisted_11 = { class: "field-row default-row" };
const _hoisted_12 = {
  key: 0,
  class: "empty-state"
};
const _hoisted_13 = { class: "section-actions" };
const _hoisted_14 = {
  key: 0,
  class: "text-caption text-medium-emphasis"
};

const {computed,onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const loading = ref(false);
const saving = ref(false);
const error = ref('');
const hint = ref('');
const usernames = ref([]);
const targetOptions = ref([]);
const actionOptions = ref([]);
const actions = reactive({ download_action: 'all', organize_action: 'all', subscribe_action: 'all' });
const defaultTargets = ref([]);
const rows = ref([]);
const savedSnapshot = ref('');
let rowUid = 0;

const actionRows = [
  { key: 'organize_action', label: '资源入库', hint: '整理完成并写入媒体库时的通知。' },
  { key: 'download_action', label: '资源下载', hint: '添加下载任务成功时的通知。' },
  { key: 'subscribe_action', label: '添加订阅 / 订阅完成', hint: '添加订阅成功和订阅完成时的通知。' },
];

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
}

function normalizedTargets(value) {
  const list = Array.isArray(value) ? value : String(value || '').split(',');
  return [...new Set(list.map(item => String(item || '').trim()).filter(Boolean))]
}

function snapshot() {
  savedSnapshot.value = JSON.stringify({
    actions: { ...actions },
    defaultTargets: [...defaultTargets.value].sort(),
    rows: rows.value
      .filter(row => String(row.username || '').trim())
      .map(row => ({ username: String(row.username).trim(), targets: normalizedTargets(row.targets).sort() }))
      .sort((a, b) => a.username.localeCompare(b.username)),
  });
}

const dirty = computed(() => {
  const current = {
    actions: { ...actions },
    defaultTargets: [...defaultTargets.value].sort(),
    rows: rows.value
      .filter(row => String(row.username || '').trim())
      .map(row => ({ username: String(row.username).trim(), targets: normalizedTargets(row.targets).sort() }))
      .sort((a, b) => a.username.localeCompare(b.username)),
  };
  return JSON.stringify(current) !== savedSnapshot.value
});

function availableUsers(current) {
  const used = new Set(rows.value.map(row => String(row.username || '').trim()).filter(name => name && name !== current));
  return usernames.value.filter(name => !used.has(name))
}

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const data = unwrap(await props.api.get('plugin/NotifyToGroupShy/options')) || {};
    const nextActions = data.actions || {};
    for (const key of Object.keys(actions)) actions[key] = String(nextActions[key] || 'all');
    actionOptions.value = Array.isArray(data.options) && data.options.length ? data.options : [
      { title: '发群组', value: 'all' },
      { title: '用户+管理员', value: 'user,admin' },
      { title: '仅用户', value: 'user' },
      { title: '仅管理员', value: 'admin' },
    ];
    usernames.value = Array.isArray(data.usernames) ? data.usernames.map(String) : [];
    targetOptions.value = (Array.isArray(data.targets) ? data.targets : []).map(item => ({
      title: item.title || String(item.id),
      value: String(item.id),
    }));
    const rules = data.rules && typeof data.rules === 'object' ? data.rules : {};
      rows.value = Object.entries(rules).map(([username, targets]) => ({
      uid: `row-${++rowUid}`,
      username,
      targets: normalizedTargets(targets),
    }));
    defaultTargets.value = normalizedTargets(data.default_target);
    snapshot();
  } catch (err) {
    error.value = err?.message || '读取通知目标配置失败';
  } finally {
    loading.value = false;
  }
}

function addRow() {
  rows.value.push({ uid: `row-${++rowUid}`, username: availableUsers('').at(0) || '', targets: [] });
}

function removeRow(index) {
  rows.value.splice(index, 1);
}

async function save() {
  const rules = {};
  for (const row of rows.value) {
    const username = String(row.username || '').trim();
    const targets = normalizedTargets(row.targets);
    if (username && targets.length) rules[username] = targets.join(',');
  }
  saving.value = true;
  error.value = '';
  hint.value = '';
  try {
    const result = unwrap(await props.api.post('plugin/NotifyToGroupShy/save', {
      actions: { ...actions },
      rules,
      default_target: normalizedTargets(defaultTargets.value).join(','),
    })) || {};
    if (result.success === false) {
      error.value = result.message || '保存失败';
      return
    }
    await load();
    hint.value = result.message || '通知目标配置已保存';
  } catch (err) {
    error.value = err?.message || '保存通知目标配置失败';
  } finally {
    saving.value = false;
  }
}

onMounted(load);

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VAvatar = _resolveComponent("VAvatar");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VCardItem = _resolveComponent("VCardItem");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VCard = _resolveComponent("VCard");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VCard, {
      flat: "",
      class: "notify-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardItem, { class: "notify-header" }, {
          prepend: _withCtx(() => [
            _createVNode(_component_VAvatar, {
              color: "primary",
              variant: "tonal",
              rounded: "lg",
              size: "44"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-bell-cog-outline",
                  size: "25"
                })
              ]),
              _: 1
            })
          ]),
          append: _withCtx(() => [
            _createElementVNode("div", _hoisted_2, [
              (dirty.value)
                ? (_openBlock(), _createBlock(_component_VChip, {
                    key: 0,
                    color: "warning",
                    size: "small",
                    variant: "tonal"
                  }, {
                    default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                      _createTextVNode("有修改未保存", -1)
                    ]))]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              _createVNode(_component_VBtn, {
                color: "primary",
                variant: "flat",
                size: "small",
                "prepend-icon": "mdi-content-save",
                loading: saving.value,
                disabled: !dirty.value,
                onClick: save
              }, {
                default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                  _createTextVNode("保存修改", -1)
                ]))]),
                _: 1
              }, 8, ["loading", "disabled"]),
              _createVNode(_component_VBtn, {
                icon: "mdi-refresh",
                variant: "text",
                size: "small",
                loading: loading.value,
                onClick: load
              }, null, 8, ["loading"]),
              _createVNode(_component_VBtn, {
                icon: "mdi-close",
                variant: "text",
                size: "small",
                "aria-label": "关闭",
                title: "关闭",
                onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
              })
            ])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-h6 notify-title" }, {
              default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                _createTextVNode("我就想通知到群组！", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VCardSubtitle, { class: "text-caption" }, {
              default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                _createTextVNode("系统通知目标与订阅用户通知映射", -1)
              ]))]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VDivider),
        (error.value)
          ? (_openBlock(), _createBlock(_component_VAlert, {
              key: 0,
              type: "error",
              variant: "tonal",
              density: "compact",
              class: "ma-4 mb-0 text-caption",
              closable: "",
              "onClick:close": _cache[1] || (_cache[1] = $event => (error.value = ''))
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(error.value), 1)
              ]),
              _: 1
            }))
          : _createCommentVNode("", true),
        (hint.value)
          ? (_openBlock(), _createBlock(_component_VAlert, {
              key: 1,
              type: "success",
              variant: "tonal",
              density: "compact",
              class: "ma-4 mb-0 text-caption",
              closable: "",
              "onClick:close": _cache[2] || (_cache[2] = $event => (hint.value = ''))
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(hint.value), 1)
              ]),
              _: 1
            }))
          : _createCommentVNode("", true),
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("main", _hoisted_4, [
            _createElementVNode("section", _hoisted_5, [
              _cache[8] || (_cache[8] = _createElementVNode("div", { class: "section-title" }, "1. 系统通知目标（资源入库 / 资源下载 / 添加订阅/订阅完成）", -1)),
              _cache[9] || (_cache[9] = _createElementVNode("div", { class: "section-hint" }, "控制 MoviePilot 对应类型系统通知的投递目标；“发群组”按各通知渠道的群组配置发送。", -1)),
              _createElementVNode("div", _hoisted_6, [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(actionRows, (row) => {
                  return _createElementVNode("div", {
                    key: row.key,
                    class: "field-row"
                  }, [
                    _createElementVNode("div", _hoisted_7, [
                      _createElementVNode("div", _hoisted_8, _toDisplayString(row.label), 1),
                      _createElementVNode("div", _hoisted_9, _toDisplayString(row.hint), 1)
                    ]),
                    _createVNode(_component_VSelect, {
                      modelValue: actions[row.key],
                      "onUpdate:modelValue": $event => ((actions[row.key]) = $event),
                      items: actionOptions.value,
                      "item-title": "title",
                      "item-value": "value",
                      label: "通知目标",
                      density: "compact",
                      variant: "outlined",
                      "hide-details": "",
                      rounded: "lg",
                      class: "field-control"
                    }, null, 8, ["modelValue", "onUpdate:modelValue", "items"])
                  ])
                }), 64))
              ])
            ]),
            _createElementVNode("section", _hoisted_10, [
              _cache[14] || (_cache[14] = _createElementVNode("div", { class: "section-title" }, "2. 订阅用户通知映射", -1)),
              _cache[15] || (_cache[15] = _createElementVNode("div", { class: "section-hint" }, "未单独配置的订阅用户使用默认目标。每个用户可以同时选择多个群组、用户或管理员目标。", -1)),
              _createElementVNode("div", _hoisted_11, [
                _cache[10] || (_cache[10] = _createElementVNode("div", { class: "field-info" }, [
                  _createElementVNode("div", { class: "field-label" }, "未单独配置的订阅用户默认目标"),
                  _createElementVNode("div", { class: "field-hint" }, "留空时回退到通知渠道的默认群组。")
                ], -1)),
                _createVNode(_component_VSelect, {
                  modelValue: defaultTargets.value,
                  "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((defaultTargets).value = $event)),
                  items: targetOptions.value,
                  "item-title": "title",
                  "item-value": "value",
                  label: "默认通知目标",
                  placeholder: "默认：群组",
                  density: "compact",
                  variant: "outlined",
                  "hide-details": "",
                  rounded: "lg",
                  multiple: "",
                  chips: "",
                  "closable-chips": "",
                  clearable: "",
                  class: "field-control",
                  "no-data-text": "无可用通知目标"
                }, null, 8, ["modelValue", "items"])
              ]),
              (!rows.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_12, [
                    _createVNode(_component_VIcon, {
                      icon: "mdi-account-multiple-outline",
                      size: "30",
                      color: "primary"
                    }),
                    _cache[11] || (_cache[11] = _createElementVNode("div", { class: "text-body-2 mt-2" }, "暂无单独配置的订阅用户", -1)),
                    _cache[12] || (_cache[12] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "点击“添加映射”后，为订阅归属用户选择通知目标。", -1))
                  ]))
                : _createCommentVNode("", true),
              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(rows.value, (row, index) => {
                return (_openBlock(), _createElementBlock("div", {
                  key: row.uid,
                  class: "field-row mapping-row"
                }, [
                  _createVNode(_component_VSelect, {
                    modelValue: row.username,
                    "onUpdate:modelValue": $event => ((row.username) = $event),
                    items: availableUsers(row.username),
                    label: "用户订阅",
                    placeholder: "选择订阅归属用户",
                    density: "compact",
                    variant: "outlined",
                    "hide-details": "",
                    rounded: "lg",
                    clearable: "",
                    class: "user-control",
                    "no-data-text": "无可用订阅用户"
                  }, null, 8, ["modelValue", "onUpdate:modelValue", "items"]),
                  _createVNode(_component_VSelect, {
                    modelValue: row.targets,
                    "onUpdate:modelValue": $event => ((row.targets) = $event),
                    items: targetOptions.value,
                    "item-title": "title",
                    "item-value": "value",
                    label: "通知目标",
                    placeholder: "选择一个或多个目标",
                    density: "compact",
                    variant: "outlined",
                    "hide-details": "",
                    rounded: "lg",
                    multiple: "",
                    chips: "",
                    "closable-chips": "",
                    clearable: "",
                    class: "target-control",
                    "no-data-text": "无可用通知目标"
                  }, null, 8, ["modelValue", "onUpdate:modelValue", "items"]),
                  _createVNode(_component_VBtn, {
                    icon: "mdi-delete-outline",
                    color: "error",
                    variant: "text",
                    size: "small",
                    onClick: $event => (removeRow(index))
                  }, null, 8, ["onClick"])
                ]))
              }), 128)),
              _createElementVNode("div", _hoisted_13, [
                _createVNode(_component_VBtn, {
                  color: "primary",
                  variant: "tonal",
                  size: "small",
                  "prepend-icon": "mdi-plus",
                  disabled: !availableUsers('').length,
                  onClick: addRow
                }, {
                  default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                    _createTextVNode("添加映射", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"]),
                (!availableUsers('').length && usernames.value.length)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_14, "所有订阅用户均已配置"))
                  : _createCommentVNode("", true)
              ])
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-150b20fc"]]);

export { Page as default };
