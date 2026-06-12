"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Điền danh sách URL bài báo cần crawl
ARTICLE_URLS = [
    "https://vnexpress.net/ca-si-miu-le-bi-bat-voi-cao-buoc-to-chuc-su-dung-ma-tuy-5074769.html",
    "https://tuoitre.vn/hoa-hau-hhen-nie-va-nghe-si-xuan-bac-keu-goi-gioi-tre-khong-thu-ma-tuy-du-chi-mot-lan-20231216141246353.htm",
    "https://tuoitre.vn/sao-han-lee-sun-kyun-duoc-phat-hien-da-chet-trong-xe-hoi-ngoai-cong-vien-20231227092224243.htm",
    "https://tuoitre.vn/yoo-ah-in-bi-cao-buoc-dung-chat-cam-181-lan-ep-nguoi-khac-hut-can-sa-20231102143132349.htm",
    "https://vnexpress.net/ma-tuy-trong-loi-song-showbiz-5074606.html"
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler

    # TODO: Implement crawling logic
    # async with AsyncWebCrawler() as crawler:
    #     result = await crawler.arun(url=url)
    #     return {
    #         "url": url,
    #         "title": result.metadata.get("title", "Unknown"),
    #         "date_crawled": datetime.now().isoformat(),
    #         "content_markdown": result.markdown,
    #     }
    # HOÀN THÀNH TODO: Triển khai logic crawling bằng AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        # Lấy title từ metadata an toàn, nếu không có thì fallback về title trong HTML đằng sau kết quả
        title = "Unknown"
        if result.metadata:
            title = result.metadata.get("title") or result.metadata.get("og:title")
        
        # Nếu vẫn không tìm thấy title từ metadata, lấy tạm dòng đầu tiên hoặc để Unknown
        if not title or title == "Unknown":
            title = url.split("/")[-1].replace(".html", "").replace(".htm", "").replace("-", " ")

        return {
            "url": url,
            "title": title.strip(),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown if result.markdown else "",
        }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
