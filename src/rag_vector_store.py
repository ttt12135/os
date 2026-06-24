import os
import json
import shutil
import hashlib
from typing import List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None


DEFAULT_RAG_DOCS_PATH = "rag_documents/history_rag_documents.json"
DEFAULT_CHROMA_DIR = "vector_store/chroma_history"
DEFAULT_COLLECTION_NAME = "os_history_projects"
DEFAULT_EMBEDDING_BACKEND = "bge"
DEFAULT_BGE_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
DEFAULT_DEVICE = "cpu"
EMBEDDING_CONFIG_FILE_NAME = "embedding_config.json"

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


class SimpleHashEmbeddings(Embeddings):
    """
    本地 Hash Embedding。

    说明：
    - 用于先打通 LangChain + Chroma + Retriever 流程。
    - 不需要 API key，不需要联网。
    - 它不是最终高质量语义 embedding，后续可以替换为 BGE / OpenAI / Ollama 等真实 embedding。
    """

    def __init__(self, dimension=384):
        self.dimension = dimension

    def _tokenize(self, text):
        """
        简单分词：
        - 英文按空格和常见符号拆分
        - 中文按单字补充
        """

        if text is None:
            text = ""

        text = str(text)

        separators = [
            "\n", "\t", " ", ".", ",", ":", ";", "(", ")", "[", "]",
            "{", "}", "/", "\\", "-", "_", "|", "`", "'", '"',
            "，", "。", "：", "；", "（", "）", "【", "】"
        ]

        normalized = text

        for separator in separators:
            normalized = normalized.replace(separator, " ")

        tokens = []

        for part in normalized.split():
            part = part.strip()

            if part:
                tokens.append(part.lower())

        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                tokens.append(char)

        return tokens

    def _embed_text(self, text):
        """
        将文本转为固定维度向量。
        """

        vector = [0.0] * self.dimension
        tokens = self._tokenize(text)

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimension
            sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
            vector[index] += sign

        norm = sum(value * value for value in vector) ** 0.5

        if norm > 0:
            vector = [value / norm for value in vector]

        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


def get_embedding_model(embedding_backend=DEFAULT_EMBEDDING_BACKEND,embedding_model_name=DEFAULT_BGE_MODEL_NAME,device=DEFAULT_DEVICE):
    """
    获取 embedding 模型。

    embedding_backend:
    - hash: 使用本地 SimpleHashEmbeddings，主要用于流程验证
    - bge: 使用 HuggingFaceEmbeddings + BGE 模型，检索质量更好
    """

    embedding_backend = (embedding_backend or "hash").strip().lower()

    if embedding_backend == "hash":
        return SimpleHashEmbeddings(dimension=384)

    if embedding_backend == "bge":
        if HuggingFaceEmbeddings is None:
            raise ImportError(
                "当前环境缺少 langchain-huggingface 或 sentence-transformers。\n"
                "请先运行：pip install -U langchain-huggingface sentence-transformers"
            )

        return HuggingFaceEmbeddings(
            model_name=embedding_model_name or DEFAULT_BGE_MODEL_NAME,
            model_kwargs={"device": device or DEFAULT_DEVICE},
            encode_kwargs={"normalize_embeddings": True}
        )

    raise ValueError(
        f"不支持的 embedding_backend：{embedding_backend}，"
        f"目前只支持 hash / bge。"
    )

def get_embedding_config_path(persist_directory):
    """
    获取 embedding 配置文件路径。
    """

    return os.path.join(
        persist_directory,
        EMBEDDING_CONFIG_FILE_NAME
    )


def save_embedding_config(
    persist_directory,
    embedding_backend,
    embedding_model_name,
    device
):
    """
    保存当前向量库使用的 embedding 配置。

    这样 rag_retrieve 时可以自动读取，不需要用户重复输入。
    """

    ensure_dir(persist_directory)

    config = {
        "embedding_backend": embedding_backend,
        "embedding_model_name": embedding_model_name,
        "device": device
    }

    config_path = get_embedding_config_path(persist_directory)

    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)

    return config_path


def load_embedding_config(persist_directory):
    """
    读取向量库的 embedding 配置。

    如果没有配置文件，则默认使用 hash，兼容 v4.3a 的旧向量库。
    """

    config_path = get_embedding_config_path(persist_directory)

    if not os.path.exists(config_path):
        return {
            "embedding_backend": "hash",
            "embedding_model_name": "",
            "device": DEFAULT_DEVICE
        }

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_embedding_model_label(embedding_backend, embedding_model_name):
    """
    生成用于展示的 embedding 名称。
    """

    if embedding_backend == "hash":
        return "SimpleHashEmbeddings"

    if embedding_backend == "bge":
        return f"HuggingFaceEmbeddings::{embedding_model_name}"

    return embedding_backend

