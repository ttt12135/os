import os
import json
import inspect
from datetime import datetime

from src.ingest_pipeline import ingest_history_repo
from src.history_kb_builder import (
    build_history_knowledge_base_full,
    save_history_knowledge_base_full
)


IGNORE_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    "target",
    "build",
    "dist",
    "out",
    "reports",
    "evaluation",
    "code_blocks",
    "function_analysis",
    "call_graph",
    "module_summary",
    "repo_profiles",
    "history_knowledge_base"
}


CODE_EXTENSIONS = {
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".hpp",
    ".rs",
    ".py",
    ".s",
    ".asm",
    ".S",
    ".sh",
    ".mk"
}


IMPORTANT_FILE_NAMES = {
    "makefile",
    "cmakelists.txt",
    "cargo.toml",
    "readme.md",
    "README.md"
}


def ensure_dir(directory):
    """
    如果目录不存在，就创建。
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def get_repo_name_from_path(repo_path):
    """
    从仓库路径中提取仓库名。
    """

    repo_path = repo_path.rstrip("/\\")
    return os.path.basename(os.path.abspath(repo_path))


def expected_history_profile_path(repo_name):
    """
    推测某个历史仓库对应的 repo_profile_full 输出路径。
    """

    return os.path.join(
        "repo_profiles",
        "history",
        f"{repo_name}_repo_profile_full.json"
    )


def is_probably_repo_dir(directory):
    """
    判断一个目录是否像代码仓库。

    规则：
    1. 不能是输出目录、缓存目录、隐藏目录
    2. 目录中至少存在代码文件或重要工程文件
    """

    name = os.path.basename(directory)

    if name in IGNORE_DIR_NAMES:
        return False

    if name.startswith("."):
        return False

    if not os.path.isdir(directory):
        return False

    checked_file_count = 0

    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIR_NAMES and not d.startswith(".")
        ]

        for file_name in files:
            checked_file_count += 1

            lower_name = file_name.lower()
            extension = os.path.splitext(file_name)[1]

            if file_name in IMPORTANT_FILE_NAMES:
                return True

            if lower_name in IMPORTANT_FILE_NAMES:
                return True

            if extension in CODE_EXTENSIONS:
                return True

            if checked_file_count >= 200:
                return False

    return False


def find_history_repos(history_root_dir):
    """
    在历史项目总目录下寻找多个历史仓库。

    默认只扫描第一层子目录。
    例如：
    history_repos/
        qinghuadaxue/
        nankai/
        tongjidaxue/
    """

    if not os.path.exists(history_root_dir):
        raise FileNotFoundError(f"历史项目总目录不存在：{history_root_dir}")

    if not os.path.isdir(history_root_dir):
        raise NotADirectoryError(f"输入路径不是文件夹：{history_root_dir}")

    repos = []

    for item in os.listdir(history_root_dir):
        item_path = os.path.join(history_root_dir, item)

        if is_probably_repo_dir(item_path):
            repos.append(item_path)

    repos.sort()

    return repos


def call_ingest_history_repo_safe(
    repo_path,
    ask_ai_once,
    analysis_mode,
    max_blocks
):
    """
    调用 ingest_history_repo。

    为了兼容不同版本的 ingest_history_repo，
    这里会自动检查它是否支持 analysis_mode 参数。
    """

    signature = inspect.signature(ingest_history_repo)
    parameters = signature.parameters

    kwargs = {
        "repo_path": repo_path,
        "ask_ai_once": ask_ai_once,
        "max_blocks": max_blocks
    }

    if "analysis_mode" in parameters:
        kwargs["analysis_mode"] = analysis_mode

    return ingest_history_repo(**kwargs)


def save_history_batch_report(batch_result):
    """
    保存历史项目批量入库报告。
    """

    output_dir = "history_knowledge_base"
    ensure_dir(output_dir)

    report_path = os.path.join(
        output_dir,
        "history_batch_report.md"
    )

    lines = []

    lines.append("# 历史项目批量入库报告")
    lines.append("")
    lines.append(f"生成时间：{batch_result.get('created_at')}")
    lines.append("")
    lines.append("## 1. 基本信息")
    lines.append("")
    lines.append(f"- 历史项目总目录：`{batch_result.get('history_root_dir')}`")
    lines.append(f"- 分析模式：`{batch_result.get('analysis_mode')}`")
    lines.append(f"- max_blocks：`{batch_result.get('max_blocks')}`")
    lines.append(f"- 是否启用缓存：`{batch_result.get('use_cache')}`")
    lines.append(f"- 是否强制重跑：`{batch_result.get('force_rebuild')}`")
    lines.append(f"- 发现仓库数量：`{batch_result.get('repo_count')}`")
    lines.append(f"- 成功数量：`{batch_result.get('success_count')}`")
    lines.append(f"- 跳过数量：`{batch_result.get('skipped_count')}`")
    lines.append(f"- 失败数量：`{batch_result.get('failed_count')}`")
    lines.append("")
    lines.append("## 2. 入库结果")
    lines.append("")
    lines.append("| 序号 | 仓库名 | 状态 | 仓库路径 | 输出 profile | 说明 |")
    lines.append("|---:|---|---|---|---|---|")

    records = batch_result.get("records", [])

    for index, record in enumerate(records, start=1):
        lines.append(
            f"| {index} | "
            f"{record.get('repo_name')} | "
            f"{record.get('status')} | "
            f"`{record.get('repo_path')}` | "
            f"`{record.get('repo_profile_full_path', '')}` | "
            f"{record.get('message', '')} |"
        )

    lines.append("")
    lines.append("## 3. 历史知识库输出")
    lines.append("")
    lines.append(f"- full 历史知识库：`{batch_result.get('history_kb_full_path')}`")
    lines.append("")
    lines.append("## 4. 说明")
    lines.append("")
    lines.append(
        "本报告由 batch_ingest_history 自动生成，用于记录多个历史 OS 项目的入库情况。"
        "入库成功的项目会在 repo_profiles/history 目录下生成 repo_profile_full，"
        "并被统一汇总进 history_profiles_full.json，供 retrieve_full 阶段进行相似历史项目检索。"
    )
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    return report_path


def run_batch_ingest_history(
    history_root_dir,
    ask_ai_once,
    analysis_mode="quick",
    max_blocks=50,
    use_cache=True,
    force_rebuild=False
):
    """
    批量入库历史项目。

    流程：
    1. 扫描历史项目总目录
    2. 识别多个历史仓库
    3. 逐个执行 ingest_history_repo
    4. 保存 repo_profiles/history/*.json
    5. 重建 history_profiles_full.json
    6. 生成 history_batch_report.md
    """

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    repos = find_history_repos(history_root_dir)

    records = []
    success_count = 0
    skipped_count = 0
    failed_count = 0

    print()
    print("=" * 70)
    print("开始 v4.0 历史项目批量入库")
    print("=" * 70)
    print(f"历史项目总目录：{history_root_dir}")
    print(f"发现历史仓库数量：{len(repos)}")
    print(f"分析模式：{analysis_mode}")
    print(f"max_blocks：{max_blocks if max_blocks is not None else 'all'}")
    print(f"启用缓存：{use_cache}")
    print(f"强制重跑：{force_rebuild}")
    print("=" * 70)

    if not repos:
        print("未发现可入库的历史仓库。")

    for index, repo_path in enumerate(repos, start=1):
        repo_name = get_repo_name_from_path(repo_path)
        expected_profile_path = expected_history_profile_path(repo_name)

        print()
        print("-" * 70)
        print(f"[{index}/{len(repos)}] 处理历史仓库：{repo_name}")
        print(f"路径：{repo_path}")

        record = {
            "repo_name": repo_name,
            "repo_path": repo_path,
            "repo_profile_full_path": expected_profile_path,
            "status": "",
            "message": ""
        }

        if (
            use_cache
            and not force_rebuild
            and os.path.exists(expected_profile_path)
        ):
            print("检测到已有历史 repo_profile_full，跳过重新入库。")
            record["status"] = "skipped"
            record["message"] = "检测到已有 repo_profile_full，已跳过。"
            skipped_count += 1
            records.append(record)
            continue

        try:
            result_files = call_ingest_history_repo_safe(
                repo_path=repo_path,
                ask_ai_once=ask_ai_once,
                analysis_mode=analysis_mode,
                max_blocks=max_blocks
            )

            profile_path = result_files.get(
                "repo_profile_full_path",
                expected_profile_path
            )

            record["repo_profile_full_path"] = profile_path
            record["status"] = "success"
            record["message"] = "入库成功。"
            success_count += 1

            print(f"入库成功：{profile_path}")

        except Exception as error:
            record["status"] = "failed"
            record["message"] = str(error).replace("\n", " ")
            failed_count += 1

            print(f"入库失败：{error}")

        records.append(record)

    print()
    print("=" * 70)
    print("正在重建 full 历史知识库...")
    print("=" * 70)

    history_kb_full = build_history_knowledge_base_full(
        profile_dir="repo_profiles/history"
    )

    history_kb_full_path = save_history_knowledge_base_full(
        history_kb_full
    )

    print(f"full 历史知识库已更新：{history_kb_full_path}")
    print(f"当前历史项目数量：{history_kb_full.get('profile_count')}")

    batch_result = {
        "created_at": created_at,
        "history_root_dir": history_root_dir,
        "analysis_mode": analysis_mode,
        "max_blocks": max_blocks,
        "use_cache": use_cache,
        "force_rebuild": force_rebuild,
        "repo_count": len(repos),
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "records": records,
        "history_kb_full_path": history_kb_full_path
    }

    report_path = save_history_batch_report(batch_result)

    batch_result["history_batch_report_path"] = report_path

    print()
    print("=" * 70)
    print("历史项目批量入库完成")
    print("=" * 70)
    print(f"成功：{success_count}")
    print(f"跳过：{skipped_count}")
    print(f"失败：{failed_count}")
    print(f"批量入库报告：{report_path}")

    return batch_result


def format_batch_ingest_history_preview(batch_result):
    """
    生成终端预览。
    """

    lines = []

    lines.append("历史项目批量入库完成。")
    lines.append("")
    lines.append(f"历史项目总目录：{batch_result.get('history_root_dir')}")
    lines.append(f"发现仓库数量：{batch_result.get('repo_count')}")
    lines.append(f"成功数量：{batch_result.get('success_count')}")
    lines.append(f"跳过数量：{batch_result.get('skipped_count')}")
    lines.append(f"失败数量：{batch_result.get('failed_count')}")
    lines.append("")
    lines.append(f"full 历史知识库：{batch_result.get('history_kb_full_path')}")
    lines.append(f"批量入库报告：{batch_result.get('history_batch_report_path')}")
    lines.append("")

    if batch_result.get("failed_count", 0) > 0:
        lines.append("失败项目：")

        for record in batch_result.get("records", []):
            if record.get("status") == "failed":
                lines.append(
                    f"- {record.get('repo_name')}: {record.get('message')}"
                )

    return "\n".join(lines)