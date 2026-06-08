import os

from src.repo_reader import build_file_tree
from src.file_reader import collect_important_files, format_file_scores
from src.code_splitter import collect_code_blocks_from_scored_files, collect_all_code_blocks
from src.code_block_store import save_code_blocks
from src.code_understander import analyze_code_blocks_file, save_function_analysis
from src.call_graph_builder import build_enhanced_call_graph, save_call_graph
from src.module_summarizer import summarize_modules, save_module_summary
from src.repo_profiler import build_repo_profile, save_repo_profile
from src.history_kb_builder import build_history_knowledge_base, save_history_knowledge_base


def get_repo_name(repo_path):
    """
    从仓库路径中提取仓库名称。
    """
    repo_path = os.path.normpath(repo_path)
    return os.path.basename(repo_path)


def run_repo_analysis_pipeline(
    repo_path,
    ask_ai_once,
    max_blocks=20,
    profile_type="history",
    analysis_mode="quick"
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

        blocks = collect_all_code_blocks(
            repo_path=repo_path,
            max_blocks=5000
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

    print(f"代码切片完成，代码块数量：{len(blocks)}")
    print(f"保存路径：{code_blocks_path}")

    # 2. AI 函数级理解
    print()
    print("步骤 2/5：正在进行 AI 函数级代码理解...")

    repo_name_from_blocks, analysis_results = analyze_code_blocks_file(
        blocks_file_path=code_blocks_path,
        ask_ai_once=ask_ai_once,
        max_blocks=max_blocks
    )

    function_analysis_path = save_function_analysis(
        repo_name=repo_name_from_blocks,
        analysis_results=analysis_results
    )

    generated_files["function_analysis_path"] = function_analysis_path

    print(f"函数理解完成，分析函数数量：{len(analysis_results)}")
    print(f"保存路径：{function_analysis_path}")

    # 3. 增强调用图
    print()
    print("步骤 3/5：正在生成增强版函数调用关系图...")

    call_graph = build_enhanced_call_graph(
        function_analysis_path=function_analysis_path,
        code_blocks_path=code_blocks_path
    )

    call_graph_path = save_call_graph(
        call_graph=call_graph,
        enhanced=True
    )

    generated_files["call_graph_path"] = call_graph_path

    print(f"调用图生成完成，调用边数量：{call_graph.get('merged_edge_count')}")
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


def ingest_history_repo(repo_path, ask_ai_once, max_blocks=20, analysis_mode="quick"):
    """
    一键入库历史仓库。

    流程：
    1. 分析仓库
    2. 生成 repo_profile
    3. 更新 history_knowledge_base/history_profiles.json
    """

    generated_files = run_repo_analysis_pipeline(
    repo_path=repo_path,
    ask_ai_once=ask_ai_once,
    max_blocks=max_blocks,
    profile_type="history",
    analysis_mode=analysis_mode
    )

    print()
    print("正在更新历史作品知识库...")

    knowledge_base = build_history_knowledge_base(profile_dir="repo_profiles/history")
    history_kb_path = save_history_knowledge_base(knowledge_base)

    generated_files["history_kb_path"] = history_kb_path

    print("历史作品知识库更新完成。")
    print(f"保存路径：{history_kb_path}")

    return generated_files


def analyze_target_repo(repo_path, ask_ai_once, max_blocks=20, analysis_mode="quick"):
    """
    一键分析新提交仓库。

    这个函数不会更新历史知识库。
    """

    generated_files = run_repo_analysis_pipeline(
    repo_path=repo_path,
    ask_ai_once=ask_ai_once,
    max_blocks=max_blocks,
    profile_type="target",
    analysis_mode=analysis_mode
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