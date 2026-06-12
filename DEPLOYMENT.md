# Deployment Information

## Public URL
https://day12-agent-production.up.railway.app

## Platform
Railway (hoặc Render)

## Test Commands

### Health Check
```bash
curl https://day12-agent-production.up.railway.app/health
# Expected: {"status": "ok", "uptime_seconds": ..., "version": "1.0.0"}
```

### Readiness Check
```bash
curl https://day12-agent-production.up.railway.app/ready
# Expected: {"ready": true}
```

### API Test (without authentication - Expected 401)
```bash
curl -X POST https://day12-agent-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected response: {"detail": "Invalid or missing API key. Include header: X-API-Key: <key>"}
```

### API Test (with authentication - Expected 200)
```bash
curl -X POST https://day12-agent-production.up.railway.app/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is deployment?"}'
# Expected response: {"question": "What is deployment?", "answer": "...", "model": "gpt-4o-mini", "timestamp": "..."}
```

## Environment Variables Set
- `PORT` = `8000`
- `ENVIRONMENT` = `production`
- `AGENT_API_KEY` = `dev-key-change-me`
- `REDIS_URL` = `redis://redis:6379/0`
- `DAILY_BUDGET_USD` = `5.0`
- `RATE_LIMIT_PER_MINUTE` = `20`
