import RSSParser from 'rss-parser';

const parser = new RSSParser({ timeout: 10000, headers: { 'User-Agent': 'Mozilla/5.0' } });
const PROBE_HANDLE = 'coinbase';

async function probeInstances(instances) {
  const alive = [];
  await Promise.allSettled(
    instances.map(async (instance) => {
      try {
        await parser.parseURL(`${instance}/${PROBE_HANDLE}/rss`);
        alive.push(instance);
        console.log(`  ✓ nitter: ${instance}`);
      } catch {
        // instance not available
      }
    })
  );
  return alive;
}

export async function fetchTweets(handles, nitterInstances, config) {
  console.log('\n→ X/Twitter (Nitter)');
  const alive = await probeInstances(nitterInstances);
  if (!alive.length) {
    console.log('  [WARN] 无可用 Nitter 实例');
    return [];
  }

  const cutoff = Date.now() - config.timeWindowHours * 3600 * 1000;
  const articles = [];

  for (const { name, handle, lang } of handles) {
    let fetched = false;
    for (const instance of alive) {
      try {
        const feed = await parser.parseURL(`${instance}/${handle}/rss`);
        let count = 0;
        for (const item of feed.items) {
          if (count >= config.twitterMaxPerHandle) break;
          const title = (item.title || '').trim();
          if (!title) continue;
          if (title.startsWith('RT @') || title.startsWith('R to @')) continue;

          const pub = item.pubDate ? new Date(item.pubDate).getTime() : 0;
          if (pub && pub < cutoff) continue;

          articles.push({
            id: item.link || item.guid || `${handle}-${count}`,
            title,
            summary: item.contentSnippet || item.content || title,
            url: item.link || `https://x.com/${handle}`,
            source: `${name} (@${handle})`,
            platform: 'X',
            lang: lang || 'en',
            published: item.pubDate || '',
          });
          count++;
        }
        fetched = true;
        break;
      } catch {
        // try next instance
      }
    }
    if (!fetched) {
      console.log(`  [WARN] @${handle} 所有实例均失败`);
    }
  }

  console.log(`  X/Twitter 抓到 ${articles.length} 条`);
  return articles;
}
