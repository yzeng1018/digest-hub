#!/usr/bin/env node
// Run via: node --env-file=.env main.js  (env vars must be loaded before modules)
import { mkdir, writeFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { parseArgs } from 'util';

const __dirname = dirname(fileURLToPath(import.meta.url));

import { fetchPrices } from './scripts/fetchPrices.js';
import { analyzeMarket, tokenUsage } from './scripts/analyze.js';
import { render } from './scripts/render.js';
import { deliver } from './scripts/deliver.js';

const { values: args } = parseArgs({
  options: {
    'no-ai':    { type: 'boolean', default: false },
    'no-email': { type: 'boolean', default: false },
  },
  strict: false,
});

async function main() {
  console.log('\n📡 加密价格雷达启动…');
  console.log('  数据源：CoinGecko (Top 100) + Alternative.me FGI\n');

  console.log('🌐 抓取市场数据…');
  const data = await fetchPrices();
  console.log(`  ✓ 总市值 ${data.overview.totalMarketCapFmt} (${data.overview.marketCapChange24h >= 0 ? '+' : ''}${data.overview.marketCapChange24h.toFixed(2)}%)`);
  if (data.keyCoins.btc) {
    const btc = data.keyCoins.btc;
    console.log(`  ✓ BTC ${btc.priceFmt} (${btc.price_change_percentage_24h >= 0 ? '+' : ''}${btc.price_change_percentage_24h.toFixed(2)}%)`);
  }
  console.log(`  ✓ 涨幅榜Top1: ${data.gainers[0]?.name} (+${data.gainers[0]?.price_change_percentage_24h?.toFixed(2)}%)`);
  console.log(`  ✓ 跌幅榜Top1: ${data.losers[0]?.name} (${data.losers[0]?.price_change_percentage_24h?.toFixed(2)}%)`);

  let insight = {};
  if (!args['no-ai']) {
    console.log('\n🧠 AI 市场分析（顶级交易员视角）…');
    insight = await analyzeMarket(data);
    if (insight.summary) console.log(`  → ${insight.summary}`);
  } else {
    console.log('\n跳过 AI 分析 (--no-ai)');
  }

  const dateStr = new Date().toISOString().slice(0, 10);
  const outputDir = join(__dirname, 'output');
  await mkdir(outputDir, { recursive: true });

  const markdown = render(data, insight, dateStr, args['no-ai'] ? {} : tokenUsage);
  const outputPath = join(outputDir, `${dateStr}.md`);
  await writeFile(outputPath, markdown, 'utf8');
  console.log(`\n📄 Markdown 已保存 → ${outputPath}`);

  if (!args['no-email']) {
    await deliver(data, insight, markdown, dateStr, args['no-ai'] ? {} : tokenUsage);
  } else {
    console.log('跳过发邮件 (--no-email)');
  }

  console.log('\n✅ 价格雷达完成。');
  process.exit(0);
}

main().catch(e => { console.error(e); process.exit(1); });
