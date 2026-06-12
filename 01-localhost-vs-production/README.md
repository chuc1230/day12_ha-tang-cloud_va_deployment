# Section 1 — Từ Localhost Đến Production

## Mục tiêu học
- Hiểu tại sao "it works on my machine" là vấn đề
- Nhận ra sự khác biệt giữa dev và production environment
- Áp dụng 4 nguyên tắc 12-factor cơ bản

---

## Ví dụ Basic — Agent "Kiểu Localhost"

```
develop/
├── app.py          # ❌ Anti-patterns: hardcode secrets, no config, no health check
└── requirements.txt
```

### Chạy thử
```bash
cd develop
pip install -r requirements.txt
python app.py
# Truy cập: http://localhost:8000
```

### Những vấn đề trong code này:
1. API key hardcode trong code
2. Không có health check endpoint
3. Debug mode bật cứng
4. Không xử lý SIGTERM gracefully
5. Config không đến từ environment

---

## Ví dụ Advanced — 12-Factor Compliant Agent

```
production/
├── app.py          # ✅ Clean: config from env, health check, graceful shutdown
├── config.py       # ✅ Centralized config management
├── .env.example    # ✅ Template — không commit .env thật
└── requirements.txt
```

### Chạy thử
```bash
cd production
pip install -r requirements.txt
cp .env.example .env
# Sửa .env nếu cần
python app.py
```

### So sánh với Basic:

| | Basic (❌) | Advanced (✅) |
|--|-----------|--------------|
| Config | Hardcode trong code | Đọc từ env vars |
| Secrets | `api_key = "sk-abc123"` | `os.getenv("OPENAI_API_KEY")` |
| Port | Cố định `8000` | Từ `PORT` env var |
| Health check | Không có | `GET /health` |
| Shutdown | Tắt đột ngột | Graceful — hoàn thành request hiện tại |
| Logging | `print()` | Structured JSON logging |

---

## Câu hỏi thảo luận

1. Điều gì xảy ra nếu bạn push code với API key hardcode lên GitHub public? Có khả năng rất cao sẽ bị các bot quét và bị lộ API key, 
2. Tại sao stateless quan trọng khi scale? Vì như thế giúp hệ thống dễ mở rộng, một request từ client có thể gửi đến bất kỳ server nào trong hệ thống, và server đó đều có thể xử lý được mà không cần biết các request trước đó đã làm gì.
3. 12-factor nói "dev/prod parity" — nghĩa là gì trong thực tế? nghĩa là cần giữ cho môi trường dev và môi trường product giống nhau nhất có thể. Mục tiêu tối thượng của nguyên tắc này là: "Nếu nó chạy tốt trên máy của tôi thì chắc chắn nó chạy tốt trên product".
