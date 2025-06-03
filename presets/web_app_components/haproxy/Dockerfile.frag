# Dockerfile fragment for WS: haproxy
FROM haproxy:3.1.6

WORKDIR /usr/local/etc/haproxy

COPY haproxy.cfg.template /usr/local/etc/haproxy/haproxy.cfg.template
COPY generate_haproxy_map.py /usr/local/etc/haproxy/generate_haproxy_map.py

RUN apt-get update && apt-get install -y python3 gettext && \
    python3 /usr/local/etc/haproxy/generate_haproxy_map.py

WORKDIR /usr/local/etc/haproxy