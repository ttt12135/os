import os
import json
from datetime import datetime

from src.rag_vector_store import rag_retrieve_history


DEFAULT_HYBRID_OUTPUT_DIR = "history_knowledge_base/hybrid_retrieval_results"


def ensure_dir(directory):
    """
    如果目录不存在，则创建目录。
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    if os.path.isdir(file_path):
        raise IsADirectoryError(f"输入的是文件夹，不是 JSON 文件：{file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_file(data, file_path):
    """
    保存 JSON 文件。
    """

    output_dir = os.path.dirname(file_path)

    if output_dir:
        ensure_dir(output_dir)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def safe_number(value, default=0):
    """
    安全转换数字。
    """

    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_list(value):
    """
    安全转换列表。
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        if value.strip() == "":
            return []
        return [value]

    return []


def safe_join(items, default="无"):
    """
    安全拼接列表。
    """

    items = safe_list(items)

    if not items:
        return default

    return "、".join(str(item) for item in items)


def normalize_structured_score(score):
    """
    归一化结构相似度。

    兼容两种情况：
    - 0~1
    - 0~100
    """

    score = safe_number(score)

    if score > 1:
        score = score / 100

    if score < 0:
        score = 0

    if score > 1:
        score = 1

    return score


def build_rag_query_from_repo_profile(repo_profile):
    """
    根据目标项目 repo_profile 自动生成 RAG 检索 query。
    """

    repo_name = repo_profile.get("repo_name", "unknown_repo")
    project_type = repo_profile.get("project_type", "unknown")
    main_languages = safe_join(repo_profile.get("main_languages"))
    core_modules = safe_join(repo_profile.get("core_modules"))

    function_count = repo_profile.get("function_count", 0)
    edge_count = repo_profile.get("edge_count", 0)
    module_count = repo_profile.get("module_count", 0)
    structure_complexity = repo_profile.get("structure_complexity", 0)

    query = (
        f"查找与目标 OS 项目 {repo_name} 相似的历史项目。"
        f"目标项目类型是 {project_type}，主要语言包括 {main_languages}，"
        f"核心模块包括 {core_modules}。"
        f"该项目包含 {function_count} 个函数节点、{edge_count} 条调用边、"
        f"{module_count} 个模块，结构复杂度为 {structure_complexity}。"
        f"请优先检索在项目类型、核心模块、系统结构、技术特征和工程复杂度上相似的历史 OS 项目。"
    )

    return query


def extract_structured_results(structured_result):
    """
    提取 retrieve_full 的结构化结果。
    """

    if isinstance(structured_result.get("results"), list):
        return structured_result.get("results")

    if isinstance(structured_result.get("similar_projects"), list):
        return structured_result.get("similar_projects")

    if isinstance(structured_result.get("top_similar_projects"), list):
        return structured_result.get("top_similar_projects")

    return []


def get_repo_name_from_structured_item(item):
    """
    从结构检索结果中提取仓库名。
    """

    return (
        item.get("repo_name")
        or item.get("history_repo_name")
        or item.get("name")
        or item.get("project_name")
        or "unknown_repo"
    )


def get_structured_similarity_score(item):
    """
    从结构检索结果中提取相似度。
    """

    candidate_keys = [
        "similarity_score",
        "final_score",
        "score",
        "total_score",
        "weighted_score"
    ]

    for key in candidate_keys:
        if key in item:
            return normalize_structured_score(item.get(key))

    return 0


def get_source_profile_from_structured_item(item):
    """
    从结构检索结果中提取 source_profile。
    """

    return (
        item.get("source_profile")
        or item.get("profile_path")
        or item.get("repo_profile_full_path")
        or ""
    )


def get_semantic_score_from_rank(rank, top_k):
    """
    根据 RAG 检索排名生成语义分数。

    说明：
    Chroma 返回的 score 在不同距离度量下含义不完全一致，
    所以这里使用 rank-based score，更稳定。
    """

    if top_k <= 1:
        return 1.0

    score = 1 - ((rank - 1) / top_k)

    if score < 0:
        score = 0

    if score > 1:
        score = 1

    return score


def merge_structured_results(merged_map, structured_results):
    """
    合并结构检索结果。
    """

    for rank, item in enumerate(structured_results, start=1):
        if not isinstance(item, dict):
            continue

        repo_name = get_repo_name_from_structured_item(item)
        structured_score = get_structured_similarity_score(item)

        if repo_name not in merged_map:
            merged_map[repo_name] = {
                "repo_name": repo_name,
                "structured_score": 0,
                "semantic_score": 0,
                "hybrid_score": 0,
                "structured_rank": None,
                "semantic_best_rank": None,
                "source_profile": "",
                "source": [],
                "structured_detail": {},
                "semantic_evidence": []
            }

        merged_map[repo_name]["structured_score"] = max(
            merged_map[repo_name]["structured_score"],
            structured_score
        )

        merged_map[repo_name]["structured_rank"] = rank

        source_profile = get_source_profile_from_structured_item(item)

        if source_profile:
            merged_map[repo_name]["source_profile"] = source_profile

        merged_map[repo_name]["structured_detail"] = item

        if "structured" not in merged_map[repo_name]["source"]:
            merged_map[repo_name]["source"].append("structured")


