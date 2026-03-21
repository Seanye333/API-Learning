import express from 'express';
import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
app.use(express.json());
app.use(express.static(join(__dirname, 'public')));

// ─── Helper: build Anthropic client from request or env ───────────────────────
function getClient(req) {
  const apiKey = req.headers['x-api-key'] || process.env.ANTHROPIC_API_KEY;
  if (!apiKey || apiKey === 'sk-ant-your-key-here') {
    throw Object.assign(new Error('No API key provided. Set ANTHROPIC_API_KEY in .env or enter one in the tutorial UI.'), { status: 401 });
  }
  return new Anthropic({ apiKey });
}

// ─── Helper: format Anthropic errors for the tutorial ─────────────────────────
function formatError(error) {
  if (error instanceof Anthropic.AuthenticationError) {
    return { code: 401, type: 'AuthenticationError', message: 'Invalid API key. Check your ANTHROPIC_API_KEY.', retryable: false };
  }
  if (error instanceof Anthropic.PermissionDeniedError) {
    return { code: 403, type: 'PermissionDeniedError', message: 'Your API key does not have access to this resource.', retryable: false };
  }
  if (error instanceof Anthropic.NotFoundError) {
    return { code: 404, type: 'NotFoundError', message: 'Model or endpoint not found. Check the model ID.', retryable: false };
  }
  if (error instanceof Anthropic.BadRequestError) {
    return { code: 400, type: 'BadRequestError', message: error.message, retryable: false };
  }
  if (error instanceof Anthropic.RateLimitError) {
    return { code: 429, type: 'RateLimitError', message: 'Too many requests. Retry after a short delay.', retryable: true };
  }
  if (error instanceof Anthropic.APIConnectionError) {
    return { code: 0, type: 'APIConnectionError', message: 'Network error. Check your internet connection.', retryable: true };
  }
  if (error instanceof Anthropic.APIStatusError) {
    return { code: error.status, type: 'APIStatusError', message: error.message, retryable: error.status >= 500 };
  }
  return { code: error.status || 500, type: 'Error', message: error.message, retryable: false };
}

// ─── Health check ──────────────────────────────────────────────────────────────
app.get('/api/health', (req, res) => {
  res.json({ ok: true, hasEnvKey: !!(process.env.ANTHROPIC_API_KEY && process.env.ANTHROPIC_API_KEY !== 'sk-ant-your-key-here') });
});

// ─── Lesson 2: Basic message ───────────────────────────────────────────────────
app.post('/api/basic', async (req, res) => {
  try {
    const client = getClient(req);
    const { message, model = 'claude-opus-4-6', maxTokens = 1024 } = req.body;

    if (!message?.trim()) return res.status(400).json({ success: false, error: { message: 'message is required', type: 'BadRequestError' } });

    const response = await client.messages.create({
      model,
      max_tokens: maxTokens,
      messages: [{ role: 'user', content: message }]
    });

    res.json({
      success: true,
      content: response.content[0].text,
      meta: {
        id: response.id,
        model: response.model,
        stop_reason: response.stop_reason,
        usage: response.usage
      },
      request: { model, max_tokens: maxTokens, messages: [{ role: 'user', content: message }] }
    });
  } catch (err) {
    const e = formatError(err);
    res.status(e.code || 500).json({ success: false, error: e });
  }
});

// ─── Lesson 3: System prompts ──────────────────────────────────────────────────
app.post('/api/system', async (req, res) => {
  try {
    const client = getClient(req);
    const { message, systemPrompt } = req.body;

    if (!message?.trim()) return res.status(400).json({ success: false, error: { message: 'message is required' } });

    const response = await client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 1024,
      system: systemPrompt || '',
      messages: [{ role: 'user', content: message }]
    });

    res.json({
      success: true,
      content: response.content[0].text,
      meta: { usage: response.usage, stop_reason: response.stop_reason },
      request: { model: 'claude-opus-4-6', system: systemPrompt, messages: [{ role: 'user', content: message }] }
    });
  } catch (err) {
    const e = formatError(err);
    res.status(e.code || 500).json({ success: false, error: e });
  }
});

