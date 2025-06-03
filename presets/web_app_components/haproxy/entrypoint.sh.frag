echo "Starting HAProxy..."

echo "Using PORT=${PORT} and PORT_MAP_PATH=${PORT_MAP_PATH}"

TMPPORT=$(python3 -c "
import os, json
path = os.getenv('PORT_MAP_PATH', '/app/port_map.json')
print(json.load(open(path)).get('tmpserver', '8000'))
")
export TMPPORT
echo "TMPPORT is set to ${TMPPORT}"

python3 /usr/local/etc/haproxy/generate_tmpserver_cfg.py || {
    echo "Error: Failed to generate haproxy.cfg"
    exit 1
}

haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg || {
    echo "Error: HAProxy configuration is invalid."
    exit 1
}

exec haproxy -f /usr/local/etc/haproxy/haproxy.cfg