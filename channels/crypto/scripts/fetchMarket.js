import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);
const COINGECKO_BASE = 'https://api.coingecko.com/api/v3';
const FGI_URL = 'https://api.alternative.me/fng/';

async function curlGet(url) {
  const args = [
    '-s', '--max-time', '20', '-L',
    '-H', 'Accept: application/json',
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

async function fetchWithRetry(url, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await curlGet(url);
    } catch (err) {
      if (attempt === retries) throw err;
      const waitMs = err.status === 429 ? 5000 * (attempt + 1) : 2000;
      await new Promise(resolve => setTimeout(resolve, waitMs));
    }
  }
}

function fmtPrice(value) {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 10000) return '$' + Math.round(value).toLocaleString('en-US');
  if (value >= 1) return '$' + value.toFixed(2);
  if (value >= 0.01) return '$' + value.toFixed(4);
  return '$' + value.toFixed(6);
}

function fmtCap(value) {
  if (!value) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  return `$${(value / 1e6).toFixed(0)}M`;
}

function formatCoin(coin) {
  return coin ? {
    ...coin,
    priceFmt: fmtPrice(coin.current_price),
    capFmt: fmtCap(coin.market_cap),
  } : null;
}

export async function fetchMarketSnapshot() {
  const globalData = await fetchWithRetry(`${COINGECKO_BASE}/global`);
  await new Promise(resolve => setTimeout(resolve, 1200));
  const markets = await fetchWithRetry(
    `${COINGECKO_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&sparkline=false&price_change_percentage=24h`
  );
  const fgi = await fetchWithRetry(FGI_URL).catch(() => null);

  const global = globalData.data || {};
  const sorted = [...markets].sort(
    (a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0)
  );

  return {
    overview: {
      totalMarketCapFmt: fmtCap(global.total_market_cap?.usd || 0),
      marketCapChange24h: global.market_cap_change_percentage_24h_usd || 0,
      btcDominance: global.market_cap_percentage?.btc || 0,
      fearGreed: fgi?.data?.[0] ? Number(fgi.data[0].value) : null,
    },
    keyCoins: {
      btc: formatCoin(markets.find(coin => coin.id === 'bitcoin')),
      eth: formatCoin(markets.find(coin => coin.id === 'ethereum')),
      sol: formatCoin(markets.find(coin => coin.id === 'solana')),
    },
    gainers: sorted.filter(coin => (coin.price_change_percentage_24h || 0) > 0).slice(0, 3).map(formatCoin),
    losers: sorted.filter(coin => (coin.price_change_percentage_24h || 0) < 0).reverse().slice(0, 3).map(formatCoin),
    fetchedAt: new Date().toISOString(),
  };
}
