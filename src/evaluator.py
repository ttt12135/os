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


def read_profile_by_path(profile_path):
    """
    根据 repo_profile 路径读取完整仓库画像。
    """
    if not profile_path:
        return None

    if not os.path.exists(profile_path):
        return None

    return load_json_file(profile_path)


def collect_history_profiles_from_retrieval(retrieval_result):
    """
    根据 v1.8 的检索结果，读取相似历史作品的完整 repo_profile。
    """

    results = retrieval_result.get("results", [])

    history_profiles = []

    for item in results:
        source_profile = item.get("source_profile", "")

        profile = read_profile_by_path(source_profile)

        if profile is None:
            continue

        history_profiles.append(
            {
                "retrieval_info": item,
                "profile": profile
            }
        )

    return history_profiles


def build_profile_brief(profile):
    """
    把 repo_profile 压缩成适合放进 Prompt 的摘要文本。
    """

    repo_name = profile.get("repo_name", "unknown_repo")

    function_summary = profile.get("function_analysis_summary", {})
    call_graph_summary = profile.get("call_graph_summary", {})
    module_summary = profile.get("module_summary", {})

    module_distribution = function_summary.get("module_distribution", {})
    module_names = module_summary.get("module_names", [])
    modules = module_summary.get("modules", [])

    lines = []

    lines.append(f"仓库名称：{repo_name}")
    lines.append("")
    lines.append("一、函数分析概况：")
    lines.append(f"- 已分析函数数量：{function_summary.get('analysis_count', 0)}")
    lines.append(f"- 函数模块分布：{module_distribution}")
    lines.append("")
    lines.append("二、调用图概况：")
    lines.append(f"- 调用边数量：{call_graph_summary.get('edge_count', 0)}")
    lines.append(f"- 高置信度调用边数量：{call_graph_summary.get('high_confidence_edge_count', 0)}")
    lines.append("")
    lines.append("三、模块概况：")
    lines.append(f"- 模块数量：{module_summary.get('module_count', 0)}")
    lines.append(f"- 模块列表：{', '.join(module_names)}")
    lines.append("")

    lines.append("四、模块总结：")

    for module in modules:
        lines.append(f"模块：{module.get('module_name')}")
        lines.append(f"总体作用：{module.get('module_summary')}")
        lines.append(f"调用流程：{module.get('call_flow_summary')}")
        lines.append(f"不确定性：{module.get('uncertainty')}")
        lines.append("")

    uncertainty = profile.get("uncertainty", [])
    lines.append("五、不确定性：")
    for item in uncertainty:
        lines.append(f"- {item}")

    return "\n".join(lines)


def build_history_profiles_text(history_profiles):
    """
    整理相似历史作品画像，方便放进 Prompt。
    """

    if len(history_profiles) == 0:
        return "没有找到可用于对比的相似历史作品完整画像。"

    sections = []

    for index, item in enumerate(history_profiles, start=1):
        retrieval_info = item.get("retrieval_info", {})
        profile = item.get("profile", {})

        sections.append(f"历史作品 {index}")
        sections.append(f"检索相似度：{retrieval_info.get('similarity_score')}")
        sections.append(f"相似度细节：{retrieval_info.get('score_detail')}")
        sections.append("")
        sections.append(build_profile_brief(profile))
        sections.append("")
        sections.append("-" * 80)

    return "\n".join(sections)


