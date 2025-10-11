import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { useTranslation } from '../i18n/LanguageContext.jsx';
import { useToast } from '../components/ToastProvider.jsx';

const LOG_POLL_INTERVAL = 4000;

export default function DaemonPage() {
  const { t, language } = useTranslation();
  const { notify } = useToast();
  const [daemonStatus, setDaemonStatus] = useState(null);
  const [status, setStatus] = useState({ key: 'daemon.status.loading', params: {}, type: 'info', raw: null });
  const [loading, setLoading] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [logs, setLogs] = useState([]);
  const [logCursor, setLogCursor] = useState(0);
  const pollTimer = useRef(null);

  const statusMessage = useMemo(() => {
    if (status.raw) {
      return status.raw;
    }
    if (!status.key) {
      return '';
    }
    return t(status.key, status.params);
  }, [status, t]);

  const formattedTasks = useMemo(() => {
    if (!daemonStatus?.tasks || !Array.isArray(daemonStatus.tasks)) {
      return [];
    }
    return daemonStatus.tasks.map((task) => ({
      ...task,
      next_run: task.next_run ? new Date(task.next_run) : null,
      last_run: task.last_run ? new Date(task.last_run) : null,
    }));
  }, [daemonStatus]);

  const latestLogId = useMemo(() => {
    if (logs.length) {
      return logs[logs.length - 1].id;
    }
    return logCursor;
  }, [logs, logCursor]);

  const updateStatus = useCallback((key, type = 'info', params = {}) => {
    setStatus({ key, type, params, raw: null });
  }, []);

  const updateStatusRaw = useCallback((message, type = 'info') => {
    setStatus({ key: null, params: {}, type, raw: message });
  }, []);

  const formatDateTime = useCallback(
    (value) => {
      if (!value) {
        return t('daemon.notRun');
      }
      const date = value instanceof Date ? value : new Date(value);
      if (Number.isNaN(date.getTime())) {
        return String(value);
      }
      const locale = language === 'zh' ? 'zh-CN' : 'en-US';
      return date.toLocaleString(locale, { hour12: false });
    },
    [language, t],
  );

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/daemon/status');
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to fetch status');
      }
      setDaemonStatus(data);
      if (data.error) {
        updateStatusRaw(data.error, 'error');
      } else if (data.running) {
        updateStatus('daemon.status.running', 'success');
      } else {
        updateStatus('daemon.status.stopped', 'info');
      }
    } catch (error) {
      console.error('Failed to load daemon status', error);
      updateStatus('daemon.status.actionFailed', 'error', { message: error.message });
    } finally {
      setLoading(false);
    }
  }, [updateStatus, updateStatusRaw]);

  const performAction = useCallback(
    async (action) => {
      setActionBusy(true);
      try {
        const response = await fetch(`/daemon/${action}`, { method: 'POST' });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || response.statusText || 'Daemon action failed');
        }
        setDaemonStatus(data);
        updateStatus('daemon.status.actionSuccess', 'success');
        notify(t('daemon.status.actionSuccess'), 'success');
      } catch (error) {
        console.error('Daemon action failed', error);
        updateStatus('daemon.status.actionFailed', 'error', { message: error.message });
        notify(t('daemon.status.actionFailed', { message: error.message }), 'error');
      } finally {
        setActionBusy(false);
      }
    },
    [notify, t, updateStatus],
  );

  const fetchLogs = useCallback(
    async (initial = false) => {
      try {
        const params = new URLSearchParams();
        params.set('limit', initial ? '50' : '100');
        if (!initial && latestLogId) {
          params.set('since', String(latestLogId));
        }
        const response = await fetch(`/logs?${params.toString()}`, { cache: 'no-store' });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || response.statusText || 'Failed to load logs');
        }
        const entries = Array.isArray(data.logs) ? data.logs : [];
        if (entries.length) {
          setLogs((current) => {
            const seen = new Set(current.map((i) => i.id));
            const merged = initial ? [] : current.slice();
            let added = false;

            entries.forEach((entry) => {
              if (!seen.has(entry.id)) {
                merged.push(entry);
                seen.add(entry.id);
                added = true;
              }
            });
            
            return added ? merged : current;
          });
          setLogCursor(entries[entries.length - 1].id);
        } else if (initial) {
          setLogs([]);
        }
      } catch (error) {
        console.error('Failed to fetch logs', error);
      }
    },
    [latestLogId],
  );

  useEffect(() => {
    fetchStatus();
    fetchLogs(true);
  }, [fetchLogs, fetchStatus]);

  useEffect(() => {
    pollTimer.current = window.setInterval(() => {
      fetchLogs(false);
    }, LOG_POLL_INTERVAL);
    return () => window.clearInterval(pollTimer.current);
  }, [fetchLogs]);

  const logEntries = useMemo(() => {
    return logs
      .slice()
      .sort((a, b) => Number(a.id) - Number(b.id))
      .map((entry) => ({
        ...entry,
        created: entry.created ? new Date(entry.created * 1000) : null,
      }));
  }, [logs]);

  const isRunning = Boolean(daemonStatus?.running);

  const startedAtText = useMemo(() => {
    if (!daemonStatus?.started_at) {
      return '';
    }
    return formatDateTime(daemonStatus.started_at);
  }, [daemonStatus, formatDateTime]);

  return (
    <div className="card-list">
      <div className="section-card">
        <h2 className="section-title">{t('daemon.section.status')}</h2>
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
        <div className="inline-actions">
          <button
            type="button"
            className="primary-button"
            onClick={() => performAction('start')}
            disabled={actionBusy || isRunning}
          >
            {t('button.daemonStart')}
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => performAction('stop')}
            disabled={actionBusy || !isRunning}
          >
            {t('button.daemonStop')}
          </button>
          <button type="button" className="secondary-button" onClick={() => performAction('restart')} disabled={actionBusy}>
            {t('button.daemonRestart')}
          </button>
          <button type="button" className="ghost-button" onClick={fetchStatus} disabled={loading}>
            {t('button.refreshStatus')}
          </button>
        </div>
        <div className="daemon-meta">
          <p className="muted-text">
            {daemonStatus?.task_count != null
              ? t('daemon.taskCount', { value: daemonStatus.task_count })
              : t('daemon.noTasks')}
          </p>
          {startedAtText ? <p className="muted-text">{t('daemon.startedAt', { value: startedAtText })}</p> : null}
          {daemonStatus?.error ? <p className="muted-text">{t('daemon.status.errorHint')}</p> : null}
        </div>
      </div>

      <div className="section-card">
        <h2 className="section-title">{t('daemon.section.schedules')}</h2>
        {formattedTasks.length === 0 ? (
          <div className="empty-state">{t('daemon.noTasks')}</div>
        ) : (
          <div className="card-list">
            {formattedTasks.map((task, index) => {
              const key = task.id || task.task_id || `${task.device_id || 'device'}-${task.task_name || index}`;
              return (
                <div key={key} className="device-card">
                  <div className="view-card-header">
                    <h3>{task.task_name || task.id || t('view.unnamed')}</h3>
                    <span className="muted-text">{task.device_name || task.device || t('daemon.unknownDevice')}</span>
                  </div>
                  <div className="params-panel">
                    <div className="param-item">
                      <strong>{t('daemon.nextRun', { value: '' })}</strong>
                      <span>{formatDateTime(task.next_run)}</span>
                    </div>
                    <div className="param-item">
                      <strong>{t('daemon.lastRun', { value: '' })}</strong>
                      <span>{formatDateTime(task.last_run)}</span>
                    </div>
                    {task.error ? (
                      <div className="param-item">
                        <strong>{t('daemon.error', { value: '' })}</strong>
                        <span>{task.error}</span>
                      </div>
                    ) : null}
                  {task.canvas_id ? (
                    <div className="param-item">
                      <strong>{t('config.label.scheduleCanvasId')}</strong>
                      <span>{task.canvas_id}</span>
                    </div>
                  ) : null}
                  {task.device_id ? (
                    <div className="param-item">
                      <strong>{t('daemon.deviceId', { value: '' })}</strong>
                      <span>{task.device_id}</span>
                    </div>
                  ) : null}
                  {task.params ? (
                    <div className="param-item">
                      <strong>{t('daemon.params', { value: '' })}</strong>
                      <span>{typeof task.params === 'object' ? JSON.stringify(task.params, null, 2) : String(task.params)}</span>
                    </div>
                  ) : null}
                </div>
              </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="section-card">
        <div className="view-card-header">
          <h2 className="section-title">{t('daemon.section.logs')}</h2>
          <button
            type="button"
            className="ghost-button"
            onClick={() => {
              setLogs([]);
            }}
          >
            {t('button.clearLogs')}
          </button>
        </div>
        {logEntries.length === 0 ? (
          <div className="empty-state">{t('logs.empty')}</div>
        ) : (
          <div className="log-feed">
            {logEntries.map((entry) => (
              <div key={entry.id} className={clsx('log-entry', entry.level && entry.level.toLowerCase())}>
                <div className="meta">
                  <span>{entry.created ? entry.created.toLocaleTimeString() : ''}</span>
                  <span>{entry.logger}</span>
                </div>
                <div>{entry.formatted || entry.message}</div>
                {entry.exception ? <pre style={{ whiteSpace: 'pre-wrap' }}>{entry.exception}</pre> : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
