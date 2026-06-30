import os

from src.repo_reader import build_file_tree
from src.file_reader import collect_important_files, format_file_scores
from src.code_splitter import collect_code_blocks_from_scored_files, collect_all_code_blocks
from src.code_block_store import save_code_blocks
from src.code_understander import analyze_code_blocks_file,analyze_code_blocks_file_concurrent,save_function_analysis
from src.call_graph_builder import build_enhanced_call_graph,build_full_call_graph,save_call_graph
from src.module_summarizer import summarize_modules,save_module_summary,build_module_profile_from_call_graph,save_module_summary_full
from src.repo_profiler import build_repo_profile,save_repo_profile,build_repo_profile_full,save_repo_profile_full
from src.history_kb_builder import build_history_knowledge_base,save_history_knowledge_base,build_history_knowledge_base_full,save_history_knowledge_base_full


def get_repo_name(repo_path):
    """
    从仓库路径中提取仓库名称。
    """
    repo_path = os.path.normpath(repo_path)
    return os.path.basename(repo_path)

def resolve_ai_block_budget(total_blocks, max_blocks, profile_type="history", analysis_mode="full"):
    """
    根据仓库代码块总量，动态决定 AI 实际分析多少个代码块。

    max_blocks:
    - None: 全量 AI 分析
    - "auto": 动态预算
    - int: 固定分析数量

    设计目标：
    - 小仓库尽量全量，避免漏掉核心逻辑。
    - 中型仓库保证足够覆盖核心 OS 模块。
    - 大型仓库按比例增加预算，避免 5000 个代码块仍只分析 1000 个。

    典型效果：
    - 3000 个代码块：约分析 1200 个
    - 5000 个代码块：约分析 3000 个
    """

    try:
        total_blocks = int(total_blocks)
    except Exception:
        total_blocks = 0

    if total_blocks <= 0:
        return 0, "empty"

    # 深度最终 / 手动 all：真正全量。
    if max_blocks is None:
        return total_blocks, "all"

    # 手动固定数字：尊重用户输入。
    if isinstance(max_blocks, int):
        return min(total_blocks, max_blocks), "fixed"

    text = str(max_blocks).strip().lower()

    if text in {"all", "full", "none", "全部", "全量"}:
        return total_blocks, "all"

    if text not in {"auto", "dynamic", "正式", "正式入库"}:
        try:
            value = int(text)
            return min(total_blocks, value), "fixed"
        except Exception:
            pass

    # auto 动态预算：正式入库默认走这里。
    if total_blocks <= 800:
        budget = total_blocks
    elif total_blocks <= 1500:
        budget = max(800, int(total_blocks * 0.75))
    elif total_blocks <= 3000:
        # 3000 个代码块约分析 1200 个。
        budget = max(1000, int(total_blocks * 0.40))
    elif total_blocks <= 5000:
        # 5000 个代码块约分析 3000 个。
        budget = int(total_blocks * 0.60)
    elif total_blocks <= 8000:
        budget = int(total_blocks * 0.55)
    else:
        # 超大仓库仍给较高预算，但防止正式入库无限拖慢。
        budget = min(8000, int(total_blocks * 0.50))

    budget = max(1, min(total_blocks, budget))
    return budget, "auto"


def format_budget_value(value):
    if value is None:
        return "all"
    return str(value)


