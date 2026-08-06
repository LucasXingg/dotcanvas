import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const ToastContext = createContext({
  notify: () => {},
  showMessageBox: () => {},
});

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [messageBox, setMessageBox] = useState(null);

  const dismiss = useCallback((id) => {
    setToasts((items) => items.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback((message, variant = 'info', duration = 4200) => {
    toastId += 1;
    const id = toastId;
    setToasts((items) => [...items, { id, message, variant }]);
    window.setTimeout(() => dismiss(id), duration);
  }, [dismiss]);

  const showMessageBox = useCallback((title, message) => {
    setMessageBox({ title, message });
  }, []);

  const dismissMessageBox = useCallback(() => {
    setMessageBox(null);
  }, []);

  const value = useMemo(
    () => ({ notify, showMessageBox }),
    [notify, showMessageBox],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-container">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.variant}`}>
            <span>{toast.message}</span>
            <button type="button" onClick={() => dismiss(toast.id)} aria-label="Dismiss notification">
              ×
            </button>
          </div>
        ))}
      </div>
      {messageBox ? (
        <div className="message-box-backdrop" role="presentation" onClick={dismissMessageBox}>
          <div
            className="message-box"
            role="dialog"
            aria-modal="true"
            aria-labelledby="message-box-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="message-box-title">{messageBox.title}</h2>
            <p>{messageBox.message}</p>
            <div className="message-box-actions">
              <button type="button" className="primary-button" onClick={dismissMessageBox}>
                OK
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}

export function notifyInstalledPackages(showMessageBox, t, packages) {
  if (!Array.isArray(packages) || packages.length === 0) {
    return;
  }
  const list = packages.join(', ');
  showMessageBox(
    t('install.title'),
    t('install.message', { packages: list }),
  );
}

export function readInstalledPackagesHeader(response) {
  const raw = response?.headers?.get('X-Installed-Packages');
  if (!raw) {
    return [];
  }
  return raw
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}
