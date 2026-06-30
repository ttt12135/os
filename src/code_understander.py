import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def ensure_dir(dir_path):
    """
    如果目录不存在，就自动创建。
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def load_code_blocks(blocks_file_path):
    """
    读取 v0.9 保存的代码块 JSON 文件。
    """

    with open(blocks_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def build_function_analysis_prompt(repo_name, block):
    """
    构造让 AI 阅读单个代码块的 Prompt
    """

    prompt = f"""
你现在要阅读一个操作系统比赛作品中的代码块，并分析它的真实逻辑。

仓库名称：{repo_name}

代码块信息：
block_id: {block.get("block_id")}
文件路径: {block.get("file_path")}
语言: {block.get("language")}
解析器: {block.get("parser")}
起始行: {block.get("start_line")}
结束行: {block.get("end_line")}
类型: {block.get("type")}
名称: {block.get("name")}

代码内容如下：

text
{block.get("content")}

请你基于代码内容进行分析，不要只根据函数名猜测。

请按 JSON 格式输出，字段如下：

{{
  "block_id": "{block.get("block_id")}",
  "file_path": "{block.get("file_path")}",
  "language": "{block.get("language")}",
  "parser": "{block.get("parser")}",
  "start_line": "{block.get("start_line")}",
  "end_line": "{block.get("end_line")}",
  "name": "{block.get("name")}",
  "type": "{block.get("type")}",

"summary": "这个代码块的主要作用",
"logic_steps": [
"第1步逻辑",
"第2步逻辑"
],
"called_functions": [
"它明显调用到的函数名"
],
"related_os_module": "可能所属模块，例如 boot / memory / process / scheduler / interrupt / syscall / filesystem / driver / build / report_generation / unknown",
"evidence": "你判断的代码依据",
"uncertainty": "如果信息不足，请说明不确定性"
}}

要求：

必须基于代码内容分析；
不要编造代码里没有体现的功能；
如果无法判断模块，就写 unknown；

