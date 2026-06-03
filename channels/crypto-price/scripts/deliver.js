import { execFile } from 'child_process';
import { promisify } from 'util';
import { writeFile, unlink } from 'fs/promises';
import { tmpdir } from 'os';
import { join } from 'path';

const execFileAsync = promisify(execFile);

const GMAIL_PASS = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const RECIPIENT  = process.env.DIGEST_RECIPIENT || 'yzeng1018@gmail.com';
const SENDER     = 'yzeng1018@gmail.com';

function fmtPct(n) {
  if (n === null || n === undefined) return '—';
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
}

function pctColor(n) {
  if (!n) return '#868e96';
  return n >= 0 ? '#51cf66' : '#ff6b6b';
}

function fgiBar(value) {
  const color = value >= 75 ? '#51cf66' : value >= 55 ? '#94d82d' : value >= 45 ? '#ffd43b' : value >= 25 ? '#ff922b' : '#ff6b6b';
  const label = value >= 75 ? '极度贪婪' : value >= 55 ? '贪婪' : value >= 45 ? '中性' : value >= 25 ? '恐惧' : '极度恐惧';
  const pct   = value + '%';
  return `
    <div style="margin-top:4px;">
      <div style="display:flex;justify-content:space-between;font-size:11px;color:rgba(255,255,255,0.7);margin-bottom:3px;">
        <span>恐惧贪婪指数</span>
        <span style="color:${color};font-weight:700;">${value}/100 · ${label}</span>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:4px;height:6px;overflow:hidden;">
        <div style="width:${pct};background:${color};height:100%;border-radius:4px;"></div>
      </div>
    </div>`;
}

function usageBar(tokenUsage) {
  if (!tokenUsage || !tokenUsage.model) return '';
  const total = tokenUsage.total || 0;
  const tokenStr = total
    ? `↑ ${(tokenUsage.prompt || 0).toLocaleString()} &nbsp;↓ ${(tokenUsage.completion || 0).toLocaleString()} &nbsp;共 ${total.toLocaleString()} tokens`
    : 'token 数据不可用';
  return `<div style="margin-top:10px;padding:6px 14px;background:rgba(255,255,255,0.12);border-radius:8px;font-size:11px;color:rgba(255,255,255,0.75);display:inline-block;">🤖 ${tokenUsage.model} &nbsp;·&nbsp; ${tokenStr}</div>`;
}

function coinRow(c, showArrow = true) {
  const chg = c.price_change_percentage_24h || 0;
  const color = pctColor(chg);
  const arrow = chg >= 0 ? '▲' : '▼';
  return `
<tr style="border-bottom:1px solid #2d2d3d;">
  <td style="padding:10px 8px;color:#c9d1d9;font-size:13px;font-weight:600;">${(c.symbol || '').toUpperCase()}</td>
  <td style="padding:10px 8px;color:#e6edf3;font-size:13px;">${c.name || ''}</td>
  <td style="padding:10px 8px;color:#e6edf3;font-size:13px;text-align:right;">${c.priceFmt || '—'}</td>
  <td style="padding:10px 8px;font-size:13px;font-weight:700;text-align:right;color:${color};">${showArrow ? arrow + ' ' : ''}${fmtPct(chg)}</td>
  <td style="padding:10px 8px;color:#8b949e;font-size:12px;text-align:right;">${c.capFmt || '—'}</td>
</tr>`;
}