// ─── Lesson 4: Multi-turn chat ─────────────────────────────────────────────────
app.post('/api/chat', async (req, res) => {
  try {
    const client = getClient(req);
    const { messages, systemPrompt } = req.body;

    if (!messages?.length) return res.status(400).json({ success: false, error: { message: 'messages array is required' } });

    const response = await client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 1024,
      ...(systemPrompt ? { system: systemPrompt } : {}),
      messages
    });

    res.json({
      success: true,
      message: { role: 'assistant', content: response.content[0].text },
      meta: { usage: response.usage, stop_reason: response.stop_reason }
    });
  } catch (err) {
    const e = formatError(err);
    res.status(e.code || 500).json({ success: false, error: e });
  }
});

// ─── Lesson 5: Streaming (SSE) ─────────────────────────────────────────────────
app.post('/api/stream', async (req, res) => {
  let client;
  try {
    client = getClient(req);
  } catch (err) {
    const e = formatError(err);
    res.status(e.code || 401).json({ success: false, error: e });
    return;
  }

  const { message } = req.body;
  if (!message?.trim()) {
    res.status(400).json({ success: false, error: { message: 'message is required' } });
    return;
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  try {
    const stream = client.messages.stream({
      model: 'claude-opus-4-6',
      max_tokens: 1024,
      messages: [{ role: 'user', content: message }]
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
        res.write(`data: ${JSON.stringify({ type: 'text', text: event.delta.text })}\n\n`);
      }
      if (event.type === 'message_start') {
        res.write(`data: ${JSON.stringify({ type: 'start', id: event.message.id })}\n\n`);
      }
    }

    const final = await stream.finalMessage();
    res.write(`data: ${JSON.stringify({ type: 'done', usage: final.usage, stop_reason: final.stop_reason })}\n\n`);
    res.end();
  } catch (err) {
    const e = formatError(err);
    res.write(`data: ${JSON.stringify({ type: 'error', error: e })}\n\n`);
    res.end();
  }
});

// ─── Lesson 6: Tool use ────────────────────────────────────────────────────────
app.post('/api/tools', async (req, res) => {
  try {
    const client = getClient(req);
    const { query } = req.body;

    if (!query?.trim()) return res.status(400).json({ success: false, error: { message: 'query is required' } });

    const tools = [
      {
        name: 'get_weather',
        description: 'Get the current weather for a city',
        input_schema: {
          type: 'object',
          properties: {
            city: { type: 'string', description: 'The city name, e.g. Paris' },
            unit: { type: 'string', enum: ['celsius', 'fahrenheit'], description: 'Temperature unit' }
          },
          required: ['city']
        }
      },
      {
        name: 'calculate',
        description: 'Evaluate a mathematical expression and return the result',
        input_schema: {
          type: 'object',
          properties: {
            expression: { type: 'string', description: 'Math expression, e.g. "2 + 2" or "Math.sqrt(16)"' }
          },
          required: ['expression']
        }
      }
    ];

    const steps = [];
    const messages = [{ role: 'user', content: query }];
    let iterations = 0;

    while (iterations < 6) {
      iterations++;
      const response = await client.messages.create({
        model: 'claude-opus-4-6',
        max_tokens: 1024,
        tools,
        messages
      });

      const toolUseBlocks = response.content.filter(b => b.type === 'tool_use');
      const textBlocks = response.content.filter(b => b.type === 'text');

      steps.push({
        step: iterations,
        type: 'assistant',
        stop_reason: response.stop_reason,
        text: textBlocks.map(b => b.text).join(''),
        tool_calls: toolUseBlocks.map(b => ({ id: b.id, name: b.name, input: b.input }))
      });

      if (response.stop_reason === 'end_turn' || toolUseBlocks.length === 0) break;

      messages.push({ role: 'assistant', content: response.content });

      const toolResults = toolUseBlocks.map(tool => {
        let result;
        if (tool.name === 'get_weather') {
          const { city, unit = 'celsius' } = tool.input;
          const temps = { celsius: '22°C', fahrenheit: '72°F' };
          result = `Weather in ${city}: ${temps[unit]}, partly cloudy, humidity 65%, wind 12 km/h.`;
        } else if (tool.name === 'calculate') {
          try {
            // Safe math evaluation using Function constructor (tutorial only)
            const safeExpr = tool.input.expression.replace(/[^0-9+\-*/.()% \t\nMathsqrtpowfloorabsceilroundlog]/g, '');
            result = String(Function('"use strict"; return (' + safeExpr + ')')());
          } catch {
            result = 'Error: Could not evaluate expression';
          }
        } else {
          result = 'Unknown tool';
        }
        return { type: 'tool_result', tool_use_id: tool.id, content: result };
      });

      steps.push({
        step: iterations,
        type: 'tool_results',
        results: toolResults.map((r, i) => ({
          tool_name: toolUseBlocks[i].name,
          input: toolUseBlocks[i].input,
          result: r.content
        }))
      });

      messages.push({ role: 'user', content: toolResults });
    }

    const finalAnswer = steps.filter(s => s.type === 'assistant').slice(-1)[0]?.text || '';
    res.json({ success: true, steps, finalAnswer });
  } catch (err) {
    const e = formatError(err);
    res.status(e.code || 500).json({ success: false, error: e });
  }
});

// ─── Lesson 7: Error showcase ──────────────────────────────────────────────────
app.post('/api/error-demo', async (req, res) => {
  const { scenario } = req.body;

  try {
    if (scenario === 'bad_key') {
      const badClient = new Anthropic({ apiKey: 'sk-ant-invalid-key-12345' });
      await badClient.messages.create({ model: 'claude-opus-4-6', max_tokens: 10, messages: [{ role: 'user', content: 'hi' }] });
    } else if (scenario === 'bad_model') {
      const client = getClient(req);
      await client.messages.create({ model: 'claude-does-not-exist', max_tokens: 10, messages: [{ role: 'user', content: 'hi' }] });
    } else if (scenario === 'bad_request') {
      const client = getClient(req);
      await client.messages.create({ model: 'claude-opus-4-6', max_tokens: 10, messages: [{ role: 'assistant', content: 'starting with assistant is invalid' }] });
    } else if (scenario === 'exceed_tokens') {
      const client = getClient(req);
      await client.messages.create({ model: 'claude-opus-4-6', max_tokens: 9999999, messages: [{ role: 'user', content: 'hi' }] });
    }
    res.json({ success: true, content: 'No error occurred.' });
  } catch (err) {
    const e = formatError(err);
    res.json({ success: false, simulated: true, error: e });
  }
});

// ─── Practice zone ─────────────────────────────────────────────────────────────
app.post('/api/practice', async (req, res) => {
  try {
    const client = getClient(req);
    const { model = 'claude-opus-4-6', maxTokens = 1024, system, messages } = req.body;

    if (!messages?.length) return res.status(400).json({ success: false, error: { message: 'messages array is required' } });

    const params = { model, max_tokens: maxTokens, messages };
    if (system) params.system = system;

    const response = await client.messages.create(params);

    res.json({
      success: true,
      content: response.content[0].text,
      meta: { id: response.id, model: response.model, stop_reason: response.stop_reason, usage: response.usage },
      request: params
    });
  } catch (err) {
    const e = formatError(err);
    res.status(e.code || 500).json({ success: false, error: e });
  }
});

// ─── Start server ──────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║        Claude API Tutorial                   ║');
  console.log('╚══════════════════════════════════════════════╝');
  console.log(`\n  Server: http://localhost:${PORT}`);
  console.log(`  API key: ${process.env.ANTHROPIC_API_KEY ? '✓ Found in .env' : '✗ Not set (enter in UI)'}`);
  console.log('\n  Open your browser to start learning!\n');
});