def build_evaluation_prompt(target_profile, history_profiles):
    """
    构造专项对比评分 Prompt。
    """

    target_text = build_profile_brief(target_profile)
    history_text = build_history_profiles_text(history_profiles)

    prompt = f"""
你现在要完成一个“操作系统比赛作品专项对比与评分报告”。

你的任务不是普通聊天，而是像评审助手一样，基于仓库画像、函数理解、调用关系、模块总结等材料，对新提交作品进行综合分析、历史对比和指标评分。

下面是新提交作品的仓库画像摘要：

{target_text}

下面是系统检索出的相似历史作品画像摘要：

{history_text}

请你生成一份完整 Markdown 报告。

报告标题必须是：

# OS 作品专项对比与评分报告

报告必须包含以下部分：

## 一、分析对象说明

说明新提交作品是什么，参与比较的历史作品有哪些。
如果历史作品资料不足，请明确说明。

## 二、新提交作品综合总结

请围绕以下角度总结新作品：

### 1. 背景 Background
根据仓库画像推断该作品所处的项目背景。如果信息不足，明确说明。

### 2. Motivation
分析该作品可能想解决什么需求或痛点。如果证据不足，明确说明。

### 3. 问题 Problem
说明该作品主要面向什么问题。

### 4. 设计 Design
根据模块总结、函数理解和调用关系，概括系统设计。

### 5. 核心实现 Implementation
结合函数理解、模块总结和调用边，说明核心实现。

### 6. 创新点 Innovation
分析作品可能的创新点。不能凭空夸大，必须结合证据。

### 7. 当前完成度 Completeness
根据模块数量、函数分析数量、调用图情况和不确定性，判断当前完成度。

## 三、相似历史作品概览

概括相似历史作品的共同特点，包括模块结构、调用关系、实现复杂度和工程组织方式。

## 四、新作品与历史作品专项对比

请从以下维度进行对比：

### 1. 背景与目标对比
### 2. Motivation 对比
### 3. 问题定义对比
### 4. 系统设计对比
### 5. 核心实现对比
### 6. 函数逻辑与调用关系对比
### 7. 创新点对比
### 8. 工程完成度对比
### 9. 可实践性对比

要求：
- 必须基于当前提供的仓库画像和历史画像；
- 不要编造没有证据的信息；
- 对不确定内容要明确说明。

## 五、指标评分表

请按下面指标评分，总分 100 分。

| 指标 | 满分 | 得分 | 评分理由 |
|---|---:|---:|---|
| 问题价值 | 10 |  |  |
| Motivation 清晰度 | 10 |  |  |
| 原创性 | 15 |  |  |
| 新颖性 | 15 |  |  |
| 设计完整度 | 15 |  |  |
| 技术难度 | 15 |  |  |
| 可实践性 | 10 |  |  |
| 完成度 | 10 |  |  |
| 总分 | 100 |  |  |

评分要求：
1. 分数要谨慎，不要虚高；
2. 每项评分必须给出理由；
3. 理由要尽量结合代码证据、模块总结、调用关系、历史作品对比；
4. 如果证据不足，要在理由中说明；
5. 总分必须等于各项得分之和。

## 六、综合评价

总结新作品目前在历史作品中的大致位置：
1. 优势是什么；
2. 不足是什么；
3. 和相似历史作品相比差异在哪里；
4. 是否具有继续完善价值。

## 七、不确定性与风险

说明本次评价的限制，例如：
1. 当前分析基于静态代码理解；
2. 未实际编译运行；
3. 函数切片和调用关系可能不完整；
4. 历史作品数量有限；
5. AI 函数理解可能存在误差。

## 八、后续改进建议

给出面向参赛作品继续完善的建议。

写作要求：
1. 使用正式 Markdown；
2. 面向评审和项目开发者；
3. 不要空泛夸奖；
4. 评价要有依据；
5. 必须输出完整报告。
"""

    return prompt


def generate_evaluation_report(
    target_profile_path,
    retrieval_result,
    ask_ai_once
):
    """
    根据目标作品 repo_profile 和相似历史作品检索结果，生成专项对比评分报告。
    """

    target_profile = load_json_file(target_profile_path)
    history_profiles = collect_history_profiles_from_retrieval(retrieval_result)

    prompt = build_evaluation_prompt(
        target_profile=target_profile,
        history_profiles=history_profiles
    )

    report_content = ask_ai_once(prompt)

    return target_profile, history_profiles, report_content


def save_evaluation_report(target_profile, report_content):
    """
    保存专项对比评分报告。
    """

    output_dir = "reports"
    ensure_dir(output_dir)

    repo_name = target_profile.get("repo_name", "unknown_repo")

    file_name = f"{repo_name}_evaluation_report.md"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(report_content)

    return file_path


def format_evaluation_preview(target_profile, history_profiles, save_path):
    """
    生成终端显示摘要。
    """

    output = []

    output.append("专项对比评分报告生成完成。")
    output.append("")
    output.append(f"目标作品：{target_profile.get('repo_name')}")
    output.append(f"参与对比的历史作品数量：{len(history_profiles)}")
    output.append(f"报告路径：{save_path}")
    output.append("")
    output.append("参与对比的历史作品：")

    if len(history_profiles) == 0:
        output.append("暂无历史作品参与对比。")
    else:
        for index, item in enumerate(history_profiles, start=1):
            profile = item.get("profile", {})
            retrieval_info = item.get("retrieval_info", {})
            output.append(
                f"{index}. {profile.get('repo_name')} "
                f"(相似度：{retrieval_info.get('similarity_score')})"
            )

    return "\n".join(output)