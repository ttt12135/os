import os
import json
from datetime import datetime

from src.implementation_quality_evaluator import (
    evaluate_implementation_quality,
    save_implementation_quality_result,
    save_implementation_quality_markdown,
    load_json_file,
    save_json_file,
    save_text_file,
    safe_number,
)


def ensure_dir(directory):
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def infer_repo_name_from_profile_file(file_name):
    suffix = "_repo_profile_full.json"
    if file_name.endswith(suffix):
        return file_name[:-len(suffix)]
    if file_name.endswith(".json"):
        return file_name[:-5]
    return file_name


def find_repo_profile_files(profile_dir):
    if not os.path.exists(profile_dir):
        return []
    files = []
    for file_name in os.listdir(profile_dir):
        if not file_name.endswith("_repo_profile_full.json"):
            continue
        repo_name = infer_repo_name_from_profile_file(file_name)
        if ".json" in repo_name or "call_graph" in repo_name:
            continue
        path = os.path.join(profile_dir, file_name)
        if os.path.isfile(path):
            files.append(path)
    files.sort()
    return files


def calculate_structure_score(repo_profile):
    function_count = safe_number(repo_profile.get("function_count"), 0)
    edge_count = safe_number(repo_profile.get("edge_count"), 0)
    module_count = safe_number(repo_profile.get("module_count"), 0)
    core_modules = repo_profile.get("core_modules", []) or []
    structure_complexity = safe_number(repo_profile.get("structure_complexity"), 0)
    module_completeness = repo_profile.get("module_completeness", {}) or {}

    score = 0.0

    if function_count >= 180:
        score += 5
    elif function_count >= 100:
        score += 4
    elif function_count >= 50:
        score += 3
    elif function_count >= 20:
        score += 2
    elif function_count >= 8:
        score += 1

    if edge_count >= 400:
        score += 4
    elif edge_count >= 200:
        score += 3
    elif edge_count >= 80:
        score += 2
    elif edge_count >= 20:
        score += 1

    if module_count >= 7:
        score += 4
    elif module_count >= 5:
        score += 3
    elif module_count >= 3:
        score += 2
    elif module_count >= 1:
        score += 1

    if len(core_modules) >= 6:
        score += 3
    elif len(core_modules) >= 4:
        score += 2
    elif len(core_modules) >= 2:
        score += 1

    if structure_complexity >= 0.75:
        score += 2
    elif structure_complexity >= 0.45:
        score += 1

    values = []
    for value in module_completeness.values():
        try:
            values.append(float(value))
        except Exception:
            pass
    if values:
        average = sum(values) / len(values)
        if average >= 0.70:
            score += 2
        elif average >= 0.45:
            score += 1

    return round(max(0, min(score, 20)), 2)


def calculate_final_repository_quality(repo_profile, implementation_quality):
    implementation_score_100 = safe_number(implementation_quality.get("overall_implementation_score"), 0)
    implementation_score_20 = implementation_score_100 / 5
    structure_score_20 = calculate_structure_score(repo_profile)
    chain_score_20 = safe_number(implementation_quality.get("chain_closure", {}).get("score"), 0)
    engineering_score_20 = safe_number(implementation_quality.get("engineering_evidence", {}).get("score"), 0)

    red_flag_count = len(implementation_quality.get("red_flags", []))
    weak_function_count = safe_number(
        implementation_quality.get("function_quality_summary", {}).get("weak_or_shell_function_count"), 0
    )
    total_function_count = safe_number(
        implementation_quality.get("function_quality_summary", {}).get("function_count"), 0
    )

    penalty_20 = 0.0
    if red_flag_count >= 20:
        penalty_20 += 3
    elif red_flag_count >= 10:
        penalty_20 += 2
    elif red_flag_count >= 4:
        penalty_20 += 1

    if total_function_count > 0:
        weak_ratio = weak_function_count / max(total_function_count, 1)
        if weak_ratio >= 0.45:
            penalty_20 += 3
        elif weak_ratio >= 0.25:
            penalty_20 += 1.5

    final_20 = (
        implementation_score_20 * 0.50
        + structure_score_20 * 0.20
        + chain_score_20 * 0.15
        + engineering_score_20 * 0.15
        - penalty_20
    )
    final_20 = max(0, min(final_20, 20))
    final_100 = round(final_20 * 5, 2)

    if final_100 >= 85:
        level = "excellent"
    elif final_100 >= 70:
        level = "good"
    elif final_100 >= 55:
        level = "medium"
    else:
        level = "weak"

    return {
        "final_quality_score": final_100,
        "quality_level": level,
        "score_components": {
            "implementation_score_20": round(implementation_score_20, 2),
            "structure_score_20": round(structure_score_20, 2),
            "chain_score_20": round(chain_score_20, 2),
            "engineering_score_20": round(engineering_score_20, 2),
            "penalty_20": round(penalty_20, 2),
            "formula": "final = implementation*0.50 + structure*0.20 + chain*0.15 + engineering*0.15 - penalty, then *5",
        }
    }


