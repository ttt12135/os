import os

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
        ".bat"
    }

    _, ext = os.path.splitext(file_path)

    return ext.lower() in text_extensions

def is_important_file(file_path):
    """
    判断是否为关键文件
    返回bool类型
    """
    file_name = os.path.basename(file_path).lower()

    important_names = {
        "readme.md",
        "requirements.txt",
        "main.py",
        "app.py",
        "run.py",
        "makefile",
        "cmakelists.txt",
        "package.json",
        "pyproject.toml"
    }

    if file_name in important_names:
        return True
    if file_path.endswith(".py"):
        return True

    return False

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

def collect_important_files(repo_path,max_files=8):
    """
    从仓库里搜集关键文件的内容
    """

    ignore_dirs = {
        ".git",
        "__pycache__",
        ".idea",
        ".vscode",
        "node_modules",
        ".venv",
        "venv"
    }

    important_files = []

    for current_path,dirs,files in os.walk(repo_path):
        #忽略无关文件
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = os.path.join(current_path,file_name)

            if not is_text_file(file_path):
                continue

            if not is_important_file(file_path):
                continue

            important_files.append(file_path)

    def file_priority(file_path):
        """
        给文件的先后顺序进行排序
        """
        file_name = os.path.basename(file_path).lower()

        if file_name == "readme.md":
            return 1
        if file_name =="main.py":
            return 2
        if file_name =="requirements.txt":
            return 3
        if file_name.endswith(".py"):
            return 4

        return 5

    important_files.sort(key = file_priority)

    important_files = important_files[:max_files]

    result = []

    for file_path in important_files:
        relative_path = os.path.relpath(file_path,repo_path)
        content = read_file_content(file_path)

        result.append(
            {
                "path":relative_path,
                "content":content
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
        result.append("文件内容：")
        result.append(file_info["content"])
        result.append("-" * 60)

    return "\n".join(result)
