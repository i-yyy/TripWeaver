# 本地旅游知识库说明

把各城市或场景知识文档放在这里，系统会在入库时自动切片并建立向量索引。

## 推荐目录结构

- `beijing/history.md`
- `beijing/rainy_day.md`
- `shanghai/citywalk.md`
- `common/family_travel.md`

## 文档规范

每篇文档建议包含 YAML frontmatter，字段尽量统一，便于后续做过滤检索与可解释推荐。

推荐字段：

- `title`: 文档标题
- `city`: 城市名（与目录保持一致）
- `category`: 文档类型（如 `attraction_guide` / `rain_backup` / `food`）
- `tags`: 标签数组（如 `[museum, history, family]`）
- `crowd_type`: 适合人群（如 `[family, couple]`）
- `budget_level`: 预算层级（如 `low/medium/high`）
- `season`: 推荐季节（如 `[spring, autumn]`）
- `transportation`: 建议交通方式（如 `[public_transit, walk]`）
- `source`: 来源标识（如 `local_editorial`）
- `updated_at`: 更新时间（YYYY-MM-DD）

## 快速开始

1. 复制 [`_TEMPLATE.md`](./_TEMPLATE.md) 为新文档。
2. 填写 frontmatter 字段与正文内容。
3. 执行 `python -m app.tasks.ingest_kb --clear` 完成入库。
4. 调用 `/api/kb/search` 或 `/api/kb/evaluate` 进行检索和评估。
5. 执行 `python -m app.tasks.evaluate_kb` 生成离线评测报告。

## 评测文件

- 评测集：`eval_queries.json`
- 评测报告：`eval_report.md`

知识库解析与检索实现位于 `backend/app/services/knowledge_base_service.py`。
