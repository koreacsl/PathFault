# Dockerfile fragment for Caddy Web Server based on Ubuntu 22.04
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

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

WORKDIR /etc/caddy

COPY Caddyfile.template /etc/caddy/Caddyfile.template
