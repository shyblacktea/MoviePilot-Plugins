import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,openBlock:_openBlock,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "config-wrap" };

const {reactive} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: { initialConfig: { type: Object, default: () => ({}) } },
  emits: ['save', 'close'],
  setup(__props) {

const props = __props;
const form = reactive({ enabled: false, year: 0, season: '当前', resolve_bangumi: true, proxy: false, ...props.initialConfig });
const seasons = ['当前', '春', '夏', '秋', '冬'];


return (_ctx, _cache) => {
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_btn = _resolveComponent("v-btn");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_switch, {
      modelValue: form.enabled,
      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((form.enabled) = $event)),
      label: "启用手动订阅助手魔改版",
      color: "primary"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_v_alert, {
      type: "info",
      variant: "tonal",
      density: "compact"
    }, {
      default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
        _createTextVNode(" 本插件不会自动运行或自动创建订阅。只有点击候选项的“创建订阅”按钮后，才会写入 MoviePilot。 ", -1)
      ]))]),
      _: 1
    }),
    _createVNode(_component_v_text_field, {
      modelValue: form.year,
      "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((form.year) = $event)),
      modelModifiers: { number: true },
      label: "年份（0=当前年）",
      type: "number"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_v_select, {
      modelValue: form.season,
      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((form.season) = $event)),
      items: seasons,
      label: "季度"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_v_switch, {
      modelValue: form.resolve_bangumi,
      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((form.resolve_bangumi) = $event)),
      label: "抓详情并识别 Bangumi/TMDB（较慢但更准确）"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_v_switch, {
      modelValue: form.proxy,
      "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((form.proxy) = $event)),
      label: "使用 MoviePilot 代理访问 Mikan"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_v_btn, {
      color: "primary",
      onClick: _cache[5] || (_cache[5] = $event => (_ctx.$emit('save', form)))
    }, {
      default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
        _createTextVNode("保存", -1)
      ]))]),
      _: 1
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-d8f9b3bd"]]);

export { Config as default };
