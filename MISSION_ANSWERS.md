# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **API key bị hardcode:** Biến `OPENAI_API_KEY` được khai báo trực tiếp dưới dạng chuỗi trần trong file code (`app.py`), dễ bị rò rỉ khi đẩy lên GitHub.
2. **Không quản lý cấu hình tập trung:** Các tham số `DEBUG` và `MAX_TOKENS` bị fix cứng trong code thay vì đọc từ biến môi trường.
3. **Sử dụng print thay vì logging:** Lệnh `print` không hỗ trợ phân cấp độ ưu tiên log (INFO, DEBUG, ERROR), không có timestamp và vô tình in cả API key nhạy cảm ra log.
4. **Không có health check endpoint:** Không có các route như `/health` hay `/ready` khiến các nền tảng đám mây không thể tự động giám sát trạng thái để restart container khi gặp lỗi treo.
5. **Cố định host và port:** Host được gán cứng `localhost` (khiến ứng dụng không thể truy cập từ bên ngoài Docker container) và port `8000` được fix cứng thay vì nhận động từ môi trường.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| **Config** | Hardcode trong mã nguồn | Sử dụng Environment Variables | Dễ dàng thay đổi cấu hình giữa các môi trường mà không cần sửa code, bảo mật tốt các thông tin bí mật (secrets). |
| **Health Check** | Không hỗ trợ | Có `/health` (Liveness) & `/ready` (Readiness) | Giúp cloud platforms phát hiện dịch vụ bị treo để restart (liveness) và biết khi nào nên định tuyến traffic (readiness). |
| **Logging** | Sử dụng `print()` đơn giản | Sử dụng JSON Structured Logging | Giúp lưu trữ logs có cấu trúc, dễ phân tích, truy vấn và quản lý tập trung qua các tool như Loki, ELK, Datadog. |
| **Shutdown** | Đột ngột (Kill process) | Graceful Shutdown (Xử lý SIGTERM) | Đảm bảo hoàn thành các request đang dở dang và giải phóng tài nguyên (DB, Redis connection) an toàn trước khi dừng hẳn. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11`. Đây là full distribution chứa môi trường chạy Python và đầy đủ thư viện Debian cơ bản (kích thước khoảng 1GB).
2. **Working directory:** `/app`. Thư mục mặc định trong container mà các câu lệnh tiếp theo sẽ chạy bên trong.
3. **Tại sao COPY requirements.txt trước:** Để tận dụng cơ chế cache layer của Docker. Khi mã nguồn thay đổi nhưng danh sách dependencies giữ nguyên, Docker sẽ tái sử dụng cache của layer cài đặt thư viện (`pip install`), giảm thời gian build image.
4. **CMD vs ENTRYPOINT:** `CMD` chỉ định câu lệnh chạy mặc định của container và có thể bị ghi đè hoàn toàn bởi các tham số truyền thêm ở cuối lệnh `docker run`. `ENTRYPOINT` quy định tiến trình cố định chạy khi container khởi động, các tham số truyền thêm sẽ được coi là đối số (arguments) của tiến trình đó.

### Exercise 2.3: Image size comparison
- **Develop:** 1.01 GB
- **Production (Multi-stage build):** 190 MB
- **Difference:** Giảm khoảng **81.2%** dung lượng.

**Lý do:** Ở stage 1 (builder), chúng ta cài đặt đầy đủ compiler tools (gcc, libpq-dev) để compile các thư viện C. Ở stage 2 (runtime), chúng ta chỉ sử dụng image `python:3.11-slim` sạch và copy các thư viện đã build sang, loại bỏ toàn bộ compiler tools và file cache tạm.

### Exercise 2.4: Architecture Diagram

```
                 [Client / Browser]
                         │
                         ▼ (HTTP requests on Port 80)
             [Nginx Load Balancer]
                         │
        ┌────────────────┼────────────────┐
        ▼ (Port 8000)    ▼ (Port 8000)    ▼ (Port 8000)
    [agent-1]        [agent-2]        [agent-3]
        │                │                │
        └────────────────┼────────────────┘
                         ▼ (Port 6379)
                      [Redis]
