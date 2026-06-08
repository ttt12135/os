import os
import re
from src.file_scorer import get_file_score_info
from src.ast_parser import parse_code_blocks_with_tree_sitter


def is_code_file(file_path):
    """
    判断是否是适合切分的代码文件。
    """

    code_extensions = {
        ".py",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cc",
        ".S",
        ".s",
        ".asm",
        ".java",
        ".js",
        ".ts",
        ".sh",
        ".bash",
    }

    file_name = os.path.basename(file_path).lower()
    _, ext = os.path.splitext(file_path)

    if file_name in {"makefile", "cmakelists.txt"}:
        return True

    if file_name in {"cargo.toml", "build.rs"}:
        return True

    if ext.lower() in {".ld", ".lds", ".toml"}:
        return True

    return ext in code_extensions or ext.lower() in code_extensions


def detect_language(file_path):
    """
    根据扩展名判断代码语言。
    """

    file_name = os.path.basename(file_path).lower()
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".py":
        return "python"

    if ext == ".sh":
        return "bash"

    if ext == ".rs":
        return "rust"

    if ext in {".c", ".h"}:
        return "c"

    if ext in {".cpp", ".hpp", ".cc"}:
        return "cpp"

    if ext in {".S", ".s", ".asm"}:
        return "assembly"

    if file_name == "makefile":
        return "makefile"

    if file_name == "cmakelists.txt":
        return "cmake"

    if file_name == "cargo.toml":
        return "cargo"

    if ext in {".ld", ".lds"}:
        return "linker_script"

    if ext == ".toml":
        return "toml"

    if ext == ".java":
        return "java"

    if ext in {".js", ".ts"}:
        return "javascript"

    return "unknown"


def read_code_file(file_path):
    """
    安全读取代码文件内容。
    """

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as file:
                return file.read()
        except UnicodeDecodeError:
            return ""
    except PermissionError:
        return ""
    except FileNotFoundError:
        return ""


def get_line_number(content, index):
    """
    根据字符下标计算行号。
    """
    return content.count("\n", 0, index) + 1


def find_matching_brace(content, open_brace_index):
    """
    从一个左大括号位置开始，找到匹配的右大括号位置。

    这是一个轻量级括号匹配器，不是完整语法解析器。
    但比“切到下一个函数开头”更稳定。
    """

    if open_brace_index < 0 or open_brace_index >= len(content):
        return -1

    if content[open_brace_index] != "{":
        return -1

    depth = 0
    index = open_brace_index
    in_string = False
    string_char = ""
    escape = False
    in_line_comment = False
    in_block_comment = False

    while index < len(content):
        char = content[index]
        next_char = content[index + 1] if index + 1 < len(content) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == string_char:
                in_string = False

            index += 1
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue

        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue

        if char in {"\"", "'"}:
            in_string = True
            string_char = char
            index += 1
            continue

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                return index

        index += 1

    return -1


def build_block(block_type, name, content, start_index, end_index, language):
    """
    构造统一格式的代码块。
    """

    block_content = content[start_index:end_index].strip()

    return {
        "type": block_type,
        "name": name,
        "language": language,
        "start_line": get_line_number(content, start_index),
        "end_line": get_line_number(content, end_index),
        "content": block_content
    }


def split_python_code(content):
    """
    按 Python 的 def / class 粗略切分代码块。
    """

    pattern = r"(?m)^(def\s+\w+\s*\(.*?\):|class\s+\w+.*?:)"
    matches = list(re.finditer(pattern, content))

    blocks = []

    if len(matches) == 0:
        return blocks

    for index, match in enumerate(matches):
        start = match.start()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(content)

        header = match.group(1)

        if header.startswith("def "):
            block_type = "function"
            name = header.split("def ")[1].split("(")[0].strip()
        elif header.startswith("class "):
            block_type = "class"
            name = header.split("class ")[1].split("(")[0].split(":")[0].strip()
        else:
            block_type = "unknown"
            name = "unknown"

        blocks.append(
            build_block(
                block_type=block_type,
                name=name,
                content=content,
                start_index=start,
                end_index=end,
                language="python"
            )
        )

    return blocks


