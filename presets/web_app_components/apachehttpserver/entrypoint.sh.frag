# Entrypoint script fragment for apachehttpserver
echo "Starting Apache HTTP Server as a reverse proxy..."

# Python 스크립트를 실행하여 Apache map 파일 생성
echo "Generating Apache map configuration from port_map.json..."
python3 /usr/local/apache2/conf/generate_apache_map.py || {
    echo "Error: Failed to generate Apache map configuration."
    exit 1
}

# Apache 설정 템플릿에서 환경 변수 치환
if [ -f /usr/local/apache2/conf/httpd.conf.template ]; then
    envsubst '${PORT}' < /usr/local/apache2/conf/httpd.conf.template > /usr/local/apache2/conf/httpd.conf
    echo "Apache configuration generated with PORT=$PORT"
else
    echo "Error: httpd.conf.template not found."
    exit 1
fi

# Apache 설정 구문 확인
httpd -t || {
    echo "Error: Apache configuration syntax is invalid."
    exit 1
}

# Apache 실행
httpd -D FOREGROUND