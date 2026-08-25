<template>
  <div class="config-wrap">
    <v-switch v-model="form.enabled" label="启用手动订阅助手魔改版" color="primary" />
    <v-alert type="info" variant="tonal" density="compact">
      本插件不会自动运行或自动创建订阅。只有点击候选项的“创建订阅”按钮后，才会写入 MoviePilot。
    </v-alert>
    <v-text-field v-model.number="form.year" label="年份（0=当前年）" type="number" />
    <v-select v-model="form.season" :items="seasons" label="季度" />
    <v-switch v-model="form.resolve_bangumi" label="抓详情并识别 Bangumi/TMDB（较慢但更准确）" />
    <v-switch v-model="form.proxy" label="使用 MoviePilot 代理访问 Mikan" />
    <v-btn color="primary" @click="$emit('save', form)">保存</v-btn>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
const props = defineProps({ initialConfig: { type: Object, default: () => ({}) } })
const form = reactive({ enabled: false, year: 0, season: '当前', resolve_bangumi: true, proxy: false, ...props.initialConfig })
const seasons = ['当前', '春', '夏', '秋', '冬']
defineEmits(['save', 'close'])
</script>

<style scoped>
.config-wrap { padding: 16px; max-width: 720px; }
</style>
