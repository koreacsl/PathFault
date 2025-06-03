# Dockerfile fragment for apachehttpserver
# Base image
FROM httpd:2.4

WORKDIR /usr/local/apache2/conf/

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY generate_apache_map.py /usr/local/apache2/conf/
COPY httpd.conf.template /usr/local/apache2/conf/
