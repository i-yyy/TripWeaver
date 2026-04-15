# 云途智织——TripWeaver 🌍✈️

基于 HelloAgents 框架构建的智能旅行规划与社区协同平台。系统集成高德地图 MCP 服务、本地 RAG 知识库、用户画像与记忆、社区交流、Two-Tower + xDeepFM 个性化推荐，以及好友共同编辑行程能力，为用户提供从“生成路线”到“分享交流”再到“多人共创”的完整旅行规划闭环。

## ✨ 功能特点

- 🤖 **AI 驱动旅行规划**：基于 HelloAgents 和多智能体协同生成多日旅行方案，覆盖景点、酒店、天气、交通、餐饮和预算。
- 🧩 **多智能体协同**：景点智能体、天气智能体、酒店智能体、规划智能体与 supervisor 协作，降低单智能体规划不稳定的问题。
- 🗺️ **高德地图集成**：通过 MCP 与高德地图能力结合，支持 POI 搜索、天气查询、步行/驾车/公交路线规划和每日路线地图展示。
- 📚 **RAG 本地知识库**：支持 Markdown + Frontmatter 入库、Qdrant 向量检索、Reranker 重排和推荐依据输出。
- 🧪 **RAG 评测能力**：开发者可访问 `/kb-eval`，对检索召回、Top-K、命中率、Top1 增益和重排效果做在线评测。
- 👤 **用户画像与记忆系统**：记录偏好、反馈、历史行程、预算、交通、出行人群等信息，参与后续推荐与规划。
- 💬 **登录后社区交流页**：登录后进入社区页面，支持朋友圈式动态、图片上传、点赞、评论、回复、关注作者和关联旅行规划。
- 🎯 **个性化旅行卡片推荐**：推荐卡片来自内置路线、社区 UGC 动态与用户行为数据，使用 Two-Tower 召回 + xDeepFM 精排的推荐流程。
- 🪪 **个人主页**：展示头像、昵称、邮箱、性别、粉丝、关注、发布动态卡片，并提供单独的账号信息编辑入口。
- 🧭 **旅行轨迹与规划保存**：每次生成的旅行规划都会保存到数据库，旅行轨迹页面可点击地点回看对应规划结果。
- 🔗 **帖子关联规划**：发布社区动态时可选择本地旅行规划，其他用户点击后可跳转查看对应规划结果。
- 🤝 **好友协同行程**：可从已有旅行轨迹创建协同行程，邀请好友共同编辑，支持权限、评论、景点投票、修改记录、删除/退出。
- 🖼️ **图片本地上传**：头像和社区动态图片均支持本地上传，后端统一通过 `/uploads` 静态资源路径提供访问。
- 🎨 **现代化前端体验**：Vue 3 + TypeScript + Vite + Ant Design Vue，包含卡片式结果页、地图轨迹页、社区瀑布/横滑卡片和协同行程编辑页。

## 🏗️ 技术栈

### 后端

- **API 框架**：FastAPI
- **智能体框架**：HelloAgents / SimpleAgent
- **数据库**：SQLite + SQLModel
- **向量检索**：Qdrant + Embedding + Reranker
- **地图与位置服务**：高德地图 MCP / 高德 Web 服务 API
- **LLM**：支持 OpenAI、DeepSeek 及兼容 OpenAI API 的模型网关
- **文件上传**：FastAPI UploadFile + 本地 `backend/uploads`

### 前端

- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **UI 组件库**：Ant Design Vue
- **地图展示**：高德地图 JavaScript API
- **HTTP 客户端**：Axios
- **状态与工具**：本地 auth 工具、媒体 URL 解析、头像生成工具

## 📁 项目结构

