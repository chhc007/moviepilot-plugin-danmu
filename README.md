# 弹幕刮削SHIELD专用版

使用弹弹play 平台生成弹幕字幕文件，实现不支持弹幕播放的设备也能看弹幕。

私有市场分发仓库，插件 ID `Danmu`（弹幕刮削SHIELD专用版）。

- **上游官方**：https://github.com/HankunYu/MoviePilot-Plugins （`plugins.v2/danmu`）
- **本仓库结构**：根 `package.json` + `plugins/danmu/`（MoviePilot 私有市场分发规范）
- **中转服务**：插件通过作者自建中转 `dandanapi.hankun.online` 访问弹弹play（官方 API 已强制 AppId 认证）

## 功能

- 按文件 hash / TMDB ID 匹配弹弹play 弹幕，转成 `.danmu.ass` 字幕
- 找到原生字幕时合并成 `.withDanmu.ass`（弹幕 + 字幕一轨）
- 支持「优先使用B站弹幕」（B站不足自动回退全源）
- 支持屏幕区域选择（全屏/半屏/1/4屏）、`.strm` 流媒体文件
- 整季查询：同一部剧后续集数零请求定位

## 维护方式（合并官方更新）

官方更新时按以下流程合并代码到本仓库：

```bash
# 1. 拉取官方最新
git remote add upstream https://github.com/HankunYu/MoviePilot-Plugins.git   # 首次
git fetch upstream main

# 2. 对比官方目录与本仓库差异（官方在 plugins.v2/，本仓在 plugins/）
git diff upstream/main -- plugins.v2/danmu

# 3. 将官方目录差异应用到本仓
git checkout upstream/main -- plugins.v2/danmu
#   （官方目录在 plugins.v2/ 下，需拷贝到 plugins/ 再整理）

# 4. 手动解决定制冲突（保留 chhc007 定制改动）

# 5. 同步根 package.json 版本与 history，提交
```

> 注意：官方目录结构为 `plugins.v2/<name>`，本仓库分发结构为 `plugins/<name>`，合并时注意路径映射。

## 定制记录

- v1.11.0 — 初始导入官方版（无定制），建立私有市场分发仓库

## 已知问题（待优化）

- **日剧匹配失败**：`/match` 接口对无精确 hash 命中的文件返回 `isMatched: false`，但 `matches` 候选列表首条往往就是正确条目；插件仅认 `isMatched`，导致直接放弃（报「未收录」）。动画番剧因 hash 库覆盖好不受影响，日剧（迅雷下载版）普遍命中。
- **TMDB 兜底对日剧无效**：中转服务 `/search/tmdb` 未建立日剧的 TMDB→弹弹映射（动画正常），返回空数组。
