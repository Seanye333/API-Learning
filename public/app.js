/* ── State ──────────────────────────────────────────────────────────────────── */
let apiKey = localStorage.getItem('tutorial_api_key') || '';
let serverOnline = false;
let chatMessages = [];

/* ── Init ───────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initApiKey();
  checkServer();
  initNavigation();
  initCodeTabs();
  initCopyButtons();
  setInterval(checkServer, 30000);
});

/* ── API Key management ─────────────────────────────────────────────────────── */
function initApiKey() {
  const input = document.getElementById('apiKey');
  const saveBtn = document.getElementById('saveKey');
  if (input && apiKey) input.value = apiKey;
  saveBtn?.addEventListener('click', saveApiKey);
  input?.addEventListener('keydown', e => { if (e.key === 'Enter') saveApiKey(); });
  updateKeyStatus();
}

function saveApiKey() {
  const input = document.getElementById('apiKey');
  apiKey = input?.value?.trim() || '';
  if (apiKey) {
    localStorage.setItem('tutorial_api_key', apiKey);
    setKeyStatus('ok', '✓ API key saved');
  } else {
    localStorage.removeItem('tutorial_api_key');
    setKeyStatus('warn', 'No key — using server .env');
  }
}

function updateKeyStatus() {
  if (apiKey) setKeyStatus('ok', '✓ API key loaded from storage');
  else setKeyStatus('warn', 'Enter key above (or set in .env)');
}

function setKeyStatus(type, msg) {
  const el = document.getElementById('keyStatus');
  if (el) { el.className = `key-status ${type}`; el.textContent = msg; }
}

function getHeaders() {
  const h = { 'Content-Type': 'application/json' };
  if (apiKey) h['x-api-key'] = apiKey;
  return h;
}

/* ── Server health ──────────────────────────────────────────────────────────── */
async function checkServer() {
  const dot = document.getElementById('serverDot');
  const lbl = document.getElementById('serverStatus');
  if (dot) dot.className = 'status-dot loading';
  try {
    const r = await fetch('/api/health');
    const data = await r.json();
    serverOnline = true;
    if (dot) dot.className = 'status-dot online';
    if (lbl) lbl.textContent = 'Server online' + (data.hasEnvKey ? ' · key in .env' : '');
  } catch {
    serverOnline = false;
    if (dot) dot.className = 'status-dot offline';
    if (lbl) lbl.textContent = 'Server offline';
  }
}

/* ── Navigation ─────────────────────────────────────────────────────────────── */
function initNavigation() {
  const links = document.querySelectorAll('.nav-link[data-section]');
  links.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const id = link.dataset.section;
      const section = document.getElementById(id);
      if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // Highlight active section on scroll
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        links.forEach(l => l.classList.remove('active'));
        const active = document.querySelector(`.nav-link[data-section="${entry.target.id}"]`);
        if (active) active.classList.add('active');
        updateProgress();
      }
    });
  }, { rootMargin: '-30% 0px -60% 0px', threshold: 0 });

  document.querySelectorAll('.lesson-section[id]').forEach(s => observer.observe(s));
}

function updateProgress() {
  const sections = document.querySelectorAll('.lesson-section[id]');
  const active = document.querySelector('.nav-link.active');
  if (!active || !sections.length) return;
  const ids = [...sections].map(s => s.id);
  const idx = ids.indexOf(active.dataset.section);
  const pct = idx < 0 ? 0 : Math.round(((idx + 1) / sections.length) * 100);
  const fill = document.querySelector('.progress-fill');
  const label = document.querySelector('.progress-label span:last-child');
  if (fill) fill.style.width = pct + '%';
  if (label) label.textContent = pct + '%';
}

/* ── Code tabs ──────────────────────────────────────────────────────────────── */
function initCodeTabs() {
  document.querySelectorAll('.code-tabs').forEach(tabs => {
    tabs.querySelectorAll('.code-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const lang = tab.dataset.lang;
        const block = tab.closest('.code-block');
        block.querySelectorAll('.code-tab').forEach(t => t.classList.toggle('active', t === tab));
        block.querySelectorAll('.code-panel').forEach(p => p.classList.toggle('active', p.dataset.lang === lang));
      });
    });
  });
}

/* ── Copy buttons ───────────────────────────────────────────────────────────── */
function initCopyButtons() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.closest('.code-block')?.querySelector('.code-panel.active pre code')
        || btn.closest('[data-copy-target]')
        || btn.nextElementSibling;
      const text = target?.textContent || '';
      navigator.clipboard.writeText(text.trim()).then(() => {
        btn.textContent = '✓ Copied';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1800);
      });
    });
  });
}

/* ── Generic POST helper ────────────────────────────────────────────────────── */
async function apiPost(endpoint, body) {
  const r = await fetch(endpoint, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) });
  return r.json();
}

/* ── Generic UI helpers ─────────────────────────────────────────────────────── */
function showOutput(areaId) {
  const el = document.getElementById(areaId);
  if (el) el.classList.add('visible');
}

function setBtn(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle('loading', loading);
}

