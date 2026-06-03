function fmtPct(n) {
  if (n === null || n === undefined) return '?%';
  const s = (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
  return s;
}

function fgiEmoji(value) {
  if (value >= 75) return '🤑 极度贪婪';
  if (value >= 55) return '😊 贪婪';
  if (value >= 45) return '😐 中性';
  if (value >= 25) return '😟 恐惧';
  return '😱 极度恐惧';
}

export function render(data, insight, dateStr, tokenUsage = {}) {
  const { overview, keyCoins, gainers, losers, volumeAnomalies, trending } = data;
  const { btc, eth, sol } = keyCoins;

  const tokenLine = tokenUsage.model
    ? `*🤖 ${tokenUsage.model} · ${tokenUsage.total ? tokenUsage.total.toLocaleString() + ' tokens' : '—'}*\n\n`
    : '';

  const lines = [];
  lines.push(`# 加密市场价格雷达 · ${dateStr}\n`);

  // Overview
  lines.push('## 📊 市场总览\n');
  lines.push(`| 指标 | 数值 |`);
  lines.push(`|------|------|`);
  lines.push(`| 总市值 | ${overview.totalMarketCapFmt} (${fmtPct(overview.marketCapChange24h)}) |`);
  lines.push(`| BTC 主导权 | ${overview.btcDominance.toFixed(1)}% |`);
  lines.push(`| ETH 主导权 | ${overview.ethDominance.toFixed(1)}% |`);
  if (overview.fearGreed) {
    lines.push(`| 恐惧贪婪指数 | ${overview.fearGreed.value}/100 · ${fgiEmoji(overview.fearGreed.value)} |`);
  }
  lines.push('');

  // Key coins
  lines.push('## 💎 主要资产\n');
  lines.push(`| 资产 | 价格 | 24h | 成交量 |`);
  lines.push(`|------|------|-----|--------|`);
  [btc, eth, sol].forEach(c => {
    if (!c) return;
    const arrow = (c.price_change_percentage_24h || 0) >= 0 ? '▲' : '▼';
    lines.push(`| **${c.symbol.toUpperCase()}** | ${c.priceFmt} | ${arrow} ${fmtPct(c.price_change_percentage_24h)} | ${c.volFmt} |`);
  });
  lines.push('');

  // AI Insight (star section)
  if (insight && Object.keys(insight).length > 0) {
    lines.push('## 🧠 顶级交易员视角\n');
    if (insight.summary) lines.push(`> **${insight.summary}**\n`);
    const sections = [
      { key: 'market_structure', label: '市场结构' },
      { key: 'movers_insight',   label: '主力异动' },
      { key: 'sector_rotation',  label: '赛道轮动' },
      { key: 'btc_dominance',    label: 'BTC主导权' },
      { key: 'risk_warning',     label: '⚠️ 风险雷达' },
      { key: 'watch_point',      label: '🎯 今日盯盘' },
    ];
    sections.forEach(({ key, label }) => {
      if (insight[key]) lines.push(`**${label}**：${insight[key]}\n`);
    });
    lines.push('---\n');
  }

  // Gainers
  lines.push('## 🚀 Top 涨幅 (Top 100市值)\n');
  lines.push(`| # | 币种 | 价格 | 24h涨幅 | 市值 |`);
  lines.push(`|---|------|------|---------|------|`);
  gainers.slice(0, 7).forEach((c, i) => {
    lines.push(`| ${i + 1} | **${c.symbol.toUpperCase()}** ${c.name} | ${c.priceFmt} | **+${c.price_change_percentage_24h.toFixed(2)}%** | ${c.capFmt} |`);
  });
  lines.push('');

  // Losers
  lines.push('## 📉 Top 跌幅 (Top 100市值)\n');
  lines.push(`| # | 币种 | 价格 | 24h跌幅 | 市值 |`);
  lines.push(`|---|------|------|---------|------|`);
  losers.slice(0, 7).forEach((c, i) => {
    lines.push(`| ${i + 1} | **${c.symbol.toUpperCase()}** ${c.name} | ${c.priceFmt} | **${c.price_change_percentage_24h.toFixed(2)}%** | ${c.capFmt} |`);
  });
  lines.push('');

  // Volume anomalies
  lines.push('## 🔊 异常放量 (量/市值比)\n');
  lines.push(`| 币种 | 量/市值 | 24h | 价格 |`);
  lines.push(`|------|---------|-----|------|`);
  volumeAnomalies.forEach(c => {
    const arrow = (c.price_change_percentage_24h || 0) >= 0 ? '▲' : '▼';
    lines.push(`| **${c.symbol.toUpperCase()}** ${c.name} | ${(c.volumeRatio * 100).toFixed(1)}% | ${arrow} ${fmtPct(c.price_change_percentage_24h)} | ${c.priceFmt} |`);
  });
  lines.push('');

  // Trending
  if (trending.length) {
    lines.push('## 🔥 CoinGecko 热搜\n');
    lines.push(trending.map((c, i) => `${i + 1}. **${c.symbol}** ${c.name}`).join('  ·  '));
    lines.push('\n');
  }

  lines.push('---\n');
  lines.push(tokenLine);
  lines.push(`*价格雷达自动生成 · 数据来源：CoinGecko · ${data.fetchedAt}*\n`);

  return lines.join('\n');
}