```text
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/                  # 多智能体：景点、天气、酒店、规划、监督
│   │   ├── api/
│   │   │   ├── main.py              # FastAPI 入口
│   │   │   └── routes/
│   │   │       ├── auth.py          # 注册、登录、头像、账号信息
│   │   │       ├── collab.py        # 好友协同行程
│   │   │       ├── community.py     # 社区动态、推荐卡片、关注、评论
│   │   │       ├── feedback.py      # 用户反馈
│   │   │       ├── kb.py            # 知识库入库、检索、评测
│   │   │       ├── map.py           # 地图、天气、路线
│   │   │       ├── poi.py           # POI 与图片
│   │   │       ├── tracks.py        # 旅行轨迹与保存规划
│   │   │       ├── trip.py          # 行程生成
│   │   │       └── user.py          # 用户画像
│   │   ├── db/
│   │   │   ├── database.py          # 数据库初始化与 SQLite 迁移
│   │   │   └── models.py            # 用户、社区、协同、记忆、反馈等表
│   │   ├── models/                  # Pydantic 请求/响应模型
│   │   ├── services/                # 业务服务层
│   │   │   ├── auth_service.py
│   │   │   ├── collab_service.py
│   │   │   ├── community_service.py
│   │   │   ├── knowledge_base_service.py
│   │   │   ├── memory_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── retriever_service.py
│   │   │   ├── reranker_service.py
│   │   │   └── tracks_service.py
│   │   ├── skills/                  # 旅行技能注册与匹配
│   │   └── tasks/                   # 知识库入库与离线评测脚本
│   ├── data/knowledge_base/         # 本地 Markdown 知识库
│   ├── uploads/                     # 头像、社区图片等上传文件
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/              # 地图等复用组件
│   │   ├── router/                  # 前端路由
│   │   ├── services/api.ts          # API 封装
│   │   ├── styles/brand-theme.css   # 全局品牌视觉
│   │   ├── types/index.ts           # TypeScript 类型
│   │   ├── utils/                   # 鉴权、头像、社区卡片、地图样式
│   │   └── views/
│   │       ├── Community.vue        # 社区首页
│   │       ├── CommunityCardDetail.vue
│   │       ├── CollabTrips.vue      # 协同行程列表
│   │       ├── CollabTripDetail.vue # 协同行程卡片式编辑页
│   │       ├── Home.vue             # 旅行规划表单
│   │       ├── Result.vue           # 行程结果页
│   │       ├── Tracks.vue           # 旅行轨迹
│   │       ├── Profile.vue          # 个人主页
│   │       └── KBEval.vue           # RAG 评测页
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🚀 快速开始

### 前提条件

- Conda / Anaconda
- Node.js 18+
- 高德地图 Web 服务 API Key
- 可用的 LLM Key，建议填写 `OPENAI_API_KEY` 或 `LLM_API_KEY`
- 可选：Qdrant，用于完整知识库向量检索与评测

### 后端启动（必须使用 Conda 环境）

```powershell
cd backend
conda create -n trip-planner python=3.10 -y
conda activate trip-planner
python -m pip install -U pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `backend/.env`，至少填写：

```env
AMAP_API_KEY=你的高德Web服务Key
OPENAI_API_KEY=你的模型Key
OPENAI_BASE_URL=你的模型网关地址(可选)
OPENAI_MODEL=模型名(可选)
DEVELOPER_EMAIL_WHITELIST=your-email@example.com,teammate@example.com
```

启动后端：

```powershell
conda activate trip-planner
cd backend
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

说明：

- `DEVELOPER_EMAIL_WHITELIST` 中的邮箱登录后会显示 `RAG评测` 入口。
- 非白名单用户访问 `/kb-eval` 和相关 KB 评测接口会被拦截。
- 后端启动时会执行数据库初始化，自动创建用户、社区、协同、轨迹、反馈、画像等表。

### 前端启动

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

浏览器打开：

- 地球主页面：`http://localhost:5173/`
- 登录后社区页：`http://localhost:5173/community`
- 旅行规划：`http://localhost:5173/planner`
- 旅行轨迹：`http://localhost:5173/tracks`
- 协同行程：`http://localhost:5173/collab`
- 个人主页：`http://localhost:5173/profile`
- RAG 评测页：`http://localhost:5173/kb-eval`，仅开发者白名单用户可见

## 📚 可选：知识库向量入库与评测

如果需要完整运行 RAG 向量检索，先启动 Qdrant：

```powershell
docker run -p 6333:6333 qdrant/qdrant
```

然后在 `backend` 目录执行：

```powershell
conda activate trip-planner
python -m app.tasks.ingest_kb --clear
python -m app.tasks.evaluate_kb --top-k 6
```

评测报告输出到：

```text
backend/data/knowledge_base/eval_report.md
```

## 📝 使用指南

### 1. 👤 注册与个人主页

1. 访问 `/register` 注册账号。
2. 登录后进入 `/profile`。
3. 可以编辑头像、昵称、邮箱、性别。
4. 个人主页会展示粉丝数、关注数、发布动态数量，以及自己发布过的帖子卡片。

### 2. 🧭 生成旅行规划

1. 访问 `/planner`。
2. 填写目的地、旅行日期、交通方式、住宿偏好、预算、旅行风格、人群、行动能力需求等信息。
3. 点击生成旅行计划。
4. 系统会调用多智能体规划流程，并结合 RAG、用户画像、历史记忆和地图工具生成结果。

结果页支持：

- 行程总览
- 预算汇总
- 每日地图路线
- 景点卡片
- 酒店推荐
- 餐饮推荐
- 天气信息
- 推荐依据
- 满意/不满意反馈
- 景点喜欢/不喜欢反馈
- 编辑景点顺序和行程内容
- 导出 PDF

