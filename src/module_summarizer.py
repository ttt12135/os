"""
模块化总结代码含义
根据增强版函数调用图谱完成
模块化的函数掉调用关系
"""
import os
import json
from datetime import datetime


def ensure_dir(dir_path):
    """
    如果目录不存在，就自动创建。
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def group_functions_by_module(functions):
    """
    按 related_os_module 对函数理解结果分组。
    """

    module_map = {}

    for item in functions:
        module = item.get("related_os_module", "unknown")

        if module is None or module == "":
            module = "unknown"

        if module not in module_map:
            module_map[module] = []

        module_map[module].append(item)

    return module_map


def group_edges_by_module(edges):
    """
    按 caller_module 对调用边分组。
    """

    module_edge_map = {}

    for edge in edges:
        module = edge.get("caller_module", "unknown")

        if module is None or module == "":
            module = "unknown"

        if module not in module_edge_map:
            module_edge_map[module] = []

        module_edge_map[module].append(edge)

    return module_edge_map


def build_module_prompt(repo_name, module_name, functions, edges):
    """
    构造模块总结 Prompt。
    """

    function_text_parts = []

    for index, func in enumerate(functions, start=1):
        function_text_parts.append(f"函数 {index}")
        function_text_parts.append(f"名称：{func.get('name')}")
        function_text_parts.append(f"文件：{func.get('file_path')}")
        function_text_parts.append(f"作用总结：{func.get('summary')}")
        function_text_parts.append("主要逻辑步骤：")

        logic_steps = func.get("logic_steps", [])
        if isinstance(logic_steps, list):
            for step in logic_steps:
                function_text_parts.append(f"- {step}")

        function_text_parts.append(f"证据：{func.get('evidence')}")
        function_text_parts.append(f"不确定性：{func.get('uncertainty')}")
        function_text_parts.append("")

    edge_text_parts = []

    for index, edge in enumerate(edges, start=1):
        edge_text_parts.append(
            f"{index}. {edge.get('caller')} -> {edge.get('callee')} "
            f"(来源：{', '.join(edge.get('source', []))}，置信度：{edge.get('confidence')})"
        )

    functions_text = "\n".join(function_text_parts)
    edges_text = "\n".join(edge_text_parts)

    prompt = f"""
你现在要分析一个操作系统比赛作品中的一个模块。

仓库名称：{repo_name}
模块名称：{module_name}

下面是AI模型对该模块下的函数理解结果：

{functions_text}

下面是该模块相关的函数调用关系：

{edges_text}

请你基于以上信息，生成该模块的结构化总结。

要求：
1. 必须基于函数理解和调用关系，不要凭空编造；
2. 说明这个模块大概负责什么；
3. 说明模块中的关键函数分别承担什么角色；
4. 说明函数之间是否存在明显调用链；
5. 如果证据不足，要明确说明，不能自己编造；
6. 输出必须是合法 JSON，不要输出 Markdown。

请按以下 JSON 格式输出：

{{
  "module_name": "{module_name}",
  "module_summary": "该模块的总体作用总结",
  "key_functions": [
    {{
      "name": "函数名",
      "role": "该函数在模块中的作用"
    }}
  ],
  "call_flow_summary": "该模块内部调用关系或执行流程总结",
  "evidence": [
    "用于支持判断的证据"
  ],
  "uncertainty": "不确定信息说明"
}}
"""

    return prompt


def summarize_single_module(repo_name, module_name, functions, edges, ask_ai_once):
    """
    调用 AI 总结单个模块。
    """

    prompt = build_module_prompt(
        repo_name=repo_name,
        module_name=module_name,
        functions=functions,
        edges=edges
    )

    ai_reply = ask_ai_once(prompt)

    try:
        summary = json.loads(ai_reply)
    except json.JSONDecodeError:
        summary = {
            "module_name": module_name,
            "module_summary": ai_reply,
            "key_functions": [],
            "call_flow_summary": "",
            "evidence": [],
            "uncertainty": "AI 返回内容不是标准 JSON，已保存为 module_summary。"
        }

    return summary


def summarize_modules(function_analysis_path, call_graph_path, ask_ai_once, max_modules=8):
    """
    根据函数理解结果和调用图，生成模块级总结。
    """

    function_data = load_json_file(function_analysis_path)
    call_graph_data = load_json_file(call_graph_path)

    repo_name = function_data.get("repo_name", "unknown_repo")
    functions = function_data.get("functions", [])
    edges = call_graph_data.get("edges", [])

    module_map = group_functions_by_module(functions)
    module_edge_map = group_edges_by_module(edges)

    module_names = list(module_map.keys())

    # 优先分析非 unknown 模块
    module_names.sort(key=lambda name: (name == "unknown", name))

    selected_modules = module_names[:max_modules]

    summaries = []

    for index, module_name in enumerate(selected_modules, start=1):
        print(f"正在总结第 {index}/{len(selected_modules)} 个模块：{module_name}")

        module_functions = module_map.get(module_name, [])
        module_edges = module_edge_map.get(module_name, [])

        summary = summarize_single_module(
            repo_name=repo_name,
            module_name=module_name,
            functions=module_functions,
            edges=module_edges,
            ask_ai_once=ask_ai_once
        )

        summaries.append(summary)

    result = {
        "repo_name": repo_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "module_count": len(summaries),
        "modules": summaries
    }

    return result


def save_module_summary(module_summary):
    """
    保存模块总结 JSON。
    """

    output_dir = "module_summary"
    ensure_dir(output_dir)

    repo_name = module_summary.get("repo_name", "unknown_repo")
    file_name = f"{repo_name}_module_summary.json"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(module_summary, file, ensure_ascii=False, indent=2)

    return file_path


def format_module_summary_preview(module_summary, save_path):
    """
    生成终端显示摘要。
    """

    output = []

    output.append("模块逻辑总结完成。")
    output.append("")
    output.append(f"仓库名称：{module_summary.get('repo_name')}")
    output.append(f"模块数量：{module_summary.get('module_count')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("模块预览：")

    modules = module_summary.get("modules", [])

    for index, module in enumerate(modules[:5], start=1):
        output.append(f"{index}. {module.get('module_name')}")
        output.append(f"   总结：{module.get('module_summary')}")
        output.append(f"   调用流程：{module.get('call_flow_summary')}")
        output.append("")

    return "\n".join(output)

