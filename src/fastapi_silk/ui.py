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
      body { font-family: Arial, sans-serif; padding: 16px; }
      pre { background:#f6f8fa; padding:8px; border-radius:6px }
      .entry { margin-bottom: 16px; }
    </style>
  </head>
  <body>
    <h1>Recent DB queries</h1>
    <div id="list">Loading…</div>
    <script>
      async function fetchRecent() {
        try {
          const res = await fetch("/_silk/api/recent");
          const data = await res.json();
          const container = document.getElementById('list');
          if (!data.recent.length) {
            container.innerHTML = '<p>No recent queries recorded.</p>';
            return;
          }
          container.innerHTML = data.recent.map(r => {
            const qs = (r.queries || []).map(q => `<pre>${q.duration}s → ${escapeHtml(q.sql || '')}</pre>`).join('\n');
            return `<div class="entry"><strong>${new Date(r.time*1000).toLocaleString()}</strong> ` +
                   `<em>${r.method} ${r.path}</em>` +
                   `<div>DB time: ${r.db_time}s — Total: ${r.total_time}s</div>` +
                   qs + `</div>`;
          }).join('\n');
        } catch (err) {
          document.getElementById('list').innerText = 'Error: ' + err;
        }
      }

      function escapeHtml(s) { return s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;') }

      fetchRecent();
      setInterval(fetchRecent, 2000);
    </script>
  </body>
</html>
"""
    return HTMLResponse(html)