### 3. 🗺️ 旅行轨迹

每次成功生成旅行规划后，系统会保存到数据库。访问 `/tracks` 可以：

- 查看搜索过/规划过的城市轨迹
- 在地图上播放旅行轨迹
- 点击轨迹地点跳转到对应规划结果页
- 删除某条旅行轨迹

### 4. 💬 社区交流与个性化推荐

登录后的 `/community` 是社区交流页，包含两个核心区域：

- 🎯 **为你推荐的旅行卡片**：展示图片、一句话描述和标签，点击可进入详情页评论、点赞、收藏、复用。
- 🧳 **旅行动态**：类似朋友圈，展示用户发布的帖子、图片、点赞、评论、回复、关注和关联规划入口。

社区动态支持：

- 发布文字动态
- 上传本地图片，最多 9 张
- 图片在主界面以正方形展示，点击后可查看原图
- 点赞与评论
- 点击评论进行回复
- 关注作者
- 发布时关联自己的旅行规划
- 其他用户点击“查看关联规划”跳转到规划结果页

### 5. 🎯 推荐算法说明

社区推荐采用“候选池 + Two-Tower 召回 + xDeepFM 精排”的结构：

- 候选池包含内置精品路线、社区动态生成的 UGC 路线卡片、用户互动后的路线记录。
- Two-Tower 负责从用户画像、近期城市、偏好标签、反馈标签中快速召回可能匹配的路线。
- xDeepFM 负责在候选内容中进一步精排，综合显式/隐式特征交互、社区热度、收藏、复用、点赞、评论等因素。
- 点击“刷新推荐”会引入探索因子，让推荐顺序产生变化，避免固定展示同一批内容。

### 6. 🤝 好友共同编辑行程

访问 `/collab` 可以使用协同行程功能：

1. 从已有旅行轨迹创建协同行程。
2. 管理员邀请好友加入，可设置“可编辑”或“仅查看”。
3. 好友在协同行程页处理待接受邀请。
4. 进入协同行程详情页后，可以卡片式查看和编辑每日行程。
5. 可编辑成员可以修改整体建议、每日概览、交通、住宿、路线备注和景点顺序。
6. 所有成员都可以评论整份行程或某一天。
7. 所有成员都可以对景点投票“想去”。
8. 系统记录创建、邀请、接受/拒绝、编辑、退出等修改记录。
9. 管理员可以删除整份协同行程，普通成员可以退出协同行程。

## 🔧 核心实现

### 🧩 多智能体旅行规划

后端将旅行规划拆成多个层次：

- `attraction_agent.py`：景点检索与景点候选整理
- `weather_agent.py`：天气查询与天气约束
- `hotel_agent.py`：酒店推荐
- `planning_agent.py`：综合生成每日行程
- `supervisor_agent.py`：调度多个智能体并汇总结果
- `skill_service.py`：根据用户输入和画像匹配旅行技能
- `plan_constraint_validator.py`：对预算、天气、行动能力等约束做修正

### 👤 用户画像与反馈闭环

用户在规划和社区中的行为会沉淀到画像与反馈中：

- 旅行表单会更新交通、住宿、预算、人群、兴趣偏好等字段。
- 结果页反馈会记录喜欢/不喜欢/满意/不满意。
- 社区卡片点赞、收藏、复用、评论会作为个性化推荐信号。
- 社区帖子点赞和评论也会反馈到用户偏好。

### 💬 社区内容生成路线卡片

用户发布社区动态后，系统会根据内容、城市、标签和首图生成社区路线卡片，进入推荐候选池。这样推荐不只依赖内置路线，也可以吸收真实用户分享。

### 🤝 协同行程数据模型

协同行程由以下表维护：

- `collab_trips`：协同行程主体、标题、城市、来源轨迹、当前版本、`plan_json`
- `collab_trip_members`：成员、角色、状态
- `collab_trip_invites`：邀请记录、邀请人、被邀请人、角色、状态
- `collab_trip_comments`：评论，支持关联到整份行程或某一天
- `collab_trip_votes`：景点投票
- `collab_trip_changes`：修改记录与版本留痕

## 📄 API 文档

启动后端服务后访问：

```text
http://localhost:8000/docs
```

主要端点：

### 🔐 认证与用户

- `POST /api/auth/register`：注册
- `POST /api/auth/login`：登录
- `GET /api/auth/me`：获取当前用户
- `PUT /api/auth/profile`：更新昵称、邮箱、性别
- `POST /api/auth/avatar`：上传头像
- `PUT /api/auth/password`：修改密码
- `DELETE /api/auth/me`：注销账号
- `GET /api/user/profile/me`：获取当前用户画像