function insightSection(insight) {
  if (!insight || Object.keys(insight).length === 0) return '';

  const items = [
    { key: 'market_structure', icon: '📊', label: '市场结构' },
    { key: 'movers_insight',   icon: '🎯', label: '主力异动' },
    { key: 'sector_rotation',  icon: '🔄', label: '赛道轮动' },
    { key: 'btc_dominance',    icon: '₿',  label: 'BTC主导权' },
    { key: 'risk_warning',     icon: '⚠️', label: '风险雷达' },
    { key: 'watch_point',      icon: '👁️', label: '今日盯盘' },
  ];

  const rows = items
    .filter(({ key }) => insight[key])
    .map(({ icon, label, key }) => `
      <tr>
        <td style="padding:10px 14px;border-bottom:1px solid #2d2d3d;vertical-align:top;width:110px;">
          <span style="font-size:12px;color:#8b949e;">${icon} ${label}</span>
        </td>
        <td style="padding:10px 14px;border-bottom:1px solid #2d2d3d;font-size:13px;color:#c9d1d9;line-height:1.6;">${insight[key]}</td>
      </tr>`).join('');

  return `
<tr><td style="padding:0 0 20px 0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#161b22;border-radius:10px;border:1px solid #30363d;overflow:hidden;">
    <tr>
      <td colspan="2" style="padding:14px 16px;background:linear-gradient(90deg,#1f2a3d,#161b22);border-bottom:1px solid #30363d;">
        <div style="font-size:15px;font-weight:700;color:#58a6ff;">🧠 顶级交易员视角</div>
        ${insight.summary ? `<div style="margin-top:6px;font-size:13px;color:#ffd700;font-weight:600;">${insight.summary}</div>` : ''}
      </td>
    </tr>
    ${rows}
  </table>
</td></tr>`;
}

