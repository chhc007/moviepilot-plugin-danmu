#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Danmu v1.12.1 配置层（__init__.py）plumbing 验证：
  - _clamp_max_same_screen 归一化
  - _apply_config 读取 max_same_screen
  - _get_config 回写 max_same_screen
  - _render_signature：默认(0) 不计入签名（零回归）；>0 才计入（触发存量重生成）
  - generate_danmu 调用 convert_comments_to_ass 时把 max_same_screen 传下去
用 stub 顶掉 MoviePilot 宿主依赖。
"""
import os
import sys
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_PARENT = os.path.join(REPO, "plugins")   # 含 danmu/ 包
PLUGIN_DIR = os.path.join(PLUGIN_PARENT, "danmu")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")


# ---- stub 宿主 ----------------------------------------------------------
def mod(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


class _Logger:
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass
    def debug(self, *a, **k): pass


class _PluginBase:
    def __init__(self, *a, **k): pass
    def get_data(self, *a, **k): return None
    def save_data(self, *a, **k): pass
    def update_config(self, *a, **k): pass


class _EventManager:
    def register(self, *a, **k):
        def deco(fn): return fn
        return deco


class _MediaType:
    MOVIE = "movie"
    TV = "tv"


class _EventType:
    TransferComplete = "transfer.complete"


class _SystemConfigKey:
    pass


class _Response:
    def __init__(self, success=True, message="", data=None):
        self.success = success
        self.message = message
        self.data = data


class _SystemUtils:
    @staticmethod
    def is_windows(): return False


class _MediaChain:
    def __init__(self, *a, **k): pass


class _MetaInfo:
    def __init__(self, *a, **k): pass


class _Settings:
    PROXY = None


app = mod("app")
app.__path__ = []
log = mod("app.log", logger=_Logger())
app.log = log
core = mod("app.core")
app.core = core
cfg = mod("app.core.config", settings=_Settings())
core.config = cfg
metainfo = mod("app.core.metainfo", MetaInfo=_MetaInfo)
core.metainfo = metainfo
ev = mod("app.core.event", eventmanager=_EventManager())
core.event = ev
chain = mod("app.chain")
app.chain = chain
chain.media = mod("app.chain.media", MediaChain=_MediaChain)
utils = mod("app.utils")
app.utils = utils
utils.system = mod("app.utils.system", SystemUtils=_SystemUtils())
schemas = mod("app.schemas")
schemas.Response = _Response
app.schemas = schemas
stypes = mod("app.schemas.types", MediaType=_MediaType, EventType=_EventType,
             SystemConfigKey=_SystemConfigKey)
schemas.types = stypes
# app.plugins 作为真实包目录，让 `from app.plugins.danmu import danmu_generator` 生效
plugins = mod("app.plugins", _PluginBase=_PluginBase)
plugins.__path__ = [PLUGIN_PARENT]
app.plugins = plugins

sys.path.insert(0, PLUGIN_PARENT)
import app.plugins.danmu as plugin_mod  # noqa: E402
Danmu = plugin_mod.Danmu

# ---- 构造实例（绕过 _PluginBase.__init__ 依赖）--------------------------
inst = Danmu.__new__(Danmu)
inst._scrape_state = {}
inst._manual_match_misses = set()
inst._danmu_count_cache = {}

# ==========================================================================
print("\n########## _clamp_max_same_screen 归一化 ##########")
check("默认 0", Danmu._clamp_max_same_screen(0) == 0)
check("20 原样", Danmu._clamp_max_same_screen(20) == 20)
check("负数归 0", Danmu._clamp_max_same_screen(-5) == 0)
check("字符串 '30' → 30", Danmu._clamp_max_same_screen("30") == 30)
check("非法值 → 0", Danmu._clamp_max_same_screen("abc") == 0)
check("None → 0", Danmu._clamp_max_same_screen(None) == 0)
check("浮点 12.9 → 12", Danmu._clamp_max_same_screen(12.9) == 12)

# ==========================================================================
print("\n########## _apply_config / _get_config 往返 ##########")
Danmu._apply_config(inst, {"enabled": True, "max_same_screen": 25})
check("_apply_config 读取 25", inst._max_same_screen == 25, f"{inst._max_same_screen}")
cfg_out = Danmu._get_config(inst)
check("_get_config 回写 max_same_screen=25", cfg_out.get("max_same_screen") == 25,
      f"{cfg_out.get('max_same_screen')}")
# 旧配置（无 max_same_screen）→ 默认 0，零回归
Danmu._apply_config(inst, {"enabled": True})
check("旧配置缺字段 → 默认 0（零回归）", inst._max_same_screen == 0,
      f"{inst._max_same_screen}")
cfg_out2 = Danmu._get_config(inst)
check("_get_config 含 max_same_screen=0", cfg_out2.get("max_same_screen") == 0)

# ==========================================================================
print("\n########## _render_signature：默认不计入、>0 才计入 ##########")
inst._data_source = "dandanplay"
inst._onlyFromBili = False
inst._screen_area = "full"
inst._fontsize = 50
inst._alpha = 0.8
inst._duration = 15
inst._width = 1920
inst._height = 1080
inst._max_same_screen = 0
sig_default = Danmu._render_signature(inst)
check("max_same_screen=0 时签名不含该键（零回归）",
      "max_same_screen" not in sig_default, f"{sig_default}")
inst._max_same_screen = 20
sig_20 = Danmu._render_signature(inst)
check("max_same_screen=20 时签名含该键", sig_20.get("max_same_screen") == 20, f"{sig_20}")
check("设置上限后签名与默认不同（触发存量重生成）", sig_default != sig_20)

# ==========================================================================
print("\n########## generate_danmu 把 max_same_screen 传到底层 ##########")
captured = {}
orig_convert = plugin_mod.generator.DanmuConverter.convert_comments_to_ass


def _fake_convert(comments, output_file, width, height, fontface, fontsize,
                  alpha, duration, screen_area="full", max_same_screen=0):
    captured["max_same_screen"] = max_same_screen
    captured["screen_area"] = screen_area
    # 写一个最小合法 .ass，供上层后续逻辑（找不到字幕等）不炸
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n[Events]\n")


plugin_mod.generator.DanmuConverter.convert_comments_to_ass = staticmethod(_fake_convert)

# stub 掉网络与媒体信息解析，只走到 convert
plugin_mod.generator.DanmuApiSource.configure = lambda *a, **k: None
plugin_mod.generator.DanmuApiSource.get_comment_id = lambda *a, **k: "12345"
plugin_mod.generator.DanmuApiSource.get_comments = lambda *a, **k: {
    "count": 200, "comments": [{"p": f"{i * 0.1},1,16777215", "m": f"弹{i}"} for i in range(200)]
}
inst._enabled = True
inst._max_same_screen = 20
inst._data_source = "danmu_api"
inst._danmu_api_url = "http://x"
inst._danmu_api_token = ""
inst._danmu_api_priority = False
inst._min_danmu_count = 100
inst._onlyFromBili = False
inst._useTmdbID = False
inst._width = 1920
inst._height = 1080
inst._fontsize = 50
inst._alpha = 0.8
inst._duration = 15
inst._screen_area = "full"
inst._path = ""
inst._enable_strm = True
inst._stop_event = __import__("threading").Event()
inst._scrape_lock = __import__("threading").Lock()
inst._record_scrape_state = lambda *a, **k: None

import tempfile
tmp = tempfile.mkdtemp(prefix="danmu_cfg_")
video = os.path.join(tmp, "生万物 S01E01.mp4")
open(video, "w").close()
try:
    plugin_mod.generator.danmu_generator = plugin_mod.generator.danmu_generator  # noqa
    # 直接调 generate_danmu（其内部走 danmu_generator→convert）
    plugin_mod.generator.danmu_generator(
        video, data_source="danmu_api", title="生万物", episode=1, season=1,
        danmu_api_url="http://x", danmu_api_token="", min_danmu_count=100,
        max_same_screen=inst._max_same_screen,
    )
    check("底层收到 max_same_screen=20", captured.get("max_same_screen") == 20,
          f"{captured.get('max_same_screen')}")
except Exception as e:
    check("底层收到 max_same_screen=20", False, f"{type(e).__name__}: {e}")
finally:
    plugin_mod.generator.DanmuConverter.convert_comments_to_ass = orig_convert

# ==========================================================================
print("\n########## _generate_danmu_impl 中间层透传 ##########")
captured2 = {}
orig_gen = plugin_mod.generator.danmu_generator


def _fake_gen(file_path, *args, **kwargs):
    captured2.update(kwargs)
    captured2["_positional"] = args
    return plugin_mod.generator.DanmuResult("ok", message="stub", danmu_count=200)


plugin_mod.generator.danmu_generator = _fake_gen
# _generate_danmu_impl 依赖 MetaInfo/recognize；danmu_api 模式仍需识别拿标题 → stub 掉
inst.media_chain = types.SimpleNamespace(recognize_media=lambda meta=None: None)
inst._resolve_manual_comment_id = lambda *a, **k: None
inst._locate_via_series = lambda *a, **k: None
inst._record_scrape_state = lambda *a, **k: None
inst._max_same_screen = 17
inst._data_source = "danmu_api"
try:
    Danmu._generate_danmu_impl(inst, video)
    check("_generate_danmu_impl 透传 max_same_screen=17",
          captured2.get("max_same_screen") == 17, f"{captured2.get('max_same_screen')}")
finally:
    plugin_mod.generator.danmu_generator = orig_gen

# ==========================================================================
print("\n" + "=" * 70)
passed = sum(1 for _, ok, _ in RESULTS if ok)
print(f"结果: {passed}/{len(RESULTS)} 通过")
for name, ok, detail in RESULTS:
    if not ok:
        print(f"  FAILED: {name}  {detail}")
print("=" * 70)
sys.exit(0 if passed == len(RESULTS) else 1)
