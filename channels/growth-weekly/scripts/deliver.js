import nodemailer from 'nodemailer';

const GMAIL_PASS  = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const RECIPIENT   = process.env.DIGEST_RECIPIENT   || 'yzeng1018@gmail.com';
const SENDER      = 'yzeng1018@gmail.com';

function scoreColor(score) {
  if (score >= 8) return '#e03131';
  return '#e67700';
}

function estimateReadTime(text) {
  const words = (text || '').split(/\s+/).length;
  return Math.max(5, Math.round(words / 200) * 5);
}

function buildHtml(articles, dateStr, weekStr, tokenUsage = {}) {
  const mustCount = articles.filter(a => a.score >= 8).length;
  const impCount  = articles.filter(a => a.score >= 6 && a.score < 8).length;

  const usageStr = tokenUsage.model
    ? `<div style="margin-top:8px;font-size:11px;color:rgba(255,255,255,0.6);">🤖 ${tokenUsage.model} · ${tokenUsage.total ? tokenUsage.total.toLocaleString() + ' tokens' : '—'}</div>`
    : '';

  const rows = articles.map((art, idx) => {
    const sc       = art.score || 5;
    const color    = scoreColor(sc);
    const label    = sc >= 8 ? '强烈推荐' : '值得精读';
    const titleZh  = art.title_zh || art.title;
    const titleEn  = art.lang === 'en' && art.title !== titleZh
      ? `<div style="font-size:11px;color:#868e96;margin-top:3px;font-style:italic;">${art.title}</div>` : '';
    const summary  = art.summary_zh || art.summary || '';
    const reason   = art.reason_zh
      ? `<div style="margin-top:8px;padding:8px 12px;background:#fff9db;border-left:3px solid #fab005;border-radius:0 4px 4px 0;font-size:13px;color:#664d03;line-height:1.5;"><strong>💡 为什么精读：</strong> ${art.reason_zh}</div>` : '';
    const bg       = art.background_zh
      ? `<div style="margin-top:6px;padding:7px 12px;background:#f1f3f5;border-radius:4px;font-size:12px;color:#495057;line-height:1.6;">📖 ${art.background_zh}</div>` : '';

    return `
<tr>
  <td style="padding:20px 24px;border-bottom:2px solid #f1f3f5;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="36" valign="top" style="padding-right:14px;">
        <div style="width:32px;height:32px;border-radius:50%;background:${color};text-align:center;
                    line-height:32px;font-size:13px;font-weight:800;color:#fff;">${idx + 1}</div>
      </td>
      <td valign="top">
        <div style="margin-bottom:4px;">
          <span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700;color:${color};background:${color}18;">${label}</span>
          <span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:11px;color:#868e96;background:#f8f9fa;margin-left:6px;">${art.source}</span>
          <span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:11px;color:#868e96;background:#f8f9fa;margin-left:6px;">评分 ${sc}/10</span>
        </div>
        <div style="font-size:16px;font-weight:700;color:#212529;line-height:1.4;margin-top:6px;">
          <a href="${art.url}" style="color:#212529;text-decoration:none;">${titleZh}</a>
        </div>
        ${titleEn}
        ${reason}
        <div style="margin-top:10px;font-size:13px;color:#495057;line-height:1.7;">${summary}</div>
        ${bg}
        <div style="margin-top:10px;">
          <a href="${art.url}" style="display:inline-block;padding:6px 14px;background:#212529;color:#fff;font-size:12px;font-weight:600;border-radius:4px;text-decoration:none;">阅读全文 →</a>
        </div>
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
  <!-- Header -->
  <tr><td style="background:#212529;border-radius:12px 12px 0 0;padding:28px 24px;">
    <div style="font-size:11px;font-weight:600;letter-spacing:2px;color:#adb5bd;text-transform:uppercase;">Growth Weekly</div>
    <div style="font-size:24px;font-weight:800;color:#fff;margin-top:6px;">本周增长精读</div>
    <div style="margin-top:4px;font-size:12px;color:#868e96;">${weekStr}</div>
    ${usageStr}
    <div style="margin-top:14px;padding-top:14px;border-top:1px solid #343a40;">
      <span style="display:inline-block;padding:3px 12px;border-radius:20px;background:#e03131;color:#fff;font-size:12px;font-weight:700;">🔥 强烈推荐 ${mustCount} 篇</span>
      <span style="display:inline-block;padding:3px 12px;border-radius:20px;background:#e67700;color:#fff;font-size:12px;font-weight:700;margin-left:8px;">⚡ 值得精读 ${impCount} 篇</span>
      <div style="margin-top:8px;font-size:11px;color:#6c757d;">共从本周 1000+ 条内容中严选 ${articles.length} 篇</div>
    </div>
  </td></tr>
  <!-- Content -->
  <tr><td style="background:#fff;border-radius:0 0 12px 12px;border:1px solid #dee2e6;border-top:none;">
    <table width="100%" cellpadding="0" cellspacing="0">
      ${rows}
      <tr><td style="padding:16px 24px;background:#f8f9fa;border-radius:0 0 12px 12px;text-align:center;">
        <div style="font-size:11px;color:#adb5bd;">Growth Weekly · 每周六 09:00 发送</div>
        <div style="font-size:11px;color:#adb5bd;margin-top:2px;">严选来源：Lenny's Newsletter · andrewchen.com · Reforge · First Round Review 等</div>
      </td></tr>
    </table>
  </td></tr>
</table>
</td></tr></table>
</body></html>`;
}

export async function deliver(markdown, articles, dateStr, weekStr, tokenUsage = {}) {
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

  const subject = `📚 Growth Weekly · ${weekStr}`;
  const html = buildHtml(articles, dateStr, weekStr, tokenUsage);

  try {
    await transporter.sendMail({ from: SENDER, to: RECIPIENT, subject, html });
    console.log(`✉️  Growth Weekly 已发送 → ${RECIPIENT}`);
  } catch (err) {
    console.log(`[ERROR] 邮件发送失败: ${err.message}`);
  }
}
