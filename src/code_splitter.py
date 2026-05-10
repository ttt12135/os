import os
import re


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
        ".java",
        ".js",
        ".ts"
    }

    _, ext = os.path.splitext(file_path)
    return ext.lower() in code_extensions


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
        block_content = content[start:end].strip()

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
            {
                "type": block_type,
                "name": name,
                "content": block_content
            }
        )

    return blocks


def split_rust_code(content):
    """
    按 Rust 的 fn / struct / impl 粗略切分代码块。
    """

    pattern = r"(?m)^(\s*(pub\s+)?(async\s+)?fn\s+\w+\s*\(.*|\s*(pub\s+)?struct\s+\w+.*|\s*impl\s+.*)"
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

        header = match.group(1).strip()
        block_content = content[start:end].strip()

        if "fn " in header:
            block_type = "function"
            name_part = header.split("fn ")[1]
            name = name_part.split("(")[0].strip()
        elif "struct " in header:
            block_type = "struct"
            name_part = header.split("struct ")[1]
            name = name_part.split("{")[0].split(";")[0].strip()
        elif header.startswith("impl"):
            block_type = "impl"
            name = header
        else:
            block_type = "unknown"
            name = "unknown"

        blocks.append(
            {
                "type": block_type,
                "name": name,
                "content": block_content
            }
        )

    return blocks


def split_c_like_code(content):
    """
    粗略切分 C / C++ / Java / JS / TS 代码。
    这个版本不做精确语法分析，只通过函数形态做初步切分。
    """

    pattern = r"(?m)^[a-zA-Z_][\w\s\*\&:<>,~]*\s+([a-zA-Z_]\w*)\s*\([^;]*\)\s*\{"
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

        name = match.group(1).strip()
        block_content = content[start:end].strip()

        blocks.append(
            {
                "type": "function",
                "name": name,
                "content": block_content
            }
        )

    return blocks


def split_code_content(file_path, content):
    """
    根据文件类型选择不同切分方式。
    """

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".py":
        return split_python_code(content)

    if ext == ".rs":
        return split_rust_code(content)

    if ext in {".c", ".h", ".cpp", ".hpp", ".java", ".js", ".ts"}:
        return split_c_like_code(content)

    return []


def collect_code_blocks(repo_path, max_files=10, max_blocks=80):
    """
    扫描仓库并收集代码块。

    当前版本先扫描所有代码文件。
    后面可以和 file_scorer 结合，只切分高评分文件。
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
        "dist"
    }

    code_files = []

    for current_path, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = os.path.join(current_path, file_name)

            if is_code_file(file_path):
                code_files.append(file_path)

    code_files = code_files[:max_files]

    all_blocks = []

    for file_path in code_files:
        content = read_code_file(file_path)

        if content == "":
            continue

        blocks = split_code_content(file_path, content)
        relative_path = os.path.relpath(file_path, repo_path)

        for block in blocks:
            all_blocks.append(
                {
                    "file_path": relative_path,
                    "type": block["type"],
                    "name": block["name"],
                    "content": block["content"]
                }
            )

            if len(all_blocks) >= max_blocks:
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
        output.append(f"类型：{block['type']}")
        output.append(f"名称：{block['name']}")
        output.append("内容：")
        output.append(content)
        output.append("-" * 80)

    return "\n".join(output)