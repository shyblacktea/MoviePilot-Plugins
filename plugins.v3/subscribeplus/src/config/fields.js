/**
 * SubscribePlus 配置字段元数据。
 *
 * 每个字段声明渲染类型与归属 tab，Config.vue 据此自动渲染表单，
 * 新增配置项只需在此追加声明，无需改模板。
 */

/** tab 分组定义：key 与 Config.vue 的导航一一对应 */
export const groups = [
  { key: 'overview', title: '运行概览', icon: 'mdi-view-dashboard-outline', desc: '扫描状态、待处理诊断与快捷操作。' },
  { key: 'identifier', title: '识别词工具', icon: 'mdi-tag-plus-outline', desc: '按 TMDB 强制绑定媒体或修正年份。' },
  { key: 'rules', title: '规则记录', icon: 'mdi-history', desc: '订阅规则修改历史。' },
  { key: 'scan', title: '扫描设置', icon: 'mdi-tune-variant', desc: '订阅扫描周期、宽限天数与站点范围。' },
  { key: 'notify', title: '通知权限', icon: 'mdi-message-badge-outline', desc: 'Telegram 通知、重复提醒抑制与规则修改授权。' },
  { key: 'cleanup', title: '清理与候选', icon: 'mdi-broom', desc: '整季包清理与候选下载缓存。' },
]

/**
 * 配置字段声明。
 * type: switch | number | text | select | multiselect
 * group: 归属 tab；section: tab 内小节标题
 * 其余属性透传给对应 Vuetify 组件。
 */
export const fields = [
  // ---- 扫描设置 ----
  {
    key: 'enabled', group: 'scan', section: '运行状态', type: 'switch',
    label: '启用插件', color: 'success',
    hint: '开启后插件将处于激活状态',
  },
  {
    key: 'delay_days', group: 'scan', section: '扫描窗口', type: 'number',
    label: '宽限天数', min: 0, unit: '天', cols: { md: 4 },
    hint: '单集播出超过 N 天仍未入库才触发诊断',
  },

  {
    key: 'cron', group: 'scan', section: '扫描窗口', type: 'text',
    label: 'Cron', cols: { md: 4 },
    hint: '每 6 小时建议写 0 */6 * * *', validate: 'cron',
  },

  {
    key: 'selected_categories', group: 'scan', section: '扫描范围', type: 'multiselect',
    label: '二级分类', optionsKey: 'categories', cols: { md: 6 },
    hint: '仅检测所选二级分类下的电视剧订阅',
  },
  {
    key: 'search_sites', group: 'scan', section: '扫描范围', type: 'multiselect',
    label: 'PT搜索范围', optionsKey: 'sites', clearable: true, cols: { md: 6 },
    hint: '插件诊断搜索的站点，留空用 MP 默认搜索站点',
  },

  // ---- 通知权限 ----
  {
    key: 'notify_tg', group: 'notify', section: '通知渠道', type: 'switch',
    label: 'Telegram 独立通知', color: 'primary', cols: { md: 6 },
    hint: '每部剧单独发送 Telegram 诊断通知',
  },
  {
    key: 'allow_tg_rule_update', group: 'notify', section: '授权', type: 'switch',
    label: '允许 TG 修改订阅规则', color: 'warning', cols: { md: 6 },
    hint: '开启后可在 Telegram 交互中直接写入订阅过滤规则',
    alert: '开启后可通过 Telegram 交互直接调整订阅过滤规则，请谨慎授权。',
  },
  {
    key: 'notification_suppression_days', group: 'notify', section: '重复提醒抑制', type: 'number',
    label: '不通知天数', min: 0, unit: '天', cols: { md: 6 },
    hint: '同一诊断选择“不通知”后，在此期限内不再重复提醒；0 表示关闭',
  },

  // ---- 清理与候选 ----
  {
    key: 'season_pack_enabled', group: 'cleanup', section: '最终集整季包', type: 'switch',
    label: '启用最终集整季包处理', color: 'primary', cols: { md: 6 },
    hint: '订阅电视剧命中最终已播集整季包时，统一执行全包下载和旧单集清理',
  },
  {
    key: 'season_pack_qb_cleanup', group: 'cleanup', section: '最终集整季包', type: 'select',
    label: '旧 qB 单集任务清理', cols: { md: 6 },
    hint: '整季包开始下载后严格匹配同剧同季旧单集 qB 任务',
    options: [
      { title: '关闭', value: 'off' },
      { title: '删除旧 qB 任务', value: 'task' },
      { title: '删除旧 qB 任务+源文件', value: 'source' },
    ],
    alert: '“删除任务”仅移除 qB 任务；“任务+源文件”直接由 qB 按精确 hash 删除任务和源文件。MV3 只补充查询整理记录，不负责删除。不会触碰媒体库目标文件。',
  },
  {
    key: 'mv3_url', group: 'cleanup', section: 'MV3 整理记录查询（可选）', type: 'text',
    label: 'MV3 网站地址', cols: { md: 6 },
    hint: '例如 http://你的-MV3-地址:7811；不要填写 /api/v1',
  },
  {
    key: 'mv3_api_token', group: 'cleanup', section: 'MV3 整理记录查询（可选）', type: 'text',
    label: 'MV3 API Token', cols: { md: 6 }, secret: true,
    hint: '使用 MV3 的 API Key；请求通过 X-API-Key 头传递，不填写账号或密码',
    alert: '仅用于按精确源路径查询 MV3 已整理记录；使用 X-API-Key 请求头，不会调用 MV3 删除接口。未配置时不影响 qB 直接删除任务和源文件。',
  },
  {
    key: 'candidate_cache_days', group: 'cleanup', section: '候选下载', type: 'number',
    label: '候选缓存天数', min: 0, unit: '天', cols: { md: 6 },
    hint: '候选种子下载信息缓存有效期；TG 选择条使用同一个天数，0 关闭',
  },
]

/** 配置默认值（与后端 PluginConfig 对齐） */
export const defaults = {
  enabled: false,
  delay_days: 1,
  cron: '0 9 * * *',
  selected_categories: [],
  search_sites: [],

  notify_tg: true,
  allow_tg_rule_update: false,
  season_pack_enabled: false,
  season_pack_qb_cleanup: 'off',
  mv3_url: '',
  mv3_api_token: '',
  candidate_cache_days: 3,
  notification_suppression_days: 3,
  custom_release_groups: [],
  custom_platforms: [],
}

/**
 * 校验 Cron 表达式（5 段）。
 * @param {string} value Cron 字符串
 * @returns {string} 错误信息，合法返回空串
 */
export function validateCron(value) {
  const parts = String(value || '').trim().split(/\s+/)
  if (parts.length !== 5) return 'Cron 需要 5 段，例如 0 */6 * * *'
  const ranges = [59, 23, 31, 12, 7]
  const invalid = parts.find((part, index) => {
    const match = part.match(/^\*\/(\d+)$/)
    return match && Number(match[1]) > ranges[index]
  })
  if (invalid) return `${invalid} 超出该 Cron 字段范围`
  return ''
}