输出必须是合法 JSON，不要输出 Markdown。
"""

    return prompt

def analyze_single_block(repo_name, block, ask_ai_once):
    """
    调用 AI 分析单个代码块
    ask_ai_once 是 main.py 中的单次 AI 调用函数,已经在main中给出
    """
    prompt = build_function_analysis_prompt(repo_name, block)
    ai_reply = ask_ai_once(prompt)

    try:
        analysis = json.loads(ai_reply)
    except json.JSONDecodeError:
        analysis = {
            "block_id": block.get("block_id"),
            "file_path": block.get("file_path"),
            "language": block.get("language"),
            "parser": block.get("parser"),
            "start_line": block.get("start_line"),
            "end_line": block.get("end_line"),
            "name": block.get("name"),
            "type": block.get("type"),
            "summary": ai_reply,
            "logic_steps": [],
            "called_functions": [],
            "related_os_module": "unknown",
            "evidence": "AI 返回内容不是标准 JSON，已保存为 summary。",
            "uncertainty": "JSON 解析失败，需要后续优化 Prompt 或手动检查。"
        }

    return analysis

def analyze_single_block_safe(repo_name, block, ask_ai_once):
    """
    安全分析单个代码块。

    这个个函数用于并发场景：
    单个 block 出错不会导致整个分析流程崩溃
    出错信息会被保存到结果中
    """

    try:
        return analyze_single_block(
            repo_name=repo_name,
            block=block,
            ask_ai_once=ask_ai_once
        )

    except Exception as error:
        return {
            "block_id": block.get("block_id"),
            "file_path": block.get("file_path"),
            "language": block.get("language"),
            "parser": block.get("parser"),
            "start_line": block.get("start_line"),
            "end_line": block.get("end_line"),
            "name": block.get("name"),
            "type": block.get("type"),
            "summary": "该代码块分析失败。",
            "logic_steps": [],
            "called_functions": [],
            "related_os_module": "unknown",
            "evidence": str(error),
            "uncertainty": "并发分析过程中该代码块发生异常，后续可单独重试。"
        }


def analyze_code_blocks_file(
    blocks_file_path,
    ask_ai_once,
    max_blocks=10,
    resume=True,
    save_every=1
):
    """
    分析代码块 JSON 文件。

    max_blocks:
    整数：分析前 max_blocks 个代码块
    None：分析全部代码块

    resume:
    True：启用断点续跑，跳过已经分析过的 block
    False：从头重新分析

    save_every:
    每分析多少个 block 保存一次进度
    """

    data = load_code_blocks(blocks_file_path)

    repo_name = data.get("repo_name", "unknown_repo")
    blocks = data.get("blocks", [])

    if max_blocks is None:
        selected_blocks = blocks
    else:
        selected_blocks = blocks[:max_blocks]

    if resume:
        results = load_analysis_progress(repo_name)
    else:
        results = []

    analyzed_block_ids = build_analyzed_block_id_set(results)

    total_count = len(selected_blocks)

    for index, block in enumerate(selected_blocks, start=1):
        block_id = block.get("block_id")

        if block_id in analyzed_block_ids:
            print(f"跳过已分析代码块 {index}/{total_count}：{block.get('name')}")
            continue

        print(f"正在分析第 {index}/{total_count} 个代码块：{block.get('name')}")

        analysis = analyze_single_block(
            repo_name=repo_name,
            block=block,
            ask_ai_once=ask_ai_once
        )

        results.append(analysis)
        analyzed_block_ids.add(block_id)

        if len(results) % save_every == 0:
            save_analysis_progress(repo_name, results)

    save_analysis_progress(repo_name, results)

    return repo_name, results


def save_function_analysis(repo_name, analysis_results, suffix="function_analysis"):
    """
    保存函数级代码理解结果。
    """

    output_dir = "function_analysis"
    ensure_dir(output_dir)

    file_name = f"{repo_name}_{suffix}.json"
    file_path = os.path.join(output_dir, file_name)

    data = {
        "repo_name": repo_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis_count": len(analysis_results),
        "functions": analysis_results
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return file_path


def format_function_analysis_summary(repo_name, analysis_results, save_path):
    """
    生成终端显示用的摘要。
    """

    output = []

    output.append("AI 函数级代码理解完成。")
    output.append("")
    output.append(f"仓库名称：{repo_name}")
    output.append(f"分析函数数量：{len(analysis_results)}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("前几个函数分析预览：")

    for index, item in enumerate(analysis_results[:5], start=1):
        output.append(f"{index}. {item.get('name')}")
        output.append(f"   文件：{item.get('file_path')}")
        output.append(f"   模块：{item.get('related_os_module')}")
        output.append(f"   作用：{item.get('summary')}")
        output.append("")

    return "\n".join(output)

def save_analysis_progress(repo_name, analysis_results):
    """
    保存函数理解进度。
    每分析完一批或一个 block，就写入 progress 文件。
    """

    output_dir = "function_analysis"

    ensure_dir(output_dir)

    file_name = f"{repo_name}_function_analysis_progress.json"
    file_path = os.path.join(output_dir, file_name)

    data = {
        "repo_name": repo_name,
        "analysis_count": len(analysis_results),
        "functions": analysis_results
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return file_path


def load_analysis_progress(repo_name):
    """
    读取已有函数理解进度。
    如果没有进度文件，就返回空列表。
    """

    file_path = os.path.join(
        "function_analysis",
        f"{repo_name}_function_analysis_progress.json"
    )

    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("functions", [])



def build_analyzed_block_id_set(analysis_results):
    """
    从已有分析结果中提取已经完成的 block_id。
    """

    analyzed_block_ids = set()

    for item in analysis_results:
        block_id = item.get("block_id")

        if block_id:
            analyzed_block_ids.add(block_id)

    return analyzed_block_ids

from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def analyze_code_blocks_file_concurrent( blocks_file_path,ask_ai_once,max_blocks=None,resume=True,save_every=5,max_workers=8):
    """
    并发分析代码块 JSON 文件。

    max_blocks:
    None：全量分析全部代码块
    数字：只分析前 max_blocks 个代码块

    resume:
    True：启用断点续跑，跳过已经分析过的 block

    save_every:
    每完成多少个新 block 保存一次进度

    max_workers:
    AI 并发线程数，默认 8
    """

    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    data = load_code_blocks(blocks_file_path)

    repo_name = data.get("repo_name", "unknown_repo")
    blocks = data.get("blocks", [])

    total_blocks_in_file = len(blocks)

    if max_blocks is None:
        selected_blocks = blocks
        print("分析模式：全量分析")
    else:
        selected_blocks = blocks[:max_blocks]
        print(f"分析模式：截断分析，最多分析前 {max_blocks} 个代码块")

    if resume:
        results = load_analysis_progress(repo_name)
    else:
        results = []

    analyzed_block_ids = build_analyzed_block_id_set(results)

    pending_blocks = []

    for block in selected_blocks:
        block_id = block.get("block_id")

        if block_id in analyzed_block_ids:
            continue

        pending_blocks.append(block)

    total_count = len(selected_blocks)
    pending_count = len(pending_blocks)
    finished_count = total_count - pending_count

    print("=" * 60)
    print(f"仓库名称：{repo_name}")
    print(f"代码块文件总数：{total_blocks_in_file}")
    print(f"本次计划分析数量：{total_count}")
    print(f"已完成数量：{finished_count}")
    print(f"待分析数量：{pending_count}")
    print(f"并发线程数：{max_workers}")
    print("=" * 60)

    if pending_count == 0:
        print("所有代码块都已经分析完成，无需重复调用 API。")
        return repo_name, results

    completed_new_count = 0

    def safe_analyze(block):
        """
        单个代码块安全分析：
        最多重试 3 次
        轻微延迟，避免 8 线程瞬间打爆 API
        """

        for attempt in range(3):
            try:
                time.sleep(0.03 * (attempt + 1))
                return analyze_single_block_safe(
                    repo_name,
                    block,
                    ask_ai_once
                )
            except Exception as e:
                block_name = block.get("name", "unknown_block")
                print(
                    f"[WARN] 代码块分析失败，准备重试 "
                    f"{attempt + 1}/3：{block_name}，错误：{e}"
                )
                time.sleep(0.5 * (attempt + 1))

        block_id = block.get("block_id")
        block_name = block.get("name", "unknown_block")

        return {
            "repo_name": repo_name,
            "block_id": block_id,
            "name": block_name,
            "analysis_status": "failed",
            "summary": "该代码块在多次重试后仍分析失败。",
            "error": "AI analysis failed after retries"
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_block = {}

        for block in pending_blocks:
            future = executor.submit(safe_analyze, block)
            future_to_block[future] = block

        for future in as_completed(future_to_block):
            block = future_to_block[future]
            block_id = block.get("block_id")
            block_name = block.get("name")

            try:
                analysis = future.result()
            except Exception as e:
                print(f"[ERROR] future 执行失败：{block_name}，错误：{e}")
                continue

            if not analysis:
                continue

            results.append(analysis)
            analyzed_block_ids.add(block_id)
            completed_new_count += 1

            print(
                f"已完成并发分析 {completed_new_count}/{pending_count}：{block_name}"
            )

            if completed_new_count % save_every == 0:
                save_analysis_progress(repo_name, results)
                print("已保存一次分析进度。")

    save_analysis_progress(repo_name, results)
    print("全部待分析代码块处理完成，最终进度已保存。")

    return repo_name, results