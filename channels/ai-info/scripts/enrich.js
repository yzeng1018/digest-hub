import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { callAIText as callAI } from '../../../common/ai.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ENRICH_PROMPT         = readFileSync(join(__dirname, '../prompts/enrich.md'), 'utf8');
const ENRICH_PODCAST_PROMPT = readFileSync(join(__dirname, '../prompts/enrich-podcast.md'), 'utf8');

function parseJson(text) {
  const clean = text.replace(/```(?:json)?/g, '').trim();
  const m = clean.match(/\{[\s\S]*\}/);
  if (!m) return {};
  try { return JSON.parse(m[0]); } catch { return {}; }
}

async function enrichOne(art) {
  try {
    if (art.platform === 'Podcast' && art.transcript) {
      const userMsg = `播客节目：${art.source}\n集标题：${art.title}\n\n转录稿（节选）：\n${art.transcript.slice(0, 6000)}`;
      const raw = await callAI(ENRICH_PODCAST_PROMPT, userMsg);
      const data = parseJson(raw);
      if (data.reason_zh) art.reason_zh = data.reason_zh;
      art.background_zh = data.background_zh || '';
    } else {
      const userMsg = `内容标题：${art.title}\n来源：${art.source} (${art.platform})\n当前摘要：${(art.summary || '').slice(0, 300)}`;
      const raw = await callAI(ENRICH_PROMPT, userMsg);
      const data = parseJson(raw);
      if (data.reason_zh) art.reason_zh = data.reason_zh;
      art.background_zh = data.background_zh || '';
    }
  } catch (err) {
    console.log(`  [WARN] enrich 失败: ${art.title.slice(0, 40)} — ${err.message}`);
    art.background_zh = '';
  }
}

export async function enrichArticles(articles, config) {
  const targets = articles
    .filter(a => (a.score || 0) >= config.enrichMinScore)
    .slice(0, config.enrichMaxCount);

  if (!targets.length) {
    articles.forEach(a => { a.background_zh ??= ''; });
    return articles;
  }

  console.log(`\nEnriching ${targets.length} 条高分内容…`);
  for (let i = 0; i < targets.length; i++) {
    const art = targets[i];
    console.log(`  [${i + 1}/${targets.length}] ${art.title.slice(0, 55)}…`);
    await enrichOne(art);
  }

  articles.forEach(a => { a.background_zh ??= ''; });
  return articles;
}
