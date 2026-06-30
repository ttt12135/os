import os
import re
import json
from datetime import datetime
from collections import defaultdict


CORE_MODULE_ALIASES = {
    "boot": "boot",
    "init": "boot",
    "startup": "boot",
    "loader": "boot",

    "memory": "memory",
    "mm": "memory",
    "vm": "memory",
    "virtual_memory": "memory",
    "page": "memory",
    "paging": "memory",
    "allocator": "memory",

    "process": "process",
    "proc": "process",
    "task": "process",
    "thread": "process",
    "scheduler": "scheduler",
    "sched": "scheduler",

    "syscall": "syscall",
    "system_call": "syscall",

    "trap": "interrupt",
    "interrupt": "interrupt",
    "irq": "interrupt",
    "exception": "interrupt",

    "filesystem": "filesystem",
    "fs": "filesystem",
    "file": "filesystem",
    "vfs": "filesystem",

    "driver": "driver",
    "drivers": "driver",
    "device": "driver",
    "block": "driver",
    "console": "driver",
    "uart": "driver",

    "user": "user",
    "user_program": "user",
    "elf": "user",
}


MODULE_RULES = {
    "boot": {
        "display_name": "启动与初始化",
        "keywords": [
            "boot", "entry", "start", "init", "kernel_main", "main", "setup", "loader", "multiboot",
            "初始化", "启动", "入口"
        ],
        "strong_keywords": ["kernel_main", "trap_init", "init_all", "setup_vm", "start_kernel"],
        "data_keywords": ["bootinfo", "multiboot", "bootloader"],
    },
    "memory": {
        "display_name": "内存管理",
        "keywords": [
            "page", "paging", "pmm", "vmm", "frame", "alloc", "dealloc", "malloc", "free",
            "heap", "buddy", "bitmap", "address_space", "page_table", "pte", "map", "unmap",
            "内存", "页表", "分配", "地址空间"
        ],
        "strong_keywords": [
            "page_table", "address_space", "frame_allocator", "buddy", "bitmap", "map_page",
            "unmap", "translate", "read_cstring", "copy_from_user", "copy_to_user"
        ],
        "data_keywords": ["PageTable", "AddressSpace", "Frame", "VmArea", "ProcessVm", "PTE"],
    },
    "process": {
        "display_name": "进程/线程管理",
        "keywords": [
            "process", "proc", "task", "thread", "fork", "exec", "exit", "wait", "pid",
            "context", "进程", "线程", "任务", "上下文"
        ],
        "strong_keywords": [
            "fork", "exec", "exit", "wait", "spawn", "context_switch", "switch_to", "ThreadState",
            "Process", "TaskControlBlock", "TrapFrame"
        ],
        "data_keywords": ["Process", "Task", "Thread", "Context", "TrapFrame", "ThreadState"],
    },
    "scheduler": {
        "display_name": "调度器",
        "keywords": [
            "schedule", "scheduler", "sched", "run_queue", "runnable", "yield", "sleep", "wakeup",
            "time_slice", "priority", "调度", "队列", "时间片"
        ],
        "strong_keywords": [
            "schedule", "pick_next", "run_queue", "context_switch", "switch_to", "yield_now",
            "wakeup", "sleep", "time_slice"
        ],
        "data_keywords": ["RunQueue", "Scheduler", "TaskQueue", "Runnable"],
    },
    "syscall": {
        "display_name": "系统调用",
        "keywords": [
            "syscall", "sys_", "system call", "syscall_id", "dispatch", "user_context",
            "copy_from_user", "copy_to_user", "errno", "系统调用", "分发"
        ],
        "strong_keywords": [
            "syscall_dispatch", "syscall_handler", "sys_open", "sys_read", "sys_write", "sys_exit",
            "sys_fork", "sys_exec", "sys_wait", "copy_from_user", "copy_to_user", "errno"
        ],
        "data_keywords": ["UserContext", "Syscall", "Errno", "IoVec"],
    },
    "interrupt": {
        "display_name": "中断/异常处理",
        "keywords": [
            "trap", "interrupt", "irq", "exception", "timer", "handler", "idt", "vector",
            "中断", "异常", "陷入", "时钟"
        ],
        "strong_keywords": [
            "trap_handler", "interrupt_handler", "timer_interrupt", "irq_handler", "exception_handler",
            "enable_interrupt", "disable_interrupt", "iret", "sret"
        ],
        "data_keywords": ["TrapFrame", "InterruptFrame", "IDT", "Vector"],
    },
    "filesystem": {
        "display_name": "文件系统",
        "keywords": [
            "file", "fs", "vfs", "inode", "dentry", "dir", "open", "read", "write", "close",
            "mount", "path", "block", "文件", "目录", "路径"
        ],
        "strong_keywords": [
            "inode", "vnode", "dentry", "openat", "readv", "writev", "path_resolver", "mount",
            "FileDescriptor", "FileOpen", "resolve"
        ],
        "data_keywords": ["Inode", "Vnode", "Dentry", "File", "Path", "DirEntry", "IoVec"],
    },
    "driver": {
        "display_name": "设备驱动",
        "keywords": [
            "driver", "device", "uart", "console", "virtio", "block", "disk", "serial", "keyboard",
            "设备", "驱动", "磁盘", "串口"
        ],
        "strong_keywords": [
            "virtio", "uart", "console", "block_device", "disk_read", "disk_write", "device_init"
        ],
        "data_keywords": ["Device", "Driver", "BlockDevice", "Console", "Uart"],
    },
    "user": {
        "display_name": "用户程序支持",
        "keywords": [
            "user", "elf", "loader", "user_app", "userspace", "user space", "load_elf", "shell",
            "用户态", "用户程序"
        ],
        "strong_keywords": ["load_elf", "exec", "user_stack", "user_context", "enter_user", "shell"],
        "data_keywords": ["Elf", "UserContext", "UserStack", "Auxv"],
    },
}


