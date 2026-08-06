import { useMemo } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import CanvasPage from './pages/CanvasPage.jsx';
import DaemonPage from './pages/DaemonPage.jsx';
import ConfigPage from './pages/ConfigPage.jsx';
import TokensPage from './pages/TokensPage.jsx';
import DocsPage from './pages/DocsPage.jsx';
import { useTranslation } from './i18n/LanguageContext.jsx';
import { ToastProvider, useToast } from './components/ToastProvider.jsx';


function LanguageSelector() {
  const { language, setLanguage, t } = useTranslation();
  const { notify } = useToast();

  return (
    <label className="inline-actions" style={{ alignItems: 'center', gap: '0.6rem' }}>
      <span className="muted-text" style={{ fontWeight: 600 }}>{t('language.label')}</span>
      <select
        className="language-select"
        value={language}
        onChange={(event) => {
          const value = event.target.value;
          setLanguage(value);
          notify(t('toast.languageSwitched', { language: value === 'zh' ? '中文' : 'English' }), 'success');
        }}
      >
        <option value="en">English</option>
        <option value="zh">中文</option>
      </select>
    </label>
  );
}

function Navigation() {
  const { t } = useTranslation();
  const location = useLocation();
  const navItems = [
    { to: '/canvas', label: t('nav.canvas') },
    { to: '/daemon', label: t('nav.daemon') },
    { to: '/config', label: t('nav.config') },
    { to: '/tokens', label: t('nav.tokens') },
    { to: '/docs', label: t('nav.docs') },
  ];

  return (
    <nav className="app-nav">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            `nav-link${
              isActive
              || (location.pathname === '/' && item.to === '/daemon')
              || (item.to === '/docs' && location.pathname.startsWith('/docs'))
                ? ' active'
                : ''
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

function Shell() {
  const { t } = useTranslation();
  const location = useLocation();

  const meta = useMemo(() => {
    const path = location.pathname;
    if (path.startsWith('/canvas')) {
      return { title: t('page.canvas.title'), subtitle: t('page.canvas.subtitle') };
    }
    if (path.startsWith('/config')) {
      return { title: t('page.config.title'), subtitle: t('page.config.subtitle') };
    }
    if (path.startsWith('/tokens')) {
      return { title: t('page.tokens.title'), subtitle: t('page.tokens.subtitle') };
    }
    if (path.startsWith('/docs')) {
      return { title: t('page.docs.title'), subtitle: t('page.docs.subtitle') };
    }
    return { title: t('page.daemon.title'), subtitle: t('page.daemon.subtitle') };
  }, [location.pathname, t]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="branding">
            <h1>{meta.title}</h1>
            <p className="page-description">{meta.subtitle}</p>
          </div>
          <div className="inline-actions" style={{ gap: '1rem' }}>
            <Navigation />
            <LanguageSelector />
          </div>
        </div>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/daemon" replace />} />
          <Route path="/canvas" element={<CanvasPage />} />
          <Route path="/daemon" element={<DaemonPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/tokens" element={<TokensPage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/docs/*" element={<DocsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <Shell />
    </ToastProvider>
  );
}
