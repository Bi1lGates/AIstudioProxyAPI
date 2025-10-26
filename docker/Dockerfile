#Dockerfile

# ------------------------------------------------------------------------------------
# Builder Stage: 负责安装依赖并构建一个干净的 Python 环境
# ------------------------------------------------------------------------------------
FROM python:3.10-slim-bookworm AS builder

# 关键优化 1: 更换为国内 apt 源，加速系统依赖下载
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

ARG DEBIAN_FRONTEND=noninteractive
ARG PROZY_ADDR

# 安装基础工具
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ----------------- Poetry 安装优化 -----------------
# 关键优化 2: 使用 pip 从国内镜像安装 Poetry，避免从官网 curl 慢速下载
# 我们先配置 pip 的全局镜像，然后用 pip 安装 poetry。
ENV POETRY_VERSION=1.8.3
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install poetry==${POETRY_VERSION}

# 关键修复 1: 立即将 poetry 添加到 PATH 环境变量
# 注意：原文件中这一行在后面，导致 poetry 命令找不到
ENV PATH="/root/.local/bin:${PATH}"
# ---------------------------------------------------

# 配置 poetry 使用国内镜像源
RUN poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple && poetry config installer.parallel true

WORKDIR /app_builder
COPY pyproject.toml poetry.lock ./


# 安装项目依赖
RUN poetry config virtualenvs.create false --local && \
    poetry install --no-root --no-dev --no-interaction --no-ansi

# ------------------------------------------------------------------------------------
# Final Stage: 构建最终的、轻量级的生产镜像
# ------------------------------------------------------------------------------------
FROM python:3.10-slim-bookworm

# 再次更换为国内源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
ARG DEBIAN_FRONTEND=noninteractive

# 步骤 1: 安装所有系统依赖 (包括 Playwright 的依赖)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxtst6 ca-certificates fonts-liberation libasound2 libpangocairo-1.0-0 libpango-1.0-0 libu2f-udev \
    supervisor curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/bash -d /app appuser

WORKDIR /app

# 步骤 2: 从 builder 阶段复制已安装的 Python 包和可执行文件
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
# 复制 poetry 可执行文件

# 复制应用代码
COPY . .

# 下载 Camoufox 浏览器（从 GitHub 官方源）
RUN python -m camoufox fetch

# 修复 Camoufox 0.4.11 的 proxy=None 问题
COPY patch_camoufox_proxy.py /tmp/
RUN python /tmp/patch_camoufox_proxy.py && rm /tmp/patch_camoufox_proxy.py

# 创建目录和设置权限
RUN mkdir -p /app/logs \
    /app/auth_profiles/active \
    /app/auth_profiles/saved \
    /app/certs \
    /app/browser_utils/custom_scripts \
    /home/appuser/.cache/ms-playwright \
    /home/appuser/.mozilla \
    /var/cache/camoufox && \
    # 修正 camoufox 缓存逻辑
    if [ -d /root/.cache/camoufox ]; then cp -a /root/.cache/camoufox/* /var/cache/camoufox/; fi && \
    mkdir -p /app/.cache && \
    ln -s /var/cache/camoufox /app/.cache/camoufox && \
    touch /app/auth_profiles/key.txt && \
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser


COPY supervisord.conf /etc/supervisor/conf.d/app.conf

RUN python update_browserforge_data.py

# 设置环境变量
EXPOSE 2048
EXPOSE 3120
USER appuser
ENV HOME=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DEFAULT_FASTAPI_PORT=2048
# ... 其他环境变量

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/app.conf"]