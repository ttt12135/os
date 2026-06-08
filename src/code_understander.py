import os
import json
from datetime import datetime


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




def analyze_code_blocks_file(blocks_file_path, ask_ai_once, max_blocks=10):
    """
    分析一个代码块 JSON 文件中的前 max_blocks 个代码块。
    max_blocks 先限制代码块数量，防止多度使用token

    max_blocks:
    整数：只分析前 max_blocks 个代码块
    None：分析全部代码块
    """
    data = load_code_blocks(blocks_file_path)

    repo_name = data.get("repo_name", "unknown_repo")
    blocks = data.get("blocks", [])

    if max_blocks is None:
        selected_blocks = blocks
    else:
        selected_blocks = blocks[:max_blocks]

    results = []

    for index, block in enumerate(selected_blocks, start=1):
        print(f"正在分析第 {index}/{len(selected_blocks)} 个代码块：{block.get('name')}")

        analysis = analyze_single_block(
            repo_name=repo_name,
            block=block,
            ask_ai_once=ask_ai_once
        )

        results.append(analysis)

    return repo_name, results


def save_function_analysis(repo_name, analysis_results):
    """
    保存AI分析结果
    """
    output_dir = "function_analysis"
    ensure_dir(output_dir)

    file_name = f"{repo_name}_function_analysis.json"
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