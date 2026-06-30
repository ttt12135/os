import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlparse
from src.repo_description_generator import generate_repo_description_report
from src.ingest_pipeline import ingest_history_repo
from src.history_kb_builder import build_history_knowledge_base_full, save_history_knowledge_base_full
from src.final_pipeline import run_final_analyze_hybrid_pipeline
import stat
import time

DEFAULT_CLONE_ROOT = "external_repos"
DEFAULT_SOURCE_REGISTRY_DIR = "repo_sources"
DEFAULT_MANIFEST_PATH = "site_config/works_manifest.json"


ALLOWED_URL_PREFIXES = (
    "https://",
    "http://",
    "git@",
    "ssh://",
)


def ensure_dir(directory):
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path, default=None):
    if default is None:
        default = {}

    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def save_json_file(data, file_path):
    output_dir = os.path.dirname(file_path)
    if output_dir:
        ensure_dir(output_dir)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def normalize_repo_url(repo_url):
    if repo_url is None:
        return ""

    text = str(repo_url).strip()

    if text.endswith(".git"):
        text = text[:-4]

    text = text.rstrip("/")

    return text.lower()


def validate_repo_url(repo_url):
    """
    只做基本 URL 安全校验。
    这里绝对不能 shell=True，避免把用户输入当成 shell 命令执行。
    """

    if not repo_url or not isinstance(repo_url, str):
        raise ValueError("仓库地址不能为空。")

    repo_url = repo_url.strip()

    if not repo_url.startswith(ALLOWED_URL_PREFIXES):
        raise ValueError(
            "当前只支持 http(s)、ssh 或 git@ 形式的 Git 仓库地址。"
        )

    dangerous_tokens = [";", "&&", "||", "`", "$(", "\n", "\r"]

    for token in dangerous_tokens:
        if token in repo_url:
            raise ValueError(f"仓库地址中包含危险字符：{token}")

    return repo_url


def sanitize_repo_name(name):
    name = str(name).strip()
    name = re.sub(r"\.git$", "", name)
    name = re.sub(r"[^A-Za-z0-9_\-\.]+", "_", name)
    name = name.strip("._-")

    if not name:
        name = "unknown_repo"

    return name


def derive_repo_name_from_url(repo_url):
    """
    从 Git URL 推断本地仓库名。

    支持：
    - https://github.com/org/repo.git
    - https://gitee.com/org/repo
    - git@github.com:org/repo.git
    - ssh://git@github.com/org/repo.git
    """

    repo_url = validate_repo_url(repo_url)

    if repo_url.startswith("git@"):
        tail = repo_url.split(":", 1)[-1]
        base = os.path.basename(tail)
        return sanitize_repo_name(base)

    parsed = urlparse(repo_url)
    path = parsed.path.rstrip("/")
    base = os.path.basename(path)

    return sanitize_repo_name(base)


def safe_rmtree(path, retries=5):
    """
    Windows 安全删除目录。

    """

    if not os.path.exists(path):
        return True

    def _remove_readonly(func, file_path, exc_info):
        try:
            os.chmod(file_path, stat.S_IWRITE)
            func(file_path)
        except Exception:
            pass

    for attempt in range(retries):
        try:
            shutil.rmtree(path, onerror=_remove_readonly)
            return True
        except PermissionError as e:
            print(f"[WARN] 删除目录失败，可能被占用，重试 {attempt + 1}/{retries}：{e}")
            time.sleep(0.8 * (attempt + 1))
        except Exception as e:
            print(f"[WARN] 删除目录失败，重试 {attempt + 1}/{retries}：{e}")
            time.sleep(0.8 * (attempt + 1))

    return False

