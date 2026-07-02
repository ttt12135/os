# -*- coding: utf-8 -*-

"""
Excel 批量导入 target 仓库脚本。

适配 Excel 格式：
A列：队伍编号
B列：Fork地址

默认读取：
D:\\os\\project3136859-376262\\new.xlsx

核心逻辑：
1. repo_name 使用“队伍编号”
2. scope 固定为 target
3. target 批量入库时，不重复重建 history Chroma 向量库
4. target 批量入库时，继续读取已有 vector_store/chroma_history 做历史检索
5. 单个仓库失败不会中断整体批次
6. 支持断点续跑

运行方式：
    cd D:\\os\\project3136859-376262
    python scripts\\excel_batch_import_target.py

手动指定 Excel：
    python scripts\\excel_batch_import_target.py --excel "D:\\os\\project3136859-376262\\new.xlsx"

关闭断点续跑：
    python scripts\\excel_batch_import_target.py --no-resume
"""

import argparse
import inspect
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd


# ============================================================
# 1. 项目路径与环境变量
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 关键设置：
# target 批量入库时，只跳过 history Chroma 的“重建”。
# 不跳过 hybrid_retrieve，因为我们仍然需要读取已有 Chroma 做历史检索。
os.environ["KERNELINSIGHT_SKIP_HISTORY_CHROMA_REBUILD"] = "1"


from main import ask_ai_once
from src.repo_url_workflow import import_repo_from_url


# ============================================================
# 2. 基础目录
# ============================================================

PROGRESS_DIR = PROJECT_ROOT / "batch_progress"
PROGRESS_DIR.mkdir(exist_ok=True)


# ============================================================
# 3. 通用工具函数
# ============================================================

