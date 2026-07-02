import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "clean-invalid-page" };
const _hoisted_2 = { class: "summary-grid mb-4" };
const _hoisted_3 = { class: "summary-panel accent-red" };
const _hoisted_4 = { class: "summary-panel accent-green" };
const _hoisted_5 = { class: "summary-panel accent-blue" };
const _hoisted_6 = { class: "path-line" };

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
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_empty_state = _resolveComponent("v-empty-state");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
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
              color: "primary",
              variant: "tonal",
              rounded: "lg"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, { icon: "mdi-puzzle-remove" })
              ]),
              _: 1
            })
          ]),
          append: _withCtx(() => [
            _createVNode(_component_v_btn, {
              icon: "mdi-refresh",
              variant: "text",
              loading: loading.value,
              onClick: loadData
            }, null, 8, ["loading"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-h6" }, {
              default: _withCtx(() => [...(_cache[1] || (_cache[1] = [
                _createTextVNode("无效插件概览", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_subtitle, null, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(summaryText.value), 1)
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
          : _createCommentVNode("", true),
        _createElementVNode("div", _hoisted_2, [
          _createElementVNode("div", _hoisted_3, [
            _cache[2] || (_cache[2] = _createElementVNode("span", null, "无效记录", -1)),
            _createElementVNode("strong", null, _toDisplayString(invalidItems.value.length), 1)
          ]),
          _createElementVNode("div", _hoisted_4, [
            _cache[3] || (_cache[3] = _createElementVNode("span", null, "本地源可用", -1)),
            _createElementVNode("strong", null, _toDisplayString(localSourceCount.value), 1)
          ]),
          _createElementVNode("div", _hoisted_5, [
            _cache[4] || (_cache[4] = _createElementVNode("span", null, "运行目录存在", -1)),
            _createElementVNode("strong", null, _toDisplayString(runtimeExistsCount.value), 1)
          ])
        ]),
        _createVNode(_component_v_alert, {
          type: invalidItems.value.length ? 'warning' : 'success',
          variant: "tonal",
          density: "comfortable",
          class: "mb-4"
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
              density: "comfortable",
              class: "mb-4"
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(lastResult.value.message), 1)
              ]),
              _: 1
            }, 8, ["type"]))
          : _createCommentVNode("", true),
        (invalidItems.value.length)
          ? (_openBlock(), _createBlock(_component_v_list, {
              key: 2,
              lines: "three",
              class: "plugin-list"
            }, {
              default: _withCtx(() => [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(invalidItems.value, (plugin) => {
                  return (_openBlock(), _createBlock(_component_v_list_item, {
                    key: plugin.id,
                    title: plugin.id,
                    subtitle: plugin.status
                  }, {
                    prepend: _withCtx(() => [
                      _createVNode(_component_v_avatar, {
                        color: plugin.local_source_path ? 'success' : 'warning',
                        variant: "tonal"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            icon: plugin.local_source_path ? 'mdi-source-branch-check' : 'mdi-alert-circle-outline'
                          }, null, 8, ["icon"])
                        ]),
                        _: 2
                      }, 1032, ["color"])
                    ]),
                    append: _withCtx(() => [
                      _createVNode(_component_v_chip, {
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
                      _createElementVNode("div", _hoisted_6, _toDisplayString(plugin.runtime_path), 1)
                    ]),
                    _: 2
                  }, 1032, ["title", "subtitle"]))
                }), 128))
              ]),
              _: 1
            }))
          : (_openBlock(), _createBlock(_component_v_empty_state, {
              key: 3,
              icon: "mdi-check-circle-outline",
              title: "没有无效插件",
              text: "当前无需清理。"
            })),
        _createVNode(_component_v_card_actions, { class: "px-0" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              "prepend-icon": "mdi-cog-outline",
              color: "primary",
              onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
            }, {
              default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                _createTextVNode(" 配置处理 ", -1)
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-87ee95b9"]]);

export { Page as default };
