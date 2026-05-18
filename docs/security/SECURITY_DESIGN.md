# AI Daily Brief v4 安全设计文档

**版本**: 1.0
**日期**: 2026-05-19
**状态**: 初稿

---

## 1. 安全威胁分析

### 1.1 系统架构概览

```
                    Internet
                        |
                    Nginx (HTTPS)
                        |
                    FastAPI App
                   /    |    \
         SQLite    LanceDB    GLM API
         (本地)    (本地)     (外部)
```

### 1.2 威胁模型 (STRIDE)

| 威胁类型 | 风险描述 | 风险等级 | 影响组件 |
|---------|---------|---------|---------|
| **Spoofing (欺骗)** | 攻击者伪造请求访问API | 高 | FastAPI端点 |
| **Tampering (篡改)** | 数据库内容被恶意修改 | 中 | SQLite/LanceDB |
| **Repudiation (抵赖)** | 无审计日志难以追溯操作 | 中 | 全系统 |
| **Information Disclosure (信息泄露)** | API密钥泄露、敏感数据暴露 | 高 | GLM_API_KEY、数据库 |
| **Denial of Service (拒绝服务)** | API被恶意请求耗尽资源 | 高 | FastAPI端点 |
| **Elevation of Privilege (权限提升)** | 容器逃逸攻击 | 中 | Docker容器 |

### 1.3 关键资产清单

| 资产 | 类型 | 敏感度 | 存储位置 |
|-----|-----|-------|---------|
| GLM_API_KEY | API密钥 | 极高 | 环境变量 |
| SQLite数据库 | 数据 | 中 | `data/metadata.db` |
| LanceDB向量库 | 数据 | 中 | `data/lancedb/` |
| Brief内容 | 数据 | 低 | 数据库 |
| 用户访问日志 | 日志 | 中 | 未实现 |

---

## 2. API安全措施

### 2.1 认证机制

**当前状态**: 无认证 (高风险)

**实施方案**:

#### 2.1.1 API Key认证

```python
# app/middleware/auth.py
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
import os
import secrets

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 生成安全的API密钥
def generate_api_key() -> str:
    return secrets.token_urlsafe(32)

# 验证API密钥
async def verify_api_key(api_key: str = Security(api_key_header)):
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    if api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key
```

#### 2.1.2 应用到路由

```python
# app/routes/brief.py (修改)
from app.middleware.auth import verify_api_key

@router.post("/generate", dependencies=[Depends(verify_api_key)])
async def generate_brief(background_tasks: BackgroundTasks, request: BriefRequest = None):
    # ... 现有代码
```

#### 2.1.3 公开端点配置

```python
# 健康检查端点保持公开
@router.get("/health")  # 无需认证
async def health_check():
    ...

# 数据端点需认证
@router.get("/latest", dependencies=[Depends(verify_api_key)])
async def get_latest_brief():
    ...
```

### 2.2 速率限制

**当前状态**: 无限制 (高风险)

**实施方案**:

#### 2.2.1 基于IP的限流中间件

```python
# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from collections import defaultdict
import time
import asyncio

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.rpm = requests_per_minute
        self.burst = burst
        self.requests = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, client_ip: str) -> bool:
        async with self._lock:
            now = time.time()
            window_start = now - 60

            # 清理过期记录
            self.requests[client_ip] = [
                t for t in self.requests[client_ip] if t > window_start
            ]

            # 检查限流
            if len(self.requests[client_ip]) >= self.rpm:
                return False

            # 突发检查 (1秒内超过burst次)
            burst_window = now - 1
            burst_count = sum(1 for t in self.requests[client_ip] if t > burst_window)
            if burst_count >= self.burst:
                return False

            self.requests[client_ip].append(now)
            return True

# 全局限流器
rate_limiter = RateLimiter(requests_per_minute=60, burst=10)

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host

    if not await rate_limiter.check(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": "60"}
        )

    return await call_next(request)
```

#### 2.2.2 集成到应用

```python
# app/main.py (添加)
from app.middleware.rate_limit import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)
```

### 2.3 输入验证

**当前状态**: 基础Pydantic验证

**实施方案**:

#### 2.3.1 增强输入验证