function renderMeta(metaId, meta) {
  const el = document.getElementById(metaId);
  if (!el || !meta) return;
  el.innerHTML = '';
  const chips = {
    model: meta.model,
    'input tokens': meta.usage?.input_tokens,
    'output tokens': meta.usage?.output_tokens,
    'stop reason': meta.stop_reason
  };
  Object.entries(chips).forEach(([k, v]) => {
    if (v == null) return;
    el.insertAdjacentHTML('beforeend', `<span class="meta-chip"><span class="chip-key">${k}:</span><span class="chip-val">${v}</span></span>`);
  });
}

function renderError(boxId, error) {
  const el = document.getElementById(boxId);
  if (!el) return;
  el.innerHTML = `
    <div class="error-type">${error.type || 'Error'}</div>
    <div class="error-msg">${escHtml(error.message || String(error))}</div>
    ${error.retryable != null ? `<div class="error-badge">${error.retryable ? '🔄 Retryable' : '✗ Not retryable'}</div>` : ''}
  `;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function toggleJson(toggleId, panelId, data) {
  const panel = document.getElementById(panelId);
  const toggle = document.getElementById(toggleId);
  if (!panel || !toggle) return;
  if (panel.classList.toggle('visible')) {
    panel.textContent = JSON.stringify(data, null, 2);
    toggle.textContent = 'Hide JSON';
  } else {
    toggle.textContent = 'View raw JSON';
  }
}

/* ── LESSON 2: Basic Demo ───────────────────────────────────────────────────── */
window.runBasicDemo = async () => {
  const message = document.getElementById('basicMessage')?.value?.trim();
  const model = document.getElementById('basicModel')?.value || 'claude-opus-4-6';
  if (!message) return alert('Please enter a message first.');

  setBtn('basicBtn', true);
  showOutput('basicOutput');
  const box = document.getElementById('basicResult');
  if (box) { box.textContent = ''; box.className = 'output-box streaming'; }

  try {
    const data = await apiPost('/api/basic', { message, model });
    if (box) box.className = 'output-box';

    if (data.success) {
      if (box) box.textContent = data.content;
      renderMeta('basicMeta', data.meta);
      window._basicData = data;
      const toggle = document.getElementById('basicJsonToggle');
      if (toggle) toggle.style.display = 'inline';
    } else {
      if (box) box.className = '';
      renderError('basicResult', data.error);
    }
  } catch (err) {
    if (box) box.className = '';
    renderError('basicResult', { message: 'Could not reach server. Is it running? (npm start)' });
  }
  setBtn('basicBtn', false);
};

window.toggleBasicJson = () => toggleJson('basicJsonToggle', 'basicJsonPanel', window._basicData);

/* ── LESSON 3: System Prompts Demo ─────────────────────────────────────────── */
const SYSTEM_PRESETS = {
  pirate:   'You are a friendly pirate. Respond to everything in pirate speak with "Arrr!" and nautical references.',
  teacher:  'You are a patient teacher explaining concepts to a 10-year-old. Use simple language and fun analogies.',
  haiku:    'You only respond in haiku format (5-7-5 syllables). No matter what the question, answer in a haiku.',
  json:     'You always respond with valid JSON only. No prose — just a JSON object with relevant fields.',
  formal:   'You are a formal British butler. Address the user as "Sir" or "Madam" and speak in an extremely formal, Victorian manner.',
  custom:   ''
};

window.selectSystemPreset = (key) => {
  document.querySelectorAll('.btn-scenario').forEach(b => b.classList.toggle('active', b.dataset.preset === key));
  const ta = document.getElementById('systemPrompt');
  if (!ta) return;
  if (key === 'custom') ta.removeAttribute('readonly');
  else { ta.value = SYSTEM_PRESETS[key]; ta.setAttribute('readonly', true); }
};

window.runSystemDemo = async () => {
  const message = document.getElementById('systemMessage')?.value?.trim();
  const systemPrompt = document.getElementById('systemPrompt')?.value?.trim();
  if (!message) return alert('Please enter a message.');

  setBtn('systemBtn', true);
  showOutput('systemOutput');
  const box = document.getElementById('systemResult');
  if (box) { box.textContent = ''; box.className = 'output-box'; }

  try {
    const data = await apiPost('/api/system', { message, systemPrompt });
    if (data.success) {
      if (box) box.textContent = data.content;
      renderMeta('systemMeta', data.meta);
    } else {
      renderError('systemResult', data.error);
    }
  } catch {
    renderError('systemResult', { message: 'Server not reachable. Run: npm start' });
  }
  setBtn('systemBtn', false);
};

/* ── LESSON 4: Chat Demo ────────────────────────────────────────────────────── */
function renderChatMessages() {
  const container = document.getElementById('chatMessages');
  if (!container) return;
  if (chatMessages.length === 0) {
    container.innerHTML = '<p class="chat-empty">Send a message to start the conversation!</p>';
    return;
  }
  container.innerHTML = chatMessages.map(m => `
    <div class="chat-msg ${m.role}">
      <div class="msg-avatar ${m.role === 'user' ? 'user-av' : 'assistant-av'}">${m.role === 'user' ? '👤' : '🤖'}</div>
      <div class="msg-bubble">${escHtml(m.content)}</div>
    </div>
  `).join('');
  container.scrollTop = container.scrollHeight;
}

window.sendChatMessage = async () => {
  const input = document.getElementById('chatInput');
  const message = input?.value?.trim();
  if (!message) return;
  if (input) input.value = '';

  chatMessages.push({ role: 'user', content: message });
  renderChatMessages();

  const sendBtn = document.getElementById('chatSendBtn');
  if (sendBtn) sendBtn.disabled = true;

  try {
    const data = await apiPost('/api/chat', {
      messages: chatMessages,
      systemPrompt: document.getElementById('chatSystem')?.value || ''
    });
    if (data.success) {
      chatMessages.push(data.message);
    } else {
      chatMessages.push({ role: 'assistant', content: `⚠️ Error: ${data.error?.message}` });
    }
  } catch {
    chatMessages.push({ role: 'assistant', content: '⚠️ Server not reachable. Run: npm start' });
  }

  renderChatMessages();
  if (sendBtn) sendBtn.disabled = false;
  updateChatCounter();
};

window.clearChat = () => { chatMessages = []; renderChatMessages(); updateChatCounter(); };

window.chatKeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); window.sendChatMessage(); } };

