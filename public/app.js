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

/* ── Mobile menu ────────────────────────────────────────────────────────────── */
window.toggleMenu = () => document.querySelector('.sidebar')?.classList.toggle('open');
