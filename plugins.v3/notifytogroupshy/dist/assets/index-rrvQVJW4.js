import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Page from './__federation_expose_Page-Cdum4eZe.js';

true&&(function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) {
    return;
  }
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) {
    processPreload(link);
  }
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") {
        continue;
      }
      for (const node of mutation.addedNodes) {
        if (node.tagName === "LINK" && node.rel === "modulepreload")
          processPreload(node);
      }
    }
  }).observe(document, { childList: true, subtree: true });
  function getFetchOpts(link) {
    const fetchOpts = {};
    if (link.integrity) fetchOpts.integrity = link.integrity;
    if (link.referrerPolicy) fetchOpts.referrerPolicy = link.referrerPolicy;
    if (link.crossOrigin === "use-credentials")
      fetchOpts.credentials = "include";
    else if (link.crossOrigin === "anonymous") fetchOpts.credentials = "omit";
    else fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep)
      return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
}());

const {openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const _sfc_main = {
  __name: 'App',
  props: {
  api: { type: Object, default: () => ({}) },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

return (_ctx, _cache) => {
  return (_openBlock(), _createBlock(Page, {
    api: props.api,
    onClose: _cache[0] || (_cache[0] = $event => (emit('close')))
  }, null, 8, ["api"]))
}
}

};

const {createApp} = await importShared('vue');

const {createVuetify} = await importShared('vuetify');

const vuetify = createVuetify();
createApp(_sfc_main).use(vuetify).mount('#app');
