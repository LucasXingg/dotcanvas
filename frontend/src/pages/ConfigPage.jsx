import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { useTranslation } from '../i18n/LanguageContext.jsx';

function createSchedule(uid) {
  return {
    _uid: uid,
    name: '',
    canvas_id: '',
    cron: '',
    paramsText: '{}',
    disabled: false,
  };
}

function toBoolean(value) {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    return value.toLowerCase() === 'true';
  }
  return false;
}

function normalizeConfig(raw, uidGenerator) {
  const config = { api_key: '', devices: [], disabled: false };
  if (raw && typeof raw === 'object') {
    config.api_key = typeof raw.api_key === 'string' ? raw.api_key : '';
    if (Array.isArray(raw.devices)) {
      config.devices = raw.devices
        .filter((device) => device && typeof device === 'object')
        .map((device) => {
          const schedules = Array.isArray(device.schedules) ? device.schedules : [];
          return {
            _uid: uidGenerator(),
            name: typeof device.name === 'string' ? device.name : '',
            device_id: typeof device.device_id === 'string' ? device.device_id : '',
            schedules: schedules
              .filter((schedule) => schedule && typeof schedule === 'object')
              .map((schedule) => {
                const params = schedule.params && typeof schedule.params === 'object' && !Array.isArray(schedule.params)
                  ? schedule.params
                  : {};
          return {
            _uid: uidGenerator(),
            name: typeof schedule.name === 'string' ? schedule.name : '',
            canvas_id: typeof schedule.canvas_id === 'string' ? schedule.canvas_id : '',
            cron: typeof schedule.cron === 'string' ? schedule.cron : '',
            paramsText: JSON.stringify(params, null, 2),
            disabled: toBoolean(schedule.disabled),
          };
        }),
      };
    });
    }
    config.disabled = toBoolean(raw.disabled);
  }
  return config;
}

