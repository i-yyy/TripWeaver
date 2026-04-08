# 本地旅游知识库说明

把各省份、地级市和场景化出行知识文档放在这里，系统会在入库时自动切片并建立向量索引。

## 推荐目录结构

- `jiangsu/nanjing/history_citywalk.md`
- `jiangsu/suzhou/gardens_citywalk.md`
- `jiangsu/yangzhou/slow_citywalk.md`
- `jiangsu/yancheng/wetland_family.md`

这里推荐使用“省份 / 地级市 / 文档”的层级。
其中真正参与城市过滤的是地级市目录名，因此文档应直接放在城市目录下。

## 文档规范

每篇文档建议包含 YAML frontmatter，字段尽量统一，便于做过滤检索和可解释推荐。

推荐字段：
- `title`: 文档标题
- `city`: 城市英文名，与地级市目录保持一致
- `category`: 文档类型，例如 `city_overview`、`family_plan`、`coastal_trip`
- `tags`: 标签数组，例如 `[history, museum, family]`
- `crowd_type`: 适合人群，例如 `[family, couple]`
- `budget_level`: 预算层级，例如 `low` / `medium` / `high`
- `season`: 适合季节，例如 `[spring, autumn]`
- `transportation`: 建议交通方式，例如 `[public_transit, walk]`
- `poi_names`: 核心地点数组
- `summary`: 一句话摘要
- `source`: 来源标识，例如 `local_editorial`
- `updated_at`: 更新时间，格式 `YYYY-MM-DD`

## 快速开始

1. 复制 [`_TEMPLATE.md`](./_TEMPLATE.md) 作为新文档模板
2. 按“场景描述 / 推荐策略 / 可选地点 / 约束与风险 / 推荐文案”填写正文
3. 执行 `python -m app.tasks.ingest_kb --clear` 完成入库
4. 调用 `/api/kb/search` 或 `/api/kb/evaluate` 进行检索和评测
5. 执行 `python -m app.tasks.evaluate_kb` 生成离线评测报告

## 评测文件

- 评测集：`eval_queries.json`
- 评测报告：`eval_report.md`

知识库解析与检索实现位于 `backend/app/services/knowledge_base_service.py`。
