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

// Groq 主力（qwen-qwq-32b，免费，质量 9.0，中文 9.0）
const GROQ_URL   = 'https://api.groq.com/openai/v1';
const GROQ_KEY   = process.env.GROQ_API_KEY || '';
const GROQ_MODEL = 'qwen-qwq-32b';

// 智谱 GLM 兜底（glm-4.7-flash，永久免费无上限）
const ZHIPU_URL   = 'https://open.bigmodel.cn/api/paas/v4';
const ZHIPU_KEY   = process.env.ZHIPU_API_KEY || '';
const ZHIPU_MODEL = 'glm-4.7-flash';

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
  // 1. Groq qwen-qwq-32b（免费，质量 9.0，中文 9.0）
  if (GROQ_KEY) {
    try {
      const c = new OpenAI({ baseURL: GROQ_URL, apiKey: GROQ_KEY });
      const r = await c.chat.completions.create({ model: GROQ_MODEL, messages, max_tokens: maxTokens });
      _appendLocal({ provider: 'groq', model: GROQ_MODEL, response: r });
      return { response: r, backend: 'groq' };
    } catch (err) {
      console.log(`  [WARN] Groq 不可用(${err.status || err.code})，切换到智谱…`);
    }
  }

  // 2. 智谱 glm-4.7-flash（永久免费无上限）
  if (!ZHIPU_KEY) throw new Error('所有 AI 服务不可用：未配置 GROQ_API_KEY 或 ZHIPU_API_KEY');
  const c = new OpenAI({ baseURL: ZHIPU_URL, apiKey: ZHIPU_KEY });
  const r = await c.chat.completions.create({ model: ZHIPU_MODEL, messages, max_tokens: maxTokens });
  _appendLocal({ provider: 'zhipu', model: ZHIPU_MODEL, response: r });
  return { response: r, backend: 'zhipu' };
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
