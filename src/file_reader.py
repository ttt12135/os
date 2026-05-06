import os
from src.file_scorer import get_file_score_info

def is_text_file(file_path):
    """
    判断是不是规范的文本文件
    防止读取乱码导致程序出错
    返回bool类型数据
    """

    text_extensions = {
         ".py",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".java",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".sh",
        ".bat",
        ".s",
        ".asm",
        ".rs",
        ".ld",
        ".lds",
        ".mk"
    }

    file_name = os.path.basename(file_path).lower()
    _,ext = os.path.splitext(file_path)

    if file_name == "makefile":
        return True

    return ext.lower() in text_extensions


def read_file_content(file_path,max_chars=3000):
    """
    读取单个文件内容
    且限制在3000字
    """

    try:
        #先用utf-8读
        with open(file_path,"r",encoding="utf-8") as file:
            content = file.read()
        #不行了用GBK读    
    except UnicodeDecodeError:
        try:
            with open(file_path,"r",encoding="gbk") as file:
                content = file.read()
        except UnicodeDecodeError:
            #gbk也读不出来就没招了
            return "该文件编码无法读取"
    except PermissionError:
        return "没有权限读取该文件"
    except FileNotFoundError:
        return "文件不存在"

    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n......文件内容过长，后面省略......"

    return content


def collect_important_files(repo_path,max_files=10):
    """
    利用v0.5新加入的打分标准
    不仅仅靠固定的文件名
    而是综合打分
    提取关键文件
    """

    #去掉无用的文件，AI无需分析
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

    scored_files = []

    for current_path, dirs, files in os.walk(repo_path):
        # 忽略不需要扫描的目录
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = os.path.join(current_path, file_name)

            if not is_text_file(file_path):
                continue

            score_info = get_file_score_info(file_path, repo_path)

            if score_info["score"] <= 0:
                continue

            scored_files.append(
                {
                    "full_path": file_path,
                    "path": score_info["path"],
                    "score": score_info["score"]
                }
            )

    # 按分数从高到低排序
    scored_files.sort(key=lambda item: item["score"], reverse=True)

    # 只取前 max_files 个
    scored_files = scored_files[:max_files]

    result = []

    for file_info in scored_files:
        content = read_file_content(file_info["full_path"])

        result.append(
            {
                "path": file_info["path"],
                "score": file_info["score"],
                "content": content
            }
        )

    return result




def format_files_content(file_content):
    """
    把多文件的内容被整理成可放入Prompt的字符串
    """

    if len(file_content) == 0:
        return "未找到可读文件"

    result = []

    for file_info in file_content:
        result.append(f"文件路径:{file_info['path']}")
        result.append(f"重要性评分：{file_info['score']}")
        result.append("文件内容：")
        result.append(file_info["content"])
        result.append("-" * 60)

    return "\n".join(result)


def format_file_scores(files_content):
    """
    单独整理文件评分结果，方便展示。
    """

    if len(files_content) == 0:
        return "没有可展示的文件评分结果。"

    result = []

    for file_info in files_content:
        result.append(f"{file_info['path']}  |  score = {file_info['score']}")

    return "\n".join(result)