CHAIN_STEPS = [
    {"key": "boot", "name": "启动入口"},
    {"key": "memory", "name": "内存初始化/管理"},
    {"key": "interrupt", "name": "中断/异常入口"},
    {"key": "process", "name": "进程/线程结构"},
    {"key": "scheduler", "name": "调度执行"},
    {"key": "syscall", "name": "系统调用链路"},
    {"key": "filesystem", "name": "文件系统/IO"},
]


PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bunimplemented!\s*\(",
    r"\btodo!\s*\(",
    r"\bpanic!\s*\(\s*[\"']todo",
    r"\bpass\b",
    r"return\s+0\s*;\s*$",
    r"return\s*;\s*$",
]


EMPTY_FUNCTION_PATTERNS = [
    r"\{\s*\}",
    r"\{\s*return\s*;\s*\}",
    r"\{\s*return\s+0\s*;\s*\}",
    r"\{\s*pass\s*\}",
]


def ensure_dir(directory):
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path, default=None):
    if default is None:
        default = {}
    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def resolve_repo_artifact_path(repo_name, directory, suffixes):
    for suffix in suffixes:
        candidate = os.path.join(directory, f"{repo_name}{suffix}")
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return candidate
    return os.path.join(directory, f"{repo_name}{suffixes[0]}")


def save_json_file(data, file_path):
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_text_file(text, file_path):
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)


def safe_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_number(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value, low=0.0, high=20.0):
    return max(low, min(high, value))


def normalize_module_name(module_name, file_path="", name="", summary=""):
    text = " ".join([
        str(module_name or ""),
        str(file_path or ""),
        str(name or ""),
        str(summary or ""),
    ]).lower().replace("\\", "/")

    for alias, canonical in CORE_MODULE_ALIASES.items():
        if alias.lower() in text:
            return canonical

    return "unknown"


def get_text_blob(function_item, code_text=""):
    return "\n".join([
        str(function_item.get("name", "")),
        str(function_item.get("file_path", "")),
        str(function_item.get("type", "")),
        str(function_item.get("summary", "")),
        "\n".join(str(x) for x in safe_list(function_item.get("logic_steps"))),
        "\n".join(str(x) for x in safe_list(function_item.get("called_functions"))),
        str(function_item.get("evidence", "")),
        str(function_item.get("uncertainty", "")),
        str(code_text or ""),
    ]).lower()


