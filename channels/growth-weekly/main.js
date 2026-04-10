#!/usr/bin/env node
import { readFileSync } from 'fs';
import { mkdir, writeFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { parseArgs } from 'util';
import { config as loadEnv } from 'dotenv';

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, '.env') });

import { fetchTweets } from './scripts/fetchTweets.js';
import { fetchBlogs }  from './scripts/fetchBlogs.js';
import { deduplicate } from './scripts/dedup.js';
import { scoreArticles, reportUsage, tokenUsage } from './scripts/score.js';
import { enrichArticles } from './scripts/enrich.js';
import { render }         from './scripts/render.js';
import { deliver }        from './scripts/deliver.js';

const sources = JSON.parse(readFileSync(join(__dirname, 'config/sources.json'), 'utf8'));
const cfg = sources.config;

const { values: args } = parseArgs({
  options: {
    'no-score': { type: 'boolean', default: false },
    'no-email': { type: 'boolean', default: false },
  },
  strict: false,
});

async function main() {
  const now = new Date();
  const weekStart = new Date(now - 7 * 24 * 3600 * 1000);
  const weekStr = `${weekStart.toISOString().slice(0, 10)} ~ ${now.toISOString().slice(0, 10)}`;
  console.log(`\n开始抓取 Growth Weekly（过去7天：${weekStr}）…`);

  const [tweets, blogs] = await Promise.all([
    fetchTweets(sources.twitter, sources.nitterInstances, cfg),
    fetchBlogs(sources.blogs, cfg),
  ]);

  let articles = [...tweets, ...blogs];
  console.log(`\n抓取完成：共 ${articles.length} 条原始内容`);

  if (!articles.length) {
    console.error('未抓到任何内容，请检查网络或数据源。');
    process.exit(1);
  }

  articles = deduplicate(articles, cfg.dedupThreshold);
  console.log(`去重后：${articles.length} 条`);

  if (!args['no-score']) {
    console.log(`\n严格评分中（${articles.length} 条）…`);
    articles = await scoreArticles(articles, cfg.scoreBatchSize);
    await reportUsage('digest-hub/growth-weekly');
  } else {
    console.log('跳过评分 (--no-score)');
    articles.forEach(a => {
      a.score = 5; a.reason_zh = ''; a.title_zh = a.title; a.summary_zh = a.summary || '';
    });
  }

  // 严选：只保留达到精读阈值的文章
  articles.sort((a, b) => (b.score || 0) - (a.score || 0));
  const beforeFilter = articles.length;
  articles = articles.filter(a => (a.score || 0) >= cfg.scoreImportant);
  articles = articles.slice(0, cfg.maxArticles);
  console.log(`\n严选后：${articles.length} 条（过滤掉 ${beforeFilter - articles.length} 条低分内容）`);

  if (!articles.length) {
    console.log('本周未发现值得精读的内容，跳过发送。');
    process.exit(0);
  }

  if (!args['no-score']) {
    articles = await enrichArticles(articles, cfg);
  } else {
    articles.forEach(a => { a.background_zh = ''; });
  }

  const dateStr = now.toISOString().slice(0, 10);
  const outputDir = join(__dirname, 'output');
  await mkdir(outputDir, { recursive: true });

  const markdown = render(articles, dateStr, weekStr, args['no-score'] ? {} : tokenUsage);
  const outputPath = join(outputDir, `${dateStr}.md`);
  await writeFile(outputPath, markdown, 'utf8');
  console.log(`\nMarkdown 已保存 → ${outputPath}`);

  if (!args['no-email']) {
    await deliver(markdown, articles, dateStr, weekStr, args['no-score'] ? {} : tokenUsage);
  }

  const mustReads = articles.filter(a => (a.score || 0) >= cfg.scoreMustRead).length;
  console.log(`\n✅ 完成。本周精读 ${articles.length} 篇 · 🔥 强烈推荐 ${mustReads} 篇`);
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
