import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import Page from './Page.vue'

createApp(Page, { api: { get: () => Promise.resolve({}), post: () => Promise.resolve({}) } })
  .use(createVuetify())
  .mount('#app')