def split_rust_code(content):
    """
    增强版 Rust 代码切分。

    支持：
    - fn / pub fn / async fn / unsafe fn / const fn / extern "C" fn
    - struct / enum / trait
    - impl Xxx
    - impl Trait for Xxx
    - macro_rules!
    - const / static
    """

    blocks = []

    patterns = [
        (
            "function",
            r"(?m)^\s*(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?(?:unsafe\s+)?(?:const\s+)?(?:extern\s+\"[^\"]+\"\s+)?fn\s+([A-Za-z_]\w*)\s*[<(]"
        ),
        (
            "struct",
            r"(?m)^\s*(?:pub(?:\([^)]+\))?\s+)?struct\s+([A-Za-z_]\w*)"
        ),
        (
            "enum",
            r"(?m)^\s*(?:pub(?:\([^)]+\))?\s+)?enum\s+([A-Za-z_]\w*)"
        ),
        (
            "trait",
            r"(?m)^\s*(?:pub(?:\([^)]+\))?\s+)?trait\s+([A-Za-z_]\w*)"
        ),
        (
            "impl",
            r"(?m)^\s*impl(?:<[^>]+>)?\s+([^{\n]+)"
        ),
        (
            "macro",
            r"(?m)^\s*macro_rules!\s+([A-Za-z_]\w*)"
        ),
        (
            "const",
            r"(?m)^\s*(?:pub(?:\([^)]+\))?\s+)?const\s+([A-Za-z_]\w*)\s*:"
        ),
        (
            "static",
            r"(?m)^\s*(?:pub(?:\([^)]+\))?\s+)?static\s+(?:mut\s+)?([A-Za-z_]\w*)\s*:"
        ),
    ]

    matches = []

    for block_type, pattern in patterns:
        for match in re.finditer(pattern, content):
            matches.append(
                {
                    "type": block_type,
                    "name": match.group(1).strip(),
                    "start": match.start(),
                    "header_end": match.end()
                }
            )

    matches.sort(key=lambda item: item["start"])

    for index, item in enumerate(matches):
        start = item["start"]

        brace_pos = content.find("{", item["header_end"])

        if brace_pos != -1:
            next_start = matches[index + 1]["start"] if index + 1 < len(matches) else len(content)

            if brace_pos < next_start:
                close_brace = find_matching_brace(content, brace_pos)

                if close_brace != -1:
                    end = close_brace + 1
                else:
                    end = next_start
            else:
                end = next_start
        else:
            # const/static 或声明式代码，切到下一块开始
            end = matches[index + 1]["start"] if index + 1 < len(matches) else len(content)

        blocks.append(
            build_block(
                block_type=item["type"],
                name=item["name"],
                content=content,
                start_index=start,
                end_index=end,
                language="rust"
            )
        )

    return remove_duplicate_blocks(blocks)


def split_c_code(content, language="c"):
    """
    增强版 C / C++ 代码切分。

    支持：
    - 普通函数
    - static / inline / extern 函数
    - struct / typedef struct
    - enum / typedef enum
    """

    blocks = []

    # C/C++ 函数定义。排除 if/for/while/switch 等控制语句。
    function_pattern = (
        r"(?m)^\s*"
        r"(?:static\s+)?(?:inline\s+)?(?:extern\s+)?(?:const\s+)?"
        r"[A-Za-z_][\w\s\*\(\),]*?\s+"
        r"([A-Za-z_]\w*)\s*"
        r"\([^;{}]*\)\s*"
        r"\{"
    )

    invalid_names = {
        "if",
        "for",
        "while",
        "switch",
        "return",
        "sizeof",
        "do"
    }

    for match in re.finditer(function_pattern, content):
        name = match.group(1)

        if name in invalid_names:
            continue

        open_brace = content.find("{", match.start(), match.end() + 1)
        close_brace = find_matching_brace(content, open_brace)

        if close_brace == -1:
            continue

        blocks.append(
            build_block(
                block_type="function",
                name=name,
                content=content,
                start_index=match.start(),
                end_index=close_brace + 1,
                language=language
            )
        )

    # typedef struct / struct
    struct_patterns = [
        r"(?ms)^\s*typedef\s+struct\s+([A-Za-z_]\w*)?\s*\{.*?\}\s*([A-Za-z_]\w*)\s*;",
        r"(?ms)^\s*struct\s+([A-Za-z_]\w*)\s*\{.*?\}\s*;",
    ]

    for pattern in struct_patterns:
        for match in re.finditer(pattern, content):
            if len(match.groups()) >= 2 and match.group(2):
                name = match.group(2)
            else:
                name = match.group(1) if match.group(1) else "anonymous_struct"

            blocks.append(
                build_block(
                    block_type="struct",
                    name=name,
                    content=content,
                    start_index=match.start(),
                    end_index=match.end(),
                    language=language
                )
            )

    # enum / typedef enum
    enum_patterns = [
        r"(?ms)^\s*typedef\s+enum\s+([A-Za-z_]\w*)?\s*\{.*?\}\s*([A-Za-z_]\w*)\s*;",
        r"(?ms)^\s*enum\s+([A-Za-z_]\w*)\s*\{.*?\}\s*;",
    ]

    for pattern in enum_patterns:
        for match in re.finditer(pattern, content):
            if len(match.groups()) >= 2 and match.group(2):
                name = match.group(2)
            else:
                name = match.group(1) if match.group(1) else "anonymous_enum"

            blocks.append(
                build_block(
                    block_type="enum",
                    name=name,
                    content=content,
                    start_index=match.start(),
                    end_index=match.end(),
                    language=language
                )
            )

    blocks.sort(key=lambda item: item["start_line"])

    return remove_duplicate_blocks(blocks)


