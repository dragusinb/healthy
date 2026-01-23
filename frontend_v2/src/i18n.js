import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import ro from './locales/ro.json';
import en from './locales/en.json';

// Get saved language or default to Romanian
const savedLanguage = localStorage.getItem('language') || 'ro';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ro: { translation: ro },
      en: { translation: en }
    },
    lng: savedLanguage,
    fallbackLng: 'ro',
    interpolation: {
      escapeValue: false
    }
  });

// Save language preference when changed
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('language', lng);
});

export default i18n;
