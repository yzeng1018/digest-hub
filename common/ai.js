/**
 * 公共 AI 调用模块
 *
 * 只调用免费的智谱 GLM Flash，避免任何付费模型费用。
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

// 固定免费模型，不接受环境变量覆盖，防止误切到付费模型。
const ZHIPU_URL   = 'https://open.bigmodel.cn/api/paas/v4';
const ZHIPU_KEY   = process.env.ZHIPU_API_KEY || '';
const ZHIPU_MODEL = 'glm-4.7-flash';

/**
 * 调用 LLM，返回 { response, backend }。
 * @param {Array<{role: string, content: string}>} messages
 * @param {number} maxTokens
 * @returns {Promise<{response: object, backend: string}>}
 */
export async function callAI(messages, maxTokens = 4096) {
  if (!ZHIPU_KEY) throw new Error('免费 AI 服务不可用：未配置 ZHIPU_API_KEY');
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
