import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { useTranslation } from '../i18n/LanguageContext.jsx';
import { useToast } from '../components/ToastProvider.jsx';

const DEFAULT_STATUS = { key: 'status.selectCanvas', params: {}, type: 'info', raw: null };

export default function CanvasPage() {
  const { t } = useTranslation();
  const { notify } = useToast();
  const [availableViews, setAvailableViews] = useState([]);
  const [availableViewMap, setAvailableViewMap] = useState(new Map());
  const [canvases, setCanvases] = useState([]);
  const [selectedCanvasId, setSelectedCanvasId] = useState('');
  const [canvasName, setCanvasName] = useState('');
  const [canvasIdentifier, setCanvasIdentifier] = useState('');
  const [views, setViews] = useState([]);
  const [viewConfigs, setViewConfigs] = useState([]);
  const [newCanvasName, setNewCanvasName] = useState('');
  const [newViewId, setNewViewId] = useState('');
  const [newViewType, setNewViewType] = useState('');
  const [status, setStatus] = useState(DEFAULT_STATUS);
  const [previewUrl, setPreviewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [collapsedViews, setCollapsedViews] = useState([]);
  const [previewParamsText, setPreviewParamsText] = useState('{}');
  const [previewParamsError, setPreviewParamsError] = useState(null);
  const previousViewIdsRef = useRef(new Set());

  useEffect(() => {
    fetchAvailableViews();
    fetchCanvases();
  }, []);

  useEffect(() => {
    if (!selectedCanvasId) {
      setStatus(DEFAULT_STATUS);
    }
  }, [selectedCanvasId]);

  const statusMessage = useMemo(() => {
    if (status.raw) {
      return status.raw;
    }
    if (!status.key) {
      return '';
    }
    return t(status.key, status.params);
  }, [status, t]);

  const viewConfigsById = useMemo(() => new Map(viewConfigs.map((item) => [item.id, item])), [viewConfigs]);

  useEffect(() => {
    const viewIds = views.map((view) => view.id);
    const validIds = new Set(viewIds);
    const previousViewIds = previousViewIdsRef.current;
    previousViewIdsRef.current = validIds;

    setCollapsedViews((previous) => {
      const filtered = previous.filter((id) => validIds.has(id));
      const missing = viewIds.filter((id) => !previousViewIds.has(id));
      if (!missing.length && filtered.length === previous.length) {
        return previous;
      }
      return [...filtered, ...missing];
    });
  }, [views]);

  async function fetchAvailableViews() {
    try {
      const response = await fetch('/views');
      if (!response.ok) {
        throw new Error(`${response.status}`);
      }
      const data = await response.json();
      const viewsList = Array.isArray(data.views) ? data.views : [];
      setAvailableViews(viewsList);
      setAvailableViewMap(new Map(viewsList.map((view) => [view.type, view.params || {}])));
      if (viewsList.length && !newViewType) {
        setNewViewType(viewsList[0].type);
      }
    } catch (error) {
      console.error('Failed to fetch available views', error);
      setStatus({ key: 'status.loadViewsFailed', params: {}, type: 'error', raw: null });
    }
  }

  async function fetchCanvases(nextSelectedId) {
    setStatus({ key: 'status.loading', params: {}, type: 'info', raw: null });
    setLoading(true);
    try {
      const response = await fetch('/canvases');
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || `${response.status}`);
      }
      const list = Array.isArray(data.canvases) ? data.canvases : [];
      setCanvases(list);
      if (!list.length) {
        setSelectedCanvasId('');
        setViews([]);
        setViewConfigs([]);
        setCanvasName('');
        setCanvasIdentifier('');
        setPreviewUrl('');
        setStatus({ key: 'status.noCanvas', params: {}, type: 'info', raw: null });
        return;
      }
      const initial = nextSelectedId || selectedCanvasId || list[0].id;
      setSelectedCanvasId(initial);
      await loadCanvas(initial, { silent: Boolean(nextSelectedId) });
    } catch (error) {
      console.error('Failed to fetch canvases', error);
      setStatus({ key: 'status.loadCanvasListFailed', params: {}, type: 'error', raw: null });
    } finally {
      setLoading(false);
    }
  }

  async function loadCanvas(canvasId, { silent = false } = {}) {
    if (!canvasId) {
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`/canvases/${canvasId}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to load canvas');
      }
      const isSameCanvas = data.id === selectedCanvasId;
      setSelectedCanvasId(data.id);
      setCanvasName(data.name || '');
      setCanvasIdentifier(data.id || '');
      setViews(Array.isArray(data.views) ? data.views.map((view) => ({ ...view })) : []);
      setViewConfigs(Array.isArray(data.view_configs) ? data.view_configs : []);
      setPreviewUrl(`/canvases/${data.id}/preview?ts=${Date.now()}`);
      if (!isSameCanvas) {
        setPreviewParamsText('{}');
      }
      setPreviewParamsError(null);
      if (!silent) {
        setStatus({ key: 'status.canvasLoaded', params: { name: data.name || data.id }, type: 'success', raw: null });
      }
    } catch (error) {
      console.error('Failed to load canvas', error);
      setStatus({ key: 'status.loadCanvasFailed', params: {}, type: 'error', raw: error.message });
    } finally {
      setLoading(false);
    }
  }

  function updateViewCode(viewId, code) {
    setViews((current) => current.map((view) => (view.id === viewId ? { ...view, code } : view)));
  }

  function removeView(viewId) {
    setViews((current) => current.filter((view) => view.id !== viewId));
  }

  async function saveCanvas() {
    if (!selectedCanvasId) {
      setStatus({ key: 'status.selectBeforeSave', params: {}, type: 'error', raw: null });
      return;
    }
    if (!canvasIdentifier.trim()) {
      setStatus({ key: 'status.canvasIdEmpty', params: {}, type: 'error', raw: null });
      return;
    }
    const payload = {
      name: canvasName,
      views: views.map((view) => ({ id: view.id, code: view.code })),
    };
    if (canvasIdentifier.trim() !== selectedCanvasId) {
      payload.new_id = canvasIdentifier.trim();
    }
    setSaving(true);
    try {
      const response = await fetch(`/canvases/${selectedCanvasId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to save canvas');
      }
      setSelectedCanvasId(data.id);
      setCanvasIdentifier(data.id);
      setCanvasName(data.name || '');
      setViews(Array.isArray(data.views) ? data.views.map((view) => ({ ...view })) : []);
      setViewConfigs(Array.isArray(data.view_configs) ? data.view_configs : []);
      setStatus({ key: 'status.saveSuccess', params: {}, type: 'success', raw: null });
      await fetchCanvases(data.id);
      refreshPreview(data.id);
    } catch (error) {
      console.error('Failed to save canvas', error);
      setStatus({ key: 'status.saveFailed', params: {}, type: 'error', raw: error.message });
    } finally {
      setSaving(false);
    }
  }

  async function createCanvas(event) {
    event?.preventDefault();
    if (!newCanvasName.trim()) {
      setStatus({ key: 'status.createCanvasMissing', params: {}, type: 'error', raw: null });
      return;
    }
    try {
      const response = await fetch('/canvases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newCanvasName.trim() }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to create canvas');
      }
      setNewCanvasName('');
      setStatus({ key: 'status.canvasCreated', params: { name: data.name || data.id }, type: 'success', raw: null });
      await fetchCanvases(data.id);
    } catch (error) {
      console.error('Failed to create canvas', error);
      setStatus({ key: 'status.createCanvasFailed', params: {}, type: 'error', raw: error.message });
    }
  }

  function addView(event) {
    event?.preventDefault();
    if (!selectedCanvasId) {
      setStatus({ key: 'status.selectBeforeAddView', params: {}, type: 'error', raw: null });
      return;
    }
    const trimmedId = newViewId.trim();
    const selectedType = newViewType || availableViews[0]?.type;
    if (!trimmedId || !selectedType) {
      setStatus({ key: 'status.addViewMissing', params: {}, type: 'error', raw: null });
      return;
    }
    if (views.some((view) => view.id === trimmedId)) {
      setStatus({ key: 'status.addViewDuplicate', params: {}, type: 'error', raw: null });
      return;
    }
    const defaultBody = `return {\n  "type": "${selectedType}",\n}\n`;
    setViews((current) => [...current, { id: trimmedId, code: defaultBody }]);
    setNewViewId('');
    setStatus({ key: 'status.addViewSuccess', params: { id: trimmedId }, type: 'success', raw: null });
  }

  function parsePreviewParams() {
    const trimmed = previewParamsText.trim();
    if (!trimmed) {
      return {};
    }
    try {
      const parsed = JSON.parse(trimmed);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error(t('status.previewParamsInvalid'));
      }
      return parsed;
    } catch (error) {
      if (error instanceof Error && error.message) {
        throw error;
      }
      throw new Error(t('status.previewParamsInvalid'));
    }
  }

  async function fetchViewConfigsWithParams(canvasId, paramsObject) {
    if (!canvasId) {
      return;
    }
    const query = new URLSearchParams();
    if (paramsObject && Object.keys(paramsObject).length) {
      query.set('params', JSON.stringify(paramsObject));
    }
    const endpoint = query.toString()
      ? `/canvases/${canvasId}/view-configs?${query.toString()}`
      : `/canvases/${canvasId}/view-configs`;
    const response = await fetch(endpoint, { method: 'GET' });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || response.statusText || 'Failed to load view configs');
    }
    setViewConfigs(Array.isArray(data.view_configs) ? data.view_configs : []);
  }

  async function refreshPreview(idOverride) {
    const id = idOverride || selectedCanvasId;
    if (!id) {
      return;
    }
    let paramsObject;
    try {
      paramsObject = parsePreviewParams();
      setPreviewParamsError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : t('status.previewParamsInvalid');
      setPreviewParamsError(message);
      setStatus({ key: null, params: {}, type: 'error', raw: message });
      return;
    }
    setLoadingPreview(true);
    try {
      const query = new URLSearchParams({ ts: String(Date.now()) });
      if (paramsObject && Object.keys(paramsObject).length) {
        query.set('params', JSON.stringify(paramsObject));
      }
      const previewEndpoint = `/canvases/${id}/preview?${query.toString()}`;
      const response = await fetch(previewEndpoint, { method: 'GET' });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || response.statusText || 'Preview failed');
      }
      setPreviewUrl(previewEndpoint);
      await fetchViewConfigsWithParams(id, paramsObject);
      setStatus({ key: 'status.previewReady', params: {}, type: 'success', raw: null });
    } catch (error) {
      console.error('Failed to refresh preview', error);
      setStatus({ key: 'status.previewFailed', params: { message: error.message }, type: 'error', raw: null });
    } finally {
      setLoadingPreview(false);
    }
  }

  useEffect(() => {
    function handleSaveShortcut(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
        event.preventDefault();
        if (!saving) {
          saveCanvas();
        }
      }
    }

    window.addEventListener('keydown', handleSaveShortcut);
    return () => window.removeEventListener('keydown', handleSaveShortcut);
  }, [saving, saveCanvas]);

  function inferViewTypeFromCode(code) {
    if (typeof code !== 'string') {
      return null;
    }
    const match = code.match(/['"]type['"]\s*:\s*['"]([^'"\s]+)['"]/);
    return match ? match[1] : null;
  }

  function resolveViewConfig(viewId) {
    return viewConfigsById.get(viewId) || null;
  }

  function resolveViewType(view) {
    const config = resolveViewConfig(view.id);
    const configType = config?.config?.type;
    const inferred = inferViewTypeFromCode(view.code);
    if (inferred && configType && inferred === configType) {
      return inferred;
    }
    return inferred || configType || null;
  }

  function toggleViewCollapse(viewId) {
    setCollapsedViews((previous) =>
      previous.includes(viewId) ? previous.filter((id) => id !== viewId) : [...previous, viewId],
    );
  }

  function handleCopyConfig(viewId) {
    const config = resolveViewConfig(viewId);
    if (!config || !config.config) {
      notify(t('view.configUnavailable'));
      return;
    }
    try {
      const payload = JSON.stringify(config.config, null, 2);
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(payload).then(
          () => notify(t('toast.copied'), 'success'),
          (error) => notify(t('toast.copyFailed', { message: error.message }), 'error'),
        );
      } else {
        notify(t('toast.clipboardUnavailable'), 'error');
      }
    } catch (error) {
      console.error('Failed to copy config', error);
      notify(t('toast.copyFailed', { message: error.message }), 'error');
    }
  }

  return (
    <div className="split-layout canvas-page-layout">
      <div className="card-list">
        <div className="section-card">
          {statusMessage ? (
            <div
              className={clsx(
                'status-banner',
                status.type === 'error' && 'error',
                status.type === 'success' && 'success',
              )}
            >
              {statusMessage}
            </div>
          ) : null}
          {loading ? <p className="muted-text">{t('status.loading')}</p> : null}
          <div className="form-grid">
            <div className="input-field">
              <label htmlFor="canvas-select">{t('label.availableCanvases')}</label>
              <select
                id="canvas-select"
                value={selectedCanvasId}
                onChange={(event) => {
                  const id = event.target.value;
                  setSelectedCanvasId(id);
                  loadCanvas(id);
                }}
              >
                {canvases.map((canvas) => (
                  <option key={canvas.id} value={canvas.id}>
                    {canvas.name} ({canvas.id})
                  </option>
                ))}
              </select>
            </div>
            <div className="input-field">
              <label htmlFor="canvas-name">{t('label.canvasName')}</label>
              <input
                id="canvas-name"
                value={canvasName}
                onChange={(event) => setCanvasName(event.target.value)}
                placeholder={t('placeholder.canvasName')}
              />
            </div>
            <div className="input-field">
              <label htmlFor="canvas-id">{t('label.canvasId')}</label>
              <input
                id="canvas-id"
                value={canvasIdentifier}
                onChange={(event) => setCanvasIdentifier(event.target.value)}
                placeholder={t('placeholder.canvasId')}
              />
            </div>
          </div>
          <div className="inline-actions">
            <button type="button" className="primary-button" onClick={saveCanvas} disabled={saving}>
              {t('button.save')}
            </button>
            <button type="button" className="secondary-button" onClick={() => refreshPreview()} disabled={loadingPreview}>
              {t('button.preview')}
            </button>
          </div>
        </div>

        <div className="section-card">
          <h2 className="section-title">{t('section.createCanvas')}</h2>
          <div className="input-field">
            <label htmlFor="new-canvas-name">{t('label.newCanvasName')}</label>
            <input
              id="new-canvas-name"
              value={newCanvasName}
              onChange={(event) => setNewCanvasName(event.target.value)}
              placeholder={t('placeholder.newCanvasName')}
            />
          </div>
          <button type="button" className="primary-button" onClick={createCanvas}>
            {t('button.createCanvas')}
          </button>
        </div>

        <div className="section-card">
          <h2 className="section-title">{t('section.addView')}</h2>
          <div className="form-grid">
            <div className="input-field">
              <label htmlFor="new-view-id">{t('label.newViewId')}</label>
              <input
                id="new-view-id"
                value={newViewId}
                onChange={(event) => setNewViewId(event.target.value)}
                placeholder={t('placeholder.newViewId')}
              />
            </div>
            <div className="input-field">
              <label htmlFor="new-view-type">{t('label.newViewType')}</label>
              <select id="new-view-type" value={newViewType} onChange={(event) => setNewViewType(event.target.value)}>
                {availableViews.map((view) => (
                  <option key={view.type} value={view.type}>
                    {view.type}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button type="button" className="secondary-button" onClick={addView}>
            {t('button.addView')}
          </button>
          <div className="params-panel">
            <h4>{t('section.availableViews')}</h4>
            {availableViews.length === 0 ? (
              <p className="muted-text">{t('status.loadViewsFailed')}</p>
            ) : (
              availableViews.map((view) => (
                <div key={view.type} className="param-item">
                  <strong>{view.type}</strong>
                  <span className="muted-text">{Object.keys(view.params || {}).length} params</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="card-list">
        <div className="section-card">
          <h2 className="section-title">{t('section.views')}</h2>
          {views.length === 0 ? (
            <div className="empty-state">{t('views.empty')}</div>
          ) : (
            <div className="card-list">
              {views.map((view) => {
                const viewType = resolveViewType(view);
                const params = (viewType && availableViewMap.get(viewType)) || {};
                const config = resolveViewConfig(view.id);
                const sanitizedId = (view.id || 'unnamed').replace(/[^a-zA-Z0-9_-]/g, '-');
                const editorId = `view-editor-${sanitizedId || 'unnamed'}`;
                const isCollapsed = collapsedViews.includes(view.id);
                return (
                  <div key={view.id} className={clsx('view-card', isCollapsed && 'collapsed')}>
                    <div className="view-card-header">
                      <h3>
                        {view.id || t('view.unnamed')}
                        {viewType ? <span className="muted-text"> · {viewType}</span> : null}
                      </h3>
                      <div className="view-card-actions">
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => toggleViewCollapse(view.id)}
                          aria-expanded={!isCollapsed}
                          aria-controls={editorId}
                        >
                          {t(isCollapsed ? 'button.expandView' : 'button.collapseView')}
                        </button>
                        <button type="button" className="ghost-button" onClick={() => removeView(view.id)}>
                          {t('button.remove')}
                        </button>
                      </div>
                    </div>
                    {isCollapsed ? (
                      <p className="muted-text view-collapsed-hint">{t('view.collapsedHint')}</p>
                    ) : (
                      <div className="view-editor" id={editorId}>
                        <textarea
                          value={view.code}
                          onChange={(event) => updateViewCode(view.id, event.target.value)}
                        />
                        <div className="params-panel">
                          <h4>{viewType ? `${t('label.viewParams')} (${viewType})` : t('label.viewParams')}</h4>
                          {params && Object.keys(params).length ? (
                            Object.entries(params).map(([paramKey, description]) => (
                              <div key={paramKey} className="param-item">
                                <strong>{paramKey}</strong>
                                <span>{description}</span>
                              </div>
                            ))
                          ) : (
                            <p className="muted-text">{t('view.paramsUnavailable')}</p>
                          )}
                          <h4>{t('label.viewPreview')}</h4>
                          {config?.error ? (
                            <p className="muted-text">{t('view.configError', { message: config.error })}</p>
                          ) : config?.config ? (
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{JSON.stringify(config.config, null, 2)}</pre>
                          ) : (
                            <p className="muted-text">{t('view.configUnavailable')}</p>
                          )}
                          <button type="button" className="secondary-button" onClick={() => handleCopyConfig(view.id)}>
                            {t('button.copyConfig')}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="floating-preview-wrapper">
        <div className="section-card live-preview-card">
          <h2 className="section-title">{t('section.livePreview')}</h2>
          <div className="preview-frame">
            {previewUrl ? (
              <img src={previewUrl} alt={t('alt.preview')} />
            ) : (
              <p className="muted-text">{t('status.selectCanvas')}</p>
            )}
          </div>
        </div>
        <div className="section-card preview-params-card">
          <h2 className="section-title">{t('label.previewParams')}</h2>
          <div className="input-field">
            <textarea
              id="preview-params"
              className={clsx(previewParamsError && 'field-error')}
              value={previewParamsText}
              onChange={(event) => {
                setPreviewParamsText(event.target.value);
                if (previewParamsError) {
                  setPreviewParamsError(null);
                }
              }}
              placeholder={t('placeholder.previewParams')}
            />
          </div>
          {previewParamsError ? <p className="muted-text">{previewParamsError}</p> : null}
        </div>
      </div>
    </div>
  );
}
