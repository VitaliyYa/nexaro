import { createI18n } from 'vue-i18n';
import en from './locales/en.json';
import ru from './locales/ru.json';

export type SupportedLocale = 'en' | 'ru' | 'ka' | 'he';

const RTL_LOCALES: SupportedLocale[] = ['he'];

function getInitialLocale(): SupportedLocale {
  const saved = localStorage.getItem('smartrent_locale') as SupportedLocale;
  if (saved && ['en', 'ru', 'ka', 'he'].includes(saved)) {
    return saved;
  }
  const browserLang = navigator.language.split('-')[0];
  if (browserLang === 'ru') return 'ru';
  return 'en';
}

export function setHtmlDirection(locale: SupportedLocale) {
  const isRtl = RTL_LOCALES.includes(locale);
  document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
  document.documentElement.lang = locale;
}

const initialLocale = getInitialLocale();
setHtmlDirection(initialLocale);

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'en',
  messages: {
    en,
    ru,
  },
});

export function switchLanguage(newLocale: SupportedLocale) {
  (i18n.global.locale as any).value = newLocale;
  localStorage.setItem('smartrent_locale', newLocale);
  setHtmlDirection(newLocale);
}
