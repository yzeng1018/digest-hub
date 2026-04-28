/**
 * 公共 AI 调用模块
 *
 * 调用链：gateway → 火山方舟豆包 Lite → Qwen Max
 * 每级失败自动切下一级，调用方无需关心。
 */

import OpenAI from 'openai';
import { appendFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const _LOCAL_LOG = join(__dirname, '..', 'data', 'usage.jsonl');

function _appendLocal({ provider, model, response, project = '' }) {
  try {
    mkdirSync(join(__dirname, '..', 'data'), { recursive: true });
    const u = response?.usage || {};
    const record = {
      ts:            new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
      provider,
      model,
      project:       project || process.env.CHANNEL_NAME || 'digest-hub',
      input_tokens:  u.prompt_tokens     || 0,
      output_tokens: u.completion_tokens || 0,
      cost_usd:      0,
      latency_ms:    0,
      status:        'success',
    };
    appendFileSync(_LOCAL_LOG, JSON.stringify(record) + '\n');
  } catch (_) { /* 日志写入失败不中断主流程 */ }
}

const GATEWAY_URL     = process.env.GATEWAY_URL     || 'http://localhost:8000/v1';
const GATEWAY_API_KEY = process.env.GATEWAY_API_KEY || 'dummy';

const VOLCENGINE_URL   = 'https://ark.cn-beijing.volces.com/api/v3';
const VOLCENGINE_KEY   = process.env.VOLCENGINE_API_KEY || '';
const VOLCENGINE_MODEL = 'ep-20260323110232-cjr59'; // 豆包 Lite，每日 200万 tokens 免费

const QWEN_URL   = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
const QWEN_KEY   = process.env.QWEN_API_KEY || '';
const QWEN_MODEL = 'qwen-max';

/**
 * 调用 LLM，返回 { response, backend }。
 * 失败时按顺序自动降级：gateway → 火山方舟 → Qwen Max。
 *
 * @param {Array<{role: string, content: string}>} messages
 * @param {number} maxTokens
 * @param {string} gatewayTier - gateway 路由 tier，如 'free' / 'best'
 * @returns {Promise<{response: object, backend: string}>}
 */
export async function callAI(messages, maxTokens = 4096, gatewayTier = 'free') {
  // 1. gateway
  try {
    const c = new OpenAI({ baseURL: GATEWAY_URL, apiKey: GATEWAY_API_KEY });
    const r = await c.chat.completions.create({ model: gatewayTier, messages, max_tokens: maxTokens });
    _appendLocal({ provider: 'gateway', model: gatewayTier, response: r });
    return { response: r, backend: 'gateway' };
  } catch (err) {
    console.log(`  [WARN] gateway 不可用(${err.status || err.code})，切换到火山方舟…`);
  }

  // 2. 火山方舟
  if (VOLCENGINE_KEY) {
    try {
      const c = new OpenAI({ baseURL: VOLCENGINE_URL, apiKey: VOLCENGINE_KEY });
      const r = await c.chat.completions.create({ model: VOLCENGINE_MODEL, messages, max_tokens: maxTokens });
      _appendLocal({ provider: 'volcengine', model: VOLCENGINE_MODEL, response: r });
      return { response: r, backend: 'volcengine' };
    } catch (err) {
      console.log(`  [WARN] 火山方舟不可用(${err.status || err.code})，切换到 Qwen Max…`);
    }
  }

  // 3. Qwen Max 最终兜底
  if (!QWEN_KEY) throw new Error('所有 AI 服务不可用：gateway / 火山方舟均失败，且未配置 QWEN_API_KEY');
  const c = new OpenAI({ baseURL: QWEN_URL, apiKey: QWEN_KEY });
  const r = await c.chat.completions.create({ model: QWEN_MODEL, messages, max_tokens: maxTokens });
  _appendLocal({ provider: 'qwen', model: QWEN_MODEL, response: r });
  return { response: r, backend: 'qwen' };
}

/**
 * 简化版：直接返回 LLM 文本输出，适合 enrich 场景。
 *
 * @param {string} systemPrompt
 * @param {string} userMsg
 * @param {number} maxTokens
 * @returns {Promise<string>}
 */
export async function callAIText(systemPrompt, userMsg, maxTokens = 1024) {
  const messages = [
    { role: 'system', content: systemPrompt },
    { role: 'user',   content: userMsg },
  ];
  const { response } = await callAI(messages, maxTokens);
  return response.choices[0].message.content || '';
}
