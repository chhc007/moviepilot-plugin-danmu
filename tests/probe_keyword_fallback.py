#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证：关键词搜索 + 标题匹配 → 构造 episodeId（不下载弹幕正文，快）"""
import json, urllib.request, urllib.parse, re, sys

UA = "Moviepilot/plugins 1.11.0"
BASE = "https://dandanapi.hankun.online/api/v1"

def req(url, data=None):
    h = {"Accept": "application/json", "User-Agent": UA}
    body = None
    if data is not None:
        body = json.dumps(data).encode(); h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"_err": str(e)}

def norm(s):
    return re.sub(r"[\s:：\-_·!！?？.。()（）\[\]【】~～]", "", (s or "").lower())

CASES = [
    ("动画", "葬送的芙莉莲", 1), ("动画", "间谍过家家", 1),
    ("国创", "灵笼", 1), ("国创", "凡人修仙传", 1), ("国创", "斗罗大陆", 1),
    ("日剧", "非自然死亡", 1), ("日剧", "胜者即是正义", 1), ("日剧", "半泽直树", 1),
    ("国剧", "甄嬛传", 1), ("国剧", "隐秘的角落", 1), ("国剧", "狂飙", 1),
    ("欧美", "权力的游戏", 1), ("欧美", "怪奇物语", 1), ("欧美", "绝命毒师", 1),
    ("韩剧", "鱿鱼游戏", 1), ("韩剧", "请回答1988", 1),
    ("电影", "千与千寻", 1), ("电影", "你的名字。", 1),
    ("电影", "肖申克的救赎", 1), ("电影", "流浪地球", 1), ("电影", "沙丘", 1),
    ("综艺", "奔跑吧兄弟", 1),
]

print(f"{'类别':<5} {'MP标题':<14} {'搜索命中(首个)':<26} {'匹配':<5} {'episodeId'}")
print("-"*85)
hit_exact = hit_fuzzy = miss = 0
for cat, title, ep in CASES:
    d = req(f"{BASE}/search/anime?" + urllib.parse.urlencode({"keyword": title}))
    if d.get("_err"):
        print(f"{cat:<5} {title:<14} ERR {d['_err'][:40]}"); continue
    res = d.get("animes", [])
    if not res:
        print(f"{cat:<5} {title:<14} {'❌ 搜索无结果':<26}"); miss += 1; continue
    best = None
    for a in res:
        if norm(a["animeTitle"]) == norm(title): best = a; break
    tag = "精确"
    if not best:
        for a in res:
            if norm(title) in norm(a["animeTitle"]) or norm(a["animeTitle"]) in norm(title):
                best = a; tag = "模糊"; break
    if not best: best = res[0]; tag = "首条"
    eid = f"{best['animeId']}{ep:04d}"
    if tag == "精确": hit_exact += 1
    else: hit_fuzzy += 1
    print(f"{cat:<5} {title:<14} {best['animeTitle']:<26} {tag:<5} {eid}")
print()
print(f"精确 {hit_exact} / 模糊或首条 {hit_fuzzy} / 搜索无结果 {miss}  (共 {len(CASES)})")
