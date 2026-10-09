#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""横向测试：各类内容在弹弹play 中转服务的匹配覆盖情况
1) /search/anime  关键词搜索（手动匹配用）
2) /search/tmdb   TMDB ID 匹配（自动刮削用）
"""
import json, urllib.request, urllib.parse, sys

UA = "Moviepilot/plugins 1.11.0"
BASE = "https://dandanapi.hankun.online/api/v1"

def req(url, data=None, method=None):
    h = {"Accept": "application/json", "User-Agent": UA}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=45) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"_err": str(e)}

def search_anime(kw):
    d = req(f"{BASE}/search/anime?" + urllib.parse.urlencode({"keyword": kw}))
    return [a.get("animeTitle") for a in d.get("animes", [])][:3] if not d.get("_err") else [f"ERR:{d['_err'][:40]}"]

def search_tmdb(tid, ttype=0):
    d = req(f"{BASE}/search/tmdb", {"tmdb_id": tid, "tmdb_id_type": ttype, "episode": 1})
    if d.get("_err"): return f"ERR:{d['_err'][:40]}"
    an = d.get("animes", [])
    if not an: return "EMPTY"
    eps = an[0].get("episodes", [])
    return f"{an[0].get('animeTitle')} ({len(eps)}集)"

# (类别, 标题, tmdb_id, tmdb_type)
CASES = [
    ("动画番剧", "葬送的芙莉莲", 209867, 0),
    ("动画番剧", "间谍过家家", 120089, 0),
    ("动画番剧", "鬼灭之刃", 85937, 0),
    ("国创动画", "灵笼", 94716, 0),
    ("国创动画", "凡人修仙传", 106921, 0),
    ("日剧", "非自然死亡", 75701, 0),
    ("日剧", "Legal High", 65294, 0),
    ("日剧", "半泽直树", 60771, 0),
    ("国剧", "甄嬛传", 48939, 0),
    ("国剧", "隐秘的角落", 104716, 0),
    ("国剧", "狂飙", 204261, 0),
    ("欧美剧", "权力的游戏", 1399, 0),
    ("欧美剧", "怪奇物语", 66732, 0),
    ("欧美剧", "绝命毒师", 1396, 0),
    ("韩剧", "鱿鱼游戏", 93405, 0),
    ("韩剧", "请回答1988", 64994, 0),
    ("电影-动画", "千与千寻", 129, 1),
    ("电影-动画", "你的名字", 372058, 1),
    ("电影-真人", "肖申克的救赎", 278, 1),
    ("电影-真人", "流浪地球", 585368, 1),
    ("电影-真人", "沙丘", 438631, 1),
    ("综艺", "奔跑吧兄弟", 78286, 0),
]

print(f"{'类别':<10} {'标题':<16} {'TMDB':<8} {'TMDB匹配':<40} 关键词搜索")
print("-" * 120)
for cat, title, tid, ttype in CASES:
    t = search_tmdb(tid, ttype)
    k = search_anime(title)
    print(f"{cat:<10} {title:<16} {tid:<8} {t:<40} {k}")
