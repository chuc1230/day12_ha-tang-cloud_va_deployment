"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from pathlib import Path
from rank_bm25 import BM25Okapi
import numpy as np

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# HOÀN THÀNH TODO: Tải cơ sở dữ liệu văn bản từ thư mục standardized
CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}


def init_corpus():
    """Đọc toàn bộ văn bản đã chuẩn hóa phục vụ xây dựng Corpus cho BM25."""
    global CORPUS
    if CORPUS or not STANDARDIZED_DIR.exists():
        return

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        
        # Chia nhỏ văn bản theo đoạn văn để đảm bảo độ mịn khi chấm điểm BM25 tương đương size chunk ở Task 4
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 20]
        for idx, para in enumerate(paragraphs):
            CORPUS.append({
                "content": para,
                "metadata": {"source": md_file.name, "doc_type": doc_type, "chunk_index": idx}
            })


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    # HOÀN THÀNH TODO: Tokenize văn bản tiếng Việt đơn giản bằng split() chữ thường theo hướng dẫn bài Lab
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    # Khởi tạo nạp dữ liệu vào bộ nhớ
    init_corpus()
    if not CORPUS:
        print("⚠ Không tìm thấy tài liệu nào trong data/standardized/ để xây dựng chỉ mục BM25.")
        return []

    bm25 = build_bm25_index(CORPUS)
    
    # HOÀN THÀNH TODO: Triển khai logic tìm kiếm Lexical BM25
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Trích xuất top_k vị trí có điểm số cao nhất từ mảng NumPy
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        # Chỉ ghi nhận các đoạn văn bản thực sự khớp từ khóa (score > 0)
        if scores[idx] > 0:
            results.append({
                "content": CORPUS[idx]["content"],
                "score": float(scores[idx]),
                "metadata": CORPUS[idx]["metadata"]
            })
    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")