function updateChatCounter() {
  const el = document.getElementById('chatCounter');
  if (el) el.textContent = `${chatMessages.length} message${chatMessages.length !== 1 ? 's' : ''}`;
}

/* ── LESSON 5: Streaming Demo ───────────────────────────────────────────────── */
window.runStreamDemo = async () => {
  const message = document.getElementById('streamMessage')?.value?.trim();
  if (!message) return alert('Enter a message first.');

  setBtn('streamBtn', true);
  showOutput('streamOutput');
  const box = document.getElementById('streamResult');
  const eventLog = document.getElementById('streamEvents');
  if (box) { box.textContent = ''; box.className = 'output-box streaming'; }
  if (eventLog) eventLog.innerHTML = '';

  function logEvent(type, detail) {
    if (!eventLog) return;
    const colors = { start: 'blue', text: 'green', done: 'teal', error: 'red' };
    const color = colors[type] || 'muted';
    eventLog.insertAdjacentHTML('beforeend',
      `<div style="color:var(--${color});font-size:12px;margin:2px 0">` +
      `<span style="opacity:.5">[${type}]</span> ${escHtml(detail)}</div>`
    );
  }

  let fullText = '';
  try {
    const response = await fetch('/api/stream', { method: 'POST', headers: getHeaders(), body: JSON.stringify({ message }) });
    if (!response.ok) { throw new Error(`HTTP ${response.status}`); }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'start') {
            logEvent('start', `message_id: ${data.id}`);
          } else if (data.type === 'text') {
            fullText += data.text;
            if (box) box.textContent = fullText;
            logEvent('text', `"${data.text.replace(/\n/g,'\\n')}"`);
          } else if (data.type === 'done') {
            if (box) box.className = 'output-box';
            logEvent('done', `input:${data.usage?.input_tokens} out:${data.usage?.output_tokens} stop:${data.stop_reason}`);
            renderMeta('streamMeta', { usage: data.usage, stop_reason: data.stop_reason });
          } else if (data.type === 'error') {
            renderError('streamResult', data.error);
          }
        } catch {}
      }
    }
  } catch (err) {
    renderError('streamResult', { message: err.message || 'Server not reachable. Run: npm start' });
  }
  setBtn('streamBtn', false);
};

/* ── LESSON 6: Tool Use Demo ────────────────────────────────────────────────── */
const TOOL_QUERIES = {
  weather:  'What is the weather in Tokyo and Paris?',
  calc:     'Calculate 15% tip on $87.50 and also compute 2^10.',
  combined: 'Check weather in London (celsius) and calculate how many Fahrenheit that is.'
};

window.setToolQuery = (key) => {
  const ta = document.getElementById('toolQuery');
  if (ta) ta.value = TOOL_QUERIES[key] || '';
  document.querySelectorAll('.btn-scenario[data-query]').forEach(b => b.classList.toggle('active', b.dataset.query === key));
};

