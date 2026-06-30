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
    读取 JSON 文件，并检查用户是否误输入文件夹路径。
    """

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


def get_score_level_comment(overall_score):
    """
    根据总分生成简要等级评价。
    """

    score = safe_number(overall_score)

    if score >= 85:
        return "项目整体表现优秀，结构完整度和技术实现水平较高，具备较强的综合竞争力。"

    if score >= 70:
        return "项目整体表现良好，已经具备较完整的系统结构和一定技术亮点，但仍有进一步优化空间。"

    if score >= 50:
        return "项目整体处于中等水平，已经形成基本结构，但在模块完整性、工程实现或创新性方面仍存在明显不足。"

    return "项目目前仍偏向原型阶段，核心结构和功能完整性不足，后续需要重点补强基础模块和工程实现。"


def get_structure_comment(repo_profile):
    """
    根据仓库画像生成结构成熟度评价。
    """

    function_count = safe_number(repo_profile.get("function_count"))
    edge_count = safe_number(repo_profile.get("edge_count"))
    module_count = safe_number(repo_profile.get("module_count"))
    structure_complexity = safe_number(repo_profile.get("structure_complexity"))

    if function_count >= 100 and edge_count >= 300 and module_count >= 5:
        return "从函数数量、调用边数量和模块覆盖情况看，该项目已经具备较明显的系统级结构。"

    if function_count >= 40 and module_count >= 3:
        return "从结构指标看，该项目已经形成一定规模的模块组织，但系统复杂度和模块覆盖仍有提升空间。"

    if function_count > 0:
        return "从结构指标看，该项目已经具备初步代码结构，但整体规模和模块覆盖仍相对有限。"

    return "当前仓库画像中的函数和调用关系信息较少，系统结构成熟度判断存在较大不确定性。"


def get_top_similar_project(retrieval_result):
    """
    获取相似度最高的历史项目。
    """

    results = retrieval_result.get("results", [])

    if not results:
        return None

    return results[0]


def build_executive_summary(repo_profile, retrieval_result, score_result):
    """
    生成报告摘要。
    """

    evaluation = score_result.get("evaluation", {})
    overall_score = evaluation.get("overall_score")
    score_level = evaluation.get("score_level", "unknown")

    repo_name = repo_profile.get("repo_name", "unknown_repo")
    project_type = repo_profile.get("project_type", "unknown")
    main_languages = safe_join(repo_profile.get("main_languages", []))
    core_modules = safe_join(repo_profile.get("core_modules", []))

    top_project = get_top_similar_project(retrieval_result)

    lines = []

    lines.append("本报告对目标 OS 项目进行自动化结构分析、历史项目对比和五维评分。")
    lines.append("")
    lines.append(f"- 目标仓库：`{repo_name}`")
    lines.append(f"- 项目类型：`{project_type}`")
    lines.append(f"- 主要语言：{main_languages}")
    lines.append(f"- 核心模块：{core_modules}")
    lines.append(f"- 综合评分：**{overall_score}/100**")
    lines.append(f"- 评分等级：**{score_level}**")

    if top_project:
        lines.append(
            f"- 最相似历史项目：`{top_project.get('repo_name')}`，"
            f"相似度为 `{top_project.get('similarity_score')}`"
        )
    else:
        lines.append("- 最相似历史项目：暂无可用历史项目检索结果")

    lines.append("")
    lines.append(get_score_level_comment(overall_score))
    lines.append("")
    lines.append(get_structure_comment(repo_profile))

    return "\n".join(lines)


def build_key_findings(repo_profile, retrieval_result, score_result):
    """
    生成关键发现。
    """

    evaluation = score_result.get("evaluation", {})
    scores = evaluation.get("scores", {})

    lines = []

    function_count = repo_profile.get("function_count")
    edge_count = repo_profile.get("edge_count")
    module_count = repo_profile.get("module_count")
    core_modules = repo_profile.get("core_modules", [])

    lines.append(
        f"该项目共识别出 `{function_count}` 个函数节点、`{edge_count}` 条调用边，"
        f"覆盖 `{module_count}` 个模块。"
    )

    if core_modules:
        lines.append(
            f"核心模块主要集中在：{safe_join(core_modules)}。"
        )

    top_project = get_top_similar_project(retrieval_result)

    if top_project:
        lines.append(
            f"历史检索结果显示，该项目与 `{top_project.get('repo_name')}` "
            f"在项目类型、模块结构或调用图规模上最为接近。"
        )

    lowest_score_name = None
    lowest_score_value = None

    name_map = {
        "originality": "原创性",
        "novelty": "新颖性",
        "practicality": "可实践性",
        "difficulty": "技术难度",
        "completion": "完成度"
    }

    for key, chinese_name in name_map.items():
        score_item = scores.get(key, {})
        score = safe_number(score_item.get("score"))

        if lowest_score_value is None or score < lowest_score_value:
            lowest_score_value = score
            lowest_score_name = chinese_name

    if lowest_score_name is not None:
        lines.append(
            f"五维评分中相对薄弱的维度是：{lowest_score_name}，"
            f"说明后续优化应优先关注该方向。"
        )

    return format_markdown_list(lines)


def build_review_conclusion(repo_profile, score_result):
    """
    生成评审式结论。
    """

    evaluation = score_result.get("evaluation", {})
    overall_score = safe_number(evaluation.get("overall_score"))
    score_level = evaluation.get("score_level", "unknown")

    repo_name = repo_profile.get("repo_name", "unknown_repo")
    project_type = repo_profile.get("project_type", "unknown")

    if overall_score >= 85:
        conclusion = (
            "该项目已经具备较高完成度和较强工程价值，核心模块与系统结构较完整，"
            "可以作为较高质量 OS 项目继续深入分析。"
        )
    elif overall_score >= 70:
        conclusion = (
            "该项目已经具备较完整的操作系统项目结构，能够体现一定的系统设计能力，"
            "但仍需要进一步增强特色模块和工程完整性。"
        )
    elif overall_score >= 50:
        conclusion = (
            "该项目已经具备基本 OS 项目雏形，但当前更适合作为阶段性作品，"
            "后续应重点提升核心模块覆盖、代码组织质量和可运行验证能力。"
        )
    else:
        conclusion = (
            "该项目目前仍处于较早期阶段，已有结构和实现不足以支撑较完整的系统评价，"
            "建议优先补齐基础模块和工程运行链路。"
        )

    return (
        f"综合来看，`{repo_name}` 属于 `{project_type}` 类型项目，"
        f"当前评分等级为 `{score_level}`，总分为 `{overall_score}/100`。"
        f"{conclusion}"
    )


def build_showcase_sentence(repo_profile, score_result):
    """
    生成适合展示的一句话总结。
    """

    evaluation = score_result.get("evaluation", {})
    repo_name = repo_profile.get("repo_name", "unknown_repo")
    overall_score = evaluation.get("overall_score")
    core_modules = safe_join(repo_profile.get("core_modules", []))

    return (
        f"`{repo_name}` 是一个以 {core_modules} 为主要结构特征的 OS 项目，"
        f"系统自动分析后给出的综合评分为 {overall_score}/100，"
        f"说明其已经具备一定代码结构和模块组织基础，但仍需要结合评分短板继续优化。"
    )

def find_description_report_path(repo_name):
    """
    查找旧版仓库描述报告 reports/{repo_name}_description.md。
    """

    path = os.path.join("reports", f"{repo_name}_description.md")

    if os.path.exists(path):
        return path

    return None


def read_description_report_for_final(repo_name, max_chars=12000):
    """
    读取旧版完整仓库描述报告，用于插入最终报告。
    """

    path = find_description_report_path(repo_name)

    if not path:
        return ""

    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception:
        return ""

    content = content.strip()

    if content.startswith("#"):
        lines = content.splitlines()
        if lines and lines[0].startswith("#"):
            content = "\n".join(lines[1:]).strip()

    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n……旧版仓库描述报告内容较长，后续部分已截断。"

    return content


def build_deep_project_description_section(repo_name):
    """
    构建 final_report 中的深度项目综述栏目。
    """

    content = read_description_report_for_final(repo_name)

    if not content:
        return (
            "当前未找到旧版仓库描述报告。"
            "如果需要完整项目综述，请先在导入仓库时生成 "
            f"`reports/{repo_name}_description.md`。"
        )

    return content

def _parse_ai_json_object(ai_text):
    """
    从 AI 输出中提取 JSON 对象。
    """

    if not ai_text:
        return None

    text = str(ai_text).strip()

    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()

    left = text.find("{")
    right = text.rfind("}")

    if left >= 0 and right > left:
        text = text[left:right + 1]

    try:
        return json.loads(text)
    except Exception:
        return None


def _safe_join(items, default="暂无"):
    """
    安全拼接列表。
    """

    if not items:
        return default

    if isinstance(items, dict):
        items = list(items.keys())

    if isinstance(items, list):
        return "、".join(str(x) for x in items[:10])

    return str(items)


def _get_evaluation(score_result):
    """
    兼容不同评分 JSON 结构。
    """

    if not isinstance(score_result, dict):
        return {}

    return (
        score_result.get("evaluation")
        or score_result.get("scores")
        or score_result
        or {}
    )


def _get_top_similar_project(retrieval_result):
    """
    提取最相似历史项目。
    """

    if not isinstance(retrieval_result, dict):
        return None

    candidates = (
        retrieval_result.get("top_k")
        or retrieval_result.get("similar_projects")
        or retrieval_result.get("results")
        or retrieval_result.get("retrieval_results")
        or []
    )

    if isinstance(candidates, list) and candidates:
        return candidates[0]

    return None


def _fallback_project_overview(repo_profile, retrieval_result, comparison_result, score_result):
    """
    AI 生成失败时，使用规则生成一个不空的项目综述。
    """

    repo_name = repo_profile.get("repo_name", "unknown_repo")

    main_languages = (
        repo_profile.get("main_languages")
        or repo_profile.get("languages")
        or repo_profile.get("language")
        or []
    )

    core_modules = (
        repo_profile.get("core_modules")
        or repo_profile.get("detected_modules")
        or []
    )

    function_count = repo_profile.get("function_count", "暂无")
    edge_count = repo_profile.get("edge_count") or repo_profile.get("call_edges") or "暂无"
    module_count = repo_profile.get("module_count", "暂无")
    structure_complexity = repo_profile.get("structure_complexity", "暂无")

    language_text = _safe_join(main_languages, default="未知语言")
    module_text = _safe_join(core_modules, default="暂未识别出明确核心模块")

    evaluation = _get_evaluation(score_result)
    overall_score = evaluation.get("overall_score") or evaluation.get("final_score") or "暂无"
    score_level = evaluation.get("score_level") or evaluation.get("level") or "暂无"

    top_project = _get_top_similar_project(retrieval_result)

    if top_project:
        similar_repo_name = (
            top_project.get("repo_name")
            or top_project.get("project_name")
            or top_project.get("name")
            or "未知历史项目"
        )
        similar_score = (
            top_project.get("hybrid_score")
            or top_project.get("similarity_score")
            or top_project.get("score")
            or "暂无"
        )
        similar_text = f"历史检索结果显示，该项目与 `{similar_repo_name}` 较为接近，相似度为 `{similar_score}`。"
    else:
        similar_text = "当前没有可用的相似历史项目结果。"

    one_sentence = (
        f"`{repo_name}` 是一个主要使用 {language_text} 实现的操作系统内核项目，"
        f"核心结构集中在 {module_text} 等模块。"
    )

    project_overview = (
        f"从当前静态分析结果看，`{repo_name}` 主要使用 {language_text} 实现，"
        f"项目围绕 {module_text} 等操作系统核心模块展开。"
        f"系统识别到该仓库包含 `{function_count}` 个函数节点、`{edge_count}` 条调用边，"
        f"覆盖 `{module_count}` 个模块，结构复杂度为 `{structure_complexity}`。"
        f"这些信息说明该仓库已经形成了一定的源码规模和模块化组织。"
        f"{similar_text}"
    )

    maturity = (
        f"结合当前评分结果，该项目综合评分为 `{overall_score}`，等级为 `{score_level}`。"
        f"该判断主要基于源码结构画像、核心模块覆盖、历史相似项目检索和五维评分结果。"
    )

    strengths = (
        evaluation.get("strengths")
        or evaluation.get("advantages")
        or []
    )

    risks = (
        evaluation.get("weaknesses")
        or evaluation.get("risks")
        or evaluation.get("limitations")
        or []
    )

    return {
        "project_positioning": "操作系统内核项目",
        "one_sentence_summary": one_sentence,
        "project_overview": project_overview,
        "core_implementation_summary": (
            f"当前识别出的核心模块包括：{module_text}。"
            "这些模块构成了仓库的主要 OS 实现方向。"
        ),
        "maturity_judgement": maturity,
        "main_strengths": strengths[:5] if isinstance(strengths, list) else [],
        "main_risks": risks[:5] if isinstance(risks, list) else [],
        "confidence": evaluation.get("confidence", "medium")
    }


def build_project_overview_prompt(repo_profile, retrieval_result, comparison_result, score_result):
    """
    构造项目分析综述 prompt。
    """

    repo_name = repo_profile.get("repo_name", "unknown_repo")

    main_languages = (
        repo_profile.get("main_languages")
        or repo_profile.get("languages")
        or repo_profile.get("language")
        or []
    )

    core_modules = (
        repo_profile.get("core_modules")
        or repo_profile.get("detected_modules")
        or []
    )

    evaluation = _get_evaluation(score_result)
    top_project = _get_top_similar_project(retrieval_result)

    prompt = f"""
