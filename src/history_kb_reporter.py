import os
import json
from datetime import datetime
from collections import Counter, defaultdict


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


def safe_number(value, default=0):
    """
    安全转换为数字。
    """

    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_list(value):
    """
    安全转换为列表。
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


def extract_profiles(history_kb):
    """
    从 history_profiles_full.json 中提取 profiles。

    为了兼容不同版本，这里支持多种字段名。
    """

    if "profiles" in history_kb and isinstance(history_kb["profiles"], list):
        return history_kb["profiles"]

    if "history_profiles" in history_kb and isinstance(history_kb["history_profiles"], list):
        return history_kb["history_profiles"]

    if "items" in history_kb and isinstance(history_kb["items"], list):
        return history_kb["items"]

    return []


def count_distribution(items):
    """
    统计分布。
    """

    counter = Counter()

    for item in items:
        if item is None or item == "":
            counter["unknown"] += 1
        else:
            counter[str(item)] += 1

    return dict(counter)


def format_distribution_table(distribution):
    """
    将分布字典格式化为 Markdown 表格。
    """

    if not distribution:
        return "暂无统计数据。"

    total = sum(distribution.values())

    lines = []
    lines.append("| 项目 | 数量 | 占比 |")
    lines.append("|---|---:|---:|")

    sorted_items = sorted(
        distribution.items(),
        key=lambda item: item[1],
        reverse=True
    )

    for key, count in sorted_items:
        ratio = 0

        if total > 0:
            ratio = count / total * 100

        lines.append(f"| {key} | {count} | {ratio:.2f}% |")

    return "\n".join(lines)


def average(values):
    """
    求平均值。
    """

    numbers = [safe_number(value) for value in values]

    if not numbers:
        return 0

    return sum(numbers) / len(numbers)


def get_average_module_completeness(profile):
    """
    计算单个项目的平均模块完整度。

    兼容几种可能结构：
    1. module_completeness = {"memory": 0.8, ...}
    2. core_module_details = [{"completeness": 0.8}, ...]
    3. average_module_completeness 直接存在
    """

    if "average_module_completeness" in profile:
        return safe_number(profile.get("average_module_completeness"))

    module_completeness = profile.get("module_completeness")

    if isinstance(module_completeness, dict):
        values = [
            safe_number(value)
            for value in module_completeness.values()
            if value is not None
        ]

        if values:
            return sum(values) / len(values)

    core_module_details = profile.get("core_module_details", [])

    if isinstance(core_module_details, list):
        values = []

        for item in core_module_details:
            if isinstance(item, dict):
                values.append(safe_number(item.get("completeness")))

        if values:
            return sum(values) / len(values)

    return 0


def collect_basic_statistics(profiles):
    """
    汇总历史知识库基础统计。
    """

    repo_count = len(profiles)

    function_counts = [
        safe_number(profile.get("function_count"))
        for profile in profiles
    ]

    edge_counts = [
        safe_number(profile.get("edge_count"))
        for profile in profiles
    ]

    module_counts = [
        safe_number(profile.get("module_count"))
        for profile in profiles
    ]

    structure_complexities = [
        safe_number(profile.get("structure_complexity"))
        for profile in profiles
    ]

    average_completeness_values = [
        get_average_module_completeness(profile)
        for profile in profiles
    ]

    return {
        "repo_count": repo_count,
        "average_function_count": average(function_counts),
        "average_edge_count": average(edge_counts),
        "average_module_count": average(module_counts),
        "average_structure_complexity": average(structure_complexities),
        "average_module_completeness": average(average_completeness_values),
        "max_function_count": max(function_counts) if function_counts else 0,
        "max_edge_count": max(edge_counts) if edge_counts else 0,
        "max_structure_complexity": max(structure_complexities) if structure_complexities else 0
    }


def collect_project_type_distribution(profiles):
    """
    统计项目类型分布。
    """

    project_types = [
        profile.get("project_type", "unknown")
        for profile in profiles
    ]

    return count_distribution(project_types)


def collect_language_distribution(profiles):
    """
    统计语言分布。
    """

    languages = []

    for profile in profiles:
        main_languages = safe_list(profile.get("main_languages"))

        if not main_languages:
            languages.append("unknown")
        else:
            for language in main_languages:
                languages.append(language)

    return count_distribution(languages)


def collect_core_module_distribution(profiles):
    """
    统计核心模块覆盖情况。
    """

    modules = []

    for profile in profiles:
        core_modules = safe_list(profile.get("core_modules"))

        if not core_modules:
            modules.append("unknown")
        else:
            for module in core_modules:
                modules.append(module)

    return count_distribution(modules)


def build_rank_table(profiles, field_name, title_name, top_n=10):
    """
    根据指定字段生成排名表。
    """

    if not profiles:
        return "暂无项目。"

    sorted_profiles = sorted(
        profiles,
        key=lambda profile: safe_number(profile.get(field_name)),
        reverse=True
    )

    lines = []
    lines.append(f"| 排名 | 仓库名 | {title_name} | 项目类型 | 核心模块 |")
    lines.append("|---:|---|---:|---|---|")

    for index, profile in enumerate(sorted_profiles[:top_n], start=1):
        repo_name = profile.get("repo_name", "unknown")
        value = safe_number(profile.get(field_name))
        project_type = profile.get("project_type", "unknown")
        core_modules = "、".join(safe_list(profile.get("core_modules"))) or "unknown"

        lines.append(
            f"| {index} | {repo_name} | {value:.2f} | {project_type} | {core_modules} |"
        )

    return "\n".join(lines)


def build_module_completeness_rank_table(profiles, top_n=10):
    """
    根据平均模块完整度生成排名表。
    """

    if not profiles:
        return "暂无项目。"

    enriched_profiles = []

    for profile in profiles:
        copied = dict(profile)
        copied["average_module_completeness_for_report"] = get_average_module_completeness(profile)
        enriched_profiles.append(copied)

    sorted_profiles = sorted(
        enriched_profiles,
        key=lambda profile: safe_number(profile.get("average_module_completeness_for_report")),
        reverse=True
    )

    lines = []
    lines.append("| 排名 | 仓库名 | 平均模块完整度 | 项目类型 | 核心模块 |")
    lines.append("|---:|---|---:|---|---|")

    for index, profile in enumerate(sorted_profiles[:top_n], start=1):
        repo_name = profile.get("repo_name", "unknown")
        completeness = safe_number(profile.get("average_module_completeness_for_report"))
        project_type = profile.get("project_type", "unknown")
        core_modules = "、".join(safe_list(profile.get("core_modules"))) or "unknown"

        lines.append(
            f"| {index} | {repo_name} | {completeness:.2f} | {project_type} | {core_modules} |"
        )

    return "\n".join(lines)


def build_history_kb_quality_comment(statistics, project_type_distribution, module_distribution):
    """
    根据统计结果生成历史知识库质量评价。
    """

    repo_count = statistics.get("repo_count", 0)
    average_function_count = statistics.get("average_function_count", 0)
    average_edge_count = statistics.get("average_edge_count", 0)

    project_type_count = len(project_type_distribution)
    module_type_count = len(module_distribution)

    lines = []

    if repo_count >= 20:
        lines.append("当前历史知识库已经具备较好的规模基础，可以支持较稳定的相似项目检索。")
    elif repo_count >= 10:
        lines.append("当前历史知识库已经具备初步规模，但后续仍建议继续扩充历史项目数量。")
    elif repo_count > 0:
        lines.append("当前历史知识库仍处于初步阶段，可以用于流程验证，但相似检索的代表性还有限。")
    else:
        lines.append("当前历史知识库为空，暂时无法支撑有效的历史项目检索。")

    if average_function_count >= 100 and average_edge_count >= 300:
        lines.append("从平均函数数量和调用边数量看，历史库中已经包含一定规模的系统级项目。")
    elif average_function_count >= 30:
        lines.append("从平均函数数量看，历史库中项目具备一定代码规模，但复杂系统项目比例仍可继续提高。")
    else:
        lines.append("从平均函数数量看，历史库项目整体规模偏小，后续应补充更完整的 OS 项目。")

    if project_type_count >= 4:
        lines.append("项目类型覆盖较丰富，有利于提高不同类型目标项目的检索质量。")
    else:
        lines.append("项目类型覆盖仍不够丰富，后续应补充更多不同方向的历史项目。")

    if module_type_count >= 6:
        lines.append("核心模块覆盖较全面，已包含多类 OS 模块特征。")
    else:
        lines.append("核心模块覆盖仍需扩展，建议补充 memory、process、scheduler、filesystem、driver 等不同类型项目。")

    return "\n".join(f"- {line}" for line in lines)


def generate_history_kb_report(history_kb_path):
    """
    生成历史知识库统计报告。
    """

    history_kb = load_json_file(history_kb_path)
    profiles = extract_profiles(history_kb)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    statistics = collect_basic_statistics(profiles)
    project_type_distribution = collect_project_type_distribution(profiles)
    language_distribution = collect_language_distribution(profiles)
    core_module_distribution = collect_core_module_distribution(profiles)

    lines = []

    lines.append("# 历史知识库统计报告")
    lines.append("")
    lines.append(f"生成时间：{created_at}")
    lines.append(f"输入文件：`{history_kb_path}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 1. 历史库概览")
    lines.append("")
    lines.append(f"- 历史项目数量：`{statistics.get('repo_count')}`")
    lines.append(f"- 平均函数数量：`{statistics.get('average_function_count'):.2f}`")
    lines.append(f"- 平均调用边数量：`{statistics.get('average_edge_count'):.2f}`")
    lines.append(f"- 平均模块数量：`{statistics.get('average_module_count'):.2f}`")
    lines.append(f"- 平均结构复杂度：`{statistics.get('average_structure_complexity'):.2f}`")
    lines.append(f"- 平均模块完整度：`{statistics.get('average_module_completeness'):.2f}`")
    lines.append(f"- 最大函数数量：`{statistics.get('max_function_count'):.2f}`")
    lines.append(f"- 最大调用边数量：`{statistics.get('max_edge_count'):.2f}`")
    lines.append(f"- 最大结构复杂度：`{statistics.get('max_structure_complexity'):.2f}`")
    lines.append("")

    lines.append("## 2. 项目类型分布")
    lines.append("")
    lines.append(format_distribution_table(project_type_distribution))
    lines.append("")

    lines.append("## 3. 语言分布")
    lines.append("")
    lines.append(format_distribution_table(language_distribution))
    lines.append("")

    lines.append("## 4. 核心模块覆盖情况")
    lines.append("")
    lines.append(format_distribution_table(core_module_distribution))
    lines.append("")

    lines.append("## 5. 函数数量排名")
    lines.append("")
    lines.append(build_rank_table(
        profiles=profiles,
        field_name="function_count",
        title_name="函数数量",
        top_n=10
    ))
    lines.append("")

    lines.append("## 6. 调用边数量排名")
    lines.append("")
    lines.append(build_rank_table(
        profiles=profiles,
        field_name="edge_count",
        title_name="调用边数量",
        top_n=10
    ))
    lines.append("")

    lines.append("## 7. 结构复杂度排名")
    lines.append("")
    lines.append(build_rank_table(
        profiles=profiles,
        field_name="structure_complexity",
        title_name="结构复杂度",
        top_n=10
    ))
    lines.append("")

    lines.append("## 8. 模块完整度排名")
    lines.append("")
    lines.append(build_module_completeness_rank_table(
        profiles=profiles,
        top_n=10
    ))
    lines.append("")

    lines.append("## 9. 历史知识库质量评价")
    lines.append("")
    lines.append(build_history_kb_quality_comment(
        statistics=statistics,
        project_type_distribution=project_type_distribution,
        module_distribution=core_module_distribution
    ))
    lines.append("")

    lines.append("## 10. 后续建议")
    lines.append("")
    lines.append("- 继续扩充历史 OS 项目数量，优先覆盖不同类型的项目。")
    lines.append("- 对历史项目进行统一 full 分析，减少 quick 模式带来的覆盖不足。")
    lines.append("- 后续可将 repo_profile_full、module_summary_full 和 final_report 转换为 RAG 文档，增强语义检索能力。")
    lines.append("- 可以将该统计报告用于展示系统历史知识库规模与覆盖情况。")
    lines.append("")

    return {
        "created_at": created_at,
        "history_kb_path": history_kb_path,
        "profile_count": statistics.get("repo_count"),
        "report_text": "\n".join(lines)
    }


def save_history_kb_report(report_result):
    """
    保存历史知识库统计报告。
    """

    output_dir = "history_knowledge_base"
    ensure_dir(output_dir)

    output_path = os.path.join(
        output_dir,
        "history_kb_report.md"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report_result.get("report_text", ""))

    return output_path


def format_history_kb_report_preview(report_result, save_path):
    """
    生成终端预览。
    """

    lines = []

    lines.append("历史知识库统计报告生成完成。")
    lines.append("")
    lines.append(f"输入文件：{report_result.get('history_kb_path')}")
    lines.append(f"历史项目数量：{report_result.get('profile_count')}")
    lines.append(f"保存路径：{save_path}")

    return "\n".join(lines)