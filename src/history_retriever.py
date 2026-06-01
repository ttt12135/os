import json


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