def load_rag_documents(rag_docs_path):
    """
    读取 v4.2 生成的 RAG 文档。
    """

    rag_result = load_json_file(rag_docs_path)

    documents = rag_result.get("documents", [])

    if not isinstance(documents, list):
        raise ValueError("RAG 文档格式错误：documents 字段不是列表。")

    return rag_result, documents


def clean_metadata_value(value):
    """
    Chroma metadata 更适合保存简单类型。
    这里把 list / dict 转成字符串，避免写入时报错。
    """

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, list):
        return "、".join(str(item) for item in value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def convert_to_langchain_documents(raw_documents):
    """
    将标准 RAG 文档转换成 LangChain Document。
    """

    langchain_documents = []
    ids = []

    for raw_doc in raw_documents:
        if not isinstance(raw_doc, dict):
            continue

        doc_id = raw_doc.get("doc_id")

        if not doc_id:
            continue

        content = raw_doc.get("content", "")

        metadata = raw_doc.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {}

        cleaned_metadata = {}

        for key, value in metadata.items():
            cleaned_metadata[key] = clean_metadata_value(value)

        cleaned_metadata["doc_id"] = doc_id
        cleaned_metadata["repo_name"] = raw_doc.get("repo_name", "unknown_repo")
        cleaned_metadata["doc_type"] = raw_doc.get("doc_type", "unknown")

        document = Document(
            page_content=content,
            metadata=cleaned_metadata
        )

        langchain_documents.append(document)
        ids.append(doc_id)

    return langchain_documents, ids


def is_directory_non_empty(directory):
    """
    判断目录是否存在且非空。
    """

    return os.path.exists(directory) and os.path.isdir(directory) and len(os.listdir(directory)) > 0


def build_chroma_vector_store(rag_docs_path=DEFAULT_RAG_DOCS_PATH,persist_directory=DEFAULT_CHROMA_DIR,collection_name=DEFAULT_COLLECTION_NAME,force_rebuild=True,embedding_backend=DEFAULT_EMBEDDING_BACKEND,embedding_model_name=DEFAULT_BGE_MODEL_NAME,device=DEFAULT_DEVICE):
    """
    从 RAG 文档构建 Chroma 向量库。

    v4.3b:
    - 支持 hash / bge 两种 embedding_backend
    - 默认使用 BGE embedding
    - 会保存 embedding_config.json，供 rag_retrieve 自动读取
    """

    embedding_backend = (embedding_backend or "hash").strip().lower()

    if embedding_backend == "hash":
        embedding_model_name = ""
    elif embedding_backend == "bge":
        if not embedding_model_name:
            embedding_model_name = DEFAULT_BGE_MODEL_NAME
    else:
        raise ValueError("embedding_backend 只能是 hash 或 bge。")

    if is_directory_non_empty(persist_directory) and not force_rebuild:
        return {
            "source_rag_docs": rag_docs_path,
            "persist_directory": persist_directory,
            "collection_name": collection_name,
            "profile_count": None,
            "document_count": None,
            "embedding_backend": embedding_backend,
            "embedding_model_name": embedding_model_name,
            "embedding_model": get_embedding_model_label(
                embedding_backend,
                embedding_model_name
            ),
            "status": "skipped_existing",
            "message": "检测到已有向量库目录，且 force_rebuild=False，已跳过重建。"
        }

    if force_rebuild and os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)

    ensure_dir(persist_directory)

    rag_result, raw_documents = load_rag_documents(rag_docs_path)

    langchain_documents, ids = convert_to_langchain_documents(raw_documents)

    if not langchain_documents:
        raise ValueError("没有可写入向量库的 RAG 文档。")

    embeddings = get_embedding_model(
        embedding_backend=embedding_backend,
        embedding_model_name=embedding_model_name,
        device=device
    )

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

    vector_store.add_documents(
        documents=langchain_documents,
        ids=ids
    )

    config_path = save_embedding_config(
        persist_directory=persist_directory,
        embedding_backend=embedding_backend,
        embedding_model_name=embedding_model_name,
        device=device
    )

    result = {
        "source_rag_docs": rag_docs_path,
        "persist_directory": persist_directory,
        "collection_name": collection_name,
        "profile_count": rag_result.get("profile_count"),
        "document_count": len(langchain_documents),
        "embedding_backend": embedding_backend,
        "embedding_model_name": embedding_model_name,
        "embedding_model": get_embedding_model_label(
            embedding_backend,
            embedding_model_name
        ),
        "embedding_config_path": config_path,
        "status": "success",
        "message": "向量库构建成功。"
    }

    return result


