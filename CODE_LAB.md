#  Code Lab: Deploy Your AI Agent to Production

> **AICB-P1 · VinUniversity 2026**  
> Thời gian: 3-4 giờ | Độ khó: Intermediate

##  Mục Tiêu

Sau khi hoàn thành lab này, bạn sẽ:
- Hiểu sự khác biệt giữa development và production
- Containerize một AI agent với Docker
- Deploy agent lên cloud platform
- Bảo mật API với authentication và rate limiting
- Thiết kế hệ thống có khả năng scale và reliable

---

##  Yêu Cầu

```bash
 Python 3.11+
 Docker & Docker Compose
 Git
 Text editor (VS Code khuyến nghị)
 Terminal/Command line
```

**Không cần:**
-  OpenAI API key (dùng mock LLM)
-  Credit card
-  Kinh nghiệm DevOps trước đó

---

##  Lộ Trình Lab

| Phần | Thời gian | Nội dung |
|------|-----------|----------|
| **Part 1** | 30 phút | Localhost vs Production |
| **Part 2** | 45 phút | Docker Containerization |
| **Part 3** | 45 phút | Cloud Deployment |
| **Part 4** | 40 phút | API Security |
| **Part 5** | 40 phút | Scaling & Reliability |
| **Part 6** | 60 phút | Final Project |

---

## Part 1: Localhost vs Production (30 phút)

###  Concepts

**Vấn đề:** "It works on my machine" — code chạy tốt trên laptop nhưng fail khi deploy.

**Nguyên nhân:**
- Hardcoded secrets
- Khác biệt về environment (Python version, OS, dependencies)
- Không có health checks
- Config không linh hoạt

**Giải pháp:** 12-Factor App principles

###  Exercise 1.1: Phát hiện anti-patterns

```bash
cd 01-localhost-vs-production/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm ít nhất 5 vấn đề.

**Các vấn đề tìm được:**
1. **API key bị hardcode:** `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"`. Nếu commit mã nguồn lên GitHub, key sẽ bị lộ.
2. **Không có config management:** Cấu hình các biến tĩnh `DEBUG = True` và `MAX_TOKENS = 500` trực tiếp trong code, không thể thay đổi linh động qua biến môi trường.
3. **Sử dụng print thay vì logging:** Hàm `print` không ghi nhận metadata quan trọng (thời gian, mức độ lỗi,...) và in cả API key ra log terminal (`print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`).
4. **Không có health check endpoint:** Không có `/health` hay `/ready` để cloud platform tự động theo dõi trạng thái và khởi động lại container khi bị crash.
5. **Cấu hình host và port cố định:** Chạy trên `localhost` (chỉ nhận request nội bộ, không chạy được trong Docker container) và port cứng `8000` thay vì đọc từ biến môi trường `PORT` (được các nền tảng tự động inject).

<details>
<summary> Gợi ý</summary>

Tìm:
- API key hardcode
- Port cố định
- Debug mode
- Không có health check
- Không xử lý shutdown

</details>

###  Exercise 1.2: Chạy basic version

```bash
pip install -r requirements.txt
python app.py
```

