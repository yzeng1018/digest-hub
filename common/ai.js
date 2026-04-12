/**
 * 公共 AI 调用模块
 *
 * 所有 JS 频道通过此模块调用 LLM，不需要各自维护 gateway/fallback 逻辑。
 * 调用链：gateway.asksidra.com → 火山方舟豆包 Lite（gateway 403/不可达时自动切换）
 */

import OpenAI from 'openai';

const GATEWAY_URL     = process.env.GATEWAY_URL     || 'http://localhost:8000/v1';
const GATEWAY_API_KEY = process.env.GATEWAY_API_KEY || 'dummy';

const VOLCENGINE_URL   = 'https://ark.cn-beijing.volces.com/api/v3';
const VOLCENGINE_KEY   = process.env.VOLCENGINE_API_KEY || '';
const VOLCENGINE_MODEL = 'ep-20260323110232-cjr59'; // 豆包 Lite，每日 200万 tokens 免费

/**
 * 调用 LLM，返回 { response, backend }。
 * gateway 不可用时自动切换到火山方舟，调用方无需关心。
 *
 * @param {Array<{role: string, content: string}>} messages
 * @param {number} maxTokens
 * @param {string} gatewayTier - gateway 路由 tier，如 'free' / 'best'
 * @returns {Promise<{response: object, backend: string}>}
 */
export async function callAI(messages, maxTokens = 4096, gatewayTier = 'free') {
  try {
    const c = new OpenAI({ baseURL: GATEWAY_URL, apiKey: GATEWAY_API_KEY });
    const r = await c.chat.completions.create({ model: gatewayTier, messages, max_tokens: maxTokens });
    return { response: r, backend: 'gateway' };
  } catch (err) {
    if (VOLCENGINE_KEY && (err.status === 403 || err.status === 429 || !err.status)) {
      console.log(`  [WARN] gateway 不可用(${err.status || err.code})，切换到火山方舟…`);
      const c = new OpenAI({ baseURL: VOLCENGINE_URL, apiKey: VOLCENGINE_KEY });
      const r = await c.chat.completions.create({ model: VOLCENGINE_MODEL, messages, max_tokens: maxTokens });
      return { response: r, backend: 'volcengine' };
    }
    throw err;
  }
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
