import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { callAI } from '../../../common/ai.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SYSTEM_PROMPT = readFileSync(join(__dirname, '../prompts/score.md'), 'utf8');

export const tokenUsage = { model: '', prompt: 0, completion: 0, total: 0 };
export const tokenMetrics = { parseRate: 0, scoreSpread: 0, translationRate: 0, perfScore: 0 };


function parseResult(text) {
  const clean = text.replace(/```(?:json)?/g, '').trim();
  const m = clean.match(/\[[\s\S]*\]/);
  if (!m) return [];
  try { return JSON.parse(m[0]); } catch { return []; }
}

export async function scoreArticles(articles, batchSize = 10) {
  const USER_TEMPLATE = (count, json) =>
    `请对以下 ${count} 条内容进行评估。\n\n严格按照以下 JSON 格式返回，不要有任何其他文字，不要有 markdown 代码块：\n[\n  {\n    "id": "序号，从0开始",\n    "score": 评分数字(1-10),\n    "reason_zh": "一句话说明价值（20字以内）",\n    "title_zh": "中文标题",\n    "summary_zh": "中文摘要4-6句，充分展开背景、核心内容和价值，不要过于简短"\n  }\n]\n\n内容列表：\n${json}`;

  let batchesTotal = 0;
  let batchesParsed = 0;

  for (let start = 0; start < articles.length; start += batchSize) {
    const batch = articles.slice(start, start + batchSize);
    console.log(`  评分 [${start + 1}–${start + batch.length}]…`);

    const items = batch.map((a, i) => ({
      id: String(i),
      platform: a.platform,
      source: a.source,
      lang: a.lang,
      title: a.title,
      summary: (a.summary || '').slice(0, 300),
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
      batchesTotal++;
      if (results.length) batchesParsed++;
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


  // Calculate model performance metrics
  const _scores = articles.map(a => a.score || 0).filter(s => s > 0);
  if (_scores.length >= 2) {
    const _mean = _scores.reduce((a, b) => a + b, 0) / _scores.length;
    tokenMetrics.scoreSpread = Math.round(Math.sqrt(_scores.reduce((acc, s) => acc + (s - _mean) ** 2, 0) / _scores.length) * 100) / 100;
  }
  const _translated = articles.filter(a => a.title_zh && a.title_zh !== a.title).length;
  tokenMetrics.parseRate        = batchesTotal > 0 ? batchesParsed / batchesTotal : 0;
  tokenMetrics.translationRate  = articles.length > 0 ? _translated / articles.length : 0;
  tokenMetrics.perfScore = Math.round((
    tokenMetrics.parseRate * 4 +
    Math.min(tokenMetrics.scoreSpread / 3, 1) * 3 +
    tokenMetrics.translationRate * 3
  ) * 100) / 100;

  if (!tokenUsage.model) tokenUsage.model = 'gateway/blocked';

  return articles;
}

export async function reportUsage(_project) {
  // Usage is now tracked automatically by the gateway — no manual reporting needed.
}
