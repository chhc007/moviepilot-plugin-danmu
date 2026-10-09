# C 方案设计：集成 danmu_api 第二数据源

> 依据：research-agent 调研报告（2026-10-09，本地实例实测）
> 目标：覆盖弹弹play 缺失的国剧/欧美剧/韩剧/真人电影/综艺

## 一、danmu_api 关键事实（实测）

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/huangxd-/danmu_api （AGPL-3.0，3257 star，活跃维护） |
| 部署 | Docker：`logvar/danmu-api:latest`（500K+ 拉取，多架构） |
| 端口 | 默认 9321 |
| 鉴权 | 默认 TOKEN=87654321 可省略；自定义 TOKEN 时必须作**路径首段** `{BASE}/{TOKEN}/api/v2/...` |
| 公开实例 | ❌ 无。必须自建 |
| 覆盖 | 国产剧/欧美剧/韩剧/真人电影/综艺/动画 —— 23 个源 |

## 二、接口（与弹弹play 同构但有差异）

### 2.1 推荐主入口：`POST /api/v2/match`（一步拿 episodeId）

```json
POST /api/v2/match
{"fileName": "生万物 S01E01"}
→ {"success":true, "isMatched":true, "matches":[
     {"episodeId":10538, "animeId":6525375,
      "animeTitle":"生万物(2025)【国产剧】from iqiyi",
      "episodeTitle":"【qiyi】 生万物第1集 绣绣大婚当日遭抢亲",
      "type":"国产剧", "shift":0}
   ]}
```
- **isMatched 语义可靠**（实测 true），比弹弹play 中转的 match 靠谱
- 支持 `@qiyi` 指定平台：`{"fileName": "赴山海 S01E28 @qiyi"}`

### 2.2 搜索：`GET /api/v2/search/episodes?anime={标题}`

```json
{"success":true, "animes":[
  {"animeId":6525375, "animeTitle":"生万物(2025)【国产剧】from iqiyi",
   "episodes":[{"episodeId":10038, "episodeTitle":"【qiyi】 生万物第1集 ...", "url":"..."}]}
]}
```

### 2.3 弹幕正文：`GET /api/v2/comment/{episodeId}?format=json`

```json
{"count":13614, "comments":[
  {"cid":1, "p":"1.00,1,16777215,[qiyi]", "m":"二刷站过来[吃瓜] ♡232", "t":1}
]}
```

## 三、⚠ 必须处理的 7 个坑

### 坑 1：`p` 字段第 4 段是来源标签，不是用户 ID
- 弹弹play：`时间,模式,颜色,用户ID`（如 `...,48454cb2`）
- danmu_api：`时间,模式,颜色,[源标签]`（如 `...,[qiyi]`）
- **影响 `_is_bili_comment()`**：它判断 `'[BiliBili]' in fields[3]`，而 danmu_api 的 B 站写 `[bilibili1]` → **永远匹配不上**，「优先B站」静默失效
- **修法**：适配层映射 `[bilibili1]` → `[BiliBili]`，或扩展 `_is_bili_comment` 同时认 `bilibili1`

### 坑 2：`animeTitle` 被装饰
`生万物(2025)【国产剧】from iqiyi` —— 需正则剥掉 `(\d{4})`、`【..】`、`from ..` 才能做标题比对

### 坑 3：episodeId 是**本地自增计数器**（从 10001 起）
- 不是 `animeId*10000+n`，与弹弹play 语义完全不同
- **进程重启后重新分配**（除非挂载 `.cache`）
- **不可持久化**：每次刮削现取现用，缓存键用 `(源名, animeTitle, episodeTitle, url)`
- 已知 bug #472：episodeId 缓存绑定错位（仍 open）

### 坑 4：响应结构差异
- comment 成功响应**无** `errorCode/success/errorMessage`，就是 `{count, comments}`
- 404 时返回 `{count:0,comments:[]}` + HTTP 404
- `episodes` 里**没有 episodeNumber**，集号要靠 `episodeTitle` 解析

### 坑 5：默认限流 **3 次/分钟/IP**
- 实测连续请求撞 429
- 部署时调大 `RATE_LIMIT_MAX_REQUESTS` 或设 0（内网自用）

### 坑 6：`m` 字段混入点赞信息
`"二刷站过来[吃瓜] ♡232"` —— 需剥掉尾部 `\s*(♡|🔥)[\d.]+[wk]?`，或部署时 `LIKE_SWITCH=false`

### 坑 7：多源并列返回噪音
一次搜索返回 2~20+ 条（含解说版/合集/动态海报）。需 `STRICT_TITLE_MATCH=true` 或用 `POST /match` 让服务端择优

## 四、集成架构设计

### 4.1 数据源抽象（改造现有硬编码）

**现状**：`DanmuAPI.BASE_URL` 硬编码唯一源。

**改造**：抽出源接口

```python
class DanmuSourceBase:
    source_id: str
    def match(self, file_name, **kw) -> Optional[str]: ...      # 返回 episodeId
    def search(self, title, **kw) -> List[dict]: ...             # 作品候选
    def get_comments(self, episode_id) -> Optional[dict]: ...    # 弹幕正文

class DandanplaySource(DanmuSourceBase):   # 包装现有 DanmuAPI（中转服务）
class DanmuApiSource(DanmuSourceBase):     # 新增（danmu_api）
```

### 4.2 匹配管线（最终）

```
手动匹配
  → 整季查询（弹弹play）
  → /match 哈希（弹弹play）
  → TMDB（弹弹play）
  → 【B】关键词搜索（弹弹play /search/anime）
  → 【C1】danmu_api POST /match
  → 【C2】danmu_api search/episodes
  → 判定未收录
```

### 4.3 配置项（新增）

| 配置 | 默认 | 说明 |
|---|---|---|
| `enable_danmu_api` | false | 启用第二数据源 |
| `danmu_api_url` | `http://192.168.123.146:9321` | 服务地址 |
| `danmu_api_token` | 空 | 自定义 TOKEN（空=默认，走 `/api/v2/...`） |
| `danmu_api_on_fallback_only` | true | 仅弹弹play 失败时才用（省请求） |

### 4.4 部署

按用户规范：`~/workspace/docker/danmu-api-deploy/`

```yaml
services:
  danmu-api:
    image: logvar/danmu-api:latest
    container_name: danmu-api
    ports: ["9321:9321"]
    volumes:
      - ./config:/app/config
      - ./.cache:/app/.cache      # 必须！否则 episodeId 重启漂移
    environment:
      - RATE_LIMIT_MAX_REQUESTS=0   # 内网自用，关限流
      - LIKE_SWITCH=false           # 不污染弹幕文本
    restart: unless-stopped
```

**部署位置待定**：本机(70) 还是 NAS(146)？→ 需用户确认

## 五、验收标准

- [ ] 国产剧（生万物）经 danmu_api 拿到弹幕
- [ ] 韩剧（泪之女王）/欧美剧/真人电影/综艺 各测 1 部
- [ ] 弹弹play 原有行为不回归（动画/日剧）
- [ ] 「优先B站」在 danmu_api 源下正确工作（或明确降级为全量）
- [ ] 点赞标记已剥离、限流已处理
- [ ] 未收录判定正确

## 六、待用户确认

1. **部署位置**：本机 70 / NAS 146？
2. **是否保留探测实例目录** `~/workspace/danmu_api_probe/`（115M）？
3. **`onlyFromBili` 在 danmu_api 下的语义**：danmu_api 是聚合源（爱奇艺+腾讯+B站…），"仅B站"无意义 → 建议该源下忽略此开关
