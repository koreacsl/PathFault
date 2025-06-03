# Dockerfile fragment for WS: nginx
FROM nginx:1.27.3

WORKDIR /etc/nginx

COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY generate_nginx_map.py /etc/nginx/generate_nginx_map.py

RUN apt-get update && apt-get install -y python3 && \
    python3 /etc/nginx/generate_nginx_map.py

WORKDIR /etc/nginx

