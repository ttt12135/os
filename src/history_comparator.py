import os
import json
from datetime import datetime


def load_json_file(file_path):
    """
    读取 JSON 文件，并提供更清晰的错误提示。
    """

    if not file_path:
        raise ValueError("JSON 文件路径为空。")

    if os.path.isdir(file_path):
        raise IsADirectoryError(
            f"你输入的是文件夹路径，不是 JSON 文件路径：{file_path}"
        )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"文件不存在：{file_path}"
        )

    if not file_path.endswith(".json"):
        raise ValueError(
            f"输入文件不是 JSON 文件：{file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def ensure_dir(directory):
    """
    如果目录不存在，就创建目录。
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def extract_json_from_text(text):
    """
    尝试从 AI 返回文本中提取 JSON。
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1).strip()

    if text.startswith("```"):
        text = text.replace("```", "", 1).strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    start_index = text.find("{")
    end_index = text.rfind("}")

    if start_index == -1 or end_index == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)

    json_text = text[start_index:end_index + 1]

    return json.loads(json_text)


def compact_profile_for_prompt(profile):
    """
    压缩 repo_profile_full，避免 prompt 过长。
    """

    return {
        "repo_name": profile.get("repo_name"),
        "project_type": profile.get("project_type"),
        "main_languages": profile.get("main_languages", []),
        "function_count": profile.get("function_count", 0),
        "edge_count": profile.get("edge_count", 0),
        "internal_edge_count": profile.get("internal_edge_count", 0),
        "external_edge_count": profile.get("external_edge_count", 0),
        "module_count": profile.get("module_count", 0),
        "core_modules": profile.get("core_modules", []),
        "core_module_details": profile.get("core_module_details", []),
        "module_completeness": profile.get("module_completeness", {}),
        "structure_complexity": profile.get("structure_complexity", 0),
        "technical_features": profile.get("technical_features", []),
        "weaknesses": profile.get("weaknesses", [])
    }


def detect_retrieval_mode(retrieval_result):
    """
    判断检索结果类型。

    支持：
    - structured: retrieve_full 原始结构检索
    - hybrid: hybrid_retrieve 融合检索
    """

    if "structured_weight" in retrieval_result or "semantic_weight" in retrieval_result:
        return "hybrid"

    results = retrieval_result.get("results", [])

    if results:
        first_item = results[0]

        if isinstance(first_item, dict):
            if "hybrid_score" in first_item or "semantic_score" in first_item:
                return "hybrid"

    return "structured"


def get_target_profile_path_from_retrieval_result(retrieval_result):
    """
    从 retrieve_full 或 hybrid_retrieve 结果中提取目标 repo_profile 路径。
    """

    candidate_keys = [
        "target_profile",
        "target_repo_profile_path",
        "repo_profile_path"
    ]

    for key in candidate_keys:
        value = retrieval_result.get(key)

        if value:
            return value

    raise KeyError(
        "检索结果中没有找到目标 repo_profile 路径。"
        "请确认输入的是 retrieve_full 或 hybrid_retrieve 生成的 json 文件。"
    )


def get_target_repo_name_from_retrieval_result(retrieval_result, target_profile):
    """
    从检索结果或目标 profile 中提取目标仓库名。
    """

    candidate_keys = [
        "target_repo",
        "target_repo_name",
        "repo_name"
    ]

    for key in candidate_keys:
        value = retrieval_result.get(key)

        if value:
            return value

    return target_profile.get("repo_name", "unknown_repo")


def extract_retrieval_results(retrieval_result):
    """
    兼容不同版本的检索结果字段。
    """

    if isinstance(retrieval_result.get("results"), list):
        return retrieval_result.get("results")

    if isinstance(retrieval_result.get("similar_projects"), list):
        return retrieval_result.get("similar_projects")

    if isinstance(retrieval_result.get("top_similar_projects"), list):
        return retrieval_result.get("top_similar_projects")

    return []


def get_repo_name_from_retrieval_item(item):
    """
    从检索结果 item 中提取历史仓库名。
    """

    return (
        item.get("repo_name")
        or item.get("history_repo_name")
        or item.get("project_name")
        or item.get("name")
        or "unknown_repo"
    )