```python
# app/schemas/validators.py
from pydantic import BaseModel, field_validator, Field
import re
from datetime import datetime

class BriefRequest(BaseModel):
    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            # 验证日期格式和范围
            date = datetime.strptime(v, "%Y-%m-%d")
            if date > datetime.now():
                raise ValueError("Date cannot be in the future")
            if date.year < 2020:
                raise ValueError("Date cannot be before 2020")
        except ValueError as e:
            raise ValueError(f"Invalid date: {e}")
        return v

class PaginationParams(BaseModel):
    limit: int = Field(30, ge=1, le=100)  # 限制1-100
    offset: int = Field(0, ge=0)
```

#### 2.3.2 SQL注入防护

```python
# 当前已使用参数化查询 (安全)
cursor = conn.execute("SELECT * FROM briefs WHERE date = ?", (date,))

# 禁止字符串拼接 (危险)
# cursor.execute(f"SELECT * FROM briefs WHERE date = '{date}'")  # 绝对禁止
```

#### 2.3.3 XSS防护

```python
# app/utils/sanitize.py
import html
import re

def sanitize_html(text: str) -> str:
    """转义HTML特殊字符"""
    return html.escape(text)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """清理用户输入"""
    if not text:
        return ""
    # 移除控制字符
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    # 限制长度
    return text[:max_length].strip()
```

---

## 3. 数据安全

### 3.1 加密措施

#### 3.1.1 传输加密

```nginx
# /etc/nginx/sites-available/ai-brief
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # TLS配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 强加密套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3.1.2 敏感数据存储加密

```python
# 对于未来可能的敏感数据存储
# app/utils/crypto.py
from cryptography.fernet import Fernet
import os

class DataEncryptor:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key().decode()
            print(f"Generated new encryption key: {key}")
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(encrypted_data).decode()
```

### 3.2 备份策略

#### 3.2.1 自动备份脚本

```bash
#!/bin/bash
# /usr/local/bin/backup-ai-brief.sh

BACKUP_DIR="/var/backups/ai-brief"
DATA_DIR="/path/to/ai-brief-site/data"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 日期标记
DATE=$(date +%Y%m%d_%H%M%S)

# SQLite备份 (在线备份)
sqlite3 "$DATA_DIR/metadata.db" ".backup '$BACKUP_DIR/metadata_$DATE.db'"

# LanceDB备份
tar -czf "$BACKUP_DIR/lancedb_$DATE.tar.gz" -C "$DATA_DIR" lancedb/

# 加密备份 (可选)
# openssl enc -aes-256-cbc -salt -pbkdf2 -in "$BACKUP_DIR/metadata_$DATE.db" \
#     -out "$BACKUP_DIR/metadata_$DATE.db.enc" -pass pass:$BACKUP_PASSWORD

# 清理过期备份
find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

#### 3.2.2 Cron定时任务

```cron
# /etc/cron.d/ai-brief-backup
# 每日凌晨3点备份
0 3 * * * root /usr/local/bin/backup-ai-brief.sh >> /var/log/ai-brief-backup.log 2>&1
```

### 3.3 访问控制

#### 3.3.1 文件权限设置

```bash
# 数据目录权限
chmod 750 /path/to/ai-brief-site/data
chown -R ai-brief:ai-brief /path/to/ai-brief-site/data

# SQLite数据库权限
chmod 640 /path/to/ai-brief-site/data/metadata.db

# 禁止其他用户访问
chmod 700 /path/to/ai-brief-site/data/lancedb
```

#### 3.3.2 Docker用户非root运行

```dockerfile
# Dockerfile (修改)
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r ai-brief && useradd -r -g ai-brief ai-brief

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用
COPY --chown=ai-brief:ai-brief app/ ./app/
COPY --chown=ai-brief:ai-brief config.py .
COPY --chown=ai-brief:ai-brief static/ ./static/
COPY --chown=ai-brief:ai-brief templates/ ./templates/

# 创建数据目录
RUN mkdir -p /app/data/lancedb && chown -R ai-brief:ai-brief /app/data

# 切换到非root用户
USER ai-brief

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. 密钥管理方案

### 4.1 当前状态分析

```python
# config.py (当前实现)
GLM_API_KEY = os.getenv("GLM_API_KEY", "")  # 正确：从环境变量读取
```

**问题**:
1. 空字符串默认值可能导致静默失败
2. 无密钥轮换机制
3. 无密钥泄露检测

### 4.2 密钥管理最佳实践

#### 4.2.1 安全启动检查

```python
# app/middleware/startup_check.py
import os
import sys
from pathlib import Path

