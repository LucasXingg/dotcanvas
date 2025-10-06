import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { translations } from './translations.js';

const STORAGE_KEY = 'dotcanvas-language';

const LanguageContext = createContext({
  language: 'en',
  setLanguage: () => {},
  t: (key, params) => key,
});

function getInitialLanguage() {
  if (typeof window === 'undefined') {
    return 'en';
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored && translations[stored]) {
      return stored;
    }
  } catch (error) {
    console.debug('Unable to read language preference', error);
  }
  const browser = typeof navigator !== 'undefined' ? navigator.language || navigator.languages?.[0] : null;
  if (browser?.startsWith('zh')) {
    return 'zh';
  }
  return 'en';
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(getInitialLanguage);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, language);
    } catch (error) {
      console.debug('Unable to persist language preference', error);
    }
  }, [language]);

  const setLanguage = useCallback((value) => {
    setLanguageState((current) => {
      if (translations[value]) {
        return value;
      }
      return current;
    });
  }, []);

  const translate = useCallback(
    (key, params = {}) => {
      const template = translations[language]?.[key] ?? translations.en?.[key] ?? translations.zh?.[key] ?? key;
      return template.replace(/\{(\w+)\}/g, (_, token) => {
        if (params[token] === null || params[token] === undefined) {
          return '';
        }
        return String(params[token]);
      });
    },
    [language],
  );

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t: translate,
    }),
    [language, setLanguage, translate],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useTranslation() {
  return useContext(LanguageContext);
}