def resolve_history_profile_path(item):
    """
    从结构检索或 hybrid 检索 item 中解析历史项目 source_profile 路径。
    """

    candidate_paths = []

    candidate_paths.append(item.get("source_profile"))
    candidate_paths.append(item.get("profile_path"))
    candidate_paths.append(item.get("repo_profile_full_path"))

    structured_detail = item.get("structured_detail", {})

    if isinstance(structured_detail, dict):
        candidate_paths.append(structured_detail.get("source_profile"))
        candidate_paths.append(structured_detail.get("profile_path"))
        candidate_paths.append(structured_detail.get("repo_profile_full_path"))

    repo_name = get_repo_name_from_retrieval_item(item)

    if repo_name:
        candidate_paths.append(
            os.path.join(
                "repo_profiles",
                "history",
                f"{repo_name}_repo_profile_full.json"
            )
        )

    for path in candidate_paths:
        if path and os.path.exists(path) and path.endswith(".json"):
            return path

    for path in candidate_paths:
        if path:
            return path

    return ""


def get_similarity_score_from_item(item):
    """
    兼容 retrieve_full 和 hybrid_retrieve 的相似度字段。
    """

    candidate_keys = [
        "similarity_score",
        "hybrid_score",
        "final_score",
        "score",
        "weighted_score"
    ]

    for key in candidate_keys:
        if key in item:
            return item.get(key)

    return 0


def build_hybrid_score_detail(item):
    """
    为 hybrid 检索结果构造 score_detail，便于 AI 理解来源。
    """

    structured_detail = item.get("structured_detail", {})

    if not isinstance(structured_detail, dict):
        structured_detail = {}

    return {
        "hybrid_score": item.get("hybrid_score", item.get("similarity_score")),
        "structured_score": item.get("structured_score", 0),
        "semantic_score": item.get("semantic_score", 0),
        "structured_rank": item.get("structured_rank"),
        "semantic_best_rank": item.get("semantic_best_rank"),
        "source": item.get("source", []),
        "structured_score_detail": structured_detail.get("score_detail", {}),
        "structured_explanations": structured_detail.get("explanations", [])
    }


def compact_semantic_evidence(item, max_items=3):
    """
    压缩 RAG 语义证据，避免 prompt 过长。
    """

    evidence_list = item.get("semantic_evidence", [])

    if not isinstance(evidence_list, list):
        return []

    compact_list = []

    for evidence in evidence_list[:max_items]:
        if not isinstance(evidence, dict):
            continue

        compact_list.append(
            {
                "rank": evidence.get("rank"),
                "doc_type": evidence.get("doc_type"),
                "doc_id": evidence.get("doc_id"),
                "semantic_score": evidence.get("semantic_score"),
                "content_preview": evidence.get("content_preview", "")[:300]
            }
        )

    return compact_list


def normalize_retrieval_item_for_comparison(item, retrieval_mode):
    """
    将 retrieve_full / hybrid_retrieve 的 item 统一成 compare_full 可用格式。
    """

    repo_name = get_repo_name_from_retrieval_item(item)
    source_profile = resolve_history_profile_path(item)
    similarity_score = get_similarity_score_from_item(item)

    normalized_item = {
        "repo_name": repo_name,
        "source_profile": source_profile,
        "similarity_score": similarity_score,
        "retrieval_mode": retrieval_mode
    }

    if retrieval_mode == "hybrid":
        normalized_item["hybrid_score"] = item.get("hybrid_score", similarity_score)
        normalized_item["structured_score"] = item.get("structured_score", 0)
        normalized_item["semantic_score"] = item.get("semantic_score", 0)
        normalized_item["source"] = item.get("source", [])
        normalized_item["score_detail"] = build_hybrid_score_detail(item)
        normalized_item["semantic_evidence"] = compact_semantic_evidence(item)
        normalized_item["explanations"] = [
            f"Hybrid 检索分数：{item.get('hybrid_score', similarity_score)}",
            f"结构相似分数：{item.get('structured_score', 0)}",
            f"语义相似分数：{item.get('semantic_score', 0)}",
            f"检索来源：{'、'.join(item.get('source', []))}"
        ]

    else:
        normalized_item["score_detail"] = item.get("score_detail", {})
        normalized_item["explanations"] = item.get("explanations", [])

    return normalized_item