export default function ConfigPage() {
  const { t } = useTranslation();
  const uidRef = useRef(1);
  const [config, setConfig] = useState({ api_key: '', devices: [], disabled: false });
  const [status, setStatus] = useState({ key: 'config.status.loading', type: 'info', params: {}, raw: null });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [invalidScheduleIds, setInvalidScheduleIds] = useState(new Set());

  const nextUid = useCallback(() => {
    const value = uidRef.current;
    uidRef.current += 1;
    return value;
  }, []);

  const statusMessage = useMemo(() => {
    if (status.raw) {
      return status.raw;
    }
    if (!status.key) {
      return '';
    }
    return t(status.key, status.params);
  }, [status, t]);

  const fetchConfig = useCallback(async () => {
    setStatus({ key: 'config.status.loading', params: {}, type: 'info', raw: null });
    setLoading(true);
    try {
      const response = await fetch('/config');
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to load config');
      }
      const normalized = normalizeConfig(data.config, nextUid);
      setConfig(normalized);
      setInvalidScheduleIds(new Set());
      setStatus({
        key: normalized.disabled ? 'config.status.tasksDisabled' : 'config.status.loaded',
        params: {},
        type: normalized.disabled ? 'info' : 'success',
        raw: null,
      });
    } catch (error) {
      console.error('Failed to load config', error);
      setStatus({ key: 'config.status.loadError', params: { message: error.message }, type: 'error', raw: null });
    } finally {
      setLoading(false);
    }
  }, [nextUid]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const updateDevice = useCallback((uid, updates) => {
    setConfig((current) => ({
      ...current,
      devices: current.devices.map((device) => (device._uid === uid ? { ...device, ...updates } : device)),
    }));
  }, []);

  const updateSchedule = useCallback((deviceUid, scheduleUid, updates) => {
    setConfig((current) => ({
      ...current,
      devices: current.devices.map((device) => {
        if (device._uid !== deviceUid) {
          return device;
        }
        return {
          ...device,
          schedules: device.schedules.map((schedule) =>
            schedule._uid === scheduleUid ? { ...schedule, ...updates } : schedule,
          ),
        };
      }),
    }));
  }, []);

  const addDevice = useCallback(() => {
    setConfig((current) => ({
      ...current,
      devices: [
        ...current.devices,
        {
          _uid: nextUid(),
          name: '',
          device_id: '',
          schedules: [],
        },
      ],
    }));
  }, [nextUid]);

  const toggleGlobalDisabled = useCallback(() => {
    setConfig((current) => {
      const nextDisabled = !current.disabled;
      setStatus({
        key: nextDisabled ? 'config.status.tasksDisabled' : 'config.status.tasksEnabled',
        params: {},
        type: nextDisabled ? 'info' : 'success',
        raw: null,
      });
      return { ...current, disabled: nextDisabled };
    });
  }, [setStatus]);

  const removeDevice = useCallback(
    (uid) => {
      if (window.confirm(t('confirm.deleteDevice'))) {
        setConfig((current) => ({
          ...current,
          devices: current.devices.filter((device) => device._uid !== uid),
        }));
      }
    },
    [t],
  );

  const addSchedule = useCallback(
    (deviceUid) => {
      setConfig((current) => ({
        ...current,
        devices: current.devices.map((device) => {
          if (device._uid !== deviceUid) {
            return device;
          }
          return {
            ...device,
            schedules: [...device.schedules, createSchedule(nextUid())],
          };
        }),
      }));
    },
    [nextUid],
  );

  const toggleScheduleDisabled = useCallback((deviceUid, scheduleUid) => {
    setConfig((current) => ({
      ...current,
      devices: current.devices.map((device) => {
        if (device._uid !== deviceUid) {
          return device;
        }
        return {
          ...device,
          schedules: device.schedules.map((schedule) =>
            schedule._uid === scheduleUid ? { ...schedule, disabled: !schedule.disabled } : schedule,
          ),
        };
      }),
    }));
  }, []);

  const removeSchedule = useCallback(
    (deviceUid, scheduleUid) => {
      if (!window.confirm(t('confirm.deleteSchedule'))) {
        return;
      }
      setConfig((current) => ({
        ...current,
        devices: current.devices.map((device) => {
          if (device._uid !== deviceUid) {
            return device;
          }
          return {
            ...device,
            schedules: device.schedules.filter((schedule) => schedule._uid !== scheduleUid),
          };
        }),
      }));
      setInvalidScheduleIds((current) => {
        const next = new Set(current);
        next.delete(scheduleUid);
        return next;
      });
    },
    [t],
  );

  const handleParamsChange = useCallback(
    (deviceUid, scheduleUid, value) => {
      setInvalidScheduleIds((current) => {
        if (!current.has(scheduleUid)) {
          return current;
        }
        const next = new Set(current);
        next.delete(scheduleUid);
        return next;
      });
      updateSchedule(deviceUid, scheduleUid, { paramsText: value });
    },
    [updateSchedule],
  );

  const saveConfig = useCallback(async () => {
    const invalid = new Set();
    const payload = {
      api_key: config.api_key,
      disabled: Boolean(config.disabled),
      devices: config.devices.map((device) => ({
        name: device.name,
        device_id: device.device_id,
        schedules: device.schedules.map((schedule) => {
          try {
            const params = schedule.paramsText.trim() ? JSON.parse(schedule.paramsText) : {};
            return {
              name: schedule.name,
              canvas_id: schedule.canvas_id,
              cron: schedule.cron,
              params,
              disabled: Boolean(schedule.disabled),
            };
          } catch (error) {
            invalid.add(schedule._uid);
            return null;
          }
        }).filter(Boolean),
      })),
    };

    if (invalid.size) {
      setInvalidScheduleIds(invalid);
      setStatus({ key: 'config.status.paramsInvalid', params: {}, type: 'error', raw: null });
      return;
    }

    setInvalidScheduleIds(new Set());
    setSaving(true);
    try {
      const response = await fetch('/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail?.errors ? JSON.stringify(data.detail.errors) : data.detail || response.statusText);
      }
      const normalized = normalizeConfig(data.config, nextUid);
      setConfig(normalized);
      setStatus({ key: 'config.status.saved', params: {}, type: 'success', raw: null });
    } catch (error) {
      console.error('Failed to save config', error);
      setStatus({ key: 'config.status.saveError', params: { message: error.message }, type: 'error', raw: null });
    } finally {
      setSaving(false);
    }
  }, [config, nextUid, t]);

  useEffect(() => {
    function handleSaveShortcut(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
        event.preventDefault();
        if (!saving) {
          saveConfig();
        }
      }
    }

    window.addEventListener('keydown', handleSaveShortcut);
    return () => window.removeEventListener('keydown', handleSaveShortcut);
  }, [saveConfig, saving]);

  return (
    <div className="card-list">
      <div className="section-card">
        <div className="view-card-header">
          <h2 className="section-title">{t('config.section.api')}</h2>
          <div className="inline-actions">
            <button type="button" className="secondary-button" onClick={fetchConfig} disabled={loading}>
              {t('button.reload')}
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={toggleGlobalDisabled}
              disabled={loading || saving}
              aria-pressed={config.disabled}
            >
              {t(config.disabled ? 'config.action.enableTasks' : 'config.action.disableTasks')}
            </button>
            <button type="button" className="primary-button" onClick={saveConfig} disabled={saving}>
              {t('button.save')}
            </button>
          </div>
        </div>
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
        <div className="input-field">
          <label htmlFor="api-key-input">{t('config.label.apiKey')}</label>
          <input
            id="api-key-input"
            value={config.api_key}
            onChange={(event) => setConfig((current) => ({ ...current, api_key: event.target.value }))}
            placeholder={t('placeholder.apiKey')}
          />
          <p className="muted-text">{t('config.hint.apiKey')}</p>
        </div>
      </div>

      <div className="section-card">
        <div className="view-card-header">
          <h2 className="section-title">{t('config.section.devices')}</h2>
          <button type="button" className="secondary-button" onClick={addDevice}>
            {t('config.action.addDevice')}
          </button>
        </div>
        {config.devices.length === 0 ? (
          <div className="empty-state">{t('config.empty.devices')}</div>
        ) : (
          <div className="card-list">
            {config.devices.map((device) => (
              <div key={device._uid} className="device-card">
                <div className="view-card-header">
                  <h3>{device.name || t('view.unnamed')}</h3>
                  <button type="button" className="ghost-button" onClick={() => removeDevice(device._uid)}>
                    {t('config.action.removeDevice')}
                  </button>
                </div>
                <div className="form-grid">
                  <div className="input-field">
                    <label>{t('config.label.deviceName')}</label>
                    <input
                      value={device.name}
                      onChange={(event) => updateDevice(device._uid, { name: event.target.value })}
                      placeholder={t('placeholder.deviceName')}
                    />
                  </div>
                  <div className="input-field">
                    <label>{t('config.label.deviceId')}</label>
                    <input
                      value={device.device_id}
                      onChange={(event) => updateDevice(device._uid, { device_id: event.target.value })}
                      placeholder={t('placeholder.deviceId')}
                    />
                  </div>
                </div>
                <div className="view-card-header">
                  <h4>{t('config.action.addSchedule')}</h4>
                  <button type="button" className="secondary-button" onClick={() => addSchedule(device._uid)}>
                    {t('config.action.addSchedule')}
                  </button>
                </div>
                {device.schedules.length === 0 ? (
                  <div className="empty-state">{t('config.empty.schedules')}</div>
                ) : (
                  <div className="card-list">
                    {device.schedules.map((schedule) => {
                      const hasError = invalidScheduleIds.has(schedule._uid);
                      return (
                        <div key={schedule._uid} className="schedule-card">
                          <div className="view-card-header">
                            <h4>{schedule.name || t('placeholder.scheduleName')}</h4>
                            <button
                              type="button"
                              className="ghost-button"
                              onClick={() => removeSchedule(device._uid, schedule._uid)}
                            >
                              {t('config.action.removeSchedule')}
                            </button>
                          </div>
                          <div className="form-grid">
                            <div className="input-field">
                              <label>{t('config.label.scheduleName')}</label>
                              <input
                                value={schedule.name}
                                onChange={(event) =>
                                  updateSchedule(device._uid, schedule._uid, { name: event.target.value })
                                }
                                placeholder={t('placeholder.scheduleName')}
                              />
                            </div>
                            <div className="input-field">
                              <label>{t('config.label.scheduleCanvasId')}</label>
                              <input
                                value={schedule.canvas_id}
                                onChange={(event) =>
                                  updateSchedule(device._uid, schedule._uid, { canvas_id: event.target.value })
                                }
                                placeholder={t('placeholder.scheduleCanvasId')}
                              />
                            </div>
                            <div className="input-field">
                              <label>{t('config.label.scheduleCron')}</label>
                              <input
                                value={schedule.cron}
                                onChange={(event) =>
                                  updateSchedule(device._uid, schedule._uid, { cron: event.target.value })
                                }
                                placeholder={t('placeholder.scheduleCron')}
                              />
                            </div>
                            <div className="input-field checkbox-field">
                              <label className="checkbox-label">
                                <input
                                  type="checkbox"
                                  checked={Boolean(schedule.disabled)}
                                  onChange={() => toggleScheduleDisabled(device._uid, schedule._uid)}
                                />
                                {t('config.label.scheduleDisabled')}
                              </label>
                              <p className="muted-text">{t('config.hint.scheduleDisabled')}</p>
                            </div>
                          </div>
                          <div className="input-field">
                            <label>{t('config.label.scheduleParams')}</label>
                            <textarea
                              className={clsx(hasError && 'field-error')}
                              value={schedule.paramsText}
                              onChange={(event) => handleParamsChange(device._uid, schedule._uid, event.target.value)}
                              placeholder={t('placeholder.scheduleParams')}
                              rows={6}
                            />
                            <p className="muted-text">{t('config.hint.paramsFormat')}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
