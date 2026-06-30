from src.repo_url_workflow import (
    import_repo_from_url,
    format_repo_url_import_preview,
    derive_repo_name_from_url,
    sanitize_repo_name,
)


def _input_with_default(prompt, default=""):
    text = input(prompt).strip()
    if text == "":
        return default
    return text


def _normalize_scope(text):
    text = str(text or "").strip().lower()
    if text in {"1", "h", "history", "历史", "历史库", "往届"}:
        return "history"
    if text in {"", "2", "t", "target", "目标", "目标库", "本届"}:
        return "target"
    print("未识别仓库用途，已按 target 处理。")
    return "target"


def _normalize_level(text):
    text = str(text or "").strip().lower()
    if text in {"1", "quick", "q", "快速", "测试"}:
        return "quick"
    if text in {"3", "deep", "d", "深度", "最终", "all"}:
        return "deep"
    return "formal"


def _build_preset(scope, level):
    """
    简化导入预设。

    新规则：
    1. 快速测试：固定少量代码块，验证流程。
    2. 正式入库：auto 动态预算。先全仓切片，再按代码块总数自动选择高优先级代码块做 AI 理解。
    3. 深度最终：all 全量 AI 分析全部代码块。

    说明：
    - max_blocks = "auto" 表示动态预算。
    - max_blocks = None 表示全量 AI 分析。
    """

    preset = {
        "clone_strategy": "replace",
        "analysis_mode": "full",
        "track": "kernel",
        "run_full_target_pipeline": scope == "target",
        "rebuild_history_kb": scope == "history",
        "embedding_backend": "hash",
        "max_workers": 8,
        # history 批量入库不生成 description_report，加快速度；target 生成详细 description_report，供 final_report 和前端展示。
        "generate_description_report": scope == "target",
    }

    if level == "quick":
        preset["analysis_mode"] = "quick"
        preset["max_blocks"] = 200
        preset["preset_name"] = "快速测试"
        preset["preset_desc"] = "快速测试：只分析前 200 个高优先级代码块，用于验证 clone 和分析流程是否能跑通。"

    elif level == "deep":
        preset["analysis_mode"] = "full"
        preset["max_blocks"] = None
        preset["preset_name"] = "深度最终"
        preset["preset_desc"] = "深度最终：全量 AI 分析全部代码块，耗时和 API 消耗最高，适合最终展示前使用。"

    else:
        preset["analysis_mode"] = "full"
        preset["max_blocks"] = "auto"
        preset["preset_name"] = "正式入库（动态预算）"
        preset["preset_desc"] = "正式入库：先全仓切片，再按仓库规模动态选择高优先级代码块做 AI 理解，例如 3000 块约分析 1200 块，5000 块约分析 3000 块。"

    return preset

def _default_year(scope):
    if scope == "history":
        return "history"
    return "2025"


def _print_import_summary(repo_url, scope, repo_name, team_name, school, year, preset):
    print()
    print("=" * 64)
    print("导入配置确认")
    print("=" * 64)
    print(f"仓库地址：{repo_url}")
    print(f"仓库用途：{'历史库 history' if scope == 'history' else '目标评测 target'}")
    print(f"固定入库目录：external_repos/{scope}/{repo_name}")
    print(f"仓库简称：{repo_name}")
    print(f"队伍/项目名：{team_name or repo_name}")
    print(f"学校：{school or 'unknown'}")
    print(f"年份：{year}")
    print(f"赛道：kernel")
    print(f"分析强度：{preset['preset_name']}")
    print(f"说明：{preset['preset_desc']}")
    print(f"clone 策略：replace（固定：删除旧目录后重新 clone，保证干净）")
    print(f"分析模式：{preset['analysis_mode']}")
    print(f"max_blocks：{('auto' if preset['max_blocks'] == 'auto' else (preset['max_blocks'] if preset['max_blocks'] is not None else 'all'))}")
    print(f"AI 并发线程：{preset.get('max_workers', 8)}")
    if scope == "target":
        print("target 完整流程：开启（会生成详细 description_report、历史对比、评分和 final_report）")
    else:
        print("history 入库：开启（跳过 description_report，加快批量入库）")
    print(f"生成 description_report：{'是' if preset.get('generate_description_report') else '否'}")
    print("=" * 64)


def run_simple_import_flow(ask_ai_once):
    """
    简化版 URL 导入流程。

    只问用户真正需要知道的 5 件事：
    1. Git 地址
    2. 用途：history / target
    3. 仓库简称
    4. 学校、队伍、年份
    5. 分析强度

    其他技术选项全部走固定预设。
    """

    print()
    print("=" * 64)
    print("导入 Git 仓库并自动分析")
    print("=" * 64)
    print("说明：只需要填写仓库地址和基本信息，技术参数已自动设置。")
    print()

    repo_url = input("1. 请输入 Git 仓库地址：").strip()

    scope_text = input("2. 这个仓库用于？[1=历史库 history，2=目标评测 target，默认 2]：")
    scope = _normalize_scope(scope_text)

    try:
        default_repo_name = derive_repo_name_from_url(repo_url)
    except Exception:
        default_repo_name = "unknown_repo"

    repo_name_text = input(f"3. 仓库简称/英文名 [默认 {default_repo_name}]：").strip()
    repo_name = sanitize_repo_name(repo_name_text or default_repo_name)

    team_name = input("4. 队伍名/项目名 [可回车]：").strip()
    school = input("5. 学校名 [可回车 unknown]：").strip()
    year = _input_with_default(f"6. 年份 [默认 {_default_year(scope)}]：", _default_year(scope))

    level_text = input("7. 分析强度 [1=快速测试，2=正式入库，3=深度最终，默认 2]：")
    level = _normalize_level(level_text)
    preset = _build_preset(scope=scope, level=level)

    _print_import_summary(
        repo_url=repo_url,
        scope=scope,
        repo_name=repo_name,
        team_name=team_name,
        school=school,
        year=year,
        preset=preset,
    )

    confirm = input("确认开始？[直接回车=开始，n=取消]：").strip().lower()
    if confirm in {"n", "no", "q", "quit", "取消"}:
        print("已取消导入。")
        return {"success": False, "stage": "cancelled", "repo_name": repo_name, "scope": scope}

    result = import_repo_from_url(
        repo_url=repo_url,
        scope=scope,
        ask_ai_once=ask_ai_once,
        repo_name=repo_name,
        team_name=team_name,
        school=school,
        year=year,
        track="kernel",
        clone_strategy=preset["clone_strategy"],
        analysis_mode=preset["analysis_mode"],
        max_blocks=preset["max_blocks"],
        run_full_target_pipeline=preset["run_full_target_pipeline"],
        rebuild_history_kb=preset["rebuild_history_kb"],
        embedding_backend=preset["embedding_backend"],
        max_workers=preset.get("max_workers", 8),
        generate_description_report=preset.get("generate_description_report", scope == "target"),
    )

    print()
    print(format_repo_url_import_preview(result))

    if result.get("success"):
        print()
        print("下一步建议：")
        if scope == "target":
            print(f"1. 查看最终报告：reports/{repo_name}_final_report.md")
            print("2. 确认报告没问题后，运行 2 导出网站数据。")
        else:
            print("1. 继续导入其他历史仓库。")
            print("2. 全部历史仓库导入后，运行 3 生成仓库排名。")
            print("3. 排名确认后，运行 2 导出网站数据。")

    return result
