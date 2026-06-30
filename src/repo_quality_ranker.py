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
    resolve_repo_artifact_path,
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


def normalize_score_level(overall_score, score_level=None):
    if score_level:
        return score_level

    score = safe_number(overall_score, 0)
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 55:
        return "medium"
    return "weak"


def load_score_full_summary(repo_name):
    score_path = os.path.join("evaluation", f"{repo_name}_score_full.json")
    score_result = load_json_file(score_path, default={})
    evaluation = score_result.get("evaluation", {}) if isinstance(score_result, dict) else {}

    if not evaluation:
        return {
            "score_result_path": score_path,
            "available": False,
            "overall_score": 0,
            "score_level": "unknown",
            "dimension_scores": {},
        }

    dimension_scores = {}
    for key, value in (evaluation.get("scores", {}) or {}).items():
        if isinstance(value, dict):
            dimension_scores[key] = safe_number(value.get("score"), 0)
        else:
            dimension_scores[key] = safe_number(value, 0)

    overall_score = safe_number(evaluation.get("overall_score"), 0)
    return {
        "score_result_path": score_path,
        "available": True,
        "overall_score": overall_score,
        "score_level": normalize_score_level(overall_score, evaluation.get("score_level")),
        "dimension_scores": dimension_scores,
        "confidence": evaluation.get("confidence", "unknown"),
    }


def build_implementation_quality_auxiliary(implementation_quality):
    summary = implementation_quality.get("function_quality_summary", {}) or {}
    return {
        "overall_implementation_score": implementation_quality.get("overall_implementation_score"),
        "implementation_level": implementation_quality.get("implementation_level"),
        "confidence": implementation_quality.get("confidence"),
        "chain_score_20": safe_number(
            implementation_quality.get("chain_closure", {}).get("score"), 0
        ),
        "engineering_score_20": safe_number(
            implementation_quality.get("engineering_evidence", {}).get("score"), 0
        ),
        "strong_function_count": summary.get("strong_function_count"),
        "real_function_count": summary.get("real_function_count"),
        "weak_or_shell_function_count": summary.get("weak_or_shell_function_count"),
        "red_flag_count": len(implementation_quality.get("red_flags", [])),
    }


def build_ranking_score(repo_profile, repo_name, implementation_quality):
    score_summary = load_score_full_summary(repo_name)
    auxiliary = build_implementation_quality_auxiliary(implementation_quality)

    if score_summary.get("available"):
        return {
            "final_quality_score": score_summary.get("overall_score"),
            "quality_level": score_summary.get("score_level"),
            "score_source": "score_full",
            "score_full_path": score_summary.get("score_result_path"),
            "score_components": {
                "dimension_scores": score_summary.get("dimension_scores", {}),
                "confidence": score_summary.get("confidence"),
                "formula": "final_quality_score = score_full.evaluation.overall_score",
            },
            "implementation_quality_auxiliary": auxiliary,
        }

    return {
        "final_quality_score": 0,
        "quality_level": "missing_score_full",
        "score_source": "missing_score_full",
        "score_full_path": score_summary.get("score_result_path"),
        "score_components": {
            "dimension_scores": {},
            "confidence": "none",
            "formula": "score_full missing; implementation_quality is auxiliary only and is not used as ranking score",
        },
        "implementation_quality_auxiliary": auxiliary,
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
            function_analysis_path=resolve_repo_artifact_path(
                repo_name,
                "function_analysis",
                ["_function_analysis_full.json", "_function_analysis.json"],
            ),
            code_blocks_path=os.path.join("code_blocks", f"{repo_name}_blocks.json"),
            module_summary_path=os.path.join("module_summary", f"{repo_name}_module_summary_full.json"),
        )

        iq_json_path = save_implementation_quality_result(implementation_quality)
        iq_md_path = save_implementation_quality_markdown(implementation_quality)

        quality_score = build_ranking_score(
            repo_profile=repo_profile,
            repo_name=repo_name,
            implementation_quality=implementation_quality,
        )

        item = {
            "repo_name": repo_name,
            "scope": scope,
            "final_quality_score": quality_score.get("final_quality_score"),
            "quality_level": quality_score.get("quality_level"),
            "score_source": quality_score.get("score_source"),
            "score_full_path": quality_score.get("score_full_path"),
            "score_components": quality_score.get("score_components"),
            "implementation_quality_auxiliary": quality_score.get("implementation_quality_auxiliary"),
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
        "ranker_version": "v6.2-score-full-ranking-with-implementation-auxiliary",
        "scope": scope,
        "profile_dir": profile_dir,
        "repository_count": len(ranking_items),
        "ranking": ranking_items,
        "detail_records": detail_records,
        "note": "排名总分直接采用 score_full 五维综合评分，与最终报告中的综合评分保持一致；真实实现质量仅作为辅助指标展示，不参与排名总分。缺少 score_full 的仓库会标记为 missing_score_full，不使用真实实现质量替代打分。"
    }

    json_path = os.path.join(output_dir, f"{scope}_repository_quality_ranking.json")
    md_path = os.path.join(output_dir, f"{scope}_repository_quality_ranking.md")
    save_json_file(result, json_path)
    save_text_file(format_repository_quality_ranking_markdown(result), md_path)

    return result, json_path, md_path


