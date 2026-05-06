import os


def calculate_file_score(file_path,repo_path):
    """
    根据文件名、目录位置、扩展名等信息，给文件打重要性的评分
    评分越高，说明这个文件越重要
    """
    
    score = 0

    file_name = os.path.basename(file_path).lower()
    relative_path = os.path.relpath(file_path, repo_path).lower()

    _,ext = os.path.splitext(file_name)
    
    #1、常见项目说明和文件的入口
    important_names = {
        "readme.md": 10,
        "main.py": 9,
        "app.py": 8,
        "run.py": 8,
        "requirements.txt": 7,
        "makefile": 8,
        "cmakelists.txt": 8,
        "package.json": 6,
        "pyproject.toml": 6,
        "cargo.toml": 6,
    }

    if file_name in important_names:
        score += important_names[file_name]

    #2、常见os关键文件名
    os_keywords = {
        "boot": 8,
        "entry": 8,
        "start": 7,
        "kernel": 8,
        "init": 7,
        "main": 6,
        "trap": 7,
        "interrupt": 7,
        "irq": 6,
        "syscall": 7,
        "proc": 7,
        "process": 6,
        "sched": 7,
        "task": 6,
        "thread": 5,
        "mm": 7,
        "memory": 7,
        "page": 6,
        "vm": 6,
        "alloc": 5,
        "fs": 5,
        "file": 4,
        "console": 4,
        "driver": 4,
        "uart": 4,
        "timer": 4,
        "lock": 4,
        "spinlock": 5,
    }

    for keyword, value in os_keywords.items():
        if keyword in file_name:
            score += value
    
    #3、根据文件类型打分

    code_extensions = {
         ".c": 6,
        ".h": 5,
        ".s": 6,
        ".asm": 6,
        ".rs": 6,
        ".cpp": 5,
        ".hpp": 5,
        ".py": 5,
        ".java": 4,
        ".js": 3,
        ".ts": 3,
        ".md": 3,
        ".txt": 2,
        ".toml": 3,
        ".json": 2,
        ".yaml": 2,
        ".yml": 2,
        ".ld": 5,
        ".lds": 5,
    }

    if ext in code_extensions:
        score += code_extensions[ext]

    #4、根据目录位置加分
    important_dirs = {
        "kernel": 7,
        "kern": 7,
        "boot": 7,
        "arch": 6,
        "src": 5,
        "os": 5,
        "mm": 5,
        "memory": 5,
        "proc": 5,
        "process": 5,
        "sched": 5,
        "trap": 5,
        "syscall": 5,
        "driver": 4,
        "drivers": 4,
        "fs": 4,
        "include": 4,
    }

    for keyword, value in important_dirs.items():
        if keyword in relative_path:
            score += value

    #5、发现是测试文档、展示文件时减分
    less_important_dirs = {
        "test": -3,
        "tests": -3,
        "example": -2,
        "examples": -2,
        "doc": -2,
        "docs": -2,
        "benchmark": -2,
    }

    for keyword, value in less_important_dirs.items():
        if keyword in relative_path:
            score += value

    return score



def get_file_score_info(file_path,repo_path):
    """
    返回文件路径和分数
    """

    relative_path = os.path.relpath(file_path,repo_path)

    return{
        "path":relative_path,
        "score":calculate_file_score(file_path,repo_path)
    }