CRITICAL_ENV_VARS = ["GLM_API_KEY"]

def check_critical_env_vars():
    """启动时检查关键环境变量"""
    missing = []
    for var in CRITICAL_ENV_VARS:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"ERROR: Missing critical environment variables: {', '.join(missing)}")
        print("Please set these variables before starting the application.")
        sys.exit(1)

    # 检查密钥强度
    api_key = os.getenv("GLM_API_KEY", "")
    if len(api_key) < 32:
        print(f"WARNING: GLM_API_KEY appears to be weak (length: {len(api_key)})")

def check_file_permissions():
    """检查敏感文件权限"""
    data_dir = Path(__file__).parent.parent / "data"
    if data_dir.exists():
        mode = data_dir.stat().st_mode
        if mode & 0o077:  # 检查其他用户是否有权限
            print(f"WARNING: data directory has overly permissive permissions: {oct(mode)}")
```

#### 4.2.2 环境变量管理

```bash
# .env (不要提交到版本控制)
GLM_API_KEY=your-secure-api-key-here
VALID_API_KEYS=client-key-1,client-key-2
DEBUG=false
LOG_LEVEL=INFO

# 可选：加密密钥
ENCRYPTION_KEY=your-fernet-key-here
```

```bash
# .env.example (提交到版本控制作为模板)
GLM_API_KEY=your-glm-api-key-here
VALID_API_KEYS=comma-separated-client-keys
DEBUG=false
LOG_LEVEL=INFO
```

#### 4.2.3 Docker环境配置

```yaml
# docker-compose.yml (修改)
services:
  ai-brief-app:
    build: .
    container_name: ai-brief-app
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8000"
    volumes:
      - ./data:/app/data
    environment:
      - API_PORT=8000
      - DEBUG=false
    env_file:
      - .env  # 从.env文件加载敏感变量
    secrets:
      - glm_api_key
    # ... 其他配置

secrets:
  glm_api_key:
    file: ./secrets/glm_api_key.txt
```

#### 4.2.4 密钥轮换流程

```
密钥轮换步骤：
1. 生成新密钥 (在GLM平台)
2. 更新环境变量/密钥文件
3. 重启服务 (滚动重启，零停机)
4. 监控API调用是否正常
5. 确认后撤销旧密钥
```

### 4.3 密钥泄露应急响应

#### 4.3.1 泄露检测

```python
# app/middleware/secret_detection.py
import re
import os

# 已知密钥模式
SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{48,}",  # OpenAI风格
    r"xox[baprs]-[a-zA-Z0-9-]+",  # Slack风格
    r"glme-[a-zA-Z0-9]+",  # GLM风格 (假设)
]

def scan_for_secrets_in_logs(log_content: str) -> list:
    """扫描日志中的密钥泄露"""
    found = []
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, log_content)
        found.extend(matches)
    return found

def mask_sensitive_data(text: str) -> str:
    """在日志中遮蔽敏感信息"""
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "***REDACTED***", text)
    # 遮蔽API密钥
    api_key = os.getenv("GLM_API_KEY", "")
    if api_key and api_key in text:
        text = text.replace(api_key, "***API_KEY_REDACTED***")
    return text
```

#### 4.3.2 应急响应流程

```markdown
## 密钥泄露应急响应流程

### 发现阶段
1. 收到泄露警报或发现泄露事件
2. 立即记录发现时间和影响范围
3. 通知安全团队

### 抑制阶段
1. 立即撤销泄露的密钥
2. 生成新密钥
3. 更新所有使用该密钥的服务

### 恢复阶段
1. 部署新密钥
2. 验证服务正常
3. 检查是否有未授权使用

### 事后分析
1. 分析泄露原因
2. 更新安全措施
3. 编写事故报告
```

---

## 5. 网络安全

### 5.1 防火墙配置

#### 5.1.1 iptables规则

```bash
#!/bin/bash
# /usr/local/bin/setup-firewall.sh

# 清空现有规则
iptables -F
iptables -X

# 默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许回环
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许SSH (限制速率)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 -DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 允许HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许本地API端口 (仅localhost)
iptables -A INPUT -s 127.0.0.1 -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# 允许ICMP (限制)
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 4 -j ACCEPT

# 记录丢弃的数据包
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables DROP: " --log-level 4

