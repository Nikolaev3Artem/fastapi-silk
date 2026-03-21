from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from .storage import recent_queries

router = APIRouter(prefix="/_silk", tags=["fastapi-silk"])


@router.get("/api/recent")
async def api_recent() -> JSONResponse:
    """Return the recent per-request query summaries as JSON."""
    # convert deque to list for JSON serialization
    return JSONResponse({"recent": list(recent_queries)})


@router.get("/", response_class=HTMLResponse)
async def ui_index() -> HTMLResponse:
    """A tiny frontend that polls `/ _silk/api/recent` and displays recent queries."""
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>FastAPI Silk — Recent Queries</title>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
        padding: 24px; 
        background: #0f0f0f;
        color: #e0e0e0;
      }
      h1 { 
        margin-bottom: 24px; 
        font-size: 28px;
        font-weight: 600;
      }
      #list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
      }
      .entry { 
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 16px;
        transition: all 0.2s ease;
      }
      .entry:hover {
        border-color: #555;
        background: #222;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      }
      .entry-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
      }
      .entry-time {
        font-size: 12px;
        color: #888;
      }
      .entry-method {
        font-weight: 600;
        font-size: 11px;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
      }
      .method-get {
        background: rgba(52, 152, 219, 0.2);
        color: #3498db;
      }
      .method-post {
        background: rgba(46, 204, 113, 0.2);
        color: #2ecc71;
      }
      .method-put {
        background: rgba(155, 89, 182, 0.2);
        color: #9b59b6;
      }
      .method-delete {
        background: rgba(231, 76, 60, 0.2);
        color: #e74c3c;
      }
      .entry-path {
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #aaa;
        margin: 8px 0;
        word-break: break-all;
      }
      .entry-stats {
        display: flex;
        gap: 12px;
        margin: 12px 0;
        padding-top: 12px;
        border-top: 1px solid #333;
        font-size: 12px;
      }
      .stat {
        display: flex;
        flex-direction: column;
      }
      .stat-label {
        color: #666;
        font-size: 10px;
        text-transform: uppercase;
        margin-bottom: 2px;
      }
      .stat-value {
        font-weight: 600;
        color: #e0e0e0;
      }
      .stat-value.slow {
        color: #e74c3c;
      }
      .queries-count {
        font-size: 11px;
        color: #666;
        margin-top: 8px;
      }
      .no-queries {
        grid-column: 1 / -1;
        text-align: center;
        padding: 40px;
        color: #666;
      }
      .error {
        grid-column: 1 / -1;
        background: rgba(231, 76, 60, 0.1);
        border: 1px solid rgba(231, 76, 60, 0.3);
        color: #e74c3c;
        padding: 16px;
        border-radius: 8px;
      }
    </style>
  </head>
  <body>
    <h1>Recent DB Queries</h1>
    <div id="list">Loading…</div>
    <script>
      let lastRecent = [];
      let isRendering = false;

      function getMethodClass(method) {
        const m = method.toUpperCase();
        if (m === 'GET') return 'method-get';
        if (m === 'POST') return 'method-post';
        if (m === 'PUT') return 'method-put';
        if (m === 'DELETE') return 'method-delete';
        return '';
      }

      function formatTime(seconds) {
        if (seconds < 0.001) return (seconds * 1000000).toFixed(0) + 'µs';
        if (seconds < 1) return (seconds * 1000).toFixed(1) + 'ms';
        return seconds.toFixed(2) + 's';
      }

      function renderEntry(r) {
        const dbTimeMs = r.db_time;
        const totalTimeMs = r.total_time;
        const isSlow = dbTimeMs > 0.1;
        const methodClass = getMethodClass(r.method);
        
        return `<div class="entry">
          <div class="entry-header">
            <div class="entry-time">${new Date(r.time*1000).toLocaleString()}</div>
            <span class="entry-method ${methodClass}">${r.method}</span>
          </div>
          <div class="entry-path">${escapeHtml(r.path)}</div>
          <div class="entry-stats">
            <div class="stat">
              <div class="stat-label">DB Time</div>
              <div class="stat-value ${isSlow ? 'slow' : ''}">${formatTime(dbTimeMs)}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Total</div>
              <div class="stat-value">${formatTime(totalTimeMs)}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Queries</div>
              <div class="stat-value">${(r.queries || []).length}</div>
            </div>
          </div>
          ${(r.queries || []).length > 0 ? `<div class="queries-count">${(r.queries || []).length} ${(r.queries || []).length === 1 ? 'query' : 'queries'}</div>` : ''}
        </div>`;
      }

      function recentChanged(newRecent) {
        if (lastRecent.length !== newRecent.length) return true;
        if (lastRecent.length > 0) {
          const lastItem = lastRecent[lastRecent.length - 1];
          const newItem = newRecent[newRecent.length - 1];
          return lastItem.time !== newItem.time || lastItem.path !== newItem.path;
        }
        return false;
      }

      async function fetchRecent() {
        if (isRendering) return;
        isRendering = true;
        
        try {
          const res = await fetch("/_silk/api/recent?t=" + Date.now());
          let data;
          try {
            data = await res.json();
          } catch (parseErr) {
            const text = await res.text();
            console.error("[silk] JSON parse error", parseErr, text);
            document.getElementById('list').innerHTML = '<div class="error">Error parsing JSON (see console)</div>';
            isRendering = false;
            return;
          }

          if (!data || !Array.isArray(data.recent) || data.recent.length === 0) {
            if (lastRecent.length !== 0) {
              document.getElementById('list').innerHTML = '<div class="no-queries">No recent queries recorded.</div>';
              lastRecent = [];
            }
            isRendering = false;
            return;
          }

          if (recentChanged(data.recent)) {
            lastRecent = data.recent;
            const container = document.getElementById('list');
            container.innerHTML = data.recent.map(renderEntry).join('');
            console.log('[silk] rendered', data.recent.length, 'queries');
          }
        } catch (err) {
          console.error('[silk] fetch error', err);
          document.getElementById('list').innerHTML = '<div class="error">Error: ' + escapeHtml(err.toString()) + '</div>';
        }
        
        isRendering = false;
      }

      function escapeHtml(s) { return s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;') }

      fetchRecent();
      setInterval(fetchRecent, 2000);
    </script>
  </body>
</html>
"""
    return HTMLResponse(html)
