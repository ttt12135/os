# -*- coding: utf-8 -*-

"""
Excel 批量导入 history 仓库脚本。

用法一：自动寻找项目根目录下的 Excel
    python scripts/excel_batch_import.py

用法二：手动指定 Excel 路径
    python scripts/excel_batch_import.py --excel "D:\os\project3136859-376262\collected-data(1).xlsx"

说明：
- 该脚本只用于批量导入 history 仓库；
- 不生成 description_report；
- 单个仓库失败不会中断整体流程；
- 支持断点记录，已经成功的仓库会自动跳过。
"""

import argparse
import inspect
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd


# ============================================================
# 1. 解决 scripts 目录下找不到 main.py / src 的问题
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from main import ask_ai_once
from src.repo_url_workflow import import_repo_from_url


# ============================================================
# 2. 基础目录
# ============================================================

PROGRESS_DIR = PROJECT_ROOT / "batch_progress"
LOG_DIR = PROJECT_ROOT / "logs"

PROGRESS_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


# ============================================================
# 3. 工具函数
# ============================================================

def normalize_text(value, default=""):
    """把 Excel 单元格内容转成安全字符串。"""
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    text = str(value).strip()

    if text.lower() in {"nan", "none", "null"}:
        return default

    return text


def find_column(df, candidates):
    """
    自动匹配 Excel 列名。

    你的 Excel 里常见列名：
    年份、赛事、子赛事、学校、队伍名称、仓库地址
    """

    columns = list(df.columns)

    # 精确匹配
    for name in candidates:
        if name in columns:
            return name

    # 忽略大小写和空格匹配
    normalized = {
        str(col).strip().lower().replace(" ", ""): col
        for col in columns
    }

    for name in candidates:
        key = str(name).strip().lower().replace(" ", "")
        if key in normalized:
            return normalized[key]

    return None


def auto_find_excel():
    """
    自动在项目根目录寻找 Excel 文件。

    优先级：
    1. collected-data*.xlsx
    2. 根目录下最新的 .xlsx 文件
    """

    xlsx_files = [
        p for p in PROJECT_ROOT.glob("*.xlsx")
        if not p.name.startswith("~$")
    ]

    if not xlsx_files:
        return None

    collected_files = [
        p for p in xlsx_files
        if "collected" in p.name.lower()
    ]

    if collected_files:
        collected_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return collected_files[0]

    xlsx_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return xlsx_files[0]


def resolve_excel_path(excel_arg):
    """
    解析 Excel 路径。

    如果用户传了 --excel，就用用户传的；
    如果没传，就自动找项目根目录下的 .xlsx。
    """

    if excel_arg:
        path = Path(excel_arg)

        if not path.is_absolute():
            path = PROJECT_ROOT / path

        return path

    auto_path = auto_find_excel()

    if auto_path:
        return auto_path

    return None


def load_progress(progress_path):
    if not progress_path.exists():
        return {
            "done": {},
            "failed": {}
        }

    try:
        return json.loads(progress_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "done": {},
            "failed": {}
        }


def save_progress(progress_path, progress):
    progress_path.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def safe_import_repo_from_url(**kwargs):
    """
    兼容不同版本的 import_repo_from_url。

    有些版本支持 generate_description_report；
    有些版本不支持 max_workers；
    这里自动过滤掉当前函数不支持的参数，避免 TypeError。
    """

    signature = inspect.signature(import_repo_from_url)
    allowed = set(signature.parameters.keys())

    filtered_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in allowed
    }

    dropped = [
        key for key in kwargs.keys()
        if key not in allowed
    ]

    if dropped:
        print(f"[INFO] 当前 import_repo_from_url 不支持这些参数，已自动忽略：{dropped}")

    return import_repo_from_url(**filtered_kwargs)


