import os
import json

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
from src.rag_document_builder import (
    build_history_rag_documents,
    save_history_rag_documents,
    save_history_rag_documents_markdown
)

from src.rag_vector_store import build_chroma_vector_store

from src.hybrid_retriever import run_hybrid_retrieve

def get_repo_name_from_path(repo_path):
    """
    从仓库路径中提取仓库名。
    """

    repo_path = repo_path.rstrip("/\\")
    return os.path.basename(os.path.abspath(repo_path))


def validate_repo_path(repo_path):
    """
    检查输入是否是一个真实仓库目录。

    这个检查主要是防止把 .json 文件误输入成仓库路径，
    避免生成 xxx.json_repo_profile_full.json 这类异常文件。
    """

    if not repo_path:
        raise ValueError("仓库路径不能为空。")

    if repo_path.endswith(".json"):
        raise ValueError(
            f"你输入的是 JSON 文件，不是仓库目录：{repo_path}\n"
            f"请重新输入目标仓库文件夹路径。"
        )

    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"仓库路径不存在：{repo_path}")

    if not os.path.isdir(repo_path):
        raise NotADirectoryError(f"输入路径不是文件夹：{repo_path}")


def require_file(file_path, description):
    """
    检查文件是否存在。
    """

    if not file_path:
        raise FileNotFoundError(f"缺少必要文件：{description}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{description} -> {file_path}")


