import nodemailer from 'nodemailer';

const GMAIL_PASS  = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const RECIPIENT   = process.env.DIGEST_RECIPIENT   || 'yzeng1018@gmail.com';
const SENDER      = 'yzeng1018@gmail.com';

function scoreColor(score) {
  if (score >= 8) return '#ff6b6b';
  if (score >= 6) return '#ffa94d';
  return '#74c0fc';
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

function buildHtml(articles, dateStr, tokenUsage = {}, tokenMetrics = {}) {
  const mustCount = articles.filter(a => a.score >= 8).length;
  const impCount  = articles.filter(a => a.score >= 6 && a.score < 8).length;

  const rows = articles.map(art => {
    const sc       = art.score || 5;
    const color    = scoreColor(sc);
    const label    = sc >= 8 ? '必读' : sc >= 6 ? '重要' : '一般';
    const titleZh  = art.title_zh || art.title;
    const titleEn  = art.lang === 'en' && art.title !== titleZh
      ? `<div style="font-size:11px;color:#868e96;margin-top:2px;font-style:italic;">${art.title}</div>` : '';
    const summary  = art.summary_zh || art.summary || '';
    const reason   = art.reason_zh
      ? `<div style="margin-top:6px;padding:5px 10px;background:#d3f9d8;border-radius:4px;font-size:12px;color:#2b8a3e;">💡 ${art.reason_zh}</div>` : '';
    const bg       = art.background_zh
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
  <tr><td style="background:linear-gradient(135deg,#2f9e44,#1971c2);border-radius:12px 12px 0 0;padding:28px 24px;text-align:center;">
    <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:0.5px;">📡 Growth Radar</div>
    <div style="margin-top:4px;font-size:12px;color:rgba(255,255,255,0.8);">${dateStr} · 增长动态日报</div>
    ${usageBar(tokenUsage, tokenMetrics)}
    <div style="margin-top:12px;">
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,107,107,0.25);color:#ff6b6b;font-size:12px;font-weight:600;">🔥 必读 ${mustCount}</span>
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,169,77,0.25);color:#ffa94d;font-size:12px;font-weight:600;margin-left:8px;">⚡ 重要 ${impCount}</span>
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,255,255,0.15);color:rgba(255,255,255,0.9);font-size:12px;margin-left:8px;">共 ${articles.length} 条</span>
    </div>
  </td></tr>
  <tr><td style="background:#fff;border-radius:0 0 12px 12px;border:1px solid #dee2e6;border-top:none;">
    <table width="100%" cellpadding="0" cellspacing="0">
      ${rows}
      <tr><td style="padding:12px;text-align:center;background:#f8f9fa;border-radius:0 0 12px 12px;">
        <div style="font-size:11px;color:#adb5bd;">Growth Radar 自动生成 · 来源：X / Blog / Newsletter</div>
        <div style="font-size:11px;color:#adb5bd;margin-top:3px;">监控：@lennysan @bbalfour @andrewchen @gustaf @Kyle_Poyar 等23位增长专家</div>
      </td></tr>
    </table>
  </td></tr>
</table>
</td></tr></table>
</body></html>`;
}

export async function deliver(markdown, articles, dateStr, tokenUsage = {}, tokenMetrics = {}) {
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

  const subject = `📡 Growth Radar · ${dateStr}`;
  const html = buildHtml(articles, dateStr, tokenUsage, tokenMetrics);

  try {
    await transporter.sendMail({ from: SENDER, to: RECIPIENT, subject, html });
    console.log(`✉️  Growth Radar 已发送 → ${RECIPIENT}`);
  } catch (err) {
    console.log(`[ERROR] 邮件发送失败: ${err.message}`);
  } finally {
    transporter.close();
  }
}
