#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地真实联网验证：弹幕插件 A+B+C 改造（v1.12.0）
用 stub 顶掉 MoviePilot 宿主依赖，直接调用 danmu_generator，三种数据源模式各跑一遍。
"""
import os
import sys
import re
import types
import tempfile
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO, "plugins", "danmu")


# ---- stub 宿主依赖 ------------------------------------------------------
def _install_stub_app():
    app = types.ModuleType("app")
    log = types.ModuleType("app.log")

    class _Logger:
        def info(self, msg, *a): print(f"[INFO] {msg}")
        def warning(self, msg, *a): print(f"[WARN] {msg}")
        def error(self, msg, *a): print(f"[ERR ] {msg}")
        def debug(self, msg, *a): pass

    log.logger = _Logger()
    app.log = log
    sys.modules["app"] = app
    sys.modules["app.log"] = log


_install_stub_app()
sys.path.insert(0, PLUGIN)
import danmu_generator as g  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")


def make_video(path, seconds=3):
    """用 ffmpeg 生成一个真实的小视频文件（供哈希/时长匹配用）"""
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=320x240:d={seconds}",
           "-pix_fmt", "yuv420p", path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


# ==========================================================================
print("\n########## 单元级：工具函数 ##########")
check("normalize_title 剥壳", g.normalize_title("生万物(2025)【国产剧】from iqiyi") == "生万物",
      g.normalize_title("生万物(2025)【国产剧】from iqiyi"))
check("normalize_title BiliBili 兼容", g.normalize_title("[BiliBili]非自然死亡") == "非自然死亡",
      g.normalize_title("[BiliBili]非自然死亡"))
check("parse_episode_number 第3集", g.parse_episode_number("【qiyi】 生万物第3集 绣绣") == 3)
check("parse_episode_number _01", g.parse_episode_number("【qq】 01:无名之毒_01") == 1)
check("parse_episode_number S01E03", g.parse_episode_number("Foo S01E03") == 3)
check("strip_like_suffix 点赞", g.strip_like_suffix("二刷站过来[吃瓜] ♡232") == "二刷站过来[吃瓜]",
      repr(g.strip_like_suffix("二刷站过来[吃瓜] ♡232")))
check("_is_bili_comment 弹弹play", g._is_bili_comment({"p": "1,1,1,[BiliBili]"}))
check("_is_bili_comment danmu_api", g._is_bili_comment({"p": "1.00,1,16777215,[bilibili1]"}))
check("_is_bili_comment 多源", g._is_bili_comment({"p": "1.00,1,16777215,[bilibili1&dandan]"}))
check("_is_bili_comment 非B站", not g._is_bili_comment({"p": "1.00,1,16777215,[qiyi]"}))

# ==========================================================================
print("\n########## 真实联网：danmu_api 源 ##########")
g.DanmuApiSource.configure("http://192.168.123.146:9321", "")
eid = g.DanmuApiSource.get_comment_id("生万物", episode=1, season=1)
check("danmu_api /match 生万物 E1 拿到 episodeId", bool(eid), f"episodeId={eid}")
if eid:
    data = g.DanmuApiSource.get_comments(eid)
    n = len((data or {}).get("comments") or [])
    check("danmu_api 弹幕正文非空", n > 100, f"{n} 条")
    if n:
        c0 = data["comments"][0]
        check("danmu_api p 第4段是来源标签", c0["p"].split(",")[3].startswith("["), c0["p"])
        print(f"       样例: p={c0['p']!r} m={c0['m']!r}")
# 集号对应：E2 应得到不同 episodeId
eid2 = g.DanmuApiSource.get_comment_id("生万物", episode=2, season=1)
check("danmu_api 集号区分 E1!=E2", eid and eid2 and eid != eid2, f"{eid} vs {eid2}")
# 未收录
miss = g.DanmuApiSource.get_comment_id("zzz不存在的剧集zzz", episode=1, season=1)
check("danmu_api 未收录返回 None", miss is None, f"{miss}")
# 404 弹幕
d404 = g.DanmuApiSource.get_comments("999999999")
check("danmu_api 404 返回空 comments", d404 == {"count": 0, "comments": []}, f"{d404}")

# ==========================================================================
print("\n########## 真实联网：弹弹play 源（A + B 方案）##########")
# B 方案：日剧《非自然死亡》——hash 无记录，关键词搜索兜底应命中
cid = g.DanmuAPI.get_comment_id("/tmp/x/非自然死亡 S01E01.mp4",
                                use_tmdb_id=False, episode=1, title="非自然死亡")
check("B 关键词兜底 非自然死亡 E1", bool(cid), f"commentId={cid}")
if cid:
    cd = g.DanmuAPI.get_comments(cid)
    n = len((cd or {}).get("comments") or [])
    check("弹弹play 弹幕正文非空", n > 100, f"{n} 条")
# 动画精确命中（回归）：葬送的芙莉莲
cid_anime = g.DanmuAPI.get_comment_id("/tmp/x/葬送的芙莉莲 S01E01.mp4",
                                      use_tmdb_id=False, episode=1, title="葬送的芙莉莲")
check("弹弹play 动画关键词命中", bool(cid_anime), f"commentId={cid_anime}")
# 未收录
cid_miss = g.DanmuAPI.get_comment_id("/tmp/x/zzz不存在zzz S01E01.mp4",
                                     use_tmdb_id=False, episode=1, title="zzz不存在的剧集zzz")
check("弹弹play 未收录返回 None", cid_miss is None, f"{cid_miss}")

# ==========================================================================
print("\n########## 端到端：danmu_generator 三模式（真实写 .ass）##########")
tmpdir = tempfile.mkdtemp(prefix="danmu_verify_")

# --- dandanplay 模式（默认，零回归）---
p1 = os.path.join(tmpdir, "非自然死亡 S01E01.mp4")
make_video(p1)
r1 = g.danmu_generator(p1, data_source="dandanplay", title="非自然死亡",
                       episode=1, season=1, use_tmdb_id=False, min_danmu_count=100)
check("dandanplay 模式生成弹幕", r1.outcome == "ok", f"{r1.outcome} {r1.message}")
if r1.output_file and os.path.exists(r1.output_file):
    lines = open(r1.output_file, encoding="utf-8").read().count("Dialogue:")
    check("dandanplay 产出 .ass 含 Dialogue", lines > 0, f"{lines} 行")

# --- danmu_api 模式 ---
p2 = os.path.join(tmpdir, "生万物 S01E01.mp4")
make_video(p2)
r2 = g.danmu_generator(p2, data_source="danmu_api", title="生万物",
                       episode=1, season=1, danmu_api_url="http://192.168.123.146:9321",
                       danmu_api_token="", min_danmu_count=100)
check("danmu_api 模式生成弹幕", r2.outcome == "ok", f"{r2.outcome} {r2.message}")
if r2.output_file and os.path.exists(r2.output_file):
    content = open(r2.output_file, encoding="utf-8").read()
    lines = content.count("Dialogue:")
    check("danmu_api 产出 .ass 含 Dialogue", lines > 0, f"{lines} 行")
    check("danmu_api 点赞后缀已剥离", not re.search(r"[♡🔥][\d.]", content))

# --- hybrid 模式（弹弹play 优先，danmu_api 兜底）---
p3 = os.path.join(tmpdir, "生万物 S01E01.mp4")  # 弹弹play 无收录 → 应回退 danmu_api
r3 = g.danmu_generator(p3, data_source="hybrid", title="生万物",
                       episode=1, season=1, danmu_api_url="http://192.168.123.146:9321",
                       danmu_api_priority=False, min_danmu_count=100)
check("hybrid 模式回退到 danmu_api 生成", r3.outcome == "ok", f"{r3.outcome} {r3.message}")

# hybrid 反序（danmu_api 优先）
p4 = os.path.join(tmpdir, "非自然死亡 S01E01.mp4")
r4 = g.danmu_generator(p4, data_source="hybrid", title="非自然死亡",
                       episode=1, season=1, danmu_api_url="http://192.168.123.146:9321",
                       danmu_api_priority=True, min_danmu_count=100)
check("hybrid 反序（danmu_api 优先）生成", r4.outcome == "ok", f"{r4.outcome} {r4.message}")

# ==========================================================================
print("\n" + "=" * 70)
passed = sum(1 for _, ok, _ in RESULTS if ok)
print(f"结果: {passed}/{len(RESULTS)} 通过")
for name, ok, detail in RESULTS:
    if not ok:
        print(f"  FAILED: {name}  {detail}")
print("=" * 70)
sys.exit(0 if passed == len(RESULTS) else 1)
