export function render(articles, dateStr, tokenUsage = {}) {
  const mustRead  = articles.filter(a => a.score >= 9);
  const important = articles.filter(a => a.score >= 6 && a.score < 9);
  const general   = articles.filter(a => a.score < 6);

  const tokenLine = tokenUsage.total
    ? `*🤖 ${tokenUsage.model || 'AI'} · ${tokenUsage.total.toLocaleString()} tokens*\n\n`
    : '';

  const lines = [];
  lines.push(`# Growth Radar · ${dateStr}\n`);
  lines.push(`> 🔥 必读 **${mustRead.length}** &nbsp; ⚡ 重要 **${important.length}** &nbsp; 📌 一般 **${general.length}** &nbsp;·&nbsp; 共 **${articles.length}** 条\n`);
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
  lines.push('*Growth Radar 自动生成 · 来源：X / Blog / Newsletter*\n');

  return lines.join('\n');
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
