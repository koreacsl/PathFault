# Dockerfile fragment for WS: nginx
FROM nginx:1.27.3

WORKDIR /etc/nginx

# Nginx 설정 템플릿 및 Python 스크립트 복사
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# 작업 디렉터리 설정
WORKDIR /etc/nginx

