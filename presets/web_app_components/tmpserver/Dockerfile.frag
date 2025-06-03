# Dockerfile fragment for WS: nginx
FROM nginx:1.27.3

WORKDIR /etc/nginx

COPY nginx.conf.template /etc/nginx/nginx.conf.template

WORKDIR /etc/nginx

