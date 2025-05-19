# Dockerfile fragment for apache_traffic_server
# Base image
FROM trafficserver/trafficserver:10.0.2

# 작업 디렉터리 설정
WORKDIR /usr/local/etc/trafficserver/

# Python 설치 및 ATS 초기화
RUN apt-get update && apt-get install -y python3 gettext-base && \
    traffic_layout init && \
    rm -rf /var/lib/apt/lists/*

# 설정 파일 및 Python 스크립트 복사
COPY generate_ats_map.py /usr/local/etc/trafficserver/
COPY remap.config.template /usr/local/etc/trafficserver/remap.config.template
COPY records.yaml /usr/local/etc/trafficserver/records.yaml.template
