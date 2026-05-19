# AI Daily Brief 运维标准操作流程 (SOP)

**版本**: 1.0
**更新日期**: 2026-05-19
**适用系统**: ai.tomabc.com

---

## 目录

1. [部署SOP](#1-部署sop)
2. [数据同步SOP](#2-数据同步sop)
3. [故障排查SOP](#3-故障排查sop)
4. [回滚SOP](#4-回滚sop)
5. [日常运维SOP](#5-日常运维sop)

---

## 1. 部署SOP

### 1.1 部署前检查

```bash
# SSH到生产服务器
ssh tomabc@ai.tomabc.com

# 进入项目目录
cd /home/tomabc/ai-brief-site-new

# 检查当前状态
docker ps --filter "name=ai-brief-app"
curl -s http://localhost:8080/health | jq .
```

### 1.2 标准部署流程

**代码更新后必须rebuild Docker镜像**

```bash
# 方式一：使用部署脚本（推荐）
bash scripts/deploy.sh

# 方式二：手动部署
# 1. 拉取最新代码
git fetch origin
git reset --hard origin/main

# 2. 重建Docker镜像（必须 --no-cache）
docker-compose build --no-cache

# 3. 重启容器
docker-compose down
docker-compose up -d

# 4. 验证部署
sleep 10
curl -sf http://localhost:8080/health
```

### 1.3 部署脚本选项

```bash
# 标准部署（包含备份和健康检查）
bash scripts/deploy.sh

# 跳过备份（紧急部署）
bash scripts/deploy.sh --skip-backup

# 跳过健康检查
bash scripts/deploy.sh --skip-tests

# 禁用自动回滚
bash scripts/deploy.sh --no-rollback
```

### 1.4 部署后验证

```bash
# 检查容器状态
docker ps --filter "name=ai-brief-app" --format "{{.Status}}"

# 检查健康端点
curl http://localhost:8080/health

# 检查就绪端点
curl http://localhost:8080/ready

# 检查指标端点
curl http://localhost:8080/metrics

# 检查API响应
curl http://localhost:8080/api/brief/latest

# 检查日志
docker logs ai-brief-app --tail 50
```

### 1.5 常见部署问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 健康检查失败 | 容器启动慢 | 等待更长时间，检查日志 |
| 镜像构建失败 | 依赖下载超时 | 重试构建，检查网络 |
| 端口冲突 | 其他进程占用 | `lsof -i :8080` 查找并处理 |
| 数据库锁定 | 并发写入 | 重启容器 |

---

## 2. 数据同步SOP

### 2.1 数据库文件传输

**从本地同步到生产环境**

```bash
# 1. 备份生产数据库
ssh tomabc@ai.tomabc.com "cp /home/tomabc/ai-brief-site-new/data/metadata.db /home/tomabc/ai-brief-site-new/data/metadata.db.bak"

# 2. 上传本地数据库到服务器
scp /Users/yongwang/Documents/cc_workspace/ai-brief-site/data/metadata.db tomabc@ai.tomabc.com:/home/tomabc/ai-brief-site-new/data/

# 3. 重启容器使数据库生效
ssh tomabc@ai.tomabc.com "cd /home/tomabc/ai-brief-site-new && docker-compose restart"
```

### 2.2 Docker容器内数据更新

**方式一：通过volume挂载（推荐）**

项目配置了 `./data:/app/data` volume挂载，直接修改宿主机 `data/` 目录即可：

```bash
# 修改后的数据会立即在容器内生效
# 但建议重启容器确保一致性
docker-compose restart
```

**方式二：复制文件到容器内**

```bash
# 复制数据库文件到运行中的容器
docker cp data/metadata.db ai-brief-app:/app/data/metadata.db

# 重启容器
docker-compose restart
```

### 2.3 数据验证

```bash
# 检查数据库文件
ls -la data/metadata.db

# 检查数据库内容
sqlite3 data/metadata.db "SELECT COUNT(*) FROM briefs;"
sqlite3 data/metadata.db "SELECT COUNT(*) FROM articles;"
sqlite3 data/metadata.db "SELECT date, title FROM briefs ORDER BY date DESC LIMIT 5;"

# 检查LanceDB目录
ls -la data/lancedb/
```

### 2.4 数据导入流程

使用 `scripts/import_articles.py` 导入数据：

```bash
# 1. 编辑脚本中的数据
vim scripts/import_articles.py

# 2. 运行导入脚本
python scripts/import_articles.py

# 3. 验证导入结果
sqlite3 data/metadata.db "SELECT COUNT(*) FROM articles WHERE date('now') = published_at;"
```

### 2.5 数据备份策略

```bash
# 手动备份
BACKUP_DIR="/home/tomabc/ai-brief-site-new/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r data/ $BACKUP_DIR/

# 自动备份（部署脚本已集成）
# 保留最近10个备份，自动清理旧备份
```

---

## 3. 故障排查SOP

### 3.1 故障排查流程图

```
功能失效
    |
    v
检查API端点响应 --> 检查数据源匹配 --> 检查前端逻辑 --> 检查日志
```

### 3.2 检查API返回

```bash
# 检查健康状态
curl -s http://localhost:8080/health | jq .

# 预期响应:
# {"status": "healthy", "components": {"sqlite": "healthy", "lancedb": "healthy"}}

# 检查最新简报
curl -s http://localhost:8080/api/brief/latest | jq .

# 检查简报列表
curl -s http://localhost:8080/api/brief/list | jq .

# 检查特定日期简报
curl -s http://localhost:8080/api/brief/2026-05-19 | jq .

# 检查文章列表
curl -s http://localhost:8080/api/articles/brief/1 | jq .
```

### 3.3 检查数据源匹配

```bash
# 进入容器检查数据库
docker exec -it ai-brief-app /bin/bash

# 或直接从宿主机检查
sqlite3 data/metadata.db

# SQL查询检查数据
sqlite3 data/metadata.db <<EOF
-- 检查简报表
SELECT * FROM briefs ORDER BY date DESC LIMIT 5;

-- 检查文章表
SELECT id, original_title, chinese_title, source_name, published_at 
FROM articles ORDER BY id DESC LIMIT 10;

-- 检查文章与简报关联
SELECT a.id, a.chinese_title, b.date 
FROM articles a 
LEFT JOIN briefs b ON a.brief_id = b.id 
ORDER BY a.id DESC LIMIT 10;

-- 检查数据完整性
SELECT 'briefs' as table_name, COUNT(*) as count FROM briefs
UNION ALL
SELECT 'articles', COUNT(*) FROM articles
UNION ALL
SELECT 'sources', COUNT(*) FROM sources;
EOF
```

### 3.4 检查容器日志

```bash
# 查看最近日志
docker logs ai-brief-app --tail 100

# 实时查看日志
docker logs ai-brief-app -f

# 查看错误日志
docker logs ai-brief-app 2>&1 | grep -i error

# 查看特定时间段的日志
docker logs ai-brief-app --since 1h
```

### 3.5 常见故障及解决方案

#### 故障1: 简报页面无数据

**排查步骤**:
```bash
# 1. 检查API是否返回数据
curl http://localhost:8080/api/brief/latest

# 2. 检查数据库是否有数据
sqlite3 data/metadata.db "SELECT COUNT(*) FROM briefs;"

# 3. 如果数据库有数据但API无返回
#    - 检查容器日志
docker logs ai-brief-app --tail 50

# 4. 检查前端JS是否正确调用API
curl http://localhost:8080/static/js/app.js | grep -i fetch
```

**解决方案**:
- 数据库无数据：运行数据导入脚本
- API报错：检查日志，修复代码后重新部署
- 前端问题：检查静态文件是否正确加载

#### 故障2: 健康检查返回unhealthy

**排查步骤**:
```bash
# 检查具体哪个组件不健康
curl -s http://localhost:8080/health | jq .components

# 检查SQLite
sqlite3 data/metadata.db "SELECT 1;"

# 检查LanceDB目录
ls -la data/lancedb/
```

**解决方案**:
- SQLite问题：检查文件权限，恢复备份
- LanceDB问题：重建目录 `mkdir -p data/lancedb`

#### 故障3: 文章详情页404

**排查步骤**:
```bash
# 检查文章是否存在
sqlite3 data/metadata.db "SELECT id, original_title FROM articles WHERE id = ?;"

# 检查API路由
curl http://localhost:8080/api/articles/1
```

#### 故障4: 数据不同步

**症状**: 本地更新数据库后，生产环境无变化

**解决方案**:
```bash
# 1. 确认volume挂载正确
docker inspect ai-brief-app | grep -A 10 Mounts

# 2. 确认文件已同步
ssh tomabc@ai.tomabc.com "ls -la /home/tomabc/ai-brief-site-new/data/"

# 3. 重启容器
docker-compose restart

# 4. 验证数据
curl http://localhost:8080/api/brief/latest
```

---

## 4. 回滚SOP

### 4.1 自动回滚

部署脚本支持自动回滚（默认开启）：

```bash
# 当健康检查失败时，自动恢复到备份状态
bash scripts/deploy.sh  # 会自动创建备份
# 如果部署失败，自动回滚
```

### 4.2 手动回滚

```bash
# 使用回滚脚本
bash scripts/rollback.sh

# 回滚到指定备份
bash scripts/rollback.sh 20260519_143000

# 查看可用备份
ls -la /home/tomabc/ai-brief-site-new/backups/
```

### 4.3 手动回滚步骤

```bash
# 1. 停止当前容器
docker-compose down

# 2. 恢复数据库
cp -r /home/tomabc/ai-brief-site-new/backups/BACKUP_NAME/data /home/tomabc/ai-brief-site-new/

# 3. 恢复代码版本（如需要）
git checkout COMMIT_HASH

# 4. 重建并启动
docker-compose build
docker-compose up -d

# 5. 验证
sleep 10
curl http://localhost:8080/health
```

### 4.4 回滚后验证

```bash
# 运行健康检查脚本
bash scripts/health-check.sh --strict

# 检查数据完整性
sqlite3 data/metadata.db "SELECT COUNT(*) FROM briefs; SELECT COUNT(*) FROM articles;"

# 检查API响应
curl http://localhost:8080/api/brief/latest
```

---

## 5. 日常运维SOP

### 5.1 日常检查清单

```bash
# 每日检查脚本
cat > /home/tomabc/ai-brief-site-new/scripts/daily-check.sh << 'EOF'
#!/bin/bash
echo "=== AI Daily Brief Daily Check ==="
echo "Date: $(date)"
echo ""

# 1. 容器状态
echo "1. Container Status:"
docker ps --filter "name=ai-brief-app" --format "table {{.Names}}\t{{.Status}}"
echo ""

# 2. Health Check
echo "2. Health Check:"
curl -s http://localhost:8080/health | jq .
echo ""

# 3. Database Status
echo "3. Database Status:"
sqlite3 data/metadata.db <<SQL
SELECT 'Briefs: ' || COUNT(*) FROM briefs;
SELECT 'Articles: ' || COUNT(*) FROM articles;
SELECT 'Latest Brief: ' || date FROM briefs ORDER BY date DESC LIMIT 1;
SQL
echo ""

# 4. Disk Usage
echo "4. Disk Usage:"
df -h /home/tomabc
echo ""

# 5. Recent Logs
echo "5. Recent Errors:"
docker logs ai-brief-app --since 24h 2>&1 | grep -i error | tail -5
echo ""
echo "=== Check Complete ==="
EOF
chmod +x /home/tomabc/ai-brief-site-new/scripts/daily-check.sh
```

### 5.2 日志管理

```bash
# 查看应用日志
docker logs ai-brief-app --tail 100

# 导出日志到文件
docker logs ai-brief-app > /tmp/ai-brief-$(date +%Y%m%d).log

# 清理Docker日志（谨慎使用）
truncate -s 0 $(docker inspect --format='{{.LogPath}}' ai-brief-app)
```

### 5.3 监控指标

```bash
# Prometheus格式的指标
curl http://localhost:8080/metrics

# 关键指标:
# - total_requests: 总请求数
# - error_requests: 错误请求数
# - error_rate: 错误率
# - avg_latency_ms: 平均延迟
# - slo_met: SLO是否达标
```

### 5.4 备份策略

| 备份类型 | 频率 | 保留策略 | 存储位置 |
|---------|------|---------|---------|
| 自动备份 | 每次部署 | 最近10个 | backups/ |
| 手动备份 | 维护前 | 永久 | backups/manual/ |
| 数据库快照 | 每日 | 7天 | 可配置 |

### 5.5 定期维护

```bash
# 清理旧备份（保留最近10个）
cd /home/tomabc/ai-brief-site-new/backups
ls -1t | tail -n +11 | xargs rm -rf

# 清理无用Docker镜像
docker image prune -f

# 数据库优化
sqlite3 data/metadata.db "VACUUM; ANALYZE;"

# 检查磁盘空间
df -h
```

---

## 附录

### A. 常用命令速查

```bash
# 查看容器状态
docker ps -a | grep ai-brief

# 进入容器
docker exec -it ai-brief-app /bin/bash

# 重启服务
docker-compose restart

# 查看日志
docker logs ai-brief-app -f

# 健康检查
curl http://localhost:8080/health

# 部署
bash scripts/deploy.sh

# 回滚
bash scripts/rollback.sh

# 数据库查询
sqlite3 data/metadata.db "SELECT * FROM briefs LIMIT 5;"
```

### B. 联系信息

- **VPS**: ai.tomabc.com (SSH: tomabc@ai.tomabc.com)
- **项目路径**: /home/tomabc/ai-brief-site-new
- **本地路径**: /Users/yongwang/Documents/cc_workspace/ai-brief-site

### C. 关键文件路径

| 文件 | 路径 | 说明 |
|-----|------|------|
| 主程序 | app/main.py | FastAPI入口 |
| 配置文件 | config.py | 应用配置 |
| 数据库 | data/metadata.db | SQLite数据库 |
| 向量库 | data/lancedb/ | LanceDB向量存储 |
| 部署脚本 | scripts/deploy.sh | 自动部署 |
| 回滚脚本 | scripts/rollback.sh | 回滚操作 |
| 健康检查 | scripts/health-check.sh | 健康检查 |

---

**文档维护**: 当系统架构或流程变更时，请及时更新本文档。