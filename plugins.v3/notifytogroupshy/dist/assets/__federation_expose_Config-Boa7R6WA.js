import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Page from './__federation_expose_Page-Cdum4eZe.js';

const {openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, default: () => ({}) },
  initialConfig: { type: Object, default: () => ({}) },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

return (_ctx, _cache) => {
  return (_openBlock(), _createBlock(Page, {
    api: props.api,
    "initial-config": props.initialConfig,
    onClose: _cache[0] || (_cache[0] = $event => (emit('close')))
  }, null, 8, ["api", "initial-config"]))
}
}

};

export { _sfc_main as default };