window.runToolsDemo = async () => {
  const query = document.getElementById('toolQuery')?.value?.trim();
  if (!query) return alert('Enter a query first.');

  setBtn('toolsBtn', true);
  showOutput('toolsOutput');
  const stepsEl = document.getElementById('toolSteps');
  const answerEl = document.getElementById('toolAnswer');
  if (stepsEl) stepsEl.innerHTML = '<p style="color:var(--muted);font-size:13px">Running agentic loop...</p>';
  if (answerEl) answerEl.textContent = '';

  try {
    const data = await apiPost('/api/tools', { query });
    if (data.success) {
      if (stepsEl) {
        stepsEl.innerHTML = data.steps.map(step => {
          if (step.type === 'assistant') {
            const toolCallsHtml = (step.tool_calls || []).map(tc => `
              <div class="tool-call-box">
                <div class="tool-call-name">🔧 ${tc.name}()</div>
                <div style="margin-top:4px;font-size:11px;opacity:.8">${escHtml(JSON.stringify(tc.input))}</div>
              </div>
            `).join('');
            return `
              <div class="tool-step">
                <div class="step-header"><span class="step-badge claude">Claude</span> Step ${step.step} — ${step.stop_reason}</div>
                ${step.text ? `<p style="font-size:13.5px;color:var(--subtext);margin-bottom:8px">${escHtml(step.text)}</p>` : ''}
                ${toolCallsHtml}
              </div>`;
          } else if (step.type === 'tool_results') {
            return `
              <div class="tool-step">
                <div class="step-header"><span class="step-badge result">Tool Results</span></div>
                ${step.results.map(r => `
                  <div class="tool-result-box">
                    <strong>${r.tool_name}:</strong> ${escHtml(r.result)}
                  </div>`).join('')}
              </div>`;
          }
          return '';
        }).join('');
      }
      if (answerEl) answerEl.textContent = data.finalAnswer;
    } else {
      if (stepsEl) renderError('toolSteps', data.error);
    }
  } catch {
    if (stepsEl) stepsEl.innerHTML = '<p style="color:var(--red)">Server not reachable. Run: npm start</p>';
  }
  setBtn('toolsBtn', false);
};

/* ── LESSON 7: Error Demo ───────────────────────────────────────────────────── */
window.runErrorDemo = async (scenario) => {
  document.querySelectorAll('.btn-scenario[data-scenario]').forEach(b => b.classList.toggle('active', b.dataset.scenario === scenario));
  const box = document.getElementById('errorResult');
  const desc = document.getElementById('errorDesc');
  const areaEl = document.getElementById('errorOutput');
  if (areaEl) areaEl.classList.add('visible');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Running...</span>';

  const descriptions = {
    bad_key:      'Simulates using an invalid API key.',
    bad_model:    'Simulates requesting a model that does not exist.',
    bad_request:  'Simulates a malformed request (first message is assistant).',
    exceed_tokens:'Simulates requesting more max_tokens than the model supports.'
  };
  if (desc) desc.textContent = descriptions[scenario] || '';

  try {
    const data = await apiPost('/api/error-demo', { scenario });
    if (!data.success) {
      box.innerHTML = `
        <div class="output-error">
          <div class="error-type">HTTP ${data.error.code} — ${data.error.type}</div>
          <div class="error-msg">${escHtml(data.error.message)}</div>
          <div class="error-badge">${data.error.retryable ? '🔄 Safe to retry' : '✗ Do not retry'}</div>
        </div>`;
    } else {
      box.innerHTML = `<div style="color:var(--green)">No error occurred (unexpected).</div>`;
    }
  } catch {
    box.innerHTML = `<div style="color:var(--red)">Server not reachable. Run: npm start</div>`;
  }
};

/* ── Practice Zone ──────────────────────────────────────────────────────────── */
window.addPracticeMessage = (role) => {
  const container = document.getElementById('practiceMessages');
  if (!container) return;
  const idx = container.querySelectorAll('.practice-msg').length;
  const div = document.createElement('div');
  div.className = 'practice-msg';
  div.style.cssText = 'margin-bottom:10px';
  div.innerHTML = `
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:5px">
      <select data-role style="width:120px;padding:6px">
        <option value="user" ${role==='user'?'selected':''}>user</option>
        <option value="assistant" ${role==='assistant'?'selected':''}>assistant</option>
      </select>
      <button onclick="this.closest('.practice-msg').remove()" style="background:var(--red-dim);color:var(--red);border:1px solid var(--red);border-radius:4px;padding:5px 10px;cursor:pointer;font-size:12px">Remove</button>
    </div>
    <textarea data-content rows="2" placeholder="${role} message..."></textarea>
  `;
  container.appendChild(div);
};

window.runPractice = async () => {
  const system = document.getElementById('practiceSystem')?.value?.trim();
  const model = document.getElementById('practiceModel')?.value || 'claude-opus-4-6';
  const maxTokens = parseInt(document.getElementById('practiceTokens')?.value) || 1024;

  const msgs = [...document.querySelectorAll('.practice-msg')].map(m => ({
    role: m.querySelector('[data-role]').value,
    content: m.querySelector('[data-content]').value
  })).filter(m => m.content.trim());

  if (!msgs.length) return alert('Add at least one message.');

  setBtn('practiceBtn', true);
  showOutput('practiceOutput');
  const box = document.getElementById('practiceResult');
  const reqPanel = document.getElementById('practiceRequest');
  const resPanel = document.getElementById('practiceResponse');

  if (box) box.textContent = 'Running...';

  const body = { model, maxTokens, messages: msgs };
  if (system) body.system = system;

  if (reqPanel) {
    reqPanel.textContent = JSON.stringify({ model, max_tokens: maxTokens, ...(system ? { system } : {}), messages: msgs }, null, 2);
    reqPanel.classList.add('visible');
  }

  try {
    const data = await apiPost('/api/practice', body);
    if (data.success) {
      if (box) box.textContent = data.content;
      renderMeta('practiceMeta', data.meta);
      if (resPanel) { resPanel.textContent = JSON.stringify(data, null, 2); resPanel.classList.add('visible'); }
    } else {
      renderError('practiceResult', data.error);
    }
  } catch {
    renderError('practiceResult', { message: 'Server not reachable. Run: npm start' });
  }
  setBtn('practiceBtn', false);
};

