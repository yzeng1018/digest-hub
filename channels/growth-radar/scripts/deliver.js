import nodemailer from 'nodemailer';

const GMAIL_PASS  = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const RECIPIENT   = process.env.DIGEST_RECIPIENT   || 'yzeng1018@gmail.com';
const SENDER      = 'yzeng1018@gmail.com';

function scoreColor(score) {
  if (score >= 9) return '#e03131';
  if (score >= 6) return '#e67700';
  return '#1971c2';
}

function usageBar(tokenUsage) {
  if (!tokenUsage || !tokenUsage.total) return '';
  const model  = tokenUsage.model || 'AI';
  const total  = tokenUsage.total.toLocaleString();
  return `<div style="margin-top:10px;padding:5px 14px;background:rgba(255,255,255,0.15);border-radius:20px;font-size:11px;color:rgba(255,255,255,0.85);display:inline-block;">🤖 ${model} &nbsp;·&nbsp; ${total} tokens</div>`;
}

function buildHtml(articles, dateStr, tokenUsage = {}) {
  const mustCount = articles.filter(a => a.score >= 9).length;
  const impCount  = articles.filter(a => a.score >= 6 && a.score < 9).length;

  const rows = articles.map(art => {
    const sc       = art.score || 5;
    const color    = scoreColor(sc);
    const label    = sc >= 9 ? '必读' : sc >= 6 ? '重要' : '一般';
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
  <td style="padding:14px 18px;border-bottom:1px solid #dee2e6;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="44" valign="top" style="padding-right:10px;">
        <div style="width:40px;height:40px;border-radius:8px;background:${color}22;text-align:center;
                    line-height:40px;font-size:17px;font-weight:800;color:${color};">${sc}</div>
      </td>
      <td valign="top">
        <div style="font-size:14px;font-weight:600;color:#212529;line-height:1.4;">
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
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;">
  <tr><td style="background:linear-gradient(135deg,#2f9e44,#1971c2);border-radius:12px 12px 0 0;padding:24px 20px;text-align:center;">
    <div style="font-size:20px;font-weight:800;color:#fff;">📡 Growth Radar</div>
    <div style="margin-top:4px;font-size:12px;color:rgba(255,255,255,0.8);">${dateStr} · 增长动态日报</div>
    ${usageBar(tokenUsage)}
    <div style="margin-top:10px;">
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

export async function deliver(markdown, articles, dateStr, tokenUsage = {}) {
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
  const html = buildHtml(articles, dateStr, tokenUsage);

  try {
    await transporter.sendMail({ from: SENDER, to: RECIPIENT, subject, html });
    console.log(`✉️  Growth Radar 已发送 → ${RECIPIENT}`);
  } catch (err) {
    console.log(`[ERROR] 邮件发送失败: ${err.message}`);
  }
}
