# danmu_api 集成最终设计（含开关联动与来源分析）

> 更新：2026-10-09，依据本地实例实测
> 用户决策：部署到 NAS，持久化在 /vol4/1000/DockerConfig，compose 在 dpanel/data/compose

## 一、关键实测结论：danmu_api 能区分弹幕来源 ✅

**每一条弹幕的 `p` 字段第 4 段就是独立来源标签**（源码 `convertToDanmakuJson` 实测确认）：

```
"1.00,1,16777215,[qiyi]"        # 爱奇艺
"7.61,1,15138834,[bilibili1]"   # B站（注意：是 bilibili1，不是 BiliBili）
"2.00,1,7885029,[youku]"        # 优酷
"...,[qq]"                      # 腾讯
"...,[renren]"                  # 人人（韩剧/欧美）
"...,[hanjutv]"                 # 韩剧TV
```

多源合并时用 `&`/`＆` 连接：`[bilibili1&dandan]`。

**实测数据**：
| 作品 | 类型 | 弹幕数 | 来源标签 |
|---|---|---|---|
| 生万物 E1 | 国产剧 | 13613 | `[qiyi]` |
| 手遮天 正片 | 华语电影 | 10446 | `[qiyi]` |
| 素手遮天 | 国产剧 | 12089 | `[qq]` |
| 泪之女王 E3 | 韩剧 | 6102 | `[renren]` |
| 葬送的芙莉莲 E1 | 日番 | 6635 | `[bilibili1]` |

→ **结论：可以做「B站优先」开关**。判据：`[bilibili1]`（danmu_api 的 B 站源键）或含 `bilibili` 的多源标签。

⚠ **注意差异**：danmu_api 用 `bilibili1`，现有插件 `_is_bili_comment()` 判的是 `[BiliBili]`。**两者不兼容**，需在适配层统一。

## 二、开关联动设计（用户要求）

**核心开关**：`data_source`（数据源模式）

| 模式 | 行为 |
|---|---|
| `dandanplay`（默认/原逻辑） | 完全走现有逻辑，行为零变化 |
| `danmu_api` | 走 danmu_api 为主源 |
| `hybrid`（可选） | 弹弹play 优先，失败时 fallback 到 danmu_api |

### 开关显隐联动（Vue 前端）

当 `data_source != "dandanplay"` 时：

| 配置项 | dandanplay 模式 | danmu_api 模式 |
|---|---|---|
| `useTmdbID`（使用TMDB ID） | 显示 | **隐藏**（danmu_api 走 /match 文件名词，不用 TMDB）|
| `onlyFromBili`（优先B站） | 显示 | **显示**（danmu_api 也支持来源过滤，见下）|
| `danmu_api_url` | 隐藏 | **显示** |
| `danmu_api_token` | 隐藏 | **显示** |
| `prefer_bilibili`（B站优先，新） | 隐藏 | **显示** |

> 用户原话：「如果走 danmu_api，则有些冲突无效的开关就隐藏掉。这样我关掉还能走原来的逻辑。」
> 实现：Vue 用 `v-if` 联动 `editableConfig.data_source`。

### B站优先在 danmu_api 下的实现

```python
# 拿到弹幕列表后，若开启 B站优先：
bili = [c for c in comments if 'bilibili' in _src_label(c)]
if len(bili) >= min_count:
    comments = bili   # 用B站
else:
    comments = comments  # 回退全量（沿用现有 _prefer_bili_comments 逻辑）
```
判据 `_src_label()`：取 `p` 第 4 段，判 `bilibili` 子串（兼容 `[bilibili1]` 和 `[bilibili1&dandan]`）。

## 三、搜索精准性（用户要求：按现有名称识别逻辑搜索，确保每集命中）

### 3.1 用 MP 识别的标题（不是原始文件名）

沿用现有逻辑：`media_chain.recognize_media(meta)` → `media_info.title`。

danmu_api 搜索用 `POST /api/v2/match`（fileName 传 `{标题} S{季}E{集}`）：

```python
r = POST {BASE}/api/v2/match  {"fileName": f"{title} S{season:02d}E{episode:02d}"}
# → matches[0].episodeId
```

**实测**：`生万物 S01E01` → isMatched=True、`泪之女王 S01E03` → isMatched=True ✅

### 3.2 每集命中保障（多层兜底）

```
1. POST /match  {"fileName": "{title} S{ss}E{ee}"}      ← 主路径，服务端择优
2. POST /match  {"fileName": "{title} 第{ee}集"}         ← 中文集号变体
3. GET /search/episodes?anime={title} → 按集号挑         ← 从 episodeTitle 解析集号
4. 失败 → 判定未收录
```

**关键**：danmu_api 的 `search/episodes` 响应里**没有 episodeNumber**，集号只能从 `episodeTitle` 解析（`【qiyi】 生万物第1集 ...` / `_01` / `第03集`）。所以优先用 `/match`（服务端已做好集号匹配）。

### 3.3 标题剥壳（danmu_api 返回的 animeTitle 被装饰）

`生万物(2025)【国产剧】from iqiyi` → 需剥掉 `(\d{4})`、`【..】`、`from ..` 才能比对。

## 四、部署方案（按用户指定路径）

### 4.1 持久化目录

```
/vol4/1000/DockerConfig/danmu-api/
├── config/          # .env（TOKEN、RATE_LIMIT、LIKE_SWITCH 等）
└── .cache/          # episodeId 计数器缓存（必须！否则重启漂移）
```

### 4.2 compose 文件

```
/vol4/@appshare/dpanel/data/compose/danmu-api/docker-compose.yaml
```

内容（格式对齐现有 moviepilot/nexusproxys 等）：

```yaml
services:
  danmu-api:
    image: logvar/danmu-api:latest
    container_name: danmu-api
    restart: always
    ports:
      - "9321:9321"
    volumes:
      - /vol4/1000/DockerConfig/danmu-api/config:/app/config
      - /vol4/1000/DockerConfig/danmu-api/.cache:/app/.cache
    environment:
      - TZ=Asia/Shanghai
      - RATE_LIMIT_MAX_REQUESTS=0    # 内网自用，关限流（默认3/分钟会拖垮批量刮削）
      - LIKE_SWITCH=false            # 不污染弹幕文本
```

### 4.3 部署后验证

```bash
curl "http://192.168.123.146:9321/api/v2/search/anime?keyword=生万物"
# 期望：success=true + animes 非空
```

## 五、⚠ 必须处理的坑（7 项，来自调研）

1. `p` 第4段是来源标签（非用户ID）→ `_is_bili_comment` 需扩展认 `bilibili1`
2. animeTitle 被装饰 → 剥壳
3. episodeId 是本地自增计数器（非 animeId*10000+n），重启漂移 → **现取现用**，不持久化；必须挂载 `.cache`
4. comment 成功响应无 `success/errorCode`；404 返回 `{count:0}`
5. 默认限流 3/分钟 → 部署时设 0
6. `m` 混入点赞 `"...♡232"` → 剥离 `\s*(♡|🔥)[\d.]+[wk]?`
7. 多源并列返回噪音 → 用 `/match` 让服务端择优

## 六、待办清单

- [ ] 部署 danmu_api 到 NAS（含 .cache 挂载）
- [ ] 插件：数据源抽象（DanmuSourceBase）
- [ ] 插件：danmu_api 源实现（match/search/comments + 剥壳 + 点赞剥离）
- [ ] 插件：开关联动（Vue v-if）
- [ ] 插件：B站优先适配（认 bilibili1）
- [ ] 插件：A+B（放宽match + 关键词兜底）
- [ ] 本地验证 + 部署验证
