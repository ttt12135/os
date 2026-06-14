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
from src.history_kb_builder import build_history_knowledge_base, save_history_knowledge_base, format_history_kb_preview
from src.history_retriever import retrieve_similar_history_profiles, format_retrieval_results
from src.evaluator import generate_evaluation_report, save_evaluation_report, format_evaluation_preview
from src.ingest_pipeline import ingest_history_repo, analyze_target_repo, format_pipeline_result

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
    print("v1.9- 专项对比评分报告版")
    print("输入 chat：普通聊天")
    print("输入 repo：分析本地仓库")
    print("输入 report：生成单个 OS 仓库描述文档")
    print("输入 batch：批量分析历史 OS 作品")
    print("输入 compare：生成新作品与历史作品对比报告")
    print("输入 split：切分仓库代码块")
    print("输入 save_blocks：切分代码块并保存 JSON")
    print("输入 understand：AI 阅读代码块并生成函数理解结果")
    print("输入 call_graph：根据函数理解结果和代码块生成增强调用关系")
    print("输入 module_summary：根据函数理解和调用图生成模块总结")
    print("输入 profile：生成仓库画像 repo_profile.json")
    print("输入 history_kb：根据 repo_profiles 构建历史作品知识库")
    print("输入 retrieve：根据 repo_profile 检索相似历史作品")
    print("输入 evaluate：生成专项对比评分报告")
    print("输入 ingest_history：一键入库历史仓库")
    print("输入 analyze_target：一键分析新提交仓库")
    print("输入 exit：退出程序")

    while True:
        command = input("请选择模式(chat/repo/report/batch/compare/split/save_blocks/understand/call_graph/module_summary/profile/history_kb/retrieve/evaluate/ingest_history/analyze_target/exit): ")
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

        else:
            print("未知命令，请输入 chat、repo、report、batch、compare 或 exit。")


if __name__ == "__main__":
    main()
    