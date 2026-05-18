# AI Daily Brief v4 - SRE 运维文档

## 目录
1. [SLO 定义](#1-slo-定义)
2. [监控指标与告警配置](#2-监控指标与告警配置)
3. [部署流程](#3-部署流程)
4. [故障排查手册](#4-故障排查手册)
5. [容灾恢复方案](#5-容灾恢复方案)
6. [运维检查清单](#6-运维检查清单)
7. [自动化任务](#7-自动化任务)

---

## 1. SLO 定义

### 1.1 服务等级目标 (SLO)

| 指标 | 目标值 | 测量方法 | 代码配置 |
|------|--------|----------|----------|
| **可用性** | 99.5% | `/health` 端点成功率 | `config.py` |
| **延迟 (P95)** | < 2000ms | 请求响应时间 | `SLO_LATENCY_THRESHOLD_MS = 2000` |
| **错误率** | < 1% | 4xx/5xx 响应占比 | `SLO_ERROR_RATE_THRESHOLD = 0.01` |

### 1.2 服务等级协议 (SLA)

- 每日简报生成：北京时间 08:00 前完成
- 数据源可用性：至少 80% 数据源可访问
- 历史简报可访问性：30 天内简报 100% 可查询

### 1.3 错误预算

```
月度错误预算 = (1 - 99.5%) x 30天 x 24小时 x 60分钟 = 216 分钟/月
```

错误预算消耗追踪：
- 查看指标：`curl http://localhost:8080/metrics | grep slo_met`
- 当 `slo_met = 0` 时，错误预算已耗尽

---

## 2. 监控指标与告警配置

### 2.1 健康检查端点

| 端点 | 用途 | 响应示例 |
|------|------|----------|
| `/health` | 存活探针 (Liveness) | `{"status": "healthy", "components": {...}}` |
| `/ready` | 就绪探针 (Readiness) | `{"status": "ready"}` |
| `/metrics` | Prometheus 指标 | Prometheus 文本格式 |

### 2.2 Prometheus 指标

```bash
# 查看实时指标
curl http://localhost:8080/metrics
```

关键指标：
```prometheus
# 总请求数
total_requests

# 错误请求数 (4xx/5xx)
error_requests

# 当前错误率
error_rate

# 平均延迟 (ms)
avg_latency_ms

# SLO 是否达标
slo_met
```

### 2.3 Prometheus 抓取配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-brief'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 2.4 告警规则

```yaml
# alerts.yml
groups:
  - name: ai-brief-alerts
    rules:
      # 服务不可用
      - alert: AIBriefDown
        expr: up{job="ai-brief"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AI Daily Brief 服务不可用"
          description: "服务已宕机超过 1 分钟"

      # 错误率过高
      - alert: AIBriefHighErrorRate
        expr: error_rate > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AI Daily Brief 错误率过高"
          description: "错误率 {{ $value | printf \"%.2f%%\" }} 超过 1% 阈值"

      # 延迟过高
      - alert: AIBriefHighLatency
        expr: avg_latency_ms > 2000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AI Daily Brief 延迟过高"
          description: "平均延迟 {{ $value | printf \"%.0fms\" }} 超过 2000ms 阈值"

      # SLO 违规
      - alert: AIBriefSLOViolation
        expr: slo_met == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "AI Daily Brief SLO 违规"
          description: "服务未达到 SLO 目标，请立即排查"

      # 数据库健康
      - alert: AIBriefDatabaseIssue
        expr: increase(error_requests[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "AI Daily Brief 数据库可能存在问题"
          description: "5 分钟内错误请求数显著增加"
```

### 2.5 Grafana Dashboard

推荐面板：
- **服务概览**: 总请求数、错误率、平均延迟
- **SLO 状态**: 错误预算剩余、SLO 达成率
- **数据源状态**: RSS/arXiv/GitHub 抓取成功率
- **数据库**: SQLite 大小、LanceDB 状态

---

## 3. 部署流程

### 3.1 环境信息

| 项目 | 值 |
|------|-----|
| VPS 地址 | tomabc.com:60022 |
| 容器名称 | ai-brief-app |
| 端口映射 | 127.0.0.1:8080 -> 8000 |
| 数据目录 | `./data` (SQLite + LanceDB) |

### 3.2 首次部署

```bash
# 1. SSH 登录
ssh -p 60022 user@tomabc.com

# 2. 克隆仓库
git clone <repo-url> /opt/ai-brief-site
cd /opt/ai-brief-site

# 3. 配置环境变量
cat > .env << EOF
GLM_API_KEY=your_glm_api_key_here
DEBUG=false
EOF

# 4. 构建并启动
docker-compose build
docker-compose up -d

# 5. 验证部署
curl http://localhost:8080/health
```

### 3.3 日常更新部署

```bash
# 使用部署脚本
cd /opt/ai-brief-site
bash deploy.sh
```

手动部署步骤：
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 构建新镜像
docker-compose build

# 3. 优雅停止旧容器
docker-compose down

# 4. 启动新容器
docker-compose up -d

# 5. 等待健康检查
sleep 10

# 6. 验证
curl -f http://localhost:8080/health || {
    echo "健康检查失败，执行回滚"
    docker-compose down
    # 回滚到上一版本
    docker-compose up -d --build
}
```

### 3.4 回滚方案

```bash
# 方案一：Git 回滚
git log --oneline -5  # 查看最近提交
git checkout <previous-commit-hash>
docker-compose build
docker-compose up -d

# 方案二：Docker 镜像回滚
# 查看历史镜像
docker images | grep ai-brief

# 标记当前镜像
docker tag ai-brief-site_ai-brief-app ai-brief-site_ai-brief-app:backup

# 回滚到备份镜像
docker-compose down
docker run -d --name ai-brief-app \
    -p 127.0.0.1:8080:8000 \
    -v ./data:/app/data \
    ai-brief-site_ai-brief-app:backup

# 方案三：完整数据恢复
# 假设备份在 /backup/ai-brief/
docker-compose down
cp -r /backup/ai-brief/data ./data
docker-compose up -d
```

### 3.5 CI/CD 配置示例

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: tomabc.com
          port: 60022
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/ai-brief-site
            git pull origin main
            docker-compose build
            docker-compose up -d
            sleep 10
            curl -f http://localhost:8080/health || exit 1
```

---

## 4. 故障排查手册

### 4.1 常见问题诊断

#### 问题：服务无响应

```bash
# 1. 检查容器状态
docker ps -a | grep ai-brief

# 2. 查看容器日志
docker logs ai-brief-app --tail 100

# 3. 检查端口占用
ss -tlnp | grep 8080

# 4. 检查资源使用
docker stats ai-brief-app --no-stream

# 5. 进入容器排查
docker exec -it ai-brief-app bash
curl http://localhost:8000/health
```

#### 问题：健康检查失败

```bash
# 检查具体组件状态
curl -s http://localhost:8080/health | jq .

# 常见原因：
# 1. SQLite 数据库损坏
ls -la data/metadata.db
sqlite3 data/metadata.db "SELECT 1"

# 2. LanceDB 目录缺失
ls -la data/lancedb/

# 3. 权限问题
ls -la data/
# 修复权限
chown -R 1000:1000 data/
```

#### 问题：数据抓取失败

```bash
# 检查网络连接
docker exec ai-brief-app python -c "
import httpx
print(httpx.get('https://www.anthropic.com/news/rss').status_code)
"

# 检查 API Key 配置
docker exec ai-brief-app env | grep GLM_API_KEY

# 手动触发抓取测试
curl -X POST http://localhost:8080/api/brief/generate
```

#### 问题：内存/磁盘不足

```bash
# 检查磁盘使用
df -h

# 检查数据目录大小
du -sh data/

# 清理旧数据（保留 30 天）
sqlite3 data/metadata.db "DELETE FROM briefs WHERE created_at < date('now', '-30 days')"
sqlite3 data/metadata.db "VACUUM"

# 清理 Docker 资源
docker system prune -a
```

### 4.2 日志查看

```bash
# 实时日志
docker logs -f ai-brief-app

# 最近 100 行日志
docker logs ai-brief-app --tail 100

# 带时间戳日志
docker logs ai-brief-app --timestamps

# 过滤错误日志
docker logs ai-brief-app 2>&1 | grep -i error

# 导出日志
docker logs ai-brief-app > /var/log/ai-brief-$(date +%Y%m%d).log
```

### 4.3 紧急恢复流程

```bash
# 1. 立即检查服务状态
docker ps -a
curl http://localhost:8080/health

# 2. 如果容器退出，重启
docker-compose restart

# 3. 如果重启失败，查看日志
docker-compose logs --tail 50

# 4. 如果镜像问题，回滚
git checkout HEAD~1
docker-compose build --no-cache
docker-compose up -d

# 5. 通知相关人员
# 严重故障需在 15 分钟内发出告警
```

---

## 5. 容灾恢复方案

### 5.1 备份策略

```bash
# 创建备份脚本 /opt/ai-brief-site/backup.sh
#!/bin/bash
BACKUP_DIR="/backup/ai-brief"
DATE=$(date +%Y%m%d)

# 备份数据目录
tar -czf $BACKUP_DIR/data-$DATE.tar.gz data/

# 备份数据库
sqlite3 data/metadata.db ".backup $BACKUP_DIR/metadata-$DATE.db"

# 保留最近 7 天备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 5.2 定时备份 (Cron)

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点执行备份
0 2 * * * /opt/ai-brief-site/backup.sh >> /var/log/ai-brief-backup.log 2>&1
```

### 5.3 恢复流程

```bash
# 1. 停止服务
docker-compose down

# 2. 恢复数据
tar -xzf /backup/ai-brief/data-YYYYMMDD.tar.gz

# 3. 验证数据库
sqlite3 data/metadata.db "SELECT COUNT(*) FROM briefs"

# 4. 重启服务
docker-compose up -d

# 5. 验证
curl http://localhost:8080/health
curl http://localhost:8080/api/brief/latest
```

### 5.4 灾难恢复 RTO/RPO

| 指标 | 目标值 | 说明 |
|------|--------|------|
| RTO (恢复时间目标) | < 30 分钟 | 从故障到服务恢复 |
| RPO (恢复点目标) | < 24 小时 | 可接受的数据丢失 |

### 5.5 多地域部署 (可选)

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  ai-brief-app:
    image: registry.example.com/ai-brief:v4
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 6. 运维检查清单

### 6.1 每日检查

- [ ] 检查服务健康状态：`curl http://localhost:8080/health`
- [ ] 检查容器运行状态：`docker ps | grep ai-brief`
- [ ] 检查错误率：`curl -s http://localhost:8080/metrics | grep error_rate`
- [ ] 验证每日简报生成：`curl http://localhost:8080/api/brief/latest`
- [ ] 检查磁盘空间：`df -h`

### 6.2 每周检查

- [ ] 查看周度错误趋势
- [ ] 检查备份完整性
- [ ] 清理过期日志：`docker logs ai-brief-app --tail 1000 > /var/log/ai-brief.log && docker restart ai-brief-app`
- [ ] 更新依赖检查：`pip list --outdated`
- [ ] 安全漏洞扫描：`docker scout cves ai-brief-site_ai-brief-app`

### 6.3 每月检查

- [ ] SLO 月度报告
- [ ] 数据库维护：`sqlite3 data/metadata.db "VACUUM; ANALYZE;"`
- [ ] 清理 30 天前数据
- [ ] 依赖版本更新
- [ ] 备份恢复演练

### 6.4 检查脚本

```bash
#!/bin/bash
# /opt/ai-brief-site/health-check.sh

echo "=== AI Brief Health Check ==="
echo "Time: $(date)"
echo

# 服务状态
echo "1. Container Status:"
docker ps --filter name=ai-brief-app --format "table {{.Status}}"

echo
echo "2. Health Endpoint:"
curl -s http://localhost:8080/health | jq .

echo
echo "3. SLO Metrics:"
curl -s http://localhost:8080/metrics | grep -E "^(total_requests|error_rate|avg_latency_ms|slo_met)"

echo
echo "4. Disk Usage:"
df -h /opt/ai-brief-site/data

echo
echo "5. Latest Brief:"
curl -s http://localhost:8080/api/brief/latest | jq '{date, title, source_count}'

echo
echo "=== Check Complete ==="
```

---

## 7. 自动化任务

### 7.1 每日简报生成 (Cron)

```bash
# 编辑 crontab
crontab -e

# 每天北京时间 7:00 生成简报 (UTC 23:00)
0 23 * * * curl -X POST http://localhost:8080/api/brief/generate >> /var/log/ai-brief-cron.log 2>&1
```

### 7.2 定时任务脚本

```bash
#!/bin/bash
# /opt/ai-brief-site/cron/generate-brief.sh

DATE=$(date +%Y-%m-%d)
LOG_FILE="/var/log/ai-brief/generate-$DATE.log"

echo "=== Generating brief for $DATE ===" >> $LOG_FILE
echo "Start: $(date)" >> $LOG_FILE

# 触发生成
RESPONSE=$(curl -s -X POST http://localhost:8080/api/brief/generate)

# 记录结果
echo "Response: $RESPONSE" >> $LOG_FILE
echo "End: $(date)" >> $LOG_FILE

# 检查是否成功
if echo "$RESPONSE" | grep -q "success\|generating"; then
    echo "Brief generation initiated successfully"
    exit 0
else
    echo "Brief generation failed: $RESPONSE"
    exit 1
fi
```

### 7.3 监控服务自动重启

```bash
# systemd 服务配置 /etc/systemd/system/ai-brief.service
[Unit]
Description=AI Daily Brief Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ai-brief-site
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
systemctl enable ai-brief
systemctl start ai-brief
```

### 7.4 日志轮转

```bash
# /etc/logrotate.d/ai-brief
/var/log/ai-brief/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

---

## 附录

### A. 常用命令速查

```bash
# 服务管理
docker-compose up -d          # 启动服务
docker-compose down           # 停止服务
docker-compose restart        # 重启服务
docker-compose logs -f        # 查看日志
docker-compose ps             # 查看状态

# 健康检查
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/metrics

# 数据库操作
sqlite3 data/metadata.db ".tables"
sqlite3 data/metadata.db "SELECT * FROM briefs ORDER BY date DESC LIMIT 5"

# 备份恢复
tar -czf backup-$(date +%Y%m%d).tar.gz data/
tar -xzf backup-20240101.tar.gz
```

### B. 联系人

| 角色 | 联系方式 | 职责 |
|------|----------|------|
| 主要负责人 | - | 服务可用性、故障响应 |
| 备份人员 | - | 主要负责人不可用时接管 |

### C. 相关文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [LanceDB 文档](https://lancedb.github.io/lancedb/)

---

*文档版本: 1.0*
*最后更新: 2026-05-19*
*维护者: SRE Team*