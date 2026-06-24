import os
from openai import OpenAI
from dotenv import load_dotenv
from src.repo_reader import build_file_tree
from src.file_reader import collect_important_files, format_files_content, format_file_scores
from src.report_writer import save_markdown_report, save_comparison_report
from src.batch_analyzer import find_repos_in_folder, format_batch_summary
from src.comparator import find_history_description_reports, format_history_reports, read_markdown_file
from src.code_splitter import collect_code_blocks, collect_code_blocks_from_scored_files, format_code_blocks
from src.code_block_store import save_code_blocks, format_block_save_summary
from src.code_understander import analyze_code_blocks_file, save_function_analysis, format_function_analysis_summary
from src.call_graph_builder import build_enhanced_call_graph, save_call_graph, format_call_graph_summary
from src.module_summarizer import summarize_modules, save_module_summary, format_module_summary_preview
from src.repo_profiler import build_repo_profile, save_repo_profile, format_repo_profile_preview
from src.history_kb_builder import build_history_knowledge_base,save_history_knowledge_base,build_history_knowledge_base_full,save_history_knowledge_base_full,format_history_kb_full_preview
from src.history_retriever import retrieve_similar_history_profiles,retrieve_similar_history_projects_full,save_retrieval_result_full,format_retrieval_result_full_preview
from src.evaluator import generate_evaluation_report, save_evaluation_report, format_evaluation_preview
from src.ingest_pipeline import ingest_history_repo, analyze_target_repo, format_pipeline_result
from src.history_comparator import compare_retrieval_results_with_ai,save_history_comparison_full,format_history_comparison_full_preview
from src.score_evaluator import evaluate_project_score_full,save_score_result_full,format_score_result_full_preview
from src.final_report_generator import generate_final_report_full,save_final_report_full,format_final_report_preview
from src.final_pipeline import run_final_analyze_pipeline,format_final_analyze_preview,run_final_analyze_hybrid_pipeline,format_final_analyze_hybrid_preview
from src.path_resolver import resolve_final_report_paths,format_resolved_paths_preview
from src.history_batch_ingestor import run_batch_ingest_history,format_batch_ingest_history_preview
from src.history_kb_reporter import generate_history_kb_report,save_history_kb_report,format_history_kb_report_preview
from src.rag_document_builder import build_history_rag_documents,save_history_rag_documents,save_history_rag_documents_markdown,format_history_rag_documents_preview
from src.rag_vector_store import build_chroma_vector_store,rag_retrieve_history,save_rag_retrieval_result,format_vector_store_build_preview,format_rag_retrieval_preview
from src.hybrid_retriever import run_hybrid_retrieve,format_hybrid_retrieval_preview


#读取.env文件
load_dotenv()

#读取.env中的DEEPSEEK_API_KEY
api_key = os.getenv("DEEPSEEK_API_KEY")

if api_key is None:
    print("api获取错误，检查.env文件")
    exit()

#创建deepseek客户端
client=OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

#创建保存对话记录的地点
messages = [
    {
        "role":"system",
        "content":"你是一个帮助新手理解代码仓库和操作系统比赛项目的AI助手,回答的时候要清楚简单"
    }
]

VERSION_NAME = "v3.9 - 主菜单工程化版"


MAIN_COMMANDS = {
    "ingest_history": "入库历史仓库，生成历史项目 repo_profile_full，并保存到 repo_profiles/history",
    "batch_ingest_history": "批量入库历史仓库，并自动重建 full 历史知识库",
    "analyze_target": "分析目标仓库，生成 code_blocks、function_analysis、call_graph、module_summary 和 repo_profile_full",
    "history_kb_full": "根据 repo_profiles/history 构建 full 历史知识库",
    "history_kb_report": "生成历史知识库统计报告，展示历史库规模、类型、语言和模块覆盖情况",
    "build_rag_docs": "将 full 历史知识库转换为标准 RAG 文档，为后续 LangChain/向量库做准备",
    "build_vector_store": "将 RAG 文档写入 Chroma 向量库",
    "hybrid_retrieve": "融合 retrieve_full 结构检索和 RAG 语义检索，生成综合相似历史项目",
    "rag_retrieve": "基于 Chroma 向量库进行历史项目语义检索",
    "retrieve_full": "基于 repo_profile_full 检索相似历史项目",
    "compare_full": "对目标项目和相似历史项目进行 AI 对比分析",
    "score_full": "基于仓库画像、历史检索和 AI 对比结果进行五维评分",
    "final_report": "整合所有结果生成最终 Markdown 报告",
    "final_analyze": "一键执行目标分析、历史检索、AI 对比、评分和报告生成",
    "final_analyze_hybrid": "一键执行结构分析、RAG 构建、Hybrid 检索、AI 对比、评分和最终报告"
}


DEBUG_COMMANDS = {
    "save_blocks": "单独执行代码切块并保存 code_blocks",
    "understand": "单独让 AI 理解已有代码块",
    "call_graph": "单独根据函数理解结果构建调用图",
    "module_summary": "单独生成模块总结",
    "profile": "单独生成旧版 repo_profile",
}


LEGACY_COMMANDS = {
    "chat": "早期普通聊天功能，不属于当前 OS 分析主流程",
    "repo": "早期单仓库 AI 分析功能，已被 analyze_target 替代",
    "report": "早期单仓库描述报告，已被 final_report 替代",
    "batch": "早期批量生成描述报告，已被 ingest_history 流程替代",
    "compare": "早期 Markdown 报告对比，已被 retrieve_full + compare_full 替代",
    "split": "早期代码切块预览命令，当前建议使用 save_blocks 或 analyze_target",
    "history_kb": "旧版历史知识库，已被 history_kb_full 替代",
    "retrieve": "旧版相似项目检索，已被 retrieve_full 替代",
    "evaluate": "旧版专项评分报告，已被 score_full + final_report 替代",
}