def build_missing_profile_comparison(item, source_profile):
    """
    历史 profile 缺失时的兜底结果。
    """

    return {
        "history_repo_name": item.get("repo_name"),
        "source_profile": source_profile,
        "similarity_score": item.get("similarity_score"),
        "retrieval_mode": item.get("retrieval_mode", "unknown"),
        "similarity_summary": "未能读取历史仓库完整画像，无法进行详细 AI 对比。",
        "main_similarities": [],
        "main_differences": [],
        "target_advantages": [],
        "target_weaknesses": [],
        "borrowable_designs": [],
        "comparison_confidence": "low",
        "uncertainty": "source_profile 路径不存在或为空。"
    }

def build_history_comparison_prompt(target_profile, history_profile, retrieval_item):
    """
    构造目标仓库与单个历史仓库的对比 Prompt。
    """

    target_compact = compact_profile_for_prompt(target_profile)
    history_compact = compact_profile_for_prompt(history_profile)

    prompt = f"""
你是一个操作系统内核比赛作品评审助手。现在需要比较一个目标 OS 仓库和一个历史 OS 仓库。

请你根据结构化仓库画像和检索证据进行对比，不要凭空编造。若信息不足，请明确说明不确定性。

【目标仓库画像】
{json.dumps(target_compact, ensure_ascii=False, indent=2)}

【历史仓库画像】
{json.dumps(history_compact, ensure_ascii=False, indent=2)}

【检索得到的相似度信息】
以下信息可能来自 retrieve_full 结构检索，也可能来自 hybrid_retrieve 融合检索。
如果 retrieval_mode 为 hybrid，请同时参考 structured_score、semantic_score 和 semantic_evidence。
{json.dumps(retrieval_item, ensure_ascii=False, indent=2)}

请严格输出 JSON，不要输出 Markdown，不要添加代码块标记。格式如下：

{{
  "history_repo_name": "历史仓库名称",
  "similarity_summary": "用一段话总结二者为什么相似",
  "main_similarities": [
    "相似点1",
    "相似点2"
  ],
  "main_differences": [
    "差异点1",
    "差异点2"
  ],
  "target_advantages": [
    "目标仓库相对历史仓库的优势"
  ],
  "target_weaknesses": [
    "目标仓库相对历史仓库的不足"
  ],
  "borrowable_designs": [
    "目标仓库可以借鉴历史仓库的设计"
  ],
  "comparison_confidence": "high / medium / low",
  "uncertainty": "说明本次对比的不确定性来源"
}}
"""

    return prompt


def compare_one_history_project(
    target_profile,
    history_profile,
    retrieval_item,
    ask_ai_once
):
    """
    对比目标仓库和单个历史仓库。
    """

    prompt = build_history_comparison_prompt(
        target_profile=target_profile,
        history_profile=history_profile,
        retrieval_item=retrieval_item
    )

    ai_reply = ask_ai_once(prompt)

    try:
        comparison = extract_json_from_text(ai_reply)

    except json.JSONDecodeError:
        comparison = {
            "history_repo_name": history_profile.get("repo_name"),
            "similarity_summary": ai_reply,
            "main_similarities": [],
            "main_differences": [],
            "target_advantages": [],
            "target_weaknesses": [],
            "borrowable_designs": [],
            "comparison_confidence": "low",
            "uncertainty": "AI 返回内容不是标准 JSON，已将原始回答保存到 similarity_summary。"
        }

    comparison["history_repo_name"] = comparison.get(
        "history_repo_name",
        history_profile.get("repo_name")
    )

    comparison["source_profile"] = retrieval_item.get("source_profile")
    comparison["similarity_score"] = retrieval_item.get("similarity_score")
    comparison["retrieval_mode"] = retrieval_item.get("retrieval_mode", "structured")
    comparison["score_detail"] = retrieval_item.get("score_detail", {})
    comparison["retrieval_explanations"] = retrieval_item.get("explanations", [])

    if retrieval_item.get("retrieval_mode") == "hybrid":
        comparison["hybrid_score"] = retrieval_item.get("hybrid_score")
        comparison["structured_score"] = retrieval_item.get("structured_score")
        comparison["semantic_score"] = retrieval_item.get("semantic_score")
        comparison["semantic_evidence"] = retrieval_item.get("semantic_evidence", [])
        comparison["retrieval_source"] = retrieval_item.get("source", [])

    return comparison


