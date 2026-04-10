export function render(articles, dateStr, weekStr, tokenUsage = {}) {
  const mustRead  = articles.filter(a => a.score >= 8);
  const important = articles.filter(a => a.score >= 6 && a.score < 8);

  const tokenLine = tokenUsage.total
    ? `*🤖 ${tokenUsage.model || 'AI'} · ${tokenUsage.total.toLocaleString()} tokens*\n\n`
    : '';

  const lines = [];
  lines.push(`# Growth Weekly · ${weekStr}\n`);
  lines.push(`> 本周精读 **${articles.length}** 篇 · 🔥 强烈推荐 **${mustRead.length}** · ⚡ 值得精读 **${important.length}**\n`);
  lines.push('---\n');

  if (mustRead.length) {
    lines.push('## 🔥 本周强烈推荐\n');
    mustRead.forEach((a, i) => lines.push(renderCard(a, i + 1)));
  }

  if (important.length) {
    lines.push('## ⚡ 值得精读\n');
    important.forEach((a, i) => lines.push(renderCard(a, mustRead.length + i + 1)));
  }

  lines.push('---\n');
  lines.push(tokenLine);
  lines.push('*Growth Weekly 严选 · 来源：X / Blog / Newsletter · 每周六发送*\n');

  return lines.join('\n');
}

function renderCard(art, index) {
  const score      = art.score || 5;
  const titleZh    = art.title_zh || art.title;
  const titleEn    = art.lang === 'en' && art.title !== titleZh ? art.title : '';
  const summaryZh  = art.summary_zh || art.summary || '';
  const reason     = art.reason_zh || '';
  const background = art.background_zh || '';
  const source     = art.source || '';
  const url        = art.url || '';

  const parts = [];
  parts.push(`### ${index}. [${titleZh}](${url})`);
  parts.push(`**来源** ${source} &nbsp;·&nbsp; **评分** ${score}/10`);
  if (titleEn) parts.push(`*${titleEn}*`);
  parts.push('');
  if (reason)     parts.push(`> 💡 **为什么精读：** ${reason}`);
  parts.push('');
  if (summaryZh) parts.push(summaryZh);
  if (background) parts.push(`\n📖 ${background}`);
  parts.push('\n---\n');

  return parts.join('\n') + '\n';
}