def format_repository_quality_ranking_markdown(result):
    lines = []
    lines.append(f"# {result.get('scope')} 仓库五维综合评分排行")
    lines.append("")
    lines.append(f"生成时间：{result.get('created_at')}")
    lines.append("")
    lines.append(result.get("note", ""))
    lines.append("")

    lines.append("## 一、总排名")
    lines.append("")
    lines.append("| 排名 | 仓库 | 五维综合分 | 等级 | 分数来源 | 真实实现质量(辅助) | 真实函数 | 弱/空壳函数 | 风险信号 |")
    lines.append("|---:|---|---:|---|---|---:|---:|---:|---:|")

    for item in result.get("ranking", []):
        auxiliary = item.get("implementation_quality_auxiliary", {}) or item.get("implementation_summary", {})
        lines.append(
            f"| {item.get('rank')} | {item.get('repo_name')} | {item.get('final_quality_score')} | "
            f"{item.get('quality_level')} | {item.get('score_source')} | "
            f"{auxiliary.get('overall_implementation_score')} | "
            f"{auxiliary.get('real_function_count')} | "
            f"{auxiliary.get('weak_or_shell_function_count')} | "
            f"{auxiliary.get('red_flag_count', item.get('red_flag_count'))} |"
        )

    lines.append("")
    lines.append("## 二、逐仓库简评")
    lines.append("")

    for item in result.get("ranking", []):
        lines.append(f"### {item.get('rank')}. {item.get('repo_name')} — {item.get('final_quality_score')} 分")
        lines.append("")
        summary = item.get("implementation_summary", {})
        lines.append(f"- 五维综合等级：{item.get('quality_level')}")
        lines.append(f"- 分数来源：{item.get('score_source')} ({item.get('score_full_path')})")
        lines.append(f"- 真实实现质量辅助指标：{summary.get('overall_implementation_score')} / 100，{summary.get('implementation_level')}")
        lines.append(f"- 真实函数数：{summary.get('real_function_count')}，强实现函数数：{summary.get('strong_function_count')}，弱/空壳函数数：{summary.get('weak_or_shell_function_count')}")
        lines.append(f"- 风险信号数：{item.get('red_flag_count')}")
        lines.append("- 辅助实现质量优势：")
        for strength in item.get("strengths", []) or ["暂无明确优势。"]:
            lines.append(f"  - {strength}")
        lines.append("- 辅助实现质量不足：")
        for weakness in item.get("weaknesses", []) or ["暂无明显不足。"]:
            lines.append(f"  - {weakness}")
        lines.append("")

    return "\n".join(lines)


def format_repository_quality_ranking_preview(result, json_path=None, md_path=None):
    lines = []
    lines.append("仓库五维综合评分排名完成。")
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
        lines.append(f"{item.get('rank')}. {item.get('repo_name')} - {item.get('final_quality_score')} 分 - {item.get('quality_level')} - {item.get('score_source')}")
    return "\n".join(lines)