### 🧭 行程规划与地图

- `POST /api/trip/plan`：生成旅行计划
- `GET /api/map/poi`：搜索 POI
- `GET /api/map/weather`：查询天气
- `POST /api/map/route`：规划路线
- `POST /api/map/day-route`：生成每日路线详情
- `GET /api/poi/photo`：获取景点图片

### 🗺️ 旅行轨迹

- `GET /api/tracks`：获取旅行轨迹
- `GET /api/tracks/{track_id}/plan`：获取某条轨迹对应的规划结果
- `DELETE /api/tracks/{track_id}`：删除旅行轨迹

### 💬 社区交流与推荐

- `GET /api/community/feed`：获取个性化社区推荐
- `GET /api/community/posts`：获取旅行动态
- `POST /api/community/posts`：发布旅行动态
- `POST /api/community/uploads/image`：上传社区图片
- `POST /api/community/posts/{post_id}/like`：点赞/取消点赞动态
- `POST /api/community/posts/{post_id}/comments`：评论动态
- `GET /api/community/posts/{post_id}/plan`：获取动态关联的规划
- `POST /api/community/users/{target_user_id}/follow`：关注/取消关注作者
- `GET /api/community/profile/me`：获取社区个人主页数据
- `POST /api/community/cards/{card_id}/like`：点赞/取消点赞推荐卡片
- `POST /api/community/cards/{card_id}/favorite`：收藏/取消收藏推荐卡片
- `POST /api/community/cards/{card_id}/reuse`：复用推荐卡片
- `POST /api/community/cards/{card_id}/comments`：评论推荐卡片

### 🤝 协同行程

- `GET /api/collab/trips`：获取我的协同行程和待处理邀请
- `POST /api/collab/trips`：从旅行轨迹创建协同行程
- `GET /api/collab/trips/{trip_id}`：获取协同行程详情
- `PUT /api/collab/trips/{trip_id}/plan`：保存协同行程编辑结果
- `DELETE /api/collab/trips/{trip_id}`：管理员删除协同行程，成员退出协同行程
- `POST /api/collab/trips/{trip_id}/invites`：邀请好友
- `POST /api/collab/invites/{invite_id}/accept`：接受邀请
- `POST /api/collab/invites/{invite_id}/reject`：拒绝邀请
- `POST /api/collab/trips/{trip_id}/comments`：发表协同评论
- `POST /api/collab/trips/{trip_id}/votes`：对景点投票

### 📚 知识库与评测

- `POST /api/kb/ingest`：本地知识库入库
- `GET /api/kb/search`：知识库检索
- `POST /api/kb/evaluate`：知识库在线评测
- `python -m app.tasks.evaluate_kb`：离线评测命令

## 🧪 RAG 评测字段说明

- `城市 / 标签 / 人群 / 预算` 是过滤条件，用来缩小候选文档范围。
- `查询词` 是检索语义本身，用来表达用户本次想找什么内容。
- `期望命中关键词` 不参与检索，只用于评测命中率。
- 固定查询词和过滤条件，对比开启/关闭重排，可以观察 Reranker 对结果质量的影响。

## ❓ 常见问题

- `AMAP_API_KEY 未配置`
  - 需要在 `backend/.env` 填写高德 Web 服务 Key。
- 前端能打开但无法生成行程
  - 先确认 `http://localhost:8000/health` 可访问，并确认前端 `.env` 中后端地址正确。
- 社区头像或图片不显示
  - 确认后端已启动，并且 `/uploads` 静态资源挂载正常。
- 协同行程创建时没有可选行程
  - 需要先在 `/planner` 成功生成一次旅行规划，系统保存后才会出现在旅行轨迹中。
- RAG 评测页不可见
  - 需要用 `DEVELOPER_EMAIL_WHITELIST` 中配置的邮箱登录。
- 依赖安装或运行环境混乱
  - 本项目后端推荐统一使用 Conda 环境，不建议混用 Python 内置 `venv`。

## 🤝 贡献指南

欢迎提交 Pull Request 或 Issue。

## 📜 开源协议

CC BY-NC-SA 4.0

## 🙏 致谢

- [HelloAgents](https://github.com/datawhalechina/Hello-Agents) - 智能体教程
- [HelloAgents框架](https://github.com/jjyaoao/HelloAgents) - 智能体框架
- [高德地图开放平台](https://lbs.amap.com/) - 地图服务
- [amap-mcp-server](https://github.com/sugarforever/amap-mcp-server) - 高德地图 MCP 服务器

---

**云途智织——TripWeaver** - 让旅行计划从智能生成，走向社区分享与好友共创 🌈
