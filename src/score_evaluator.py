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


def extract_json_from_text(text):
    """
    从 AI 返回文本中提取 JSON。
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


def calculate_average_module_completeness(module_completeness):
    """
    计算模块平均完成度。
    """

    if not module_completeness:
        return 0.0

    values = []

    for value in module_completeness.values():
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue

    if not values:
        return 0.0

    return round(sum(values) / len(values), 4)


def calculate_rule_based_reference_scores(repo_profile, retrieval_result, comparison_result):
    """
    根据结构化数据生成一个规则参考分。

    这个分数不是最终分数，只作为 AI 评分时的参考依据。
    """

    structure_complexity = repo_profile.get("structure_complexity", 0)
    module_count = repo_profile.get("module_count", 0)
    function_count = repo_profile.get("function_count", 0)
    edge_count = repo_profile.get("edge_count", 0)
    core_modules = repo_profile.get("core_modules", [])
    module_completeness = repo_profile.get("module_completeness", {})

    average_completeness = calculate_average_module_completeness(
        module_completeness
    )

    retrieval_results = retrieval_result.get("results", [])
    top_similarity = 0.0

    if retrieval_results:
        top_similarity = retrieval_results[0].get("similarity_score", 0) or 0.0

    comparisons = comparison_result.get("comparisons", [])

    weakness_count = 0
    advantage_count = 0

    for item in comparisons:
        weakness_count += len(item.get("target_weaknesses", []))
        advantage_count += len(item.get("target_advantages", []))

    completion_score = 0

    if average_completeness >= 0.75:
        completion_score += 12
    elif average_completeness >= 0.55:
        completion_score += 9
    elif average_completeness >= 0.35:
        completion_score += 6
    else:
        completion_score += 3

    if module_count >= 6:
        completion_score += 4
    elif module_count >= 4:
        completion_score += 3
    elif module_count >= 2:
        completion_score += 2

    if function_count >= 100:
        completion_score += 4
    elif function_count >= 50:
        completion_score += 3
    elif function_count >= 20:
        completion_score += 2

    completion_score = min(completion_score, 20)

    difficulty_score = 0

    if structure_complexity >= 0.75:
        difficulty_score += 10
    elif structure_complexity >= 0.55:
        difficulty_score += 8
    elif structure_complexity >= 0.35:
        difficulty_score += 5
    else:
        difficulty_score += 3

    if edge_count >= 300:
        difficulty_score += 5
    elif edge_count >= 150:
        difficulty_score += 4
    elif edge_count >= 50:
        difficulty_score += 2

    if len(core_modules) >= 5:
        difficulty_score += 5
    elif len(core_modules) >= 3:
        difficulty_score += 3
    elif len(core_modules) >= 1:
        difficulty_score += 1

    difficulty_score = min(difficulty_score, 20)

    practicality_score = 8

    if completion_score >= 15:
        practicality_score += 5
    elif completion_score >= 10:
        practicality_score += 3

    if "filesystem" in core_modules:
        practicality_score += 2

    if "driver" in core_modules:
        practicality_score += 2

    if "syscall" in core_modules:
        practicality_score += 2

    if weakness_count >= 6:
        practicality_score -= 3
    elif weakness_count >= 3:
        practicality_score -= 1

    practicality_score = max(0, min(practicality_score, 20))

    novelty_score = 10

    if top_similarity >= 0.85:
        novelty_score -= 4
    elif top_similarity >= 0.70:
        novelty_score -= 2
    elif top_similarity <= 0.45:
        novelty_score += 3

    if advantage_count >= 3:
        novelty_score += 3
    elif advantage_count >= 1:
        novelty_score += 1

    novelty_score = max(0, min(novelty_score, 20))

    originality_score = 10

    if top_similarity >= 0.85:
        originality_score -= 5
    elif top_similarity >= 0.70:
        originality_score -= 3
    elif top_similarity <= 0.45:
        originality_score += 3

    if advantage_count >= 3:
        originality_score += 3
    elif advantage_count >= 1:
        originality_score += 1

    originality_score = max(0, min(originality_score, 20))

    return {
        "originality": originality_score,
        "novelty": novelty_score,
        "practicality": practicality_score,
        "difficulty": difficulty_score,
        "completion": completion_score,
        "reference_factors": {
            "average_module_completeness": average_completeness,
            "structure_complexity": structure_complexity,
            "module_count": module_count,
            "function_count": function_count,
            "edge_count": edge_count,
            "top_similarity": top_similarity,
            "advantage_count": advantage_count,
            "weakness_count": weakness_count
        }
    }


def build_score_prompt(repo_profile, retrieval_result, comparison_result, reference_scores):
    """
    构造评分 Prompt。
    """

    compact_repo_profile = {
        "repo_name": repo_profile.get("repo_name"),
        "project_type": repo_profile.get("project_type"),
        "main_languages": repo_profile.get("main_languages", []),
        "function_count": repo_profile.get("function_count"),
        "edge_count": repo_profile.get("edge_count"),
        "internal_edge_count": repo_profile.get("internal_edge_count"),
        "external_edge_count": repo_profile.get("external_edge_count"),
        "module_count": repo_profile.get("module_count"),
        "core_modules": repo_profile.get("core_modules", []),
        "module_completeness": repo_profile.get("module_completeness", {}),
        "structure_complexity": repo_profile.get("structure_complexity")
    }

    compact_retrieval = {
        "target_repo": retrieval_result.get("target_repo"),
        "candidate_count": retrieval_result.get("candidate_count"),
        "results": retrieval_result.get("results", [])[:5]
    }

    compact_comparison = {
        "target_repo": comparison_result.get("target_repo"),
        "comparison_count": comparison_result.get("comparison_count"),
        "comparisons": comparison_result.get("comparisons", [])
    }

    prompt = f"""