Test:
```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** Nó chạy! Nhưng có production-ready không?

###  Exercise 1.3: So sánh với advanced version

```bash
cd ../production
cp .env.example .env
pip install -r requirements.txt
python app.py
```

**Nhiệm vụ:** So sánh 2 files `app.py`. Điền vào bảng:

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Dễ thay đổi giữa các môi trường (dev, staging, prod) mà không cần đổi code, không làm lộ thông tin nhạy cảm khi commit lên GitHub. |
| Health check | ❌ Không có | ✅ /health và /ready | Cloud platform biết khi nào ứng dụng bị treo để tự động restart (liveness) và khi nào sẵn sàng nhận request (readiness). |
| Logging | print() | JSON Structured | Structured logs ở dạng JSON giúp dễ dàng thu thập, phân tích và tìm kiếm tập trung bằng các công cụ như Datadog, ELK, Loki. |
| Shutdown | Đột ngột | Graceful | Đảm bảo các request đang chạy được hoàn thành nốt, đóng các kết nối tới database/Redis an toàn trước khi tắt ứng dụng, tránh mất mát dữ liệu. |

###  Checkpoint 1

- [ ] Hiểu tại sao hardcode secrets là nguy hiểm
- [ ] Biết cách dùng environment variables
- [ ] Hiểu vai trò của health check endpoint
- [ ] Biết graceful shutdown là gì

---

## Part 2: Docker Containerization (45 phút)

###  Concepts

**Vấn đề:** "Works on my machine" part 2 — Python version khác, dependencies conflict.

**Giải pháp:** Docker — đóng gói app + dependencies vào container.

**Benefits:**
- Consistent environment
- Dễ deploy
- Isolation
- Reproducible builds

###  Exercise 2.1: Dockerfile cơ bản

```bash
cd ../../02-docker/develop
```

**Nhiệm vụ:** Đọc `Dockerfile` và trả lời:

1. **Base image là gì?**
   - Trả lời: Base image là `python:3.11`. Đây là image chứa đầy đủ hệ điều hành Debian và môi trường chạy Python 3.11 (dung lượng khoảng 1GB).
2. **Working directory là gì?**
   - Trả lời: Working directory là `/app`. Đây là thư mục làm việc mặc định trong container, nơi tất cả các câu lệnh tiếp theo (như COPY, RUN, CMD) được thực thi trong bối cảnh thư mục này.
3. **Tại sao COPY requirements.txt trước?**
   - Trả lời: Để tối ưu hóa Docker layer cache. Docker lưu trữ cache cho từng layer (dòng lệnh). Vì dependencies (`requirements.txt`) ít khi thay đổi so với source code, việc copy và cài đặt dependencies trước sẽ giúp Docker tái sử dụng cache cho layer này trong những lần build sau khi chỉ có source code thay đổi, giảm đáng kể thời gian build.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - Trả lời:
     - `CMD` định nghĩa câu lệnh và/hoặc tham số mặc định khi container chạy. Nó có thể dễ dàng bị ghi đè hoàn toàn khi ta truyền câu lệnh khác ở cuối lệnh `docker run`.
     - `ENTRYPOINT` định nghĩa một tiến trình cố định chạy khi container khởi động. Các tham số truyền vào từ `docker run` hoặc `CMD` sẽ được nối tiếp (append) vào làm đối số của tiến trình này chứ không ghi đè tiến trình đó.

###  Exercise 2.2: Build và run

```bash
# Build image
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Quan sát:** Image size là bao nhiêu?
- Trả lời: Dung lượng image `my-agent:develop` khoảng **1.01 GB**. Dung lượng này rất lớn và không tối ưu cho việc truyền tải hay lưu trữ trên môi trường production.

###  Exercise 2.3: Multi-stage build

```bash
cd ../production
```

**Nhiệm vụ:** Đọc `Dockerfile` và trả lời:
- **Stage 1 (Builder) làm gì?**
  - Trả lời: Sử dụng `python:3.11-slim` để cài đặt các build dependencies (như gcc, libpq-dev) và tiến hành cài các Python packages cần thiết vào thư mục user (`/root/.local`). Image này chỉ được dùng làm môi trường build tạm thời.
- **Stage 2 (Runtime) làm gì?**
  - Trả lời: Khởi tạo từ một image `python:3.11-slim` sạch hoàn toàn, copy thư mục packages đã build sẵn từ builder sang (`/home/appuser/.local`), copy code dự án, cấu hình chạy dưới quyền user phi root (`appuser`), Expose port và khai báo cấu hình healthcheck.
- **Tại sao image nhỏ hơn?**
  - Trả lời: Vì image ở Stage 2 (Runtime) là kết quả cuối cùng không chứa các package build (như gcc, compiler tools) hay cache cài đặt trung gian. Dung lượng image `my-agent:advanced` được rút gọn từ 1.01 GB xuống còn khoảng **190 MB** (giảm ~80%).

###  Exercise 2.4: Docker Compose stack

**Nhiệm vụ:** Đọc `docker-compose.yml` và vẽ architecture diagram.

**Architecture Diagram:**
```
[Client / Browser]
        │ (HTTP requests, Port 80)
        ▼
  [Nginx (Reverse Proxy / Load Balancer)]
        │
        ├─► [agent-1] (Port 8000) ──► [Redis] (Port 6379)
        ├─► [agent-2] (Port 8000) ──► [Redis] (Port 6379)
        └─► [agent-3] (Port 8000) ──► [Redis] (Port 6379)
```