/* ── REST Fundamentals Demo ─────────────────────────────────────────────────── */
window.restDemo = async (method, path, body, outputId) => {
  const outputEl = document.getElementById(outputId);
  if (!outputEl) return;
  outputEl.innerHTML = `<span style="color:var(--muted)">Sending ${method} ${path}...</span>`;

  const url = `https://jsonplaceholder.typicode.com${path}`;
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);

  try {
    const start = performance.now();
    const response = await fetch(url, options);
    const elapsed = (performance.now() - start).toFixed(0);
    const data = await response.json();

    const methodColors = { GET: '#a6e3a1', POST: '#89b4fa', PUT: '#fab387', PATCH: '#f9e2af', DELETE: '#f38ba8' };
    const color = methodColors[method] || '#cdd6f4';
    const statusColor = response.status < 300 ? '#a6e3a1' : response.status < 400 ? '#f9e2af' : '#f38ba8';

    let html = `<div style="margin-bottom:8px">`;
    html += `<span style="color:${color};font-weight:bold">${method}</span> `;
    html += `<span style="color:var(--subtext)">${url}</span>`;
    html += `</div>`;

    if (body) {
      html += `<div style="margin-bottom:8px;font-size:12px;color:var(--muted)">Request Body:</div>`;
      html += `<pre style="background:var(--mantle);padding:8px;border-radius:4px;margin-bottom:8px;font-size:12px;overflow-x:auto">${escHtml(JSON.stringify(body, null, 2))}</pre>`;
    }

    html += `<div style="margin-bottom:8px">`;
    html += `<span style="color:${statusColor};font-weight:bold">${response.status} ${response.statusText}</span>`;
    html += `<span style="color:var(--muted);margin-left:12px">${elapsed}ms</span>`;
    html += `</div>`;

    html += `<div style="font-size:12px;color:var(--muted);margin-bottom:4px">Response Body:</div>`;
    const jsonStr = JSON.stringify(data, null, 2);
    const truncated = jsonStr.length > 1500 ? jsonStr.slice(0, 1500) + '\n... (truncated)' : jsonStr;
    html += `<pre style="background:var(--mantle);padding:8px;border-radius:4px;font-size:12px;overflow-x:auto;max-height:300px">${escHtml(truncated)}</pre>`;

    outputEl.innerHTML = html;
  } catch (err) {
    outputEl.innerHTML = `<span style="color:var(--red)">Error: ${escHtml(err.message)}</span>`;
  }
};

/* ── LESSON 8: Autodesk ACC Build Demos ─────────────────────────────────────── */
let accToken = '';
let accProjectId = '';

// Save APS credentials to localStorage
window.saveApsCredentials = () => {
  const id = document.getElementById('apsClientId')?.value?.trim();
  const secret = document.getElementById('apsClientSecret')?.value?.trim();
  if (id) localStorage.setItem('aps_client_id', id);
  if (secret) localStorage.setItem('aps_client_secret', secret);
  const status = document.getElementById('apsCredStatus');
  if (status) status.innerHTML = id && secret
    ? '<span style="color:var(--green)">✓ Credentials saved</span>'
    : '<span style="color:var(--yellow)">⚠ Enter both Client ID and Secret</span>';
};

// Load saved APS credentials on init
document.addEventListener('DOMContentLoaded', () => {
  const savedId = localStorage.getItem('aps_client_id');
  const savedSecret = localStorage.getItem('aps_client_secret');
  if (savedId) { const el = document.getElementById('apsClientId'); if (el) el.value = savedId; }
  if (savedSecret) { const el = document.getElementById('apsClientSecret'); if (el) el.value = savedSecret; }
  if (savedId && savedSecret) {
    const status = document.getElementById('apsCredStatus');
    if (status) status.innerHTML = '<span style="color:var(--green)">✓ Credentials loaded from storage</span>';
  }
});

// Helper: get APS headers for proxy requests
function getAccHeaders() {
  const h = { 'Content-Type': 'application/json' };
  const id = document.getElementById('apsClientId')?.value?.trim() || localStorage.getItem('aps_client_id') || '';
  const secret = document.getElementById('apsClientSecret')?.value?.trim() || localStorage.getItem('aps_client_secret') || '';
  if (id) h['x-aps-client-id'] = id;
  if (secret) h['x-aps-client-secret'] = secret;
  return h;
}

