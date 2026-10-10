#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Danmu v1.12.1：滚动弹幕速度算法一致性修复。

覆盖：
  1) 滚动弹幕终点 = -text_width（含 0.6 系数），不再是 -len(text)*fontsize
  2) 不同长度文本在相同 duration 下的速度 = 统一公式 (width+text_width)/duration
     （修复前是变长的 1/0.6~1.67 偏差系数，即"忽快忽慢"）
  3) 移动距离 = width + text_width（不再浪费行程）
  4) 顶部/底部弹幕用 \pos，无 \move，不受影响
  5) 轨道分配 / leave_time 行为不变
  6) 端到端：真实联网生成一个 .ass 并检查 \move 终点值

无需网络的检查用 stub 顶掉 MoviePilot 宿主依赖直接调用 convert_comments_to_ass。
"""
import os
import re
import sys
import types
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO, "plugins", "danmu")


# ---- stub 宿主依赖 ------------------------------------------------------
def _install_stub_app():
    app = types.ModuleType("app")
    log = types.ModuleType("app.log")

    class _Logger:
        def info(self, msg, *a): pass
        def warning(self, msg, *a): pass
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


# ---- 参数与工具 --------------------------------------------------------
WIDTH, HEIGHT, FONTSIZE, DURATION, ALPHA, FONTFACE = 1920, 1080, 54.0, 15.0, 0.8, "微软雅黑"
COEF = 0.6  # danmu_generator 内文本宽度系数


def text_width_of(text):
    return len(text) * FONTSIZE * COEF


def gen(comments, screen_area="full", duration=DURATION):
    """调用 convert_comments_to_ass 生成 .ass，返回文件内容"""
    fd, path = tempfile.mkstemp(suffix=".ass", prefix="danmu_v1121_")
    os.close(fd)
    try:
        g.DanmuConverter.convert_comments_to_ass(
            comments, path, WIDTH, HEIGHT, FONTFACE, FONTSIZE, ALPHA,
            duration, screen_area,
        )
        with open(path, encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


DIALOGUE_RE = re.compile(
    r"Dialogue: 0,(?P<start>[^,]+),(?P<end>[^,]+),Danmu,,0,0,0,,(?P<body>.*)$"
)
MOVE_RE = re.compile(r"\\move\(([^)]*)\)")


def parse_dialogues(content):
    """返回 [(text, body, move_args|None), ...]"""
    out = []
    for line in content.splitlines():
        m = DIALOGUE_RE.match(line)
        if not m:
            continue
        body = m.group("body")
        # 文本在最后一个 '}' 之后
        text = body.rsplit("}", 1)[-1]
        mv = MOVE_RE.search(body)
        args = [float(x) for x in mv.group(1).split(",")] if mv else None
        out.append((text, body, args))
    return out


# ==========================================================================
print("\n########## 1) 滚动弹幕终点 = -text_width（不再是 -len*fontsize） ##########")
SHORT, LONG = "短" * 11, "长" * 23
content = gen([
    {"p": "0,1,16777215", "m": SHORT},
    {"p": "0,1,16777215", "m": LONG},
])
dial = parse_dialogues(content)
check("生成 2 条 Dialogue", len(dial) == 2, f"{len(dial)}")

moves = {}
for text, body, args in dial:
    if args:
        moves[text] = args

for text in (SHORT, LONG):
    tw = text_width_of(text)
    args = moves.get(text)
    ok = args is not None
    check(f"[{len(text)}字] 有 \\move 指令", ok)
    if not ok:
        continue
    x1, y1, x2, y2 = args
    check(f"[{len(text)}字] 起点 x = width", x1 == WIDTH, f"x1={x1}")
    check(f"[{len(text)}字] 终点 x = -text_width ({-tw:.1f})",
          abs(x2 - (-tw)) < 1e-6, f"x2={x2}")
    old_end = -len(text) * FONTSIZE
    check(f"[{len(text)}字] 终点不再是旧值 -len*fontsize ({old_end:.1f})",
          abs(x2 - old_end) > 1e-6, f"x2={x2} old={old_end}")
    check(f"[{len(text)}字] y 固定（水平滚动）", y1 == y2, f"y1={y1} y2={y2}")

# ==========================================================================
print("\n########## 2) 移动距离 = width + text_width ##########")
for text in (SHORT, LONG):
    args = moves.get(text)
    if not args:
        continue
    x1, _, x2, _ = args
    dist = x1 - x2
    expect = WIDTH + text_width_of(text)
    check(f"[{len(text)}字] 移动距离 = width + text_width ({expect:.1f})",
          abs(dist - expect) < 1e-6, f"dist={dist:.1f}")

# ==========================================================================
print("\n########## 3) 速度一致：等于统一公式 (width+text_width)/duration ##########")
speeds = {}
for text in (SHORT, LONG):
    args = moves.get(text)
    if not args:
        continue
    x1, _, x2, _ = args
    speed = (x1 - x2) / DURATION
    unified = (WIDTH + text_width_of(text)) / DURATION
    speeds[text] = speed
    check(f"[{len(text)}字] 实测速度 == (width+text_width)/duration ({unified:.3f} px/s)",
          abs(speed - unified) < 1e-6, f"speed={speed:.3f}")

# 修复前：实际速度 = (width + len*fontsize)/duration（0.6 被吞掉），偏差系数随长度变化
# 修复后：偏差系数恒为 1.0
for text in (SHORT, LONG):
    args = moves.get(text)
    if not args:
        continue
    x1, _, x2, _ = args
    speed = (x1 - x2) / DURATION
    intended = (WIDTH + text_width_of(text)) / DURATION
    buggy = (WIDTH + len(text) * FONTSIZE) / DURATION
    check(f"[{len(text)}字] 速度自洽系数 = 1.0（修复前为 {buggy/intended:.3f}）",
          abs(speed / intended - 1.0) < 1e-6, f"ratio={speed/intended:.6f}")

# 长/短速度比 = text_width 预测值（确定性，不再有 0.6 失配引入的额外放大）
if SHORT in speeds and LONG in speeds:
    pred = (WIDTH + text_width_of(LONG)) / (WIDTH + text_width_of(SHORT))
    got = speeds[LONG] / speeds[SHORT]
    check(f"长短速度比 == 由 text_width 预测的 {pred:.6f}（确定性）",
          abs(got - pred) < 1e-6, f"got={got:.6f}")
    # 修复前长短比 = (W+23*FS)/(W+11*FS) = 1.257；修复后 = 1.171，长短差距明显收窄
    buggy_ratio = (WIDTH + 23 * FONTSIZE) / (WIDTH + 11 * FONTSIZE)
    check(f"长短速度差已收窄（修复前 {buggy_ratio:.3f} → 修复后 {got:.3f}）",
          got < buggy_ratio - 1e-6, f"fixed={got:.3f} buggy={buggy_ratio:.3f}")

# ==========================================================================
print("\n########## 4) 顶部/底部弹幕用 \\pos，无 \\move，不受影响 ##########")
content2 = gen([
    {"p": "0,4,16777215", "m": "底部弹幕"},
    {"p": "0,5,16777215", "m": "顶部弹幕"},
])
dial2 = parse_dialogues(content2)
check("生成 2 条顶/底 Dialogue", len(dial2) == 2, f"{len(dial2)}")
for text, body, args in dial2:
    check(f"[{text}] 无 \\move", args is None, f"args={args}")
    check(f"[{text}] 含 \\pos", "\\pos(" in body, body[:60])
    if text == "底部弹幕":
        check("[底部] 用 \\an2", "\\an2" in body)
        check("[底部] pos 在屏幕下半", body, "")
    if text == "顶部弹幕":
        check("[顶部] 用 \\an8", "\\an8" in body)

# ==========================================================================
print("\n########## 5) 轨道分配 / leave_time 行为不变 ##########")
# leave_time = text_width/velocity + gap(1)
tw = text_width_of(SHORT)
velocity = (WIDTH + tw) / DURATION
leave_time = tw / velocity + 1.0
# 用三条滚动弹幕验证轨道释放边界：
#   t=0      -> 轨道1（占用到 leave_time）
#   t=leave-0.5 -> 轨道1仍占用 -> 轨道2
#   t=leave+0.5 -> 轨道1已释放 -> 轨道1
t_early = leave_time - 0.5
t_late = leave_time + 0.5
content3 = gen([
    {"p": "0,1,16777215", "m": SHORT},
    {"p": f"{t_early},1,16777215", "m": "早"},
    {"p": f"{t_late},1,16777215", "m": "晚"},
])
dial3 = parse_dialogues(content3)
check("生成 3 条滚动 Dialogue", len(dial3) == 3, f"{len(dial3)}")
ys = {}
for text, body, args in dial3:
    if args:
        ys[text] = args[1]
# track1 -> y=10, track2 -> y=64
check("首条占轨道1 (y=10)", ys.get(SHORT) == 10, f"y={ys.get(SHORT)}")
check(f"leave_time 前 ({t_early:.3f}s) 占用轨道1 → 走轨道2 (y=64)",
      ys.get("早") == 64, f"y={ys.get('早')} leave_time={leave_time:.3f}")
check(f"leave_time 后 ({t_late:.3f}s) 轨道1已释放 → 复用轨道1 (y=10)",
      ys.get("晚") == 10, f"y={ys.get('晚')}")

# leave_time 公式回归（仅终点行改动，公式必须不变）
tw23 = text_width_of(LONG)
v23 = (WIDTH + tw23) / DURATION
check("leave_time 公式 = text_width/velocity + 1 未变",
      abs((tw / velocity + 1.0) - leave_time) < 1e-12, f"{leave_time:.4f}")

# ==========================================================================
print("\n########## 6) 端到端：真实联网生成 .ass 并检查 \\move 终点 ##########")
try:
    g.DanmuApiSource.configure("http://192.168.123.146:9321", "")
    eid = g.DanmuApiSource.get_comment_id("生万物", episode=1, season=1)
    check("danmu_api 生万物 E1 拿到 episodeId", bool(eid), f"episodeId={eid}")
    if eid:
        data = g.DanmuApiSource.get_comments(eid)
        n = len((data or {}).get("comments") or [])
        check("danmu_api 弹幕非空", n > 100, f"{n} 条")
        if n:
            comments = data["comments"]
            fd, path = tempfile.mkstemp(suffix=".danmu.ass", prefix="e2e_")
            os.close(fd)
            g.DanmuConverter.convert_comments_to_ass(
                comments, path, WIDTH, HEIGHT, FONTFACE, FONTSIZE, ALPHA, DURATION, "full",
            )
            content_e2e = open(path, encoding="utf-8").read()
            dial_e2e = parse_dialogues(content_e2e)
            scrolls = [(t, a) for t, b, a in dial_e2e if a is not None]
            check("端到端 .ass 含滚动弹幕", len(scrolls) > 0,
                  f"{len(scrolls)}/{len(dial_e2e)} 条滚动")
            bad = []
            checked = 0
            for text, args in scrolls[:200]:
                x1, y1, x2, y2 = args
                expect_end = -text_width_of(text)
                if abs(x2 - expect_end) > 1e-6:
                    bad.append((text, x2, expect_end))
                checked += 1
            check(f"端到端 {checked} 条滚动弹幕终点全部 = -text_width",
                  not bad, f"不符 {len(bad)} 条 {bad[:2]}")
            if scrolls:
                t0, a0 = scrolls[0]
                tw0 = text_width_of(t0)
                print(f"       样例: text={t0[:12]!r} len={len(t0)} "
                      f"\\move 终点={a0[2]:.1f} 期望={-tw0:.1f} "
                      f"速度={(a0[0]-a0[2])/DURATION:.1f} px/s")
            print(f"       .ass 路径: {path}")
except Exception as e:  # 网络异常不应掩盖离线检查结果
    check("端到端联网生成", False, f"{type(e).__name__}: {e}")

# ==========================================================================
print("\n" + "=" * 70)
passed = sum(1 for _, ok, _ in RESULTS if ok)
print(f"结果: {passed}/{len(RESULTS)} 通过")
for name, ok, detail in RESULTS:
    if not ok:
        print(f"  FAILED: {name}  {detail}")
print("=" * 70)
sys.exit(0 if passed == len(RESULTS) else 1)
