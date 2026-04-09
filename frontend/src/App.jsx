import React, { useState } from 'react';
import { Search, Loader2, BookOpen, GitBranch, RefreshCw, ChevronRight, FileCode, CheckCircle2, Download, ChevronDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const PRODUCTION_API_URL = 'https://memograph-production.up.railway.app';

function getApiUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL?.trim();

  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, '');
  }

  const hostname = window.location.hostname;
  const isLocalHost = hostname === 'localhost' || hostname === '127.0.0.1';

  return isLocalHost ? 'http://localhost:8000' : PRODUCTION_API_URL;
}

function App() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('formatted');
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  const handleSubmit = async (e, forcedQuery = null) => {
    if (e) e.preventDefault();
    const activeQuery = forcedQuery || query;
    if (!activeQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const apiUrl = getApiUrl();
      const res = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: activeQuery }),
      });

      if (!res.ok) throw new Error('API server is not responding. Please ensure the backend is running.');
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRelatedClick = (topic) => {
    setQuery(topic);
    handleSubmit(null, topic);
  };

  const downloadFile = (format) => {
    if (!response) return;

    let content = '';
    let filename = '';
    const timestamp = new Date().toISOString().slice(0, 10);

    switch (format) {
      case 'markdown':
        content = response.content;
        filename = `knowledge_${timestamp}.md`;
        break;
      case 'json':
        content = JSON.stringify(response, null, 2);
        filename = `knowledge_${timestamp}.json`;
        break;
      case 'text':
        content = response.content.replace(/[#*_`\[\]()]/g, '').replace(/\n\n+/g, '\n\n');
        filename = `knowledge_${timestamp}.txt`;
        break;
      default:
        return;
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    setShowDownloadMenu(false);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="logo-section">
          <div className="logo-icon">
            <GitBranch className="text-[#8ff5ff]" size={32} />
          </div>
          <div>
            <h1 className="logo-title">MemoGraph</h1>
            <div className="status-indicator">
              <div className="status-dot"></div>
              Evolution Active
            </div>
          </div>
        </div>
        <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-dim)', textTransform: 'uppercase' }}>System Node</div>
          <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--primary)' }}>agent-graph-v1</div>
        </div>
      </header>

      {/* Search Input Section */}
      <section className="search-section">
        <form onSubmit={handleSubmit} className="search-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a topic (e.g., Explain Transformers)"
            disabled={isLoading}
            className="search-input"
          />
          <Search className="search-icon" size={24} />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="submit-button"
          >
            {isLoading ? <Loader2 className="spinner" size={20} /> : 'Analyze & Build'}
          </button>
        </form>
      </section>

      {isLoading && (
        <div className="loading-section">
          <RefreshCw className="spinner" size={48} color="var(--primary)" style={{ opacity: 0.2 }} />
          <p style={{ color: 'var(--text-dim)', fontWeight: 600 }}>Orchestrating Knowledge Base...</p>
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(255, 113, 108, 0.1)', border: '1px solid rgba(255, 113, 108, 0.2)', padding: '1rem', borderRadius: '12px', color: 'var(--error)', maxWidth: '600px', margin: '0 auto' }}>
          <strong>System Error:</strong> {error}
        </div>
      )}

      {response && (
        <div className="dashboard-grid animate-fade">
          {/* Result Column */}
          <div className="left-panel">
            {/* Banner */}
            <div className="banner">
              <CheckCircle2 color="var(--primary)" size={24} />
              <div className="banner-info">
                <div className="banner-title">Knowledge Evolution Success</div>
                <div className="banner-subtitle">{response.file_path}</div>
              </div>
              <div className="status-pill">{response.status}</div>
            </div>

            {/* Summary Card */}
            <div className="card">
              <div className="card-title">
                <BookOpen size={16} /> Summary
              </div>
              <div className="card-content">
                {response.summary || response.answer}
              </div>
            </div>

            {/* Key Concepts */}
            <div className="card">
              <div className="card-title">
                <GitBranch size={16} /> Key Concepts
              </div>
              <ul className="concept-list">
                {response.key_concepts.map((concept, i) => (
                  <li key={i} className="concept-item">
                    <ChevronRight className="concept-bullet" size={16} />
                    {concept}
                  </li>
                ))}
              </ul>
            </div>

            {/* Related Topics */}
            <div className="card">
              <div className="card-title">Related Evolution</div>
              <div className="pill-grid">
                {response.related_topics.map((topic, i) => (
                  <button
                    key={i}
                    onClick={() => handleRelatedClick(topic)}
                    className="pill-btn"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Viewer Column */}
          <div className="right-panel">
            <div className="card viewer-panel">
              <div className="viewer-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: 800 }}>
                  <FileCode size={16} color="var(--primary)" />
                  KNOWLEDGE FILE VIEW
                </div>
                <div className="viewer-actions">
                  <div className="toggle-group">
                    <button
                      onClick={() => setViewMode('formatted')}
                      className={`toggle-btn ${viewMode === 'formatted' ? 'active' : ''}`}
                    >
                      PREVIEW
                    </button>
                    <button
                      onClick={() => setViewMode('raw')}
                      className={`toggle-btn ${viewMode === 'raw' ? 'active' : ''}`}
                    >
                      RAW
                    </button>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <button
                      onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                      className="download-btn"
                    >
                      <Download size={16} />
                      DOWNLOAD
                      <ChevronDown size={14} style={{ marginLeft: '4px' }} />
                    </button>
                    {showDownloadMenu && (
                      <div className="download-menu">
                        <button
                          onClick={() => downloadFile('markdown')}
                          className="download-menu-item"
                        >
                          📄 Download as Markdown
                        </button>
                        <button
                          onClick={() => downloadFile('json')}
                          className="download-menu-item"
                        >
                          {'{}'} Download as JSON
                        </button>
                        <button
                          onClick={() => downloadFile('text')}
                          className="download-menu-item"
                        >
                          📝 Download as Text
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="viewer-content">
                {viewMode === 'formatted' ? (
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {response.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                    {response.content}
                  </pre>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {!response && !isLoading && (
         <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '100px 0', opacity: 0.1 }}>
            <GitBranch size={96} />
            <p style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.2em', marginTop: '1rem' }}>System Standby</p>
         </div>
      )}
    </div>
  );
}

export default App;
