import os
import json
from datetime import datetime


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """

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


def build_history_comparison_prompt(target_profile, history_profile, retrieval_item):
    """
    构造目标仓库与单个历史仓库的对比 Prompt。
    """

    target_compact = compact_profile_for_prompt(target_profile)
    history_compact = compact_profile_for_prompt(history_profile)

    prompt = f"""
你是一个操作系统内核比赛作品评审助手。现在需要比较一个目标 OS 仓库和一个历史 OS 仓库。

请你根据结构化仓库画像进行对比，不要凭空编造。若信息不足，请明确说明不确定性。

【目标仓库画像】
{json.dumps(target_compact, ensure_ascii=False, indent=2)}

【历史仓库画像】
{json.dumps(history_compact, ensure_ascii=False, indent=2)}

【规则检索得到的相似度信息】
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
    comparison["score_detail"] = retrieval_item.get("score_detail", {})
    comparison["retrieval_explanations"] = retrieval_item.get("explanations", [])

    return comparison


def compare_retrieval_results_with_ai(retrieval_result_path, ask_ai_once):
    """
    对 retrieve_full 得到的 Top-K 相似历史项目进行 AI 对比解释。
    """

    retrieval_result = load_json_file(retrieval_result_path)

    target_profile_path = retrieval_result.get("target_profile")
    target_profile = load_json_file(target_profile_path)

    results = retrieval_result.get("results", [])

    comparisons = []

    for index, item in enumerate(results, start=1):
        source_profile = item.get("source_profile")

        if not source_profile or not os.path.exists(source_profile):
            comparisons.append(
                {
                    "history_repo_name": item.get("repo_name"),
                    "source_profile": source_profile,
                    "similarity_score": item.get("similarity_score"),
                    "similarity_summary": "未能读取历史仓库完整画像，无法进行详细 AI 对比。",
                    "main_similarities": [],
                    "main_differences": [],
                    "target_advantages": [],
                    "target_weaknesses": [],
                    "borrowable_designs": [],
                    "comparison_confidence": "low",
                    "uncertainty": "source_profile 路径不存在或为空。"
                }
            )
            continue

        print(f"正在进行第 {index}/{len(results)} 个历史项目 AI 对比：{item.get('repo_name')}")

        history_profile = load_json_file(source_profile)

        comparison = compare_one_history_project(
            target_profile=target_profile,
            history_profile=history_profile,
            retrieval_item=item,
            ask_ai_once=ask_ai_once
        )

        comparisons.append(comparison)

    comparison_result = {
        "target_repo": retrieval_result.get("target_repo"),
        "target_profile": target_profile_path,
        "retrieval_result": retrieval_result_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comparison_count": len(comparisons),
        "comparisons": comparisons
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
        output.append(f"   置信度：{item.get('comparison_confidence')}")
        output.append(f"   总结：{item.get('similarity_summary')}")
        output.append("   主要相似点：")

        for point in item.get("main_similarities", [])[:3]:
            output.append(f"   - {point}")

        output.append("")

    return "\n".join(output)