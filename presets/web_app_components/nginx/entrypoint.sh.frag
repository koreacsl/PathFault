echo "Starting Nginx Web Server..."

# Python 스크립트를 실행하여 Nginx map 파일 생성
echo "Generating Nginx map configuration from port_map.json..."
python3 /etc/nginx/generate_nginx_map.py || {
    echo "Error: Failed to generate Nginx map configuration."
    exit 1
}

# Nginx 설정 템플릿에서 환경 변수 치환
if [ -f /etc/nginx/nginx.conf.template ]; then
    envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
    echo "Nginx configuration generated with PORT=$PORT"
else
    echo "Error: nginx.conf.template not found."
    exit 1
fi

echo "Starting Nginx Web Server..."

# Nginx 설정 파일 확인
if [ ! -f /etc/nginx/nginx.conf ]; then
    echo "Error: nginx.conf not found in /etc/nginx. Ensure your configuration file is correctly mounted."
    exit 1
fi

# Nginx 실행
exec nginx -g "daemon off;"