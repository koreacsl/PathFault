#!/bin/bash

echo "Starting Apache Tomcat..."

echo "Using PORT=${PORT} and PORT_MAP_PATH=${PORT_MAP_PATH}"

# server.xml의 Connector 포트 설정
if [ -f /usr/local/tomcat/conf/server.xml ]; then
    echo "Updating server.xml with PORT=${PORT}..."
    sed -i "s/port=\"8080\"/port=\"${PORT}\"/" /usr/local/tomcat/conf/server.xml || {
        echo "Error: Failed to update server.xml with PORT=${PORT}."
        exit 1
    }
else
    echo "Error: server.xml not found in /usr/local/tomcat/conf."
    exit 1
fi

echo "Tomcat will listen on external port $PORT"

# Tomcat 실행
exec catalina.sh run