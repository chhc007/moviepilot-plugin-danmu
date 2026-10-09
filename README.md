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
- **多数据源**：`dandanplay`（默认）/ `danmu_api`（扩展源）/ `hybrid`（混合）
  - danmu_api 覆盖国产剧/欧美剧/韩剧/真人电影/综艺（弹弹play 缺失部分）
  - 配置页按数据源联动显隐相关开关（danmu_api 模式隐藏「使用TMDB ID」等）

## 数据源配置（v1.12.0+）

| 配置项 | 说明 | 默认 |
|---|---|---|
| `data_source` | 数据源：dandanplay / danmu_api / hybrid | dandanplay |
| `danmu_api_url` | danmu_api 服务地址（非 dandanplay 模式显示） | `http://192.168.123.146:9321` |
| `danmu_api_token` | 自定义 TOKEN，留空则 URL 不带 token 段 | 空 |
| `danmu_api_priority` | hybrid 模式下 danmu_api 是否优先 | false |

**匹配管线（改造后）**：手动匹配 → 整季查询 → `/match`（含 A 方案候选校验）→ TMDB → **B 关键词搜索兜底** → **C danmu_api 源**

- A：`isMatched=false` 时按标题归一化 + 集号强校验挑候选，同分歧义放弃
- B：hash/TMDB 都失败后走 `/search/anime` 关键词兜底（日剧/国创主力）
- C：danmu_api 的 `/match` 主入口 + `search/episodes` 兜底；处理来源标签 `[bilibili1]`、animeTitle 剥壳、点赞后缀剥离、episodeId 不持久化

## 本地验证

```bash
cd plugins/danmu && python3 -m py_compile *.py        # 语法
node node_modules/vite/bin/vite.js build              # 前端构建
python3 ../tests/verify_v1_12_0.py                     # 真实联网三模式验证（需 requests/chardet）
```

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

- v1.12.0 — A+B+C 改造：A 放宽 /match 候选校验、B 关键词搜索兜底、C 新增 danmu_api 数据源；新增 data_source 等配置项与 Vue 联动；「优先B站」兼容 `[bilibili1]`
- v1.11.0 — 初始导入官方版（无定制），建立私有市场分发仓库

## 已知问题（待优化）

- **日剧匹配失败**：v1.12.0 起由 A（候选校验）/ B（关键词搜索）兜底解决，实测《非自然死亡》已可命中
- **TMDB 兜底对日剧无效**：中转服务 `/search/tmdb` 未建立日剧的 TMDB→弹弹映射（动画正常），返回空数组