# 保存规则
iptables-save > /etc/iptables/rules.v4

echo "Firewall configured successfully"
```

#### 5.1.2 UFW简化配置

```bash
# 使用UFW (更简单)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 5.2 Nginx安全配置

```nginx
# /etc/nginx/nginx.conf (安全相关部分)

# 隐藏版本号
server_tokens off;

# 安全头
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# 限制请求大小
client_max_body_size 1M;

# 限制请求方法和路径
# /etc/nginx/sites-available/ai-brief

# 速率限制 (Nginx层)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

    # API速率限制
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn conn_limit 10;

        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查端点 (允许更高频率)
    location /health {
        limit_req zone=api_limit burst=50 nodelay;
        proxy_pass http://127.0.0.1:8080;
    }

    # 静态文件
    location /static/ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # 禁止访问敏感路径
    location ~ /\.(?!well-known) {
        deny all;
    }

    location ~ /\.(env|git|htaccess) {
        deny all;
    }

    # 禁止直接访问数据目录
    location ~* ^/(data|lancedb)/ {
        deny all;
        return 404;
    }
}
```

### 5.3 Docker网络安全

```yaml
# docker-compose.yml (网络隔离)
version: '3.8'

services:
  ai-brief-app:
    build: .
    container_name: ai-brief-app
    restart: unless-stopped
    # 不暴露到外部，仅通过nginx代理
    expose:
      - "8000"
    volumes:
      - ./data:/app/data:rw
    environment:
      - API_PORT=8000
      - DEBUG=false
    env_file:
      - .env
    networks:
      - internal
    security_opt:
      - no-new-privileges:true
    read_only: false  # 数据目录需要写权限
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
      - NET_BIND_SERVICE

  nginx:
    image: nginx:alpine
    container_name: ai-brief-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - internal
    depends_on:
      - ai-brief-app

networks:
  internal:
    driver: bridge
    internal: true  # 内部网络，不对外
```

---

## 6. 安全监控与审计

### 6.1 日志记录

#### 6.1.1 应用日志配置

```python
# app/middleware/logging.py
import logging
import time
import json
from fastapi import Request, Response
from datetime import datetime
from pathlib import Path

# 日志配置
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 结构化日志
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 文件处理器
        fh = logging.FileHandler(LOG_DIR / "app.log")
        fh.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(fh)

        # 安全审计日志 (单独文件)
        self.audit_logger = logging.getLogger(f"{name}.audit")
        audit_fh = logging.FileHandler(LOG_DIR / "audit.log")
        audit_fh.setFormatter(logging.Formatter('%(message)s'))
        self.audit_logger.addHandler(audit_fh)

    def log_request(self, request: Request, response: Response, duration_ms: float):
        """记录请求日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        self.logger.info(json.dumps(log_entry))

    def log_security_event(self, event_type: str, details: dict):
        """记录安全事件"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **details
        }
        self.audit_logger.warning(json.dumps(entry))

logger = StructuredLogger("ai-brief")

# 日志中间件
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    await logger.log_request(request, response, duration_ms)

    # 记录可疑请求
    if response.status_code == 401:
        logger.log_security_event("auth_failure", {
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        })
    elif response.status_code == 429:
        logger.log_security_event("rate_limit_hit", {
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        })

    return response
```

#### 6.1.2 审计日志格式

```json
// audit.log 示例
{
    "timestamp": "2026-05-19T03:45:22.123456",
    "event_type": "auth_success",
    "user_id": "api-client-1",
    "client_ip": "192.168.1.100",
    "path": "/api/brief/generate",
    "method": "POST"
}

{
    "timestamp": "2026-05-19T03:46:00.456789",
    "event_type": "api_key_rotated",
    "operator": "admin",
    "old_key_hash": "sha256:abc123...",
    "new_key_hash": "sha256:def456..."
}

{
    "timestamp": "2026-05-19T03:50:15.789012",
    "event_type": "suspicious_activity",
    "client_ip": "10.0.0.50",
    "reason": "Multiple failed auth attempts",
    "details": {
        "failed_attempts": 5,
        "time_window_seconds": 60
    }
}
```

### 6.2 安全监控指标

#### 6.2.1 Prometheus指标