def build_code_block_map(code_blocks_data):
    block_map = {}
    for block in code_blocks_data.get("blocks", []):
        block_id = block.get("block_id")
        if block_id:
            block_map[block_id] = block
    return block_map


def detect_red_flags(code_text, analysis_text):
    red_flags = []
    text = f"{code_text}\n{analysis_text}".lower()

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            red_flags.append(f"命中占位/未完成模式：{pattern}")

    compact_code = re.sub(r"\s+", " ", code_text or "")
    for pattern in EMPTY_FUNCTION_PATTERNS:
        if re.search(pattern, compact_code, flags=re.IGNORECASE):
            red_flags.append(f"疑似空壳函数：{pattern}")

    weak_words = ["无法确定", "未展示", "不确定", "仅定义", "没有实际", "无法判断", "可能"]
    weak_count = sum(1 for word in weak_words if word in analysis_text)
    if weak_count >= 2:
        red_flags.append("函数理解结果存在较多不确定性表述")

    return red_flags


def analyze_function_quality(function_item, block_map):
    block = block_map.get(function_item.get("block_id"), {})
    code_text = block.get("content", "")
    function_type = str(function_item.get("type", block.get("type", ""))).lower()
    summary = str(function_item.get("summary", ""))
    logic_steps = safe_list(function_item.get("logic_steps"))
    called_functions = safe_list(function_item.get("called_functions"))
    evidence = str(function_item.get("evidence", ""))
    uncertainty = str(function_item.get("uncertainty", ""))
    file_path = function_item.get("file_path", block.get("file_path", ""))
    name = function_item.get("name", block.get("name", ""))

    module = normalize_module_name(
        function_item.get("related_os_module"),
        file_path=file_path,
        name=name,
        summary=summary,
    )

    analysis_text = "\n".join([summary, "\n".join(str(x) for x in logic_steps), evidence, uncertainty])
    text_blob = get_text_blob(function_item, code_text)

    red_flags = detect_red_flags(code_text, analysis_text)

    mechanism_hits = []
    data_hits = []
    strong_hits = []

    module_rules = MODULE_RULES.get(module, {})

    for keyword in module_rules.get("keywords", []):
        if keyword.lower() in text_blob:
            mechanism_hits.append(keyword)

    for keyword in module_rules.get("strong_keywords", []):
        if keyword.lower() in text_blob:
            strong_hits.append(keyword)

    for keyword in module_rules.get("data_keywords", []):
        if keyword.lower() in text_blob:
            data_hits.append(keyword)

    meaningful_line_count = 0
    for line in str(code_text).splitlines():
        line = line.strip()
        if line and not line.startswith("//") and not line.startswith("#") and not line.startswith("/*"):
            meaningful_line_count += 1

    score = 0.0

    if function_type in {"function", "method", "impl_item", "fn"}:
        score += 4
    elif function_type in {"struct", "enum", "class", "type"}:
        score += 2.5
    elif function_type in {"const", "static"}:
        score += 1

    score += min(len(logic_steps), 5) * 1.0
    score += min(len(called_functions), 5) * 0.7
    score += min(len(set(mechanism_hits)), 5) * 0.6
    score += min(len(set(strong_hits)), 4) * 1.0
    score += min(len(set(data_hits)), 3) * 0.8

    if meaningful_line_count >= 60:
        score += 3
    elif meaningful_line_count >= 25:
        score += 2
    elif meaningful_line_count >= 8:
        score += 1

    if evidence:
        score += 1

    if uncertainty and any(word in uncertainty for word in ["无法确定", "不确定", "未展示", "仅"]):
        score -= 1.5

    score -= min(len(red_flags) * 2.0, 8.0)
    score = clamp(score, 0, 20)

    if score >= 15:
        level = "strong"
    elif score >= 10:
        level = "medium"
    elif score >= 5:
        level = "weak"
    else:
        level = "shell_or_unclear"

    return {
        "block_id": function_item.get("block_id"),
        "name": name,
        "file_path": file_path,
        "type": function_type,
        "module": module,
        "score": round(score, 2),
        "level": level,
        "meaningful_line_count": meaningful_line_count,
        "called_function_count": len(called_functions),
        "logic_step_count": len(logic_steps),
        "mechanism_hits": sorted(set(mechanism_hits))[:10],
        "strong_mechanism_hits": sorted(set(strong_hits))[:10],
        "data_structure_hits": sorted(set(data_hits))[:10],
        "red_flags": red_flags[:8],
        "summary": summary[:300],
        "evidence": evidence[:300],
        "uncertainty": uncertainty[:300],
    }