def make_unique_repo_dir(base_dir, repo_name, strategy="skip"):
    """
    根据策略处理已存在的本地目录。

    strategy:
    skip: 已存在就直接复用
    update: 已存在且是 git 仓库则 git fetch/pull
    replace: 删除后重新 clone

    Windows 下 .git/objects/pack 文件可能被占用或只读，
    所以 replace 不再直接 shutil.rmtree，而是使用 safe_rmtree。
    如果旧目录无法删除，会尝试改名；如果改名也失败，则使用一个新的目录继续 clone。
    """

    ensure_dir(base_dir)

    repo_dir = os.path.join(base_dir, repo_name)

    if not os.path.exists(repo_dir):
        return repo_dir, "new"

    if strategy == "skip":
        return repo_dir, "existing_reused"

    if strategy == "replace":
        print(f"检测到旧仓库目录，准备删除：{repo_dir}")

        deleted = safe_rmtree(repo_dir)

        if deleted:
            return repo_dir, "removed_for_reclone"

        # 删除失败，尝试改名旧目录
        backup_dir = repo_dir + "_old_" + time.strftime("%Y%m%d_%H%M%S")

        print("旧仓库目录暂时无法删除。")
        print(f"旧目录：{repo_dir}")
        print(f"尝试改名为：{backup_dir}")

        try:
            os.rename(repo_dir, backup_dir)
            print("旧目录已改名，继续使用原目录重新 clone。")
            return repo_dir, "renamed_old_for_reclone"
        except Exception as e:
            print(f"旧目录改名也失败：{e}")

            # 删除失败、改名也失败，就换一个新目录，保证流程不中断
            new_repo_dir = repo_dir + "_new_" + time.strftime("%Y%m%d_%H%M%S")
            print(f"将改用新的仓库目录继续 clone：{new_repo_dir}")

            return new_repo_dir, "use_new_dir_due_to_locked_old"

    if strategy == "update":
        return repo_dir, "existing_update"

    raise ValueError(f"未知 clone_strategy：{strategy}")

def run_subprocess(command, cwd=None, timeout=600):
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": command,
        "cwd": cwd
    }


def clone_or_update_repo(
    repo_url,
    local_dir,
    clone_status,
    clone_depth=None,
    timeout=1200
):
    """
    clone 或 update 仓库。
    注意：这里不会运行仓库代码，只会执行 git clone / git pull。
    """

    repo_url = validate_repo_url(repo_url)

    if clone_status == "existing_reused":
        return {
            "action": "reuse_existing",
            "local_dir": local_dir,
            "success": True,
            "message": "本地目录已存在，按 skip 策略直接复用。"
        }

    if clone_status == "existing_update":
        git_dir = os.path.join(local_dir, ".git")

        if not os.path.exists(git_dir):
            return {
                "action": "update_failed",
                "local_dir": local_dir,
                "success": False,
                "message": "本地目录存在，但不是 Git 仓库，无法 update。建议使用 replace 策略。"
            }

        fetch_result = run_subprocess(["git", "fetch", "--all"], cwd=local_dir, timeout=timeout)
        pull_result = run_subprocess(["git", "pull", "--ff-only"], cwd=local_dir, timeout=timeout)

        success = fetch_result["returncode"] == 0 and pull_result["returncode"] == 0

        return {
            "action": "update_existing",
            "local_dir": local_dir,
            "success": success,
            "fetch": fetch_result,
            "pull": pull_result,
            "message": "本地仓库已尝试更新。"
        }

    clone_command = ["git", "clone"]

    if clone_depth is not None:
        clone_command.extend(["--depth", str(clone_depth)])

    clone_command.extend([repo_url, local_dir])

    clone_result = run_subprocess(clone_command, cwd=None, timeout=timeout)

    return {
        "action": "clone",
        "local_dir": local_dir,
        "success": clone_result["returncode"] == 0,
        "clone": clone_result,
        "message": "已执行 git clone。"
    }


def get_git_current_commit(repo_dir):
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        return ""

    result = run_subprocess(["git", "rev-parse", "HEAD"], cwd=repo_dir, timeout=60)

    if result["returncode"] != 0:
        return ""

    return result["stdout"].strip()


def get_git_default_branch(repo_dir):
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        return ""

    result = run_subprocess(["git", "branch", "--show-current"], cwd=repo_dir, timeout=60)

    if result["returncode"] != 0:
        return ""

    return result["stdout"].strip()


