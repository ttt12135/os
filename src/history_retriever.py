import json
import os


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_module_names_from_profile(profile):
    """
    从 repo_profile 或 history_profile 中提取模块名称集合。
    """

    module_summary = profile.get("module_summary", {})
    module_names = module_summary.get("module_names", [])

    if module_names is None:
        return set()

    return set(module_names)


def get_module_distribution(profile):
    """
    从 repo_profile 中提取函数模块分布。
    """

    function_summary = profile.get("function_analysis_summary", {})
    module_distribution = function_summary.get("module_distribution", {})

    if module_distribution is None:
        return {}

    return module_distribution


def calculate_module_overlap_score(target_profile, history_profile):
    """
    计算模块重合度分数。

    分数范围：0 到 1。
    """

    target_modules = get_module_names_from_profile(target_profile)
    history_modules = get_module_names_from_profile(history_profile)

    if len(target_modules) == 0 or len(history_modules) == 0:
        return 0

    intersection = target_modules & history_modules
    union = target_modules | history_modules

    return len(intersection) / len(union)


def calculate_module_distribution_score(target_profile, history_profile):
    """
    根据函数模块分布计算相似度。

    简单做法：
    看两个仓库函数分析结果中出现的模块是否相似。
    """

    target_distribution = get_module_distribution(target_profile)
    history_distribution = get_module_distribution(history_profile)

    target_modules = set(target_distribution.keys())
    history_modules = set(history_distribution.keys())

    if len(target_modules) == 0 or len(history_modules) == 0:
        return 0

    intersection = target_modules & history_modules
    union = target_modules | history_modules

    return len(intersection) / len(union)


def calculate_call_graph_score(target_profile, history_profile):
    """
    根据调用图规模粗略计算相似度。

    注意：
    这不是深度调用图对比，只是初步用调用边数量判断复杂度是否接近。
    """

    target_call_graph = target_profile.get("call_graph_summary", {})
    history_call_graph = history_profile.get("call_graph_summary", {})

    target_edges = target_call_graph.get("edge_count", 0)
    history_edges = history_call_graph.get("edge_count", 0)

    if target_edges == 0 or history_edges == 0:
        return 0

    smaller = min(target_edges, history_edges)
    larger = max(target_edges, history_edges)

    return smaller / larger


def calculate_similarity_score(target_profile, history_profile):
    """
    综合计算新作品和历史作品的相似度。

    当前是规则版：
    - 模块名称重合度：50%
    - 模块分布相似度：30%
    - 调用图规模相似度：20%
    """

    module_overlap_score = calculate_module_overlap_score(
        target_profile,
        history_profile
    )

    module_distribution_score = calculate_module_distribution_score(
        target_profile,
        history_profile
    )

    call_graph_score = calculate_call_graph_score(
        target_profile,
        history_profile
    )

    total_score = (
        module_overlap_score * 0.5
        + module_distribution_score * 0.3
        + call_graph_score * 0.2
    )

    detail = {
        "module_overlap_score": round(module_overlap_score, 4),
        "module_distribution_score": round(module_distribution_score, 4),
        "call_graph_score": round(call_graph_score, 4),
        "total_score": round(total_score, 4)
    }

    return total_score, detail