def evaluate_module_quality(module_name, function_scores, repo_profile):
    module_function_scores = [item for item in function_scores if item.get("module") == module_name]
    module_profile = repo_profile.get("module_profiles", {}).get(module_name, {})

    real_functions = [item for item in module_function_scores if item.get("score", 0) >= 10]
    strong_functions = [item for item in module_function_scores if item.get("score", 0) >= 15]
    weak_functions = [item for item in module_function_scores if item.get("score", 0) < 5]

    all_mechanisms = set()
    all_data_structures = set()
    all_red_flags = []
    evidence = []

    for item in module_function_scores:
        all_mechanisms.update(item.get("mechanism_hits", []))
        all_mechanisms.update(item.get("strong_mechanism_hits", []))
        all_data_structures.update(item.get("data_structure_hits", []))
        all_red_flags.extend(item.get("red_flags", []))
        if item.get("score", 0) >= 10 and item.get("summary"):
            evidence.append(f"{item.get('name')}: {item.get('summary')}")

    function_count = len(module_function_scores)
    repo_module_count = safe_number(module_profile.get("function_count"), 0)
    outgoing_edges = safe_number(module_profile.get("outgoing_edge_count"), 0)
    internal_edges = safe_number(module_profile.get("internal_edge_count"), 0)
    module_completeness = safe_number(repo_profile.get("module_completeness", {}).get(module_name), 0)

    score = 0.0

    if function_count >= 15:
        score += 4
    elif function_count >= 8:
        score += 3
    elif function_count >= 3:
        score += 2
    elif function_count >= 1:
        score += 1

    if real_functions:
        score += min(len(real_functions), 6) * 1.5
    if strong_functions:
        score += min(len(strong_functions), 3) * 1.2

    if len(all_mechanisms) >= 8:
        score += 4
    elif len(all_mechanisms) >= 4:
        score += 3
    elif len(all_mechanisms) >= 2:
        score += 1.5

    if len(all_data_structures) >= 4:
        score += 2.5
    elif len(all_data_structures) >= 2:
        score += 1.5

    if outgoing_edges + internal_edges >= 30:
        score += 2
    elif outgoing_edges + internal_edges >= 10:
        score += 1

    if module_completeness >= 0.70:
        score += 2
    elif module_completeness >= 0.45:
        score += 1

    if function_count > 0:
        weak_ratio = len(weak_functions) / max(function_count, 1)
        if weak_ratio >= 0.6:
            score -= 4
        elif weak_ratio >= 0.35:
            score -= 2

    if len(all_red_flags) >= 8:
        score -= 4
    elif len(all_red_flags) >= 3:
        score -= 2

    # 如果 repo_profile 认为模块存在，但函数理解没有抓到对应函数，降分。
    if repo_module_count > 0 and function_count == 0:
        score -= 3

    score = clamp(score, 0, 20)

    if score >= 16:
        level = "strong_real_implementation"
    elif score >= 11:
        level = "medium_real_implementation"
    elif score >= 6:
        level = "weak_or_partial_implementation"
    else:
        level = "shell_or_missing"

    weaknesses = []
    if function_count == 0:
        weaknesses.append("未在函数理解结果中发现该模块的明确实现函数")
    if not real_functions:
        weaknesses.append("缺少得分较高的真实实现函数证据")
    if len(all_mechanisms) < 2:
        weaknesses.append("缺少关键机制关键词证据")
    if len(all_red_flags) > 0:
        weaknesses.append("存在 TODO、空壳或不确定性等风险信号")

    return {
        "module_name": module_name,
        "display_name": MODULE_RULES.get(module_name, {}).get("display_name", module_name),
        "score": round(score, 2),
        "max_score": 20,
        "implementation_level": level,
        "function_count": function_count,
        "real_function_count": len(real_functions),
        "strong_function_count": len(strong_functions),
        "weak_function_count": len(weak_functions),
        "repo_profile_function_count": repo_module_count,
        "module_completeness": module_completeness,
        "mechanism_hits": sorted(all_mechanisms)[:20],
        "data_structure_hits": sorted(all_data_structures)[:20],
        "red_flags": list(dict.fromkeys(all_red_flags))[:20],
        "evidence": evidence[:8],
        "weaknesses": weaknesses,
        "top_functions": sorted(
            module_function_scores,
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:8],
    }