def merge_rag_results(merged_map, rag_results):
    """
    合并 RAG 语义检索结果。
    """

    results = rag_results.get("results", [])
    top_k = rag_results.get("top_k", len(results))

    for rank, item in enumerate(results, start=1):
        metadata = item.get("metadata", {})
        repo_name = metadata.get("repo_name", "unknown_repo")
        doc_type = metadata.get("doc_type", "unknown")
        doc_id = metadata.get("doc_id", "")
        content = item.get("content", "")
        raw_score = item.get("score")

        semantic_score = get_semantic_score_from_rank(
            rank=rank,
            top_k=top_k
        )

        if repo_name not in merged_map:
            merged_map[repo_name] = {
                "repo_name": repo_name,
                "structured_score": 0,
                "semantic_score": 0,
                "hybrid_score": 0,
                "structured_rank": None,
                "semantic_best_rank": None,
                "source_profile": "",
                "source": [],
                "structured_detail": {},
                "semantic_evidence": []
            }

        if semantic_score > merged_map[repo_name]["semantic_score"]:
            merged_map[repo_name]["semantic_score"] = semantic_score
            merged_map[repo_name]["semantic_best_rank"] = rank

        source_profile = metadata.get("source_profile", "")

        if source_profile and not merged_map[repo_name].get("source_profile"):
            merged_map[repo_name]["source_profile"] = source_profile

        evidence = {
            "rank": rank,
            "doc_id": doc_id,
            "doc_type": doc_type,
            "raw_score": raw_score,
            "semantic_score": semantic_score,
            "content_preview": content[:300]
        }

        merged_map[repo_name]["semantic_evidence"].append(evidence)

        if "rag" not in merged_map[repo_name]["source"]:
            merged_map[repo_name]["source"].append("rag")


def compute_hybrid_scores(merged_map, structured_weight=0.65, semantic_weight=0.35):
    """
    计算融合分数。
    """

    results = []

    for repo_name, item in merged_map.items():
        structured_score = safe_number(item.get("structured_score"))
        semantic_score = safe_number(item.get("semantic_score"))

        hybrid_score = (
            structured_score * structured_weight
            + semantic_score * semantic_weight
        )

        item["hybrid_score"] = round(hybrid_score, 4)
        item["similarity_score"] = round(hybrid_score, 4)

        item["structured_score"] = round(structured_score, 4)
        item["semantic_score"] = round(semantic_score, 4)

        results.append(item)

    results.sort(
        key=lambda item: item.get("hybrid_score", 0),
        reverse=True
    )

    return results


def generate_hybrid_retrieval_markdown(hybrid_result):
    """
    生成 hybrid 检索 Markdown 报告。
    """

    lines = []

    lines.append("# Hybrid 历史项目检索报告")
    lines.append("")
    lines.append(f"生成时间：{hybrid_result.get('created_at')}")
    lines.append(f"目标仓库：`{hybrid_result.get('target_repo_name')}`")
    lines.append("")
    lines.append("## 1. 检索配置")
    lines.append("")
    lines.append(f"- 结构检索结果：`{hybrid_result.get('structured_result_path')}`")
    lines.append(f"- RAG Query：{hybrid_result.get('rag_query')}")
    lines.append(f"- structured_weight：`{hybrid_result.get('structured_weight')}`")
    lines.append(f"- semantic_weight：`{hybrid_result.get('semantic_weight')}`")
    lines.append(f"- top_k：`{hybrid_result.get('top_k')}`")
    lines.append("")
    lines.append("## 2. 融合检索结果")
    lines.append("")
    lines.append("| 排名 | 仓库名 | Hybrid分数 | 结构分数 | 语义分数 | 来源 |")
    lines.append("|---:|---|---:|---:|---:|---|")

    for index, item in enumerate(hybrid_result.get("results", []), start=1):
        lines.append(
            f"| {index} | "
            f"{item.get('repo_name')} | "
            f"{item.get('hybrid_score')} | "
            f"{item.get('structured_score')} | "
            f"{item.get('semantic_score')} | "
            f"{'、'.join(item.get('source', []))} |"
        )

    lines.append("")
    lines.append("## 3. RAG 语义证据")
    lines.append("")

    for index, item in enumerate(hybrid_result.get("results", []), start=1):
        lines.append(f"### {index}. {item.get('repo_name')}")
        lines.append("")
        lines.append(f"- Hybrid 分数：`{item.get('hybrid_score')}`")
        lines.append(f"- 结构分数：`{item.get('structured_score')}`")
        lines.append(f"- 语义分数：`{item.get('semantic_score')}`")
        lines.append(f"- 来源：`{'、'.join(item.get('source', []))}`")
        lines.append("")

        evidence_list = item.get("semantic_evidence", [])

        if not evidence_list:
            lines.append("暂无 RAG 语义证据。")
            lines.append("")
            continue

        for evidence in evidence_list[:3]:
            lines.append(
                f"- `{evidence.get('doc_type')}` / `{evidence.get('doc_id')}`："
                f"{evidence.get('content_preview')}"
            )

        lines.append("")

    lines.append("## 4. 说明")
    lines.append("")
    lines.append(
        "Hybrid 检索结果同时考虑结构相似度和 RAG 语义相似度。"
        "其中结构相似度主要来自 retrieve_full，关注项目类型、模块结构、函数规模和调用图规模；"
        "语义相似度主要来自 RAG 文档向量检索，关注技术描述、模块特征和文本语义。"
    )
    lines.append("")

    return "\n".join(lines)


