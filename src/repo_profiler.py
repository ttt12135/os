import os
import json
from datetime import datetime


def ensure_dir(dir_path):
    """
    如果目录不存在，就自动创建。
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_repo_name(repo_path):
    """
    从仓库路径中提取仓库名称。
    """
    repo_path = os.path.normpath(repo_path)
    return os.path.basename(repo_path)


def summarize_function_modules(function_analysis_data):
    """
    统计函数理解结果中出现的模块分布。
    """

    functions = function_analysis_data.get("functions", [])

    module_count = {}

    for func in functions:
        module = func.get("related_os_module", "unknown")

        if module is None or module == "":
            module = "unknown"

        if module not in module_count:
            module_count[module] = 0

        module_count[module] += 1

    return module_count


def summarize_call_graph(call_graph_data):
    """
    汇总调用图基本信息。
    """

    edges = call_graph_data.get("edges", [])

    high_confidence_edges = []

    for edge in edges:
        confidence = edge.get("confidence", 0)

        if confidence >= 0.8:
            high_confidence_edges.append(edge)

    return {
        "edge_count": len(edges),
        "high_confidence_edge_count": len(high_confidence_edges),
        "high_confidence_edges_preview": high_confidence_edges[:10]
    }


def summarize_modules(module_summary_data):
    """
    汇总模块总结结果。
    """

    modules = module_summary_data.get("modules", [])

    module_names = []

    for module in modules:
        module_names.append(module.get("module_name", "unknown"))

    return {
        "module_count": len(modules),
        "module_names": module_names,
        "modules": modules
    }


def build_repo_profile(
    repo_path,
    file_tree,
    file_scores,
    function_analysis_path,
    call_graph_path,
    module_summary_path
):
    """
    构建单仓库画像。
    """

    repo_name = get_repo_name(repo_path)

    function_analysis_data = load_json_file(function_analysis_path)
    call_graph_data = load_json_file(call_graph_path)
    module_summary_data = load_json_file(module_summary_path)

    function_module_count = summarize_function_modules(function_analysis_data)
    call_graph_summary = summarize_call_graph(call_graph_data)
    module_summary = summarize_modules(module_summary_data)

    profile = {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "basic_info": {
            "repo_name": repo_name,
            "repo_path": repo_path
        },

        "file_tree": file_tree,

        "file_scores": file_scores,

        "function_analysis_summary": {
            "analysis_count": function_analysis_data.get("analysis_count", 0),
            "module_distribution": function_module_count
        },

        "call_graph_summary": call_graph_summary,

        "module_summary": module_summary,

        "source_files": {
            "function_analysis_path": function_analysis_path,
            "call_graph_path": call_graph_path,
            "module_summary_path": module_summary_path
        },

        "uncertainty": [
            "当前仓库画像基于静态分析结果生成，尚未实际编译运行项目。",
            "函数切片和调用关系提取可能受到宏、泛型、条件编译和跨语言调用影响。",
            "模块总结依赖已分析的代码块，未深度分析的代码可能暂未覆盖。"
        ]
    }

    return profile


def save_repo_profile(profile, profile_type="history"):
    """
    保存仓库画像 JSON，
    区分历史仓库和目标仓库
    """


    if profile_type == "history":
        output_dir = "repo_profiles/history"
    elif profile_type == "target":
        output_dir = "repo_profiles/target"
    else:
        output_dir = "repo_profiles/other"

    ensure_dir(output_dir)

    repo_name = profile.get("repo_name", "unknown_repo")
    file_name = f"{repo_name}_repo_profile.json"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, ensure_ascii=False, indent=2)

    return file_path


def format_repo_profile_preview(profile, save_path):
    """
    生成终端显示摘要。
    """

    output = []

    output.append("仓库画像生成完成。")
    output.append("")
    output.append(f"仓库名称：{profile.get('repo_name')}")
    output.append(f"保存路径：{save_path}")
    output.append("")

    function_summary = profile.get("function_analysis_summary", {})
    output.append(f"函数分析数量：{function_summary.get('analysis_count')}")
    output.append("模块分布：")

    module_distribution = function_summary.get("module_distribution", {})

    for module, count in module_distribution.items():
        output.append(f"- {module}: {count}")

    output.append("")

    call_graph_summary = profile.get("call_graph_summary", {})
    output.append(f"调用边数量：{call_graph_summary.get('edge_count')}")
    output.append(f"高置信度调用边数量：{call_graph_summary.get('high_confidence_edge_count')}")
    output.append("")

    module_summary = profile.get("module_summary", {})
    output.append(f"模块总结数量：{module_summary.get('module_count')}")
    output.append("模块列表：")

    for module_name in module_summary.get("module_names", []):
        output.append(f"- {module_name}")

    return "\n".join(output)

def estimate_module_completeness(module_profile):
    """
    根据模块函数数量、调用关系和文件数量，粗略估算模块完成度。
    返回 0 到 1 之间的小数。

    这不是最终评分，而是用于仓库画像的结构化参考指标。
    """

    function_count = module_profile.get("function_count", 0)
    outgoing_edge_count = module_profile.get("outgoing_edge_count", 0)
    internal_edge_count = module_profile.get("internal_edge_count", 0)
    file_count = module_profile.get("file_count", 0)

    score = 0.0

    if function_count >= 20:
        score += 0.35
    elif function_count >= 10:
        score += 0.25
    elif function_count >= 5:
        score += 0.15
    elif function_count > 0:
        score += 0.08

    if outgoing_edge_count >= 30:
        score += 0.25
    elif outgoing_edge_count >= 15:
        score += 0.18
    elif outgoing_edge_count >= 5:
        score += 0.10
    elif outgoing_edge_count > 0:
        score += 0.05

    if internal_edge_count >= 15:
        score += 0.25
    elif internal_edge_count >= 8:
        score += 0.18
    elif internal_edge_count >= 3:
        score += 0.10
    elif internal_edge_count > 0:
        score += 0.05

    if file_count >= 5:
        score += 0.15
    elif file_count >= 3:
        score += 0.10
    elif file_count >= 1:
        score += 0.05

    return min(round(score, 2), 1.0)

def infer_project_type(module_profiles):
    """
    根据模块分布粗略推断 OS 项目类型。
    """

    module_names = set(module_profiles.keys())

    has_memory = "memory" in module_names
    has_process = "process" in module_names
    has_scheduler = "scheduler" in module_names
    has_filesystem = "filesystem" in module_names
    has_syscall = "syscall" in module_names
    has_driver = "driver" in module_names
    has_interrupt = "interrupt" in module_names
    has_network = "network" in module_names

    if has_memory and has_process and has_syscall:
        if has_filesystem and has_driver:
            return "teaching_os_or_general_kernel"

        if has_scheduler or has_interrupt:
            return "minimal_general_kernel"

        return "basic_kernel"

    if has_scheduler and has_driver and not has_filesystem:
        return "rtos_like_kernel"

    if has_filesystem and not has_process:
        return "filesystem_focused_project"

    if has_network and has_driver:
        return "network_or_driver_focused_kernel"

    if has_memory and not has_process:
        return "memory_management_focused_project"

    return "unknown_os_project"


def estimate_structure_complexity(call_graph, module_profiles):
    """
    根据调用图和模块分布估算仓库结构复杂度。
    """

    node_count = call_graph.get("node_count", 0)
    edge_count = call_graph.get("merged_edge_count", 0)
    internal_edge_count = call_graph.get("internal_edge_count", 0)
    module_count = len(module_profiles)

    score = 0.0

    if node_count >= 200:
        score += 0.30
    elif node_count >= 100:
        score += 0.22
    elif node_count >= 50:
        score += 0.15
    elif node_count > 0:
        score += 0.08

    if edge_count >= 500:
        score += 0.30
    elif edge_count >= 200:
        score += 0.22
    elif edge_count >= 80:
        score += 0.15
    elif edge_count > 0:
        score += 0.08

    if internal_edge_count >= 200:
        score += 0.20
    elif internal_edge_count >= 80:
        score += 0.15
    elif internal_edge_count >= 30:
        score += 0.10
    elif internal_edge_count > 0:
        score += 0.05

    if module_count >= 8:
        score += 0.20
    elif module_count >= 5:
        score += 0.15
    elif module_count >= 3:
        score += 0.10
    elif module_count > 0:
        score += 0.05

    return min(round(score, 2), 1.0)


def select_core_modules(module_profiles, max_modules=5):
    """
    根据模块权重和完成度选择核心模块。
    """

    scored_modules = []

    for module_name, profile in module_profiles.items():
        module_weight = profile.get("module_weight", 0)
        completeness = estimate_module_completeness(profile)

        final_score = module_weight * 0.6 + completeness * 0.4

        scored_modules.append(
            {
                "module_name": module_name,
                "module_weight": module_weight,
                "completeness": completeness,
                "final_score": round(final_score, 4)
            }
        )

    scored_modules.sort(
        key=lambda item: item.get("final_score", 0),
        reverse=True
    )

    return scored_modules[:max_modules]


def infer_main_languages_from_modules(module_profiles):
    """
    从核心函数信息中粗略统计主要语言。
    """

    language_count = {}

    for profile in module_profiles.values():
        core_functions = profile.get("core_functions", [])

        for function in core_functions:
            language = function.get("language")

            if not language:
                continue

            if language not in language_count:
                language_count[language] = 0

            language_count[language] += 1

    sorted_languages = sorted(
        language_count.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [language for language, count in sorted_languages]


def build_repo_profile_full(repo_name, call_graph, module_summary_full, profile_type="target"):
    """
    构建 full 版本仓库画像。

    数据来源：
    - call_graph_full / enhanced
    - module_summary_full
    """

    module_profiles = module_summary_full.get("modules", {})

    module_completeness = {}

    for module_name, module_profile in module_profiles.items():
        module_completeness[module_name] = estimate_module_completeness(
            module_profile
        )

    core_module_items = select_core_modules(
        module_profiles=module_profiles,
        max_modules=5
    )

    core_modules = [
        item.get("module_name")
        for item in core_module_items
    ]

    structure_complexity = estimate_structure_complexity(
        call_graph=call_graph,
        module_profiles=module_profiles
    )

    main_languages = infer_main_languages_from_modules(module_profiles)

    profile = {
        "repo_name": repo_name,
        "profile_type": "full",
        "target_or_history": profile_type,
        "project_type": infer_project_type(module_profiles),
        "main_languages": main_languages,
        "function_count": call_graph.get("function_count", 0),
        "node_count": call_graph.get("node_count", 0),
        "edge_count": call_graph.get("merged_edge_count", 0),
        "internal_edge_count": call_graph.get("internal_edge_count", 0),
        "external_edge_count": call_graph.get("external_edge_count", 0),
        "module_count": module_summary_full.get("module_count", 0),
        "core_modules": core_modules,
        "core_module_details": core_module_items,
        "module_completeness": module_completeness,
        "structure_complexity": structure_complexity,
        "module_profiles": module_profiles,
        "data_quality": {
            "data_sources": [
                "function_analysis",
                "call_graph",
                "module_summary_full"
            ],
            "note": "当前画像基于静态代码切片、AI 函数理解和调用图统计生成，模块分类可能受到 AI 输出质量影响。"
        },
        "technical_features": [],
        "weaknesses": [],
        "created_by": "os_analysis_agent"
    }

    return profile


def save_repo_profile_full(profile, profile_type="target"):
    """
    保存 full 版本仓库画像。

    profile_type:
    target：保存到 repo_profiles/target/
    history：保存到 repo_profiles/history/
    """

    repo_name = profile.get("repo_name", "unknown_repo")

    if profile_type == "history":
        output_dir = os.path.join("repo_profiles", "history")
    else:
        output_dir = os.path.join("repo_profiles", "target")

    ensure_dir(output_dir)

    file_name = f"{repo_name}_repo_profile_full.json"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, ensure_ascii=False, indent=2)

    return file_path



def format_repo_profile_full_preview(profile, save_path):
    """
    生成 full 仓库画像的终端预览。
    """

    output = []

    output.append("full 仓库画像生成完成。")
    output.append("")
    output.append(f"仓库名称：{profile.get('repo_name')}")
    output.append(f"项目类型：{profile.get('project_type')}")
    output.append(f"主要语言：{', '.join(profile.get('main_languages', []))}")
    output.append(f"函数数量：{profile.get('function_count')}")
    output.append(f"调用边数量：{profile.get('edge_count')}")
    output.append(f"模块数量：{profile.get('module_count')}")
    output.append(f"结构复杂度：{profile.get('structure_complexity')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("核心模块：")

    for item in profile.get("core_module_details", []):
        output.append(
            f"- {item.get('module_name')} | "
            f"权重：{item.get('module_weight')} | "
            f"完成度：{item.get('completeness')} | "
            f"综合值：{item.get('final_score')}"
        )

    return "\n".join(output)