def evaluate_chain_closure(module_scores, function_scores):
    present_modules = {name for name, data in module_scores.items() if data.get("score", 0) >= 6}
    strong_modules = {name for name, data in module_scores.items() if data.get("score", 0) >= 11}

    steps = []
    for step in CHAIN_STEPS:
        key = step["key"]
        status = "missing"
        if key in strong_modules:
            status = "strong"
        elif key in present_modules:
            status = "partial"
        steps.append({"key": key, "name": step["name"], "status": status})

    base_score = 0.0
    for item in steps:
        if item["status"] == "strong":
            base_score += 1.0
        elif item["status"] == "partial":
            base_score += 0.55

    base_score = base_score / len(steps)

    # 识别跨模块调用/文本证据。没有完整调用图，只用函数理解的 called_functions 与模块文本做静态证据近似。
    cross_module_evidence = []
    module_by_function_name = {}
    for item in function_scores:
        name = str(item.get("name", "")).lower()
        if name:
            module_by_function_name[name] = item.get("module")

    for item in function_scores:
        src_module = item.get("module")
        for keyword in item.get("mechanism_hits", []) + item.get("strong_mechanism_hits", []):
            keyword_lower = str(keyword).lower()
            target_module = module_by_function_name.get(keyword_lower)
            if target_module and target_module != src_module:
                cross_module_evidence.append(f"{item.get('name')}({src_module}) -> {keyword}({target_module})")

    cross_bonus = min(len(cross_module_evidence), 5) * 0.03
    chain_score_0_20 = clamp((base_score + cross_bonus) * 20, 0, 20)

    if chain_score_0_20 >= 15:
        level = "good_system_closure"
    elif chain_score_0_20 >= 10:
        level = "partial_system_closure"
    elif chain_score_0_20 >= 5:
        level = "weak_system_closure"
    else:
        level = "fragmented_modules"

    missing = [item["name"] for item in steps if item["status"] == "missing"]

    return {
        "score": round(chain_score_0_20, 2),
        "max_score": 20,
        "level": level,
        "steps": steps,
        "missing_steps": missing,
        "cross_module_evidence": cross_module_evidence[:10],
    }


