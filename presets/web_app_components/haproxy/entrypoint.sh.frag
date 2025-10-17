echo "Starting HAProxy..."

echo "Using PORT=${PORT} and PORT_MAP_PATH=${PORT_MAP_PATH}"

TMP=$(python3 -c "import os, json; path = os.getenv('PORT_MAP_PATH', '/app/port_map.json'); print(json.load(open(path)).get('tmpserver', '8000'))")
export TMPPORT=$TMP
echo "TMPPORT is set to ${TMPPORT}"

python3 /usr/local/etc/haproxy/generate_haproxy_map.py || {
    echo "Error: Failed to generate HAProxy backend configuration."
    exit 1
}

envsubst '${PORT} ${TMPPORT}' < /usr/local/etc/haproxy/haproxy.cfg.template > /usr/local/etc/haproxy/haproxy.cfg

haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg || {
    echo "Error: HAProxy configuration is invalid."
    exit 1
}

echo "HAProxy is ready on port $PORT"
exec haproxy -f /usr/local/etc/haproxy/haproxy.cfg