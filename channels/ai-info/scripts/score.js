import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SYSTEM_PROMPT = readFileSync(join(__dirname, '../prompts/score.md'), 'utf8');

const GATEWAY_URL     = process.env.GATEWAY_URL     || 'http://localhost:8000/v1';
const GATEWAY_API_KEY = process.env.GATEWAY_API_KEY || 'dummy';

export const tokenUsage = { model: '', prompt: 0, completion: 0, total: 0 };

function makeClient(baseURL, apiKey) {
  return new OpenAI({ baseURL, apiKey });
}

async function callAI(messages) {
  const c = makeClient(GATEWAY_URL, GATEWAY_API_KEY);
  const r = await c.chat.completions.create({ model: 'free', messages, max_tokens: 4096 });
  return { response: r, backend: 'gateway' };
}

function summaryFor(art) {
  if (art.platform === 'Podcast' && art.transcript) return art.transcript.slice(0, 2000);
  return (art.summary || '').slice(0, 300);
}

function parseResult(text) {
  const clean = text.replace(/```(?:json)?/g, '').trim();
  const m = clean.match(/\[[\s\S]*\]/);
  if (!m) return [];
  try { return JSON.parse(m[0]); } catch { return []; }
}

export async function scoreArticles(articles, batchSize = 10) {
  if (!GATEWAY_URL) {
    console.log('[WARN] 无 AI key，跳过评分');
    articles.forEach(a => { a.score = 5; a.reason_zh = ''; a.title_zh = a.title; a.summary_zh = a.summary || ''; });
    return articles;
  }

  const USER_TEMPLATE = (count, json) =>
    `请对以下 ${count} 条内容进行评估。\n\n严格按照以下 JSON 格式返回，不要有任何其他文字，不要有 markdown 代码块：\n[\n  {\n    "id": "序号，从0开始",\n    "score": 评分数字(1-10),\n    "reason_zh": "一句话说明价值（20字以内）",\n    "title_zh": "中文标题",\n    "summary_zh": "中文摘要2-3句"\n  }\n]\n\n内容列表：\n${json}`;

  for (let start = 0; start < articles.length; start += batchSize) {
    const batch = articles.slice(start, start + batchSize);
    console.log(`  评分 [${start + 1}–${start + batch.length}]…`);

    const items = batch.map((a, i) => ({
      id: String(i),
      platform: a.platform,
      source: a.source,
      lang: a.lang,
      title: a.title,
      summary: summaryFor(a),
    }));

    try {
      const { response, backend } = await callAI([
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: USER_TEMPLATE(batch.length, JSON.stringify(items, null, 2)) },
      ]);

      if (!tokenUsage.model) tokenUsage.model = response.model || `${backend}/auto`;
      if (response.usage) {
        tokenUsage.prompt     += response.usage.prompt_tokens     || 0;
        tokenUsage.completion += response.usage.completion_tokens || 0;
        tokenUsage.total      += response.usage.total_tokens      || 0;
      }

      const results = parseResult(response.choices[0].message.content || '');
      const byId = Object.fromEntries(results.map(r => [r.id, r]));

      batch.forEach((art, i) => {
        const r = byId[String(i)];
        art.score      = r ? Math.min(10, Math.max(1, Number(r.score) || 5)) : 5;
        art.reason_zh  = r?.reason_zh  || '';
        art.title_zh   = r?.title_zh   || art.title;
        art.summary_zh = r?.summary_zh || art.summary || '';
      });
    } catch (err) {
      console.log(`  [ERROR] 评分批次失败: ${err.message}`);
      batch.forEach(art => {
        art.score = 5; art.reason_zh = ''; art.title_zh = art.title; art.summary_zh = art.summary || '';
      });
    }
  }

  // 兜底：若所有批次均失败（如 gateway 被 Cloudflare 拦截），确保 model 字段有值
  if (!tokenUsage.model) tokenUsage.model = 'gateway/blocked';

  return articles;
}

export async function reportUsage(_project) {
  // Usage is now tracked automatically by the gateway — no manual reporting needed.
}
