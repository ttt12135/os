import os
import json
import shutil
from datetime import datetime

DEFAULT_SITE_OUTPUT_DIR = "site/public"
DEFAULT_WORKS_MANIFEST_PATH = "site_config/works_manifest.json"


def ensure_dir(directory):
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path, default=None):
    if default is None:
        default = {}
    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def save_json_file(data, file_path):
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def copy_file_if_exists(source_path, target_path):
    if not source_path or not os.path.exists(source_path) or os.path.isdir(source_path):
        return False
    ensure_dir(os.path.dirname(target_path))
    shutil.copyfile(source_path, target_path)
    return True


def safe_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value] if value.strip() else []
    return []


def safe_number(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_repo_url(repo_url):
    if repo_url is None:
        return ""
    text = str(repo_url).strip().lower()
    if text.endswith(".git"):
        text = text[:-4]
    return text.rstrip("/")


def infer_repo_name_from_profile_file(file_name):
    suffix = "_repo_profile_full.json"
    if file_name.endswith(suffix):
        return file_name.replace(suffix, "")
    if file_name.endswith(".json"):
        return file_name.replace(".json", "")
    return file_name


def is_valid_repo_profile_filename(file_name):
    if not file_name.endswith("_repo_profile_full.json"):
        return False
    repo_name = infer_repo_name_from_profile_file(file_name)
    # 过滤把中间产物误当仓库名的文件，例如 xxx_call_graph_enhanced.json_repo_profile_full.json
    if ".json" in repo_name:
        return False
    if "call_graph" in repo_name or "blocks" in repo_name or "module_summary" in repo_name:
        return False
    return True


def find_repo_profiles(profile_dir):
    if not os.path.exists(profile_dir):
        return []
    profile_files = []
    for file_name in os.listdir(profile_dir):
        if not is_valid_repo_profile_filename(file_name):
            continue
        file_path = os.path.join(profile_dir, file_name)
        if os.path.isfile(file_path):
            profile_files.append(file_path)
    profile_files.sort()
    return profile_files


def find_target_repo_profiles(profile_dir="repo_profiles/target"):
    return find_repo_profiles(profile_dir)


def find_history_repo_profiles(profile_dir="repo_profiles/history"):
    return find_repo_profiles(profile_dir)


def load_works_manifest(manifest_path=DEFAULT_WORKS_MANIFEST_PATH):
    manifest_data = load_json_file(manifest_path, default=[])
    if not isinstance(manifest_data, list):
        return {}
    manifest_map = {}
    for item in manifest_data:
        if not isinstance(item, dict):
            continue
        repo_name = item.get("repo_name")
        if repo_name:
            manifest_map[repo_name] = item
    return manifest_map


def get_manifest_item(manifest_map, repo_name, repo_profile=None):
    if repo_name in manifest_map:
        return manifest_map[repo_name]
    repo_url = ""
    if isinstance(repo_profile, dict):
        repo_url = normalize_repo_url(repo_profile.get("repo_url", ""))
    for item in manifest_map.values():
        if normalize_repo_url(item.get("repo_url", "")) and normalize_repo_url(item.get("repo_url", "")) == repo_url:
            return item
    return {}


def get_score_summary(score_result):
    evaluation = score_result.get("evaluation", {}) if isinstance(score_result, dict) else {}
    scores = evaluation.get("scores", {}) if isinstance(evaluation, dict) else {}

    def score_of(key):
        item = scores.get(key, {})
        if isinstance(item, dict):
            return safe_number(item.get("score"))
        return safe_number(item)

    return {
        "overall_score": safe_number(evaluation.get("overall_score", 0)),
        "score_level": evaluation.get("score_level", "unknown"),
        "scores": {
            "originality": score_of("originality"),
            "novelty": score_of("novelty"),
            "practicality": score_of("practicality"),
            "difficulty": score_of("difficulty"),
            "completion": score_of("completion")
        },
        "summary": evaluation.get("summary", ""),
        "strengths": evaluation.get("strengths", []),
        "weaknesses": evaluation.get("weaknesses", []),
        "suggestions": evaluation.get("suggestions", [])
    }


def get_top_hybrid_results(hybrid_result, top_n=5):
    if not isinstance(hybrid_result, dict):
        return []
    results = hybrid_result.get("results", [])
    if not isinstance(results, list):
        return []
    output = []
    for item in results[:top_n]:
        if not isinstance(item, dict):
            continue
        output.append({
            "repo_name": item.get("repo_name", item.get("history_repo_name", "unknown_repo")),
            "hybrid_score": safe_number(item.get("hybrid_score", item.get("similarity_score", 0))),
            "structured_score": safe_number(item.get("structured_score", 0)),
            "semantic_score": safe_number(item.get("semantic_score", 0)),
            "rank": item.get("rank"),
            "source": item.get("source", []),
            "semantic_evidence": item.get("semantic_evidence", []),
            "matched_reasons": item.get("matched_reasons", [])
        })
    return output


def get_comparison_summary(comparison_result):
    if not isinstance(comparison_result, dict):
        comparison_result = {}
    comparisons = comparison_result.get("comparisons", [])
    if not isinstance(comparisons, list):
        comparisons = []
    output = []
    for item in comparisons:
        if not isinstance(item, dict):
            continue
        output.append({
            "history_repo_name": item.get("history_repo_name", item.get("repo_name", "unknown_repo")),
            "similarity_score": safe_number(item.get("similarity_score", item.get("hybrid_score", 0))),
            "hybrid_score": safe_number(item.get("hybrid_score", item.get("similarity_score", 0))),
            "structured_score": safe_number(item.get("structured_score", 0)),
            "semantic_score": safe_number(item.get("semantic_score", 0)),
            "retrieval_mode": item.get("retrieval_mode", comparison_result.get("retrieval_mode", "structured")),
            "similarity_summary": item.get("similarity_summary", ""),
            "main_similarities": item.get("main_similarities", []),
            "main_differences": item.get("main_differences", []),
            "target_advantages": item.get("target_advantages", []),
            "target_weaknesses": item.get("target_weaknesses", []),
            "borrowable_designs": item.get("borrowable_designs", []),
            "comparison_confidence": item.get("comparison_confidence", "unknown")
        })
    return {
        "retrieval_mode": comparison_result.get("retrieval_mode", "structured"),
        "comparison_count": comparison_result.get("comparison_count", len(output)),
        "comparisons": output
    }


def common_profile_fields(repo_profile):
    return {
        "project_type": repo_profile.get("project_type", "unknown"),
        "main_languages": safe_list(repo_profile.get("main_languages")),
        "core_modules": safe_list(repo_profile.get("core_modules")),
        "function_count": repo_profile.get("function_count", repo_profile.get("node_count", 0)),
        "node_count": repo_profile.get("node_count", repo_profile.get("function_count", 0)),
        "edge_count": repo_profile.get("edge_count", 0),
        "internal_edge_count": repo_profile.get("internal_edge_count", 0),
        "external_edge_count": repo_profile.get("external_edge_count", 0),
        "module_count": repo_profile.get("module_count", 0),
        "structure_complexity": repo_profile.get("structure_complexity", 0),
        "module_completeness": repo_profile.get("module_completeness", {}),
        "core_module_details": repo_profile.get("core_module_details", {}),
        "module_profiles": repo_profile.get("module_profiles", {}),
        "technical_features": repo_profile.get("technical_features", []),
        "weaknesses": repo_profile.get("weaknesses", []),
        "data_quality": repo_profile.get("data_quality", {})
    }


def build_work_detail(repo_name, repo_profile, score_result, hybrid_result, comparison_result, manifest_item, report_public_path):
    repo_url = manifest_item.get("repo_url", repo_profile.get("repo_url", ""))
    detail = {
        "repo_name": repo_name,
        "team_name": manifest_item.get("team_name", repo_name),
        "school": manifest_item.get("school", "unknown"),
        "repo_url": repo_url,
        "normalized_repo_url": normalize_repo_url(repo_url),
        "year": manifest_item.get("year", "2026"),
        "track": manifest_item.get("track", "kernel"),
        "status": "analyzed",
        **common_profile_fields(repo_profile),
        "score": get_score_summary(score_result),
        "hybrid_top_results": get_top_hybrid_results(hybrid_result),
        "comparison": get_comparison_summary(comparison_result),
        "urls": {
            "report_markdown": report_public_path,
            "work_detail_data": f"/data/works/{repo_name}.json",
            "comparison_data": f"/data/comparisons/{repo_name}.json"
        },
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return detail


def build_work_summary(work_detail):
    score = work_detail.get("score", {})
    return {
        "repo_name": work_detail.get("repo_name"),
        "team_name": work_detail.get("team_name"),
        "school": work_detail.get("school"),
        "repo_url": work_detail.get("repo_url"),
        "normalized_repo_url": work_detail.get("normalized_repo_url"),
        "year": work_detail.get("year"),
        "track": work_detail.get("track"),
        "status": work_detail.get("status"),
        "project_type": work_detail.get("project_type"),
        "main_languages": work_detail.get("main_languages", []),
        "core_modules": work_detail.get("core_modules", []),
        "overall_score": score.get("overall_score", 0),
        "score_level": score.get("score_level", "unknown"),
        "function_count": work_detail.get("function_count", 0),
        "edge_count": work_detail.get("edge_count", 0),
        "module_count": work_detail.get("module_count", 0),
        "structure_complexity": work_detail.get("structure_complexity", 0),
        "report_url": f"/works/{work_detail.get('repo_name')}",
        "comparison_url": f"/compare/{work_detail.get('repo_name')}",
        "data_url": work_detail.get("urls", {}).get("work_detail_data")
    }


def build_history_detail(repo_name, repo_profile, manifest_item):
    repo_url = manifest_item.get("repo_url", repo_profile.get("repo_url", ""))
    return {
        "repo_name": repo_name,
        "team_name": manifest_item.get("team_name", repo_name),
        "school": manifest_item.get("school", "unknown"),
        "repo_url": repo_url,
        "normalized_repo_url": normalize_repo_url(repo_url),
        "year": manifest_item.get("year", "history"),
        "track": manifest_item.get("track", "kernel"),
        "status": "indexed_history",
        **common_profile_fields(repo_profile),
        "urls": {"history_detail_data": f"/data/history/{repo_name}.json"},
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def build_history_summary(history_detail):
    return {
        "repo_name": history_detail.get("repo_name"),
        "team_name": history_detail.get("team_name"),
        "school": history_detail.get("school"),
        "repo_url": history_detail.get("repo_url"),
        "normalized_repo_url": history_detail.get("normalized_repo_url"),
        "year": history_detail.get("year"),
        "track": history_detail.get("track"),
        "status": history_detail.get("status"),
        "project_type": history_detail.get("project_type"),
        "main_languages": history_detail.get("main_languages", []),
        "core_modules": history_detail.get("core_modules", []),
        "function_count": history_detail.get("function_count", 0),
        "edge_count": history_detail.get("edge_count", 0),
        "module_count": history_detail.get("module_count", 0),
        "structure_complexity": history_detail.get("structure_complexity", 0),
        "detail_url": f"/history/{history_detail.get('repo_name')}",
        "data_url": history_detail.get("urls", {}).get("history_detail_data")
    }


def build_site_stats(work_summaries, history_summaries=None):
    history_summaries = history_summaries or []
    all_items = list(work_summaries) + list(history_summaries)
    average_score = 0
    if work_summaries:
        average_score = sum(safe_number(item.get("overall_score")) for item in work_summaries) / len(work_summaries)
    languages, modules, schools = set(), set(), set()
    for item in all_items:
        for lang in safe_list(item.get("main_languages")):
            languages.add(str(lang))
        for module in safe_list(item.get("core_modules")):
            modules.add(str(module))
        school = item.get("school")
        if school and school != "unknown":
            schools.add(str(school))
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_work_count": len(work_summaries),
        "analyzed_works": len([item for item in work_summaries if item.get("status") == "analyzed"]),
        "history_count": len(history_summaries),
        "total_indexed_projects": len(all_items),
        "average_score": round(average_score, 2),
        "language_count": len(languages),
        "core_module_count": len(modules),
        "school_count": len(schools)
    }


def export_one_work(repo_profile_path, manifest_map, site_output_dir=DEFAULT_SITE_OUTPUT_DIR):
    file_name = os.path.basename(repo_profile_path)
    repo_name = infer_repo_name_from_profile_file(file_name)
    repo_profile = load_json_file(repo_profile_path)
    manifest_item = get_manifest_item(manifest_map, repo_name, repo_profile)
    score_path = os.path.join("evaluation", f"{repo_name}_score_full.json")
    hybrid_path = os.path.join("history_knowledge_base", "hybrid_retrieval_results", f"{repo_name}_hybrid_retrieval_full.json")
    comparison_path = os.path.join("history_knowledge_base", "comparisons", f"{repo_name}_history_comparison_full.json")
    report_path = os.path.join("reports", f"{repo_name}_final_report.md")
    report_public_path = f"/reports/{repo_name}_final_report.md"
    report_target_path = os.path.join(site_output_dir, "reports", f"{repo_name}_final_report.md")
    report_copied = copy_file_if_exists(report_path, report_target_path)
    work_detail = build_work_detail(
        repo_name=repo_name,
        repo_profile=repo_profile,
        score_result=load_json_file(score_path),
        hybrid_result=load_json_file(hybrid_path),
        comparison_result=load_json_file(comparison_path),
        manifest_item=manifest_item,
        report_public_path=report_public_path
    )
    work_detail_path = os.path.join(site_output_dir, "data", "works", f"{repo_name}.json")
    comparison_data_path = os.path.join(site_output_dir, "data", "comparisons", f"{repo_name}.json")
    save_json_file(work_detail, work_detail_path)
    save_json_file(work_detail.get("comparison", {}), comparison_data_path)
    return {
        "repo_name": repo_name,
        "work_summary": build_work_summary(work_detail),
        "work_detail_path": work_detail_path,
        "comparison_data_path": comparison_data_path,
        "report_copied": report_copied
    }


def export_history_data(site_output_dir=DEFAULT_SITE_OUTPUT_DIR, manifest_map=None, exclude_repo_names=None):
    manifest_map = manifest_map or {}
    exclude_repo_names = set(exclude_repo_names or [])
    profile_files = find_history_repo_profiles()
    history_summaries, records = [], []
    for profile_path in profile_files:
        file_name = os.path.basename(profile_path)
        repo_name = infer_repo_name_from_profile_file(file_name)
        if repo_name in exclude_repo_names:
            continue
        repo_profile = load_json_file(profile_path)
        manifest_item = get_manifest_item(manifest_map, repo_name, repo_profile)
        history_detail = build_history_detail(repo_name, repo_profile, manifest_item)
        history_detail_path = os.path.join(site_output_dir, "data", "history", f"{repo_name}.json")
        save_json_file(history_detail, history_detail_path)
        history_summary = build_history_summary(history_detail)
        history_summaries.append(history_summary)
        records.append({"repo_name": repo_name, "history_detail_path": history_detail_path})
    history_summary_path = os.path.join(site_output_dir, "data", "history_summary.json")
    save_json_file(history_summaries, history_summary_path)
    return {
        "history_count": len(history_summaries),
        "history_summary_path": history_summary_path,
        "history_summaries": history_summaries,
        "records": records
    }


def build_scoring_logic():
    return {
        "title": "内核赛道作品五维评分体系",
        "total_score": 100,
        "dimensions": [
            {"key": "originality", "name": "原创性", "english_name": "Originality", "max_score": 20, "meaning": "评价项目是否具有独立设计思路，是否只是重复已有历史作品的常见结构。", "basis": ["目标作品与历史作品的结构相似度", "核心模块组合是否具有独特性", "是否存在明显区别于往届作品的设计思路"], "high_score": "具有清晰原创架构，核心模块设计与历史项目差异明显。", "low_score": "与多个历史项目高度相似，核心设计缺乏独立性。"},
            {"key": "novelty", "name": "新颖性", "english_name": "Novelty", "max_score": 20, "meaning": "评价项目是否使用新的技术路线、模块组合或实现方式。", "basis": ["语言和技术栈选择", "模块设计是否有新意", "与历史作品相比是否有新的功能亮点"], "high_score": "技术路线新颖，功能组合或实现方式有明显创新。", "low_score": "技术路径常规，模块组合与历史作品重合度高。"},
            {"key": "practicality", "name": "可实践性", "english_name": "Practicality", "max_score": 20, "meaning": "评价项目是否具备实际运行、扩展和继续开发的价值。", "basis": ["核心模块完整度", "系统调用、文件系统、进程管理等功能可用性", "工程结构是否适合继续扩展"], "high_score": "核心功能较完整，工程结构清晰，具备较强实用价值。", "low_score": "功能覆盖不足，模块完成度低，实际可运行价值有限。"},
            {"key": "difficulty", "name": "技术难度", "english_name": "Difficulty", "max_score": 20, "meaning": "评价项目实现所体现的技术复杂度和系统性。", "basis": ["函数数量与调用图复杂度", "核心模块数量", "内部调用关系复杂度", "是否涉及底层内核关键机制"], "high_score": "涉及多个核心 OS 模块，调用关系复杂，实现难度高。", "low_score": "模块较少，内部逻辑简单，主要依赖外部代码或已有框架。"},
            {"key": "completion", "name": "完成度", "english_name": "Completion", "max_score": 20, "meaning": "评价项目目标功能完成情况和整体工程成熟度。", "basis": ["模块完成度", "核心功能覆盖范围", "报告和代码证据是否完整", "与同类历史项目相比的完成情况"], "high_score": "模块实现均衡，核心功能完成较好，工程材料完整。", "low_score": "关键模块缺失或完成度低，整体系统不完整。"}
        ],
        "workflow": ["读取源码结构", "生成函数级语义理解", "构建调用图与模块画像", "检索历史相似作品", "对比相似点和差异点", "结合模块完整度与实现复杂度", "输出五维评分和证据"]
    }


def export_scoring_logic(site_output_dir=DEFAULT_SITE_OUTPUT_DIR):
    scoring_logic_path = os.path.join(site_output_dir, "data", "scoring_logic.json")
    save_json_file(build_scoring_logic(), scoring_logic_path)
    return scoring_logic_path


def export_website_data(site_output_dir=DEFAULT_SITE_OUTPUT_DIR, manifest_path=DEFAULT_WORKS_MANIFEST_PATH):
    ensure_dir(site_output_dir)
    manifest_map = load_works_manifest(manifest_path)
    profile_files = find_target_repo_profiles()
    records, work_summaries, target_repo_names = [], [], set()
    for profile_path in profile_files:
        record = export_one_work(profile_path, manifest_map, site_output_dir)
        records.append(record)
        work_summaries.append(record.get("work_summary"))
        target_repo_names.add(record.get("repo_name"))

    history_result = export_history_data(
        site_output_dir=site_output_dir,
        manifest_map=manifest_map,
        exclude_repo_names=target_repo_names
    )
    site_stats = build_site_stats(work_summaries, history_result.get("history_summaries", []))

    summary_path = os.path.join(site_output_dir, "data", "works_summary.json")
    stats_path = os.path.join(site_output_dir, "data", "site_stats.json")
    scoring_logic_path = export_scoring_logic(site_output_dir)

    save_json_file(work_summaries, summary_path)
    save_json_file(site_stats, stats_path)

    return {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "site_output_dir": site_output_dir,
        "manifest_path": manifest_path,
        "work_count": len(work_summaries),
        "history_count": history_result.get("history_count", 0),
        "works_summary_path": summary_path,
        "history_summary_path": history_result.get("history_summary_path"),
        "site_stats_path": stats_path,
        "scoring_logic_path": scoring_logic_path,
        "records": records,
        "history_records": history_result.get("records", [])
    }


def format_website_export_preview(export_result):
    lines = []
    lines.append("网站数据导出完成。")
    lines.append("")
    lines.append(f"导出时间：{export_result.get('created_at')}")
    lines.append(f"网站 public 目录：{export_result.get('site_output_dir')}")
    lines.append(f"本届作品数量：{export_result.get('work_count')}")
    lines.append(f"历史作品数量：{export_result.get('history_count')}")
    lines.append(f"本届作品汇总：{export_result.get('works_summary_path')}")
    lines.append(f"历史作品汇总：{export_result.get('history_summary_path')}")
    lines.append(f"网站统计数据：{export_result.get('site_stats_path')}")
    lines.append(f"评分逻辑数据：{export_result.get('scoring_logic_path')}")
    lines.append("")
    lines.append("导出本届作品：")
    for record in export_result.get("records", []):
        lines.append(f"- {record.get('repo_name')} | detail={record.get('work_detail_path')} | report_copied={record.get('report_copied')}")
    lines.append("")
    lines.append("导出历史作品：")
    for record in export_result.get("history_records", []):
        lines.append(f"- {record.get('repo_name')} | detail={record.get('history_detail_path')}")
    return "\n".join(lines)
