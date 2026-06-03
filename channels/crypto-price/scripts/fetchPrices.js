import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

const COINGECKO_BASE = 'https://api.coingecko.com/api/v3';
const FGI_URL = 'https://api.alternative.me/fng/';

async function curlGet(url, extraHeaders = []) {
  const args = [
    '-s', '--max-time', '20', '-L',
    '-H', 'Accept: application/json',
    ...extraHeaders.flatMap(h => ['-H', h]),
  ];
  if (process.env.COINGECKO_API_KEY) {
    args.push('-H', `x-cg-demo-api-key: ${process.env.COINGECKO_API_KEY}`);
  }
  args.push(url);
  const { stdout } = await execFileAsync('curl', args, { maxBuffer: 4 * 1024 * 1024 });
  const text = stdout.trim();
  if (!text) throw new Error(`Empty response: ${url}`);
  const json = JSON.parse(text);
  if (json.status?.error_code === 429) {
    throw Object.assign(new Error(`Rate limited: ${url}`), { status: 429 });
  }
  return json;
}

async function fetchWithRetry(url, retries = 3) {
  for (let i = 0; i <= retries; i++) {
    try {
      return await curlGet(url);
    } catch (err) {
      if (err.status === 429) {
        const wait = 5000 * (i + 1);
        console.log(`  [CoinGecko] 被限速，等待 ${wait / 1000}s…`);
        await new Promise(r => setTimeout(r, wait));
        continue;
      }
      if (i === retries) throw err;
      await new Promise(r => setTimeout(r, 2000));
    }
  }
}

function fmtPrice(p) {
  if (!p && p !== 0) return 'N/A';
  if (p >= 10000) return '$' + Math.round(p).toLocaleString('en-US');
  if (p >= 1)     return '$' + p.toFixed(2);
  if (p >= 0.01)  return '$' + p.toFixed(4);
  return '$' + p.toFixed(6);
}

function fmtCap(n) {
  if (!n) return 'N/A';
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9)  return `$${(n / 1e9).toFixed(1)}B`;
  return `$${(n / 1e6).toFixed(0)}M`;
}

function processData({ globalData, markets, trending, fgi }) {
  const gd = globalData.data || {};
  const totalMarketCap = gd.total_market_cap?.usd || 0;
  const marketCapChange24h = gd.market_cap_change_percentage_24h_usd || 0;
  const btcDominance = gd.market_cap_percentage?.btc || 0;
  const ethDominance = gd.market_cap_percentage?.eth || 0;

  const sortedByChange = [...markets].sort(
    (a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0)
  );

  const gainers = sortedByChange
    .filter(c => (c.price_change_percentage_24h || 0) > 0)
    .slice(0, 7);
  const losers = [...sortedByChange]
    .filter(c => (c.price_change_percentage_24h || 0) < 0)
    .reverse()
    .slice(0, 7);

  // Volume anomalies: volume / market cap ratio — signals unusual activity
  const volumeAnomalies = markets
    .map(c => ({ ...c, volumeRatio: (c.total_volume || 0) / (c.market_cap || 1) }))
    .sort((a, b) => b.volumeRatio - a.volumeRatio)
    .slice(0, 5);

  const btc = markets.find(c => c.id === 'bitcoin') || null;
  const eth = markets.find(c => c.id === 'ethereum') || null;
  const sol = markets.find(c => c.id === 'solana') || null;
  const bnb = markets.find(c => c.id === 'binancecoin') || null;

  const fearGreed = fgi?.data?.[0]
    ? { value: Number(fgi.data[0].value), label: fgi.data[0].value_classification }
    : null;

  const trendingCoins = (trending?.coins || []).slice(0, 8).map(t => t.item);

  return {
    overview: {
      totalMarketCap,
      totalMarketCapFmt: fmtCap(totalMarketCap),
      marketCapChange24h,
      btcDominance,
      ethDominance,
      fearGreed,
    },
    keyCoins: {
      btc: btc ? { ...btc, priceFmt: fmtPrice(btc.current_price), capFmt: fmtCap(btc.market_cap), volFmt: fmtCap(btc.total_volume) } : null,
      eth: eth ? { ...eth, priceFmt: fmtPrice(eth.current_price), capFmt: fmtCap(eth.market_cap), volFmt: fmtCap(eth.total_volume) } : null,
      sol: sol ? { ...sol, priceFmt: fmtPrice(sol.current_price), capFmt: fmtCap(sol.market_cap), volFmt: fmtCap(sol.total_volume) } : null,
      bnb: bnb ? { ...bnb, priceFmt: fmtPrice(bnb.current_price) } : null,
    },
    gainers: gainers.map(c => ({ ...c, priceFmt: fmtPrice(c.current_price), capFmt: fmtCap(c.market_cap) })),
    losers:  losers.map(c =>  ({ ...c, priceFmt: fmtPrice(c.current_price), capFmt: fmtCap(c.market_cap) })),
    volumeAnomalies: volumeAnomalies.map(c => ({ ...c, priceFmt: fmtPrice(c.current_price) })),
    trending: trendingCoins,
    fetchedAt: new Date().toISOString(),
  };
}

export async function fetchPrices() {
  console.log('  抓取 CoinGecko 全局数据…');
  const globalData = await fetchWithRetry(`${COINGECKO_BASE}/global`);

  // Delay to respect CoinGecko rate limit on free tier
  await new Promise(r => setTimeout(r, 1200));
  console.log('  抓取 Top 100 市值币种行情…');
  const markets = await fetchWithRetry(
    `${COINGECKO_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&sparkline=false&price_change_percentage=24h`
  );

  await new Promise(r => setTimeout(r, 1200));
  console.log('  抓取热搜榜…');
  const trending = await fetchWithRetry(`${COINGECKO_BASE}/search/trending`);

  console.log('  抓取恐惧贪婪指数…');
  const fgi = await fetchWithRetry(FGI_URL).catch(() => null);

  return processData({ globalData, markets, trending, fgi });
}
