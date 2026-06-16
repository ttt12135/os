import os
import json
from datetime import datetime


def ensure_dir(directory):
    """
    如果目录不存在，就创建目录。
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_join(items, default="无"):
    """
    安全拼接列表。
    """

    if not items:
        return default

    return "、".join(str(item) for item in items)


def format_markdown_list(items, empty_text="暂无"):
    """
    将列表转换为 Markdown 列表。
    """

    if not items:
        return f"- {empty_text}"

    lines = []

    for item in items:
        lines.append(f"- {item}")

    return "\n".join(lines)


def format_score_table(score_result):
    """
    生成五项评分表格。
    """

    evaluation = score_result.get("evaluation", {})
    scores = evaluation.get("scores", {})

    name_map = {
        "originality": "原创性",
        "novelty": "新颖性",
        "practicality": "可实践性",
        "difficulty": "技术难度",
        "completion": "完成度"
    }

    lines = []
    lines.append("| 评分维度 | 得分 | 参考分 | 评分理由 |")
    lines.append("|---|---:|---:|---|")

    for key, chinese_name in name_map.items():
        item = scores.get(key, {})

        score = item.get("score", 0)
        reference_score = item.get("reference_score", "无")
        max_score = item.get("max_score", 20)
        reason = item.get("reason", "")

        reason = str(reason).replace("\n", " ")

        lines.append(
            f"| {chinese_name} | {score}/{max_score} | {reference_score} | {reason} |"
        )

    return "\n".join(lines)


def format_core_modules(repo_profile):
    """
    生成核心模块说明。
    """

    core_module_details = repo_profile.get("core_module_details", [])

    if not core_module_details:
        core_modules = repo_profile.get("core_modules", [])

        if not core_modules:
            return "暂无核心模块信息。"

        return format_markdown_list(core_modules)

    lines = []
    lines.append("| 模块 | 模块权重 | 完成度 | 综合值 |")
    lines.append("|---|---:|---:|---:|")

    for item in core_module_details:
        lines.append(
            f"| {item.get('module_name')} | "
            f"{item.get('module_weight')} | "
            f"{item.get('completeness')} | "
            f"{item.get('final_score')} |"
        )

    return "\n".join(lines)


def format_module_profiles(repo_profile, max_modules=8):
    """
    生成模块画像表格。
    """

    module_profiles = repo_profile.get("module_profiles", {})

    if not module_profiles:
        return "暂无模块画像信息。"

    modules = list(module_profiles.values())

    modules.sort(
        key=lambda item: item.get("module_weight", 0),
        reverse=True
    )

    lines = []
    lines.append("| 模块 | 函数数量 | 调用边数量 | 内部调用 | 外部调用 | 模块权重 | 文件数量 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for module in modules[:max_modules]:
        lines.append(
            f"| {module.get('module_name')} | "
            f"{module.get('function_count', 0)} | "
            f"{module.get('outgoing_edge_count', 0)} | "
            f"{module.get('internal_edge_count', 0)} | "
            f"{module.get('external_edge_count', 0)} | "
            f"{module.get('module_weight', 0)} | "
            f"{module.get('file_count', 0)} |"
        )

    return "\n".join(lines)


def format_similar_projects(retrieval_result):
    """
    生成相似历史项目检索结果。
    """

    results = retrieval_result.get("results", [])

    if not results:
        return "暂无相似历史项目。"

    lines = []
    lines.append("| 排名 | 历史项目 | 相似度 | 项目类型 | 核心模块 | 函数数量 | 调用边数量 |")
    lines.append("|---:|---|---:|---|---|---:|---:|")

    for index, item in enumerate(results, start=1):
        lines.append(
            f"| {index} | "
            f"{item.get('repo_name')} | "
            f"{item.get('similarity_score')} | "
            f"{item.get('project_type')} | "
            f"{safe_join(item.get('core_modules', []))} | "
            f"{item.get('function_count', 0)} | "
            f"{item.get('edge_count', 0)} |"
        )

    return "\n".join(lines)


def format_retrieval_explanations(retrieval_result):
    """
    生成规则检索相似依据。
    """

    results = retrieval_result.get("results", [])

    if not results:
        return "暂无规则检索解释。"

    lines = []

    for index, item in enumerate(results, start=1):
        lines.append(f"### {index}. {item.get('repo_name')}")
        lines.append("")
        lines.append(f"- 相似度：{item.get('similarity_score')}")
        lines.append(f"- 项目类型：{item.get('project_type')}")
        lines.append("- 相似依据：")

        explanations = item.get("explanations", [])

        if explanations:
            for explanation in explanations:
                lines.append(f"  - {explanation}")
        else:
            lines.append("  - 暂无详细相似依据。")

        lines.append("")

    return "\n".join(lines)


def format_history_comparisons(comparison_result):
    """
    生成 AI 历史项目对比解释。
    """

    comparisons = comparison_result.get("comparisons", [])

    if not comparisons:
        return "暂无 AI 历史项目对比结果。"

    lines = []

    for index, item in enumerate(comparisons, start=1):
        lines.append(f"### {index}. 与历史项目 {item.get('history_repo_name')} 的对比")
        lines.append("")
        lines.append(f"- 相似度：{item.get('similarity_score')}")
        lines.append(f"- 对比置信度：{item.get('comparison_confidence')}")
        lines.append(f"- 总结：{item.get('similarity_summary')}")
        lines.append("")

        lines.append("**主要相似点：**")
        lines.append(format_markdown_list(item.get("main_similarities", [])))
        lines.append("")

        lines.append("**主要差异点：**")
        lines.append(format_markdown_list(item.get("main_differences", [])))
        lines.append("")

        lines.append("**目标项目优势：**")
        lines.append(format_markdown_list(item.get("target_advantages", [])))
        lines.append("")

        lines.append("**目标项目不足：**")
        lines.append(format_markdown_list(item.get("target_weaknesses", [])))
        lines.append("")

        lines.append("**可借鉴设计：**")
        lines.append(format_markdown_list(item.get("borrowable_designs", [])))
        lines.append("")

        uncertainty = item.get("uncertainty", "")

        if uncertainty:
            lines.append(f"**不确定性说明：** {uncertainty}")
            lines.append("")

    return "\n".join(lines)


def format_score_evidence(score_result):
    """
    生成评分证据说明。
    """

    evaluation = score_result.get("evaluation", {})
    scores = evaluation.get("scores", {})

    name_map = {
        "originality": "原创性",
        "novelty": "新颖性",
        "practicality": "可实践性",
        "difficulty": "技术难度",
        "completion": "完成度"
    }

    lines = []

    for key, chinese_name in name_map.items():
        item = scores.get(key, {})

        lines.append(f"### {chinese_name}")
        lines.append("")
        lines.append(f"- 得分：{item.get('score')}/{item.get('max_score')}")
        lines.append(f"- 参考分：{item.get('reference_score')}")
        lines.append(f"- 理由：{item.get('reason')}")
        lines.append("- 证据：")

        evidence = item.get("evidence", [])

        if evidence:
            for evidence_item in evidence:
                lines.append(f"  - {evidence_item}")
        else:
            lines.append("  - 暂无明确证据。")

        lines.append("")

    return "\n".join(lines)


def generate_final_report_full(
    repo_profile_path,
    retrieval_result_path,
    comparison_result_path,
    score_result_path
):
    """
    生成最终 Markdown 报告文本。
    """

    repo_profile = load_json_file(repo_profile_path)
    retrieval_result = load_json_file(retrieval_result_path)
    comparison_result = load_json_file(comparison_result_path)
    score_result = load_json_file(score_result_path)

    repo_name = repo_profile.get("repo_name", "unknown_repo")
    evaluation = score_result.get("evaluation", {})
    reference_scores = score_result.get("reference_scores", {})

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []

    lines.append(f"# OS 项目自动分析与评价报告：{repo_name}")
    lines.append("")
    lines.append(f"> 报告生成时间：{created_at}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 1. 项目概览")
    lines.append("")
    lines.append(f"- 仓库名称：`{repo_name}`")
    lines.append(f"- 项目类型：`{repo_profile.get('project_type')}`")
    lines.append(f"- 主要语言：{safe_join(repo_profile.get('main_languages', []))}")
    lines.append(f"- 函数数量：{repo_profile.get('function_count')}")
    lines.append(f"- 调用边数量：{repo_profile.get('edge_count')}")
    lines.append(f"- 内部调用边数量：{repo_profile.get('internal_edge_count')}")
    lines.append(f"- 外部调用边数量：{repo_profile.get('external_edge_count')}")
    lines.append(f"- 模块数量：{repo_profile.get('module_count')}")
    lines.append(f"- 结构复杂度：{repo_profile.get('structure_complexity')}")
    lines.append("")

    lines.append("## 2. 仓库结构画像")
    lines.append("")
    lines.append("### 2.1 核心模块")
    lines.append("")
    lines.append(format_core_modules(repo_profile))
    lines.append("")

    lines.append("### 2.2 模块画像概览")
    lines.append("")
    lines.append(format_module_profiles(repo_profile, max_modules=8))
    lines.append("")

    lines.append("## 3. 调用图与结构复杂度分析")
    lines.append("")
    lines.append(
        "系统根据函数级理解结果和调用关系构建调用图，并统计内部调用、外部调用和模块分布。"
    )
    lines.append("")
    lines.append(f"- 节点数量：{repo_profile.get('node_count')}")
    lines.append(f"- 调用边数量：{repo_profile.get('edge_count')}")
    lines.append(f"- 内部调用边数量：{repo_profile.get('internal_edge_count')}")
    lines.append(f"- 外部调用边数量：{repo_profile.get('external_edge_count')}")
    lines.append(f"- 结构复杂度：{repo_profile.get('structure_complexity')}")
    lines.append("")

    lines.append("## 4. 相似历史项目检索结果")
    lines.append("")
    lines.append(format_similar_projects(retrieval_result))
    lines.append("")

    lines.append("### 4.1 规则检索相似依据")
    lines.append("")
    lines.append(format_retrieval_explanations(retrieval_result))
    lines.append("")

    lines.append("## 5. AI 历史项目对比解释")
    lines.append("")
    lines.append(format_history_comparisons(comparison_result))
    lines.append("")

    lines.append("## 6. 五项结构化评分")
    lines.append("")
    lines.append(f"- 总分：**{evaluation.get('overall_score')}/100**")
    lines.append(f"- 等级：**{evaluation.get('score_level')}**")
    lines.append(f"- 置信度：**{evaluation.get('confidence')}**")
    lines.append("")
    lines.append(format_score_table(score_result))
    lines.append("")

    lines.append("### 6.1 评分证据")
    lines.append("")
    lines.append(format_score_evidence(score_result))
    lines.append("")

    lines.append("### 6.2 规则参考分")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(reference_scores, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("## 7. 综合评价")
    lines.append("")
    lines.append("### 7.1 主要优势")
    lines.append("")
    lines.append(format_markdown_list(evaluation.get("strengths", [])))
    lines.append("")

    lines.append("### 7.2 主要不足")
    lines.append("")
    lines.append(format_markdown_list(evaluation.get("weaknesses", [])))
    lines.append("")

    lines.append("### 7.3 改进建议")
    lines.append("")
    lines.append(format_markdown_list(evaluation.get("recommendations", [])))
    lines.append("")

    lines.append("## 8. 不确定性说明")
    lines.append("")
    uncertainty = evaluation.get("uncertainty", "")

    if uncertainty:
        lines.append(uncertainty)
    else:
        lines.append(
            "本报告基于静态代码切片、AI 函数理解、调用图统计、历史项目检索与结构化评分自动生成，"
            "可能受到代码块覆盖范围、模块分类准确性、AI 输出稳定性和历史库规模的影响。"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 9. 输入文件")
    lines.append("")
    lines.append(f"- repo_profile_full：`{repo_profile_path}`")
    lines.append(f"- retrieve_full：`{retrieval_result_path}`")
    lines.append(f"- compare_full：`{comparison_result_path}`")
    lines.append(f"- score_full：`{score_result_path}`")
    lines.append("")

    report_text = "\n".join(lines)

    return {
        "repo_name": repo_name,
        "created_at": created_at,
        "report_text": report_text,
        "input_files": {
            "repo_profile": repo_profile_path,
            "retrieval_result": retrieval_result_path,
            "comparison_result": comparison_result_path,
            "score_result": score_result_path
        }
    }


def save_final_report_full(report_result):
    """
    保存最终 Markdown 报告。
    """

    output_dir = "reports"
    ensure_dir(output_dir)

    repo_name = report_result.get("repo_name", "unknown_repo")

    file_path = os.path.join(
        output_dir,
        f"{repo_name}_final_report.md"
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(report_result.get("report_text", ""))

    return file_path


def format_final_report_preview(report_result, save_path):
    """
    生成终端预览。
    """

    output = []

    output.append("最终 Markdown 报告生成完成。")
    output.append("")
    output.append(f"仓库名称：{report_result.get('repo_name')}")
    output.append(f"生成时间：{report_result.get('created_at')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("输入文件：")

    input_files = report_result.get("input_files", {})

    for key, value in input_files.items():
        output.append(f"- {key}: {value}")

    return "\n".join(output)