def retrieve_similar_history_profiles(
    target_profile_path,
    history_kb_path,
    top_k=5
):
    """
    根据目标作品 repo_profile，从历史知识库中检索相似历史作品。
    """

    target_profile = load_json_file(target_profile_path)
    history_kb = load_json_file(history_kb_path)

    target_repo_name = target_profile.get("repo_name", "unknown_target")
    history_profiles = history_kb.get("profiles", [])

    results = []

    for history_profile in history_profiles:
        history_repo_name = history_profile.get("repo_name", "unknown_history")

        # 避免把自己和自己比较
        if history_repo_name == target_repo_name:
            continue

        score, detail = calculate_similarity_score(
            target_profile,
            history_profile
        )

        results.append(
            {
                "repo_name": history_repo_name,
                "repo_path": history_profile.get("repo_path", ""),
                "source_profile": history_profile.get("source_profile", ""),
                "similarity_score": round(score, 4),
                "score_detail": detail,
                "module_names": history_profile.get("module_summary", {}).get("module_names", []),
                "module_count": history_profile.get("module_summary", {}).get("module_count", 0),
                "edge_count": history_profile.get("call_graph_summary", {}).get("edge_count", 0)
            }
        )

    results.sort(key=lambda item: item["similarity_score"], reverse=True)

    return {
        "target_repo_name": target_repo_name,
        "top_k": top_k,
        "results": results[:top_k]
    }


def format_retrieval_results(retrieval_result):
    """
    格式化检索结果，方便终端显示。
    """

    output = []

    output.append("相似历史作品检索完成。")
    output.append("")
    output.append(f"目标作品：{retrieval_result.get('target_repo_name')}")
    output.append(f"返回数量：Top {retrieval_result.get('top_k')}")
    output.append("")
    output.append("相似历史作品列表：")

    results = retrieval_result.get("results", [])

    if len(results) == 0:
        output.append("没有找到可用于对比的历史作品。")
        return "\n".join(output)

    for index, item in enumerate(results, start=1):
        output.append(f"{index}. {item.get('repo_name')}")
        output.append(f"   相似度：{item.get('similarity_score')}")
        output.append(f"   模块数量：{item.get('module_count')}")
        output.append(f"   调用边数量：{item.get('edge_count')}")
        output.append(f"   模块列表：{', '.join(item.get('module_names', []))}")
        output.append(f"   来源画像：{item.get('source_profile')}")
        output.append("   分数细节：")
        detail = item.get("score_detail", {})
        output.append(f"      模块重合度：{detail.get('module_overlap_score')}")
        output.append(f"      模块分布相似度：{detail.get('module_distribution_score')}")
        output.append(f"      调用图规模相似度：{detail.get('call_graph_score')}")
        output.append("")

    return "\n".join(output)

def calculate_jaccard_similarity(list_a, list_b):
    """
    计算两个列表的 Jaccard 相似度。

    用于比较 core_modules、main_languages 等集合型字段。
    """

    set_a = set(list_a or [])
    set_b = set(list_b or [])

    if not set_a and not set_b:
        return 0.0

    intersection_count = len(set_a.intersection(set_b))
    union_count = len(set_a.union(set_b))

    if union_count == 0:
        return 0.0

    return round(intersection_count / union_count, 4)


def calculate_numeric_similarity(value_a, value_b):
    """
    计算两个数值的相似度。

    数值越接近，相似度越高。
    """

    try:
        value_a = float(value_a)
        value_b = float(value_b)
    except (TypeError, ValueError):
        return 0.0

    if value_a == 0 and value_b == 0:
        return 1.0

    max_value = max(abs(value_a), abs(value_b))

    if max_value == 0:
        return 0.0

    difference = abs(value_a - value_b)

    similarity = 1 - difference / max_value

    if similarity < 0:
        similarity = 0.0

    return round(similarity, 4)


def calculate_module_completeness_similarity(target_modules, history_modules):
    """
    计算两个仓库模块完成度分布的相似度。

    只比较双方共同出现的模块。
    """

    target_modules = target_modules or {}
    history_modules = history_modules or {}

    common_modules = set(target_modules.keys()).intersection(
        set(history_modules.keys())
    )

    if not common_modules:
        return 0.0

    similarities = []

    for module_name in common_modules:
        target_value = target_modules.get(module_name, 0)
        history_value = history_modules.get(module_name, 0)

        similarity = calculate_numeric_similarity(target_value, history_value)

        similarities.append(similarity)

    if not similarities:
        return 0.0

    return round(sum(similarities) / len(similarities), 4)


