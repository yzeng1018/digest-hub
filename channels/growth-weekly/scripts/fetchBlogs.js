import RSSParser from 'rss-parser';

const parser = new RSSParser({ timeout: 15000, headers: { 'User-Agent': 'Mozilla/5.0' } });

export async function fetchBlogs(blogs, config) {
  console.log('\n→ Blogs/Substack');
  const cutoff = Date.now() - config.blogTimeWindowHours * 3600 * 1000;
  const articles = [];

  await Promise.allSettled(
    blogs.map(async ({ name, url, lang }) => {
      try {
        const feed = await parser.parseURL(url);
        let count = 0;
        for (const item of feed.items) {
          const pub = item.pubDate ? new Date(item.pubDate).getTime() : 0;
          if (pub && pub < cutoff) continue;

          const title = (item.title || '').trim();
          if (!title) continue;

          articles.push({
            id: item.link || item.guid || title,
            title,
            summary: item.contentSnippet || item.content || '',
            url: item.link || url,
            source: name,
            platform: 'Blog',
            lang: lang || 'en',
            published: item.pubDate || '',
          });
          count++;
        }
        if (count) console.log(`  ${name}: ${count} 条`);
      } catch (err) {
        console.log(`  [WARN] ${name}: ${err.message}`);
      }
    })
  );

  console.log(`  Blog 抓到 ${articles.length} 条`);
  return articles;
}
