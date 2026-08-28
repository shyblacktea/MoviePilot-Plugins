import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Page from './__federation_expose_Page-SYe24Je1.js';

const {openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');

/**
 * 侧栏全页：在主应用 #/plugin-app/:pluginId/:navKey 中渲染，占据主内容区。
 * 需在插件后端实现 get_sidebar_nav 才会出现在侧栏。
 */

const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: {
    type: Object,
    default: () => ({}),
  },
  navKey: {
    type: String,
    default: 'main',
  },
  pluginId: {
    type: String,
    default: '',
  },
},
  emits: ['action'],
  setup(__props, { emit: __emit }) {

const emit = __emit;

return (_ctx, _cache) => {
  return (_openBlock(), _createBlock(Page, {
    api: __props.api,
    show_switch: false,
    onAction: _cache[0] || (_cache[0] = $event => (emit('action')))
  }, null, 8, ["api"]))
}
}

};

export { _sfc_main as default };