def calculate_project_type_similarity(target_type, history_type):
    """
    计算项目类型相似度。
    """

    if not target_type or not history_type:
        return 0.0

    if target_type == history_type:
        return 1.0

    related_groups = [
        {
            "teaching_os_or_general_kernel",
            "minimal_general_kernel",
            "basic_kernel"
        },
        {
            "rtos_like_kernel",
            "network_or_driver_focused_kernel"
        },
        {
            "filesystem_focused_project"
        },
        {
            "memory_management_focused_project"
        }
    ]

    for group in related_groups:
        if target_type in group and history_type in group:
            return 0.6

    return 0.0


def calculate_full_profile_similarity(target_profile, history_profile):
    """
    计算目标仓库与单个历史仓库的结构相似度。

    相似度组成：
    project_type：项目类型
    core_modules：核心模块重合度
    module_completeness：模块完成度相似度
    scale：函数/调用边/模块数量规模相似度
    structure_complexity：结构复杂度相似度
    languages：主要语言相似度
    """

    project_type_score = calculate_project_type_similarity(
        target_profile.get("project_type"),
        history_profile.get("project_type")
    )

    core_module_score = calculate_jaccard_similarity(
        target_profile.get("core_modules", []),
        history_profile.get("core_modules", [])
    )

    module_completeness_score = calculate_module_completeness_similarity(
        target_profile.get("module_completeness", {}),
        history_profile.get("module_completeness", {})
    )

    function_count_score = calculate_numeric_similarity(
        target_profile.get("function_count", 0),
        history_profile.get("function_count", 0)
    )

    edge_count_score = calculate_numeric_similarity(
        target_profile.get("edge_count", 0),
        history_profile.get("edge_count", 0)
    )

    module_count_score = calculate_numeric_similarity(
        target_profile.get("module_count", 0),
        history_profile.get("module_count", 0)
    )

    scale_score = round(
        function_count_score * 0.4
        + edge_count_score * 0.4
        + module_count_score * 0.2,
        4
    )

    structure_complexity_score = calculate_numeric_similarity(
        target_profile.get("structure_complexity", 0),
        history_profile.get("structure_complexity", 0)
    )

    language_score = calculate_jaccard_similarity(
        target_profile.get("main_languages", []),
        history_profile.get("main_languages", [])
    )

    overall_score = round(
        project_type_score * 0.20
        + core_module_score * 0.25
        + module_completeness_score * 0.20
        + scale_score * 0.15
        + structure_complexity_score * 0.15
        + language_score * 0.05,
        4
    )

    detail = {
        "project_type_score": project_type_score,
        "core_module_score": core_module_score,
        "module_completeness_score": module_completeness_score,
        "scale_score": scale_score,
        "structure_complexity_score": structure_complexity_score,
        "language_score": language_score,
        "overall_score": overall_score
    }

    return detail


def explain_similarity(target_profile, history_profile, score_detail):
    """
    生成规则检索的可解释说明。
    """

    explanations = []

    target_type = target_profile.get("project_type")
    history_type = history_profile.get("project_type")

    if score_detail.get("project_type_score", 0) == 1.0:
        explanations.append(f"项目类型相同，均为 {target_type}。")
    elif score_detail.get("project_type_score", 0) > 0:
        explanations.append(
            f"项目类型相关，目标项目为 {target_type}，历史项目为 {history_type}。"
        )

    target_modules = set(target_profile.get("core_modules", []))
    history_modules = set(history_profile.get("core_modules", []))
    common_modules = sorted(list(target_modules.intersection(history_modules)))

    if common_modules:
        explanations.append(
            f"核心模块存在重合：{', '.join(common_modules)}。"
        )

    if score_detail.get("scale_score", 0) >= 0.7:
        explanations.append("函数数量、调用边数量和模块数量规模较接近。")

    if score_detail.get("structure_complexity_score", 0) >= 0.7:
        explanations.append("结构复杂度较接近。")

    if score_detail.get("module_completeness_score", 0) >= 0.7:
        explanations.append("共同模块的完成度分布较接近。")

    if not explanations:
        explanations.append("该项目与目标项目存在一定结构相似性，但相似原因不突出。")

    return explanations


