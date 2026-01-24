import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.js'
import enUS from './en-US.js'

// 获取存储的语言偏好，默认中文
const getStoredLocale = () => {
  const stored = localStorage.getItem('locale')
  if (stored && ['zh-CN', 'en-US'].includes(stored)) {
    return stored
  }
  // 检测浏览器语言
  const browserLang = navigator.language
  if (browserLang.startsWith('en')) {
    return 'en-US'
  }
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false,
  locale: getStoredLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

// 切换语言并保存偏好
export const setLocale = (locale) => {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}

export default i18n