你是一个操作系统内核比赛作品评审助手。现在需要根据结构化分析结果，对目标 OS 仓库进行评分。

请注意：
1. 评分必须基于给定数据，不要凭空编造。
2. 每项满分 20 分，总分 100 分。
3. 如果数据不足，请降低置信度，并在 uncertainty 中说明。
4. 输出必须是严格 JSON，不要输出 Markdown，不要添加代码块标记。

【目标仓库画像 repo_profile_full】
{json.dumps(compact_repo_profile, ensure_ascii=False, indent=2)}

【相似历史项目检索结果 retrieve_full】
{json.dumps(compact_retrieval, ensure_ascii=False, indent=2)}

【AI 历史项目对比结果 compare_full】
{json.dumps(compact_comparison, ensure_ascii=False, indent=2)}

【规则参考分（评分必须围绕它波动，不可偏离过大）】

originality: {reference_scores["originality"]}
novelty: {reference_scores["novelty"]}
practicality: {reference_scores["practicality"]}
difficulty: {reference_scores["difficulty"]}
completion: {reference_scores["completion"]}

评分约束规则（非常重要）

1. 每个维度最终评分必须以“规则参考分”为中心进行调整
2. 单项评分与规则参考分的偏差原则上不得超过 ±3 分
3. 只有在 evidence 明确支持的情况下才允许超过该范围
4. 如果没有明确证据，必须保持接近规则参考分
5. 不允许凭主观印象进行大幅度调整


请将规则参考分填入每个评分项的 reference_score 字段。
每个维度最终 score 应以 reference_score 为基准进行微调，除非 evidence 明确支持，否则 score 与 reference_score 的偏差不得超过 3 分。
请按照下面格式输出 JSON：