def load_chroma_vector_store(persist_directory=DEFAULT_CHROMA_DIR,collection_name=DEFAULT_COLLECTION_NAME,embedding_backend=None,embedding_model_name=None,device=None):
    """
    加载已有 Chroma 向量库。

    如果没有手动传 embedding 参数，则自动读取 embedding_config.json。
    """

    if not os.path.exists(persist_directory):
        raise FileNotFoundError(
            f"向量库目录不存在：{persist_directory}\n"
            f"请先运行 build_vector_store。"
        )

    if embedding_backend is None:
        config = load_embedding_config(persist_directory)
        embedding_backend = config.get("embedding_backend", "hash")
        embedding_model_name = config.get("embedding_model_name", "")
        device = config.get("device", DEFAULT_DEVICE)

    embeddings = get_embedding_model(
        embedding_backend=embedding_backend,
        embedding_model_name=embedding_model_name,
        device=device or DEFAULT_DEVICE
    )

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

    return vector_store


def rag_retrieve_history(
    query,
    persist_directory=DEFAULT_CHROMA_DIR,
    collection_name=DEFAULT_COLLECTION_NAME,
    top_k=5
):
    """
    从 Chroma 向量库中进行历史项目语义检索。
    """

    if query is None or str(query).strip() == "":
        raise ValueError("检索 query 不能为空。")

    vector_store = load_chroma_vector_store(
        persist_directory=persist_directory,
        collection_name=collection_name
    )

    results = vector_store.similarity_search_with_score(
        query=str(query),
        k=top_k
    )

    formatted_results = []

    for document, score in results:
        item = {
            "score": score,
            "content": document.page_content,
            "metadata": document.metadata
        }

        formatted_results.append(item)

    return {
        "query": query,
        "top_k": top_k,
        "persist_directory": persist_directory,
        "collection_name": collection_name,
        "results": formatted_results
    }


def save_rag_retrieval_result(retrieval_result):
    """
    保存 RAG 检索结果。
    """

    output_dir = "rag_documents/retrieval_results"
    ensure_dir(output_dir)

    safe_query = str(retrieval_result.get("query", "query"))
    safe_query = safe_query.replace("\\", "_").replace("/", "_").replace(" ", "_")
    safe_query = safe_query.replace("，", "_").replace("。", "_").replace("：", "_")
    safe_query = safe_query[:40]

    output_path = os.path.join(
        output_dir,
        f"rag_retrieve_{safe_query}.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(retrieval_result, file, ensure_ascii=False, indent=2)

    return output_path


def format_vector_store_build_preview(build_result):
    """
    格式化向量库构建结果。
    """

    lines = []

    lines.append("Chroma 向量库处理完成。")
    lines.append("")
    lines.append(f"状态：{build_result.get('status')}")
    lines.append(f"说明：{build_result.get('message')}")
    lines.append(f"来源 RAG 文档：{build_result.get('source_rag_docs')}")
    lines.append(f"向量库目录：{build_result.get('persist_directory')}")
    lines.append(f"Collection：{build_result.get('collection_name')}")
    lines.append(f"历史项目数量：{build_result.get('profile_count')}")
    lines.append(f"文档数量：{build_result.get('document_count')}")
    lines.append(f"Embedding backend：{build_result.get('embedding_backend')}")
    lines.append(f"Embedding 模型名：{build_result.get('embedding_model_name')}")
    lines.append(f"Embedding 模型：{build_result.get('embedding_model')}")
    lines.append(f"Embedding 配置：{build_result.get('embedding_config_path')}")
    lines.append("")
    if build_result.get("embedding_backend") == "hash":
        lines.append("说明：当前使用本地 HashEmbedding，适合验证 RAG 工程流程。")
    else:
        lines.append("说明：当前使用真实 HuggingFace/BGE embedding，检索质量将明显优于 HashEmbedding。")

    return "\n".join(lines)


def format_rag_retrieval_preview(retrieval_result, save_path=None):
    """
    格式化 RAG 检索结果。
    """

    lines = []

    lines.append("RAG 历史项目语义检索完成。")
    lines.append("")
    lines.append(f"Query：{retrieval_result.get('query')}")
    lines.append(f"Top-K：{retrieval_result.get('top_k')}")
    lines.append(f"向量库目录：{retrieval_result.get('persist_directory')}")
    lines.append("")

    if save_path:
        lines.append(f"保存路径：{save_path}")
        lines.append("")

    results = retrieval_result.get("results", [])

    if not results:
        lines.append("没有检索到结果。")
        return "\n".join(lines)

    lines.append("检索结果：")

    for index, item in enumerate(results, start=1):
        metadata = item.get("metadata", {})
        content = item.get("content", "")

        lines.append("")
        lines.append(f"{index}. {metadata.get('repo_name')} / {metadata.get('doc_type')}")
        lines.append(f"   doc_id: {metadata.get('doc_id')}")
        lines.append(f"   score: {item.get('score')}")
        lines.append(f"   content: {content[:180]}...")

    return "\n".join(lines)