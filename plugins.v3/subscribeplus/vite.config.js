import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'
import { rmSync } from 'node:fs'

// 生产联邦包由宿主提供 Vuetify/MDI 基础样式；开发服务器则保留依赖样式，保证本地预览可用。
const vuetifyFilter = {
  postcssPlugin: 'vuetify-filter',
  Root(root) {
    root.walkRules(rule => {
      if (rule.selector && (rule.selector.includes('.v-') || rule.selector.includes('.mdi-'))) {
        rule.remove()
      }
    })
  },
}

function removeUnreachableSharedAssets() {
  return {
    name: 'remove-unreachable-shared-assets',
    apply: 'build',
    closeBundle() {
      rmSync(new URL('./dist/assets/__federation_shared_vuetify', import.meta.url), {
        recursive: true,
        force: true,
      })
    },
  }
}

export default defineConfig(({ command }) => ({
  plugins: [
    vue(),
    federation({
      name: 'SubscribePlus',
      filename: 'remoteEntry.js',
      exposes: {
        './Page': './src/components/Page.vue',
        './Config': './src/components/Config.vue',
      },
      shared: {
        vue: {
          requiredVersion: false,
          generate: false,
        },
        vuetify: {
          requiredVersion: false,
          generate: false,
          singleton: true,
        },
        'vuetify/styles': {
          requiredVersion: false,
          generate: false,
          singleton: true,
        },
      },
      format: 'esm',
    }),
    removeUnreachableSharedAssets(),
  ],
  build: {
    target: 'esnext',
    minify: false,
    cssCodeSplit: true,
  },
  css: {
    postcss: {
      plugins: [
        {
          postcssPlugin: 'internal:charset-removal',
          AtRule: {
            charset: atRule => {
              if (atRule.name === 'charset') atRule.remove()
            },
          },
        },
        // 仅生产构建剥离宿主已经提供的 Vuetify/MDI 全局规则；dev serve 保留它们。
        ...(command === 'build' ? [vuetifyFilter] : []),
      ],
    },
  },
}))
