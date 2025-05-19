# Dockerfile fragment for WS: haproxy
FROM haproxy:3.1.6

WORKDIR /usr/local/etc/haproxy

# HAProxy 설정 템플릿 및 backend 생성 스크립트 복사
COPY haproxy.cfg.template /usr/local/etc/haproxy/haproxy.cfg.template
COPY generate_haproxy_map.py /usr/local/etc/haproxy/generate_haproxy_map.py

# Python3 및 envsubst 설치, 초기 backend 파일 생성
RUN apt-get update && apt-get install -y python3 gettext && \
    python3 /usr/local/etc/haproxy/generate_haproxy_map.py

# 작업 디렉토리 유지
WORKDIR /usr/local/etc/haproxy