{{
  "repo_name": "目标仓库名称",
  "overall_score": 0,
  "score_level": "excellent / good / medium / weak",
  "scores": {{
    "originality": {{
      "score": 0,
      "reference_score": {reference_scores["originality"]},
      "max_score": 20,
      "reason": "原创性评分理由",
      "evidence": ["依据1", "依据2"]
    }},
    "novelty": {{
      "score": 0,
      "reference_score": {reference_scores["originality"]},
      "max_score": 20,
      "reason": "新颖性评分理由",
      "evidence": ["依据1", "依据2"]
    }},
    "practicality": {{
      "score": 0,
      "reference_score": {reference_scores["originality"]},
      "max_score": 20,
      "reason": "可实践性评分理由",
      "evidence": ["依据1", "依据2"]
    }},
    "difficulty": {{
      "score": 0,
      "reference_score": {reference_scores["originality"]},
      "max_score": 20,
      "reason": "技术难度评分理由",
      "evidence": ["依据1", "依据2"]
    }},
    "completion": {{
      "score": 0,
      "reference_score": {reference_scores["originality"]},
      "max_score": 20,
      "reason": "完成度评分理由",
      "evidence": ["依据1", "依据2"]
    }}
  }},
  "strengths": [
    "主要优势1",
    "主要优势2"
  ],
  "weaknesses": [
    "主要不足1",
    "主要不足2"
  ],
  "recommendations": [
    "改进建议1",
    "改进建议2"
  ],
  "confidence": "high / medium / low",
  "uncertainty": "本次评分的不确定性说明"
}}


