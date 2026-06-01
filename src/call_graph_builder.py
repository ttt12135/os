import os
import json
import re
from datetime import datetime
#v1.5中加入正则提取

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


def build_block_map(code_blocks_data):
    """
    根据 block_id 建立代码块索引，方便通过 block_id 找回原始代码内容。
    """
    block_map = {}

    for block in code_blocks_data.get("blocks", []):
        block_id = block.get("block_id")
        if block_id:
            block_map[block_id] = block

    return block_map


def clean_callee_name(name):
    """
    清洗提取出来的调用名，去掉明显无效的内容。
    """
    if not name:
        return ""

    name = name.strip()

    invalid_names = {
        "if",
        "for",
        "while",
        "match",
        "loop",
        "return",
        "sizeof",
        "switch",
        "catch",
        "await",
        "Some",
        "Ok",
        "Err",
        "None",
        "true",
        "false",
    }

    if name in invalid_names:
        return ""

    return name


def extract_calls_by_regex(code_content):
    """
    从代码内容中用正则提取可能的函数调用。

    支持常见形式：
    - func(...)
    - self.func(...)
    - module::func(...)
    - object.method(...)
    """

    if not code_content:
        return []

    patterns = [
        # Rust / C++ 风格：module::func(
        r"\b([A-Za-z_][\w]*::[A-Za-z_][\w]*)\s*\(",

        # 方法调用：self.func( 或 object.func(
        r"\b([A-Za-z_][\w]*\.[A-Za-z_][\w]*)\s*\(",

        # 普通函数调用：func(
        r"\b([A-Za-z_][\w]*)\s*\(",
    ]

    calls = []

    for pattern in patterns:
        matches = re.findall(pattern, code_content)

        for match in matches:
            callee = clean_callee_name(match)

            if callee == "":
                continue

            if callee not in calls:
                calls.append(callee)

    return calls


def extract_ai_edges(functions):
    """
    从 AI 函数理解结果中提取调用边。
    """
    edges = []

    for item in functions:
        caller = item.get("name")
        caller_file = item.get("file_path")
        caller_module = item.get("related_os_module", "unknown")
        source_block_id = item.get("block_id", "")
        evidence = item.get("evidence", "")
        called_functions = item.get("called_functions", [])

        if not caller:
            continue

        if not isinstance(called_functions, list):
            continue

        for callee in called_functions:
            callee = clean_callee_name(callee)

            if callee == "":
                continue

            edges.append(
                {
                    "caller": caller,
                    "caller_file": caller_file,
                    "callee": callee,
                    "caller_module": caller_module,
                    "evidence": evidence,
                    "source_block_id": source_block_id,
                    "source": ["ai"],
                    "confidence": 0.7
                }
            )

    return edges


def extract_regex_edges(functions, block_map):
    """
    根据函数理解结果中的 block_id，找到原始代码块，再用正则提取调用边
    """
    edges = []

    for item in functions:
        caller = item.get("name")
        caller_file = item.get("file_path")
        caller_module = item.get("related_os_module", "unknown")
        source_block_id = item.get("block_id", "")

        if not caller:
            continue

        block = block_map.get(source_block_id)

        if block is None:
            continue

        code_content = block.get("content", "")
        calls = extract_calls_by_regex(code_content)

        for callee in calls:
            if callee == caller:
                continue

            edges.append(
                {
                    "caller": caller,
                    "caller_file": caller_file,
                    "callee": callee,
                    "caller_module": caller_module,
                    "evidence": "该调用关系由源码正则规则从代码块 content 中提取。",
                    "source_block_id": source_block_id,
                    "source": ["regex"],
                    "confidence": 0.6
                }
            )

    return edges


def merge_edges(ai_edges, regex_edges):
    """
    合并 AI 提取和正则提取的调用边。

    如果同一条 caller -> callee 同时被 AI 和 regex 发现，
    则提高置信度。
    """
    edge_map = {}

    all_edges = ai_edges + regex_edges

    for edge in all_edges:
        key = (
            edge.get("caller"),
            edge.get("caller_file"),
            edge.get("callee")
        )

        if key not in edge_map:
            edge_map[key] = edge
        else:
            old_edge = edge_map[key]

            old_sources = set(old_edge.get("source", []))
            new_sources = set(edge.get("source", []))
            merged_sources = sorted(list(old_sources | new_sources))

            old_edge["source"] = merged_sources

            if "ai" in merged_sources and "regex" in merged_sources:
                old_edge["confidence"] = 0.9
                old_edge["evidence"] = (
                    "该调用关系同时由 AI 函数理解和源码正则提取发现，可信度较高。"
                )
            else:
                old_edge["confidence"] = max(
                    old_edge.get("confidence", 0.5),
                    edge.get("confidence", 0.5)
                )

    return list(edge_map.values())


def build_enhanced_call_graph(function_analysis_path, code_blocks_path):
    """

    输入：
    1.function_analysis_path：AI 函数理解结果
    2.code_blocks_path：原始代码切片结果

    输出：
    AI + 正则合并后的调用图
    """
    function_analysis_data = load_json_file(function_analysis_path)
    code_blocks_data = load_json_file(code_blocks_path)

    repo_name = function_analysis_data.get("repo_name", "unknown_repo")
    functions = function_analysis_data.get("functions", [])

    block_map = build_block_map(code_blocks_data)

    ai_edges = extract_ai_edges(functions)
    regex_edges = extract_regex_edges(functions, block_map)

    merged_edges = merge_edges(ai_edges, regex_edges)

    call_graph = {
        "repo_name": repo_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "function_count": len(functions),
        "ai_edge_count": len(ai_edges),
        "regex_edge_count": len(regex_edges),
        "merged_edge_count": len(merged_edges),
        "edges": merged_edges
    }

    return call_graph


def save_call_graph(call_graph, enhanced=True):
    """
    保存调用图 JSON。
    """
    output_dir = "call_graph"
    ensure_dir(output_dir)

    repo_name = call_graph.get("repo_name", "unknown_repo")

    if enhanced:
        file_name = f"{repo_name}_call_graph_enhanced.json"
    else:
        file_name = f"{repo_name}_call_graph.json"

    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(call_graph, file, ensure_ascii=False, indent=2)

    return file_path


def format_call_graph_summary(call_graph, save_path):
    """
    生成终端显示摘要。
    """
    output = []

    output.append("增强版函数调用关系提取完成。")
    output.append("")
    output.append(f"仓库名称：{call_graph.get('repo_name')}")
    output.append(f"函数数量：{call_graph.get('function_count')}")
    output.append(f"AI 提取调用边数量：{call_graph.get('ai_edge_count')}")
    output.append(f"正则提取调用边数量：{call_graph.get('regex_edge_count')}")
    output.append(f"合并后调用边数量：{call_graph.get('merged_edge_count')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("前几个调用关系预览：")

    edges = call_graph.get("edges", [])

    if len(edges) == 0:
        output.append("暂无调用关系。")
    else:
        for index, edge in enumerate(edges[:10], start=1):
            output.append(
                f"{index}. {edge.get('caller')}  ->  {edge.get('callee')}"
            )
            output.append(f"   文件：{edge.get('caller_file')}")
            output.append(f"   模块：{edge.get('caller_module')}")
            output.append(f"   来源：{', '.join(edge.get('source', []))}")
            output.append(f"   置信度：{edge.get('confidence')}")
            output.append("")

    return "\n".join(output)