你是操作系统内核赛道作品评审助手。现在要为一个 OS 仓库生成最终报告开头的“项目分析综述”。

目标：
让评委先明白：这个仓库是什么、想实现什么、主要做了哪些 OS 模块、实现成熟度如何、优势和风险是什么。

要求：
1. 必须基于给出的结构画像、评分和历史对比信息。
2. 不要空泛，不要只写“具有一定复杂度”。
3. 不要编造没有证据的功能。
4. 如果证据不足，要明确说“当前证据不足”。
5. 输出必须是合法 JSON，不要 Markdown，不要解释。

JSON 格式：
{{
  "project_positioning": "项目定位，例如：基于 Rust 的 RISC-V 教学型微型操作系统",
  "one_sentence_summary": "一句话说明这个仓库是什么",
  "project_overview": "200到400字项目综述，说明它想实现什么、主要模块、技术路线和整体特点",
  "core_implementation_summary": "说明核心模块实现情况和可能的执行链路",
  "maturity_judgement": "说明实现成熟度、完成度和评分位置",
  "main_strengths": ["优势1", "优势2", "优势3"],
  "main_risks": ["风险1", "风险2", "风险3"],
  "confidence": "high/medium/low"
}}

仓库名称：
{repo_name}

主要语言：
{main_languages}

