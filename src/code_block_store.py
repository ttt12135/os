import os
import json
from datetime import datetime


def ensure_dir(dir_path):
    """
    如果目录不存在，就自动创建一个
    """

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_repo_name(repo_path):
    """
    从仓库路径中提取名称
    """

    repo_path =os.path.normpath(repo_path)
    return os.path.basename(repo_path)


def add_block_ids(blocks):
    """
    给每个代码块添加 block_id，方便后续检索和引用。
    同时保留 file_score，方便知道这个代码块来自多重要的文件。
    """

    new_blocks = []

    for index, block in enumerate(blocks, start=1):
        new_block = {
            "block_id": f"block_{index}",
            "file_path": block["file_path"],
            "file_score": block.get("file_score", 0),
            "language": block.get("language", "unknown"),
            "parser": block.get("parser", "unknown"),
            "start_line": block.get("start_line"),
            "end_line": block.get("end_line"),
            "type": block["type"],
            "name": block["name"],
            "content": block["content"]
        }

        new_blocks.append(new_block)

    return new_blocks

def save_code_blocks(repo_path, blocks):
    """
    把代码切片结果保存成 JSON 文件。
    """

    output_dir= "code_blocks"
    ensure_dir(output_dir)

    repo_name = get_repo_name(repo_path)
    file_name = f"{repo_name}_blocks.json"
    file_path = os.path.join(output_dir, file_name)

    blocks_with_ids = add_block_ids(blocks)

    data = {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "block_count": len(blocks_with_ids),
        "blocks": blocks_with_ids
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return file_path


def format_block_save_summary(repo_path, blocks, save_path):
    """
    整理代码块保存结果，方便终端显示。
    """

    repo_name = get_repo_name(repo_path)

    output = []

    output.append("代码切片保存完成。")
    output.append("")
    output.append(f"仓库名称：{repo_name}")
    output.append(f"代码块数量：{len(blocks)}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("前几个代码块预览：")

    for index, block in enumerate(blocks[:5], start=1):
        output.append(f"{index}. {block['type']}  {block['name']}")
        output.append(f"   文件：{block['file_path']}")

    return "\n".join(output)