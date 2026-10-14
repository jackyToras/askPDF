import os
import uuid
import chromadb
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_ollama import OllamaEmbeddings, OllamaLLM

load_dotenv()

embedding_model = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
llm = OllamaLLM(model="mistral", base_url="http://localhost:11434", temperature=0)


def get_chroma_client():
    return chromadb.PersistentClient(path="./chroma_db")


def extract_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file")
    return loader.load()


def process_and_embed(file_path, user_id="default", filename="document"):
    docs = extract_text(file_path)
    if not docs:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)
    texts = [c.page_content.strip() for c in chunks if c.page_content and c.page_content.strip()]
    if not texts:
        return []

    vectors = embedding_model.embed_documents(texts)

    page_numbers = []
    for chunk in chunks:
        if hasattr(chunk, 'metadata') and 'page' in chunk.metadata:
            page_numbers.append(chunk.metadata['page'] + 1)  # Pages are 0-indexed
        else:
            page_numbers.append(0)

    return [
        {
            "id": str(uuid.uuid4()),
            "text": texts[i],
            "embedding": vectors[i],
            "user_id": user_id,
            "source": filename,
            "page": page_numbers[i] if i < len(page_numbers) else 0
        }
        for i in range(len(texts))
    ]


def get_supported_formats():
    return ["pdf", "docx"]


def save_to_chromadb(chunks, client, collection_name):
    try:
        collection = client.get_collection(name=collection_name)
    except:
        collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        metadatas=[{
            "user_id": c["user_id"],
            "source": c["source"],
            "page": int(c["page"])
        } for c in chunks]
    )


def answer_query(query, client, collection_name, user_id="default", top_k=5):
    try:
        collection = client.get_collection(name=collection_name)
    except:
        return "No documents uploaded."

    query_vector = embedding_model.embed_query(query)

    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where={"user_id": user_id}
        )
    except Exception as e:
        print(f"Filter query failed: {e}, falling back to unfiltered search")
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        if "metadatas" in results and results["metadatas"]:
            filtered_docs = []
            filtered_metas = []
            for doc, meta in zip(results.get("documents", [[]]), results.get("metadatas", [[]])):
                if isinstance(meta, list):
                    filtered_doc = []
                    filtered_meta = []
                    for d, m in zip(doc, meta):
                        if m.get("user_id") == user_id:
                            filtered_doc.append(d)
                            filtered_meta.append(m)
                    if filtered_doc:
                        filtered_docs.append(filtered_doc[:top_k])
                        filtered_metas.append(filtered_meta[:top_k])
                else:
                    if meta.get("user_id") == user_id:
                        filtered_docs.append(doc)
                        filtered_metas.append(meta)
            results["documents"] = filtered_docs
            results["metadatas"] = filtered_metas

    docs_lists = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    if not docs_lists or not docs_lists[0]:
        return "No relevant context found in your documents."

    context = "\n".join(docs_lists[0])


    sources = set()
    if metadatas and metadatas[0]:
        meta_list = metadatas[0] if isinstance(metadatas[0], list) else [metadatas[0]]
        for meta in meta_list:
            if isinstance(meta, dict):
                source_str = f"{meta.get('source', 'Unknown')}"
                page = meta.get('page', 0)
                if page > 0:
                    source_str += f" (page {page})"
                sources.add(source_str)

    sources_str = ", ".join(sorted(sources)) if sources else "Unknown source"

    prompt = f"""Answer ONLY from the context below.
If not found, say you don't know.

Context:
{context}

Question:
{query}"""

    answer = llm.invoke(prompt)

    return f"{answer}\n\n[Sources: {sources_str}]"