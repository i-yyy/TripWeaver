# HelloAgents智能旅行助手 🌍✈️

基于HelloAgents框架构建的智能旅行规划助手,集成高德地图MCP服务,提供个性化的旅行计划生成。

## ✨ 功能特点

- 🤖 **AI驱动的旅行规划**: 基于HelloAgents框架的SimpleAgent,智能生成详细的多日旅程
- 🧩 **多智能体协同**: 景点检索、天气查询、酒店推荐与总规划分工协作
- 🗺️ **高德地图集成**: 通过MCP协议接入高德地图服务,支持景点搜索、路线规划、天气查询
- 📚 **RAG本地知识库**: 支持Markdown+Frontmatter入库、向量检索、重排与解释性推荐依据输出
- 🧪 **RAG评测能力**: 支持在线评估接口和离线评测脚本,可对比重排开/关效果
- 👤 **用户画像与记忆系统**: 记录用户偏好、反馈和历史行程,实现个性化推荐闭环
- 🧠 **智能工具调用**: Agent自动调用高德地图MCP工具,获取实时POI、路线和天气信息
- 🎨 **现代化前端**: Vue3 + TypeScript + Vite,响应式设计,流畅的用户体验
- 📱 **完整功能**: 包含住宿、交通、餐饮和景点游览时间推荐

## 🏗️ 技术栈

### 后端
- **框架**: HelloAgents (基于SimpleAgent)
- **API**: FastAPI
- **数据库**: SQLite + SQLModel
- **向量检索**: Qdrant + Embedding + Reranker
- **MCP工具**: amap-mcp-server (高德地图)
- **LLM**: 支持多种LLM提供商(OpenAI, DeepSeek等)

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design Vue
- **地图服务**: 高德地图 JavaScript API
- **HTTP客户端**: Axios

## 📁 项目结构

```
helloagents-trip-planner/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── agents/            # Agent实现
│   │   │   └── trip_planner_agent.py
│   │   ├── api/               # FastAPI路由
│   │   │   ├── main.py
│   │   │   └── routes/
│   │   │       ├── trip.py
│   │   │       └── map.py
│   │   ├── services/          # 服务层
│   │   │   ├── amap_service.py
│   │   │   └── llm_service.py
│   │   ├── models/            # 数据模型
│   │   │   └── schemas.py
│   │   └── config.py          # 配置管理
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # Vue组件
│   │   ├── services/          # API服务
│   │   ├── types/             # TypeScript类型
│   │   └── views/             # 页面视图
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🚀 快速开始

### 前提条件

- Python 3.10+
- Node.js 18+
- 高德地图 Web 服务 API Key（后端必填）
- 可用的 LLM Key（建议填 `OPENAI_API_KEY` 或 `LLM_API_KEY`）
- 可选：Qdrant（需要完整向量检索/入库时）

### Windows（PowerShell）推荐步骤

1. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
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
```

然后启动后端：

```powershell
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

2. 启动前端（新开一个 PowerShell 窗口）

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

浏览器打开：

- 行程页：`http://localhost:5173/`
- RAG评测页：`http://localhost:5173/kb-eval`

### 完整功能（含向量入库）可选步骤

如果你要跑知识库向量入库与重排评测，建议先启动 Qdrant。

```powershell
docker run -p 6333:6333 qdrant/qdrant
```

然后在 `backend` 目录执行：

```powershell
python -m app.tasks.ingest_kb --clear
python -m app.tasks.evaluate_kb --top-k 6
```

评测报告输出到：

- `backend/data/knowledge_base/eval_report.md`

### 常见问题

- `No matching distribution found for hello-agents`
  - 说明当前网络或源无法拉取该包，先切换可用 PyPI 源后重试。
- `ModuleNotFoundError: qdrant_client`
  - 说明依赖没装完整，重新执行 `pip install -r requirements.txt`。
- 启动时报 `AMAP_API_KEY 未配置`
  - 需要在 `backend/.env` 填写高德 Key，否则后端会拒绝启动。
- 前端能打开但无法生成行程
  - 先确认后端 `http://localhost:8000/health` 可访问。

## 📝 使用指南

1. 在首页填写旅行信息:
   - 目的地城市
   - 旅行日期和天数
   - 交通方式偏好
   - 住宿偏好
   - 旅行风格标签

2. 点击"生成旅行计划"按钮

3. 系统将:
   - 调用HelloAgents Agent生成初步计划
   - Agent自动调用高德地图MCP工具搜索景点
   - Agent获取天气信息和路线规划
   - 整合所有信息生成完整行程

4. 查看结果:
   - 每日详细行程
   - 景点信息与地图标记
   - 交通路线规划
   - 天气预报
   - 餐饮推荐

## 🔧 核心实现

### HelloAgents Agent集成

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

# 创建高德地图MCP工具
amap_tool = MCPTool(
    name="amap",
    server_command=["uvx", "amap-mcp-server"],
    env={"AMAP_MAPS_API_KEY": "your_api_key"},
    auto_expand=True
)

# 创建旅行规划Agent
agent = SimpleAgent(
    name="旅行规划助手",
    llm=HelloAgentsLLM(),
    system_prompt="你是一个专业的旅行规划助手..."
)

# 添加工具
agent.add_tool(amap_tool)
```

### MCP工具调用

Agent可以自动调用以下高德地图MCP工具:
- `maps_text_search`: 搜索景点POI
- `maps_weather`: 查询天气
- `maps_direction_walking_by_address`: 步行路线规划
- `maps_direction_driving_by_address`: 驾车路线规划
- `maps_direction_transit_integrated_by_address`: 公共交通路线规划

## 📄 API文档

启动后端服务后,访问 `http://localhost:8000/docs` 查看完整的API文档。

主要端点:
- `POST /api/trip/plan` - 生成旅行计划
- `GET /api/map/poi` - 搜索POI
- `GET /api/map/weather` - 查询天气
- `POST /api/map/route` - 规划路线
- `POST /api/feedback/submit` - 提交反馈
- `GET /api/user/profile/{user_id}` - 获取用户画像
- `POST /api/kb/ingest` - 本地知识库入库
- `GET /api/kb/search` - 知识库检索
- `POST /api/kb/evaluate` - 知识库在线评估

离线评测命令:
- `python -m app.tasks.evaluate_kb`

前端评测页面:
- 启动前端后访问 `http://localhost:5173/kb-eval`
- 支持输入查询词、城市/标签/人群/预算过滤、期望命中关键词
- 页面会展示 Top-K 结果、命中率和 Top1 增益

## 🤝 贡献指南

欢迎提交Pull Request或Issue!

## 📜 开源协议

CC BY-NC-SA 4.0

## 🙏 致谢

- [HelloAgents](https://github.com/datawhalechina/Hello-Agents) - 智能体教程
- [HelloAgents框架](https://github.com/jjyaoao/HelloAgents) - 智能体框架
- [高德地图开放平台](https://lbs.amap.com/) - 地图服务
- [amap-mcp-server](https://github.com/sugarforever/amap-mcp-server) - 高德地图MCP服务器

---

**HelloAgents智能旅行助手** - 让旅行计划变得简单而智能 🌈


todo：
1、prompt: 分离出不需要ai做的json结构 backend\agent\planning