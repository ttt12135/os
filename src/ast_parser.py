import os


try:
    from tree_sitter import Language, Parser

    import tree_sitter_rust
    import tree_sitter_c
    import tree_sitter_cpp
    import tree_sitter_python
    import tree_sitter_bash

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


def detect_ast_language(file_path):
    """
    根据文件后缀判断 tree-sitter 语言名称。
    """

    file_name = os.path.basename(file_path).lower()
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".rs":
        return "rust"

    if ext in {".c", ".h"}:
        return "c"

    if ext in {".cpp", ".hpp", ".cc"}:
        return "cpp"

    if ext == ".py":
        return "python"

    if ext == ".sh":
        return "bash"

    return None


def get_parser_for_language(language):
    """
    根据语言名称创建 tree-sitter Parser。
    使用本地单语言 grammar 包，不依赖 GitHub 下载
    """

    if not TREE_SITTER_AVAILABLE:
        return None

    parser = Parser()

    try:
        if language == "rust":
            parser.language = Language(tree_sitter_rust.language())
            return parser

        if language == "c":
            parser.language = Language(tree_sitter_c.language())
            return parser

        if language == "cpp":
            parser.language = Language(tree_sitter_cpp.language())
            return parser

        if language == "python":
            parser.language = Language(tree_sitter_python.language())
            return parser

        if language == "bash":
            parser.language = Language(tree_sitter_bash.language())
            return parser

    except Exception:
        return None

    return None


def get_node_text(source_bytes, node):
    """
    根据 AST 节点取源码文本。
    """

    return source_bytes[node.start_byte:node.end_byte].decode(
        "utf-8",
        errors="ignore"
    )


def get_first_line(text):
    """
    取代码块第一行，用于 impl 等不容易提取名字的节点。
    """

    lines = text.strip().splitlines()

    if len(lines) == 0:
        return "unknown"

    return lines[0].strip()


def walk_tree(node):
    """
    深度遍历 AST。
    """

    yield node

    for child in node.children:
        yield from walk_tree(child)


def find_first_named_child_text(source_bytes, node, wanted_types):
    """
    在节点内部查找第一个指定类型的子节点文本。
    """

    for child in walk_tree(node):
        if child.type in wanted_types:
            return get_node_text(source_bytes, child)

    return None


def find_last_named_child_text(source_bytes, node, wanted_types):
    """
    在节点内部查找最后一个指定类型的子节点文本。
    """

    result = None

    for child in walk_tree(node):
        if child.type in wanted_types:
            result = get_node_text(source_bytes, child)

    return result


def get_rust_node_name(source_bytes, node):
    """
    提取 Rust AST 节点名称。
    """

    if node.type in {
        "function_item",
        "struct_item",
        "enum_item",
        "trait_item",
        "const_item",
        "static_item",
        "macro_definition"
    }:
        name_node = node.child_by_field_name("name")

        if name_node is not None:
            return get_node_text(source_bytes, name_node)

        name = find_first_named_child_text(
            source_bytes,
            node,
            {"identifier", "type_identifier"}
        )

        if name:
            return name

    if node.type == "impl_item":
        text = get_node_text(source_bytes, node)
        return get_first_line(text)

    return "unknown"


def get_c_node_name(source_bytes, node):
    """
    提取 C / C++ AST 节点名称。
    """

    if node.type == "function_definition":
        name = find_first_named_child_text(
            source_bytes,
            node,
            {"identifier", "field_identifier"}
        )

        if name:
            return name

    if node.type in {"struct_specifier", "enum_specifier"}:
        name = find_first_named_child_text(
            source_bytes,
            node,
            {"type_identifier", "identifier"}
        )

        if name:
            return name

    if node.type == "type_definition":
        name = find_last_named_child_text(
            source_bytes,
            node,
            {"type_identifier", "identifier"}
        )

        if name:
            return name

    return "unknown"


def get_python_node_name(source_bytes, node):
    """
    提取 Python 函数 / 类名称。
    """

    name_node = node.child_by_field_name("name")

    if name_node is not None:
        return get_node_text(source_bytes, name_node)

    name = find_first_named_child_text(
        source_bytes,
        node,
        {"identifier"}
    )

    if name:
        return name

    return "unknown"


def get_bash_node_name(source_bytes, node):
    """
    提取 Bash 函数名称。
    """

    name = find_first_named_child_text(
        source_bytes,
        node,
        {"word", "identifier"}
    )

    if name:
        return name

    return "unknown"


def map_rust_node_type(node_type):
    """
    把 Rust AST 节点类型映射成项目内部代码块类型。
    """

    mapping = {
        "function_item": "function",
        "struct_item": "struct",
        "enum_item": "enum",
        "trait_item": "trait",
        "impl_item": "impl",
        "const_item": "const",
        "static_item": "static",
        "macro_definition": "macro"
    }

    return mapping.get(node_type, "unknown")