- **Services nào được start?**
  - Trả lời: `agent` (được scale lên 3 instances), `redis` (in-memory data store), và `nginx` (làm load balancer/reverse proxy).
- **Chúng communicate thế nào?**
  - Trả lời: Client gửi HTTP requests tới cổng 80 của Nginx. Nginx thực hiện cân bằng tải, định tuyến (round-robin) các requests tới các instances của service `agent` trên mạng Docker nội bộ. Mỗi instance `agent` kết nối trực tiếp với service `redis` bằng cách gọi hostname `redis` trên cổng `6379` để chia sẻ thông tin trạng thái người dùng (stateless architecture).

Test:
```bash
# Health check
curl http://localhost/health

# Agent endpoint
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
```

###  Checkpoint 2

- [ ] Hiểu cấu trúc Dockerfile
- [ ] Biết lợi ích của multi-stage builds
- [ ] Hiểu Docker Compose orchestration
- [ ] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment (45 phút)

###  Concepts

**Vấn đề:** Laptop không thể chạy 24/7, không có public IP.

**Giải pháp:** Cloud platforms — Railway, Render, GCP Cloud Run.

**So sánh:**

| Platform | Độ khó | Free tier | Best for |
|----------|--------|-----------|----------|
| Railway | ⭐ | $5 credit | Prototypes |
| Render | ⭐⭐ | 750h/month | Side projects |
| Cloud Run | ⭐⭐⭐ | 2M requests | Production |

###  Exercise 3.1: Deploy Railway (15 phút)

```bash
cd ../../03-cloud-deployment/railway
```

**Steps:**

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Login:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

4. Set environment variables:
```bash
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
```

5. Deploy:
```bash
railway up
```

6. Get public URL:
```bash
railway domain
```

**Nhiệm vụ:** Test public URL với curl hoặc Postman.

Test:
```bash
# Health check
curl http://student-agent-domain/health

# Agent endpoint
curl http://studen-agent-domain/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```

###  Exercise 3.2: Deploy Render (15 phút)

```bash
cd ../render
```

**Steps:**

