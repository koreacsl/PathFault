# Dockerfile fragment for apachehttpserver
# Base image
FROM httpd:2.4

# 작업 디렉터리 설정
WORKDIR /usr/local/apache2/conf/

# Python 설치 및 필요한 디렉토리 생성
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Python 스크립트 및 템플릿 복사
COPY generate_apache_map.py /usr/local/apache2/conf/
COPY httpd.conf.template /usr/local/apache2/conf/