```

- **Services được khởi chạy:** `agent` (scale lên 3 instances), `redis` (database lưu state/history), và `nginx` (làm load balancer).
- **Cách giao tiếp:** Client gửi HTTP request tới cổng 80 của Nginx. Nginx đóng vai trò reverse proxy chuyển tiếp các request tới các instance `agent` theo thuật toán round-robin. Mỗi instance `agent` kết nối tới cổng 6379 của container `redis` để đọc/ghi lịch sử hội thoại của người dùng, giúp hệ thống hoạt động stateless hoàn hảo.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **Public URL:** `https://day12-agent-production.up.railway.app`
- **Health Check Endpoint:** `https://day12-agent-production.up.railway.app/health`

### Exercise 3.2: Comparison of `render.yaml` and `railway.toml`
- `render.yaml` là file cấu hình Infrastructure as Code (IaC) toàn diện cho Render. Nó cho phép định nghĩa nhiều dịch vụ khác nhau trong một cụm (ví dụ: một web service chạy Python và một database service chạy Redis), đồng thời mô tả rõ cấu hình phần cứng (RAM, CPU), region, và mối quan hệ biến môi trường giữa chúng.
- `railway.toml` là file cấu hình chỉ dành cho service hiện tại trên Railway. Nó rất đơn giản và chủ yếu định nghĩa các bước build, chạy (start command), và watch patterns. Các dịch vụ phụ trợ như Redis thường được thêm trực tiếp thông qua Railway Dashboard bằng giao diện trực quan và liên kết biến môi trường tự động.

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- **API Key Auth:** endpoint `/ask` yêu cầu header `X-API-Key`. Không gửi key trả về `401 Unauthorized`. Gửi sai key trả về `403 Forbidden`. Gửi đúng key trả về kết quả `200 OK`.
- **Rate Limiting:** Giới hạn 20 requests/phút. Khi chạy vòng lặp gửi liên tục 21 requests, request thứ 21 lập tức nhận về status code `429 Too Many Requests` với header `Retry-After: 60`.
- **Cost Guard:** Giới hạn ngân sách tối đa của mỗi người dùng theo cấu hình `DAILY_BUDGET_USD` (hoặc `MONTHLY_BUDGET_USD`). Khi tổng số token sử dụng quy đổi ra tiền đạt mức giới hạn, API sẽ từ chối xử lý và trả về lỗi `503 Service Unavailable` hoặc `402 Payment Required`.

### Exercise 4.4: Cost guard implementation
Giải pháp đã cài đặt trong [app/cost_guard.py](file:///F:/student/AIthucChien/lab12/day12_ha-tang-cloud_va_deployment/app/cost_guard.py):
- Mỗi khi người dùng gọi API, chúng ta tính toán số lượng token ước tính của câu hỏi (input) và câu trả lời (output).
- Giá trị này được nhân với đơn giá (ví dụ: $0.15/1M input tokens và $0.60/1M output tokens cho gpt-4o-mini).
- Tổng chi phí trong ngày được cộng dồn và so sánh với hạn mức budget trong ngày (`DAILY_BUDGET_USD`). Nếu vượt mức, hệ thống ném ra lỗi `HTTPException` với status code `503` (Daily budget exhausted).

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
1. **Health checks:** Đã thiết lập `/health` (liveness check trả về 200 trạng thái ứng dụng) và `/ready` (readiness check kiểm tra xem ứng dụng đã sẵn sàng nhận request chưa).
2. **Graceful shutdown:** Sử dụng signal handler để bắt tín hiệu `SIGTERM` từ Docker container orchestrator. Khi nhận được tín hiệu tắt, cờ `is_ready` sẽ chuyển sang `False` để báo cho Load Balancer dừng chuyển traffic mới đến, đồng thời ứng dụng đợi vài giây để xử lý nốt các request dở dang trong hàng đợi trước khi ngắt các kết nối và thoát tiến trình.
3. **Stateless design:** Toàn bộ lịch sử hội thoại hoặc các thông tin tracking được đồng bộ và lưu trữ tại Redis thay vì lưu trong bộ nhớ RAM (In-Memory). Nhờ vậy, khi chạy 3 instance song song qua Load Balancer, người dùng có thể gửi request đến bất kỳ instance nào mà vẫn giữ nguyên được ngữ cảnh trò chuyện.