def build_source_record(
    repo_name,
    repo_url,
    scope,
    local_dir,
    team_name="",
    school="",
    year="",
    track="kernel"
):
    return {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "normalized_repo_url": normalize_repo_url(repo_url),
        "scope": scope,
        "profile_type": scope,
        "local_dir": local_dir,
        "team_name": team_name or repo_name,
        "school": school or "unknown",
        "year": year or ("history" if scope == "history" else "2026"),
        "track": track or "kernel",
        "git_commit": get_git_current_commit(local_dir),
        "git_branch": get_git_default_branch(local_dir),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def save_source_record(source_record, registry_dir=DEFAULT_SOURCE_REGISTRY_DIR):
    scope = source_record.get("scope", "unknown")
    repo_name = source_record.get("repo_name", "unknown_repo")

    output_dir = os.path.join(registry_dir, scope)
    ensure_dir(output_dir)

    output_path = os.path.join(output_dir, f"{repo_name}_source.json")
    save_json_file(source_record, output_path)

    return output_path


def update_works_manifest(
    source_record,
    manifest_path=DEFAULT_MANIFEST_PATH
):
    """
    把仓库来源写入 works_manifest.json。
    这样网站前端可以通过原始 repo_url 进行匹配。
    """

    manifest = load_json_file(manifest_path, default=[])

    if not isinstance(manifest, list):
        manifest = []

    repo_name = source_record.get("repo_name")
    normalized_url = source_record.get("normalized_repo_url")

    new_item = {
        "repo_name": repo_name,
        "team_name": source_record.get("team_name", repo_name),
        "school": source_record.get("school", "unknown"),
        "repo_url": source_record.get("repo_url", ""),
        "normalized_repo_url": normalized_url,
        "year": source_record.get("year", ""),
        "track": source_record.get("track", "kernel"),
        "scope": source_record.get("scope", "target"),
        "local_dir": source_record.get("local_dir", ""),
        "git_commit": source_record.get("git_commit", ""),
        "git_branch": source_record.get("git_branch", "")
    }

    updated = False

    for index, item in enumerate(manifest):
        if not isinstance(item, dict):
            continue

        same_repo = item.get("repo_name") == repo_name
        same_url = normalize_repo_url(item.get("repo_url", "")) == normalized_url

        if same_repo or same_url:
            merged = dict(item)
            merged.update(new_item)
            manifest[index] = merged
            updated = True
            break

    if not updated:
        manifest.append(new_item)

    save_json_file(manifest, manifest_path)

    return manifest_path


def inject_source_to_profile(profile_path, source_record):
    if not os.path.exists(profile_path):
        return False

    profile = load_json_file(profile_path, default={})

    if not isinstance(profile, dict):
        return False

    profile["repo_url"] = source_record.get("repo_url", "")
    profile["normalized_repo_url"] = source_record.get("normalized_repo_url", "")
    profile["local_dir"] = source_record.get("local_dir", "")
    profile["team_name"] = source_record.get("team_name", profile.get("team_name", ""))
    profile["school"] = source_record.get("school", profile.get("school", "unknown"))
    profile["year"] = source_record.get("year", profile.get("year", ""))
    profile["track"] = source_record.get("track", profile.get("track", "kernel"))
    profile["git_commit"] = source_record.get("git_commit", "")
    profile["git_branch"] = source_record.get("git_branch", "")
    profile["source_record"] = source_record

    save_json_file(profile, profile_path)

    return True


def inject_source_to_generated_profiles(repo_name, scope, source_record):
    profile_dir = os.path.join("repo_profiles", scope)

    candidate_paths = [
        os.path.join(profile_dir, f"{repo_name}_repo_profile.json"),
        os.path.join(profile_dir, f"{repo_name}_repo_profile_full.json")
    ]

    updated_paths = []

    for path in candidate_paths:
        if inject_source_to_profile(path, source_record):
            updated_paths.append(path)

    return updated_paths


def rebuild_history_kb_full():
    history_kb_full = build_history_knowledge_base_full(
        profile_dir="repo_profiles/history"
    )

    history_kb_full_path = save_history_knowledge_base_full(
        history_kb_full
    )

    return history_kb_full_path


def import_repo_from_url(
    repo_url,
    scope,
    ask_ai_once,
    repo_name=None,
    team_name="",
    school="",
    year="",
    track="kernel",
    clone_root=DEFAULT_CLONE_ROOT,
    clone_strategy="skip",
    clone_depth=None,
    analysis_mode="quick",
    max_blocks="auto",
    max_workers=8,
    generate_description_report=None,
    run_full_target_pipeline=True,
    rebuild_history_kb=True,
    top_k=3,
    rag_top_k=10,
    final_top_k=5,
    structured_weight=0.65,
    semantic_weight=0.35,
    embedding_backend="hash",
    embedding_model_name="",
    device="cpu",
    force_rebuild_vector_store=True,
    manifest_path=DEFAULT_MANIFEST_PATH,
    registry_dir=DEFAULT_SOURCE_REGISTRY_DIR
):
    """
    从 Git 仓库 URL 完成 clone + 分析 + 入库。

    scope:
    - history: 作为历史仓库入库
    - target: 作为本届目标仓库分析
    """

    repo_url = validate_repo_url(repo_url)
    scope = (scope or "").strip().lower()

    if scope not in {"history", "target"}:
        raise ValueError("scope 必须是 history 或 target。")

    if repo_name is None or str(repo_name).strip() == "":
        repo_name = derive_repo_name_from_url(repo_url)
    else:
        repo_name = sanitize_repo_name(repo_name)

    base_dir = os.path.join(clone_root, scope)
    local_dir, clone_status = make_unique_repo_dir(
        base_dir=base_dir,
        repo_name=repo_name,
        strategy=clone_strategy
    )

    print()
    print("=" * 70)
    print("开始从仓库地址导入项目")
    print("=" * 70)
    print(f"仓库地址：{repo_url}")
    print(f"仓库类型：{scope}")
    print(f"本地名称：{repo_name}")
    print(f"本地路径：{local_dir}")
    print(f"clone 策略：{clone_strategy}")
    print(f"分析模式：{analysis_mode}")
    print(f"max_blocks：{'auto' if max_blocks == 'auto' else (max_blocks if max_blocks is not None else 'all')}")
    print("=" * 70)

    clone_result = clone_or_update_repo(
        repo_url=repo_url,
        local_dir=local_dir,
        clone_status=clone_status,
        clone_depth=clone_depth
    )

    if not clone_result.get("success"):
        return {
            "success": False,
            "stage": "clone",
            "repo_name": repo_name,
            "repo_url": repo_url,
            "scope": scope,
            "local_dir": local_dir,
            "clone_result": clone_result
        }

    source_record = build_source_record(
        repo_name=repo_name,
        repo_url=repo_url,
        scope=scope,
        local_dir=local_dir,
        team_name=team_name,
        school=school,
        year=year,
        track=track
    )

    source_record_path = save_source_record(
        source_record=source_record,
        registry_dir=registry_dir
    )

    manifest_output_path = update_works_manifest(
        source_record=source_record,
        manifest_path=manifest_path
    )

    generated_files = {}

    description_report_path = ""
    description_report_content = ""

    if generate_description_report is None:
        generate_description_report = scope == "target"

    if generate_description_report:
        try:
            print()
            print("正在生成仓库描述报告 description_report...")
            description_report_path, description_report_content = generate_repo_description_report(
                repo_path=local_dir,
                ask_ai_once=ask_ai_once
            )
            print(f"仓库描述报告：{description_report_path}")
        except Exception as e:
            print(f"仓库描述报告生成失败：{e}")
    else:
        print()
        print("跳过 description_report：history 批量入库默认不生成描述报告，以提高入库速度。")

    if scope == "history":
        generated_files = ingest_history_repo(
            repo_path=local_dir,
            ask_ai_once=ask_ai_once,
            max_blocks=max_blocks,
            analysis_mode=analysis_mode,
            max_workers=max_workers
        )

        
        updated_profiles = inject_source_to_generated_profiles(
            repo_name=repo_name,
            scope="history",
            source_record=source_record
        )

        history_kb_full_path = ""

        if rebuild_history_kb:
            history_kb_full_path = rebuild_history_kb_full()

        generated_files["description_report_path"] = description_report_path

        return {
            "success": True,
            "stage": "history_import_done",
            "repo_name": repo_name,
            "repo_url": repo_url,
            "scope": scope,
            "local_dir": local_dir,
            "clone_result": clone_result,
            "source_record_path": source_record_path,
            "manifest_path": manifest_output_path,
            "description_report_path": description_report_path,
            "generated_files": generated_files,
            "updated_profiles": updated_profiles,
            "description_report_path": description_report_path,
            "history_kb_full_path": history_kb_full_path
        }

    # target
    if run_full_target_pipeline:
        generated_files = run_final_analyze_hybrid_pipeline(
            repo_path=local_dir,
            ask_ai_once=ask_ai_once,
            analysis_mode=analysis_mode,
            max_blocks=max_blocks,
            max_workers=max_workers,
            top_k=top_k,
            rag_top_k=rag_top_k,
            final_top_k=final_top_k,
            structured_weight=structured_weight,
            semantic_weight=semantic_weight,
            embedding_backend=embedding_backend,
            embedding_model_name=embedding_model_name,
            device=device,
            force_rebuild_vector_store=force_rebuild_vector_store
        )
    else:
        from src.ingest_pipeline import analyze_target_repo

        generated_files = analyze_target_repo(
            repo_path=local_dir,
            ask_ai_once=ask_ai_once,
            max_blocks=max_blocks,
            analysis_mode=analysis_mode,
            max_workers=max_workers
        )

    generated_files["description_report_path"] = description_report_path

    updated_profiles = inject_source_to_generated_profiles(
        repo_name=repo_name,
        scope="target",
        source_record=source_record
    )

    return {
        "success": True,
        "stage": "target_import_done",
        "repo_name": repo_name,
        "repo_url": repo_url,
        "scope": scope,
        "local_dir": local_dir,
        "clone_result": clone_result,
        "source_record_path": source_record_path,
        "manifest_path": manifest_output_path,
        "description_report_path": description_report_path,
        "generated_files": generated_files,
        "updated_profiles": updated_profiles
    }


def format_repo_url_import_preview(result):
    lines = []

    lines.append("仓库地址导入流程完成。" if result.get("success") else "仓库地址导入流程失败。")
    lines.append("")
    lines.append(f"阶段：{result.get('stage')}")
    lines.append(f"仓库名：{result.get('repo_name')}")
    lines.append(f"仓库类型：{result.get('scope')}")
    lines.append(f"原始地址：{result.get('repo_url')}")
    lines.append(f"本地路径：{result.get('local_dir')}")

    clone_result = result.get("clone_result", {})
    lines.append(f"clone/update 动作：{clone_result.get('action')}")
    lines.append(f"clone/update 是否成功：{clone_result.get('success')}")

    if not result.get("success"):
        if clone_result.get("clone"):
            lines.append("")
            lines.append("clone stderr：")
            lines.append(str(clone_result.get("clone", {}).get("stderr", ""))[:2000])
        return "\n".join(lines)

    lines.append(f"来源记录：{result.get('source_record_path')}")
    lines.append(f"manifest：{result.get('manifest_path')}")

    if result.get("history_kb_full_path"):
        lines.append(f"历史知识库：{result.get('history_kb_full_path')}")

    updated_profiles = result.get("updated_profiles", [])

    if updated_profiles:
        lines.append("")
        lines.append("已写入来源信息的 profile：")
        for path in updated_profiles:
            lines.append(f"- {path}")

    generated_files = result.get("generated_files", {})

    if generated_files:
        lines.append("")
        lines.append("生成文件：")
        for key, value in generated_files.items():
            if isinstance(value, str):
                lines.append(f"- {key}: {value}")

    return "\n".join(lines)