1. Push code lên GitHub (nếu chưa có)
2. Vào [render.com](https://render.com) → Sign up
3. New → Blueprint
4. Connect GitHub repo
5. Render tự động đọc `render.yaml`
6. Set environment variables trong dashboard
7. Deploy!

**Nhiệm vụ:** So sánh `render.yaml` với `railway.toml`. Khác nhau gì?
- Trả lời:
  - `render.yaml` định nghĩa cấu trúc Infrastructure as Code (IaC) để cấu hình nhiều dịch vụ đồng thời (ví dụ: tạo song song một Web Service chạy Agent và một Redis Database Service). Nó mô tả chi tiết cả các thông tin hệ thống như RAM, CPU plan, cách liên kết môi trường giữa Web và Redis.
  - `railway.toml` là file cấu hình đơn lẻ, nhẹ nhàng cho chính project hiện tại, dùng để khai báo cách build & chạy (build command, start command, watch patterns). Các service phụ trợ như Redis hoặc database thường được thêm thủ công thông qua dashboard giao diện đồ họa của Railway và tự động kết nối qua biến môi trường.

###  Exercise 3.3: (Optional) GCP Cloud Run (15 phút)

```bash
cd ../production-cloud-run
```

**Yêu cầu:** GCP account (có free tier).

**Nhiệm vụ:** Đọc `cloudbuild.yaml` và `service.yaml`. Hiểu CI/CD pipeline.
- Trả lời:
  - **CI/CD Pipeline với Cloud Build (`cloudbuild.yaml`):**
    1. **test**: Chạy pytest để chạy unit tests cho codebase trước khi build.
    2. **build**: Build Docker image từ Dockerfile và đánh tag (`$COMMIT_SHA` và `latest`), sử dụng cache layer để tối ưu hóa thời gian build.
    3. **push**: Đẩy image vừa build lên Google Container Registry (GCR).
    4. **deploy**: Triển khai image đó lên Google Cloud Run ở region `asia-southeast1`, cấu hình tài nguyên (1 CPU, 512MB RAM), set biến môi trường, bảo mật key từ Google Secret Manager.
  - **Knative Service Definition (`service.yaml`):** Cấu hình khai báo cơ sở hạ tầng ở dạng code (IaC) cho Cloud Run. Cấu hình tự động scale từ tối thiểu 1 instance (minScale: "1" để tránh độ trễ cold start) đến tối đa 10 instances, đồng thời cấu hình healthcheck định kỳ qua livenessProbe (`/health`) và startupProbe (`/ready`).

###  Checkpoint 3

- [ ] Deploy thành công lên ít nhất 1 platform
- [ ] Có public URL hoạt động
- [ ] Hiểu cách set environment variables trên cloud
- [ ] Biết cách xem logs

---

## Part 4: API Security (40 phút)

###  Concepts

**Vấn đề:** Public URL = ai cũng gọi được = hết tiền OpenAI.

**Giải pháp:**
1. **Authentication** — Chỉ user hợp lệ mới gọi được
2. **Rate Limiting** — Giới hạn số request/phút
3. **Cost Guard** — Dừng khi vượt budget

###  Exercise 4.1: API Key authentication

```bash
cd ../../04-api-gateway/develop
```

**Nhiệm vụ:** Đọc `app.py` và trả lời:
- **API key được check ở đâu?**
  - Trả lời: API key được kiểm tra tại dependency `verify_api_key` (dòng 39), được gắn vào endpoint `/ask` thông qua `_key: str = Depends(verify_api_key)`. Nó đọc giá trị bí mật từ biến môi trường `AGENT_API_KEY`.
- **Điều gì xảy ra nếu sai key?**
  - Trả lời: Nếu thiếu API key trong header `X-API-Key`, hệ thống trả về `401 Unauthorized` kèm thông báo `"Missing API key."`. Nếu cung cấp sai key, hệ thống trả về `403 Forbidden` kèm thông báo `"Invalid API key."`.
- **Làm sao rotate key?**
  - Trả lời: Thay đổi giá trị biến môi trường `AGENT_API_KEY` trên dashboard quản trị của cloud platform (hoặc file `.env`), sau đó kích hoạt redeploy/restart service mà không cần thay đổi hay build lại mã nguồn.

Test:
```bash
python app.py

#  Không có key
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

#  Có key
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

###  Exercise 4.2: JWT authentication (Advanced)

```bash
cd ../production
```

**Nhiệm vụ:** 
1. Đọc `auth.py` — hiểu JWT flow
2. Lấy token:
```bash
python app.py

curl http://localhost:8000/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

3. Dùng token để gọi API:
```bash
TOKEN="<token_từ_bước_2>"
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

###  Exercise 4.3: Rate limiting

**Nhiệm vụ:** Đọc `rate_limiter.py` và trả lời:
- **Algorithm nào được dùng?**
  - Trả lời: Thuật toán **Sliding Window Counter** sử dụng một cấu trúc deque lưu trữ timestamp của các request gần nhất, liên tục loại bỏ các request đã quá thời gian trượt (60 giây) để kiểm tra số request hiện tại.
- **Limit là bao nhiêu requests/minute?**
  - Trả lời: Đối với user thường (`rate_limiter_user`) giới hạn là **10 requests/phút**. Đối với tài khoản admin (`rate_limiter_admin`) giới hạn là **100 requests/phút**.
- **Làm sao bypass limit cho admin?**
  - Trả lời: Bằng cách kiểm tra thuộc tính `role` của user sau khi decode JWT. Nếu `role == "admin"`, hệ thống sử dụng instance `rate_limiter_admin` có hạn mức cao hơn nhiều, hoặc có thể tùy biến bỏ qua không gọi hàm check của limiter.

Test:
```bash
# Gọi liên tục 20 lần
for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
```

Quan sát response khi hit limit.

###  Exercise 4.4: Cost guard

**Nhiệm vụ:** Đọc `cost_guard.py` và implement logic:

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.
    
    Logic:
    - Mỗi user có budget $10/tháng
    - Track spending trong Redis
    - Reset đầu tháng
    """
    # TODO: Implement
    pass
```

<details>
<summary> Solution</summary>

```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
```

</details>

###  Checkpoint 4

- [ ] Implement API key authentication
- [ ] Hiểu JWT flow
- [ ] Implement rate limiting
- [ ] Implement cost guard với Redis

---

## Part 5: Scaling & Reliability (40 phút)

###  Concepts

**Vấn đề:** 1 instance không đủ khi có nhiều users.

**Giải pháp:**
1. **Stateless design** — Không lưu state trong memory
2. **Health checks** — Platform biết khi nào restart
3. **Graceful shutdown** — Hoàn thành requests trước khi tắt
4. **Load balancing** — Phân tán traffic

###  Exercise 5.1: Health checks

```bash
cd ../../05-scaling-reliability/develop
```

**Nhiệm vụ:** Implement 2 endpoints:

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
    # TODO: Return 200 nếu process OK
    pass

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic không?"""
    # TODO: Check database connection, Redis, etc.
    # Return 200 nếu OK, 503 nếu chưa ready
    pass
```

<details>
<summary> Solution</summary>

```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        # Check Redis
        r.ping()
        # Check database
        db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )
```

</details>

###  Exercise 5.2: Graceful shutdown

**Nhiệm vụ:** Implement signal handler:

```python
import signal
import sys

def shutdown_handler(signum, frame):
    """Handle SIGTERM from container orchestrator"""
    # TODO:
    # 1. Stop accepting new requests
    # 2. Finish current requests
    # 3. Close connections
    # 4. Exit
    pass

signal.signal(signal.SIGTERM, shutdown_handler)
```

Test:
```bash
python app.py &
PID=$!

# Gửi request
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
kill -TERM $PID

# Quan sát: Request có hoàn thành không?
```

###  Exercise 5.3: Stateless design

```bash
cd ../production
```

**Nhiệm vụ:** Refactor code để stateless.

**Anti-pattern:**
```python
#  State trong memory
conversation_history = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
    # ...
```

**Correct:**
```python
#  State trong Redis
@app.post("/ask")
def ask(user_id: str, question: str):
    history = r.lrange(f"history:{user_id}", 0, -1)
    # ...
```

Tại sao? Vì khi scale ra nhiều instances, mỗi instance có memory riêng.

###  Exercise 5.4: Load balancing

**Nhiệm vụ:** Chạy stack với Nginx load balancer:

```bash
docker compose up --scale agent=3
```

Quan sát:
- 3 agent instances được start
- Nginx phân tán requests
- Nếu 1 instance die, traffic chuyển sang instances khác

Test:
```bash
# Gọi 10 requests
for i in {1..10}; do
  curl http://localhost/ask -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
done

# Check logs — requests được phân tán
docker compose logs agent
```

###  Exercise 5.5: Test stateless

```bash
python test_stateless.py
```

Script này:
1. Gọi API để tạo conversation
2. Kill random instance
3. Gọi tiếp — conversation vẫn còn không?

###  Checkpoint 5

- [ ] Implement health và readiness checks
- [ ] Implement graceful shutdown
- [ ] Refactor code thành stateless
- [ ] Hiểu load balancing với Nginx
- [ ] Test stateless design

---

## Part 6: Final Project (60 phút)

###  Objective

Build một production-ready AI agent từ đầu, kết hợp TẤT CẢ concepts đã học.

###  Requirements

**Functional:**
- [ ] Agent trả lời câu hỏi qua REST API
- [ ] Support conversation history
- [ ] Streaming responses (optional)

**Non-functional:**
- [ ] Dockerized với multi-stage build
- [ ] Config từ environment variables
- [ ] API key authentication
- [ ] Rate limiting (10 req/min per user)
- [ ] Cost guard ($10/month per user)
- [ ] Health check endpoint
- [ ] Readiness check endpoint
- [ ] Graceful shutdown
- [ ] Stateless design (state trong Redis)
- [ ] Structured JSON logging
- [ ] Deploy lên Railway hoặc Render
- [ ] Public URL hoạt động

### 🏗 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐
   │Agent1│  │Agent2│  │Agent3│
   └───┬──┘  └───┬──┘  └───┬──┘
       │         │         │
       └─────────┴─────────┘
                 │
                 ▼
           ┌──────────┐
           │  Redis   │
           └──────────┘
```

###  Step-by-step

#### Step 1: Project setup (5 phút)

```bash
mkdir my-production-agent
cd my-production-agent

# Tạo structure
mkdir -p app
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/auth.py
touch app/rate_limiter.py
touch app/cost_guard.py
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch .env.example
touch .dockerignore
```

#### Step 2: Config management (10 phút)

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # TODO: Define all config
    # - PORT
    # - REDIS_URL
    # - AGENT_API_KEY
    # - LOG_LEVEL
    # - RATE_LIMIT_PER_MINUTE
    # - MONTHLY_BUDGET_USD
    pass

settings = Settings()
```

#### Step 3: Main application (15 phút)

**File:** `app/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

app = FastAPI()

@app.get("/health")
def health():
    # TODO
    pass

@app.get("/ready")
def ready():
    # TODO: Check Redis connection
    pass

@app.post("/ask")
def ask(
    question: str,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    # TODO: 
    # 1. Get conversation history from Redis
    # 2. Call LLM
    # 3. Save to Redis
    # 4. Return response
    pass
```

#### Step 4: Authentication (5 phút)

**File:** `app/auth.py`

```python
from fastapi import Header, HTTPException

def verify_api_key(x_api_key: str = Header(...)):
    # TODO: Verify against settings.AGENT_API_KEY
    # Return user_id if valid
    # Raise HTTPException(401) if invalid
    pass
```

#### Step 5: Rate limiting (10 phút)

**File:** `app/rate_limiter.py`

```python
import redis
from fastapi import HTTPException

r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str):
    # TODO: Implement sliding window
    # Raise HTTPException(429) if exceeded
    pass
```

#### Step 6: Cost guard (10 phút)

**File:** `app/cost_guard.py`

```python
def check_budget(user_id: str):
    # TODO: Check monthly spending
    # Raise HTTPException(402) if exceeded
    pass
```

#### Step 7: Dockerfile (5 phút)

```dockerfile
# TODO: Multi-stage build
# Stage 1: Builder
# Stage 2: Runtime
```

#### Step 8: Docker Compose (5 phút)

```yaml
# TODO: Define services
# - agent (scale to 3)
# - redis
# - nginx (load balancer)
```

#### Step 9: Test locally (5 phút)

```bash
docker compose up --scale agent=3

# Test all endpoints
curl http://localhost/health
curl http://localhost/ready
curl -H "X-API-Key: secret" http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
```

#### Step 10: Deploy (10 phút)

```bash
# Railway
railway init
railway variables set REDIS_URL=...
railway variables set AGENT_API_KEY=...
railway up

# Hoặc Render
# Push lên GitHub → Connect Render → Deploy
```

###  Validation

Chạy script kiểm tra:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Script sẽ kiểm tra:
-  Dockerfile exists và valid
-  Multi-stage build
-  .dockerignore exists
-  Health endpoint returns 200
-  Readiness endpoint returns 200
-  Auth required (401 without key)
-  Rate limiting works (429 after limit)
-  Cost guard works (402 when exceeded)
-  Graceful shutdown (SIGTERM handled)
-  Stateless (state trong Redis, không trong memory)
-  Structured logging (JSON format)

###  Grading Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Functionality** | 20 | Agent hoạt động đúng |
| **Docker** | 15 | Multi-stage, optimized |
| **Security** | 20 | Auth + rate limit + cost guard |
| **Reliability** | 20 | Health checks + graceful shutdown |
| **Scalability** | 15 | Stateless + load balanced |
| **Deployment** | 10 | Public URL hoạt động |
| **Total** | 100 | |

---

##  Hoàn Thành!

Bạn đã:
-  Hiểu sự khác biệt dev vs production
-  Containerize app với Docker
-  Deploy lên cloud platform
-  Bảo mật API
-  Thiết kế hệ thống scalable và reliable

###  Next Steps

1. **Monitoring:** Thêm Prometheus + Grafana
2. **CI/CD:** GitHub Actions auto-deploy
3. **Advanced scaling:** Kubernetes
4. **Observability:** Distributed tracing với OpenTelemetry
5. **Cost optimization:** Spot instances, auto-scaling

###  Resources

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

##  Q&A

**Q: Tôi không có credit card, có thể deploy không?**  
A: Có! Railway cho $5 credit, Render có 750h free tier.

**Q: Mock LLM khác gì với OpenAI thật?**  
A: Mock trả về canned responses, không gọi API. Để dùng OpenAI thật, set `OPENAI_API_KEY` trong env.

**Q: Làm sao debug khi container fail?**  
A: `docker logs <container_id>` hoặc `docker exec -it <container_id> /bin/sh`

**Q: Redis data mất khi restart?**  
A: Dùng volume: `volumes: - redis-data:/data` trong docker-compose.

**Q: Làm sao scale trên Railway/Render?**  
A: Railway: `railway scale <replicas>`. Render: Dashboard → Settings → Instances.

---

**Happy Deploying! **
