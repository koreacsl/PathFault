FROM ubuntu:22.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y curl tar gettext-base

RUN curl -LO https://github.com/traefik/traefik/releases/download/v3.4.0-rc2/traefik_v3.4.0-rc2_linux_amd64.tar.gz && \
    tar -xzf traefik_v3.4.0-rc2_linux_amd64.tar.gz && \
    chmod +x traefik && \
    mv traefik /usr/local/bin/traefik && \
    rm traefik_v3.4.0-rc2_linux_amd64.tar.gz

COPY traefik.yaml.template /app/traefik.yaml.template
COPY dynamic_conf.yaml.template /app/dynamic_conf.yaml.template