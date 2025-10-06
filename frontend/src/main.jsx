import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './styles.css';
import { LanguageProvider } from './i18n/LanguageContext.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LanguageProvider>
      <BrowserRouter basename="/ui">
        <App />
      </BrowserRouter>
    </LanguageProvider>
  </React.StrictMode>,
);
