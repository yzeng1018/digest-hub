import RSSParser from 'rss-parser';
import { execFile } from 'child_process';
import { promisify } from 'util';

const parser = new RSSParser({ timeout: 15000, headers: { 'User-Agent': 'Mozilla/5.0' } });
const HEADERS = {
  'User-Agent': 'Mozilla/5.0',
  'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, text/html, */*',
};
const execFileAsync = promisify(execFile);

async function fetchText(url) {
  try {
    const response = await fetch(url, { headers: HEADERS, signal: AbortSignal.timeout(15000) });
    if (response.ok) return await response.text();
    throw new Error(`HTTP ${response.status}`);
  } catch (fetchError) {
    try {
      const { stdout } = await execFileAsync('curl', [
        '-L', '-sS', '--fail', '--max-time', '15',
        '-A', HEADERS['User-Agent'], url,
      ], { maxBuffer: 5 * 1024 * 1024 });
      return stdout;
    } catch {
      throw fetchError;
    }
  }
}

function decodeHtml(value = '') {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
}

function metaContent(html, property) {
  const escaped = property.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const patterns = [
    new RegExp(`<meta[^>]+(?:property|name)=["']${escaped}["'][^>]+content=["']([^"']*)["']`, 'i'),
    new RegExp(`<meta[^>]+content=["']([^"']*)["'][^>]+(?:property|name)=["']${escaped}["']`, 'i'),
  ];
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) return decodeHtml(match[1].trim());
  }
  return '';
}

async function fetchHtmlIndex(source, cutoff) {
  const indexHtml = await fetchText(source.url);
  const links = [];
  const seen = new Set();

  for (const match of indexHtml.matchAll(/href=["']([^"'#]+)["']/gi)) {
    let articleUrl;
    try {
      articleUrl = new URL(decodeHtml(match[1]), source.url).href;
    } catch {
      continue;
    }
    if (!articleUrl.startsWith(source.linkPrefix) || seen.has(articleUrl)) continue;
    seen.add(articleUrl);
    links.push(articleUrl);
    if (links.length >= (source.maxLinks || 12)) break;
  }

  const settled = await Promise.allSettled(links.map(async articleUrl => {
    const pageHtml = await fetchText(articleUrl);
    const published = metaContent(pageHtml, 'article:published_time')
      || pageHtml.match(/<time[^>]+datetime=["']([^"']+)["']/i)?.[1]
      || '';
    const publishedAt = published ? new Date(published).getTime() : 0;
    if (!publishedAt || publishedAt < cutoff) return null;

    const title = metaContent(pageHtml, 'og:title');
    if (!title) return null;
    return {
      id: articleUrl,
      title,
      summary: metaContent(pageHtml, 'og:description') || metaContent(pageHtml, 'description'),
      url: articleUrl,
      source: source.name,
      platform: 'Newsletter',
      lang: source.lang || 'en',
      published,
    };
  }));

  return settled
    .filter(result => result.status === 'fulfilled' && result.value)
    .map(result => result.value);
}

export async function fetchBlogs(blogs, config) {
  console.log('\n→ Blogs/Substack');
  const cutoff = Date.now() - config.blogTimeWindowHours * 3600 * 1000;
  const articles = [];

  await Promise.allSettled(
    blogs.map(async source => {
      const { name, url, lang } = source;
      try {
        if (source.type === 'html-index') {
          const items = await fetchHtmlIndex(source, cutoff);
          articles.push(...items);
          if (items.length) console.log(`  ${name}: ${items.length} 条`);
          return;
        }

        const feed = source.transport === 'fetch-with-curl-fallback'
          ? await parser.parseString(await fetchText(url))
          : await parser.parseURL(url);
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
