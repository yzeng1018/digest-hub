import RSSParser from 'rss-parser';
import { fetchTranscript } from 'youtube-transcript/dist/youtube-transcript.esm.js';

const parser = new RSSParser({ timeout: 15000 });

function videoIdFromUrl(url) {
  const m = url.match(/[?&]v=([^&]+)/) || url.match(/youtu\.be\/([^?]+)/);
  return m ? m[1] : null;
}

async function getTranscript(videoId) {
  try {
    const chunks = await fetchTranscript(videoId);
    return chunks.map(c => c.text).join(' ');
  } catch {
    return '';
  }
}

export async function fetchPodcasts(podcasts, config) {
  console.log('\n→ Podcasts (YouTube)');
  const cutoff = Date.now() - config.podcastTimeWindowHours * 3600 * 1000;
  const articles = [];

  for (const podcast of podcasts) {
    try {
      const rssUrl = podcast.type === 'playlist'
        ? `https://www.youtube.com/feeds/videos.xml?playlist_id=${podcast.id}`
        : `https://www.youtube.com/feeds/videos.xml?channel_id=${podcast.id}`;

      const feed = await parser.parseURL(rssUrl);

      for (const item of feed.items) {
        const pub = item.pubDate ? new Date(item.pubDate).getTime() : 0;
        if (pub && pub < cutoff) continue;

        const title = (item.title || '').trim();
        if (!title) continue;

        const videoId = videoIdFromUrl(item.link || item.id || '');
        let transcript = '';
        if (videoId) {
          console.log(`  ${podcast.name}: 《${title.slice(0, 40)}》→ 拉转录稿…`);
          transcript = await getTranscript(videoId);
        }

        articles.push({
          id: item.link || item.id || title,
          title,
          summary: transcript ? transcript.slice(0, 400) : (item.contentSnippet || ''),
          url: item.link || `https://www.youtube.com/watch?v=${videoId}`,
          source: podcast.name,
          platform: 'Podcast',
          lang: 'en',
          published: item.pubDate || '',
          transcript,
        });
      }
    } catch (err) {
      console.log(`  [WARN] ${podcast.name}: ${err.message}`);
    }
  }

  console.log(`  Podcast 抓到 ${articles.length} 条`);
  return articles;
}
