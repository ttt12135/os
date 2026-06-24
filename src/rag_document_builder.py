import os
import json
from datetime import datetime


def ensure_dir(directory):
    """
    如果目录不存在，则创建目录。
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path):
    """
    读取 JSON 文件。
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    if os.path.isdir(file_path):
        raise IsADirectoryError(f"输入的是文件夹，不是 JSON 文件：{file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_file(data, file_path):
    """
    保存 JSON 文件。
    """

    output_dir = os.path.dirname(file_path)

    if output_dir:
        ensure_dir(output_dir)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def safe_list(value):
    """
    安全转列表。
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        if value.strip() == "":
            return []
        return [value]

    return []


def safe_join(items, default="无"):
    """
    安全拼接列表。
    """

    items = safe_list(items)

    if not items:
        return default

    return "、".join(str(item) for item in items)


def safe_text(value, default="无"):
    """
    安全转文本。
    """

    if value is None:
        return default

    text = str(value).strip()

    if text == "":
        return default

    return text


def extract_profiles(history_kb):
    """
    从 history_profiles_full.json 中提取历史项目 profile。
    兼容不同版本字段名。
    """

    if isinstance(history_kb.get("profiles"), list):
        return history_kb.get("profiles")

    if isinstance(history_kb.get("history_profiles"), list):
        return history_kb.get("history_profiles")

    if isinstance(history_kb.get("items"), list):
        return history_kb.get("items")

    return []


def try_load_source_profile(profile):
    """
    尝试读取 profile 中记录的 source_profile 文件。

    如果 source_profile 不存在，就直接返回当前 profile。
    """

    source_profile_path = profile.get("source_profile")

    if source_profile_path and os.path.exists(source_profile_path):
        try:
            return load_json_file(source_profile_path)
        except Exception:
            return profile

    return profile


def build_document(doc_id, repo_name, doc_type, content, metadata):
    """
    构造标准 RAG 文档。
    """

    return {
        "doc_id": doc_id,
        "repo_name": repo_name,
        "doc_type": doc_type,
        "content": content,
        "metadata": metadata
    }


def build_base_metadata(profile):
    """
    构造通用 metadata。
    """

    return {
        "repo_name": profile.get("repo_name", "unknown_repo"),
        "project_type": profile.get("project_type", "unknown"),
        "main_languages": safe_list(profile.get("main_languages")),
        "core_modules": safe_list(profile.get("core_modules")),
        "function_count": profile.get("function_count", 0),
        "edge_count": profile.get("edge_count", 0),
        "module_count": profile.get("module_count", 0),
        "structure_complexity": profile.get("structure_complexity", 0),
        "source_profile": profile.get("source_profile", "")
    }


def build_repo_overview_document(profile):
    """
    构造仓库概览文档。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    metadata = build_base_metadata(profile)

    content = (
        f"历史项目 {repo_name} 是一个 {safe_text(profile.get('project_type'), 'unknown')} 类型的 OS 项目。"
        f"该项目主要语言包括 {safe_join(profile.get('main_languages'))}。"
        f"系统识别到该项目包含 {profile.get('function_count', 0)} 个函数节点、"
        f"{profile.get('edge_count', 0)} 条调用边、{profile.get('module_count', 0)} 个模块。"
        f"核心模块包括 {safe_join(profile.get('core_modules'))}。"
        f"结构复杂度为 {profile.get('structure_complexity', 0)}。"
    )

    return build_document(
        doc_id=f"{repo_name}__repo_overview",
        repo_name=repo_name,
        doc_type="repo_overview",
        content=content,
        metadata=metadata
    )


def build_core_modules_document(profile):
    """
    构造核心模块文档。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    metadata = build_base_metadata(profile)

    core_modules = safe_list(profile.get("core_modules"))
    core_module_details = profile.get("core_module_details", [])

    lines = []

    lines.append(f"历史项目 {repo_name} 的核心模块包括：{safe_join(core_modules)}。")

    if isinstance(core_module_details, list) and core_module_details:
        lines.append("系统识别到的核心模块详情如下：")

        for item in core_module_details:
            if not isinstance(item, dict):
                continue

            module_name = item.get("module_name", "unknown")
            module_weight = item.get("module_weight", 0)
            completeness = item.get("completeness", 0)
            final_score = item.get("final_score", 0)

            lines.append(
                f"- {module_name}：模块权重 {module_weight}，"
                f"完成度 {completeness}，综合值 {final_score}。"
            )
    else:
        lines.append("当前 profile 中没有详细 core_module_details 字段。")

    return build_document(
        doc_id=f"{repo_name}__core_modules",
        repo_name=repo_name,
        doc_type="core_modules",
        content="\n".join(lines),
        metadata=metadata
    )


def build_module_completeness_document(profile):
    """
    构造模块完整度文档。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    metadata = build_base_metadata(profile)

    module_completeness = profile.get("module_completeness", {})
    core_module_details = profile.get("core_module_details", [])

    lines = []

    lines.append(f"历史项目 {repo_name} 的模块完整度信息如下。")

    if isinstance(module_completeness, dict) and module_completeness:
        for module_name, value in module_completeness.items():
            lines.append(f"- {module_name}：完整度 {value}")
    elif isinstance(core_module_details, list) and core_module_details:
        for item in core_module_details:
            if not isinstance(item, dict):
                continue

            lines.append(
                f"- {item.get('module_name', 'unknown')}："
                f"完整度 {item.get('completeness', 0)}"
            )
    else:
        lines.append("当前 profile 中没有明确模块完整度字段。")

    return build_document(
        doc_id=f"{repo_name}__module_completeness",
        repo_name=repo_name,
        doc_type="module_completeness",
        content="\n".join(lines),
        metadata=metadata
    )


def build_technical_features_document(profile):
    """
    构造技术特征文档。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    metadata = build_base_metadata(profile)

    technical_features = safe_list(profile.get("technical_features"))

    lines = []

    lines.append(f"历史项目 {repo_name} 的技术特征如下：")

    if technical_features:
        for feature in technical_features:
            lines.append(f"- {feature}")
    else:
        lines.append("当前 profile 中没有明确 technical_features 字段。")

    return build_document(
        doc_id=f"{repo_name}__technical_features",
        repo_name=repo_name,
        doc_type="technical_features",
        content="\n".join(lines),
        metadata=metadata
    )


def build_weaknesses_document(profile):
    """
    构造不足与风险文档。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    metadata = build_base_metadata(profile)

    weaknesses = safe_list(profile.get("weaknesses"))

    lines = []

    lines.append(f"历史项目 {repo_name} 的不足或风险点如下：")

    if weaknesses:
        for weakness in weaknesses:
            lines.append(f"- {weakness}")
    else:
        lines.append("当前 profile 中没有明确 weaknesses 字段。")

    return build_document(
        doc_id=f"{repo_name}__weaknesses",
        repo_name=repo_name,
        doc_type="weaknesses",
        content="\n".join(lines),
        metadata=metadata
    )


def build_call_graph_document(profile):
    """
    构造调用图结构文档。
    """

    repo_name = profile.get("repo_name", "unknown_repo")
    metadata = build_base_metadata(profile)

    content = (
        f"历史项目 {repo_name} 的调用图结构信息如下："
        f"函数节点数量为 {profile.get('function_count', 0)}，"
        f"调用边数量为 {profile.get('edge_count', 0)}，"
        f"内部调用边数量为 {profile.get('internal_edge_count', 0)}，"
        f"外部调用边数量为 {profile.get('external_edge_count', 0)}，"
        f"模块数量为 {profile.get('module_count', 0)}，"
        f"结构复杂度为 {profile.get('structure_complexity', 0)}。"
        f"这些指标可用于衡量该项目的工程复杂度和系统组织程度。"
    )

    return build_document(
        doc_id=f"{repo_name}__call_graph_structure",
        repo_name=repo_name,
        doc_type="call_graph_structure",
        content=content,
        metadata=metadata
    )


def build_project_profile_documents(profile):
    """
    将单个历史项目 profile 转换为多条 RAG 文档。
    """

    full_profile = try_load_source_profile(profile)

    repo_name = full_profile.get(
        "repo_name",
        profile.get("repo_name", "unknown_repo")
    )

    if "source_profile" not in full_profile and profile.get("source_profile"):
        full_profile["source_profile"] = profile.get("source_profile")

    documents = []

    documents.append(build_repo_overview_document(full_profile))
    documents.append(build_core_modules_document(full_profile))
    documents.append(build_module_completeness_document(full_profile))
    documents.append(build_technical_features_document(full_profile))
    documents.append(build_weaknesses_document(full_profile))
    documents.append(build_call_graph_document(full_profile))

    return documents


def build_history_rag_documents(history_kb_path):
    """
    从 full 历史知识库构建标准 RAG 文档集合。
    """

    history_kb = load_json_file(history_kb_path)
    profiles = extract_profiles(history_kb)

    all_documents = []

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        documents = build_project_profile_documents(profile)
        all_documents.extend(documents)

    result = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_history_kb": history_kb_path,
        "profile_count": len(profiles),
        "document_count": len(all_documents),
        "documents": all_documents
    }

    return result


