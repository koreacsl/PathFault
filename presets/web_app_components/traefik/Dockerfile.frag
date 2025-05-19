FROM ubuntu:22.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# 필수 패키지 설치
RUN apt-get update && apt-get install -y curl tar gettext-base

# Traefik 바이너리 다운로드 및 설치
RUN curl -LO https://github.com/traefik/traefik/releases/download/v3.4.0-rc2/traefik_v3.4.0-rc2_linux_amd64.tar.gz && \
    tar -xzf traefik_v3.4.0-rc2_linux_amd64.tar.gz && \
    chmod +x traefik && \
    mv traefik /usr/local/bin/traefik && \
    rm traefik_v3.4.0-rc2_linux_amd64.tar.gz

# 구성 파일 복사
COPY traefik.yaml.template /app/traefik.yaml.template
COPY dynamic_conf.yaml.template /app/dynamic_conf.yaml.template