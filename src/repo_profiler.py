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