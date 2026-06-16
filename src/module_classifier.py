def normalize_text(text):
    """
    统一小写
    """

    if text is None:
        return ""

    return str(text).replace("\\", "/").lower()


def match_keywords(text, keywords):
    """
    判断文本中是否包含任一关键词。
    """

    for keyword in keywords:
        if keyword in text:
            return True

    return False


MODULE_RULES = {
    "memory": {
        "path_keywords": [
            "mm", "memory", "page", "pmm", "vmm", "heap", "alloc", "malloc"
        ],
        "name_keywords": [
            "alloc", "free", "page", "memory", "mem", "kmalloc", "kfree",
            "map", "unmap", "pte", "pde", "vm", "copy_from_user", "copy_to_user"
        ]
    },
    "process": {
        "path_keywords": [
            "proc", "process", "task", "thread", "fork", "exec"
        ],
        "name_keywords": [
            "proc", "process", "task", "thread", "fork", "exec", "wait",
            "exit", "clone", "spawn"
        ]
    },
    "scheduler": {
        "path_keywords": [
            "sched", "scheduler"
        ],
        "name_keywords": [
            "schedule", "scheduler", "yield", "switch", "context_switch",
            "run_queue", "pick_next"
        ]
    },
    "filesystem": {
        "path_keywords": [
            "fs", "file", "inode", "vfs", "fat", "ext", "dir", "path"
        ],
        "name_keywords": [
            "file", "inode", "open", "close", "read", "write", "mkdir",
            "unlink", "lookup", "mount", "vfs", "dir"
        ]
    },
    "syscall": {
        "path_keywords": [
            "syscall", "sys"
        ],
        "name_keywords": [
            "syscall", "sys_", "syscall_handler", "do_syscall"
        ]
    },
    "driver": {
        "path_keywords": [
            "driver", "drivers", "dev", "device", "uart", "virtio",
            "block", "disk", "console", "tty", "keyboard"
        ],
        "name_keywords": [
            "driver", "device", "uart", "virtio", "disk", "block",
            "console", "tty", "keyboard", "read_reg", "write_reg"
        ]
    },
    "interrupt": {
        "path_keywords": [
            "trap", "irq", "interrupt", "exception", "idt", "isr"
        ],
        "name_keywords": [
            "trap", "irq", "interrupt", "exception", "handler", "idt",
            "isr", "fault"
        ]
    },
    "network": {
        "path_keywords": [
            "net", "network", "tcp", "udp", "ip", "ethernet", "socket"
        ],
        "name_keywords": [
            "net", "tcp", "udp", "ip", "socket", "packet", "ethernet"
        ]
    },
    "ipc": {
        "path_keywords": [
            "ipc", "pipe", "signal", "msg", "semaphore", "mutex"
        ],
        "name_keywords": [
            "ipc", "pipe", "signal", "semaphore", "mutex", "lock",
            "spinlock", "message"
        ]
    },
    "build": {
        "path_keywords": [
            "makefile", "cmake", "cargo", "build", "linker", "ld"
        ],
        "name_keywords": [
            "build", "link"
        ]
    },
    "test": {
        "path_keywords": [
            "test", "tests", "unittest", "benchmark"
        ],
        "name_keywords": [
            "test", "bench"
        ]
    },
    "user": {
        "path_keywords": [
            "user", "usr", "apps", "app", "shell", "bin"
        ],
        "name_keywords": [
            "main", "shell", "user"
        ]
    }
}


def classify_by_rules(file_path, function_name):
    """
    根据文件路径和函数名进行规则分类。
    """

    path_text = normalize_text(file_path)
    name_text = normalize_text(function_name)

    scores = {}

    for module_name, rules in MODULE_RULES.items():
        score = 0

        if match_keywords(path_text, rules.get("path_keywords", [])):
            score += 2

        if match_keywords(name_text, rules.get("name_keywords", [])):
            score += 3

        if score > 0:
            scores[module_name] = score

    if not scores:
        return "unknown", 0

    best_module = max(scores.items(), key=lambda item: item[1])

    return best_module[0], best_module[1]


def normalize_ai_module(ai_module):
    """
    规范化 AI 输出的模块名称
    """

    text = normalize_text(ai_module)

    alias_map = {
        "mm": "memory",
        "memory management": "memory",
        "process management": "process",
        "task": "process",
        "thread": "process",
        "scheduling": "scheduler",
        "scheduler": "scheduler",
        "file system": "filesystem",
        "fs": "filesystem",
        "vfs": "filesystem",
        "system call": "syscall",
        "system calls": "syscall",
        "device": "driver",
        "device driver": "driver",
        "drivers": "driver",
        "irq": "interrupt",
        "trap": "interrupt",
        "exception": "interrupt",
        "networking": "network",
        "unknown": "unknown",
        "": "unknown"
    }

    if text in alias_map:
        return alias_map[text]

    valid_modules = set(MODULE_RULES.keys())
    valid_modules.add("unknown")

    if text in valid_modules:
        return text

    return "unknown"


def classify_os_module(file_path, function_name, ai_module=None):
    """
    综合 AI 分类和规则分类，输出最终 OS 模块。

    优先级：
    1. 如果规则得分较高，采用规则结果
    2. 如果规则不确定，但 AI 给出有效模块，采用 AI 结果
    3. 否则 unknown
    """

    ai_module = normalize_ai_module(ai_module)
    rule_module, rule_score = classify_by_rules(file_path, function_name)

    if rule_score >= 3:
        return rule_module

    if ai_module != "unknown":
        return ai_module

    if rule_module != "unknown":
        return rule_module

    return "unknown"