def rank_repositories_by_quality(profile_dir="repo_profiles/history", output_dir="repository_quality", scope="history"):
    ensure_dir(output_dir)
    profile_files = find_repo_profile_files(profile_dir)
    ranking_items = []
    detail_records = []

    for profile_path in profile_files:
        repo_profile = load_json_file(profile_path)
        repo_name = repo_profile.get("repo_name") or infer_repo_name_from_profile_file(os.path.basename(profile_path))

        implementation_quality = evaluate_implementation_quality(
            repo_profile_path=profile_path,
            function_analysis_path=os.path.join("function_analysis", f"{repo_name}_function_analysis.json"),
            code_blocks_path=os.path.join("code_blocks", f"{repo_name}_blocks.json"),
            module_summary_path=os.path.join("module_summary", f"{repo_name}_module_summary_full.json"),
        )

        iq_json_path = save_implementation_quality_result(implementation_quality)
        iq_md_path = save_implementation_quality_markdown(implementation_quality)

        quality_score = calculate_final_repository_quality(repo_profile, implementation_quality)

        item = {
            "repo_name": repo_name,
            "scope": scope,
            "final_quality_score": quality_score.get("final_quality_score"),
            "quality_level": quality_score.get("quality_level"),
            "score_components": quality_score.get("score_components"),
            "implementation_quality_path": iq_json_path,
            "implementation_quality_report_path": iq_md_path,
            "implementation_summary": {
                "overall_implementation_score": implementation_quality.get("overall_implementation_score"),
                "implementation_level": implementation_quality.get("implementation_level"),
                "confidence": implementation_quality.get("confidence"),
                "strong_function_count": implementation_quality.get("function_quality_summary", {}).get("strong_function_count"),
                "real_function_count": implementation_quality.get("function_quality_summary", {}).get("real_function_count"),
                "weak_or_shell_function_count": implementation_quality.get("function_quality_summary", {}).get("weak_or_shell_function_count"),
            },
            "repo_profile_summary": {
                "project_type": repo_profile.get("project_type"),
                "main_languages": repo_profile.get("main_languages", []),
                "function_count": repo_profile.get("function_count"),
                "edge_count": repo_profile.get("edge_count"),
                "module_count": repo_profile.get("module_count"),
                "core_modules": repo_profile.get("core_modules", []),
                "structure_complexity": repo_profile.get("structure_complexity"),
            },
            "strengths": implementation_quality.get("strengths", [])[:5],
            "weaknesses": implementation_quality.get("weaknesses", [])[:5],
            "red_flag_count": len(implementation_quality.get("red_flags", [])),
        }
        ranking_items.append(item)
        detail_records.append({
            "repo_name": repo_name,
            "profile_path": profile_path,
            "implementation_quality_path": iq_json_path,
            "implementation_quality_report_path": iq_md_path,
        })

    ranking_items.sort(key=lambda x: x.get("final_quality_score", 0), reverse=True)

    for index, item in enumerate(ranking_items, start=1):
        item["rank"] = index

    result = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ranker_version": "v6.1-repository-quality-ranker",
        "scope": scope,
        "profile_dir": profile_dir,
        "repository_count": len(ranking_items),
        "ranking": ranking_items,
        "detail_records": detail_records,
        "note": "该排名基于静态代码内容理解、模块真实实现质量、OS 链路闭环、工程证据和结构规模综合得出，不等同于真实运行测试。"
    }

    json_path = os.path.join(output_dir, f"{scope}_repository_quality_ranking.json")
    md_path = os.path.join(output_dir, f"{scope}_repository_quality_ranking.md")
    save_json_file(result, json_path)
    save_text_file(format_repository_quality_ranking_markdown(result), md_path)

    return result, json_path, md_path


def format_repository_quality_ranking_markdown(result):
    lines = []
    lines.append(f"# {result.get('scope')} 仓库真实实现质量排行榜")
    lines.append("")
    lines.append(f"生成时间：{result.get('created_at')}")
    lines.append("")
    lines.append(result.get("note", ""))
    lines.append("")

    lines.append("## 一、总排名")
    lines.append("")
    lines.append("| 排名 | 仓库 | 总分 | 等级 | 实现质量 | 结构分 | 链路分 | 工程证据 |")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|")

    for item in result.get("ranking", []):
        comp = item.get("score_components", {})
        lines.append(
            f"| {item.get('rank')} | {item.get('repo_name')} | {item.get('final_quality_score')} | "
            f"{item.get('quality_level')} | {comp.get('implementation_score_20')} | {comp.get('structure_score_20')} | "
            f"{comp.get('chain_score_20')} | {comp.get('engineering_score_20')} |"
        )

    lines.append("")
    lines.append("## 二、逐仓库简评")
    lines.append("")

    for item in result.get("ranking", []):
        lines.append(f"### {item.get('rank')}. {item.get('repo_name')} — {item.get('final_quality_score')} 分")
        lines.append("")
        summary = item.get("implementation_summary", {})
        lines.append(f"- 等级：{item.get('quality_level')}")
        lines.append(f"- 实现质量：{summary.get('overall_implementation_score')} / 100，{summary.get('implementation_level')}")
        lines.append(f"- 真实函数数：{summary.get('real_function_count')}，强实现函数数：{summary.get('strong_function_count')}，弱/空壳函数数：{summary.get('weak_or_shell_function_count')}")
        lines.append(f"- 风险信号数：{item.get('red_flag_count')}")
        lines.append("- 主要优势：")
        for strength in item.get("strengths", []) or ["暂无明确优势。"]:
            lines.append(f"  - {strength}")
        lines.append("- 主要不足：")
        for weakness in item.get("weaknesses", []) or ["暂无明显不足。"]:
            lines.append(f"  - {weakness}")
        lines.append("")

    return "\n".join(lines)


def format_repository_quality_ranking_preview(result, json_path=None, md_path=None):
    lines = []
    lines.append("仓库真实实现质量排名完成。")
    lines.append("")
    lines.append(f"范围：{result.get('scope')}")
    lines.append(f"仓库数量：{result.get('repository_count')}")
    if json_path:
        lines.append(f"JSON：{json_path}")
    if md_path:
        lines.append(f"Markdown：{md_path}")
    lines.append("")
    lines.append("排名：")
    for item in result.get("ranking", [])[:20]:
        lines.append(f"{item.get('rank')}. {item.get('repo_name')} - {item.get('final_quality_score')} 分 - {item.get('quality_level')}")
    return "\n".join(lines)