def map_c_node_type(node_type):
    """
    把 C / C++ AST 节点类型映射成项目内部代码块类型。
    """

    mapping = {
        "function_definition": "function",
        "struct_specifier": "struct",
        "enum_specifier": "enum",
        "type_definition": "typedef"
    }

    return mapping.get(node_type, "unknown")


def map_python_node_type(node_type):
    """
    把 Python AST 节点类型映射成项目内部代码块类型。
    """

    mapping = {
        "function_definition": "function",
        "class_definition": "class"
    }

    return mapping.get(node_type, "unknown")


def map_bash_node_type(node_type):
    """
    把 Bash AST 节点类型映射成项目内部代码块类型。
    """

    mapping = {
        "function_definition": "function"
    }

    return mapping.get(node_type, "unknown")


def remove_duplicate_blocks(blocks):
    """
    去掉完全重复的代码块。
    """

    blocks.sort(key=lambda item: (item["start_line"], item["end_line"]))

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

def has_child_type(node, target_type):
    """
    判断节点内部是否包含某种子节点。
    用于区分 struct file 这种类型引用，
    和 struct file { ... } 这种完整定义
    """

    for child in walk_tree(node):
        if child.type == target_type:
            return True

    return False

def is_inside_function(node):
    """
    判断当前节点是否位于某个函数定义内部。

    C/C++ 中，函数内部可能出现 struct_specifier、enum_specifier、
    type_definition 等节点，这些通常不应该作为独立代码块保存
    """

    current = node.parent

    while current is not None:
        if current.type == "function_definition":
            return True

        current = current.parent

    return False

def parse_code_blocks_with_tree_sitter(file_path, content):
    """
    使用 tree-sitter 提取代码块。

    支持：
    - rust
    - c
    - cpp
    - python
    - bash

    如果 tree-sitter 不可用、语言不支持或解析失败，返回空列表，
    由 code_splitter.py 回退到原来的正则解析。
    """

    if not TREE_SITTER_AVAILABLE:
        return []

    language = detect_ast_language(file_path)

    if language is None:
        return []

    parser = get_parser_for_language(language)

    if parser is None:
        return []

    source_bytes = content.encode("utf-8", errors="ignore")

    try:
        tree = parser.parse(source_bytes)
    except Exception:
        return []

    root = tree.root_node

    rust_target_nodes = {
        "function_item",
        "struct_item",
        "enum_item",
        "trait_item",
        "impl_item",
        "const_item",
        "static_item",
        "macro_definition"
    }

    c_target_nodes = {
        "function_definition",
        "struct_specifier",
        "enum_specifier",
        "type_definition"
    }

    python_target_nodes = {
        "function_definition",
        "class_definition"
    }

    bash_target_nodes = {
        "function_definition"
    }

    blocks = []

    for node in walk_tree(root):
        if language == "rust":
            if node.type not in rust_target_nodes:
                continue

            block_type = map_rust_node_type(node.type)
            name = get_rust_node_name(source_bytes, node)

        elif language in {"c", "cpp"}:
            if node.type not in c_target_nodes:
                continue

            block_type = map_c_node_type(node.type)

            if node.type != "function_definition" and is_inside_function(node):
                continue

            if not is_meaningful_c_block(source_bytes, node, block_type):
                continue

            name = get_c_node_name(source_bytes, node)

        elif language == "python":
            if node.type not in python_target_nodes:
                continue

            block_type = map_python_node_type(node.type)
            name = get_python_node_name(source_bytes, node)

        elif language == "bash":
            if node.type not in bash_target_nodes:
                continue

            block_type = map_bash_node_type(node.type)
            name = get_bash_node_name(source_bytes, node)

        else:
            continue

        block_content = get_node_text(source_bytes, node).strip()

        if block_content == "":
            continue

        # 过滤掉过短的类型引用，比如 struct file、enum state
        if language in {"c", "cpp"}:
            if len(block_content.splitlines()) <= 1 and block_type in {"struct", "enum", "typedef"}:
                continue

        blocks.append(
            {
                "type": block_type,
                "name": name,
                "language": language,
                "parser": "tree_sitter",
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "content": block_content
            }
        )

    return remove_duplicate_blocks(blocks)


def is_meaningful_c_block(source_bytes, node, block_type):
    """
    判断 C/C++ AST 节点是否值得保存为代码块。
    """

    content = get_node_text(source_bytes, node).strip()

    if content == "":
        return False

    if block_type == "function":
        return True

    if block_type == "struct":
        if not has_child_type(node, "field_declaration_list"):
            return False

        if len(content.splitlines()) <= 1:
            return False

        return True

    if block_type == "enum":
        if not has_child_type(node, "enumerator_list"):
            return False

        if len(content.splitlines()) <= 1:
            return False

        return True

    if block_type == "typedef":
        if "{" not in content:
            return False

        if len(content.splitlines()) <= 1:
            return False

        return True

    return False