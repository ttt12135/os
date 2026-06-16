import os
import json
from datetime import datetime


def ensure_dir(dir_path):
    """
    目录不存在就创一个
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_repo_profile_files(profile_dir):
    """
    在 repo_profiles 目录中查找所有仓库画像文件。
    """

    if not os.path.exists(profile_dir):
        return []

    if not os.path.isdir(profile_dir):
        return []

    profile_files = []

    for file_name in os.listdir(profile_dir):
        if file_name.endswith("_repo_profile.json"):
            file_path = os.path.join(profile_dir, file_name)
            profile_files.append(file_path)

    profile_files.sort()

    return profile_files


def simplify_profile(profile):
    """
    从完整 repo_profile 中提取适合知识库索引的核心内容。

    完整 repo_profile 肯定很大
    history_profiles.json 先保存核心摘要，后续 LangChain 入库时再进一步拆分。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    repo_path = profile.get("repo_path", "")

    function_summary = profile.get("function_analysis_summary", {})
    call_graph_summary = profile.get("call_graph_summary", {})
    module_summary = profile.get("module_summary", {})

    simplified = {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "created_at": profile.get("created_at", ""),

        "function_analysis_summary": function_summary,

        "call_graph_summary": {
            "edge_count": call_graph_summary.get("edge_count", 0),
            "high_confidence_edge_count": call_graph_summary.get("high_confidence_edge_count", 0)
        },

        "module_summary": {
            "module_count": module_summary.get("module_count", 0),
            "module_names": module_summary.get("module_names", []),
            "modules": module_summary.get("modules", [])
        },

        "uncertainty": profile.get("uncertainty", []),

        "source_profile": f"repo_profiles/history/{repo_name}_repo_profile.json"
    }

    return simplified


def build_history_knowledge_base(profile_dir="repo_profiles/history"):
    """
    构建历史作品知识库

    读取 repo_profiles 目录下的所有 repo_profile，
    汇总成 history_profiles.json。
    """

    profile_files = find_repo_profile_files(profile_dir)

    profiles = []

    for profile_file in profile_files:
        profile = load_json_file(profile_file)
        simplified_profile = simplify_profile(profile)
        profiles.append(simplified_profile)

    knowledge_base = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile_count": len(profiles),
        "profiles": profiles
    }

    return knowledge_base


def save_history_knowledge_base(knowledge_base):
    """
    保存历史作品知识库。
    """

    output_dir = "history_knowledge_base"
    ensure_dir(output_dir)

    file_path = os.path.join(output_dir, "history_profiles.json")

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(knowledge_base, file, ensure_ascii=False, indent=2)

    return file_path


def format_history_kb_preview(knowledge_base, save_path):
    """
    生成终端显示摘要。
    """

    output = []

    output.append("历史作品知识库构建完成。")
    output.append("")
    output.append(f"画像数量：{knowledge_base.get('profile_count')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("已入库作品：")

    profiles = knowledge_base.get("profiles", [])

    if len(profiles) == 0:
        output.append("暂无仓库画像，请先生成 repo_profiles/*.json。")
    else:
        for index, profile in enumerate(profiles, start=1):
            output.append(f"{index}. {profile.get('repo_name')}")
            output.append(f"   模块数量：{profile.get('module_summary', {}).get('module_count')}")
            output.append(f"   调用边数量：{profile.get('call_graph_summary', {}).get('edge_count')}")
            output.append("")

    return "\n".join(output)


def extract_history_profile_full(profile, source_profile):
    """
    从 repo_profile_full 中提取适合历史知识库保存的核心字段。
    """

    return {
        "repo_name": profile.get("repo_name"),
        "source_profile": source_profile,
        "profile_type": profile.get("profile_type", "full"),
        "target_or_history": profile.get("target_or_history", "history"),
        "project_type": profile.get("project_type", "unknown_os_project"),
        "main_languages": profile.get("main_languages", []),
        "function_count": profile.get("function_count", 0),
        "node_count": profile.get("node_count", 0),
        "edge_count": profile.get("edge_count", 0),
        "internal_edge_count": profile.get("internal_edge_count", 0),
        "external_edge_count": profile.get("external_edge_count", 0),
        "module_count": profile.get("module_count", 0),
        "core_modules": profile.get("core_modules", []),
        "core_module_details": profile.get("core_module_details", []),
        "module_completeness": profile.get("module_completeness", {}),
        "structure_complexity": profile.get("structure_complexity", 0),
        "technical_features": profile.get("technical_features", []),
        "weaknesses": profile.get("weaknesses", []),
        "data_quality": profile.get("data_quality", {})
    }



def build_history_knowledge_base_full(profile_dir="repo_profiles/history"):
    """
    构建 full 版本历史知识库。

    扫描 repo_profiles/history/ 下所有 *_repo_profile_full.json，
    汇总成 history_profiles_full.json。
    """

    profiles = []

    if not os.path.exists(profile_dir):
        return {
            "kb_type": "full",
            "profile_count": 0,
            "profiles": [],
            "warning": f"历史 profile 目录不存在：{profile_dir}"
        }

    for file_name in os.listdir(profile_dir):
        if not file_name.endswith("_repo_profile_full.json"):
            continue

        file_path = os.path.join(profile_dir, file_name)

        try:
            profile = load_json_file(file_path)
            compact_profile = extract_history_profile_full(
                profile=profile,
                source_profile=file_path
            )

            profiles.append(compact_profile)

        except Exception as error:
            profiles.append(
                {
                    "repo_name": file_name,
                    "source_profile": file_path,
                    "error": str(error)
                }
            )

    profiles.sort(
        key=lambda item: item.get("repo_name", "")
    )

    history_kb = {
        "kb_type": "full",
        "profile_count": len(profiles),
        "profiles": profiles,
        "source_dir": profile_dir,
        "description": "Full version history knowledge base built from repo_profile_full files."
    }

    return history_kb


def save_history_knowledge_base_full(history_kb):
    """
    保存 full 版本历史知识库。
    """

    output_dir = "history_knowledge_base"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, "history_profiles_full.json")

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(history_kb, file, ensure_ascii=False, indent=2)

    return file_path


def format_history_kb_full_preview(history_kb, save_path):
    """
    生成 full 历史知识库的终端预览。
    """

    output = []

    output.append("full 历史知识库构建完成。")
    output.append("")
    output.append(f"知识库类型：{history_kb.get('kb_type')}")
    output.append(f"历史项目数量：{history_kb.get('profile_count')}")
    output.append(f"保存路径：{save_path}")
    output.append("")
    output.append("历史项目预览：")

    profiles = history_kb.get("profiles", [])

    for index, profile in enumerate(profiles[:10], start=1):
        output.append(f"{index}. {profile.get('repo_name')}")
        output.append(f"   项目类型：{profile.get('project_type')}")
        output.append(f"   核心模块：{profile.get('core_modules')}")
        output.append(f"   函数数量：{profile.get('function_count')}")
        output.append(f"   调用边数量：{profile.get('edge_count')}")
        output.append(f"   结构复杂度：{profile.get('structure_complexity')}")
        output.append("")

    return "\n".join(output)