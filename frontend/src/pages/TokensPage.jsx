import { useCallback, useEffect, useMemo, useState } from 'react';
import clsx from 'clsx';
import { useTranslation } from '../i18n/LanguageContext.jsx';
import { useToast } from '../components/ToastProvider.jsx';

export default function TokensPage() {
  const { t } = useTranslation();
  const { notify } = useToast();
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [generatedToken, setGeneratedToken] = useState(null);
  const [error, setError] = useState(null);

  const loadTokens = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/tokens');
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText);
      }
      setTokens(Array.isArray(data.tokens) ? data.tokens : []);
    } catch (err) {
      console.error('Failed to load tokens', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTokens();
  }, [loadTokens]);

  const createToken = useCallback(async (event) => {
    event.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const response = await fetch('/tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText);
      }
      setGeneratedToken(data.token);
      setTokens((current) => [data.record, ...current]);
      setName('');
      notify(t('tokens.status.created'), 'success');
    } catch (err) {
      console.error('Failed to create token', err);
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }, [name, notify, t]);

  const deleteToken = useCallback(async (tokenId) => {
    if (!window.confirm(t('tokens.confirm.delete'))) {
      return;
    }
    try {
      const response = await fetch(`/tokens/${tokenId}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || response.statusText);
      }
      setTokens((current) => current.filter((token) => token.id !== tokenId));
      notify(t('tokens.status.deleted'), 'success');
    } catch (err) {
      console.error('Failed to delete token', err);
      notify(t('tokens.status.deleteFailed', { message: err.message }), 'error');
    }
  }, [notify, t]);

  const copyGeneratedToken = useCallback(async () => {
    if (!generatedToken) {
      return;
    }
    try {
      await navigator.clipboard.writeText(generatedToken);
      notify(t('toast.copied'), 'success');
    } catch (err) {
      console.error('Failed to copy token', err);
      notify(t('toast.copyFailed', { message: err.message }), 'error');
    }
  }, [generatedToken, notify, t]);

  const statusMessage = useMemo(() => {
    if (error) {
      return { message: t('tokens.status.error', { message: error }), variant: 'error' };
    }
    if (loading) {
      return { message: t('tokens.status.loading'), variant: 'info' };
    }
    return null;
  }, [error, loading, t]);

  return (
    <div className="card-list">
      <div className="section-card">
        <div className="view-card-header">
          <h2 className="section-title">{t('tokens.section.manage')}</h2>
          <div className="inline-actions">
            <button type="button" className="secondary-button" onClick={loadTokens} disabled={loading}>
              {t('button.reload')}
            </button>
          </div>
        </div>
        <p className="muted-text">{t('tokens.description')}</p>
        <form className="form-grid" onSubmit={createToken}>
          <div className="input-field">
            <label htmlFor="token-name-input">{t('tokens.label.name')}</label>
            <input
              id="token-name-input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder={t('tokens.placeholder.name')}
            />
          </div>
          <div className="input-field" style={{ alignItems: 'flex-end' }}>
            <button type="submit" className="primary-button" disabled={creating}>
              {creating ? t('tokens.action.creating') : t('tokens.action.create')}
            </button>
          </div>
        </form>
        {generatedToken ? (
          <div className="generated-token">
            <div className="generated-token__content">
              <h3>{t('tokens.generated.title')}</h3>
              <p className="muted-text">{t('tokens.generated.hint')}</p>
              <code className="token-value">{generatedToken}</code>
            </div>
            <div className="inline-actions">
              <button type="button" className="secondary-button" onClick={copyGeneratedToken}>
                {t('tokens.action.copy')}
              </button>
              <button type="button" className="ghost-button" onClick={() => setGeneratedToken(null)}>
                {t('tokens.action.dismiss')}
              </button>
            </div>
          </div>
        ) : null}
        {statusMessage ? (
          <div className={clsx('status-banner', statusMessage.variant === 'error' && 'error')}>
            {statusMessage.message}
          </div>
        ) : null}
      </div>
      <div className="section-card">
        <div className="view-card-header">
          <h2 className="section-title">{t('tokens.section.active')}</h2>
        </div>
        {tokens.length === 0 ? (
          <div className="empty-state">{t('tokens.empty')}</div>
        ) : (
          <div className="token-list">
            {tokens.map((token) => (
              <div key={token.id} className="token-row">
                <div>
                  <p className="token-name">{token.name || t('tokens.unnamed')}</p>
                  <p className="muted-text token-meta">
                    {t('tokens.meta.preview', { preview: token.preview || '••••' })}
                    {' · '}
                    {t('tokens.meta.createdAt', { value: token.created_at })}
                  </p>
                </div>
                <button type="button" className="ghost-button" onClick={() => deleteToken(token.id)}>
                  {t('tokens.action.revoke')}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