```python
# app/metrics/security_metrics.py
from prometheus_client import Counter, Gauge, Histogram

# 认证相关
auth_attempts = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['status']  # success, failure
)

auth_failures = Counter(
    'auth_failures_total',
    'Total authentication failures',
    ['reason']  # invalid_key, expired_key, rate_limited
)

# 请求相关
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# 安全事件
security_events = Counter(
    'security_events_total',
    'Total security events',
    ['event_type']  # auth_failure, rate_limit, suspicious_request
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

blocked_ips = Gauge(
    'blocked_ips_total',
    'Number of blocked IP addresses'
)
```

#### 6.2.2 告警规则

```yaml
# alerting_rules.yml (Prometheus)
groups:
  - name: security_alerts
    rules:
      - alert: HighAuthFailureRate
        expr: rate(auth_failures_total[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"
          description: "{{ $value }} auth failures per second"

      - alert: PossibleBruteForce
        expr: increase(auth_failures_total[1m]) > 20
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Possible brute force attack"
          description: "{{ $value }} auth failures in 1 minute"

      - alert: SuspiciousIPBlocked
        expr: increase(blocked_ips_total[5m]) > 0
        for: 0s
        labels:
          severity: info
        annotations:
          summary: "IP address blocked"
          description: "A suspicious IP has been blocked"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High 5xx error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"
```

### 6.3 安全事件响应

#### 6.3.1 自动封禁机制

```python
# app/middleware/ip_blocker.py
import time
from collections import defaultdict
from fastapi import Request, HTTPException
import asyncio

class IPBlocker:
    def __init__(
        self,
        max_failed_attempts: int = 5,
        block_duration_seconds: int = 3600,
        window_seconds: int = 300
    ):
        self.max_failed = max_failed_attempts
        self.block_duration = block_duration_seconds
        self.window = window_seconds

        self.failed_attempts = defaultdict(list)  # IP -> [timestamps]
        self.blocked_ips = {}  # IP -> block_until_timestamp
        self._lock = asyncio.Lock()

    async def is_blocked(self, ip: str) -> bool:
        async with self._lock:
            if ip in self.blocked_ips:
                if time.time() < self.blocked_ips[ip]:
                    return True
                else:
                    del self.blocked_ips[ip]
            return False

    async def record_failure(self, ip: str):
        async with self._lock:
            now = time.time()
            window_start = now - self.window

            # 清理过期记录
            self.failed_attempts[ip] = [
                t for t in self.failed_attempts[ip] if t > window_start
            ]

            # 添加新失败
            self.failed_attempts[ip].append(now)

            # 检查是否需要封禁
            if len(self.failed_attempts[ip]) >= self.max_failed:
                self.blocked_ips[ip] = now + self.block_duration
                del self.failed_attempts[ip]
                # 记录安全事件
                from app.middleware.logging import logger
                logger.log_security_event("ip_blocked", {
                    "client_ip": ip,
                    "reason": "excessive_auth_failures",
                    "duration_seconds": self.block_duration
                })

    async def check_and_block(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"

        if await self.is_blocked(client_ip):
            raise HTTPException(
                status_code=403,
                detail="IP temporarily blocked due to suspicious activity"
            )

# 全局实例
ip_blocker = IPBlocker()
```

#### 6.3.2 安全事件处理流程

```markdown
## 安全事件处理流程

### 级别定义
- **P0 Critical**: 数据泄露、系统入侵、服务完全不可用
- **P1 High**: 认证绕过、DDoS攻击、API密钥泄露
- **P2 Medium**: 异常访问模式、单点故障
- **P3 Low**: 性能下降、非关键告警

### 响应时间
- P0: 15分钟内响应
- P1: 1小时内响应
- P2: 4小时内响应
- P3: 24小时内响应

### 处理步骤
1. **确认**: 验证警报真实性
2. **抑制**: 阻止攻击继续
3. **分析**: 确定攻击范围和影响
4. **修复**: 恢复服务，修补漏洞
5. **复盘**: 编写事故报告，改进措施
```

---

## 7. 安全检查清单

### 7.1 部署前检查清单

#### 7.1.1 环境配置

- [ ] 所有密钥通过环境变量或密钥管理服务注入
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 生产环境 `DEBUG=false`
- [ ] 日志级别设置为 `INFO` 或更高
- [ ] 敏感文件权限正确 (600/640)

#### 7.1.2 网络安全