def evaluate_engineering_evidence(repo_profile, code_blocks_data):
    repo_path = code_blocks_data.get("repo_path", "")
    blocks = code_blocks_data.get("blocks", [])
    file_paths = set()
    for block in blocks:
        file_path = str(block.get("file_path", "")).replace("\\", "/").lower()
        if file_path:
            file_paths.add(file_path)

    evidence = []
    missing = []

    def has_file_keyword(keywords):
        return any(any(keyword in path for keyword in keywords) for path in file_paths)

    checks = [
        ("readme", ["readme"], "存在 README/说明文档"),
        ("build", ["makefile", "cargo.toml", "cmakelists.txt", "build.rs", "meson.build"], "存在构建配置文件"),
        ("kernel_entry", ["main.c", "main.rs", "entry", "boot", "start"], "存在启动/入口相关文件"),
        ("test", ["test", "tests", "spec"], "存在测试或验证相关文件"),
        ("docs", ["doc", "docs", "manual"], "存在文档目录"),
    ]

    score = 0.0
    for key, keywords, description in checks:
        if has_file_keyword(keywords):
            evidence.append(description)
            score += 4
        else:
            missing.append(description)

    # 如果 code_blocks 不包含 README/Makefile 这类非代码文件，可能误判。给 repo_profile data_quality 一个兜底。
    data_sources = repo_profile.get("data_quality", {}).get("data_sources", [])
    if data_sources:
        score += 1
        evidence.append("已有 function_analysis/call_graph/module_summary 等分析数据来源")

    score = clamp(score, 0, 20)

    if score >= 14:
        level = "good_engineering_evidence"
    elif score >= 8:
        level = "partial_engineering_evidence"
    else:
        level = "weak_engineering_evidence"

    return {
        "score": round(score, 2),
        "max_score": 20,
        "level": level,
        "repo_path": repo_path,
        "evidence": evidence,
        "missing": missing,
        "note": "该项基于静态文件名和已有分析产物判断，不等同于真实编译运行测试。"
    }


def calculate_overall_implementation_score(module_scores, chain_closure, engineering_evidence):
    # 模块真实实现质量占 65%，关键链路闭环占 25%，工程证据占 10%。
    important_modules = ["memory", "process", "scheduler", "syscall", "interrupt", "filesystem", "driver", "boot", "user"]
    weighted_scores = []

    module_weights = {
        "memory": 1.20,
        "process": 1.15,
        "scheduler": 1.10,
        "syscall": 1.15,
        "interrupt": 1.05,
        "filesystem": 1.00,
        "driver": 0.85,
        "boot": 0.90,
        "user": 0.80,
    }

    total_weight = 0.0
    module_weighted_sum = 0.0

    for module in important_modules:
        data = module_scores.get(module)
        if not data:
            continue
        score = safe_number(data.get("score"), 0)
        weight = module_weights.get(module, 1.0)
        module_weighted_sum += score * weight
        total_weight += weight
        weighted_scores.append(score)

    if total_weight == 0:
        module_average = 0.0
    else:
        module_average = module_weighted_sum / total_weight

    chain_score = safe_number(chain_closure.get("score"), 0)
    engineering_score = safe_number(engineering_evidence.get("score"), 0)

    overall_20 = module_average * 0.65 + chain_score * 0.25 + engineering_score * 0.10
    overall_100 = round(overall_20 * 5, 2)

    if overall_100 >= 85:
        level = "excellent"
    elif overall_100 >= 70:
        level = "good"
    elif overall_100 >= 55:
        level = "medium"
    else:
        level = "weak"

    return overall_100, level, {
        "module_average_20": round(module_average, 2),
        "chain_score_20": round(chain_score, 2),
        "engineering_score_20": round(engineering_score, 2),
        "formula": "overall = module_average*0.65 + chain_closure*0.25 + engineering_evidence*0.10, then *5"
    }


