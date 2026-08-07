import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { marked } from 'marked';
import clsx from 'clsx';
import { useTranslation } from '../i18n/LanguageContext.jsx';

marked.setOptions({
  gfm: true,
  breaks: false,
});

function rewriteDocHref(href, currentPath) {
  if (!href || href.startsWith('#') || href.startsWith('http://') || href.startsWith('https://') || href.startsWith('mailto:')) {
    return href;
  }
  if (href.startsWith('/ui/')) {
    return href;
  }
  const baseDir = currentPath.includes('/')
    ? currentPath.slice(0, currentPath.lastIndexOf('/') + 1)
    : '';
  let resolved = href.replace(/^\.\//, '');
  if (resolved.startsWith('../')) {
    const parts = baseDir.split('/').filter(Boolean);
    while (resolved.startsWith('../')) {
      parts.pop();
      resolved = resolved.slice(3);
    }
    resolved = [...parts, resolved].join('/');
  } else if (!resolved.startsWith('/')) {
    resolved = `${baseDir}${resolved}`;
  } else {
    resolved = resolved.replace(/^\//, '');
  }
  if (resolved.endsWith('.md')) {
    return `/docs/${resolved}`;
  }
  return href;
}

function renderMarkdown(markdown, currentPath) {
  const renderer = new marked.Renderer();
  renderer.link = ({ href, title, text }) => {
    const nextHref = rewriteDocHref(href || '', currentPath);
    const titleAttr = title ? ` title="${title}"` : '';
    const external = nextHref.startsWith('http://') || nextHref.startsWith('https://');
    const rel = external ? ' rel="noreferrer noopener" target="_blank"' : '';
    return `<a href="${nextHref}"${titleAttr}${rel}>${text}</a>`;
  };
  return marked.parse(markdown || '', { renderer });
}

export default function DocsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { '*': docPathParam } = useParams();
  const selectedPath = docPathParam || 'index.md';

  const [docs, setDocs] = useState([]);
  const [doc, setDoc] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDoc, setLoadingDoc] = useState(true);
  const [error, setError] = useState(null);

  const loadList = useCallback(async () => {
    setLoadingList(true);
    setError(null);
    try {
      const response = await fetch('/documentation');
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to load docs');
      }
      setDocs(Array.isArray(data.docs) ? data.docs : []);
    } catch (err) {
      console.error('Failed to load documentation list', err);
      setError(err.message);
    } finally {
      setLoadingList(false);
    }
  }, []);

  const loadDoc = useCallback(async (path) => {
    setLoadingDoc(true);
    setError(null);
    try {
      const response = await fetch(`/documentation/${path}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || 'Failed to load document');
      }
      setDoc(data);
    } catch (err) {
      console.error('Failed to load document', err);
      setDoc(null);
      setError(err.message);
    } finally {
      setLoadingDoc(false);
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  useEffect(() => {
    loadDoc(selectedPath);
  }, [loadDoc, selectedPath]);

  const html = useMemo(() => {
    if (!doc?.content) {
      return '';
    }
    return renderMarkdown(doc.content, doc.path || selectedPath);
  }, [doc, selectedPath]);

  function handleContentClick(event) {
    const anchor = event.target.closest('a');
    if (!anchor) {
      return;
    }
    const href = anchor.getAttribute('href');
    if (!href || !href.startsWith('/docs/')) {
      return;
    }
    event.preventDefault();
    navigate(href);
  }

  const groupedDocs = useMemo(() => {
    const groups = { root: [], views: [], other: [] };
    docs.forEach((item) => {
      if (!item.path.includes('/')) {
        groups.root.push(item);
      } else if (item.path.startsWith('views/')) {
        groups.views.push(item);
      } else {
        groups.other.push(item);
      }
    });
    return groups;
  }, [docs]);

  return (
    <div className="docs-layout">
      <aside className="section-card docs-sidebar">
        <h2>{t('docs.section.index')}</h2>
        {loadingList ? <p className="muted-text">{t('docs.status.loading')}</p> : null}
        {!loadingList && !docs.length ? <p className="muted-text">{t('docs.empty')}</p> : null}
        <nav className="docs-nav">
          {groupedDocs.root.map((item) => (
            <Link
              key={item.path}
              to={`/docs/${item.path}`}
              className={clsx('docs-nav-link', selectedPath === item.path && 'active')}
            >
              {item.title}
            </Link>
          ))}
          {groupedDocs.other.length ? (
            <>
              <p className="docs-nav-group">{t('docs.group.guides')}</p>
              {groupedDocs.other.map((item) => (
                <Link
                  key={item.path}
                  to={`/docs/${item.path}`}
                  className={clsx('docs-nav-link', selectedPath === item.path && 'active')}
                >
                  {item.title}
                </Link>
              ))}
            </>
          ) : null}
          {groupedDocs.views.length ? (
            <>
              <p className="docs-nav-group">{t('docs.group.views')}</p>
              {groupedDocs.views.map((item) => (
                <Link
                  key={item.path}
                  to={`/docs/${item.path}`}
                  className={clsx('docs-nav-link', selectedPath === item.path && 'active')}
                >
                  {item.title}
                </Link>
              ))}
            </>
          ) : null}
        </nav>
      </aside>

      <article className="section-card docs-article">
        {error ? <p className="status-banner error">{error}</p> : null}
        {loadingDoc ? <p className="muted-text">{t('docs.status.loading')}</p> : null}
        {!loadingDoc && doc ? (
          <div
            className="markdown-body"
            dangerouslySetInnerHTML={{ __html: html }}
            onClick={handleContentClick}
          />
        ) : null}
      </article>
    </div>
  );
}
