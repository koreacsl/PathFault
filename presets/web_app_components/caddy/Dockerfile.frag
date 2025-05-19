# Dockerfile fragment for Caddy Web Server based on Ubuntu 22.04
FROM ubuntu:22.04

# 기본 환경 설정
ENV DEBIAN_FRONTEND=noninteractive

# 패키지 업데이트 및 필수 패키지 설치
RUN echo "Acquire::AllowInsecureRepositories true;" > /etc/apt/apt.conf.d/99allow-insecure && \
    echo "Acquire::AllowDowngradeToInsecureRepositories true;" >> /etc/apt/apt.conf.d/99allow-insecure && \
    apt-get update && apt-get install -y \
    curl \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    ca-certificates \
    gnupg \
    gettext-base --allow-unauthenticated && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && apt-get install -y caddy --allow-unauthenticated && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉터리 설정
WORKDIR /etc/caddy

# Caddyfile 템플릿 복사
COPY Caddyfile.template /etc/caddy/Caddyfile.template