- [ ] HTTPS 证书有效且配置正确
- [ ] 防火墙规则已配置
- [ ] 仅必要端口对外开放
- [ ] API端口不直接暴露公网
- [ ] Nginx安全头已配置

#### 7.1.3 应用安全

- [ ] API认证已启用
- [ ] 速率限制已启用
- [ ] 输入验证已实现
- [ ] 错误信息不泄露敏感数据
- [ ] SQL注入防护已验证

#### 7.1.4 容器安全

- [ ] 容器以非root用户运行
- [ ] 容器能力已限制 (`cap_drop: ALL`)
- [ ] 只读文件系统 (除必要目录)
- [ ] 无特权容器
- [ ] 镜像来自可信源

### 7.2 运维检查清单

#### 7.2.1 日常检查 (每日)

- [ ] 检查安全告警
- [ ] 检查异常日志
- [ ] 验证备份完整性
- [ ] 确认服务健康状态

#### 7.2.2 周期检查 (每周)

- [ ] 审查访问日志
- [ ] 检查依赖安全更新
- [ ] 验证备份恢复流程
- [ ] 检查证书有效期

#### 7.2.3 定期检查 (每月)

- [ ] 安全漏洞扫描
- [ ] 密钥轮换评估
- [ ] 访问权限审查
- [ ] 应急预案演练

### 7.3 代码审查检查清单

#### 7.3.1 认证与授权

- [ ] 所有敏感端点都需要认证
- [ ] API密钥验证逻辑正确
- [ ] 权限检查无遗漏

#### 7.3.2 输入处理

- [ ] 所有用户输入都经过验证
- [ ] 无字符串拼接SQL
- [ ] 输出正确编码/转义
- [ ] 文件上传有限制

#### 7.3.3 敏感数据处理

- [ ] 密钥不在日志中出现
- [ ] 敏感数据正确加密存储
- [ ] 响应不含敏感信息
- [ ] 错误消息不泄露内部信息

#### 7.3.4 依赖管理

- [ ] 无已知漏洞依赖
- [ ] 依赖版本固定
- [ ] 最小依赖原则

### 7.4 事故响应检查清单

#### 7.4.1 发现阶段

- [ ] 记录发现时间
- [ ] 评估影响范围
- [ ] 确定事件级别
- [ ] 通知相关人员

#### 7.4.2 抑制阶段

- [ ] 隔离受影响系统
- [ ] 撤销泄露密钥
- [ ] 封禁恶意IP
- [ ] 保留证据

#### 7.4.3 恢复阶段

- [ ] 应用安全补丁
- [ ] 部署新密钥
- [ ] 验证服务正常
- [ ] 增强监控

#### 7.4.4 复盘阶段

- [ ] 编写事故报告
- [ ] 分析根本原因
- [ ] 制定改进措施
- [ ] 更新文档和流程

---

## 附录

### A. 相关配置文件路径

| 文件 | 路径 | 用途 |
|-----|-----|-----|
| 应用配置 | `config.py` | 基础配置 |
| 环境变量 | `.env` | 敏感配置 |
| Docker配置 | `docker-compose.yml` | 容器编排 |
| Nginx配置 | `/etc/nginx/nginx.conf` | 反向代理 |
| 防火墙规则 | `/etc/iptables/rules.v4` | 网络安全 |

### B. 密钥管理命令

```bash
# 生成安全的API密钥
openssl rand -base64 32

# 生成Fernet加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 检查密钥强度
python -c "import secrets; print(f'Entropy: {len(secrets.token_bytes(32)) * 8} bits')"

# Docker密钥管理
echo "your-api-key" | docker secret create glm_api_key -
docker secret inspect glm_api_key --pretty
docker secret rm glm_api_key
```

### C. 安全扫描工具

```bash
# 依赖漏洞扫描
pip install safety
safety check -r requirements.txt

# 代码安全扫描
pip install bandit
bandit -r app/

# 容器镜像扫描
docker scout cves ai-brief-app:latest

# SSL证书检查
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### D. 应急联系方式

| 角色 | 联系方式 | 响应时间 |
|-----|---------|---------|
| 安全负责人 | security@example.com | 即时 |
| 运维负责人 | ops@example.com | 即时 |
| 开发负责人 | dev@example.com | 1小时 |
| 值班人员 | oncall@example.com | 15分钟 |

---

**文档维护**:
- 每季度审查一次
- 发生安全事件后及时更新
- 重大架构变更后更新