function buildHtml(data, insight, dateStr, tokenUsage = {}) {
  const { overview, keyCoins, gainers, losers, volumeAnomalies, trending } = data;
  const { btc, eth, sol } = keyCoins;

  const bigCoinBlock = (c, label) => {
    if (!c) return '';
    const chg = c.price_change_percentage_24h || 0;
    const color = pctColor(chg);
    return `
      <td style="text-align:center;padding:0 20px;">
        <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:2px;">${label}</div>
        <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;">${c.priceFmt}</div>
        <div style="font-size:14px;font-weight:700;color:${color};">${chg >= 0 ? '▲' : '▼'} ${fmtPct(chg)}</div>
      </td>`;
  };

  const volRows = volumeAnomalies.map(c => {
    const chg = c.price_change_percentage_24h || 0;
    return `
    <tr style="border-bottom:1px solid #2d2d3d;">
      <td style="padding:9px 8px;color:#e6edf3;font-size:13px;font-weight:600;">${(c.symbol || '').toUpperCase()}</td>
      <td style="padding:9px 8px;color:#c9d1d9;font-size:13px;">${c.name || ''}</td>
      <td style="padding:9px 8px;color:#ffd700;font-size:13px;font-weight:700;text-align:right;">${(c.volumeRatio * 100).toFixed(1)}%</td>
      <td style="padding:9px 8px;font-weight:700;text-align:right;color:${pctColor(chg)};font-size:13px;">${fmtPct(chg)}</td>
      <td style="padding:9px 8px;color:#8b949e;font-size:12px;text-align:right;">${c.priceFmt}</td>
    </tr>`;
  }).join('');

  const trendingHtml = trending.length
    ? trending.map(c => `<span style="display:inline-block;margin:3px 4px;padding:3px 10px;background:#1f2a3d;border:1px solid #30363d;border-radius:20px;font-size:12px;color:#58a6ff;">${c.symbol} ${c.name}</span>`).join('')
    : '';

  return `<!DOCTYPE html><html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:-apple-system,'PingFang SC','Microsoft YaHei',monospace;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0d1117;padding:20px 0;">
<tr><td align="center">
<table width="660" cellpadding="0" cellspacing="0" style="max-width:660px;width:100%;">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#0f3460,#1a1a2e,#16213e);border-radius:12px 12px 0 0;padding:28px 24px;">
    <div style="text-align:center;margin-bottom:18px;">
      <div style="font-size:11px;letter-spacing:3px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:6px;">Crypto Price Radar</div>
      <div style="font-size:20px;font-weight:800;color:#fff;">加密市场价格雷达</div>
      <div style="margin-top:4px;font-size:12px;color:rgba(255,255,255,0.5);">${dateStr}</div>
    </div>
    <!-- Key prices -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0;border-top:1px solid rgba(255,255,255,0.1);border-bottom:1px solid rgba(255,255,255,0.1);padding:16px 0;">
    <tr>
      ${bigCoinBlock(btc, 'BTC')}
      <td style="width:1px;background:rgba(255,255,255,0.1);"></td>
      ${bigCoinBlock(eth, 'ETH')}
      <td style="width:1px;background:rgba(255,255,255,0.1);"></td>
      ${bigCoinBlock(sol, 'SOL')}
    </tr>
    </table>
    <!-- Market cap row -->
    <div style="text-align:center;font-size:12px;color:rgba(255,255,255,0.6);">
      总市值 <strong style="color:#fff;">${overview.totalMarketCapFmt}</strong>
      <span style="color:${pctColor(overview.marketCapChange24h)};font-weight:700;margin-left:6px;">${fmtPct(overview.marketCapChange24h)}</span>
      &nbsp;·&nbsp;
      BTC主导 <strong style="color:#f5a623;">${overview.btcDominance.toFixed(1)}%</strong>
    </div>
    ${overview.fearGreed ? fgiBar(overview.fearGreed.value) : ''}
    <div style="text-align:center;margin-top:12px;">${usageBar(tokenUsage)}</div>
  </td></tr>

  <!-- Body -->
  <tr><td style="background:#161b22;border:1px solid #30363d;border-top:none;border-radius:0 0 12px 12px;padding:20px;">
  <table width="100%" cellpadding="0" cellspacing="0">

    <!-- AI Insight -->
    ${insightSection(insight)}

    <!-- Gainers & Losers side by side -->
    <tr><td style="padding-bottom:20px;">
      <table width="100%" cellpadding="0" cellspacing="0">
      <tr valign="top">
        <!-- Gainers -->
        <td width="49%" style="padding-right:8px;">
          <div style="background:#0d1117;border-radius:8px;border:1px solid #30363d;overflow:hidden;">
            <div style="padding:10px 12px;background:#1a2a1a;border-bottom:1px solid #30363d;">
              <span style="font-size:13px;font-weight:700;color:#51cf66;">🚀 Top 涨幅</span>
              <span style="font-size:11px;color:#8b949e;margin-left:6px;">Top 100市值</span>
            </div>
            <table width="100%" cellpadding="0" cellspacing="0">
              ${gainers.slice(0, 7).map(c => coinRow(c)).join('')}
            </table>
          </div>
        </td>
        <!-- Losers -->
        <td width="49%" style="padding-left:8px;">
          <div style="background:#0d1117;border-radius:8px;border:1px solid #30363d;overflow:hidden;">
            <div style="padding:10px 12px;background:#2a1a1a;border-bottom:1px solid #30363d;">
              <span style="font-size:13px;font-weight:700;color:#ff6b6b;">📉 Top 跌幅</span>
              <span style="font-size:11px;color:#8b949e;margin-left:6px;">Top 100市值</span>
            </div>
            <table width="100%" cellpadding="0" cellspacing="0">
              ${losers.slice(0, 7).map(c => coinRow(c)).join('')}
            </table>
          </div>
        </td>
      </tr>
      </table>
    </td></tr>

    <!-- Volume Anomalies -->
    <tr><td style="padding-bottom:20px;">
      <div style="background:#0d1117;border-radius:8px;border:1px solid #30363d;overflow:hidden;">
        <div style="padding:10px 14px;background:#1a1a0d;border-bottom:1px solid #30363d;">
          <span style="font-size:13px;font-weight:700;color:#ffd700;">🔊 异常放量</span>
          <span style="font-size:11px;color:#8b949e;margin-left:6px;">量/市值比最高，代表资金异常活跃</span>
        </div>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr style="border-bottom:1px solid #2d2d3d;">
            <th style="padding:6px 8px;text-align:left;font-size:11px;color:#8b949e;font-weight:400;">代码</th>
            <th style="padding:6px 8px;text-align:left;font-size:11px;color:#8b949e;font-weight:400;">名称</th>
            <th style="padding:6px 8px;text-align:right;font-size:11px;color:#8b949e;font-weight:400;">量/市值</th>
            <th style="padding:6px 8px;text-align:right;font-size:11px;color:#8b949e;font-weight:400;">24h</th>
            <th style="padding:6px 8px;text-align:right;font-size:11px;color:#8b949e;font-weight:400;">价格</th>
          </tr>
          ${volRows}
        </table>
      </div>
    </td></tr>

    <!-- Trending -->
    ${trendingHtml ? `
    <tr><td style="padding-bottom:20px;">
      <div style="background:#0d1117;border-radius:8px;border:1px solid #30363d;padding:12px 14px;">
        <div style="font-size:13px;font-weight:700;color:#ff7b7b;margin-bottom:8px;">🔥 CoinGecko 热搜榜</div>
        <div>${trendingHtml}</div>
      </div>
    </td></tr>` : ''}

    <!-- Footer -->
    <tr><td style="text-align:center;padding-top:8px;">
      <div style="font-size:11px;color:#484f58;">AI 自动生成 · 数据来源：CoinGecko · ${data.fetchedAt.slice(0, 19).replace('T', ' ')} UTC</div>
    </td></tr>

  </table>
  </td></tr>

</table>
</td></tr></table>
</body></html>`;
}

