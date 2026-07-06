export function render(articles, dateStr, tokenUsage = {}, marketData = null) {
  const mustRead  = articles.filter(a => a.score >= 9);
  const important = articles.filter(a => a.score >= 6 && a.score < 9);
  const general   = articles.filter(a => a.score < 6);

  const tokenLine = tokenUsage.model
    ? `*🤖 ${tokenUsage.model} · ${tokenUsage.total ? tokenUsage.total.toLocaleString() + ' tokens' : '—'}*\n\n`
    : '';

  const lines = [];
  lines.push(`# 每日加密情报 · ${dateStr}\n`);
  lines.push(`> 🔥 必读 **${mustRead.length}** &nbsp; ⚡ 重要 **${important.length}** &nbsp; 📌 一般 **${general.length}** &nbsp;·&nbsp; 共 **${articles.length}** 条\n`);
  if (marketData) lines.push(renderMarketSnapshot(marketData));
  lines.push('---\n');

  if (mustRead.length) {
    lines.push('## 🔥 必读\n');
    mustRead.forEach(a => lines.push(renderCard(a)));
  }

  if (important.length) {
    lines.push('## ⚡ 重要\n');
    important.forEach(a => lines.push(renderCard(a)));
  }

  if (general.length) {
    lines.push('## 📌 一般\n');
    general.forEach(a => lines.push(renderCard(a)));
  }

  lines.push('---\n');
  lines.push(tokenLine);
  lines.push('*加密情报自动生成 · 来源：X / Blog*\n');

  return lines.join('\n');
}

function renderMarketSnapshot({ overview, keyCoins, gainers, losers }) {
  const pct = value => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  const formatCoin = value => value ? `${value.symbol.toUpperCase()} ${value.priceFmt} (${pct(value.price_change_percentage_24h || 0)})` : '';
  const keyLine = [keyCoins.btc, keyCoins.eth, keyCoins.sol].filter(Boolean).map(formatCoin).join(' · ');
  const gainLine = gainers.map(formatCoin).join('、');
  const lossLine = losers.map(formatCoin).join('、');
  const sentiment = overview.fearGreed === null ? '' : ` · 恐惧贪婪 ${overview.fearGreed}/100`;

  return [
    '## 📈 市场快照\n',
    `> ${keyLine}`,
    `> 总市值 ${overview.totalMarketCapFmt} (${pct(overview.marketCapChange24h)}) · BTC 市占率 ${overview.btcDominance.toFixed(1)}%${sentiment}`,
    `> 领涨：${gainLine}`,
    `> 领跌：${lossLine}\n`,
  ].join('\n');
}

function renderCard(art) {
  const score      = art.score || 5;
  const titleZh    = art.title_zh || art.title;
  const titleEn    = art.lang === 'en' && art.title !== titleZh ? art.title : '';
  const summaryZh  = art.summary_zh || art.summary || '';
  const reason     = art.reason_zh || '';
  const background = art.background_zh || '';
  const source     = art.source || '';
  const platform   = art.platform || '';
  const url        = art.url || '';

  const parts = [];
  parts.push(`### [${titleZh}](${url})`);
  parts.push(`**来源** ${source} · ${platform} &nbsp;·&nbsp; **评分** ${score}/10`);
  if (titleEn) parts.push(`*${titleEn}*`);
  parts.push('');
  if (summaryZh) parts.push(summaryZh);
  if (reason)     parts.push(`\n💡 ${reason}`);
  if (background) parts.push(`\n📖 ${background}`);
  parts.push('\n---\n');

  return parts.join('\n') + '\n';
}