def run_repo_analysis_pipeline(
    repo_path,
    ask_ai_once,
    max_blocks="auto",
    profile_type="history",
    analysis_mode="quick",
    max_workers=8
):
    """
    一键分析一个仓库。

    这个函数只负责生成：
    1. code_blocks
    2. function_analysis
    3. call_graph
    4. module_summary
    5. repo_profile

    它不会更新历史知识库。
    """

    repo_name = get_repo_name(repo_path)

    generated_files = {}
    generated_files["analysis_mode"] = analysis_mode

    print()
    print(f"开始分析仓库：{repo_name}")
    print(f"仓库路径：{repo_path}")
    print("-" * 60)

    # 1. 代码切片
    if analysis_mode == "full":
        print("步骤 1/5：正在进行 full 模式全仓库代码切片...")
        print("说明：full 模式会先收集全仓代码块，再由动态预算决定 AI 实际分析数量。")

        blocks = collect_all_code_blocks(
            repo_path=repo_path,
            max_blocks=None
        )
    else:
        print("步骤 1/5：正在进行 quick 模式高分文件优先代码切片...")

        blocks = collect_code_blocks_from_scored_files(
            repo_path=repo_path,
            max_files=30,
            max_blocks=200
        )

    code_blocks_path = save_code_blocks(
        repo_path=repo_path,
        blocks=blocks
    )

    generated_files["code_blocks_path"] = code_blocks_path

    total_code_blocks = len(blocks)
    ai_max_blocks, budget_mode = resolve_ai_block_budget(
        total_blocks=total_code_blocks,
        max_blocks=max_blocks,
        profile_type=profile_type,
        analysis_mode=analysis_mode
    )

    generated_files["total_code_blocks"] = total_code_blocks
    generated_files["requested_max_blocks"] = format_budget_value(max_blocks)
    generated_files["resolved_ai_max_blocks"] = ai_max_blocks
    generated_files["budget_mode"] = budget_mode
    generated_files["max_workers"] = max_workers

    print(f"代码切片完成，代码块数量：{total_code_blocks}")
    print(f"保存路径：{code_blocks_path}")
    print(f"AI 分析预算模式：{budget_mode}")
    print(f"AI 实际计划分析数量：{ai_max_blocks}/{total_code_blocks}")

    # 2. AI 函数级理解
    print()
    print("步骤 2/5：正在进行 AI 函数级代码理解...")

    repo_name_from_blocks, analysis_results = analyze_code_blocks_file_concurrent(
        blocks_file_path=code_blocks_path,
        ask_ai_once=ask_ai_once,
        max_blocks=ai_max_blocks,
        resume=True,
        save_every=25,
        max_workers=max_workers
    )

    if budget_mode == "all":
        function_suffix = "function_analysis_full"
    else:
        function_suffix = "function_analysis"

    function_analysis_path = save_function_analysis(
        repo_name=repo_name_from_blocks,
        analysis_results=analysis_results,
        suffix=function_suffix
    )

    generated_files["function_analysis_path"] = function_analysis_path

    print(f"函数理解完成，分析函数数量：{len(analysis_results)}")
    print(f"保存路径：{function_analysis_path}")

    # 3. 增强调用图
    print()
    print("步骤 3/5：正在生成增强版函数调用关系图...")

    if budget_mode == "all":
        print("正在生成 full 版本函数调用关系图...")

        call_graph = build_full_call_graph(
            function_analysis_path=function_analysis_path,
            code_blocks_path=code_blocks_path
        )

        call_graph_path = save_call_graph(
            call_graph=call_graph,
            graph_type="full"
        )
    else:
        print("正在生成增强版函数调用关系图...")

        call_graph = build_full_call_graph(
            function_analysis_path=function_analysis_path,
            code_blocks_path=code_blocks_path
        )

        call_graph_path = save_call_graph(
            call_graph=call_graph,
            enhanced=True
        )

    generated_files["call_graph_path"] = call_graph_path

    print(f"调用图生成完成，节点数量：{call_graph.get('node_count')}")
    print(f"调用图生成完成，调用边数量：{call_graph.get('merged_edge_count')}")
    print(f"内部调用边数量：{call_graph.get('internal_edge_count')}")
    print(f"外部调用边数量：{call_graph.get('external_edge_count')}")
    print(f"保存路径：{call_graph_path}")

    # 4. 模块逻辑总结
    print()
    print("步骤 4/5：正在生成模块逻辑总结...")

    module_summary = summarize_modules(
        function_analysis_path=function_analysis_path,
        call_graph_path=call_graph_path,
        ask_ai_once=ask_ai_once,
        max_modules=8
    )

    module_summary_path = save_module_summary(module_summary)

    generated_files["module_summary_path"] = module_summary_path

    print(f"模块总结完成，模块数量：{module_summary.get('module_count')}")
    print(f"保存路径：{module_summary_path}")

    print()
    print("步骤 4.1/5：正在生成 full 结构化模块画像...")

    module_summary_full = build_module_profile_from_call_graph(call_graph)

    module_summary_full_path = save_module_summary_full(module_summary_full)

    generated_files["module_summary_full_path"] = module_summary_full_path

    print(f"full 模块画像生成完成，模块数量：{module_summary_full.get('module_count')}")
    print(f"保存路径：{module_summary_full_path}")

    print()
    print("步骤 4.2/5：正在生成 full 仓库画像...")

    repo_profile_full = build_repo_profile_full(
        repo_name=repo_name_from_blocks,
        call_graph=call_graph,
        module_summary_full=module_summary_full,
        profile_type=profile_type
    )

    repo_profile_full_path = save_repo_profile_full(
        profile=repo_profile_full,
        profile_type=profile_type
    )

    generated_files["repo_profile_full_path"] = repo_profile_full_path

    print(f"full 仓库画像生成完成：{repo_profile_full_path}")
    print(f"项目类型：{repo_profile_full.get('project_type')}")
    print(f"核心模块：{repo_profile_full.get('core_modules')}")
    print(f"结构复杂度：{repo_profile_full.get('structure_complexity')}")


    # 5. 仓库画像
    print()
    print("步骤 5/5：正在生成仓库画像 repo_profile...")

    file_tree = build_file_tree(repo_path)

    important_files = collect_important_files(repo_path)
    file_scores = format_file_scores(important_files)

    profile = build_repo_profile(
        repo_path=repo_path,
        file_tree=file_tree,
        file_scores=file_scores,
        function_analysis_path=function_analysis_path,
        call_graph_path=call_graph_path,
        module_summary_path=module_summary_path
    )

    repo_profile_path = save_repo_profile(
        profile,
        profile_type=profile_type
    )

    generated_files["repo_profile_path"] = repo_profile_path

    print("仓库画像生成完成。")
    print(f"保存路径：{repo_profile_path}")

    print()
    print("仓库分析流水线完成。")
    print("-" * 60)

    return generated_files


