#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 danmu_api 真实响应结构（用于集成开发）"""
import json, urllib.request, urllib.parse, sys

BASE = "http://192.168.123.146:9321"
UA = "Moviepilot/plugins 1.12.0"


def req(path, data=None, params=None, timeout=40):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    h = {"Accept": "application/json", "User-Agent": UA}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return None, f"ERR:{e}"


def show(tag, path, data=None, params=None, limit=900):
    st, raw = req(path, data=data, params=params)
    print(f"===== {tag}  [{path}] status={st}")
    print(raw[:limit])
    print()


# 1) match 主入口
show("match-生万物E1", "/api/v2/match", data={"fileName": "生万物 S01E01"})
show("match-非自然死亡E1", "/api/v2/match", data={"fileName": "非自然死亡 S01E01"})
show("match-泪之女王E3", "/api/v2/match", data={"fileName": "泪之女王 S01E03"})
show("match-中文集号", "/api/v2/match", data={"fileName": "生万物 第1集"})
show("match-不存在", "/api/v2/match", data={"fileName": "zzz不存在的剧集zzz S01E01"})

# 2) search/episodes
show("search/episodes-生万物", "/api/v2/search/episodes", params={"anime": "生万物"}, limit=1400)
show("search/episodes-空", "/api/v2/search/episodes", params={"anime": "zzz不存在zzz"}, limit=300)

# 3) search/anime
show("search/anime-生万物", "/api/v2/search/anime", params={"keyword": "生万物"}, limit=1200)

# 4) comment
st, raw = req("/api/v2/match", data={"fileName": "生万物 S01E01"})
try:
    eid = json.loads(raw)["matches"][0]["episodeId"]
except Exception as e:
    eid = None
    print("拿不到 episodeId:", e)
if eid:
    show(f"comment-{eid}", f"/api/v2/comment/{eid}", params={"format": "json"}, limit=1200)
    show("comment-404", "/api/v2/comment/999999999", params={"format": "json"}, limit=300)