def split_assembly_code(content):
    """
    轻量切分汇编代码。

    主要识别标签，例如：
    _start:
    trap_entry:
    context_switch:
    """

    blocks = []

    pattern = r"(?m)^([A-Za-z_.$][\w.$]*):\s*$"
    matches = list(re.finditer(pattern, content))

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        name = match.group(1)

        blocks.append(
            build_block(
                block_type="assembly_label",
                name=name,
                content=content,
                start_index=start,
                end_index=end,
                language="assembly"
            )
        )

    return blocks


def split_text_config_file(file_path, content):
    """
    对 Makefile / Cargo.toml / linker script 等配置文件做轻量切分。

    这些不是函数，但对 OS 项目分析很重要。
    """

    language = detect_language(file_path)
    file_name = os.path.basename(file_path)

    if content.strip() == "":
        return []

    return [
        {
            "type": "config",
            "name": file_name,
            "language": language,
            "start_line": 1,
            "end_line": len(content.splitlines()),
            "content": content.strip()
        }
    ]


def remove_duplicate_blocks(blocks):
    """
    去除起止行相同的重复块。
    """

    result = []
    seen = set()

    for block in blocks:
        key = (
            block.get("type"),
            block.get("name"),
            block.get("start_line"),
            block.get("end_line")
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(block)

    return result


def split_code_content(file_path, content):
    """
    根据文件类型选择不同切分方式。

    Rust / C / C++ / Python / Bash 优先使用 tree-sitter AST 解析；
    如果 AST 解析失败，再回退到原来的正则切分。
    """

    language = detect_language(file_path)
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    file_name = os.path.basename(file_path).lower()

    if language in {"rust", "c", "cpp", "python", "bash"}:
        ast_blocks = parse_code_blocks_with_tree_sitter(file_path, content)

        if len(ast_blocks) > 0:
            return ast_blocks

    if language == "python":
        return split_python_code(content)

    if language == "rust":
        return split_rust_code(content)

    if language == "c":
        return split_c_code(content, language="c")

    if language == "cpp":
        return split_c_code(content, language="cpp")

    if language == "assembly":
        return split_assembly_code(content)

    if file_name in {"makefile", "cmakelists.txt", "cargo.toml"}:
        return split_text_config_file(file_path, content)

    if ext in {".ld", ".lds", ".toml"}:
        return split_text_config_file(file_path, content)

    if ext in {".java", ".js", ".ts"}:
        return split_c_code(content, language=language)

    return []


def collect_code_blocks(repo_path, max_files=50, max_blocks=200):
    """
    扫描仓库并收集代码块

    当前函数保留用于调试
    """

    ignore_dirs = {
       ".git",
        "__pycache__",
        ".idea",
        ".vscode",
        "node_modules",
        ".venv",
        "venv",
        "target",
        "build",
        "dist",
        "out",
        ".cargo",

        "code_blocks",
        "function_analysis",
        "call_graph",
        "module_summary",
        "repo_profiles",
        "reports",
        "history_knowledge_base",
    }

    code_files = []

    for current_path, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = os.path.join(current_path, file_name)

            if is_code_file(file_path):
                code_files.append(file_path)

    code_files.sort()

    all_blocks = []
    scanned_files = 0

    for file_path in code_files:
        if scanned_files >= max_files:
            break

        content = read_code_file(file_path)

        if content == "":
            continue

        blocks = split_code_content(file_path, content)
        relative_path = os.path.relpath(file_path, repo_path)

        scanned_files += 1

        for block in blocks:
            all_blocks.append(
                {
                    all_blocks.append(
                        {
                            "file_path": file_info["relative_path"],
                            "file_score": file_info["score"],
                            "language": block.get("language", detect_language(file_path)),
                            "parser": block.get("parser", "regex"),
                            "start_line": block.get("start_line"),
                            "end_line": block.get("end_line"),
                            "type": block["type"],
                            "name": block["name"],
                            "content": block["content"]
                        }
)
                }
            )

            if len(all_blocks) >= max_blocks:
                return all_blocks

    return all_blocks


def collect_code_blocks_from_scored_files(repo_path, max_files=30, max_blocks=200):
    """
    从高分关键文件中收集代码块。

    这个函数不会盲目扫描整个仓库，
    而是先给代码文件打分，再优先切分高分文件。
    """

    ignore_dirs = {
        ".git",
        "__pycache__",
        ".idea",
        ".vscode",
        "node_modules",
        ".venv",
        "venv",
        "target",
        "build",
        "dist",
        "out",
        ".cargo",

        "code_blocks",
        "function_analysis",
        "call_graph",
        "module_summary",
        "repo_profiles",
        "reports",
        "history_knowledge_base",
    }

    scored_files = []

    for current_path, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = os.path.join(current_path, file_name)

            if not is_code_file(file_path):
                continue

            score_info = get_file_score_info(file_path, repo_path)
            score = score_info["score"]

            if score <= 0:
                continue

            scored_files.append(
                {
                    "file_path": file_path,
                    "relative_path": score_info["path"],
                    "score": score
                }
            )

    scored_files.sort(key=lambda item: item["score"], reverse=True)

    selected_files = scored_files[:max_files]

    all_blocks = []

    for file_info in selected_files:
        file_path = file_info["file_path"]
        content = read_code_file(file_path)

        if content == "":
            continue

        blocks = split_code_content(file_path, content)

        for block in blocks:
            all_blocks.append(
                {
                    "file_path": file_info["relative_path"],
                    "file_score": file_info["score"],
                    "language": block.get("language", detect_language(file_path)),
                    "parser": block.get("parser", "regex"),
                    "start_line": block.get("start_line"),
                    "end_line": block.get("end_line"),
                    "type": block["type"],
                    "name": block["name"],
                    "content": block["content"]
                }
            )

            if len(all_blocks) >= max_blocks:
                return all_blocks

    return all_blocks

def collect_all_code_blocks(repo_path, max_blocks=None):
    """
    全仓库收集代码块。

    这个函数用于 full 模式：
    - 不只扫描高分文件
    - 会尽量扫描整个仓库的所有代码文件
    - 每个代码块仍然保留 file_score，方便后续排序和分析
    """

    ignore_dirs = {
        ".git",
        "__pycache__",
        ".idea",
        ".vscode",
        "node_modules",
        ".venv",
        "venv",
        "target",
        "build",
        "dist",
        "out",
        ".cargo",

        "code_blocks",
        "function_analysis",
        "call_graph",
        "module_summary",
        "repo_profiles",
        "reports",
        "history_knowledge_base",
    }

    code_files = []

    for current_path, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = os.path.join(current_path, file_name)

            if is_code_file(file_path):
                code_files.append(file_path)

    scored_files = []

    for file_path in code_files:
        score_info = get_file_score_info(file_path, repo_path)

        scored_files.append(
            {
                "file_path": file_path,
                "relative_path": score_info["path"],
                "score": score_info["score"]
            }
        )

    # full 模式仍然优先把高分文件放前面，但不会丢掉低分文件
    scored_files.sort(key=lambda item: item["score"], reverse=True)

    all_blocks = []

    for file_info in scored_files:
        file_path = file_info["file_path"]
        content = read_code_file(file_path)

        if content == "":
            continue

        blocks = split_code_content(file_path, content)

        for block in blocks:
            all_blocks.append(
                {
                    "file_path": file_info["relative_path"],
                    "file_score": file_info["score"],
                    "language": block.get("language", detect_language(file_path)),
                    "parser": block.get("parser", "regex"),
                    "start_line": block.get("start_line"),
                    "end_line": block.get("end_line"),
                    "type": block["type"],
                    "name": block["name"],
                    "content": block["content"]
                }
            )

            if max_blocks is not None and len(all_blocks) >= max_blocks:
                return all_blocks

    return all_blocks

def format_code_blocks(blocks, max_chars_per_block=1200):
    """
    把代码块格式化成适合终端查看的文本。
    """

    if len(blocks) == 0:
        return "没有提取到代码块。"

    output = []

    for index, block in enumerate(blocks, start=1):
        content = block["content"]

        if len(content) > max_chars_per_block:
            content = content[:max_chars_per_block] + "\n......代码块过长，后面部分已省略......"

        output.append(f"代码块 {index}")
        output.append(f"文件：{block['file_path']}")
        output.append(f"语言：{block.get('language', 'unknown')}")
        output.append(f"行号：{block.get('start_line')} - {block.get('end_line')}")
        output.append(f"类型：{block['type']}")
        output.append(f"名称：{block['name']}")
        output.append("内容：")
        output.append(content)
        output.append("-" * 80)

    return "\n".join(output)