export async function deliver(data, insight, markdown, dateStr, tokenUsage = {}) {
  if (!GMAIL_PASS) {
    throw new Error('GMAIL_APP_PASSWORD 未设置，拒绝静默跳过邮件发送');
  }

  const btcPrice = data.keyCoins.btc?.priceFmt || '';
  const btcChg   = data.keyCoins.btc?.price_change_percentage_24h;
  const chgStr   = btcChg !== undefined && btcChg !== null
    ? ` · BTC ${btcChg >= 0 ? '▲' : '▼'} ${Math.abs(btcChg).toFixed(2)}%`
    : '';
  const subject = `加密价格雷达 · ${dateStr}${btcPrice ? ' · BTC ' + btcPrice : ''}${chgStr}`;
  const html    = buildHtml(data, insight, dateStr, tokenUsage);

  // Build RFC 2822 email payload
  const subjectEncoded = `=?UTF-8?B?${Buffer.from(subject).toString('base64')}?=`;
  const payload = [
    `From: ${SENDER}`,
    `To: ${RECIPIENT}`,
    `Subject: ${subjectEncoded}`,
    'MIME-Version: 1.0',
    'Content-Type: text/html; charset=UTF-8',
    'Content-Transfer-Encoding: base64',
    '',
    Buffer.from(html).toString('base64'),
  ].join('\r\n');

  const tmpFile = join(tmpdir(), `crypto-price-mail-${Date.now()}.eml`);
  await writeFile(tmpFile, payload, 'utf8');

  try {
    const smtpUrl = `smtps://smtp.gmail.com:465`;
    await execFileAsync('curl', [
      '--silent', '--show-error', '--max-time', '60',
      '--url', smtpUrl,
      '--ssl-reqd',
      '--mail-from', SENDER,
      '--mail-rcpt', RECIPIENT,
      '--user', `${SENDER}:${GMAIL_PASS}`,
      '--upload-file', tmpFile,
    ]);
    console.log(`✉️  邮件已发送 → ${RECIPIENT}`);
  } catch (err) {
    const msg = err.stderr || err.message;
    console.log(`[ERROR] 邮件发送失败: ${msg}`);
    throw new Error(msg);
  } finally {
    await unlink(tmpFile).catch(() => {});
  }
}