def evaluate_implementation_quality(
    repo_profile_path,
    function_analysis_path=None,
    code_blocks_path=None,
    module_summary_path=None,
):
    repo_profile = load_json_file(repo_profile_path)
    repo_name = repo_profile.get("repo_name") or infer_repo_name_from_profile_path(repo_profile_path)

    if function_analysis_path is None:
        function_analysis_path = resolve_repo_artifact_path(
            repo_name,
            "function_analysis",
            ["_function_analysis_full.json", "_function_analysis.json"],
        )
    if code_blocks_path is None:
        code_blocks_path = os.path.join("code_blocks", f"{repo_name}_blocks.json")
    if module_summary_path is None:
        module_summary_path = os.path.join("module_summary", f"{repo_name}_module_summary_full.json")

    function_analysis = load_json_file(function_analysis_path, default={})
    code_blocks_data = load_json_file(code_blocks_path, default={})
    module_summary = load_json_file(module_summary_path, default={})

    block_map = build_code_block_map(code_blocks_data)
    functions = function_analysis.get("functions", [])

    function_scores = []
    for function_item in functions:
        function_scores.append(analyze_function_quality(function_item, block_map))

    modules_to_check = set(MODULE_RULES.keys())
    modules_to_check.update(repo_profile.get("module_profiles", {}).keys())
    modules_to_check.update(item.get("module") for item in function_scores if item.get("module"))
    modules_to_check.discard(None)
    modules_to_check.discard("unknown")

    module_scores = {}
    for module_name in sorted(modules_to_check):
        module_scores[module_name] = evaluate_module_quality(module_name, function_scores, repo_profile)

    chain_closure = evaluate_chain_closure(module_scores, function_scores)
    engineering_evidence = evaluate_engineering_evidence(repo_profile, code_blocks_data)

    overall_score, level, score_breakdown = calculate_overall_implementation_score(
        module_scores=module_scores,
        chain_closure=chain_closure,
        engineering_evidence=engineering_evidence,
    )

    red_flags = []
    for item in function_scores:
        for flag in item.get("red_flags", []):
            red_flags.append(f"{item.get('name')}: {flag}")

    strengths = []
    weaknesses = []

    for module_name, data in sorted(module_scores.items(), key=lambda x: x[1].get("score", 0), reverse=True):
        if data.get("score", 0) >= 14:
            strengths.append(f"{data.get('display_name', module_name)}模块存在较强真实实现证据，得分 {data.get('score')}/20。")
        elif data.get("score", 0) <= 6:
            weaknesses.append(f"{data.get('display_name', module_name)}模块实现证据较弱，得分 {data.get('score')}/20。")

    if chain_closure.get("score", 0) < 10:
        weaknesses.append("核心 OS 执行链路闭环证据不足，模块之间可能只是局部堆叠。")
    if engineering_evidence.get("score", 0) < 8:
        weaknesses.append("构建、文档或测试等工程证据不足，实际可运行性置信度较低。")

    confidence = "high"
    if len(function_scores) < 20 or overall_score < 55:
        confidence = "medium"
    if len(function_scores) < 8 or not code_blocks_data.get("blocks"):
        confidence = "low"

    return {
        "repo_name": repo_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "evaluator_version": "v6.1-implementation-quality-rule-based",
        "overall_implementation_score": overall_score,
        "implementation_level": level,
        "score_breakdown": score_breakdown,
        "module_scores": module_scores,
        "chain_closure": chain_closure,
        "engineering_evidence": engineering_evidence,
        "function_quality_summary": {
            "function_count": len(function_scores),
            "strong_function_count": len([x for x in function_scores if x.get("score", 0) >= 15]),
            "real_function_count": len([x for x in function_scores if x.get("score", 0) >= 10]),
            "weak_or_shell_function_count": len([x for x in function_scores if x.get("score", 0) < 5]),
        },
        "top_real_functions": sorted(function_scores, key=lambda x: x.get("score", 0), reverse=True)[:20],
        "red_flags": list(dict.fromkeys(red_flags))[:40],
        "strengths": strengths[:12],
        "weaknesses": weaknesses[:12],
        "confidence": confidence,
        "input_paths": {
            "repo_profile_path": repo_profile_path,
            "function_analysis_path": function_analysis_path,
            "code_blocks_path": code_blocks_path,
            "module_summary_path": module_summary_path,
        },
        "note": "本结果基于静态代码切块、函数语义理解、模块画像和启发式规则评估。它比单纯统计函数数量更可靠，但仍不等同于真实编译运行测试。"
    }


def infer_repo_name_from_profile_path(profile_path):
    file_name = os.path.basename(profile_path)
    suffix = "_repo_profile_full.json"
    if file_name.endswith(suffix):
        return file_name[:-len(suffix)]
    return os.path.splitext(file_name)[0]


def save_implementation_quality_result(result, output_dir="implementation_quality"):
    repo_name = result.get("repo_name", "unknown_repo")
    output_path = os.path.join(output_dir, f"{repo_name}_implementation_quality.json")
    save_json_file(result, output_path)
    return output_path


