import RSSParser from 'rss-parser';

const parser = new RSSParser({ timeout: 10000 });

export async function fetchJike(users, rsshubInstances, config) {
  console.log('\n→ 即刻 (RSSHub)');
  const cutoff = Date.now() - config.timeWindowHours * 3600 * 1000;
  const articles = [];

  for (const { name, id } of users) {
    let fetched = false;
    for (const instance of rsshubInstances) {
      try {
        const url = `${instance}/jike/user/${id}`;
        const feed = await parser.parseURL(url);
        for (const item of feed.items) {
          const pub = item.pubDate ? new Date(item.pubDate).getTime() : 0;
          if (pub && pub < cutoff) continue;

          const title = (item.title || '').trim();
          if (!title) continue;

          articles.push({
            id: item.link || item.guid || title,
            title,
            summary: item.contentSnippet || item.content || title,
            url: item.link || '',
            source: name,
            platform: '即刻',
            lang: 'zh',
            published: item.pubDate || '',
          });
        }
        fetched = true;
        break;
      } catch {
        // try next instance
      }
    }
    if (!fetched) {
      console.log(`  [WARN] 即刻用户 ${name} 所有 RSSHub 实例均失败`);
    }
  }

  console.log(`  即刻 抓到 ${articles.length} 条`);
  return articles;
}
