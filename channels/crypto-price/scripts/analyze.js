import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { callAI } from '../../../common/ai.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SYSTEM_PROMPT = readFileSync(join(__dirname, '../prompts/analyze.md'), 'utf8');

export const tokenUsage = { model: '', prompt: 0, completion: 0, total: 0 };

function fmtPct(n) {
  if (n === null || n === undefined) return '?%';
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
}

function buildMarketSummary(data) {
  const { overview, keyCoins, gainers, losers, volumeAnomalies, trending } = data;
  const { btc, eth, sol } = keyCoins;

  const lines = [];

  lines.push('## 全球市场概览');
  lines.push(`- 总市值：${overview.totalMarketCapFmt} (24h: ${fmtPct(overview.marketCapChange24h)})`);
  lines.push(`- BTC 主导权：${overview.btcDominance.toFixed(1)}% | ETH：${overview.ethDominance.toFixed(1)}%`);
  if (overview.fearGreed) {
    lines.push(`- 恐惧贪婪指数：${overview.fearGreed.value}/100 · ${overview.fearGreed.label}`);
  }

  lines.push('\n## 主要资产 (24h)');
  if (btc) lines.push(`- BTC: ${btc.priceFmt} | 24h: ${fmtPct(btc.price_change_percentage_24h)} | 市值: ${btc.capFmt} | 成交量: ${btc.volFmt}`);
  if (eth) lines.push(`- ETH: ${eth.priceFmt} | 24h: ${fmtPct(eth.price_change_percentage_24h)} | 市值: ${eth.capFmt} | 成交量: ${eth.volFmt}`);
  if (sol) lines.push(`- SOL: ${sol.priceFmt} | 24h: ${fmtPct(sol.price_change_percentage_24h)} | 市值: ${sol.capFmt} | 成交量: ${sol.volFmt}`);

  lines.push('\n## 24h 最大涨幅 (Top 100市值)');
  gainers.slice(0, 5).forEach((c, i) => {
    lines.push(`${i + 1}. ${c.name} (${c.symbol.toUpperCase()}): ${fmtPct(c.price_change_percentage_24h)} | ${c.priceFmt} | 市值: ${c.capFmt}`);
  });

  lines.push('\n## 24h 最大跌幅 (Top 100市值)');
  losers.slice(0, 5).forEach((c, i) => {
    lines.push(`${i + 1}. ${c.name} (${c.symbol.toUpperCase()}): ${fmtPct(c.price_change_percentage_24h)} | ${c.priceFmt} | 市值: ${c.capFmt}`);
  });

  lines.push('\n## 异常放量 (量/市值比最高，代表资金异常活跃)');
  volumeAnomalies.forEach((c, i) => {
    lines.push(`${i + 1}. ${c.name} (${c.symbol.toUpperCase()}): 量/市值=${(c.volumeRatio * 100).toFixed(1)}% | 24h: ${fmtPct(c.price_change_percentage_24h)} | ${c.priceFmt}`);
  });

  lines.push('\n## CoinGecko 热搜榜 (市场情绪指标)');
  trending.forEach((c, i) => {
    lines.push(`${i + 1}. ${c.name} (${c.symbol})`);
  });

  return lines.join('\n');
}

function parseInsight(text) {
  if (!text || !text.trim()) {
    console.log('  [WARN] AI 返回空内容');
    return null;
  }
  const clean = text.replace(/```(?:json)?/g, '').replace(/```/g, '').trim();
  const m = clean.match(/\{[\s\S]*\}/);
  if (!m) {
    console.log(`  [WARN] 未找到 JSON 块，原始长度 ${text.length}，前200字：${text.slice(0, 200)}`);
    return null;
  }
  try { return JSON.parse(m[0]); }
  catch (e) {
    console.log(`  [WARN] JSON 解析失败: ${e.message}，JSON 片段：${m[0].slice(0, 200)}`);
    return null;
  }
}

export async function analyzeMarket(data) {
  const userMsg = buildMarketSummary(data);

  try {
    const { response, backend } = await callAI([
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userMsg },
    ], 3000);

    tokenUsage.model = response.model || `${backend}/auto`;
    if (response.usage) {
      tokenUsage.prompt     = response.usage.prompt_tokens     || 0;
      tokenUsage.completion = response.usage.completion_tokens || 0;
      tokenUsage.total      = response.usage.total_tokens      || 0;
    }

    const rawContent = response.choices[0].message.content || '';
    const insight = parseInsight(rawContent);
    console.log(`  AI 分析完成 (${tokenUsage.model}, ${tokenUsage.total} tokens, finish=${response.choices[0].finish_reason})`);
    return insight || {};
  } catch (err) {
    console.log(`  [WARN] AI 分析失败: ${err.message}`);
    return {};
  }
}
