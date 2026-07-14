/**
 * 公共 AI 调用模块
 *
 * 只调用 Groq 免费层上的 Qwen，避免任何付费模型费用。
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

// 固定 Groq 免费层上的 Qwen 模型，不接受环境变量覆盖，防止误切到付费模型。
const GROQ_URL   = 'https://api.groq.com/openai/v1';
const GROQ_KEY   = process.env.GROQ_API_KEY || '';
const GROQ_MODEL = 'qwen/qwen3.6-27b';

/**
 * 调用 LLM，返回 { response, backend }。
 * @param {Array<{role: string, content: string}>} messages
 * @param {number} maxTokens
 * @returns {Promise<{response: object, backend: string}>}
 */
export async function callAI(messages, maxTokens = 4096) {
  if (!GROQ_KEY) throw new Error('免费 AI 服务不可用：未配置 GROQ_API_KEY');
  const c = new OpenAI({ baseURL: GROQ_URL, apiKey: GROQ_KEY });
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await c.chat.completions.create({
        model: GROQ_MODEL,
        messages,
        max_tokens: maxTokens,
        reasoning_effort: 'none',
      });
      _appendLocal({ provider: 'groq', model: GROQ_MODEL, response: r });
      return { response: r, backend: 'groq' };
    } catch (err) {
      if (err?.status !== 429 || attempt === 2) throw err;
      const header = err?.headers?.get?.('retry-after') ?? err?.headers?.['retry-after'];
      const parsed = Number(header);
      const delaySeconds = Number.isFinite(parsed)
        ? Math.min(90, Math.max(1, parsed))
        : 30 * (attempt + 1);
      console.log(`  [groq] 触发免费层限流，${delaySeconds} 秒后重试…`);
      await new Promise(resolve => setTimeout(resolve, delaySeconds * 1000));
    }
  }
  throw new Error('Groq 请求重试失败');
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
