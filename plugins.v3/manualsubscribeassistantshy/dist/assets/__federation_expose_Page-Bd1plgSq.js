import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "page-wrap" };

const {reactive,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: { api: { type: Object, default: null }, pluginId: { type: String, default: 'ManualSubscribeAssistantShy' }, initialConfig: { type: Object, default: () => ({}) } },
  setup(__props, { expose: __expose }) {

const props = __props;
const form = reactive({ year: 0, season: '当前', resolve_bangumi: true, proxy: false, ...props.initialConfig });
const seasons = ['当前', '春', '夏', '秋', '冬'];
const candidates = ref([]);
const loading = ref(false);
const subscribing = ref(null);
const message = ref('');
const error = ref(false);

function call(method, path, payload) {
  return props.api?.[method]?.(`plugin/${props.pluginId}/${path}`, payload)
}
async function loadCandidates() {
  loading.value = true; message.value = ''; error.value = false;
  try {
    const result = await call('post', 'candidates', form);
    const data = result?.data || result;
    if (data?.code) throw new Error(data.message)
    candidates.value = data?.list || [];
    message.value = `已读取 ${candidates.value.length} 条候选`;
  } catch (e) { error.value = true; message.value = e.message || '抓取失败'; }
  finally { loading.value = false; }
}
async function subscribe(item) {
  subscribing.value = item; message.value = ''; error.value = false;
  try {
    const result = await call('post', 'subscribe', { candidate: item });
    const data = result?.data || result;
    if (data?.code) throw new Error(data.message)
    message.value = `${item.title} 已创建订阅（ID ${data.subscribe_id}）`;
  } catch (e) { error.value = true; message.value = e.message || '创建订阅失败'; }
  finally { subscribing.value = null; }
}
__expose({ loadCandidates });

return (_ctx, _cache) => {
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_img = _resolveComponent("v-img");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      variant: "outlined",
      class: "mb-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, null, {
          default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
            _createTextVNode("手动订阅助手魔改版", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_v_card_subtitle, null, {
          default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
            _createTextVNode("只在你点击时创建订阅，不会后台自动订阅", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_row, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_text_field, {
                      modelValue: form.year,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((form.year) = $event)),
                      modelModifiers: { number: true },
                      label: "年份（0=当前年）",
                      type: "number"
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_select, {
                      modelValue: form.season,
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((form.season) = $event)),
                      items: seasons,
                      label: "季度"
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6",
                  class: "d-flex align-center"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_switch, {
                      modelValue: form.resolve_bangumi,
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((form.resolve_bangumi) = $event)),
                      label: "识别 Bangumi/TMDB"
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              color: "primary",
              loading: loading.value,
              onClick: loadCandidates
            }, {
              default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                _createTextVNode("抓取候选", -1)
              ]))]),
              _: 1
            }, 8, ["loading"]),
            (message.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  class: "mt-3",
                  type: error.value ? 'error' : 'info',
                  density: "compact"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(message.value), 1)
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
    _createVNode(_component_v_card, { variant: "outlined" }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, null, {
          default: _withCtx(() => [
            _createTextVNode("候选列表（" + _toDisplayString(candidates.value.length) + "）", 1)
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            (!candidates.value.length)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "info",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                    _createTextVNode("点击“抓取候选”后在这里查看季度番剧。", -1)
                  ]))]),
                  _: 1
                }))
              : (_openBlock(), _createBlock(_component_v_row, { key: 1 }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(candidates.value, (item) => {
                      return (_openBlock(), _createBlock(_component_v_col, {
                        key: `${item.mikan_id}-${item.bangumi_id || ''}`,
                        cols: "12",
                        md: "6",
                        xl: "4"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_card, {
                            variant: "tonal",
                            class: "candidate-card"
                          }, {
                            default: _withCtx(() => [
                              (item.cover)
                                ? (_openBlock(), _createBlock(_component_v_img, {
                                    key: 0,
                                    src: item.cover,
                                    height: "180",
                                    cover: ""
                                  }, null, 8, ["src"]))
                                : _createCommentVNode("", true),
                              _createVNode(_component_v_card_title, { class: "text-wrap" }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(item.title), 1)
                                ]),
                                _: 2
                              }, 1024),
                              _createVNode(_component_v_card_subtitle, null, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(item.year) + " · " + _toDisplayString(item.week || '季度新番'), 1)
                                ]),
                                _: 2
                              }, 1024),
                              _createVNode(_component_v_card_actions, null, {
                                default: _withCtx(() => [
                                  (item.bangumi_url)
                                    ? (_openBlock(), _createBlock(_component_v_btn, {
                                        key: 0,
                                        size: "small",
                                        variant: "text",
                                        href: item.bangumi_url,
                                        target: "_blank"
                                      }, {
                                        default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                                          _createTextVNode("打开 Bangumi", -1)
                                        ]))]),
                                        _: 1
                                      }, 8, ["href"]))
                                    : _createCommentVNode("", true),
                                  (item.tmdb_url)
                                    ? (_openBlock(), _createBlock(_component_v_btn, {
                                        key: 1,
                                        size: "small",
                                        variant: "text",
                                        href: item.tmdb_url,
                                        target: "_blank"
                                      }, {
                                        default: _withCtx(() => [...(_cache[8] || (_cache[8] = [
                                          _createTextVNode("打开 TMDB", -1)
                                        ]))]),
                                        _: 1
                                      }, 8, ["href"]))
                                    : _createCommentVNode("", true),
                                  _createVNode(_component_v_spacer),
                                  _createVNode(_component_v_btn, {
                                    color: "primary",
                                    size: "small",
                                    loading: subscribing.value === item,
                                    onClick: $event => (subscribe(item))
                                  }, {
                                    default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                                      _createTextVNode("创建订阅", -1)
                                    ]))]),
                                    _: 1
                                  }, 8, ["loading", "onClick"])
                                ]),
                                _: 2
                              }, 1024)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        _: 2
                      }, 1024))
                    }), 128))
                  ]),
                  _: 1
                }))
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-9b4a871a"]]);

export { Page as default };
