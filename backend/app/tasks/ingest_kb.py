"""知识库入库脚本。"""

from __future__ import annotations

import argparse

from app.services.knowledge_base_service import get_knowledge_base_service


def main() -> None:
    parser = argparse.ArgumentParser(description="将本地 Markdown 文档入库到 Qdrant")
    parser.add_argument("--city", type=str, default=None, help="可选：只入库某个城市目录")
    parser.add_argument("--clear", action="store_true", help="入库前清空集合")
    args = parser.parse_args()

    service = get_knowledge_base_service()
    result = service.ingest_documents(city=args.city, clear_collection=args.clear)
    print("入库结果:")
    for key, value in result.items():
        print(f"- {key}: {value}")

    if result.get("success"):
        query = "亲子 雨天 博物馆"
        sample = service.search(query=query, city=args.city, top_k=3)
        print("\n示例检索结果:")
        for idx, item in enumerate(sample, start=1):
            preview = str(item.get("content", "")).replace("\n", " ")[:120]
            print(f"{idx}. 分数={item.get('score', 0):.3f} 内容={preview}")


if __name__ == "__main__":
    main()