"""

    return prompt


def normalize_score_item(score_item, reference_score=None):
    """
    规范化单项评分。

    reference_score:
    - 规则参考分
    - 用于限制 AI 评分不要偏离太远
    """

    if not isinstance(score_item, dict):
        score_item = {}

    try:
        score = float(score_item.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    if reference_score is not None:
        try:
            reference_score = float(reference_score)
            score = clamp_score_with_reference(
                score=score,
                reference=reference_score,
                max_deviation=3
            )
        except (TypeError, ValueError):
            reference_score = None

    score = max(0, min(score, 20))

    result = {
        "score": round(score, 2),
        "reference_score": reference_score,
        "max_score": 20,
        "reason": score_item.get("reason", ""),
        "evidence": score_item.get("evidence", [])
    }

    return result

def clamp_score_with_reference(score, reference, max_deviation=3):
    lower = reference - max_deviation
    upper = reference + max_deviation
    return max(lower, min(upper, score))

def normalize_score_result(score_result, repo_name, reference_scores=None):
    """
    规范化 AI 评分结果，防止字段缺失。
    """

    if reference_scores is None:
        reference_scores = {}

    scores = score_result.get("scores", {})

    normalized_scores = {
        "originality": normalize_score_item(
            scores.get("originality", {}),
            reference_scores.get("originality")
        ),
        "novelty": normalize_score_item(
            scores.get("novelty", {}),
            reference_scores.get("novelty")
        ),
        "practicality": normalize_score_item(
            scores.get("practicality", {}),
            reference_scores.get("practicality")
        ),
        "difficulty": normalize_score_item(
            scores.get("difficulty", {}),
            reference_scores.get("difficulty")
        ),
        "completion": normalize_score_item(
            scores.get("completion", {}),
            reference_scores.get("completion")
        )
    }

    overall_score = 0

    for item in normalized_scores.values():
        overall_score += item.get("score", 0)

    overall_score = round(overall_score, 2)

    if overall_score >= 85:
        score_level = "excellent"
    elif overall_score >= 70:
        score_level = "good"
    elif overall_score >= 55:
        score_level = "medium"
    else:
        score_level = "weak"

    return {
        "repo_name": score_result.get("repo_name", repo_name),
        "overall_score": overall_score,
        "score_level": score_result.get("score_level", score_level),
        "scores": normalized_scores,
        "strengths": score_result.get("strengths", []),
        "weaknesses": score_result.get("weaknesses", []),
        "recommendations": score_result.get("recommendations", []),
        "confidence": score_result.get("confidence", "medium"),
        "uncertainty": score_result.get("uncertainty", "")
    }


def build_fallback_score(repo_profile, reference_scores, error_message):
    """
    AI 评分失败时，使用规则参考分生成兜底评分。
    """

    repo_name = repo_profile.get("repo_name", "unknown_repo")

    scores = {}

    for key in [
        "originality",
        "novelty",
        "practicality",
        "difficulty",
        "completion"
    ]:
        scores[key] = {
            "score": reference_scores.get(key, 0),
            "reference_score": reference_scores.get(key, 0),
            "max_score": 20,
            "reason": "AI 评分失败，当前分数由规则参考分生成。",
            "evidence": [
                "基于 repo_profile_full、retrieve_full 和 compare_full 中的结构化字段估算。"
            ]
        }

    overall_score = sum(item.get("score", 0) for item in scores.values())

    if overall_score >= 85:
        score_level = "excellent"
    elif overall_score >= 70:
        score_level = "good"
    elif overall_score >= 55:
        score_level = "medium"
    else:
        score_level = "weak"

    return {
        "repo_name": repo_name,
        "overall_score": round(overall_score, 2),
        "score_level": score_level,
        "scores": scores,
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
        "confidence": "low",
        "uncertainty": f"AI 评分失败，已使用规则分兜底。错误信息：{error_message}"
    }


def evaluate_project_score_full(
    repo_profile_path,
    retrieval_result_path,
    comparison_result_path,
    ask_ai_once
):
    """
    生成 full 版本结构化评分。
    """

    repo_profile = load_json_file(repo_profile_path)
    retrieval_result = load_json_file(retrieval_result_path)
    comparison_result = load_json_file(comparison_result_path)

    repo_name = repo_profile.get("repo_name", "unknown_repo")

    reference_scores = calculate_rule_based_reference_scores(
        repo_profile=repo_profile,
        retrieval_result=retrieval_result,
        comparison_result=comparison_result
    )

    prompt = build_score_prompt(
        repo_profile=repo_profile,
        retrieval_result=retrieval_result,
        comparison_result=comparison_result,
        reference_scores=reference_scores
    )

    ai_reply = ask_ai_once(prompt)

    try:
        score_result = extract_json_from_text(ai_reply)
        normalized_result = normalize_score_result(
            score_result=score_result,
            repo_name=repo_name,
            reference_scores=reference_scores
        )

    except Exception as error:
        normalized_result = build_fallback_score(
            repo_profile=repo_profile,
            reference_scores=reference_scores,
            error_message=str(error)
        )

    final_result = {
        "repo_name": repo_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_type": "full",
        "inputs": {
            "repo_profile": repo_profile_path,
            "retrieval_result": retrieval_result_path,
            "comparison_result": comparison_result_path
        },
        "reference_scores": reference_scores,
        "evaluation": normalized_result
    }

    return final_result


def save_score_result_full(score_result):
    """
    保存 full 结构化评分结果。
    """

    output_dir = "evaluation"
    ensure_dir(output_dir)

    repo_name = score_result.get("repo_name", "unknown_repo")
    file_name = f"{repo_name}_score_full.json"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(score_result, file, ensure_ascii=False, indent=2)

    return file_path


def format_score_result_full_preview(score_result, save_path):
    """
    生成评分结果终端预览。
    """

    output = []

    evaluation = score_result.get("evaluation", {})

    output.append("full 结构化评分完成。")
    output.append("")
    output.append(f"仓库名称：{score_result.get('repo_name')}")
    output.append(f"总分：{evaluation.get('overall_score')}/100")
    output.append(f"等级：{evaluation.get('score_level')}")
    output.append(f"置信度：{evaluation.get('confidence')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("五项评分：")

    scores = evaluation.get("scores", {})

    name_map = {
        "originality": "原创性",
        "novelty": "新颖性",
        "practicality": "可实践性",
        "difficulty": "技术难度",
        "completion": "完成度"
    }

    for key, chinese_name in name_map.items():
        item = scores.get(key, {})
        output.append(
            f"- {chinese_name}: {item.get('score')}/{item.get('max_score')}"
        )
        output.append(f"  理由：{item.get('reason')}")

    output.append("")
    output.append("主要优势：")

    for item in evaluation.get("strengths", []):
        output.append(f"- {item}")

    output.append("")
    output.append("主要不足：")

    for item in evaluation.get("weaknesses", []):
        output.append(f"- {item}")

    return "\n".join(output)