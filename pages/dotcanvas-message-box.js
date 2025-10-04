(function () {
  if (window.dotcanvasLogger) {
    return;
  }

  const MAX_MESSAGES = 50;
  const LEVEL_LABELS = {
    log: 'Info',
    info: 'Info',
    warn: 'Warning',
    error: 'Error',
  };
  const BACKEND_LEVEL_MAP = {
    debug: 'log',
    info: 'info',
    warning: 'warn',
    warn: 'warn',
    error: 'error',
    critical: 'error',
    exception: 'error',
  };
  const BACKEND_POLL_INTERVAL = 4000;
  const BACKEND_INITIAL_LIMIT = 50;
  const BACKEND_MAX_DELAY = 60000;

  function createStyle() {
    const style = document.createElement('style');
    style.id = 'dotcanvas-message-box-style';
    style.textContent = `
      .dotcanvas-message-box {
        position: fixed;
        bottom: 1.25rem;
        right: 1.25rem;
        max-width: min(22rem, calc(100vw - 2.5rem));
        background: rgba(15, 23, 42, 0.94);
        color: #e2e8f0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 0.85rem;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.35);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        z-index: 1000;
      }
      .dotcanvas-message-box__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0.6rem 0.75rem;
        background: rgba(30, 41, 59, 0.92);
        border-bottom: 1px solid rgba(148, 163, 184, 0.25);
      }
      .dotcanvas-message-box__title {
        margin: 0;
        font-size: 0.95rem;
        font-weight: 600;
        color: #f8fafc;
      }
      .dotcanvas-message-box__controls {
        display: flex;
        gap: 0.4rem;
      }
      .dotcanvas-message-box__button {
        background: rgba(71, 85, 105, 0.35);
        color: #e2e8f0;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
      }
      .dotcanvas-message-box__button:hover {
        background: rgba(148, 163, 184, 0.25);
      }
      .dotcanvas-message-box__body {
        max-height: 280px;
        overflow: auto;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 0.75rem;
      }
      .dotcanvas-message-box--collapsed .dotcanvas-message-box__body {
        display: none;
      }
      .dotcanvas-message-box__entry {
        background: rgba(15, 23, 42, 0.65);
        border-radius: 8px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 0.5rem 0.6rem;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .dotcanvas-message-box__entry::before {
        content: '';
        display: block;
        height: 0.2rem;
        border-radius: 999px;
        background: rgba(96, 165, 250, 0.8);
      }
      .dotcanvas-message-box__entry--warn::before {
        background: rgba(251, 191, 36, 0.85);
      }
      .dotcanvas-message-box__entry--error::before {
        background: rgba(248, 113, 113, 0.9);
      }
      .dotcanvas-message-box__meta {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        font-size: 0.7rem;
        color: #cbd5f5;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .dotcanvas-message-box__text {
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.35;
      }
      @media (max-width: 640px) {
        .dotcanvas-message-box {
          left: 0.75rem;
          right: 0.75rem;
          max-width: unset;
          width: calc(100vw - 1.5rem);
        }
      }
    `;
    document.head.appendChild(style);
  }

  function formatTimestamp(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  }

  function normaliseArg(arg) {
    if (arg instanceof Error) {
      return arg.stack || arg.message || String(arg);
    }
    if (typeof arg === 'string') {
      return arg;
    }
    if (typeof arg === 'number' || typeof arg === 'boolean' || arg === null || arg === undefined) {
      return String(arg);
    }
    try {
      return JSON.stringify(arg, null, 2);
    } catch (err) {
      return '[object]';
    }
  }

  class DotcanvasMessageBox {
    constructor(maxMessages = MAX_MESSAGES) {
      this.maxMessages = maxMessages;
      this.container = document.createElement('div');
      this.container.className = 'dotcanvas-message-box';

      const header = document.createElement('div');
      header.className = 'dotcanvas-message-box__header';

      const title = document.createElement('div');
      title.className = 'dotcanvas-message-box__title';
      title.textContent = 'Messages';
      header.appendChild(title);

      const controls = document.createElement('div');
      controls.className = 'dotcanvas-message-box__controls';

      const clearBtn = document.createElement('button');
      clearBtn.type = 'button';
      clearBtn.className = 'dotcanvas-message-box__button';
      clearBtn.textContent = 'Clear';
      clearBtn.addEventListener('click', () => this.clear());
      controls.appendChild(clearBtn);

      const collapseBtn = document.createElement('button');
      collapseBtn.type = 'button';
      collapseBtn.className = 'dotcanvas-message-box__button';
      collapseBtn.textContent = 'Collapse';
      collapseBtn.addEventListener('click', () => {
        const collapsed = this.container.classList.toggle('dotcanvas-message-box--collapsed');
        collapseBtn.textContent = collapsed ? 'Expand' : 'Collapse';
      });
      controls.appendChild(collapseBtn);

      header.appendChild(controls);

      const body = document.createElement('div');
      body.className = 'dotcanvas-message-box__body';

      this.container.appendChild(header);
      this.container.appendChild(body);
      document.body.appendChild(this.container);

      this.body = body;
      this.entries = [];
    }

    push(level, args, options = {}) {
      const entry = document.createElement('div');
      entry.className = `dotcanvas-message-box__entry dotcanvas-message-box__entry--${level}`;

      const meta = document.createElement('div');
      meta.className = 'dotcanvas-message-box__meta';
      const label = options.label || LEVEL_LABELS[level] || 'Info';
      const timestamp = options.timestamp instanceof Date
        ? options.timestamp
        : new Date(typeof options.timestamp === 'number' ? options.timestamp : Date.now());
      meta.innerHTML = `<span>${label}</span><span>${formatTimestamp(timestamp)}</span>`;

      const text = document.createElement('div');
      text.className = 'dotcanvas-message-box__text';
      text.textContent = args.map(item => normaliseArg(item)).join('\n');

      entry.appendChild(meta);
      entry.appendChild(text);

      this.body.appendChild(entry);
      this.entries.push(entry);

      while (this.entries.length > this.maxMessages) {
        const removed = this.entries.shift();
        removed?.remove();
      }

      this.body.scrollTop = this.body.scrollHeight;
    }

    clear() {
      this.entries.forEach(entry => entry.remove());
      this.entries = [];
    }
  }

  class DotcanvasLogger {
    constructor(box) {
      this.box = box;
    }

    log(...args) {
      this.box.push('log', args);
    }

    info(...args) {
      this.box.push('info', args);
    }

    warn(...args) {
      this.box.push('warn', args);
    }

    error(...args) {
      this.box.push('error', args);
    }

    pushBackendEntry(entry) {
      if (!entry || typeof entry !== 'object') {
        return;
      }

      const levelKey = normaliseBackendLevel(entry.level);
      const label = typeof entry.level === 'string' ? entry.level : 'Server';

      const segments = [];
      if (entry.logger) {
        segments.push(entry.logger);
      } else if (entry.module) {
        segments.push(entry.module);
      }
      const funcName = entry.func && entry.func !== '<module>' ? entry.func : null;
      if (funcName) {
        segments.push(funcName);
      }
      const lineNumber = Number(entry.line);
      if (Number.isFinite(lineNumber) && segments.length) {
        const lastIdx = segments.length - 1;
        segments[lastIdx] = `${segments[lastIdx]}:${lineNumber}`;
      } else if (Number.isFinite(lineNumber)) {
        segments.push(`line ${lineNumber}`);
      }
      const sourcePrefix = segments.length ? `[${segments.join(' › ')}]` : '[Server]';

      const lines = [];
      const baseMessage = typeof entry.message === 'string' && entry.message.trim()
        ? entry.message
        : typeof entry.formatted === 'string' && entry.formatted.trim()
          ? entry.formatted
          : '(no message)';
      lines.push(`${sourcePrefix} ${baseMessage}`);

      const additional = [];
      if (entry.exception && typeof entry.exception === 'string') {
        additional.push(entry.exception);
      } else if (
        typeof entry.formatted === 'string'
        && entry.formatted.trim()
        && entry.formatted !== baseMessage
      ) {
        additional.push(entry.formatted);
      }

      additional.forEach(item => lines.push(item));

      const created = typeof entry.created === 'number' ? entry.created * 1000 : undefined;
      this.box.push(levelKey, lines, { label, timestamp: created });
    }
  }

  createStyle();

  const messageBox = new DotcanvasMessageBox();
  const logger = new DotcanvasLogger(messageBox);

  function normaliseBackendLevel(level) {
    if (typeof level !== 'string') {
      return 'log';
    }
    const normalized = BACKEND_LEVEL_MAP[level.toLowerCase()];
    return normalized || 'log';
  }

  function startBackendLogPolling() {
    if (window.dotcanvasBackendLogPolling) {
      return;
    }

    const state = {
      lastId: 0,
      delay: BACKEND_POLL_INTERVAL,
      timerId: null,
    };

    async function poll() {
      const params = new URLSearchParams();
      if (state.lastId > 0) {
        params.set('since', String(state.lastId));
        params.set('limit', '200');
      } else {
        params.set('limit', String(BACKEND_INITIAL_LIMIT));
      }

      try {
        const res = await fetch(`/logs?${params.toString()}`, { cache: 'no-store' });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const payload = await res.json();
        const entries = Array.isArray(payload?.logs) ? payload.logs : [];
        entries.forEach(entry => {
          const entryId = Number(entry?.id) || 0;
          if (entryId <= state.lastId) {
            return;
          }
          state.lastId = entryId;
          logger.pushBackendEntry(entry);
        });
        state.delay = BACKEND_POLL_INTERVAL;
      } catch (err) {
        if (typeof console !== 'undefined' && typeof console.debug === 'function') {
          console.debug('Backend log polling failed', err);
        }
        state.delay = Math.min(Math.round(state.delay * 1.5) || BACKEND_POLL_INTERVAL, BACKEND_MAX_DELAY);
      } finally {
        state.timerId = window.setTimeout(poll, state.delay);
      }
    }

    state.timerId = window.setTimeout(poll, 100);

    window.addEventListener('beforeunload', () => {
      if (state.timerId) {
        clearTimeout(state.timerId);
      }
    });

    window.dotcanvasBackendLogPolling = state;
  }

  const fallback = console.log.bind(console);
  const originalConsole = {
    log: console.log.bind(console),
    info: console.info ? console.info.bind(console) : fallback,
    warn: console.warn ? console.warn.bind(console) : fallback,
    error: console.error ? console.error.bind(console) : fallback,
  };

  console.log = (...args) => {
    originalConsole.log(...args);
    logger.log(...args);
  };

  console.info = (...args) => {
    originalConsole.info(...args);
    logger.info(...args);
  };

  console.warn = (...args) => {
    originalConsole.warn(...args);
    logger.warn(...args);
  };

  console.error = (...args) => {
    originalConsole.error(...args);
    logger.error(...args);
  };

  window.dotcanvasMessageBox = messageBox;
  window.dotcanvasLogger = logger;
  window.dotcanvasStartBackendLogPolling = startBackendLogPolling;

  if (typeof window.fetch === 'function') {
    startBackendLogPolling();
  }
})();