def compare_retrieval_results_with_ai(retrieval_result_path, ask_ai_once):
    """
    对检索得到的 Top-K 相似历史项目进行 AI 对比解释。

    v4.5:
    同时兼容：
    - retrieve_full 结构检索结果
    - hybrid_retrieve 融合检索结果
    """

    retrieval_result = load_json_file(retrieval_result_path)

    retrieval_mode = detect_retrieval_mode(retrieval_result)

    target_profile_path = get_target_profile_path_from_retrieval_result(
        retrieval_result
    )

    target_profile = load_json_file(target_profile_path)

    target_repo_name = get_target_repo_name_from_retrieval_result(
        retrieval_result=retrieval_result,
        target_profile=target_profile
    )

    raw_results = extract_retrieval_results(retrieval_result)

    normalized_results = []

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        normalized_item = normalize_retrieval_item_for_comparison(
            item=item,
            retrieval_mode=retrieval_mode
        )

        normalized_results.append(normalized_item)

    comparisons = []

    for index, item in enumerate(normalized_results, start=1):
        source_profile = item.get("source_profile")

        if not source_profile or not os.path.exists(source_profile):
            comparisons.append(
                build_missing_profile_comparison(
                    item=item,
                    source_profile=source_profile
                )
            )
            continue

        print(
            f"正在进行第 {index}/{len(normalized_results)} 个历史项目 AI 对比："
            f"{item.get('repo_name')}，检索模式：{retrieval_mode}"
        )

        history_profile = load_json_file(source_profile)

        comparison = compare_one_history_project(
            target_profile=target_profile,
            history_profile=history_profile,
            retrieval_item=item,
            ask_ai_once=ask_ai_once
        )

        comparisons.append(comparison)

    comparison_result = {
        "target_repo": target_repo_name,
        "target_profile": target_profile_path,
        "retrieval_result": retrieval_result_path,
        "retrieval_mode": retrieval_mode,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comparison_count": len(comparisons),
        "comparisons": comparisons
    }

    if retrieval_mode == "hybrid":
        comparison_result["structured_weight"] = retrieval_result.get("structured_weight")
        comparison_result["semantic_weight"] = retrieval_result.get("semantic_weight")
        comparison_result["rag_query"] = retrieval_result.get("rag_query")
        comparison_result["hybrid_source"] = {
            "structured_result_path": retrieval_result.get("structured_result_path"),
            "persist_directory": retrieval_result.get("persist_directory"),
            "collection_name": retrieval_result.get("collection_name")
        }

    return comparison_result


def save_history_comparison_full(comparison_result):
    """
    保存 AI 历史项目对比解释结果。
    """

    output_dir = os.path.join(
        "history_knowledge_base",
        "comparisons"
    )

    ensure_dir(output_dir)

    target_repo = comparison_result.get("target_repo", "unknown_repo")

    file_path = os.path.join(
        output_dir,
        f"{target_repo}_history_comparison_full.json"
    )

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(comparison_result, file, ensure_ascii=False, indent=2)

    return file_path


def format_history_comparison_full_preview(comparison_result, save_path):
    """
    生成 AI 历史项目对比结果的终端预览。
    """

    output = []

    output.append("AI 历史项目对比解释完成。")
    output.append("")
    output.append(f"目标仓库：{comparison_result.get('target_repo')}")
    output.append(f"检索模式：{comparison_result.get('retrieval_mode', 'structured')}")
    output.append(f"对比项目数量：{comparison_result.get('comparison_count')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("对比结果预览：")

    comparisons = comparison_result.get("comparisons", [])

    if not comparisons:
        output.append("暂无对比结果。")
        return "\n".join(output)

    for index, item in enumerate(comparisons, start=1):
        output.append(f"{index}. 历史仓库：{item.get('history_repo_name')}")
        output.append(f"   相似度：{item.get('similarity_score')}")
        if item.get("retrieval_mode") == "hybrid":
            output.append(f"   Hybrid分数：{item.get('hybrid_score')}")
            output.append(f"   结构分数：{item.get('structured_score')}")
            output.append(f"   语义分数：{item.get('semantic_score')}")
        output.append(f"   置信度：{item.get('comparison_confidence')}")
        output.append(f"   总结：{item.get('similarity_summary')}")
        output.append("   主要相似点：")

        for point in item.get("main_similarities", [])[:3]:
            output.append(f"   - {point}")

        output.append("")

    return "\n".join(output)