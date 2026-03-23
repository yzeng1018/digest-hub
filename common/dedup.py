"""
去重：基于标题的 token 重叠（Jaccard 相似度）合并近似内容。
保留规则：同等内容取 priority 最高的；priority 相同则优先保留中文。
threshold 从调用方（各 channel 的 config）传入。
"""

import re


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", text.lower())
    stops = {"a", "an", "the", "in", "of", "to", "and", "for", "is", "on",
             "at", "by", "with", "that", "this", "are", "was", "it", "its"}
    return {w for w in words if w not in stops and len(w) > 1}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def deduplicate(articles: list[dict], threshold: float = 0.55) -> list[dict]:
    n = len(articles)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            if _similarity(articles[i]["title"], articles[j]["title"]) >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    def _rank(idx: int) -> tuple:
        art = articles[idx]
        return (-art.get("priority", 1), 0 if art["lang"] == "zh" else 1, idx)

    kept = []
    for indices in groups.values():
        kept.append(articles[min(indices, key=_rank)])

    original_order = {id(a): i for i, a in enumerate(articles)}
    kept.sort(key=lambda a: original_order.get(id(a), 0))

    print(f"去重：{n} → {len(kept)} 条。")
    return kept
