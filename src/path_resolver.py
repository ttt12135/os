import os
import json


def normalize_input_path(path):
    """
    规范化用户输入路径。
    去掉首尾空格和引号，避免复制 Windows 路径时出错。
    """

    if path is None:
        return ""

    path = path.strip()
    path = path.strip('"')
    path = path.strip("'")

    return path


def load_json_file_safe(file_path):
    """
    安全读取 JSON 文件。
    """

    file_path = normalize_input_path(file_path)

    if os.path.isdir(file_path):
        raise IsADirectoryError(
            f"你输入的是文件夹路径，不是 JSON 文件路径：{file_path}\n"
            f"请继续进入该文件夹，选择具体的 .json 文件。"
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


def infer_repo_name_from_json_path(file_path):
    """
    从常见 JSON 文件名中反推出 repo_name。
    """

    file_path = normalize_input_path(file_path)
    file_name = os.path.basename(file_path)

    suffixes = [
        "_repo_profile_full.json",
        "_similar_projects_full.json",
        "_history_comparison_full.json",
        "_score_full.json",
        "_final_report.json"
    ]

    for suffix in suffixes:
        if file_name.endswith(suffix):
            return file_name.replace(suffix, "")

    if file_name.endswith(".json"):
        return file_name.replace(".json", "")

    return file_name


def build_default_final_report_paths(repo_name):
    """
    根据仓库名自动构造 final_report 需要的四个输入路径。
    """

    return {
        "repo_profile_path": os.path.join(
            "repo_profiles",
            "target",
            f"{repo_name}_repo_profile_full.json"
        ),
        "retrieval_result_path": os.path.join(
            "history_knowledge_base",
            "retrieval_results",
            f"{repo_name}_similar_projects_full.json"
        ),
        "comparison_result_path": os.path.join(
            "history_knowledge_base",
            "comparisons",
            f"{repo_name}_history_comparison_full.json"
        ),
        "score_result_path": os.path.join(
            "evaluation",
            f"{repo_name}_score_full.json"
        )
    }


def check_required_json_files(path_map):
    """
    检查 final_report 所需的四个 JSON 文件是否存在。
    """

    missing_files = []

    for key, file_path in path_map.items():
        file_path = normalize_input_path(file_path)

        if not os.path.exists(file_path):
            missing_files.append((key, file_path))
        elif os.path.isdir(file_path):
            missing_files.append((key, file_path))

    if missing_files:
        lines = []
        lines.append("缺少以下必要 JSON 文件：")

        for key, file_path in missing_files:
            lines.append(f"- {key}: {file_path}")

        lines.append("")
        lines.append("请先确认对应步骤是否已经运行：")
        lines.append("- repo_profile_path 缺失：先运行 analyze_target")
        lines.append("- retrieval_result_path 缺失：先运行 retrieve_full")
        lines.append("- comparison_result_path 缺失：先运行 compare_full")
        lines.append("- score_result_path 缺失：先运行 score_full")

        raise FileNotFoundError("\n".join(lines))


def resolve_final_report_paths(repo_name_or_path):
    """
    根据用户输入自动推断 final_report 所需路径。

    支持两种输入：
    1. 仓库名，例如 zhengzhoudaxue111
    2. repo_profile_full.json 路径，例如 repo_profiles/target/xxx_repo_profile_full.json
    """

    repo_name_or_path = normalize_input_path(repo_name_or_path)

    if repo_name_or_path == "":
        raise ValueError("输入不能为空。请输入仓库名或 repo_profile_full.json 路径。")

    if os.path.isdir(repo_name_or_path):
        raise IsADirectoryError(
            f"你输入的是文件夹路径：{repo_name_or_path}\n"
            f"请直接输入仓库名，例如 zhengzhoudaxue111；"
            f"或者输入具体的 repo_profile_full.json 文件路径。"
        )

    if repo_name_or_path.endswith(".json"):
        repo_name = infer_repo_name_from_json_path(repo_name_or_path)
    else:
        repo_name = repo_name_or_path

    path_map = build_default_final_report_paths(repo_name)

    check_required_json_files(path_map)

    return repo_name, path_map


def format_resolved_paths_preview(repo_name, path_map):
    """
    格式化展示自动推断出的路径。
    """

    lines = []

    lines.append(f"已根据仓库名 `{repo_name}` 自动推断 final_report 输入路径：")
    lines.append("")
    lines.append(f"- repo_profile_full: {path_map.get('repo_profile_path')}")
    lines.append(f"- retrieve_full: {path_map.get('retrieval_result_path')}")
    lines.append(f"- compare_full: {path_map.get('comparison_result_path')}")
    lines.append(f"- score_full: {path_map.get('score_result_path')}")

    return "\n".join(lines)