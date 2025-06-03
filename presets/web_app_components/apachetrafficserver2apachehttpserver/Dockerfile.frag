# Dockerfile fragment for apache_traffic_server
# Base image
FROM trafficserver/trafficserver:10.0.2

WORKDIR /usr/local/etc/trafficserver/

RUN apt-get update && apt-get install -y python3 gettext-base && \
    traffic_layout init && \
    rm -rf /var/lib/apt/lists/*

COPY generate_ats_map.py /usr/local/etc/trafficserver/
COPY remap.config.template /usr/local/etc/trafficserver/remap.config.template
COPY records.yaml /usr/local/etc/trafficserver/records.yaml.template
