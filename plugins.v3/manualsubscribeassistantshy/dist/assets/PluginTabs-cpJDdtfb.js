import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,resolveComponent:_resolveComponent,createVNode:_createVNode,toDisplayString:_toDisplayString,createElementVNode:_createElementVNode,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = {
  class: "asa-tabs",
  role: "tablist"
};
const _hoisted_2 = ["aria-selected", "onClick"];
const _hoisted_3 = { class: "asa-tab__label" };


const _sfc_main = {
  __name: 'PluginTabs',
  props: {
  active: { type: String, default: '' },
  // [{ key, label, icon }]
  tabs: { type: Array, default: () => [] },
},
  emits: ['select'],
  setup(__props, { emit: __emit }) {


const emit = __emit;

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");

  return (_openBlock(), _createElementBlock("nav", _hoisted_1, [
    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(__props.tabs, (tab) => {
      return (_openBlock(), _createElementBlock("button", {
        key: tab.key,
        type: "button",
        role: "tab",
        "aria-selected": __props.active === tab.key,
        class: _normalizeClass(['asa-tab', { 'asa-tab--active': __props.active === tab.key }]),
        onClick: $event => (emit('select', tab.key))
      }, [
        _createVNode(_component_v_icon, {
          icon: tab.icon,
          size: "16"
        }, null, 8, ["icon"]),
        _createElementVNode("span", _hoisted_3, _toDisplayString(tab.label), 1)
      ], 10, _hoisted_2))
    }), 128))
  ]))
}
}

};
const PluginTabs = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-e0a89083"]]);

export { PluginTabs as P };
