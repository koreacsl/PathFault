echo "Starting HAProxy..."

echo "Using PORT=${PORT} and PORT_MAP_PATH=${PORT_MAP_PATH}"

# tmpserver 포트를 port_map.json에서 추출
TMPPORT=$(python3 -c "
import os, json
path = os.getenv('PORT_MAP_PATH', '/app/port_map.json')
print(json.load(open(path)).get('tmpserver', '8000'))
")
export TMPPORT
echo "TMPPORT is set to ${TMPPORT}"

# haproxy.cfg 생성
python3 /usr/local/etc/haproxy/generate_tmpserver_cfg.py || {
    echo "Error: Failed to generate haproxy.cfg"
    exit 1
}

echo "Validating haproxy.cfg..."
haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg || {
    echo "Error: HAProxy configuration is invalid."
    exit 1
}

echo "Launching HAProxy..."
exec haproxy -f /usr/local/etc/haproxy/haproxy.cfg