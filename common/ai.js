/**
 * 公共 AI 调用模块。
 *
 * A/B 实验：DeepSeek V4 Flash 与 Qwen Max 按频道、按北京时间日期轮转。
 * 同一次 digest 的评分和 enrich 始终使用同一个实验臂；首选不可用时才
 * 降级到另一臂，最终邮件会展示实际响应的模型名。
 */

import OpenAI from 'openai';
import { appendFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const DEEPSEEK_URL   = process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com';
const DEEPSEEK_KEY   = process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-v4-flash';

const QWEN_URL   = process.env.QWEN_BASE_URL || 'https://dashscope.aliyuncs.com/compatible-mode/v1';
const QWEN_KEY   = process.env.QWEN_API_KEY || process.env.DASHSCOPE_API_KEY || '';
const QWEN_MODEL = process.env.QWEN_MODEL || 'qwen-max';

const CHANNEL_SLOTS = {
  'digest-hub/crypto': 0,
  'digest-hub/investment': 0,
  'digest-hub/ai-info': 1,
  'digest-hub/product-radar': 1,
  'digest-hub/growth-weekly': 0,
  'digest-hub/product-radar-weekly': 1,
};

function beijingDateString(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const values = Object.fromEntries(parts.map(p => [p.type, p.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function epochDay(dateString) {
  const [year, month, day] = dateString.split('-').map(Number);
  return Math.floor(Date.UTC(year, month - 1, day) / 86_400_000);
}

function fallbackSlot(channel) {
  return Array.from(channel).reduce((sum, ch) => sum + ch.codePointAt(0), 0) % 2;
}

/** Pure selector exported for local verification. */
export function selectModel(
  channel = process.env.CHANNEL_NAME || 'digest-hub',
  dateString = process.env.MODEL_AB_DATE || beijingDateString(),
  override = (process.env.MODEL_AB_OVERRIDE || '').toLowerCase(),
) {
  if (override === 'deepseek' || override === 'qwen') return override;
  const slot = CHANNEL_SLOTS[channel] ?? fallbackSlot(channel);
  return (epochDay(dateString) + slot) % 2 === 0 ? 'deepseek' : 'qwen';
}

const CHANNEL = process.env.CHANNEL_NAME || 'digest-hub';
const AB_DATE = process.env.MODEL_AB_DATE || beijingDateString();
const SELECTED_PROVIDER = selectModel(CHANNEL, AB_DATE);
let activeProvider = null;
const LOG_NAME = `${CHANNEL.replace(/[^a-zA-Z0-9._-]+/g, '-')}.jsonl`;
const LOCAL_LOG = join(__dirname, '..', 'data', 'usage', LOG_NAME);

function providerConfig(provider) {
  if (provider === 'deepseek') {
    return { provider, baseURL: DEEPSEEK_URL, apiKey: DEEPSEEK_KEY, model: DEEPSEEK_MODEL };
  }
  return { provider: 'qwen', baseURL: QWEN_URL, apiKey: QWEN_KEY, model: QWEN_MODEL };
}

function appendLocal({ provider, model, response, scheduledProvider }) {
  try {
    mkdirSync(join(__dirname, '..', 'data', 'usage'), { recursive: true });
    const u = response?.usage || {};
    const record = {
      ts: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
      provider,
      model,
      project: CHANNEL,
      input_tokens: u.prompt_tokens || 0,
      output_tokens: u.completion_tokens || 0,
      cost_usd: 0,
      latency_ms: 0,
      status: 'success',
      experiment: 'deepseek-v4-flash_vs_qwen-max',
      experiment_date: AB_DATE,
      scheduled_provider: scheduledProvider,
    };
    appendFileSync(LOCAL_LOG, JSON.stringify(record) + '\n');
  } catch (_) { /* 日志写入失败不中断主流程 */ }
}

async function callProvider(config, messages, maxTokens) {
  if (!config.apiKey) throw new Error(`未配置 ${config.provider} API key`);
  const client = new OpenAI({ baseURL: config.baseURL, apiKey: config.apiKey });
  const options = {
    model: config.model,
    messages,
    max_tokens: maxTokens,
  };
  // 摘要与 JSON 评分更需要稳定格式，关闭 DeepSeek 的思考模式。
  if (config.provider === 'deepseek') {
    options.extra_body = { thinking: { type: 'disabled' } };
  }
  return client.chat.completions.create(options);
}

/**
 * 调用 LLM，返回 { response, backend }。
 * 首选实验臂失败时降级到另一臂，保证日报尽量送达。
 */
export async function callAI(messages, maxTokens = 8192) {
  const fallback = SELECTED_PROVIDER === 'deepseek' ? 'qwen' : 'deepseek';
  let firstError;

  const candidates = activeProvider ? [activeProvider] : [SELECTED_PROVIDER, fallback];
  console.log(`  [A/B] ${AB_DATE} · ${CHANNEL} → ${activeProvider || SELECTED_PROVIDER}`);
  for (const provider of candidates) {
    const config = providerConfig(provider);
    try {
      const response = await callProvider(config, messages, maxTokens);
      appendLocal({
        provider,
        model: response.model || config.model,
        response,
        scheduledProvider: SELECTED_PROVIDER,
      });
      if (provider !== SELECTED_PROVIDER) {
        console.log(`  [A/B] ${SELECTED_PROVIDER} 不可用，已降级到 ${provider}`);
      }
      activeProvider = provider;
      return { response, backend: provider };
    } catch (err) {
      firstError ||= err;
      console.log(`  [${provider}] 调用失败: ${err?.message || err}`);
    }
  }
  throw firstError || new Error('DeepSeek 与 Qwen 均不可用');
}

export async function callAIText(systemPrompt, userMsg, maxTokens = 1024) {
  const messages = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMsg },
  ];
  const { response } = await callAI(messages, maxTokens);
  return response.choices[0].message.content || '';
}

export function reportExperimentScore(metrics = {}, model = '', project = CHANNEL) {
  if (!model || !Object.keys(metrics).length) return;
  try {
    const logName = `${project.replace(/[^a-zA-Z0-9._-]+/g, '-')}.jsonl`;
    const logDir = join(__dirname, '..', 'data', 'model-scores');
    mkdirSync(logDir, { recursive: true });
    appendFileSync(join(logDir, logName), JSON.stringify({
      ts: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
      project,
      model,
      provider: activeProvider || SELECTED_PROVIDER,
      scheduled_provider: SELECTED_PROVIDER,
      experiment_date: AB_DATE,
      parse_rate: metrics.parseRate || 0,
      score_spread: metrics.scoreSpread || 0,
      translation_rate: metrics.translationRate || 0,
      perf_score: metrics.perfScore || 0,
    }) + '\n');
  } catch (_) { /* 指标日志失败不中断邮件 */ }
}