def ingest_history_repo(repo_path, ask_ai_once, max_blocks="auto", analysis_mode="full", max_workers=8):
    """
    一键入库历史仓库。

    流程：
    分析仓库
    2生成 repo_profile
    3更新 history_knowledge_base/history_profiles.json
    4更新 history_knowledge_base/history_profiles_full.json
    """

    generated_files = run_repo_analysis_pipeline(
        repo_path=repo_path,
        ask_ai_once=ask_ai_once,
        max_blocks=max_blocks,
        profile_type="history",
        analysis_mode=analysis_mode,
        max_workers=max_workers
    )

    print()
    print("正在更新历史作品知识库...")

    knowledge_base = build_history_knowledge_base(
        profile_dir="repo_profiles/history"
    )

    history_kb_path = save_history_knowledge_base(knowledge_base)

    generated_files["history_kb_path"] = history_kb_path

    print("历史作品知识库更新完成。")
    print(f"保存路径：{history_kb_path}")


    print()
    print("正在更新 full 历史作品知识库...")

    history_kb_full = build_history_knowledge_base_full(
        profile_dir="repo_profiles/history"
    )

    history_kb_full_path = save_history_knowledge_base_full(history_kb_full)

    generated_files["history_kb_full_path"] = history_kb_full_path

    print("full 历史作品知识库更新完成。")
    print(f"保存路径：{history_kb_full_path}")
    print(f"full 历史项目数量：{history_kb_full.get('profile_count')}")

    return generated_files


def analyze_target_repo(repo_path, ask_ai_once, max_blocks="auto", analysis_mode="full", max_workers=8):
    """
    一键分析新提交仓库。

    这个函数不会更新历史知识库。
    """

    generated_files = run_repo_analysis_pipeline(
        repo_path=repo_path,
        ask_ai_once=ask_ai_once,
        max_blocks=max_blocks,
        profile_type="target",
        analysis_mode=analysis_mode,
        max_workers=max_workers
    )

    return generated_files


def format_pipeline_result(title, generated_files):
    """
    整理流水线结果，方便终端打印。
    """

    output = []

    output.append(title)
    output.append("")
    output.append("生成文件如下：")

    for key, value in generated_files.items():
        output.append(f"- {key}: {value}")

    return "\n".join(output)