// Demo 1: Get OAuth token
window.runAccAuth = async () => {
  setBtn('accTokenBtn', true);
  showOutput('accTokenOutput');
  const box = document.getElementById('accTokenResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Authenticating...</span>';

  try {
    const resp = await fetch('/api/acc/token', { method: 'POST', headers: getAccHeaders(), body: JSON.stringify({}) });
    const data = await resp.json();

    if (data.success && data.access_token) {
      accToken = data.access_token;
      box.innerHTML = `
        <div style="color:var(--green);font-weight:bold;margin-bottom:8px">✅ Token received!</div>
        <div style="font-size:13px"><strong>Token:</strong> ${escHtml(accToken.substring(0, 50))}...</div>
        <div style="font-size:13px"><strong>Expires in:</strong> ${data.expires_in}s (${Math.floor(data.expires_in / 60)} min)</div>
        <div style="font-size:13px"><strong>Type:</strong> ${data.token_type || 'Bearer'}</div>
      `;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Auth failed: ${escHtml(JSON.stringify(data.error || data))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}. Is the server running? (npm start)</div>`;
  }
  setBtn('accTokenBtn', false);
};

// Demo 2: List projects
window.runAccProjects = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  setBtn('accProjectsBtn', true);
  showOutput('accProjectsOutput');
  const box = document.getElementById('accProjectsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Fetching projects...</span>';

  try {
    const resp = await fetch('/api/acc/proxy/construction/admin/v1/projects', {
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();

    if (resp.ok && data.results) {
      const results = data.results;
      accProjectId = results[0]?.id || '';
      let html = `<div style="color:var(--green);margin-bottom:8px">✅ Found ${data.pagination?.totalResults ?? results.length} project(s)</div>`;
      results.slice(0, 8).forEach((p, i) => {
        html += `<div style="padding:6px 0;border-bottom:1px solid var(--surface1)">
          <strong>${i+1}. ${escHtml(p.name || 'Unnamed')}</strong>
          <div style="font-size:12px;color:var(--muted)">ID: ${escHtml(p.id)} | Status: ${escHtml(p.status || 'N/A')}</div>
        </div>`;
      });
      box.innerHTML = html;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
  setBtn('accProjectsBtn', false);
};

// Demo 3: List issues
window.runAccIssues = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2) to get a project ID.');
  setBtn('accIssuesBtn', true);
  showOutput('accIssuesOutput');
  const box = document.getElementById('accIssuesResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Fetching issues...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/issues/v1/projects/${accProjectId}/issues`, {
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();

    if (resp.ok && data.results) {
      const results = data.results;
      let html = `<div style="color:var(--green);margin-bottom:8px">✅ Found ${data.pagination?.totalResults ?? results.length} issue(s)</div>`;
      if (results.length === 0) html += '<div style="color:var(--muted)">No issues found in this project.</div>';
      results.slice(0, 10).forEach((iss, i) => {
        html += `<div style="padding:6px 0;border-bottom:1px solid var(--surface1)">
          <strong>${i+1}. ${escHtml(iss.title || 'Untitled')}</strong>
          <div style="font-size:12px;color:var(--muted)">Status: ${escHtml(iss.status || 'N/A')} | Type: ${escHtml(iss.issueType || 'N/A')}</div>
        </div>`;
      });
      box.innerHTML = html;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
  setBtn('accIssuesBtn', false);
};

// Demo 4: Create issue
window.runAccCreateIssue = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2) to get a project ID.');
  const title = document.getElementById('accIssueTitle')?.value?.trim();
  if (!title) return alert('Enter an issue title.');

  setBtn('accCreateBtn', true);
  showOutput('accCreateOutput');
  const box = document.getElementById('accCreateResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Creating issue...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/issues/v1/projects/${accProjectId}/issues`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description: 'Created by API tutorial.', status: 'open' })
    });
    const data = await resp.json();

    if (resp.ok) {
      box.innerHTML = `
        <div style="color:var(--green);font-weight:bold;margin-bottom:8px">✅ Issue created!</div>
        <div style="font-size:13px"><strong>ID:</strong> ${escHtml(data.id || 'N/A')}</div>
        <div style="font-size:13px"><strong>Title:</strong> ${escHtml(data.title || 'N/A')}</div>
        <div style="font-size:13px"><strong>Status:</strong> ${escHtml(data.status || 'N/A')}</div>
      `;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
  setBtn('accCreateBtn', false);
};

/* ── ACC: Submittals Demos ──────────────────────────────────────────────────── */

window.runAccSubmittals = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2).');
  showOutput('accSubmittalsOutput');
  const box = document.getElementById('accSubmittalsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Fetching submittals...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/submittals/v2/projects/${accProjectId}/items`, {
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();
    if (resp.ok && data.results) {
      let html = `<div style="color:var(--green);margin-bottom:8px">✅ Found ${data.pagination?.totalResults ?? data.results.length} submittal(s)</div>`;
      if (data.results.length === 0) html += '<div style="color:var(--muted)">No submittals found.</div>';
      data.results.slice(0, 10).forEach((s, i) => {
        html += `<div style="padding:4px 0;border-bottom:1px solid var(--surface1)">
          <strong>${i+1}. ${escHtml(s.title || 'Untitled')}</strong>
          <span style="font-size:12px;color:var(--muted)"> — ${escHtml(s.status || 'N/A')}</span>
        </div>`;
      });
      box.innerHTML = html;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccCreateSubmittal = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2).');
  showOutput('accSubmittalsOutput');
  const box = document.getElementById('accSubmittalsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Creating submittal...</span>';

  try {
    // Step 1: Create draft
    const createResp = await fetch(`/api/acc/proxy/construction/submittals/v2/projects/${accProjectId}/items`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Tutorial Test Submittal', description: 'Created by tutorial.', status: 'draft' })
    });
    const createData = await createResp.json();

    if (!createResp.ok) {
      box.innerHTML = `<div style="color:var(--red)">✗ Create failed (${createResp.status}): ${escHtml(JSON.stringify(createData).substring(0, 300))}</div>`;
      return;
    }

    let html = `<div style="color:var(--green);margin-bottom:8px">✅ Submittal created (draft)</div>
      <div style="font-size:13px">ID: ${escHtml(createData.id || 'N/A')} | Status: ${escHtml(createData.status || 'draft')}</div>`;

    // Step 2: Transition to submitted
    if (createData.id) {
      const transResp = await fetch(`/api/acc/proxy/construction/submittals/v2/projects/${accProjectId}/items/${createData.id}:transition`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ toState: 'submitted' })
      });
      if (transResp.ok) {
        html += `<div style="color:var(--green);margin-top:8px">✅ Submitted for review!</div>`;
      } else {
        html += `<div style="color:var(--yellow);margin-top:8px">⚠ Created but transition failed (${transResp.status})</div>`;
      }
    }

    box.innerHTML = html;
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

/* ── ACC: Assets Demos ─────────────────────────────────────────────────────── */
let accLastAssetId = '';
let accCategoryId = '';

window.runAccAssetCategories = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2).');
  showOutput('accAssetsOutput');
  const box = document.getElementById('accAssetsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Fetching categories...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/assets/v2/projects/${accProjectId}/categories`, {
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();
    const cats = Array.isArray(data) ? data : (data.results || []);
    if (resp.ok && cats.length > 0) {
      accCategoryId = cats[0].id || '';
      let html = `<div style="color:var(--green);margin-bottom:8px">✅ Found ${cats.length} categor(ies)</div>`;
      cats.slice(0, 10).forEach((c, i) => {
        html += `<div style="padding:3px 0;font-size:13px">${i+1}. ${escHtml(c.name || 'Unnamed')} <span style="color:var(--muted)">(${escHtml(c.id)})</span></div>`;
      });
      box.innerHTML = html;
    } else {
      box.innerHTML = `<div style="color:var(--yellow)">No categories found or failed (${resp.status})</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccListAssets = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2).');
  showOutput('accAssetsOutput');
  const box = document.getElementById('accAssetsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Fetching assets...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/assets/v2/projects/${accProjectId}/assets:search`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await resp.json();
    if (resp.ok) {
      const results = data.results || [];
      let html = `<div style="color:var(--green);margin-bottom:8px">✅ Found ${results.length} asset(s)</div>`;
      results.slice(0, 10).forEach((a, i) => {
        html += `<div style="padding:4px 0;border-bottom:1px solid var(--surface1)">
          <strong>${i+1}. ${escHtml(a.displayName || 'Unnamed')}</strong>
          <div style="font-size:12px;color:var(--muted)">ID: ${escHtml(a.id)}</div>
        </div>`;
      });
      box.innerHTML = html;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status})</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccCreateAsset = async () => {
  if (!accToken) return alert('Get a token first (Demo 1).');
  if (!accProjectId) return alert('List projects first (Demo 2).');
  const name = document.getElementById('accAssetName')?.value?.trim() || 'Tutorial Asset';
  showOutput('accAssetsOutput');
  const box = document.getElementById('accAssetsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Creating asset...</span>';

  try {
    const item = { displayName: name, description: 'Created by API tutorial.' };
    if (accCategoryId) item.categoryId = accCategoryId;
    const resp = await fetch(`/api/acc/proxy/construction/assets/v2/projects/${accProjectId}/assets:batch-create`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: [item] })
    });
    const data = await resp.json();
    if (resp.ok) {
      const results = data.results || (data.id ? [data] : []);
      accLastAssetId = results[0]?.id || '';
      box.innerHTML = `<div style="color:var(--green);font-weight:bold">✅ Asset created!</div>
        <div style="font-size:13px">ID: ${escHtml(accLastAssetId)}</div>
        <div style="font-size:13px">Name: ${escHtml(results[0]?.displayName || name)}</div>`;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccUpdateAsset = async () => {
  if (!accToken) return alert('Get a token first.');
  if (!accLastAssetId) return alert('Create an asset first.');
  showOutput('accAssetsOutput');
  const box = document.getElementById('accAssetsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Updating asset...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/assets/v2/projects/${accProjectId}/assets:batch-patch`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: [{ id: accLastAssetId, displayName: 'Updated Asset (Tutorial)' }] })
    });
    box.innerHTML = resp.ok
      ? '<div style="color:var(--green);font-weight:bold">✅ Asset updated!</div>'
      : `<div style="color:var(--red)">✗ Failed (${resp.status})</div>`;
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccDeleteAsset = async () => {
  if (!accToken) return alert('Get a token first.');
  if (!accLastAssetId) return alert('Create an asset first.');
  showOutput('accAssetsOutput');
  const box = document.getElementById('accAssetsResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Deleting asset...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/assets/v2/projects/${accProjectId}/assets:batch-delete`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [accLastAssetId] })
    });
    if (resp.ok || resp.status === 204) {
      accLastAssetId = '';
      box.innerHTML = '<div style="color:var(--green);font-weight:bold">✅ Asset deleted!</div>';
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status})</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

/* ── ACC: Revit + Assets Demos ─────────────────────────────────────────────── */

window.runAccRevitManifest = async () => {
  if (!accToken) return alert('Get a token first.');
  const urn = document.getElementById('accRevitUrn')?.value?.trim();
  if (!urn) return alert('Enter a base64-encoded URN of a translated Revit file.');
  showOutput('accRevitOutput');
  const box = document.getElementById('accRevitResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Checking translation status...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/modelderivative/v2/designdata/${encodeURIComponent(urn)}/manifest`, {
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();
    if (resp.ok) {
      const statusColor = data.status === 'success' ? 'var(--green)' : data.status === 'failed' ? 'var(--red)' : 'var(--yellow)';
      box.innerHTML = `<div style="color:${statusColor};font-weight:bold;margin-bottom:8px">Status: ${escHtml(data.status || 'unknown')}</div>
        <div style="font-size:13px">Progress: ${escHtml(data.progress || 'N/A')}</div>
        <pre style="background:var(--mantle);padding:8px;border-radius:4px;font-size:12px;max-height:200px;overflow:auto">${escHtml(JSON.stringify(data, null, 2).substring(0, 1000))}</pre>`;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccRevitProperties = async () => {
  if (!accToken) return alert('Get a token first.');
  const urn = document.getElementById('accRevitUrn')?.value?.trim();
  if (!urn) return alert('Enter a URN first.');
  showOutput('accRevitOutput');
  const box = document.getElementById('accRevitResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Fetching metadata...</span>';

  try {
    // Step 1: Get GUIDs
    const metaResp = await fetch(`/api/acc/proxy/modelderivative/v2/designdata/${encodeURIComponent(urn)}/metadata`, {
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
    });
    const metaData = await metaResp.json();

    if (!metaResp.ok) {
      box.innerHTML = `<div style="color:var(--red)">✗ Metadata failed (${metaResp.status})</div>`;
      return;
    }

    const guids = metaData?.data?.metadata || [];
    let html = `<div style="color:var(--green);margin-bottom:8px">✅ Found ${guids.length} model view(s)</div>`;

    // Step 2: Get properties from first GUID
    if (guids.length > 0) {
      const guid = guids[0].guid;
      html += `<div style="font-size:13px;margin-bottom:8px">Fetching properties for GUID: ${escHtml(guid)}...</div>`;

      const propsResp = await fetch(`/api/acc/proxy/modelderivative/v2/designdata/${encodeURIComponent(urn)}/metadata/${guid}/properties?limit=5`, {
        headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' }
      });
      const propsData = await propsResp.json();

      if (propsResp.ok && propsData?.data?.collection) {
        const elems = propsData.data.collection;
        html += `<div style="color:var(--green);margin-bottom:8px">✅ Found ${elems.length} element(s) (showing up to 5)</div>`;
        elems.slice(0, 5).forEach((el, i) => {
          html += `<div style="padding:6px 0;border-bottom:1px solid var(--surface1)">
            <strong>${i+1}. ${escHtml(el.name || 'Unnamed')}</strong>
            <div style="font-size:12px;color:var(--muted)">externalId: ${escHtml(el.externalId || 'N/A')}</div>
          </div>`;
        });
      }
    }

    box.innerHTML = html;
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

window.runAccRevitLinkAsset = async () => {
  if (!accToken) return alert('Get a token first.');
  if (!accProjectId) return alert('List projects first (Demo 2).');
  showOutput('accRevitOutput');
  const box = document.getElementById('accRevitResult');
  if (box) box.innerHTML = '<span style="color:var(--muted)">Creating Revit-linked asset...</span>';

  try {
    const resp = await fetch(`/api/acc/proxy/construction/assets/v2/projects/${accProjectId}/assets:batch-create`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: [{
          displayName: 'Revit-Linked Asset (Tutorial Demo)',
          description: 'Linked to Revit externalId via custom attribute',
          clientAssetId: 'tutorial-revit-' + Date.now()
        }]
      })
    });
    const data = await resp.json();
    if (resp.ok) {
      const results = data.results || (data.id ? [data] : []);
      box.innerHTML = `<div style="color:var(--green);font-weight:bold;margin-bottom:8px">✅ Revit-linked asset created!</div>
        <div style="font-size:13px">ID: ${escHtml(results[0]?.id || 'N/A')}</div>
        <div style="font-size:13px;margin-top:8px;color:var(--muted)">In production, you'd add custom attributes with the Revit externalId to link this asset to a specific BIM element.</div>`;
    } else {
      box.innerHTML = `<div style="color:var(--red)">✗ Failed (${resp.status}): ${escHtml(JSON.stringify(data).substring(0, 300))}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red)">✗ Error: ${escHtml(err.message)}</div>`;
  }
};

/* ── Mobile menu ────────────────────────────────────────────────────────────── */
window.toggleMenu = () => document.querySelector('.sidebar')?.classList.toggle('open');
