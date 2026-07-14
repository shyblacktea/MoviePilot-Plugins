import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Config from './__federation_expose_Config-C-f8D2NG.js';

const {openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const {onMounted,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
},
  emits: ['action', 'switch', 'close', 'layout'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

// 数据页与配置页共用同一 UI；数据页入口自行拉取当前配置作为初始值
const initialConfig = ref({});

function unwrap(response) {
  const body = response?.data ?? response ?? {};
  return body?.data ?? body
}

async function onSave(payload) {
  try {
    await props.api.post('plugin/SubscribePlus/config', payload);
    emit('action');
  } catch (err) {
    console.error('保存配置失败', err);
  }
}

onMounted(async () => {
  try {
    const response = await props.api.get('plugin/SubscribePlus/config');
    initialConfig.value = unwrap(response) || {};
  } catch (err) {
    console.error('读取配置失败', err);
  }
});

return (_ctx, _cache) => {
  return (_openBlock(), _createBlock(Config, {
    "initial-config": initialConfig.value,
    api: __props.api,
    onSave: onSave,
    onClose: _cache[0] || (_cache[0] = $event => (emit('close'))),
    onSwitch: _cache[1] || (_cache[1] = $event => (emit('switch'))),
    onLayout: _cache[2] || (_cache[2] = $event => (emit('layout', $event)))
  }, null, 8, ["initial-config", "api"]))
}
}

};

export { _sfc_main as default };