def save_history_rag_documents(rag_result):
    """
    保存 RAG 文档 JSON。
    """

    output_dir = "rag_documents"
    ensure_dir(output_dir)

    output_path = os.path.join(
        output_dir,
        "history_rag_documents.json"
    )

    save_json_file(rag_result, output_path)

    return output_path


def save_history_rag_documents_markdown(rag_result):
    """
    保存 RAG 文档预览 Markdown。
    """

    output_dir = "rag_documents"
    ensure_dir(output_dir)

    output_path = os.path.join(
        output_dir,
        "history_rag_documents.md"
    )

    lines = []

    lines.append("# 历史项目 RAG 文档预览")
    lines.append("")
    lines.append(f"生成时间：{rag_result.get('created_at')}")
    lines.append(f"来源历史知识库：`{rag_result.get('source_history_kb')}`")
    lines.append(f"历史项目数量：`{rag_result.get('profile_count')}`")
    lines.append(f"文档数量：`{rag_result.get('document_count')}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    documents = rag_result.get("documents", [])

    for index, document in enumerate(documents, start=1):
        lines.append(f"## {index}. {document.get('doc_id')}")
        lines.append("")
        lines.append(f"- 仓库名：`{document.get('repo_name')}`")
        lines.append(f"- 文档类型：`{document.get('doc_type')}`")
        lines.append("")
        lines.append("```text")
        lines.append(document.get("content", ""))
        lines.append("```")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    return output_path


def format_history_rag_documents_preview(rag_result, json_path, markdown_path):
    """
    终端预览。
    """

    lines = []

    lines.append("历史项目 RAG 文档构建完成。")
    lines.append("")
    lines.append(f"来源历史知识库：{rag_result.get('source_history_kb')}")
    lines.append(f"历史项目数量：{rag_result.get('profile_count')}")
    lines.append(f"生成文档数量：{rag_result.get('document_count')}")
    lines.append("")
    lines.append(f"JSON 输出：{json_path}")
    lines.append(f"Markdown 预览：{markdown_path}")
    lines.append("")
    lines.append("下一步可以将这些 documents 接入 LangChain / Chroma / FAISS。")

    return "\n".join(lines)