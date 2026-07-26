import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Config, { _ as _export_sfc } from './__federation_expose_Config-Ds_toVcx.js';

const {toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createVNode:_createVNode,createElementVNode:_createElementVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "page-shell" };
const _hoisted_2 = {
  key: 1,
  class: "loading-state"
};

const {onMounted,ref} = await importShared('vue');


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

const loading = ref(true);
const error = ref('');
const initialConfig = ref({});

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
}

async function loadConfig() {
  const response = await props.api.get('plugin/CleanInvalidPlugin');
  initialConfig.value = unwrap(response) || {};
}

onMounted(async () => {
  try {
    await loadConfig();
  } catch (err) {
    error.value = err?.message || '读取插件配置失败';
  } finally {
    loading.value = false;
  }
});

return (_ctx, _cache) => {
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    (error.value)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 0,
          type: "error",
          variant: "tonal",
          density: "compact",
          closable: "",
          class: "ma-2",
          "onClick:close": _cache[0] || (_cache[0] = $event => (error.value = ''))
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(error.value), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (loading.value)
      ? (_openBlock(), _createElementBlock("div", _hoisted_2, [
          _createVNode(_component_v_progress_circular, {
            indeterminate: "",
            color: "primary"
          }),
          _cache[3] || (_cache[3] = _createElementVNode("span", null, "正在读取插件状态...", -1))
        ]))
      : (_openBlock(), _createBlock(Config, {
          key: 2,
          "initial-config": initialConfig.value,
          api: __props.api,
          "show-switch": false,
          onAction: _cache[1] || (_cache[1] = $event => (emit('action'))),
          onClose: _cache[2] || (_cache[2] = $event => (emit('close')))
        }, null, 8, ["initial-config", "api"]))
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-bbe62d59"]]);

export { Page as default };