核心模块：
{core_modules}

结构统计：
{{
  "function_count": {repo_profile.get("function_count")},
  "edge_count": {repo_profile.get("edge_count") or repo_profile.get("call_edges")},
  "module_count": {repo_profile.get("module_count")},
  "structure_complexity": {repo_profile.get("structure_complexity")}
}}

评分结果：
{json.dumps(evaluation, ensure_ascii=False, indent=2)}

最相似历史项目：
{json.dumps(top_project, ensure_ascii=False, indent=2)}
"""

    return prompt


def build_project_analysis_overview(
    repo_profile,
    retrieval_result,
    comparison_result,
    score_result,
    ask_ai_once=None
):
    """
    生成最终报告中的“项目分析综述”栏目。
    """

    overview = None

    if ask_ai_once is not None:
        try:
            prompt = build_project_overview_prompt(
                repo_profile=repo_profile,
                retrieval_result=retrieval_result,
                comparison_result=comparison_result,
                score_result=score_result
            )

            ai_text = ask_ai_once(prompt)
            overview = _parse_ai_json_object(ai_text)
        except Exception:
            overview = None

    if not isinstance(overview, dict):
        overview = _fallback_project_overview(
            repo_profile=repo_profile,
            retrieval_result=retrieval_result,
            comparison_result=comparison_result,
            score_result=score_result
        )

    lines = []

    lines.append(f"**项目定位：** {overview.get('project_positioning', '暂无明确项目定位')}")
    lines.append("")
    lines.append(f"**一句话综述：** {overview.get('one_sentence_summary', '暂无')}")
    lines.append("")
    lines.append(overview.get("project_overview", "暂无项目综述。"))
    lines.append("")
    lines.append("### 1.1 核心实现判断")
    lines.append("")
    lines.append(overview.get("core_implementation_summary", "暂无核心实现判断。"))
    lines.append("")
    lines.append("### 1.2 实现成熟度判断")
    lines.append("")
    lines.append(overview.get("maturity_judgement", "暂无实现成熟度判断。"))
    lines.append("")
    lines.append("### 1.3 主要优势")
    lines.append("")

    strengths = overview.get("main_strengths", [])
    if strengths:
        for item in strengths:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无明确优势。")

    lines.append("")
    lines.append("### 1.4 主要风险")
    lines.append("")

    risks = overview.get("main_risks", [])
    if risks:
        for item in risks:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无明确风险。")

    lines.append("")
    lines.append(f"**综述置信度：** {overview.get('confidence', 'medium')}")

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


def generate_final_report_full(repo_profile_path,retrieval_result_path,comparison_result_path,score_result_path,ask_ai_once=None):
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

    lines.append("## 0. 报告摘要")
    lines.append("")
    lines.append(build_executive_summary(
        repo_profile=repo_profile,
        retrieval_result=retrieval_result,
        score_result=score_result
    ))
    lines.append("")

    lines.append("### 0.1 关键发现")
    lines.append("")
    lines.append(build_key_findings(
        repo_profile=repo_profile,
        retrieval_result=retrieval_result,
        score_result=score_result
    ))
    lines.append("")

    lines.append("### 0.2 评审结论")
    lines.append("")
    lines.append(build_review_conclusion(
        repo_profile=repo_profile,
        score_result=score_result
    ))
    lines.append("")

    lines.append("### 0.3 展示版一句话总结")
    lines.append("")
    lines.append(build_showcase_sentence(
        repo_profile=repo_profile,
        score_result=score_result
    ))
    lines.append("")

    lines.append("## 1. 项目深度综述")
    lines.append("")
    lines.append(build_deep_project_description_section(repo_name))
    lines.append("")

    lines.append("## 2. 项目概览")
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

    lines.append("## 3. 仓库结构画像")
    lines.append("")
    lines.append("### 3.1 核心模块")
    lines.append("")
    lines.append(format_core_modules(repo_profile))
    lines.append("")

    lines.append("### 3.2 模块画像概览")
    lines.append("")
    lines.append(format_module_profiles(repo_profile, max_modules=8))
    lines.append("")

    lines.append("## 4. 调用图与结构复杂度分析")
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

    lines.append("## 5. 相似历史项目检索结果")
    lines.append("")
    lines.append(format_similar_projects(retrieval_result))
    lines.append("")

    lines.append("### 5.1 规则检索相似依据")
    lines.append("")
    lines.append(format_retrieval_explanations(retrieval_result))
    lines.append("")

    lines.append("## 6. AI 历史项目对比解释")
    lines.append("")
    lines.append(format_history_comparisons(comparison_result))
    lines.append("")

    lines.append("## 7. 五项结构化评分")
    lines.append("")
    lines.append(f"- 总分：**{evaluation.get('overall_score')}/100**")
    lines.append(f"- 等级：**{evaluation.get('score_level')}**")
    lines.append(f"- 置信度：**{evaluation.get('confidence')}**")
    lines.append("")
    lines.append(format_score_table(score_result))
    lines.append("")

    lines.append("### 7.1 评分证据")
    lines.append("")
    lines.append(format_score_evidence(score_result))
    lines.append("")

    lines.append("### 7.2 规则参考分")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(reference_scores, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("## 8. 综合评价")
    lines.append("")
    lines.append("### 8.1 主要优势")
    lines.append("")
    lines.append(format_markdown_list(evaluation.get("strengths", [])))
    lines.append("")

    lines.append("### 8.2 主要不足")
    lines.append("")
    lines.append(format_markdown_list(evaluation.get("weaknesses", [])))
    lines.append("")

    lines.append("### 8.3 改进建议")
    lines.append("")
    lines.append(format_markdown_list(evaluation.get("recommendations", [])))
    lines.append("")

    lines.append("## 9. 不确定性说明")
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
    lines.append("## 10. 输入文件")
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