def load_excel_rows(excel_path):
    """
    读取 Excel，并转成批量入库任务列表。
    """

    df = pd.read_excel(excel_path)

    print()
    print("Excel 列名如下：")
    for col in df.columns:
        print(f"- {col}")

    year_col = find_column(df, ["年份", "year", "比赛年份"])
    event_col = find_column(df, ["赛事", "event"])
    sub_event_col = find_column(df, ["子赛事", "sub_event", "track_name"])
    school_col = find_column(df, ["学校", "school", "高校", "单位"])
    team_col = find_column(df, ["队伍名称", "队伍名", "团队名", "team_name", "team", "repo_name", "项目名"])
    url_col = find_column(df, ["仓库地址", "repo_url", "Git地址", "git", "项目地址", "代码地址", "url"])

    if not url_col:
        raise ValueError(
            "Excel 中没有找到仓库地址列。请确认列名包含：仓库地址 / repo_url / Git地址 / 项目地址"
        )

    if not team_col:
        raise ValueError(
            "Excel 中没有找到队伍名称列。请确认列名包含：队伍名称 / 队伍名 / team_name / repo_name"
        )

    rows = []

    for index, row in df.iterrows():
        repo_url = normalize_text(row.get(url_col))

        if not repo_url:
            continue

        team_name = normalize_text(row.get(team_col), default=f"history_repo_{index + 1}")
        school = normalize_text(row.get(school_col), default="unknown_school") if school_col else "unknown_school"
        year = normalize_text(row.get(year_col), default="2025") if year_col else "2025"
        event = normalize_text(row.get(event_col), default="") if event_col else ""
        sub_event = normalize_text(row.get(sub_event_col), default="") if sub_event_col else ""

        # repo_name 用队伍名称生成，避免中文和特殊符号导致路径混乱
        repo_name = team_name

        # 清理 Windows 路径非法字符
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            repo_name = repo_name.replace(ch, "_")

        repo_name = repo_name.strip()

        if not repo_name:
            repo_name = f"history_repo_{index + 1}"

        rows.append({
            "excel_row": int(index + 2),
            "repo_name": repo_name,
            "team_name": team_name,
            "school": school,
            "year": year,
            "event": event,
            "sub_event": sub_event,
            "repo_url": repo_url
        })

    return rows


# ============================================================
# 4. 核心批量入库逻辑
# ============================================================

