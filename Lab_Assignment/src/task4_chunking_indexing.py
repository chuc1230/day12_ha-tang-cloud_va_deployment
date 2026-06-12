"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn (Yêu cầu bài Lab)
# =============================================================================

# LÝ DO CHỌN CHUNKING STRATEGY (RecursiveCharacterTextSplitter):
# 1. Cấu trúc dữ liệu của chúng ta bao gồm cả văn bản pháp lý (Nghị định/Luật) có cấu trúc dài và các bài báo tin tức ngắn.
# 2. Phương pháp "recursive" chia nhỏ văn bản một cách thông minh bằng cách thử nghiệm lần lượt các ký tự ngắt câu 
#    (xuống dòng đôi, xuống dòng đơn, dấu chấm, khoảng trắng). Điều này giúp giữ các câu, các đoạn luật liên quan 
#    ở nguyên cùng một khối, tránh tình trạng câu bị cắt nửa chừng làm mất ngữ nghĩa gốc.

CHUNK_SIZE = 600        
# LÝ DO CHỌN CHUNK SIZE = 600:
# - Nếu chọn kích thước quá nhỏ (ví dụ 100-200 từ), một Điều luật hoặc một bối cảnh bài báo sẽ bị xé nát, Chatbot không đủ thông tin trả lời.
# - Nếu chọn kích thước quá lớn (ví dụ >1000 từ), chunk sẽ bị lẫn nhiều thông tin tạp nham và vượt quá giới hạn ngữ cảnh của mô hình nhúng.
# - 600 từ là con số tối ưu, vừa vặn chứa trọn vẹn nội dung của 1-2 Điều luật hoặc 1 đoạn phóng sự tin tức lớn.

CHUNK_OVERLAP = 100      
# LÝ DO CHỌN CHUNK OVERLAP = 100:
# - Tạo ra một khoảng giao thoa gối đầu (100 từ) giữa khối văn bản trước và khối văn bản sau.
# - Điều này đảm bảo thông tin nằm ở vùng biên (vị trí bị cắt) không bị mất ngữ cảnh liên kết, giúp thông tin liền mạch khi truy vấn.

CHUNKING_METHOD = "recursive"  


# LÝ DO CHỌN EMBEDDING MODEL (all-MiniLM-L6-v2):
# 1. Đây là mô hình cục bộ (Local Model) cực kỳ gọn nhẹ (chỉ khoảng 90MB), giúp quá trình tải và tính toán sinh vector nhúng 
#    diễn ra vô cùng nhanh chóng ngay trên CPU/GPU của máy cá nhân mà không bị nghẽn mạng hay phụ thuộc vào OpenAI API Key.
# 2. Mô hình này rất phù hợp để chạy thử nghiệm nhanh toàn bộ pipeline của bài Lab (Proof of Concept) trước khi nâng cấp lên các hệ thống lớn.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  
EMBEDDING_DIM = 384  # Kích thước số chiều vector bắt buộc của mô hình all-MiniLM-L6-v2


# LÝ DO CHỌN VECTOR STORE (ChromaDB):
# 1. ChromaDB hỗ trợ lưu trữ cơ sở dữ liệu Vector Store trực tiếp dưới dạng file cục bộ (file-based) trong thư mục dự án.
# 2. Khác với Weaviate (đòi hỏi phải cài đặt và kích hoạt hệ thống ảo hóa Docker Desktop chạy ngầm vốn rất nặng và dễ lỗi môi trường),
#    ChromaDB vận hành hoàn toàn bằng Python thuần, giúp giảm thiểu tối đa tài nguyên máy và đảm bảo script luôn thực thi thành công.
VECTOR_STORE = "chromadb"  


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        print(f"⚠ Thư mục standardized không tồn tại: {STANDARDIZED_DIR}")
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đệ quy và đóng gói đầy đủ metadata tương ứng.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = []
    for doc in documents:
        # Nếu văn bản quá ngắn, ép buộc đưa nguyên văn bản vào 1 chunk thay vì bỏ qua
        if len(doc["content"].strip()) < 10:
            continue
            
        splits = splitter.split_text(doc["content"])
        
        # Nếu bộ chia đệ quy trả về rỗng do văn bản ngắn hơn cả chunk_size, tự gom thành 1 bản ghi
        if not splits:
            splits = [doc["content"]]
            
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "source": doc["metadata"]["source"],
                    "doc_type": doc["metadata"]["type"],
                    "chunk_index": i
                }
            })
    return chunks

def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Tính toán vector nhúng (Embedding) cho toàn bộ chunks bằng SentenceTransformer.
    """
    from sentence_transformers import SentenceTransformer
    
    print(f"-> Đang khởi tạo mô hình nhúng cục bộ: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    texts = [c["content"] for c in chunks]
    print(f"-> Tiến hành tính toán định danh vector cho {len(texts)} đoạn văn bản...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    for chunk, emb in zip(chunks, embeddings):
        # Ép mảng NumPy về kiểu list thuần của Python để các cơ sở dữ liệu Vector Store nhận diện chính xác
        chunk["embedding"] = emb.tolist()
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu trữ cấu trúc Vector và Metadata của chunks vào cơ sở dữ liệu ChromaDB cục bộ.
    """
    import chromadb

    print("-> Đang khởi tạo kết nối tới ChromaDB (Local File)...")
    db_path = Path(__file__).parent.parent / "data" / "vector_store"
    client = chromadb.PersistentClient(path=str(db_path))

    collection_name = "DrugLawDocs"
    collection = client.get_or_create_collection(name=collection_name)

    print(f"-> Đang tiến hành nạp {len(chunks)} chunks vào ChromaDB...")
    
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in chunks:
        source_stem = Path(chunk["metadata"]["source"]).stem
        idx = chunk["metadata"]["chunk_index"]
        # Thiết lập ID duy nhất để phân biệt giữa các đoạn (ví dụ: Luat-120_chunk_0)
        ids.append(f"{source_stem}_chunk_{idx}")
        
        embeddings.append(chunk["embedding"])
        documents.append(chunk["content"])
        metadatas.append({
            "source": chunk["metadata"]["source"],
            "doc_type": chunk["metadata"]["doc_type"]
        })

    # Đẩy toàn bộ danh sách dữ liệu có cấu trúc xuống file database cục bộ
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    print("  ✓ Đồng bộ dữ liệu thành công lên ChromaDB (Local Database)!")


def run_pipeline():
    """Chạy toàn bộ quy trình pipeline tuần tự: Load -> Chunk -> Embed -> Index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()