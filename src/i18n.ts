import { createI18n } from 'vue-i18n'

const messages = {
  zh: {
    common: {
      login: '登录',
      register: '注册',
      username: '用户名',
      password: '密码',
      submit: '提交',
      cancel: '取消',
      logout: '退出登录',
      dashboard: '统计看板',
      species: '物命品种库',
      billing: '物命',
      logs: '历史单据',
    },
    billing: {
      species_name: '品种',
      weight: '重量',
      unit: '单位',
      unit_price: '单价',
      fee_type: '服务费类型',
      fee_value: '服务费',
      subtotal: '小计',
      total: '总计',
      percentage: '按比例 (%)',
      fixed: '固定金额',
      save: '保存单据'
    },
    dashboard: {
      price_trend: '周单价趋势',
      select_species: '选择品种',
    }
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  fallbackLocale: 'zh',
  messages,
})
