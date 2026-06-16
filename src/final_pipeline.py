import os


from src.ingest_pipeline import analyze_target_repo
from src.history_kb_builder import (
    build_history_knowledge_base_full,
    save_history_knowledge_base_full
)
from src.history_retriever import (
    retrieve_similar_history_projects_full,
    save_retrieval_result_full
)
from src.history_comparator import (
    compare_retrieval_results_with_ai,
    save_history_comparison_full
)
from src.score_evaluator import (
    evaluate_project_score_full,
    save_score_result_full
)
from src.final_report_generator import (
    generate_final_report_full,
    save_final_report_full
)


def get_repo_name_from_path(repo_path):
    """
    从仓库路径中提取仓库名。
    """

    repo_path = repo_path.rstrip("/\\")
    return os.path.basename(os.path.abspath(repo_path))


def find_target_repo_profile_full(repo_path):
    """
    根据仓库路径推测 target repo_profile_full 路径。
    用于 generated_files 中没有 repo_profile_full_path 时兜底。
    """

    repo_name = get_repo_name_from_path(repo_path)

    candidate_path = os.path.join(
        "repo_profiles",
        "target",
        f"{repo_name}_repo_profile_full.json"
    )

    if os.path.exists(candidate_path):
        return candidate_path

    return None


def require_file(file_path, description):
    """
    检查文件是否存在。
    """

    if not file_path:
        raise FileNotFoundError(f"缺少必要文件：{description}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{description} -> {file_path}")


def run_final_analyze_pipeline(
    repo_path,
    ask_ai_once,
    analysis_mode="full",
    max_blocks=100,
    top_k=3
):
    """
    一键完整分析目标仓库。

    流程：
    1. 分析目标仓库，生成 repo_profile_full
    2. 构建 full 历史知识库
    3. 检索相似历史项目
    4. AI 对比解释
    5. 结构化评分
    6. 生成最终 Markdown 报告
    """

    generated_files = {}

    print()
    print("=" * 70)
    print("开始 final_analyze 一键完整分析流程")
    print("=" * 70)
    print(f"目标仓库路径：{repo_path}")
    print(f"分析模式：{analysis_mode}")
    print(f"AI 分析代码块数量：{max_blocks if max_blocks is not None else 'all'}")
    print(f"相似历史项目 Top-K：{top_k}")
    print("=" * 70)

    # 1. 分析目标仓库
    print()
    print("步骤 1/6：正在分析目标仓库...")

    analysis_files = analyze_target_repo(
        repo_path=repo_path,
        ask_ai_once=ask_ai_once,
        max_blocks=max_blocks,
        analysis_mode=analysis_mode
    )

    generated_files.update(analysis_files)

    repo_profile_full_path = generated_files.get("repo_profile_full_path")

    if not repo_profile_full_path:
        repo_profile_full_path = find_target_repo_profile_full(repo_path)

    require_file(
        repo_profile_full_path,
        "目标仓库 repo_profile_full"
    )

    generated_files["repo_profile_full_path"] = repo_profile_full_path

    print(f"目标仓库画像文件：{repo_profile_full_path}")

    # 2. 更新 full 历史知识库
    print()
    print("步骤 2/6：正在更新 full 历史知识库...")

    history_kb_full = build_history_knowledge_base_full(
        profile_dir="repo_profiles/history"
    )

    history_kb_full_path = save_history_knowledge_base_full(
        history_kb_full
    )

    generated_files["history_kb_full_path"] = history_kb_full_path

    print(f"full 历史知识库：{history_kb_full_path}")
    print(f"历史项目数量：{history_kb_full.get('profile_count')}")

    if history_kb_full.get("profile_count", 0) == 0:
        print("警告：full 历史知识库为空，后续相似项目检索结果可能为空。")

    # 3. 检索相似历史项目
    print()
    print("步骤 3/6：正在检索相似历史项目...")

    retrieval_result = retrieve_similar_history_projects_full(
        target_profile_path=repo_profile_full_path,
        history_kb_full_path=history_kb_full_path,
        top_k=top_k
    )

    retrieval_result_path = save_retrieval_result_full(
        retrieval_result
    )

    generated_files["retrieval_result_full_path"] = retrieval_result_path

    print(f"相似历史项目检索结果：{retrieval_result_path}")
    print(f"候选历史项目数量：{retrieval_result.get('candidate_count')}")
    print(f"返回结果数量：{len(retrieval_result.get('results', []))}")

    # 4. AI 历史项目对比解释
    print()
    print("步骤 4/6：正在进行 AI 历史项目对比解释...")

    comparison_result = compare_retrieval_results_with_ai(
        retrieval_result_path=retrieval_result_path,
        ask_ai_once=ask_ai_once
    )

    comparison_result_path = save_history_comparison_full(
        comparison_result
    )

    generated_files["history_comparison_full_path"] = comparison_result_path

    print(f"AI 历史项目对比结果：{comparison_result_path}")
    print(f"对比项目数量：{comparison_result.get('comparison_count')}")

    # 5. 结构化评分
    print()
    print("步骤 5/6：正在生成 full 结构化评分...")

    score_result = evaluate_project_score_full(
        repo_profile_path=repo_profile_full_path,
        retrieval_result_path=retrieval_result_path,
        comparison_result_path=comparison_result_path,
        ask_ai_once=ask_ai_once
    )

    score_result_path = save_score_result_full(
        score_result
    )

    generated_files["score_full_path"] = score_result_path

    evaluation = score_result.get("evaluation", {})

    print(f"结构化评分结果：{score_result_path}")
    print(f"总分：{evaluation.get('overall_score')}")
    print(f"等级：{evaluation.get('score_level')}")

    # 6. 最终 Markdown 报告
    print()
    print("步骤 6/6：正在生成最终 Markdown 报告...")

    final_report_result = generate_final_report_full(
        repo_profile_path=repo_profile_full_path,
        retrieval_result_path=retrieval_result_path,
        comparison_result_path=comparison_result_path,
        score_result_path=score_result_path
    )

    final_report_path = save_final_report_full(
        final_report_result
    )

    generated_files["final_report_path"] = final_report_path

    print(f"最终 Markdown 报告：{final_report_path}")

    print()
    print("=" * 70)
    print("final_analyze 一键完整分析流程完成")
    print("=" * 70)

    return generated_files


def format_final_analyze_preview(generated_files):
    """
    生成 final_analyze 结果预览。
    """

    output = []

    output.append("final_analyze 一键完整分析完成。")
    output.append("")
    output.append("生成文件：")

    key_order = [
        "repo_profile_full_path",
        "history_kb_full_path",
        "retrieval_result_full_path",
        "history_comparison_full_path",
        "score_full_path",
        "final_report_path"
    ]

    for key in key_order:
        value = generated_files.get(key)

        if value:
            output.append(f"- {key}: {value}")

    output.append("")

    final_report_path = generated_files.get("final_report_path")

    if final_report_path:
        output.append(f"最终报告路径：{final_report_path}")

    return "\n".join(output)