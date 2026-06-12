"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# Cấu hình đồng bộ hoàn toàn với mô hình và cơ sở dữ liệu ở Task 4
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DB_PATH = Path(__file__).parent.parent / "data" / "vector_store"


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not DB_PATH.exists():
        print("⚠ Thư mục Vector Store không tồn tại. Hãy chạy Task 4 trước!")
        return []

    # HOÀN THÀNH TODO: Bước 1: Embed query bằng cùng model ở Task 4
    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(query).tolist()

    # HOÀN THÀNH TODO: Bước 2: Query vector store (ChromaDB cục bộ)
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_or_create_collection(name="DrugLawDocs")

    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    if not response or not response["ids"] or not response["ids"][0]:
        return []

    # HOÀN THÀNH TODO: Bước 3: Return top_k results đúng định dạng cấu trúc đề bài
    results = []
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    distances = response["distances"][0]

    for i in range(len(documents)):
        # Chuyển đổi khoảng cách khoảng cách (distance) thành điểm tương đồng (similarity)
        # Điểm similarity tỉ lệ nghịch với khoảng cách khoảng cách hình học của ChromaDB
        score = 1.0 / (1.0 + distances[i])
        
        results.append({
            "content": documents[i],
            "score": float(score),
            "metadata": metadatas[i]
        })

    # Đảm bảo danh sách kết quả được xếp giảm dần theo điểm số tương đồng
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")