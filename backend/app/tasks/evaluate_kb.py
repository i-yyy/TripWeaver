"""知识库 RAG 评测脚本（重排开/关对比）。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class EvalCase:
    name: str
    query: str
    city: Optional[str]
    tags: List[str]
    crowd_type: List[str]
    budget_level: Optional[str]
    expected_terms: List[str]


@dataclass
class EvalResult:
    case_name: str
    query: str
    city: Optional[str]
    metadata_filters: Dict[str, Any]
    recall_count: int
    expected_terms: List[str]
    baseline_hit_rate: float
    rerank_hit_rate: float
    hit_rate_gain: float
    baseline_avg_score: float
    rerank_avg_score: float
    top1_score_gain: float
    baseline_top1: Dict[str, Any]
    rerank_top1: Dict[str, Any]


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="评估知识库检索与重排效果")
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(base_dir / "data" / "knowledge_base" / "eval_queries.json"),
        help="评测数据集路径（JSON）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(base_dir / "data" / "knowledge_base" / "eval_report.md"),
        help="评测报告输出路径（Markdown）",
    )
    parser.add_argument("--top-k", type=int, default=6, help="每个用例保留结果数量")
    parser.add_argument("--city", type=str, default=None, help="可选：强制覆盖所有用例城市过滤")
    return parser.parse_args()


def load_cases(dataset_path: Path) -> List[EvalCase]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"数据集文件不存在: {dataset_path}")

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("数据集必须是数组格式")

    cases: List[EvalCase] = []
    for idx, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        query = str(item.get("query", "")).strip()
        if not query:
            continue

        case = EvalCase(
            name=str(item.get("name") or f"case_{idx}"),
            query=query,
            city=_maybe_text(item.get("city")),
            tags=_normalize_list(item.get("tags")),
            crowd_type=_normalize_list(item.get("crowd_type")),
            budget_level=_maybe_text(item.get("budget_level")),
            expected_terms=[token.lower() for token in _normalize_list(item.get("expected_terms"))],
        )
        cases.append(case)

    if not cases:
        raise ValueError("数据集为空或格式不正确")
    return cases


def evaluate_case(case: EvalCase, top_k: int, forced_city: Optional[str] = None) -> EvalResult:
    kb_service, reranker = _get_services()

    city = forced_city or case.city
    filters: Dict[str, Any] = {}
    if case.tags:
        filters["tags"] = case.tags
    if case.crowd_type:
        filters["crowd_type"] = case.crowd_type
    if case.budget_level:
        filters["budget_level"] = case.budget_level

    recall_items = kb_service.search(
        query=case.query,
        city=city,
        top_k=max(1, top_k * 2),
        metadata_filters=filters or None,
    )
    baseline_items = recall_items[:top_k]
    rerank_items = reranker.rerank(
        query=case.query,
        candidates=recall_items,
        top_n=top_k,
    )

    baseline_hit_rate = _hit_rate(baseline_items, case.expected_terms)
    rerank_hit_rate = _hit_rate(rerank_items, case.expected_terms)

    baseline_scores = [_item_score(item) for item in baseline_items]
    rerank_scores = [_item_score(item) for item in rerank_items]

    baseline_top1 = _brief_item(baseline_items[0]) if baseline_items else {}
    rerank_top1 = _brief_item(rerank_items[0]) if rerank_items else {}
    top1_score_gain = _item_score(rerank_items[0]) - _item_score(baseline_items[0]) if baseline_items and rerank_items else 0.0

    return EvalResult(
        case_name=case.name,
        query=case.query,
        city=city,
        metadata_filters=filters,
        recall_count=len(recall_items),
        expected_terms=case.expected_terms,
        baseline_hit_rate=baseline_hit_rate,
        rerank_hit_rate=rerank_hit_rate,
        hit_rate_gain=rerank_hit_rate - baseline_hit_rate,
        baseline_avg_score=mean(baseline_scores) if baseline_scores else 0.0,
        rerank_avg_score=mean(rerank_scores) if rerank_scores else 0.0,
        top1_score_gain=top1_score_gain,
        baseline_top1=baseline_top1,
        rerank_top1=rerank_top1,
    )


def build_report(results: List[EvalResult], top_k: int, dataset_path: Path) -> str:
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    avg_baseline = mean([item.baseline_hit_rate for item in results]) if results else 0.0
    avg_rerank = mean([item.rerank_hit_rate for item in results]) if results else 0.0
    avg_gain = mean([item.hit_rate_gain for item in results]) if results else 0.0
    avg_top1_gain = mean([item.top1_score_gain for item in results]) if results else 0.0
    win_cases = sum(1 for item in results if item.hit_rate_gain > 0)
    tie_cases = sum(1 for item in results if item.hit_rate_gain == 0)

    lines: List[str] = []
    lines.append("# RAG 评测报告")
    lines.append("")
    lines.append(f"- 生成时间: {now_text}")
    lines.append(f"- 评测集: `{dataset_path}`")
    lines.append(f"- Top-K: {top_k}")
    lines.append(f"- 用例数: {len(results)}")
    lines.append("")
    lines.append("## 汇总指标")
    lines.append("")
    lines.append(f"- 基线命中率均值: {avg_baseline:.4f}")
    lines.append(f"- 重排命中率均值: {avg_rerank:.4f}")
    lines.append(f"- 命中率平均提升: {avg_gain:.4f}")
    lines.append(f"- Top1 分数平均提升: {avg_top1_gain:.4f}")
    lines.append(f"- 提升用例数: {win_cases} / {len(results)}（持平 {tie_cases}）")
    lines.append("")
    lines.append("## 用例结果")
    lines.append("")
    lines.append("| 用例 | 召回数 | 基线命中率 | 重排命中率 | 提升 | 基线均分 | 重排均分 | Top1增益 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for item in results:
        lines.append(
            f"| {item.case_name} | {item.recall_count} | {item.baseline_hit_rate:.4f} | "
            f"{item.rerank_hit_rate:.4f} | {item.hit_rate_gain:.4f} | "
            f"{item.baseline_avg_score:.4f} | {item.rerank_avg_score:.4f} | {item.top1_score_gain:.4f} |"
        )

    lines.append("")
    lines.append("## 详情")
    for item in results:
        lines.append("")
        lines.append(f"### {item.case_name}")
        lines.append("")
        lines.append(f"- 查询: `{item.query}`")
        lines.append(f"- 城市过滤: `{item.city or '无'}`")
        lines.append(f"- 元数据过滤: `{json.dumps(item.metadata_filters, ensure_ascii=False)}`")
        lines.append(f"- 期望关键词: `{', '.join(item.expected_terms) if item.expected_terms else '无'}`")
        lines.append(f"- 基线命中率: {item.baseline_hit_rate:.4f}")
        lines.append(f"- 重排命中率: {item.rerank_hit_rate:.4f}")
        lines.append(f"- 命中率提升: {item.hit_rate_gain:.4f}")
        lines.append(f"- Top1 分数增益: {item.top1_score_gain:.4f}")
        lines.append(f"- 基线 Top1: `{json.dumps(item.baseline_top1, ensure_ascii=False)}`")
        lines.append(f"- 重排 Top1: `{json.dumps(item.rerank_top1, ensure_ascii=False)}`")

    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- 命中率定义: Top-K 结果中，至少包含一个期望关键词的比例。")
    lines.append("- 基线结果: 向量召回后不做重排，直接取前 Top-K。")
    lines.append("- 重排结果: 向量召回后做二次排序，再取前 Top-K。")
    return "\n".join(lines) + "\n"


def _normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [token.strip() for token in text.split(",") if token.strip()]


def _maybe_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _item_score(item: Dict[str, Any]) -> float:
    return float(item.get("final_score", item.get("score", 0.0)))


def _hit_rate(items: List[Dict[str, Any]], expected_terms: List[str]) -> float:
    if not items:
        return 0.0
    if not expected_terms:
        return 0.0
    hit_count = sum(1 for item in items if _matches_expected_terms(item, expected_terms))
    return float(hit_count) / float(len(items))


def _matches_expected_terms(item: Dict[str, Any], expected_terms: Iterable[str]) -> bool:
    terms = [str(token).strip().lower() for token in expected_terms if str(token).strip()]
    if not terms:
        return False

    payload = dict(item.get("metadata", {}))
    text_segments = [
        str(item.get("content", "")),
        str(payload.get("title", "")),
        str(payload.get("city_hint", "")),
    ]
    text_segments.extend(_flatten_payload(payload))
    text_blob = " ".join(text_segments).lower()
    return any(term in text_blob for term in terms)


def _flatten_payload(value: Any) -> List[str]:
    results: List[str] = []
    if isinstance(value, dict):
        for key, val in value.items():
            results.append(str(key))
            results.extend(_flatten_payload(val))
    elif isinstance(value, list):
        for item in value:
            results.extend(_flatten_payload(item))
    else:
        text = str(value).strip()
        if text:
            results.append(text)
    return results


def _brief_item(item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = dict(item.get("metadata", {}))
    content = str(item.get("content", "")).replace("\n", " ").strip()
    return {
        "score": round(_item_score(item), 4),
        "city_hint": metadata.get("city_hint"),
        "doc_path": metadata.get("doc_path"),
        "snippet": content[:120],
    }


def _get_services() -> tuple[Any, Any]:
    from app.services.knowledge_base_service import get_knowledge_base_service
    from app.services.reranker_service import get_reranker_service

    return get_knowledge_base_service(), get_reranker_service()


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    output_path = Path(args.output).resolve()
    top_k = max(1, min(20, int(args.top_k)))

    cases = load_cases(dataset_path)
    try:
        results = [evaluate_case(case=case, top_k=top_k, forced_city=args.city) for case in cases]
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "unknown")
        raise SystemExit(
            f"评测失败：缺少依赖 `{missing}`。请先在 backend 目录执行 `pip install -r requirements.txt`。"
        ) from exc

    report = build_report(results=results, top_k=top_k, dataset_path=dataset_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print("评测完成。")
    print(f"- 用例数: {len(results)}")
    print(f"- 报告路径: {output_path}")


if __name__ == "__main__":
    main()