def save_hybrid_retrieval_result(hybrid_result):
    """
    保存 hybrid 检索结果。
    """

    ensure_dir(DEFAULT_HYBRID_OUTPUT_DIR)

    repo_name = hybrid_result.get("target_repo_name", "unknown_repo")

    json_path = os.path.join(
        DEFAULT_HYBRID_OUTPUT_DIR,
        f"{repo_name}_hybrid_retrieval_full.json"
    )

    md_path = os.path.join(
        DEFAULT_HYBRID_OUTPUT_DIR,
        f"{repo_name}_hybrid_retrieval_report.md"
    )

    save_json_file(hybrid_result, json_path)

    markdown_text = generate_hybrid_retrieval_markdown(hybrid_result)

    with open(md_path, "w", encoding="utf-8") as file:
        file.write(markdown_text)

    return json_path, md_path


def run_hybrid_retrieve(
    target_repo_profile_path,
    structured_result_path,
    rag_query=None,
    persist_directory="vector_store/chroma_history",
    collection_name="os_history_projects",
    structured_weight=0.65,
    semantic_weight=0.35,
    rag_top_k=10,
    final_top_k=5
):
    """
    执行 Hybrid 检索。

    输入：
    - 目标 repo_profile_full
    - retrieve_full 的结构检索结果
    - Chroma RAG 向量库

    输出：
    - hybrid_retrieval_full.json
    - hybrid_retrieval_report.md
    """

    target_repo_profile = load_json_file(target_repo_profile_path)
    structured_result = load_json_file(structured_result_path)

    target_repo_name = target_repo_profile.get("repo_name", "unknown_repo")

    if rag_query is None or str(rag_query).strip() == "":
        rag_query = build_rag_query_from_repo_profile(target_repo_profile)

    structured_results = extract_structured_results(structured_result)

    rag_result = rag_retrieve_history(
        query=rag_query,
        persist_directory=persist_directory,
        collection_name=collection_name,
        top_k=rag_top_k
    )

    merged_map = {}

    merge_structured_results(
        merged_map=merged_map,
        structured_results=structured_results
    )

    merge_rag_results(
        merged_map=merged_map,
        rag_results=rag_result
    )

    merged_results = compute_hybrid_scores(
        merged_map=merged_map,
        structured_weight=structured_weight,
        semantic_weight=semantic_weight
    )

    final_results = merged_results[:final_top_k]

    hybrid_result = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_repo_name": target_repo_name,
        "target_repo_profile_path": target_repo_profile_path,
        "structured_result_path": structured_result_path,
        "rag_query": rag_query,
        "persist_directory": persist_directory,
        "collection_name": collection_name,
        "structured_weight": structured_weight,
        "semantic_weight": semantic_weight,
        "rag_top_k": rag_top_k,
        "top_k": final_top_k,
        "results": final_results,
        "all_candidates": merged_results,
        "raw_rag_result": rag_result
    }

    json_path, md_path = save_hybrid_retrieval_result(hybrid_result)

    hybrid_result["save_json_path"] = json_path
    hybrid_result["save_markdown_path"] = md_path

    return hybrid_result


def format_hybrid_retrieval_preview(hybrid_result):
    """
    终端预览。
    """

    lines = []

    lines.append("Hybrid 历史项目检索完成。")
    lines.append("")
    lines.append(f"目标仓库：{hybrid_result.get('target_repo_name')}")
    lines.append(f"结构检索结果：{hybrid_result.get('structured_result_path')}")
    lines.append(f"向量库目录：{hybrid_result.get('persist_directory')}")
    lines.append(f"structured_weight：{hybrid_result.get('structured_weight')}")
    lines.append(f"semantic_weight：{hybrid_result.get('semantic_weight')}")
    lines.append("")
    lines.append(f"JSON 输出：{hybrid_result.get('save_json_path')}")
    lines.append(f"Markdown 报告：{hybrid_result.get('save_markdown_path')}")
    lines.append("")
    lines.append("Top 结果：")

    for index, item in enumerate(hybrid_result.get("results", []), start=1):
        lines.append(
            f"{index}. {item.get('repo_name')} "
            f"hybrid={item.get('hybrid_score')} "
            f"structured={item.get('structured_score')} "
            f"semantic={item.get('semantic_score')} "
            f"source={','.join(item.get('source', []))}"
        )

    return "\n".join(lines)