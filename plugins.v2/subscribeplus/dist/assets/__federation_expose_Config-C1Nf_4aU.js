import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "config-section" };
const _hoisted_3 = { class: "section-title" };
const _hoisted_4 = { class: "config-section" };
const _hoisted_5 = { class: "section-title" };
const _hoisted_6 = { class: "config-section" };
const _hoisted_7 = { class: "section-title" };

const {computed,onMounted,reactive,ref,watch} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
  api: {
    type: Object,
    default: () => ({}),
  },
},
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

const loading = ref(false);
const error = ref('');
const categories = ref([]);
const sites = ref([]);

const config = reactive({
  enabled: false,
  delay_days: 1,
  cron: '0 9 * * *',
  selected_categories: [],
  use_moviepilot_search_sites: true,
  category_sites: {},
  max_scan_subscribes: 20,
  notify_tg: true,
  allow_tg_rule_update: false,
});

const selectedCategoryItems = computed(() => {
  const selected = new Set(config.selected_categories);
  return categories.value.filter(item => selected.has(item.value))
});

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
}

function applyInitialConfig() {
  Object.assign(config, {
    ...config,
    ...props.initialConfig,
    selected_categories: Array.isArray(props.initialConfig.selected_categories)
      ? [...props.initialConfig.selected_categories]
      : [],
    category_sites: props.initialConfig.category_sites
      ? { ...props.initialConfig.category_sites }
      : {},
  });
}

async function loadOptions() {
  loading.value = true;
  error.value = '';
  try {
    const [categoryResponse, siteResponse] = await Promise.all([
      props.api.get('plugin/SubscribePlus/categories'),
      props.api.get('plugin/SubscribePlus/sites'),
    ]);
    categories.value = unwrap(categoryResponse).items || [];
    sites.value = unwrap(siteResponse).items || [];
    const staleUncategorizedOnly =
      config.selected_categories.length === 1 &&
      config.selected_categories[0] === '未分类' &&
      categories.value.some(item => item.value !== '未分类');
    if (!config.selected_categories.length || staleUncategorizedOnly) {
      config.selected_categories = categories.value.map(item => item.value);
    }
  } catch (err) {
    error.value = err?.message || '读取配置选项失败';
  } finally {
    loading.value = false;
  }
}

function saveConfig() {
  const selected = new Set(config.selected_categories);
  const categorySites = Object.fromEntries(
    Object.entries(config.category_sites || {}).filter(([category]) => selected.has(category))
  );
  emit('save', {
    ...config,
    delay_days: Number(config.delay_days),
    max_scan_subscribes: Number(config.max_scan_subscribes),
    category_sites: categorySites,
  });
}

watch(
  () => config.selected_categories,
  categoriesValue => {
    for (const category of categoriesValue) {
      if (!Array.isArray(config.category_sites[category])) {
        config.category_sites[category] = [];
      }
    }
  },
  { deep: true }
);