def retrieve_similar_history_projects_full(
    target_profile_path,
    history_kb_full_path="history_knowledge_base/history_profiles_full.json",
    top_k=3
):
    """
    基于 repo_profile_full 和 history_profiles_full 检索相似历史项目。
    """

    target_profile = load_json_file(target_profile_path)
    history_kb = load_json_file(history_kb_full_path)

    history_profiles = history_kb.get("profiles", [])

    results = []

    for history_profile in history_profiles:
        if history_profile.get("error"):
            continue

        # 避免目标仓库误混入历史库后和自己比较
        if history_profile.get("repo_name") == target_profile.get("repo_name"):
            continue

        score_detail = calculate_full_profile_similarity(
            target_profile=target_profile,
            history_profile=history_profile
        )

        explanations = explain_similarity(
            target_profile=target_profile,
            history_profile=history_profile,
            score_detail=score_detail
        )

        result = {
            "repo_name": history_profile.get("repo_name"),
            "source_profile": history_profile.get("source_profile"),
            "project_type": history_profile.get("project_type"),
            "core_modules": history_profile.get("core_modules", []),
            "function_count": history_profile.get("function_count", 0),
            "edge_count": history_profile.get("edge_count", 0),
            "module_count": history_profile.get("module_count", 0),
            "structure_complexity": history_profile.get("structure_complexity", 0),
            "similarity_score": score_detail.get("overall_score"),
            "score_detail": score_detail,
            "explanations": explanations
        }

        results.append(result)

    results.sort(
        key=lambda item: item.get("similarity_score", 0),
        reverse=True
    )

    selected_results = results[:top_k]

    retrieval_result = {
        "target_repo": target_profile.get("repo_name"),
        "target_profile": target_profile_path,
        "history_kb": history_kb_full_path,
        "top_k": top_k,
        "candidate_count": len(results),
        "results": selected_results
    }

    return retrieval_result


def save_retrieval_result_full(retrieval_result):
    """
    保存 full 相似历史项目检索结果。
    """

    output_dir = os.path.join(
        "history_knowledge_base",
        "retrieval_results"
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    target_repo = retrieval_result.get("target_repo", "unknown_repo")

    file_path = os.path.join(
        output_dir,
        f"{target_repo}_similar_projects_full.json"
    )

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(retrieval_result, file, ensure_ascii=False, indent=2)

    return file_path

def format_retrieval_result_full_preview(retrieval_result, save_path):
    """
    生成 full 相似历史项目检索结果的终端预览。
    """

    output = []

    output.append("full 相似历史项目检索完成。")
    output.append("")
    output.append(f"目标仓库：{retrieval_result.get('target_repo')}")
    output.append(f"候选历史项目数量：{retrieval_result.get('candidate_count')}")
    output.append(f"Top-K：{retrieval_result.get('top_k')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("相似项目结果：")

    results = retrieval_result.get("results", [])

    if not results:
        output.append("暂无相似历史项目。")
        return "\n".join(output)

    for index, item in enumerate(results, start=1):
        output.append(f"{index}. {item.get('repo_name')}")
        output.append(f"   相似度：{item.get('similarity_score')}")
        output.append(f"   项目类型：{item.get('project_type')}")
        output.append(f"   核心模块：{item.get('core_modules')}")
        output.append(f"   函数数量：{item.get('function_count')}")
        output.append(f"   调用边数量：{item.get('edge_count')}")
        output.append("   相似依据：")

        for explanation in item.get("explanations", []):
            output.append(f"   - {explanation}")

        output.append("")

    return "\n".join(output)