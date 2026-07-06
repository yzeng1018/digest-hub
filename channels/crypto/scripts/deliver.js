import nodemailer from 'nodemailer';

const GMAIL_PASS  = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const RECIPIENT   = process.env.DIGEST_RECIPIENT   || 'yzeng1018@gmail.com';
const SENDER      = 'yzeng1018@gmail.com';

function scoreColor(score) {
  if (score >= 8) return '#ff6b6b';
  if (score >= 6) return '#ffa94d';
  return '#74c0fc';
}

function fmtPct(value) {
  if (value === null || value === undefined) return '—';
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function changeColor(value) {
  return value >= 0 ? '#2f9e44' : '#e03131';
}

function marketSnapshot(data) {
  if (!data) return '';
  const { overview, keyCoins, gainers, losers } = data;
  const keyCards = [keyCoins.btc, keyCoins.eth, keyCoins.sol]
    .filter(Boolean)
    .map(coin => {
      const change = coin.price_change_percentage_24h || 0;
      return `<td width="33.33%" style="padding:10px 6px;text-align:center;">
        <div style="font-size:11px;color:#868e96;">${coin.symbol.toUpperCase()}</div>
        <div style="margin-top:3px;font-size:17px;font-weight:800;color:#212529;">${coin.priceFmt}</div>
        <div style="margin-top:2px;font-size:12px;font-weight:700;color:${changeColor(change)};">${fmtPct(change)}</div>
      </td>`;
    }).join('');
  const mover = coin => {
    const change = coin.price_change_percentage_24h || 0;
    return `<span style="display:inline-block;margin:2px 4px 2px 0;padding:3px 7px;border-radius:4px;background:#f1f3f5;font-size:11px;color:#495057;">
      ${coin.symbol.toUpperCase()} <strong style="color:${changeColor(change)};">${fmtPct(change)}</strong>
    </span>`;
  };
  const sentiment = overview.fearGreed === null
    ? ''
    : ` &nbsp;·&nbsp; 恐惧贪婪 <strong>${overview.fearGreed}/100</strong>`;

  return `<tr><td style="padding:16px 20px;border-bottom:1px solid #dee2e6;background:#fff9db;">
    <div style="font-size:14px;font-weight:700;color:#e67700;margin-bottom:8px;">📈 市场快照</div>
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #ffe8a1;border-radius:8px;"><tr>${keyCards}</tr></table>
    <div style="margin-top:9px;font-size:12px;color:#495057;line-height:1.6;">
      总市值 <strong>${overview.totalMarketCapFmt}</strong>
      <strong style="color:${changeColor(overview.marketCapChange24h)};">${fmtPct(overview.marketCapChange24h)}</strong>
      &nbsp;·&nbsp; BTC 市占率 <strong>${overview.btcDominance.toFixed(1)}%</strong>${sentiment}
    </div>
    <div style="margin-top:7px;font-size:11px;color:#868e96;">领涨 ${gainers.map(mover).join('')} &nbsp; 领跌 ${losers.map(mover).join('')}</div>
  </td></tr>`;
}

function usageBar(tokenUsage, tokenMetrics = {}) {
  if (!tokenUsage || !tokenUsage.model) return '';
  const model = tokenUsage.model;
  const total = tokenUsage.total || 0;
  const tokenStr = total
    ? `↑ ${(tokenUsage.prompt||0).toLocaleString()} &nbsp;↓ ${(tokenUsage.completion||0).toLocaleString()} &nbsp;共 ${total.toLocaleString()} tokens`
    : 'token 数据不可用';
  let perfHtml = '';
  if (tokenMetrics && tokenMetrics.perfScore !== undefined && tokenMetrics.perfScore > 0) {
    const ps    = tokenMetrics.perfScore;
    const pr    = Math.round((tokenMetrics.parseRate || 0) * 100);
    const tr    = Math.round((tokenMetrics.translationRate || 0) * 100);
    const ss    = (tokenMetrics.scoreSpread || 0).toFixed(1);
    const color = ps >= 8 ? '#69db7c' : ps >= 6 ? '#ffa94d' : '#ff6b6b';
    perfHtml = ` &nbsp;·&nbsp; <span style="color:${color};font-weight:700;">评分 ${ps}/10</span> (解析率 ${pr}% · 翻译率 ${tr}% · 区分度 ${ss}σ)`;
  }
  return `<div style="margin-top:10px;padding:6px 14px;background:rgba(255,255,255,0.15);border-radius:8px;font-size:11px;color:rgba(255,255,255,0.85);display:inline-block;">🤖 ${model} &nbsp;·&nbsp; ${tokenStr}${perfHtml}</div>`;
}

function buildHtml(articles, dateStr, tokenUsage = {}, tokenMetrics = {}, marketData = null) {
  const mustCount = articles.filter(a => a.score >= 8).length;
  const impCount  = articles.filter(a => a.score >= 6 && a.score < 8).length;

  const rows = articles.map(art => {
    const sc     = art.score || 5;
    const color  = scoreColor(sc);
    const label  = sc >= 8 ? '必读' : sc >= 6 ? '重要' : '一般';
    const titleZh = art.title_zh || art.title;
    const titleEn = art.lang === 'en' && art.title !== titleZh
      ? `<div style="font-size:12px;color:#868e96;margin-top:3px;">${art.title}</div>` : '';
    const summary = art.summary_zh || art.summary || '';
    const reason  = art.reason_zh
      ? `<div style="margin-top:6px;padding:5px 10px;background:#d4edda;border-radius:4px;font-size:12px;color:#155724;">💡 ${art.reason_zh}</div>` : '';
    const bg      = art.background_zh
      ? `<div style="margin-top:5px;padding:5px 10px;background:#e8f4fd;border-radius:4px;font-size:12px;color:#1c7ed6;">📖 ${art.background_zh}</div>` : '';

    return `
<tr>
  <td style="padding:16px 20px;border-bottom:1px solid #dee2e6;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="46" valign="top" style="padding-right:12px;">
        <div style="width:42px;height:42px;border-radius:8px;background:${color}22;text-align:center;
                    line-height:42px;font-size:18px;font-weight:800;color:${color};">${sc}</div>
      </td>
      <td valign="top">
        <div style="font-size:15px;font-weight:600;color:#212529;line-height:1.4;">
          <a href="${art.url}" style="color:#212529;text-decoration:none;">${titleZh}</a>
        </div>
        ${titleEn}
        <div style="margin-top:5px;">
          <span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:700;color:${color};background:${color}22;">${label}</span>
          <span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;color:#6c757d;background:#f8f9fa;border:1px solid #dee2e6;margin-left:4px;">${art.source}</span>
          <span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;color:#6c757d;background:#f8f9fa;border:1px solid #dee2e6;margin-left:4px;">${art.platform}</span>
        </div>
        <div style="margin-top:7px;font-size:13px;color:#495057;line-height:1.6;">${summary}</div>
        ${reason}${bg}
      </td>
    </tr></table>
  </td>
</tr>`;
  }).join('');

  return `<!DOCTYPE html><html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8f9fa;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;padding:20px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">
  <tr><td style="background:linear-gradient(135deg,#f59f00,#e67700);border-radius:12px 12px 0 0;padding:28px 24px;text-align:center;">
    <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:0.5px;">每日加密情报</div>
    <div style="margin-top:6px;font-size:13px;color:rgba(255,255,255,0.8);">${dateStr}</div>
    ${usageBar(tokenUsage, tokenMetrics)}
    <div style="margin-top:12px;">
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,107,107,0.25);color:#ff6b6b;font-size:12px;font-weight:600;">🔥 必读 ${mustCount}</span>
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,255,255,0.2);color:#fff;font-size:12px;font-weight:600;margin-left:8px;">⚡ 重要 ${impCount}</span>
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,255,255,0.15);color:rgba(255,255,255,0.9);font-size:12px;margin-left:8px;">共 ${articles.length} 条</span>
    </div>
  </td></tr>
  <tr><td style="background:#fff;border-radius:0 0 12px 12px;border:1px solid #dee2e6;border-top:none;">
    <table width="100%" cellpadding="0" cellspacing="0">
      ${marketSnapshot(marketData)}
      ${rows}
      <tr><td style="padding:12px;text-align:center;background:#f8f9fa;border-radius:0 0 12px 12px;">
        <div style="font-size:11px;color:#adb5bd;">AI 自动生成 · 来源：X / Blog</div>
      </td></tr>
    </table>
  </td></tr>
</table>
</td></tr></table>
</body></html>`;
}

export async function deliver(markdown, articles, dateStr, tokenUsage = {}, tokenMetrics = {}, marketData = null) {
  if (!GMAIL_PASS) {
    console.log('[WARN] GMAIL_APP_PASSWORD 未设置，跳过邮件');
    return;
  }

  const smtpHost = process.env.SMTP_HOST || 'smtp.gmail.com';
  const transporter = nodemailer.createTransport({
    host: smtpHost,
    port: 465,
    secure: true,
    auth: { user: SENDER, pass: GMAIL_PASS },
    connectionTimeout: 60000,
    greetingTimeout: 60000,
    socketTimeout: 60000,
    tls: { servername: 'smtp.gmail.com', rejectUnauthorized: false },
  });

  const btc = marketData?.keyCoins?.btc;
  const marketSuffix = btc ? ` · BTC ${btc.priceFmt} ${fmtPct(btc.price_change_percentage_24h || 0)}` : '';
  const subject = `每日加密情报 · ${dateStr}${marketSuffix}`;
  const html = buildHtml(articles, dateStr, tokenUsage, tokenMetrics, marketData);

  try {
    await transporter.sendMail({ from: SENDER, to: RECIPIENT, subject, html });
    console.log(`✉️  邮件已发送 → ${RECIPIENT}`);
  } catch (err) {
    console.log(`[ERROR] 邮件发送失败: ${err.message}`);
  } finally {
    transporter.close();
  }
}