def format_implementation_quality_markdown(result):
    repo_name = result.get("repo_name", "unknown_repo")
    lines = []
    lines.append(f"# {repo_name} 真实实现质量评估报告")
    lines.append("")
    lines.append(f"- 综合实现质量分：**{result.get('overall_implementation_score')} / 100**")
    lines.append(f"- 等级：**{result.get('implementation_level')}**")
    lines.append(f"- 置信度：**{result.get('confidence')}**")
    lines.append("")

    breakdown = result.get("score_breakdown", {})
    lines.append("## 一、评分构成")
    lines.append("")
    lines.append(f"- 模块真实实现均分：{breakdown.get('module_average_20')} / 20")
    lines.append(f"- 核心链路闭环分：{breakdown.get('chain_score_20')} / 20")
    lines.append(f"- 工程证据分：{breakdown.get('engineering_score_20')} / 20")
    lines.append(f"- 公式：{breakdown.get('formula')}")
    lines.append("")

    lines.append("## 二、核心模块真实实现质量")
    lines.append("")
    lines.append("| 模块 | 得分 | 等级 | 真实函数 | 风险函数 |")
    lines.append("|---|---:|---|---:|---:|")
    for module_name, data in sorted(result.get("module_scores", {}).items(), key=lambda x: x[1].get("score", 0), reverse=True):
        lines.append(
            f"| {data.get('display_name', module_name)} | {data.get('score')} | {data.get('implementation_level')} | "
            f"{data.get('real_function_count')} | {data.get('weak_function_count')} |"
        )
    lines.append("")

    lines.append("## 三、关键链路闭环")
    lines.append("")
    for step in result.get("chain_closure", {}).get("steps", []):
        lines.append(f"- {step.get('name')}：{step.get('status')}")
    lines.append("")

    lines.append("## 四、主要优势")
    lines.append("")
    for item in result.get("strengths", []):
        lines.append(f"- {item}")
    if not result.get("strengths"):
        lines.append("- 暂无明确高强度实现优势。")
    lines.append("")

    lines.append("## 五、主要不足")
    lines.append("")
    for item in result.get("weaknesses", []):
        lines.append(f"- {item}")
    if not result.get("weaknesses"):
        lines.append("- 暂无明显不足。")
    lines.append("")

    lines.append("## 六、风险信号")
    lines.append("")
    for item in result.get("red_flags", [])[:20]:
        lines.append(f"- {item}")
    if not result.get("red_flags"):
        lines.append("- 未发现明显 TODO、空壳函数或未完成实现信号。")
    lines.append("")

    lines.append("## 七、说明")
    lines.append("")
    lines.append(result.get("note", ""))

    return "\n".join(lines)


def save_implementation_quality_markdown(result, output_dir="implementation_quality"):
    repo_name = result.get("repo_name", "unknown_repo")
    output_path = os.path.join(output_dir, f"{repo_name}_implementation_quality.md")
    save_text_file(format_implementation_quality_markdown(result), output_path)
    return output_path


def format_implementation_quality_preview(result, json_path=None, md_path=None):
    lines = []
    lines.append("真实实现质量评估完成。")
    lines.append("")
    lines.append(f"仓库：{result.get('repo_name')}")
    lines.append(f"综合实现质量分：{result.get('overall_implementation_score')} / 100")
    lines.append(f"等级：{result.get('implementation_level')}")
    lines.append(f"置信度：{result.get('confidence')}")
    if json_path:
        lines.append(f"JSON：{json_path}")
    if md_path:
        lines.append(f"Markdown：{md_path}")
    lines.append("")
    lines.append("模块得分：")
    for module_name, data in sorted(result.get("module_scores", {}).items(), key=lambda x: x[1].get("score", 0), reverse=True):
        lines.append(f"- {data.get('display_name', module_name)}: {data.get('score')} / 20 | {data.get('implementation_level')}")
    return "\n".join(lines)