def run_excel_batch_import(excel_path, resume=True):
    excel_path = Path(excel_path)

    if not excel_path.exists():
        print()
        print("错误：Excel 文件不存在。")
        print(f"当前识别到的路径：{excel_path}")
        print()
        print("解决方法：")
        print("1. 把 Excel 放到项目根目录；")
        print("2. 或者运行时手动指定路径：")
        print(r'   python scripts\excel_batch_import.py --excel "D:\os\project3136859-376262\collected-data(1).xlsx"')
        print()
        return

    rows = load_excel_rows(excel_path)

    progress_path = PROGRESS_DIR / "history_excel_import_progress.json"
    progress = load_progress(progress_path)

    print()
    print("=" * 80)
    print("KernelInsight Excel 历史仓库批量入库")
    print("=" * 80)
    print(f"项目根目录：{PROJECT_ROOT}")
    print(f"Excel 文件：{excel_path}")
    print(f"有效仓库数量：{len(rows)}")
    print(f"断点续跑：{'开启' if resume else '关闭'}")
    print(f"进度文件：{progress_path}")
    print("=" * 80)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, item in enumerate(rows, start=1):
        repo_name = item["repo_name"]
        repo_url = item["repo_url"]

        if resume and repo_name in progress.get("done", {}):
            skipped_count += 1
            print(f"[SKIP] {i}/{len(rows)} 已完成，跳过：{repo_name}")
            continue

        print()
        print("=" * 80)
        print(f"[START] {i}/{len(rows)} 正在导入 history 仓库")
        print(f"Excel 行号：{item['excel_row']}")
        print(f"仓库名：{repo_name}")
        print(f"队伍名：{item['team_name']}")
        print(f"学校：{item['school']}")
        print(f"年份：{item['year']}")
        print(f"赛事：{item['event']}")
        print(f"子赛事：{item['sub_event']}")
        print(f"地址：{repo_url}")
        print("=" * 80)

        try:
            result = safe_import_repo_from_url(
                repo_url=repo_url,
                scope="history",
                repo_name=repo_name,
                team_name=item["team_name"],
                school=item["school"],
                year=item["year"],
                track="kernel",

                # history 批量入库建议 replace，保证重新 clone 干净
                clone_strategy="replace",

                # history 自动入库：走 full 流程，但 max_blocks 使用 auto 动态预算
                analysis_mode="full",
                max_blocks="auto",
                max_workers=8,

                # history 不生成详细报告，节省时间
                generate_description_report=False,

                # history 不跑 target 完整报告流程
                run_full_target_pipeline=False,

                # 批量期间不重复重建历史库，避免每个仓库都重建一次
                rebuild_history_kb=False,

                ask_ai_once=ask_ai_once
            )

            progress.setdefault("done", {})[repo_name] = {
                "repo_url": repo_url,
                "team_name": item["team_name"],
                "school": item["school"],
                "year": item["year"],
                "event": item["event"],
                "sub_event": item["sub_event"],
                "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "result": str(result)
            }

            if repo_name in progress.get("failed", {}):
                progress["failed"].pop(repo_name, None)

            save_progress(progress_path, progress)

            success_count += 1
            print(f"[DONE] 入库完成：{repo_name}")

        except KeyboardInterrupt:
            print()
            print("检测到用户手动中断，已保存当前进度。")
            save_progress(progress_path, progress)
            return

        except Exception as e:
            failed_count += 1
            print(f"[FAILED] 入库失败：{repo_name}")
            print(f"错误信息：{e}")

            progress.setdefault("failed", {})[repo_name] = {
                "repo_url": repo_url,
                "team_name": item["team_name"],
                "school": item["school"],
                "year": item["year"],
                "event": item["event"],
                "sub_event": item["sub_event"],
                "error": str(e),
                "failed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            save_progress(progress_path, progress)

            # 单个仓库失败，不中断整体批次
            continue

        # 轻微暂停，避免连续仓库对 API 和 git 造成瞬时压力
        time.sleep(1.0)

    failed_path = PROGRESS_DIR / "history_excel_import_failed.json"
    failed_path.write_text(
        json.dumps(progress.get("failed", {}), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print("=" * 80)
    print("批量入库结束")
    print("=" * 80)
    print(f"本次新成功：{success_count}")
    print(f"本次跳过：{skipped_count}")
    print(f"本次失败：{failed_count}")
    print(f"累计成功：{len(progress.get('done', {}))}")
    print(f"累计失败：{len(progress.get('failed', {}))}")
    print(f"进度文件：{progress_path}")
    print(f"失败记录：{failed_path}")
    print("=" * 80)

    print()
    print("下一步建议：")
    print("1. 如果有失败仓库，查看 batch_progress/history_excel_import_failed.json")
    print("2. 修复失败原因后，重新运行本脚本，会自动跳过已完成仓库")
    print("3. 全部 history 入库完成后，再运行 main.py 里的仓库质量排名")
    print("4. 最后再运行导出网站数据")


# ============================================================
# 5. 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="从 Excel 批量导入 history 仓库"
    )

    parser.add_argument(
        "--excel",
        type=str,
        default=None,
        help="Excel 文件路径。如果不填，自动寻找项目根目录下的 .xlsx 文件。"
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="关闭断点续跑，重新尝试所有仓库。"
    )

    args = parser.parse_args()

    excel_path = resolve_excel_path(args.excel)

    if not excel_path:
        print()
        print("没有找到 Excel 文件。")
        print()
        print("请使用下面任意一种方法：")
        print("1. 把 Excel 文件放到项目根目录，然后运行：")
        print(r"   python scripts\excel_batch_import.py")
        print()
        print("2. 或者手动指定 Excel 路径：")
        print(r'   python scripts\excel_batch_import.py --excel "D:\os\project3136859-376262\collected-data(1).xlsx"')
        print()
        return

    run_excel_batch_import(
        excel_path=excel_path,
        resume=not args.no_resume
    )


if __name__ == "__main__":
    main()