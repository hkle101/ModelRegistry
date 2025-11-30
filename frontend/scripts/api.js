const API_BASE = 'http://localhost:8000';

async function apiCall(method, path, body = null, extraHeaders = {}) {
  const headers = { 'Content-Type': 'application/json', ...extraHeaders };
  const init = { method, headers };
  if (body !== null) init.body = JSON.stringify(body);
  const started = performance.now();
  let status = 0;
  let data = null;
  let text = '';
  let requestTs = null;
  let responseTs = null;
  try {
    const res = await fetch(API_BASE + path, init);
    status = res.status;
    requestTs = res.headers.get('x-request-timestamp');
    responseTs = res.headers.get('x-response-timestamp');
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      try { data = await res.json(); } catch { text = await res.text(); }
    } else {
      text = await res.text();
    }
  } catch (e) {
    text = 'Network error: ' + e.message;
  }
  const pretty = data ? JSON.stringify(data, null, 2) : text;
  return { status, data, pretty, requestTs, responseTs, ms: (performance.now() - started).toFixed(1) };
}

// Expose globally
window.apiCall = apiCall;