onMounted(() => {
  applyInitialConfig();
  loadOptions();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_form = _resolveComponent("v-form");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "title-bar" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              icon: "mdi-playlist-star",
              color: "primary",
              size: "small"
            }),
            _cache[9] || (_cache[9] = _createElementVNode("span", null, "订阅下载增强", -1)),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              icon: "mdi-refresh",
              variant: "text",
              size: "small",
              loading: loading.value,
              "aria-label": "刷新",
              onClick: loadOptions
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
                  variant: "tonal",
                  density: "compact",
                  class: "mb-3 text-caption",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_form, {
              onSubmit: _withModifiers(saveConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _createElementVNode("section", _hoisted_2, [
                  _createElementVNode("div", _hoisted_3, [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-tune-variant",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[10] || (_cache[10] = _createElementVNode("span", null, "扫描设置", -1))
                  ]),
                  _createVNode(_component_v_row, null, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "4"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_switch, {
                            modelValue: config.enabled,
                            "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((config.enabled) = $event)),
                            color: "primary",
                            label: "启用",
                            density: "compact",
                            "hide-details": ""
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "4"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.delay_days,
                            "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.delay_days) = $event)),
                            modelModifiers: { number: true },
                            type: "number",
                            min: "0",
                            label: "宽限天数",
                            variant: "outlined",
                            density: "compact",
                            "hide-details": "auto"
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "4"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.cron,
                            "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.cron) = $event)),
                            label: "Cron",
                            variant: "outlined",
                            density: "compact",
                            "hide-details": "auto"
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "6"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_select, {
                            modelValue: config.selected_categories,
                            "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.selected_categories) = $event)),
                            items: categories.value,
                            "item-title": "title",
                            "item-value": "value",
                            label: "二级分类",
                            variant: "outlined",
                            density: "compact",
                            multiple: "",
                            chips: "",
                            "closable-chips": "",
                            "hide-details": "auto"
                          }, null, 8, ["modelValue", "items"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.max_scan_subscribes,
                            "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.max_scan_subscribes) = $event)),
                            modelModifiers: { number: true },
                            type: "number",
                            min: "1",
                            label: "单次最多诊断",
                            variant: "outlined",
                            density: "compact",
                            "hide-details": "auto"
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      })
                    ]),
                    _: 1
                  })
                ]),
                _createElementVNode("section", _hoisted_4, [
                  _createElementVNode("div", _hoisted_5, [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-server-network",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[11] || (_cache[11] = _createElementVNode("span", null, "分类站点范围", -1))
                  ]),
                  _createVNode(_component_v_row, null, {
                    default: _withCtx(() => [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(selectedCategoryItems.value, (category) => {
                        return (_openBlock(), _createBlock(_component_v_col, {
                          key: category.value,
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_select, {
                              modelValue: config.category_sites[category.value],
                              "onUpdate:modelValue": $event => ((config.category_sites[category.value]) = $event),
                              items: sites.value,
                              "item-title": "name",
                              "item-value": "id",
                              label: category.title,
                              variant: "outlined",
                              density: "compact",
                              multiple: "",
                              chips: "",
                              "closable-chips": "",
                              clearable: "",
                              "hide-details": "auto"
                            }, null, 8, ["modelValue", "onUpdate:modelValue", "items", "label"])
                          ]),
                          _: 2
                        }, 1024))
                      }), 128))
                    ]),
                    _: 1
                  })
                ]),
                _createElementVNode("section", _hoisted_6, [
                  _createElementVNode("div", _hoisted_7, [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-message-badge-outline",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[12] || (_cache[12] = _createElementVNode("span", null, "通知权限", -1))
                  ]),
                  _createVNode(_component_v_row, null, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "6"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_switch, {
                            modelValue: config.notify_tg,
                            "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.notify_tg) = $event)),
                            color: "primary",
                            label: "Telegram 独立通知",
                            density: "compact",
                            "hide-details": ""
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "6"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_switch, {
                            modelValue: config.allow_tg_rule_update,
                            "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.allow_tg_rule_update) = $event)),
                            color: "warning",
                            label: "允许 TG 修改订阅规则",
                            density: "compact",
                            "hide-details": ""
                          }, null, 8, ["modelValue"])
                        ]),
                        _: 1
                      })
                    ]),
                    _: 1
                  })
                ]),
                _createVNode(_component_v_card_actions, { class: "action-bar" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_btn, {
                      color: "info",
                      "prepend-icon": "mdi-view-dashboard-outline",
                      variant: "text",
                      size: "small",
                      onClick: _cache[7] || (_cache[7] = $event => (emit('switch')))
                    }, {
                      default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                        _createTextVNode("数据页", -1)
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
                      onClick: loadOptions
                    }, {
                      default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
                        _createTextVNode("刷新", -1)
                      ]))]),
                      _: 1
                    }, 8, ["loading"]),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      "prepend-icon": "mdi-content-save",
                      variant: "text",
                      size: "small",
                      onClick: saveConfig
                    }, {
                      default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
                        _createTextVNode("保存", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_btn, {
                      color: "grey",
                      "prepend-icon": "mdi-close",
                      variant: "text",
                      size: "small",
                      onClick: _cache[8] || (_cache[8] = $event => (emit('close')))
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-d16d6b8d"]]);

export { Config as default };