def normalize_text(value, default=""):
    """
    把 Excel 单元格内容转成字符串。
    """

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
    """

    columns = list(df.columns)

    # 精确匹配
    for name in candidates:
        if name in columns:
            return name

    # 忽略大小写和空格匹配
    normalized_columns = {
        str(col).strip().lower().replace(" ", ""): col
        for col in columns
    }

    for name in candidates:
        key = str(name).strip().lower().replace(" ", "")

        if key in normalized_columns:
            return normalized_columns[key]

    return None


def safe_repo_name(text, fallback):
    """
    生成安全的 repo_name。

    例如：
    T2026100019911468
    """

    text = normalize_text(text, fallback)

    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("._-")

    if not text:
        return fallback

    return text[:120]


def parse_year_from_team_code(team_code, default="2026"):
    """
    从队伍编号中解析年份。

    例如：
    T2026100019911468 -> 2026
    """

    match = re.search(r"T(\d{4})", team_code)

    if match:
        return match.group(1)

    return default


def load_progress(progress_path):
    """
    读取断点续跑进度。
    """

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
    """
    保存断点续跑进度。
    """

    progress_path.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def safe_import_repo_from_url(**kwargs):
    """
    兼容不同版本的 import_repo_from_url。

    如果当前 import_repo_from_url 不支持某些参数，会自动忽略，
    避免因为 TypeError 中断批量任务。
    """

    signature = inspect.signature(import_repo_from_url)
    allowed_keys = set(signature.parameters.keys())

    filtered_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in allowed_keys
    }

    dropped_keys = [
        key
        for key in kwargs.keys()
        if key not in allowed_keys
    ]

    if dropped_keys:
        print(f"[INFO] 当前 import_repo_from_url 不支持这些参数，已自动忽略：{dropped_keys}")

    return import_repo_from_url(**filtered_kwargs)


def resolve_excel_path(excel_arg):
    """
    解析 Excel 路径。

    默认使用项目根目录下的 new.xlsx。
    """

    if excel_arg:
        path = Path(excel_arg)

        if not path.is_absolute():
            path = PROJECT_ROOT / path

        return path

    return PROJECT_ROOT / "new.xlsx"


def check_history_chroma_exists():
    """
    检查是否已经存在 history Chroma 向量库。

    target 批量入库时不会重建 Chroma，
    但需要读取已有 vector_store/chroma_history 做历史检索。
    """

    chroma_dir = PROJECT_ROOT / "vector_store" / "chroma_history"

    if not chroma_dir.exists():
        return False, chroma_dir

    try:
        has_files = any(chroma_dir.rglob("*"))
    except Exception:
        has_files = False

    return has_files, chroma_dir


# ============================================================
# 4. Excel 读取逻辑
# ============================================================

def load_target_rows(excel_path):
    """
    读取 target Excel。

    支持列名：
    - 队伍编号
    - Fork地址
    """

    df = pd.read_excel(excel_path)

    print()
    print("Excel 列名如下：")

    for col in df.columns:
        print(f"- {col}")

    team_code_col = find_column(
        df,
        [
            "队伍编号",
            "团队编号",
            "编号",
            "team_code",
            "repo_name"
        ]
    )

    repo_url_col = find_column(
        df,
        [
            "Fork地址",
            "fork地址",
            "Fork 地址",
            "仓库地址",
            "repo_url",
            "Git地址",
            "项目地址",
            "代码地址",
            "url"
        ]
    )

    if not team_code_col:
        raise ValueError("Excel 中没有找到“队伍编号”列。")

    if not repo_url_col:
        raise ValueError("Excel 中没有找到“Fork地址”列。")

    rows = []

    for index, row in df.iterrows():
        team_code = normalize_text(row.get(team_code_col))
        repo_url = normalize_text(row.get(repo_url_col))

        if not team_code or not repo_url:
            continue

        repo_name = safe_repo_name(
            team_code,
            fallback=f"target_repo_{index + 1}"
        )

        year = parse_year_from_team_code(team_code, default="2026")

        rows.append(
            {
                "excel_row": int(index + 2),
                "repo_name": repo_name,
                "team_code": team_code,
                "team_name": team_code,
                "school": "unknown_school",
                "year": year,
                "repo_url": repo_url
            }
        )

    return rows


# ============================================================
# 5. 核心批量入库逻辑
# ============================================================

def run_target_excel_batch_import(
    excel_path,
    resume=True,
    require_history_chroma=True
):
    """
    批量导入 target 仓库。
    """

    excel_path = Path(excel_path)

    if not excel_path.exists():
        print()
        print("错误：Excel 文件不存在。")
        print(f"当前识别到的路径：{excel_path}")
        print()
        print("请确认文件是否存在：")
        print(r"D:\os\project3136859-376262\new.xlsx")
        print()
        return

    if require_history_chroma:
        ok, chroma_dir = check_history_chroma_exists()

        if not ok:
            print()
            print("=" * 80)
            print("错误：没有找到可用的 history Chroma 向量库。")
            print("=" * 80)
            print(f"需要的目录：{chroma_dir}")
            print()
            print("你现在要保留历史检索，所以必须先单独构建一次历史向量库。")
            print()
            print("请先运行：")
            print()
            print(r"cd D:\os\project3136859-376262")
            print("python main.py")
            print()
            print("然后输入命令：")
            print()
            print("build_vector_store")
            print()
            print("构建成功后，再重新运行：")
            print()
            print("python scripts\\excel_batch_import_target.py")
            print("=" * 80)
            print()
            return

        print()
        print(f"[OK] 已检测到 history Chroma 向量库：{chroma_dir}")
        print("[OK] target 批量入库时将跳过重建，但继续读取它做历史检索。")

    rows = load_target_rows(excel_path)

    progress_path = PROGRESS_DIR / "target_excel_import_progress.json"
    progress = load_progress(progress_path)

    print()
    print("=" * 80)
    print("KernelInsight Excel target 仓库批量入库")
    print("=" * 80)
    print(f"项目根目录：{PROJECT_ROOT}")
    print(f"Excel 文件：{excel_path}")
    print(f"有效 target 仓库数量：{len(rows)}")
    print(f"断点续跑：{'开启' if resume else '关闭'}")
    print(f"进度文件：{progress_path}")
    print("Chroma 策略：跳过重建，保留历史检索")
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
        print(f"[START] {i}/{len(rows)} 正在导入 target 仓库")
        print(f"Excel 行号：{item['excel_row']}")
        print(f"队伍编号：{item['team_code']}")
        print(f"repo_name：{repo_name}")
        print(f"年份：{item['year']}")
        print(f"地址：{repo_url}")
        print("=" * 80)

        try:
            result = safe_import_repo_from_url(
                repo_url=repo_url,
                scope="target",
                repo_name=repo_name,
                team_name=item["team_name"],
                school=item["school"],
                year=item["year"],
                track="kernel",

                # target 批量入库建议 replace，避免旧 clone 残留
                clone_strategy="replace",

                # target 正式分析
                analysis_mode="full",
                max_blocks="auto",
                max_workers=8,

                # target 需要详细描述报告，用于前端展示
                generate_description_report=True,

                # target 完整流程：
                # 读取已有 history Chroma，做历史检索、对比、评分、final_report
                run_full_target_pipeline=True,

                # 关键：
                # 不要在每个 target 仓库中重复重建 history Chroma
                rebuild_history_kb=False,

                ask_ai_once=ask_ai_once
            )

            progress.setdefault("done", {})[repo_name] = {
                "repo_url": repo_url,
                "team_code": item["team_code"],
                "team_name": item["team_name"],
                "school": item["school"],
                "year": item["year"],
                "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "result": str(result)
            }

            if repo_name in progress.get("failed", {}):
                progress["failed"].pop(repo_name, None)

            save_progress(progress_path, progress)

            success_count += 1
            print(f"[DONE] target 入库完成：{repo_name}")

        except KeyboardInterrupt:
            print()
            print("检测到用户手动中断，已保存当前进度。")
            save_progress(progress_path, progress)
            return

        except Exception as e:
            failed_count += 1

            print(f"[FAILED] target 入库失败：{repo_name}")
            print(f"错误信息：{e}")

            progress.setdefault("failed", {})[repo_name] = {
                "repo_url": repo_url,
                "team_code": item["team_code"],
                "team_name": item["team_name"],
                "school": item["school"],
                "year": item["year"],
                "error": str(e),
                "failed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            save_progress(progress_path, progress)

            # 单个 target 失败，不中断整体批次
            continue

        # 防止连续仓库对 API / Git / 文件系统造成瞬时压力
        time.sleep(1.0)

    failed_path = PROGRESS_DIR / "target_excel_import_failed.json"

    failed_path.write_text(
        json.dumps(progress.get("failed", {}), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print("=" * 80)
    print("target 批量入库结束")
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
    print("1. 如果有失败仓库，查看 batch_progress/target_excel_import_failed.json")
    print("2. 修复失败原因后，重新运行本脚本，会自动跳过已完成 target")
    print("3. target 全部入库完成后，运行 main.py 生成 target 仓库质量排名")
    print("4. 最后运行导出网站数据，用于前端展示")


# ============================================================
# 6. 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="从 Excel 批量导入 target 仓库"
    )

    parser.add_argument(
        "--excel",
        type=str,
        default=None,
        help="Excel 文件路径。默认使用项目根目录下的 new.xlsx。"
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="关闭断点续跑，重新尝试所有 target 仓库。"
    )

    parser.add_argument(
        "--allow-no-history-chroma",
        action="store_true",
        help="允许没有 history Chroma 时继续跑。一般不建议，因为会影响历史检索。"
    )

    args = parser.parse_args()

    excel_path = resolve_excel_path(args.excel)

    run_target_excel_batch_import(
        excel_path=excel_path,
        resume=not args.no_resume,
        require_history_chroma=not args.allow_no_history_chroma
    )


if __name__ == "__main__":
    main()