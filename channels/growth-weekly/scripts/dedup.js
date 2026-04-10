function tokenize(text) {
  return new Set(
    text.toLowerCase()
      .replace(/[^\w\u4e00-\u9fff]+/g, ' ')
      .trim()
      .split(/\s+/)
      .filter(t => t.length > 1)
  );
}

function jaccard(a, b) {
  const setA = tokenize(a);
  const setB = tokenize(b);
  if (!setA.size || !setB.size) return 0;
  let intersection = 0;
  for (const t of setA) if (setB.has(t)) intersection++;
  return intersection / (setA.size + setB.size - intersection);
}

// Union-Find
function makeUF(n) {
  const parent = Array.from({ length: n }, (_, i) => i);
  function find(x) {
    while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; }
    return x;
  }
  function union(x, y) { parent[find(x)] = find(y); }
  return { find, union };
}

// Priority: Blog > X > 即刻 > Podcast; then zh > en
function priority(art) {
  const platform = { 'Blog': 0, 'X': 1, '即刻': 2, 'Podcast': 3 };
  const lang = art.lang === 'zh' ? 0 : 1;
  return (platform[art.platform] ?? 4) * 10 + lang;
}

export function deduplicate(articles, threshold = 0.55) {
  const n = articles.length;
  const uf = makeUF(n);

  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (jaccard(articles[i].title, articles[j].title) >= threshold) {
        uf.union(i, j);
      }
    }
  }

  const best = new Map();
  for (let i = 0; i < n; i++) {
    const root = uf.find(i);
    if (!best.has(root) || priority(articles[i]) < priority(articles[best.get(root)])) {
      best.set(root, i);
    }
  }

  return [...best.values()].map(i => articles[i]);
}