def load_json_file(file_path):
    """
    安全读取 JSON 文件。
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_expected_output_paths(repo_name):
    """
    根据仓库名推测 final_analyze 各阶段默认输出路径。
    """

    return {
        "repo_profile_full_path": os.path.join(
            "repo_profiles",
            "target",
            f"{repo_name}_repo_profile_full.json"
        ),
        "history_kb_full_path": os.path.join(
            "history_knowledge_base",
            "history_profiles_full.json"
        ),
        "retrieval_result_full_path": os.path.join(
            "history_knowledge_base",
            "retrieval_results",
            f"{repo_name}_similar_projects_full.json"
        ),
        "history_comparison_full_path": os.path.join(
            "history_knowledge_base",
            "comparisons",
            f"{repo_name}_history_comparison_full.json"
        ),
        "score_full_path": os.path.join(
            "evaluation",
            f"{repo_name}_score_full.json"
        ),
        "final_report_path": os.path.join(
            "reports",
            f"{repo_name}_final_report.md"
        )
    }


def can_use_file_cache(file_path):
    """
    判断某个缓存文件是否可用。
    """

    return file_path and os.path.exists(file_path) and os.path.isfile(file_path)


def is_retrieval_cache_usable(retrieval_path, repo_name, top_k):
    """
    判断 retrieve_full 缓存是否可用。

    这里不仅检查文件是否存在，还检查：
    1. target_repo 是否匹配
    2. top_k 是否匹配

    避免用户改了 top_k 之后还复用旧结果。
    """

    if not can_use_file_cache(retrieval_path):
        return False

    try:
        retrieval_result = load_json_file(retrieval_path)
    except Exception:
        return False

    if retrieval_result.get("target_repo") != repo_name:
        return False

    if retrieval_result.get("top_k") != top_k:
        return False

    return True


def print_cache_hit(step_name, file_path):
    """
    打印缓存命中信息。
    """

    print(f"{step_name}：检测到已有结果，跳过重新生成。")
    print(f"复用路径：{file_path}")


def print_cache_miss(step_name):
    """
    打印缓存未命中信息。
    """

    print(f"{step_name}：未发现可用缓存，开始重新生成。")


def run_final_analyze_pipeline(
    repo_path,
    ask_ai_once,
    analysis_mode="full",
    max_blocks=100,
    max_workers=8,
    top_k=3,
    use_cache=True,
    force_rebuild=False
):
    """
    一键完整分析目标仓库。

    v3.6 新增：
    1. 支持缓存复用
    2. 支持强制重跑
    3. 防止把 .json 文件误输入成仓库路径
    4. 如果上游结果被重建，下游自动重建，避免旧结果污染
    """

    validate_repo_path(repo_path)

    repo_name = get_repo_name_from_path(repo_path)
    expected_paths = get_expected_output_paths(repo_name)

    generated_files = {}
    execution_status = {}

    generated_files["repo_name"] = repo_name
    generated_files["analysis_mode"] = analysis_mode
    generated_files["max_blocks"] = max_blocks
    generated_files["top_k"] = top_k
    generated_files["use_cache"] = use_cache
    generated_files["force_rebuild"] = force_rebuild

    print()
    print("=" * 70)
    print("开始 final_analyze 一键完整分析流程 v3.6")
    print("=" * 70)
    print(f"目标仓库名称：{repo_name}")
    print(f"目标仓库路径：{repo_path}")
    print(f"分析模式：{analysis_mode}")
    print(f"AI 分析代码块数量：{max_blocks if max_blocks is not None else 'all'}")
    print(f"相似历史项目 Top-K：{top_k}")
    print(f"是否启用缓存：{use_cache}")
    print(f"是否强制重跑：{force_rebuild}")
    print("=" * 70)

    upstream_rebuilt = False

    # 1. 分析目标仓库，生成 repo_profile_full
    print()
    print("步骤 1/6：目标仓库分析")

    repo_profile_full_path = expected_paths["repo_profile_full_path"]

    if use_cache and not force_rebuild and can_use_file_cache(repo_profile_full_path):
        print_cache_hit("目标仓库画像 repo_profile_full", repo_profile_full_path)
        execution_status["analyze_target"] = "skipped_by_cache"
    else:
        print_cache_miss("目标仓库画像 repo_profile_full")

        analysis_files = analyze_target_repo(
            repo_path=repo_path,
            ask_ai_once=ask_ai_once,
            max_blocks=max_blocks,
            analysis_mode=analysis_mode,
            max_workers=max_workers
        )

        generated_files.update(analysis_files)

        repo_profile_full_path = generated_files.get(
            "repo_profile_full_path",
            repo_profile_full_path
        )

        execution_status["analyze_target"] = "rebuilt"
        upstream_rebuilt = True

    require_file(repo_profile_full_path, "目标仓库 repo_profile_full")

    generated_files["repo_profile_full_path"] = repo_profile_full_path

    print(f"目标仓库画像文件：{repo_profile_full_path}")

    # 2. 构建 full 历史知识库
    print()
    print("步骤 2/6：full 历史知识库")

    history_kb_full_path = expected_paths["history_kb_full_path"]

    if use_cache and not force_rebuild and can_use_file_cache(history_kb_full_path):
        print_cache_hit("full 历史知识库", history_kb_full_path)
        execution_status["history_kb_full"] = "skipped_by_cache"
    else:
        print_cache_miss("full 历史知识库")

        history_kb_full = build_history_knowledge_base_full(
            profile_dir="repo_profiles/history"
        )

        history_kb_full_path = save_history_knowledge_base_full(
            history_kb_full
        )

        print(f"历史项目数量：{history_kb_full.get('profile_count')}")

        if history_kb_full.get("profile_count", 0) == 0:
            print("警告：full 历史知识库为空，后续相似项目检索结果可能为空。")

        execution_status["history_kb_full"] = "rebuilt"
        upstream_rebuilt = True

    require_file(history_kb_full_path, "full 历史知识库")

    generated_files["history_kb_full_path"] = history_kb_full_path

    print(f"full 历史知识库：{history_kb_full_path}")

    # 3. 检索相似历史项目
    print()
    print("步骤 3/6：相似历史项目检索 retrieve_full")

    retrieval_result_path = expected_paths["retrieval_result_full_path"]

    retrieval_cache_ok = is_retrieval_cache_usable(
        retrieval_path=retrieval_result_path,
        repo_name=repo_name,
        top_k=top_k
    )

    if (
        use_cache
        and not force_rebuild
        and not upstream_rebuilt
        and retrieval_cache_ok
    ):
        print_cache_hit("retrieve_full 相似项目检索结果", retrieval_result_path)
        execution_status["retrieve_full"] = "skipped_by_cache"
    else:
        print_cache_miss("retrieve_full 相似项目检索结果")

        retrieval_result = retrieve_similar_history_projects_full(
            target_profile_path=repo_profile_full_path,
            history_kb_full_path=history_kb_full_path,
            top_k=top_k
        )

        retrieval_result_path = save_retrieval_result_full(
            retrieval_result
        )

        print(f"候选历史项目数量：{retrieval_result.get('candidate_count')}")
        print(f"返回结果数量：{len(retrieval_result.get('results', []))}")

        execution_status["retrieve_full"] = "rebuilt"
        upstream_rebuilt = True

    require_file(retrieval_result_path, "retrieve_full 相似项目检索结果")

    generated_files["retrieval_result_full_path"] = retrieval_result_path

    print(f"相似历史项目检索结果：{retrieval_result_path}")

    # 4. AI 历史项目对比
    print()
    print("步骤 4/6：AI 历史项目对比 compare_full")

    comparison_result_path = expected_paths["history_comparison_full_path"]

    if (
        use_cache
        and not force_rebuild
        and not upstream_rebuilt
        and can_use_file_cache(comparison_result_path)
    ):
        print_cache_hit("compare_full AI 历史项目对比结果", comparison_result_path)
        execution_status["compare_full"] = "skipped_by_cache"
    else:
        print_cache_miss("compare_full AI 历史项目对比结果")

        comparison_result = compare_retrieval_results_with_ai(
            retrieval_result_path=retrieval_result_path,
            ask_ai_once=ask_ai_once
        )

        comparison_result_path = save_history_comparison_full(
            comparison_result
        )

        print(f"对比项目数量：{comparison_result.get('comparison_count')}")

        execution_status["compare_full"] = "rebuilt"
        upstream_rebuilt = True

    require_file(comparison_result_path, "compare_full AI 历史项目对比结果")

    generated_files["history_comparison_full_path"] = comparison_result_path

    print(f"AI 历史项目对比结果：{comparison_result_path}")

    # 5. 结构化评分
    print()
    print("步骤 5/6：full 结构化评分 score_full")

    score_result_path = expected_paths["score_full_path"]

    if (
        use_cache
        and not force_rebuild
        and not upstream_rebuilt
        and can_use_file_cache(score_result_path)
    ):
        print_cache_hit("score_full 结构化评分结果", score_result_path)
        execution_status["score_full"] = "skipped_by_cache"
    else:
        print_cache_miss("score_full 结构化评分结果")

        score_result = evaluate_project_score_full(
            repo_profile_path=repo_profile_full_path,
            retrieval_result_path=retrieval_result_path,
            comparison_result_path=comparison_result_path,
            ask_ai_once=ask_ai_once
        )

        score_result_path = save_score_result_full(
            score_result
        )

        evaluation = score_result.get("evaluation", {})

        print(f"总分：{evaluation.get('overall_score')}")
        print(f"等级：{evaluation.get('score_level')}")

        execution_status["score_full"] = "rebuilt"
        upstream_rebuilt = True

    require_file(score_result_path, "score_full 结构化评分结果")

    generated_files["score_full_path"] = score_result_path

    print(f"结构化评分结果：{score_result_path}")

    # 6. 最终 Markdown 报告
    print()
    print("步骤 6/6：最终 Markdown 报告 final_report")

    final_report_path = expected_paths["final_report_path"]

    if (
        use_cache
        and not force_rebuild
        and not upstream_rebuilt
        and can_use_file_cache(final_report_path)
    ):
        print_cache_hit("final_report 最终 Markdown 报告", final_report_path)
        execution_status["final_report"] = "skipped_by_cache"
    else:
        print_cache_miss("final_report 最终 Markdown 报告")

        final_report_result = generate_final_report_full(
            repo_profile_path=repo_profile_full_path,
            retrieval_result_path=retrieval_result_path,
            comparison_result_path=comparison_result_path,
            score_result_path=score_result_path,
            ask_ai_once=ask_ai_once
        )

        final_report_path = save_final_report_full(
            final_report_result
        )

        execution_status["final_report"] = "rebuilt"

    require_file(final_report_path, "final_report 最终 Markdown 报告")

    generated_files["final_report_path"] = final_report_path

    print(f"最终 Markdown 报告：{final_report_path}")

    generated_files["execution_status"] = execution_status

    print()
    print("=" * 70)
    print("final_analyze v3.6 一键完整分析流程完成")
    print("=" * 70)

    return generated_files


def format_final_analyze_preview(generated_files):
    """
    生成 final_analyze 结果预览。
    """

    output = []

    output.append("final_analyze 一键完整分析完成。")
    output.append("")
    output.append(f"仓库名称：{generated_files.get('repo_name')}")
    output.append(f"分析模式：{generated_files.get('analysis_mode')}")
    output.append(f"max_blocks：{generated_files.get('max_blocks')}")
    output.append(f"top_k：{generated_files.get('top_k')}")
    output.append(f"启用缓存：{generated_files.get('use_cache')}")
    output.append(f"强制重跑：{generated_files.get('force_rebuild')}")
    output.append("")

    output.append("执行状态：")

    execution_status = generated_files.get("execution_status", {})

    if execution_status:
        for key, value in execution_status.items():
            output.append(f"- {key}: {value}")
    else:
        output.append("- 暂无执行状态。")

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

def run_final_analyze_hybrid_pipeline(
    repo_path,
    ask_ai_once,
    analysis_mode="full",
    max_blocks=100,
    max_workers=8,
    top_k=3,
    rag_top_k=10,
    final_top_k=5,
    structured_weight=0.65,
    semantic_weight=0.35,
    embedding_backend="hash",
    embedding_model_name="",
    device="cpu",
    force_rebuild_vector_store=True
):
    """
    一键执行 Hybrid 增强完整分析流程。

    流程：
    1. 分析目标仓库，生成 repo_profile_full
    2. 构建 full 历史知识库
    3. retrieve_full 结构相似检索
    4. 构建 RAG 文档
    5. 构建 Chroma 向量库
    6. hybrid_retrieve 融合检索
    7. compare_full AI 历史项目对比
    8. score_full 五维评分
    9. final_report 最终 Markdown 报告
    """

    generated_files = {}

    print()
    print("=" * 70)
    print("开始 final_analyze_hybrid 一键完整分析流程")
    print("=" * 70)
    print(f"目标仓库路径：{repo_path}")
    print(f"分析模式：{analysis_mode}")
    print(f"AI 分析代码块数量：{max_blocks if max_blocks is not None else 'all'}")
    print(f"结构检索 Top-K：{top_k}")
    print(f"RAG Top-K：{rag_top_k}")
    print(f"最终 Hybrid Top-K：{final_top_k}")
    print(f"结构权重：{structured_weight}")
    print(f"语义权重：{semantic_weight}")
    print(f"Embedding backend：{embedding_backend}")
    print("=" * 70)

    # 1. 分析目标仓库
    print()
    print("步骤 1/9：正在分析目标仓库...")

    analysis_files = analyze_target_repo(
        repo_path=repo_path,
        ask_ai_once=ask_ai_once,
        max_blocks=max_blocks,
        analysis_mode=analysis_mode,
        max_workers=max_workers
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
    print("步骤 2/9：正在更新 full 历史知识库...")

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
        print("警告：full 历史知识库为空，后续检索结果可能为空。")

    # 3. retrieve_full 结构检索
    print()
    print("步骤 3/9：正在进行 retrieve_full 结构相似检索...")

    retrieval_result = retrieve_similar_history_projects_full(
        target_profile_path=repo_profile_full_path,
        history_kb_full_path=history_kb_full_path,
        top_k=top_k
    )

    retrieval_result_path = save_retrieval_result_full(
        retrieval_result
    )

    generated_files["retrieval_result_full_path"] = retrieval_result_path

    print(f"结构检索结果：{retrieval_result_path}")
    print(f"候选历史项目数量：{retrieval_result.get('candidate_count')}")
    print(f"返回结果数量：{len(retrieval_result.get('results', []))}")

    # 4. 构建 RAG 文档
    print()
    print("步骤 4/9：正在构建历史项目 RAG 文档...")

    rag_result = build_history_rag_documents(
        history_kb_path=history_kb_full_path
    )

    rag_docs_json_path = save_history_rag_documents(
        rag_result
    )

    rag_docs_md_path = save_history_rag_documents_markdown(
        rag_result
    )

    generated_files["rag_docs_json_path"] = rag_docs_json_path
    generated_files["rag_docs_markdown_path"] = rag_docs_md_path

    print(f"RAG 文档 JSON：{rag_docs_json_path}")
    print(f"RAG 文档预览：{rag_docs_md_path}")
    print(f"RAG 文档数量：{rag_result.get('document_count')}")

    # 5. 构建 Chroma 向量库
    print()
    print("步骤 5/9：正在构建 Chroma 向量库...")

    vector_store_result = build_chroma_vector_store(
        rag_docs_path=rag_docs_json_path,
        persist_directory="vector_store/chroma_history",
        collection_name="os_history_projects",
        force_rebuild=force_rebuild_vector_store,
        embedding_backend=embedding_backend,
        embedding_model_name=embedding_model_name,
        device=device
    )

    generated_files["vector_store_path"] = vector_store_result.get("persist_directory")
    generated_files["embedding_config_path"] = vector_store_result.get("embedding_config_path")

    print(f"向量库目录：{vector_store_result.get('persist_directory')}")
    print(f"Embedding 模型：{vector_store_result.get('embedding_model')}")
    print(f"向量库状态：{vector_store_result.get('status')}")

    # 6. hybrid_retrieve 融合检索
    print()
    print("步骤 6/9：正在进行 hybrid_retrieve 融合检索...")

    hybrid_result = run_hybrid_retrieve(
        target_repo_profile_path=repo_profile_full_path,
        structured_result_path=retrieval_result_path,
        rag_query=None,
        persist_directory="vector_store/chroma_history",
        collection_name="os_history_projects",
        structured_weight=structured_weight,
        semantic_weight=semantic_weight,
        rag_top_k=rag_top_k,
        final_top_k=final_top_k
    )

    hybrid_result_path = hybrid_result.get("save_json_path")
    hybrid_report_path = hybrid_result.get("save_markdown_path")

    require_file(
        hybrid_result_path,
        "hybrid_retrieve 融合检索结果"
    )

    generated_files["hybrid_retrieval_full_path"] = hybrid_result_path
    generated_files["hybrid_retrieval_report_path"] = hybrid_report_path

    print(f"Hybrid 检索结果：{hybrid_result_path}")
    print(f"Hybrid 检索报告：{hybrid_report_path}")

    # 7. AI 历史项目对比解释
    print()
    print("步骤 7/9：正在基于 hybrid 结果进行 AI 历史项目对比解释...")

    comparison_result = compare_retrieval_results_with_ai(
        retrieval_result_path=hybrid_result_path,
        ask_ai_once=ask_ai_once
    )

    comparison_result_path = save_history_comparison_full(
        comparison_result
    )

    generated_files["history_comparison_full_path"] = comparison_result_path

    print(f"AI 历史项目对比结果：{comparison_result_path}")
    print(f"检索模式：{comparison_result.get('retrieval_mode')}")
    print(f"对比项目数量：{comparison_result.get('comparison_count')}")

    # 8. 结构化评分
    print()
    print("步骤 8/9：正在生成 hybrid 增强五维评分...")

    score_result = evaluate_project_score_full(
        repo_profile_path=repo_profile_full_path,
        retrieval_result_path=hybrid_result_path,
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

    # 9. 最终 Markdown 报告
    print()
    print("步骤 9/9：正在生成 hybrid 增强最终 Markdown 报告...")

    final_report_result = generate_final_report_full(
        repo_profile_path=repo_profile_full_path,
        retrieval_result_path=hybrid_result_path,
        comparison_result_path=comparison_result_path,
        score_result_path=score_result_path,
        ask_ai_once=ask_ai_once
    )

    final_report_path = save_final_report_full(
        final_report_result
    )

    generated_files["final_report_path"] = final_report_path

    print(f"最终 Markdown 报告：{final_report_path}")

    print()
    print("=" * 70)
    print("final_analyze_hybrid 一键完整分析流程完成")
    print("=" * 70)

    return generated_files


def format_final_analyze_hybrid_preview(generated_files):
    """
    生成 final_analyze_hybrid 结果预览。
    """

    output = []

    output.append("final_analyze_hybrid 一键完整分析完成。")
    output.append("")
    output.append("生成文件：")

    key_order = [
        "repo_profile_full_path",
        "history_kb_full_path",
        "retrieval_result_full_path",
        "rag_docs_json_path",
        "rag_docs_markdown_path",
        "vector_store_path",
        "embedding_config_path",
        "hybrid_retrieval_full_path",
        "hybrid_retrieval_report_path",
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