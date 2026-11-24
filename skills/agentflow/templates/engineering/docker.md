# 容器化与 Dockerfile 工程模板

> 用法：目标仓需要容器化交付、本地环境编排或云原生部署时，按本模板规范编写 `Dockerfile` 与 `docker-compose.yml`。
> 复制时将 `<项目名>`、`<构建命令>` 等占位符替换为目标仓真实配置。
> 关联规范：必须满足 [`security.md`](../../references/standards/security.md) 中关于凭据零硬编码与非 root 运行的硬要求（复制到目标仓后对应落点为目标仓 `.agentflow/standards/security.md`）。

## 0. 容器化硬边界（MUST 检查项）

1. **多阶段构建（Multi-Stage Builds）**：必须分离构建环境与生产运行环境。生产镜像中严禁携带源码编译器、构建依赖与测试工具。
2. **非 root 用户运行**：运行阶段必须创建并切换至非特权专用系统用户（如 `USER appuser`），严禁以 root 身份暴露在容器中运行。
3. **固定镜像标签与摘要**：严禁使用 `latest` 标签。基础镜像必须锁定明确版本号（如 `node:22-alpine3.20` 或带 sha256 摘要）。
4. **最小化生产运行时**：优先选用轻量级 Linux 发行版（Alpine 或 Google Distroless）。
5. **显式健康检查（HEALTHCHECK）**：生产镜像必须定义 `HEALTHCHECK` 指令或与 K8s 探针兼容的健康检查端点。
6. **完备 `.dockerignore`**：根目录下必须具备 `.dockerignore`，排除 `node_modules`、`.git`、测试报告、本地环境文件与临时日志。

---

## 1. 现代化多阶段 Dockerfile 模板

### 1.1 Node.js (TypeScript / 前端 / 服务端)

```dockerfile
# ==========================================
# 阶段 1: 依赖安装与构建
# ==========================================
FROM node:22-alpine3.20 AS builder

WORKDIR /app

# 先复制依赖定义，充分利用 Docker 层缓存
COPY package.json pnpm-lock.yaml* package-lock.json* ./

RUN \
  if [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm install --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  else echo "Lockfile not found." && exit 1; \
  fi

# 复制源码并构建
COPY . .
RUN npm run build

# 生产依赖清理
RUN npm prune --production

# ==========================================
# 阶段 2: 极简生产运行镜像
# ==========================================
FROM node:22-alpine3.20 AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# 创建非特权安全运行用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser

# 仅从构建阶段复制产物与生产依赖
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./package.json

USER appuser

EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["node", "dist/index.js"]
```

### 1.2 Golang

```dockerfile
# ==========================================
# 阶段 1: 静态编译
# ==========================================
FROM golang:1.24-alpine3.20 AS builder

WORKDIR /src

# 缓存依赖
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# 静态无符号编译
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /bin/server ./cmd/server

# ==========================================
# 阶段 2: 极简运行镜像 (Distroless / Scratch)
# ==========================================
FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app

# 从构建镜像复制二进制与 CA 证书
COPY --from=builder /bin/server /app/server

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/app/server"]
```

### 1.3 Python

```dockerfile
# ==========================================
# 阶段 1: 依赖编译
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --user -r requirements.txt

# ==========================================
# 阶段 2: 生产运行环境
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd --create-home appuser
USER appuser

# 复制依赖与源码
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
```

---

## 2. `.dockerignore` 模板

复制到目标仓根目录 `.dockerignore`：

```text
.git
.github
.gitignore
.dockerignore
node_modules
npm-debug.log
dist
build
coverage
*.md
.env*
!.env.example
.DS_Store
.idea
.vscode
```
