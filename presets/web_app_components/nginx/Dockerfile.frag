# Dockerfile fragment for WS: nginx
FROM nginx:1.27.3

WORKDIR /etc/nginx


# Nginx 설정 템플릿 및 Python 스크립트 복사
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY generate_nginx_map.py /etc/nginx/generate_nginx_map.py

# Python 설치 및 Nginx map 파일 생성
RUN apt-get update && apt-get install -y python3 && \
    python3 /etc/nginx/generate_nginx_map.py

# 작업 디렉터리 설정
WORKDIR /etc/nginx