UTILITY_COMMANDS = {
    "help": "查看帮助菜单",
    "workflow": "查看推荐演示流程",
    "exit": "退出程序"
}


def print_command_menu():
    """
    打印简洁主菜单。
    """

    print("=" * 70)
    print(VERSION_NAME)
    print("=" * 70)
    print()
    print("【推荐主流程命令】")

    for command, description in MAIN_COMMANDS.items():
        print(f"  {command:<16} {description}")

    print()
    print("【辅助命令】")

    for command, description in UTILITY_COMMANDS.items():
        print(f"  {command:<16} {description}")

    print()
    print("如需查看调试命令或旧版命令，请输入：")
    print("  help debug")
    print("  help legacy")
    print("=" * 70)


def print_debug_commands():
    """
    打印调试命令。
    """

    print()
    print("【调试命令】")
    print("这些命令主要用于开发阶段单步测试，不是最终演示主线。")

    for command, description in DEBUG_COMMANDS.items():
        print(f"  {command:<16} {description}")

    print()


def print_legacy_commands():
    """
    打印旧版命令。
    """

    print()
    print("【旧版 legacy 命令】")
    print("这些命令是早期版本保留下来的功能，不建议作为当前主流程演示。")

    for command, description in LEGACY_COMMANDS.items():
        print(f"  {command:<16} {description}")

    print()


def print_workflow_guide():
    """
    打印推荐演示流程。
    """

    print()
    print("【推荐演示流程】")
    print()
    print("方式一：分步骤演示")
    print("  1. ingest_history   入库历史项目")
    print("  2. analyze_target   分析目标项目")
    print("  3. history_kb_full  构建 full 历史知识库")
    print("  4. retrieve_full    检索相似历史项目")
    print("  5. compare_full     AI 历史项目对比")
    print("  6. score_full       五维结构化评分")
    print("  7. final_report     生成最终 Markdown 报告")
    print()
    print("方式二：一键演示")
    print("  final_analyze")
    print()
    print("建议现场汇报时先讲分步骤逻辑，再用 final_analyze 说明系统已完成端到端闭环。")
    print()


def print_command_help(command=None):
    """
    打印命令帮助。
    """

    if command is None or command == "":
        print_command_menu()
        return

    command = command.strip()

    if command == "debug":
        print_debug_commands()
        return

    if command == "legacy":
        print_legacy_commands()
        return

    if command in MAIN_COMMANDS:
        print(f"{command}: {MAIN_COMMANDS[command]}")
        return

    if command in DEBUG_COMMANDS:
        print(f"{command}: {DEBUG_COMMANDS[command]}")
        return

    if command in LEGACY_COMMANDS:
        print(f"{command}: {LEGACY_COMMANDS[command]}")
        return

    if command in UTILITY_COMMANDS:
        print(f"{command}: {UTILITY_COMMANDS[command]}")
        return

    print(f"未知命令：{command}")


def is_known_command(command):
    """
    判断是否是已知命令。
    """

    return (
        command in MAIN_COMMANDS
        or command in DEBUG_COMMANDS
        or command in LEGACY_COMMANDS
        or command in UTILITY_COMMANDS
    )


def confirm_legacy_command(command):
    """
    旧版命令执行前确认。
    防止误用旧流程。
    """

    print()
    print(f"提示：{command} 是旧版 legacy 命令，不属于当前推荐主流程。")
    print(f"说明：{LEGACY_COMMANDS.get(command)}")
    confirm_text = input("是否仍然执行？y/n，直接回车默认 n: ")

    return confirm_text.strip().lower() in {"y", "yes", "1", "true"}


def chat_with_ai(user_input):
#函数用途：把用户的话发给DeepSeek

#加入对话历史
    messages.append(
        {
            "role":"user",
            "content":user_input
        }
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
#提取AI第一个回答
    ai_reply = response.choices[0].message.content
#把回答添加进对话信息
    messages.append(
        {
            "role":"assistant",
            "content":ai_reply
        }
    )
    return ai_reply


def ask_ai_once(prompt):
    """
    单次调用 AI。
    不保存上下文，适合生成报告、批量分析、对比分析。

    这样做的原因：
    报告内容通常很长，如果全部塞进 messages 历史记录里，
    后续请求会越来越长，容易超过上下文长度。
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的操作系统比赛作品分析助手。你的任务是基于代码材料生成准确、清楚、少幻觉的描述和比较报告。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        stream=False
    )

    return response.choices[0].message.content



def analyze_repo(repo_path):
    #读取本地的repo文件和关键文件的内容（有一定的优先度）

    file_tree = build_file_tree(repo_path)

    important_files = collect_important_files(repo_path)
    file_scores = format_file_scores(important_files)
    files_content = format_files_content(important_files)

    #AI提示词模块，首次接触加深学习
    prompt = f"""
下面是一个代码仓库的文件结构：
一、仓库的文件结构
{file_tree}

二、文件重要性评分结果：

{file_scores}

三、高评分关键文件内容：

{files_content}


请你认真的解释这个代码仓库结构和文件内容，认真分析这个代码仓库。
要求如下：
1. 说明这个仓库当前已经实现了什么功能；
2. 解释主要文件分别负责什么；
3. 分析程序的大致运行流程；
4. 指出当前实现的不足；
5. 给出下一步适合迭代的方向；
6. 回答要适合初学者理解，不要写得太抽象。
"""
    ai_reply = ask_ai_once(prompt)

    return file_tree,file_scores, files_content, ai_reply
     

def generate_repo_description(repo_path):
    """
    函数用途是生成单个os仓库的描述文档
    """

    file_tree = build_file_tree(repo_path)

    important_files = collect_important_files(repo_path)
    file_scores = format_file_scores(important_files)
    file_content = format_files_content(important_files)

    prompt = f"""
你先在要为一个操作系统比赛作品生成一份“人类友好的描述文档”

下面是该仓库的信息。

一、仓库文件的结构树：
{file_tree}

二、文件重要性评分结果：
{file_scores}

三、高评分关键文件：
{file_content}

请你生成一份Markdown格式的仓库描述报告。

标题为：
#os仓库描述报告

报告需包含一下几个部分：

##一、项目基本信息

说明这个项目是什么类型的项目。
若无法确定项目名称、编程语言或运行平台，请如实说明

##二、仓库结构概览

根据仓库文件树解释主要目录和文件的作用

##三、关键性文件分析

结合文件重要性评分，解释高分文件为什么重要。

##四、核心模块推测

从以下角度分析仓库可能包含哪些模块：

1.启动模块
2.内核初始化模块
3.内存管理模块
4.进程或人物管理模块
5.中断或异常处理模块
6.系统调用模块
7.文件系统或驱动模块
8.构建与运行模块

如果某些模块没有明显体现，请明确说明“当前仓库中未发现明显证据”

##五、程序运行流程推测

根据当前代码内容，推测项目的大致运行流程。
可以合理进行推测，不要过度编造，只能基于已有文件和代码进行合理推测。

##六、项目特点总结

总结这个os作品的特点、可能优势和当前完成度。

##七、当前不足与不确定的信息

说明当前分析可能存在的不确定性。例如读取文件数量有限、未运行项目、未完整分析全部代码等。

##八、后续比较建议
说明如果要和历史os作品比较，后续应该重点比较哪些维度。

输出要求：
1.面向评审和初学者，语言清楚；
2.不要写成普通聊天，要写成正式报告；
3.不要编造没有代码依据的内容；
4.遇到不确定内容要明确标注；
5.输出必须是完整的 Markdown 文档。
    """


    report_content = ask_ai_once(prompt)

    report_path = save_markdown_report(
        repo_path=repo_path,
        report_content=report_content,
        report_type="description"
    )

    return report_path,report_content



def batch_generate_history_reports(history_folder_path):
    """
    可以直接批量分析os作品文件夹
    这是非常令人激动的一步
    因为这是真正可以贴合赛题第一个要求的第一步
    现在是5.10一点十五分，版本v0.7
    """

    repo_paths = find_repos_in_folder(history_folder_path)

    results = []

    if not len(repo_paths):
        return results

    for repo_path in repo_paths:
        repo_name = os.path.basename(os.path.normpath(repo_path))

        print()
        print(f"正在分析历史仓库：{repo_name}")
        print(f"仓库路径：{repo_path}")

        report_path,report_content = generate_repo_description(repo_path)

        results.append(
            {
            "repo_name":repo_name,
            "repo_path":repo_path,
            "report_path":report_path
            }
        )

    return results



def generate_comparison_report(target_repo_path,reports_dir="reports"):
    """
    生成新提交作品与历史作品的对比报告

    流程
    1、先给新提交作品生成描述报告；
    2、再读取reports目录下已有的历史作品报告；
    3、让AI基于这些报告生成对比文档；
    4、保存对比报告
    """

    print("\n正在生成新提交作品的描述报告")
    target_report_path, target_report_content = generate_repo_description(target_repo_path)


    history_report_paths = find_history_description_reports(
        reports_dir = reports_dir,
        exclude_report_path=target_report_path
    )

    history_reports_content = format_history_reports(history_report_paths)

    prompt = f"""
你现在要完成操作系统比赛作品的 “新旧作品对比分析”

下面是新提交作品的描述报告：

{target_report_content}

下面是历史操作系统比赛作品的描述报告资料：

{history_reports_content}

请你基于以上内容，生成一份 Markdown 格式的“新提交作品与历史作品对比报告”。

报告标题请使用：
#os作品对比报告

报告必须包含一下部分：

##一、对比对象说明：

说明本次对比的新提交作品是什么，历史作品资料来自哪些报告。
如果历史报告数量不足，要明确说明。

##二、新提交作品概览

简要概括新提交作品的仓库结构、主要模块和当前完成度

##三、历史作品概览

总结历史作品中常见的结构特点、技术路线和核心模块。

##四、核心模块对比

请从一下维度进行对比：

1. 启动模块
2. 内核初始化模块
3. 内存管理模块
4. 进程或任务管理模块
5. 中断或异常处理模块
6. 系统调用模块
7. 文件系统或驱动模块
8. 构建与运行模块

要求：
1、如果新作品或历史作品某个模块证据不足，要明确说明。
2、不能把没有证据的内容写成确定的结论。

## 五、技术路线差异分析

比较新提交作品与历史作品在编程语言、目录组织、模块划分、构建方式上的差异。

## 六、完成度与复杂度对比

从代码结构完整性、模块覆盖范围、工程组织复杂度等角度进行比较。

## 七、可能创新点分析

分析新提交作品相比历史作品可能有哪些新特点或创新点。
如果无法判断创新点，要明确说明依据不足。

## 八、不确定信息与风险

说明本次对比的限制，例如：
1. 只读取了部分高评分文件；
2. 没有实际编译运行；
3. 历史作品描述报告数量有限；
4. 可能存在代码未被读取导致判断不完整。

## 九、总结评价

用简洁清楚的语言总结：
1. 新作品目前大致处在什么水平；
2. 和历史作品相比主要差异是什么；
3. 后续如果继续完善，应该重点补强哪些方面。

写作要求：
1. 面向评审和初学者；
2. 语言正式、清楚；
3. 尽量基于已有报告，不要凭空编造；
4. 对不确定内容必须明确标注；
5. 输出必须是完整 Markdown 文档。
"""
    comparison_content = ask_ai_once(prompt)

    comparison_report_path = save_comparison_report(
        target_repo_path=target_repo_path,
        report_content=comparison_content
    )

    return target_report_path, comparison_report_path, comparison_content


def split_and_save_repo_code(repo_path):
    """
    优先切分高分关键文件中的代码块，并保存成 JSON 文件。
    """

    blocks = collect_code_blocks_from_scored_files(repo_path)
    save_path = save_code_blocks(repo_path, blocks)
    summary = format_block_save_summary(repo_path, blocks, save_path)

    return blocks, save_path, summary

def understand_code_blocks(blocks_file_path):
    """
    让 AI 阅读代码块 JSON 文件，并生成函数级理解结果。
    """

    repo_name, analysis_results = analyze_code_blocks_file(
        blocks_file_path=blocks_file_path,
        ask_ai_once=ask_ai_once,
        max_blocks=10
    )

    save_path = save_function_analysis(repo_name, analysis_results)
    summary = format_function_analysis_summary(repo_name, analysis_results, save_path)

    return save_path, summary

def build_repo_call_graph(function_analysis_path, code_blocks_path):
    """
    根据函数级理解结果和原始代码块，生成增强版函数调用关系图。
    """

    call_graph = build_enhanced_call_graph(
        function_analysis_path=function_analysis_path,
        code_blocks_path=code_blocks_path
    )

    save_path = save_call_graph(call_graph, enhanced=True)
    summary = format_call_graph_summary(call_graph, save_path)

    return save_path, summary

def summarize_repo_modules(function_analysis_path, call_graph_path):
    """
    根据函数理解结果和增强调用图，生成模块逻辑总结。
    """

    module_summary = summarize_modules(
        function_analysis_path=function_analysis_path,
        call_graph_path=call_graph_path,
        ask_ai_once=ask_ai_once,
        max_modules=8
    )

    save_path = save_module_summary(module_summary)
    preview = format_module_summary_preview(module_summary, save_path)

    return save_path, preview

def generate_repo_profile(
    repo_path,
    function_analysis_path,
    call_graph_path,
    module_summary_path
):
    """
    整合文件树、文件评分、函数理解、调用图和模块总结，生成仓库画像。
    """

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

    save_path = save_repo_profile(profile)
    preview = format_repo_profile_preview(profile, save_path)

    return save_path, preview


def build_history_kb():
    """
    根据 repo_profiles 目录下的仓库画像，构建历史作品知识库。
    """

    knowledge_base = build_history_knowledge_base(profile_dir="repo_profiles/history")
    save_path = save_history_knowledge_base(knowledge_base)
    preview = format_history_kb_preview(knowledge_base, save_path)

    return save_path, preview

def retrieve_similar_history(target_profile_path, history_kb_path, top_k=5):
    """
    根据新作品 repo_profile，从历史知识库中筛选相似历史作品。
    """

    retrieval_result = retrieve_similar_history_profiles(
        target_profile_path=target_profile_path,
        history_kb_path=history_kb_path,
        top_k=top_k
    )

    preview = format_retrieval_results(retrieval_result)

    return retrieval_result, preview

def generate_special_evaluation_report(
    target_profile_path,
    history_kb_path,
    top_k=5
):
    """
    先检索相似历史作品，再生成专项对比评分报告。
    """

    retrieval_result, retrieval_preview = retrieve_similar_history(
        target_profile_path=target_profile_path,
        history_kb_path=history_kb_path,
        top_k=top_k
    )

    target_profile, history_profiles, report_content = generate_evaluation_report(
        target_profile_path=target_profile_path,
        retrieval_result=retrieval_result,
        ask_ai_once=ask_ai_once
    )

    save_path = save_evaluation_report(
        target_profile=target_profile,
        report_content=report_content
    )

    preview = format_evaluation_preview(
        target_profile=target_profile,
        history_profiles=history_profiles,
        save_path=save_path
    )

    return save_path, preview, report_content


def run_ingest_history(repo_path, max_blocks=20, analysis_mode="quick"):
    """
    一键入库历史仓库。
    """

    generated_files = ingest_history_repo(
        repo_path=repo_path,
        ask_ai_once=ask_ai_once,
        max_blocks=max_blocks,
        analysis_mode=analysis_mode
    )

    result_text = format_pipeline_result(
        title="历史仓库一键入库完成。",
        generated_files=generated_files
    )

    return generated_files, result_text

def run_analyze_target(repo_path, max_blocks=20, analysis_mode="quick"):
    """
    分析目标仓库
    - repo_path: 仓库路径
    - max_blocks: 最大分析代码块数
    - analysis_mode: quick/full
    """

    generated_files = analyze_target_repo(
    repo_path=repo_path,
    ask_ai_once=ask_ai_once,
    max_blocks=max_blocks,
    analysis_mode=analysis_mode
    )

    result_text = format_pipeline_result(
        title="新提交仓库一键分析完成。",
        generated_files=generated_files
    )

    return generated_files, result_text

def parse_max_blocks_input(max_blocks_text, default_value=20):
    """
    解析用户输入的 max_blocks。

    - 直接回车：返回默认值
    - all：返回 None，表示分析全部代码块
    - 数字：返回对应整数
    """

    text = max_blocks_text.strip().lower()

    if text == "":
        return default_value

    if text == "all":
        return None

    return int(text)

def main():

    print_command_menu()

    while True:
        command = input("请输入命令（help 查看菜单，workflow 查看演示流程，exit 退出）: ")
        command = command.strip()

        if command.startswith("help"):
            parts = command.split(maxsplit=1)

            if len(parts) == 1:
                print_command_help()
            else:
                print_command_help(parts[1])

            continue

        if command == "workflow":
            print_workflow_guide()
            continue

        if not is_known_command(command):
            print(f"未知命令：{command}")
            print("输入 help 查看可用命令。")
            continue

        if command in LEGACY_COMMANDS:
            if not confirm_legacy_command(command):
                print("已取消执行 legacy 命令。")
                continue

        if command == "exit":
            print("程序退出")
            break

        elif command == "chat":
            user_input = input("用户: ")
            ai_reply = chat_with_ai(user_input)

            print("AI:")
            print(ai_reply)
            print("-" * 30)

        elif command == "repo":
            repo_path = input("请输入本地仓库路径: ")

            file_tree, file_scores, files_content, ai_reply = analyze_repo(repo_path)

            print("\n仓库文件结构:")
            print(file_tree)

            print("\n文件重要性评分:")
            print(file_scores)

            print("\n关键文件内容:")
            print(files_content)

            print("\nAI 分析:")
            print(ai_reply)
            print("-" * 30)

        elif command == "report":
            repo_path = input("请输入本地仓库路径: ")

            report_path, report_content = generate_repo_description(repo_path)

            print("\n描述文档已生成:")
            print(report_path)

            print("\n报告内容预览:")
            print(report_content)
            print("-" * 30)

        elif command == "batch":
            history_folder_path = input("请输入历史作品总文件夹路径: ")

            results = batch_generate_history_reports(history_folder_path)
            summary = format_batch_summary(results)

            print("\n批量分析结果:")
            print(summary)
            print("-" * 30)

        elif command == "compare":
            target_repo_path = input("请输入新提交作品仓库路径: ")

            target_report_path, comparison_report_path, comparison_content = generate_comparison_report(
                target_repo_path=target_repo_path,
                reports_dir="reports"
            )

            print("\n新提交作品描述报告:")
            print(target_report_path)

            print("\n对比报告已生成:")
            print(comparison_report_path)

            print("\n对比报告内容预览:")
            print(comparison_content)
            print("-" * 30)

        elif command == "split":
            repo_path = input("请输入本地仓库路径: ")

            blocks, formatted_blocks = split_repo_code(repo_path)

            print(f"\n共提取到 {len(blocks)} 个代码块。")
            print("\n代码块预览:")
            print(formatted_blocks)
            print("-" * 30)

        elif command == "save_blocks":
            repo_path = input("请输入本地仓库路径: ")

            blocks, save_path, summary = split_and_save_repo_code(repo_path)

            print()
            print(summary)
            print("-" * 30)

        elif command == "understand":
            blocks_file_path = input("请输入代码块 JSON 文件路径: ")

            save_path, summary = understand_code_blocks(blocks_file_path)

            print()
            print(summary)
            print("-" * 30)

        elif command == "call_graph":
            function_analysis_path = input("请输入函数理解 JSON 文件路径: ")
            code_blocks_path = input("请输入代码块 JSON 文件路径: ")

            save_path, summary = build_repo_call_graph(
                function_analysis_path=function_analysis_path,
                code_blocks_path=code_blocks_path
            )

            print()
            print(summary)
            print("-" * 30)

        elif command == "module_summary":
            function_analysis_path = input("请输入函数理解 JSON 文件路径: ")
            call_graph_path = input("请输入增强调用图 JSON 文件路径: ")

            save_path, preview = summarize_repo_modules(
                function_analysis_path=function_analysis_path,
                call_graph_path=call_graph_path
            )

            print()
            print(preview)
            print("-" * 30)

        elif command == "profile":
            repo_path = input("请输入本地仓库路径: ")
            function_analysis_path = input("请输入函数理解 JSON 文件路径: ")
            call_graph_path = input("请输入增强调用图 JSON 文件路径: ")
            module_summary_path = input("请输入模块总结 JSON 文件路径: ")

            save_path, preview = generate_repo_profile(
                repo_path=repo_path,
                function_analysis_path=function_analysis_path,
                call_graph_path=call_graph_path,
                module_summary_path=module_summary_path
            )

            print()
            print(preview)
            print("-" * 30)

        elif command == "history_kb":
            save_path, preview = build_history_kb()

            print()
            print(preview)
            print("-" * 30)

        elif command == "history_kb_full":
            history_kb_full = build_history_knowledge_base_full(
                profile_dir="repo_profiles/history"
            )

            history_kb_full_path = save_history_knowledge_base_full(
                history_kb_full
            )

            result_text = format_history_kb_full_preview(
                history_kb=history_kb_full,
                save_path=history_kb_full_path
            )

            print()
            print(result_text)
            print("-" * 30)

        elif command == "retrieve":
            target_profile_path = input("请输入目标作品 repo_profile JSON 路径: ")
            history_kb_path = input("请输入历史知识库 JSON 路径: ")
            top_k_text = input("请输入返回数量 top_k，直接回车默认 5: ")

            if top_k_text.strip() == "":
                top_k = 5
            else:
                top_k = int(top_k_text)

            retrieval_result, preview = retrieve_similar_history(
                target_profile_path=target_profile_path,
                history_kb_path=history_kb_path,
                top_k=top_k
            )

            print()
            print(preview)
            print("-" * 30)


        elif command == "retrieve_full":
            target_profile_path = input("请输入目标仓库 repo_profile_full 路径: ")

            top_k_text = input("请输入返回相似项目数量 top_k，直接回车默认 3: ")

            if top_k_text.strip() == "":
                top_k = 3
            else:
                top_k = int(top_k_text)

            retrieval_result = retrieve_similar_history_projects_full(
                target_profile_path=target_profile_path,
                history_kb_full_path="history_knowledge_base/history_profiles_full.json",
                top_k=top_k
            )

            retrieval_result_path = save_retrieval_result_full(
                retrieval_result
            )

            result_text = format_retrieval_result_full_preview(
                retrieval_result=retrieval_result,
                save_path=retrieval_result_path
            )

            print()
            print(result_text)
            print("-" * 30)


        elif command == "evaluate":
            target_profile_path = input("请输入目标作品 repo_profile JSON 路径: ")
            history_kb_path = input("请输入历史知识库 JSON 路径: ")
            top_k_text = input("请输入参与对比的历史作品数量 top_k，直接回车默认 5: ")

            if top_k_text.strip() == "":
                top_k = 5
            else:
                top_k = int(top_k_text)

            save_path, preview, report_content = generate_special_evaluation_report(
                target_profile_path=target_profile_path,
                history_kb_path=history_kb_path,
                top_k=top_k
            )

            print()
            print(preview)

            print("\n报告内容预览:")
            print(report_content)
            print("-" * 30)

        elif command == "ingest_history":
            repo_path = input("请输入历史仓库路径: ")
            analysis_mode = input("请选择分析模式 quick/full，直接回车默认 quick: ")

            if analysis_mode.strip() == "":
                analysis_mode = "quick"

            analysis_mode = analysis_mode.strip().lower()

            max_blocks_text = input("请输入 AI 分析代码块数量 max_blocks，输入 all 表示全部分析，直接回车默认 20: ")
            max_blocks = parse_max_blocks_input(max_blocks_text, default_value=20)

            if max_blocks is None:
                print("你选择了 all，将尝试分析全部代码块。")
                print("本模式可能耗时较长，但支持断点续跑。中途失败后可重新运行继续分析。")

            generated_files, result_text = run_ingest_history(
                repo_path=repo_path,
                max_blocks=max_blocks,
                analysis_mode=analysis_mode
            )

            print()
            print(result_text)
            print("-" * 30)


        elif command == "batch_ingest_history":
            history_root_dir = input("请输入历史项目总目录路径: ")

            analysis_mode = input("请选择分析模式 quick/full，直接回车默认 quick: ")

            if analysis_mode.strip() == "":
                analysis_mode = "quick"

            analysis_mode = analysis_mode.strip().lower()

            max_blocks_text = input("请输入每个历史项目 AI 分析代码块数量 max_blocks，输入 all 表示全部分析，直接回车默认 50: ")

            max_blocks = parse_max_blocks_input(
                max_blocks_text,
                default_value=50
            )

            cache_text = input("是否启用缓存 use_cache？y/n，直接回车默认 y: ")

            if cache_text.strip() == "":
                use_cache = True
            else:
                use_cache = cache_text.strip().lower() in {"y", "yes", "1", "true"}

            force_text = input("是否强制重跑 force_rebuild？y/n，直接回车默认 n: ")

            if force_text.strip() == "":
                force_rebuild = False
            else:
                force_rebuild = force_text.strip().lower() in {"y", "yes", "1", "true"}

            if max_blocks is None:
                print()
                print("你选择了 all，将尝试分析每个历史项目的全部代码块。")
                print("该模式可能耗时较长，建议正式大规模入库前先用 quick + 50 测试。")

            batch_result = run_batch_ingest_history(
                history_root_dir=history_root_dir,
                ask_ai_once=ask_ai_once,
                analysis_mode=analysis_mode,
                max_blocks=max_blocks,
                use_cache=use_cache,
                force_rebuild=force_rebuild
            )

            result_text = format_batch_ingest_history_preview(
                batch_result
            )

            print()
            print(result_text)
            print("-" * 30)

        elif command == "analyze_target":
            repo_path = input("请输入新提交仓库路径: ")
            analysis_mode = input("请选择分析模式 quick/full，直接回车默认 quick: ")

            if analysis_mode.strip() == "":
                analysis_mode = "quick"

            analysis_mode = analysis_mode.strip().lower()

            max_blocks_text = input("请输入 AI 分析代码块数量 max_blocks，输入 all 表示全部分析，直接回车默认 20: ")
            max_blocks = parse_max_blocks_input(max_blocks_text, default_value=20)

            if max_blocks is None:
                print("你选择了 all，将尝试分析全部代码块。")
                print("本模式可能耗时较长，但支持断点续跑。中途失败后可重新运行继续分析。")

            generated_files, result_text = run_analyze_target(
                repo_path=repo_path,
                max_blocks=max_blocks,
                analysis_mode=analysis_mode
            )

            print()
            print(result_text)
            print("-" * 30)


        elif command == "compare_full":
            retrieval_result_path = input("请输入 retrieve_full 或 hybrid_retrieve 生成的相似项目结果路径: ")

            comparison_result = compare_retrieval_results_with_ai(
                retrieval_result_path=retrieval_result_path,
                ask_ai_once=ask_ai_once
            )

            comparison_result_path = save_history_comparison_full(
                comparison_result
            )

            result_text = format_history_comparison_full_preview(
                comparison_result=comparison_result,
                save_path=comparison_result_path
            )

            print()
            print(result_text)
            print("-" * 30)


        elif command == "score_full":
            repo_profile_path = input("请输入目标仓库 repo_profile_full 路径: ")
            retrieval_result_path = input("请输入 retrieve_full 结果路径: ")
            comparison_result_path = input("请输入 compare_full 结果路径: ")

            score_result = evaluate_project_score_full(
                repo_profile_path=repo_profile_path,
                retrieval_result_path=retrieval_result_path,
                comparison_result_path=comparison_result_path,
                ask_ai_once=ask_ai_once
            )

            score_result_path = save_score_result_full(score_result)

            result_text = format_score_result_full_preview(
                score_result=score_result,
                save_path=score_result_path
            )

            print()
            print(result_text)
            print("-" * 30)
    

        elif command == "final_report":
            print()
            print("final_report 支持两种输入方式：")
            print("1. 直接输入仓库名，例如：zhengzhoudaxue111")
            print("2. 输入 repo_profile_full.json 路径")
            print()

            repo_name_or_path = input("请输入仓库名或 repo_profile_full.json 路径: ")

            repo_name, path_map = resolve_final_report_paths(
                repo_name_or_path
            )

            print()
            print(format_resolved_paths_preview(
                repo_name=repo_name,
                path_map=path_map
            ))

            confirm_text = input("是否使用以上路径生成最终报告？y/n，直接回车默认 y: ")

            if confirm_text.strip() == "" or confirm_text.strip().lower() in {"y", "yes", "1", "true"}:
                report_result = generate_final_report_full(
                    repo_profile_path=path_map["repo_profile_path"],
                    retrieval_result_path=path_map["retrieval_result_path"],
                    comparison_result_path=path_map["comparison_result_path"],
                    score_result_path=path_map["score_result_path"]
                )

                report_path = save_final_report_full(report_result)

                result_text = format_final_report_preview(
                    report_result=report_result,
                    save_path=report_path
                )

                print()
                print(result_text)
                print("-" * 30)
            else:
                print("已取消生成最终报告。")

        elif command == "final_analyze_hybrid":
            repo_path = input("请输入目标仓库路径: ")

            analysis_mode = input("请选择分析模式 quick/full，直接回车默认 full: ")

            if analysis_mode.strip() == "":
                analysis_mode = "full"

            analysis_mode = analysis_mode.strip().lower()

            max_blocks_text = input("请输入 AI 分析代码块数量 max_blocks，输入 all 表示全部分析，直接回车默认 100: ")

            max_blocks = parse_max_blocks_input(
                max_blocks_text,
                default_value=100
            )

            top_k_text = input("请输入 retrieve_full 结构检索 top_k，直接回车默认 3: ")

            if top_k_text.strip() == "":
                top_k = 3
            else:
                top_k = int(top_k_text)

            rag_top_k_text = input("请输入 RAG top_k，直接回车默认 10: ")

            if rag_top_k_text.strip() == "":
                rag_top_k = 10
            else:
                rag_top_k = int(rag_top_k_text)

            final_top_k_text = input("请输入最终 Hybrid top_k，直接回车默认 5: ")

            if final_top_k_text.strip() == "":
                final_top_k = 5
            else:
                final_top_k = int(final_top_k_text)

            structured_weight_text = input("请输入结构检索权重，直接回车默认 0.65: ")

            if structured_weight_text.strip() == "":
                structured_weight = 0.65
            else:
                structured_weight = float(structured_weight_text)

            semantic_weight_text = input("请输入 RAG 语义检索权重，直接回车默认 0.35: ")

            if semantic_weight_text.strip() == "":
                semantic_weight = 0.35
            else:
                semantic_weight = float(semantic_weight_text)

            embedding_backend = input("请选择 embedding_backend hash/bge，直接回车默认 hash: ")

            if embedding_backend.strip() == "":
                embedding_backend = "hash"

            embedding_backend = embedding_backend.strip().lower()

            embedding_model_name = ""

            if embedding_backend == "bge":
                embedding_model_name = input("请输入 BGE 模型名，直接回车默认 BAAI/bge-small-zh-v1.5: ")

                if embedding_model_name.strip() == "":
                    embedding_model_name = "BAAI/bge-small-zh-v1.5"

            device = input("请输入运行设备 cpu/cuda，直接回车默认 cpu: ")

            if device.strip() == "":
                device = "cpu"

            force_text = input("是否强制重建向量库？y/n，直接回车默认 y: ")

            if force_text.strip() == "":
                force_rebuild_vector_store = True
            else:
                force_rebuild_vector_store = force_text.strip().lower() in {"y", "yes", "1", "true"}

            if max_blocks is None:
                print()
                print("你选择了 all，将尝试分析全部代码块。")
                print("该模式可能耗时较长，但支持断点续跑。")

            generated_files = run_final_analyze_hybrid_pipeline(
                repo_path=repo_path,
                ask_ai_once=ask_ai_once,
                analysis_mode=analysis_mode,
                max_blocks=max_blocks,
                top_k=top_k,
                rag_top_k=rag_top_k,
                final_top_k=final_top_k,
                structured_weight=structured_weight,
                semantic_weight=semantic_weight,
                embedding_backend=embedding_backend,
                embedding_model_name=embedding_model_name,
                device=device,
                force_rebuild_vector_store=force_rebuild_vector_store
            )

            result_text = format_final_analyze_hybrid_preview(
                generated_files
            )

            print()
            print(result_text)
            print("-" * 30)

        elif command == "history_kb_report":
            history_kb_path = input("请输入 full 历史知识库路径，直接回车默认 history_knowledge_base/history_profiles_full.json: ")

            if history_kb_path.strip() == "":
                history_kb_path = "history_knowledge_base/history_profiles_full.json"

            report_result = generate_history_kb_report(
                history_kb_path=history_kb_path
            )

            report_path = save_history_kb_report(report_result)

            result_text = format_history_kb_report_preview(
                report_result=report_result,
                save_path=report_path
            )

            print()
            print(result_text)
            print("-" * 30)

        elif command == "build_rag_docs":
            history_kb_path = input("请输入 full 历史知识库路径，直接回车默认 history_knowledge_base/history_profiles_full.json: ")

            if history_kb_path.strip() == "":
                history_kb_path = "history_knowledge_base/history_profiles_full.json"

            rag_result = build_history_rag_documents(
                history_kb_path=history_kb_path
            )

            json_path = save_history_rag_documents(
                rag_result
            )

            markdown_path = save_history_rag_documents_markdown(
                rag_result
            )

            result_text = format_history_rag_documents_preview(
                rag_result=rag_result,
                json_path=json_path,
                markdown_path=markdown_path
            )

            print()
            print(result_text)
            print("-" * 30)


        elif command == "build_vector_store":
            rag_docs_path = input("请输入 RAG 文档路径，直接回车默认 rag_documents/history_rag_documents.json: ")

            if rag_docs_path.strip() == "":
                rag_docs_path = "rag_documents/history_rag_documents.json"

            persist_directory = input("请输入 Chroma 向量库目录，直接回车默认 vector_store/chroma_history: ")

            if persist_directory.strip() == "":
                persist_directory = "vector_store/chroma_history"

            collection_name = input("请输入 collection 名称，直接回车默认 os_history_projects: ")

            if collection_name.strip() == "":
                collection_name = "os_history_projects"

            embedding_backend = input("请选择 embedding_backend hash/bge，直接回车默认 bge: ")

            if embedding_backend.strip() == "":
                embedding_backend = "bge"

            embedding_backend = embedding_backend.strip().lower()

            embedding_model_name = ""

            if embedding_backend == "bge":
                embedding_model_name = input("请输入 BGE 模型名，直接回车默认 BAAI/bge-small-zh-v1.5: ")

                if embedding_model_name.strip() == "":
                    embedding_model_name = "BAAI/bge-small-zh-v1.5"

            device = input("请输入运行设备 cpu/cuda，直接回车默认 cpu: ")

            if device.strip() == "":
                device = "cpu"

            force_text = input("是否强制重建向量库？y/n，直接回车默认 y: ")

            if force_text.strip() == "":
                force_rebuild = True
            else:
                force_rebuild = force_text.strip().lower() in {"y", "yes", "1", "true"}

            build_result = build_chroma_vector_store(
                rag_docs_path=rag_docs_path,
                persist_directory=persist_directory,
                collection_name=collection_name,
                force_rebuild=force_rebuild,
                embedding_backend=embedding_backend,
                embedding_model_name=embedding_model_name,
                device=device
            )

            result_text = format_vector_store_build_preview(
                build_result
            )

            print()
            print(result_text)
            print("-" * 30)

        elif command == "rag_retrieve":
            query = input("请输入检索问题或目标项目描述: ")

            top_k_text = input("请输入 top_k，直接回车默认 5: ")

            if top_k_text.strip() == "":
                top_k = 5
            else:
                top_k = int(top_k_text)

            persist_directory = input("请输入 Chroma 向量库目录，直接回车默认 vector_store/chroma_history: ")

            if persist_directory.strip() == "":
                persist_directory = "vector_store/chroma_history"

            collection_name = input("请输入 collection 名称，直接回车默认 os_history_projects: ")

            if collection_name.strip() == "":
                collection_name = "os_history_projects"

            retrieval_result = rag_retrieve_history(
                query=query,
                persist_directory=persist_directory,
                collection_name=collection_name,
                top_k=top_k
            )

            save_path = save_rag_retrieval_result(
                retrieval_result
            )

            result_text = format_rag_retrieval_preview(
                retrieval_result=retrieval_result,
                save_path=save_path
            )

            print()
            print(result_text)
            print("-" * 30)

        elif command == "hybrid_retrieve":
            target_repo_profile_path = input("请输入目标 repo_profile_full 路径: ")

            structured_result_path = input("请输入 retrieve_full 结构检索结果路径: ")

            rag_query = input("请输入 RAG 检索 query，直接回车则根据 repo_profile 自动生成: ")

            persist_directory = input("请输入 Chroma 向量库目录，直接回车默认 vector_store/chroma_history: ")

            if persist_directory.strip() == "":
                persist_directory = "vector_store/chroma_history"

            collection_name = input("请输入 collection 名称，直接回车默认 os_history_projects: ")

            if collection_name.strip() == "":
                collection_name = "os_history_projects"

            structured_weight_text = input("请输入结构检索权重，直接回车默认 0.65: ")

            if structured_weight_text.strip() == "":
                structured_weight = 0.65
            else:
                structured_weight = float(structured_weight_text)

            semantic_weight_text = input("请输入 RAG 语义检索权重，直接回车默认 0.35: ")

            if semantic_weight_text.strip() == "":
                semantic_weight = 0.35
            else:
                semantic_weight = float(semantic_weight_text)

            rag_top_k_text = input("请输入 RAG top_k，直接回车默认 10: ")

            if rag_top_k_text.strip() == "":
                rag_top_k = 10
            else:
                rag_top_k = int(rag_top_k_text)

            final_top_k_text = input("请输入最终 top_k，直接回车默认 5: ")

            if final_top_k_text.strip() == "":
                final_top_k = 5
            else:
                final_top_k = int(final_top_k_text)

            hybrid_result = run_hybrid_retrieve(
                target_repo_profile_path=target_repo_profile_path,
                structured_result_path=structured_result_path,
                rag_query=rag_query,
                persist_directory=persist_directory,
                collection_name=collection_name,
                structured_weight=structured_weight,
                semantic_weight=semantic_weight,
                rag_top_k=rag_top_k,
                final_top_k=final_top_k
            )

            result_text = format_hybrid_retrieval_preview(
                hybrid_result
            )

            print()
            print(result_text)
            print("-" * 30)

        else:
            print(f"未知命令：{command}")
            print("输入 help 查看可用命令。")


if __name__ == "__main__":
    main()
    