set -e

echo "Starting Caddy Web Server..."

PORT=${PORT:-8080}
PORT_MAP_PATH=${PORT_MAP_PATH:-"/app/port_map.json"}

echo "Using PORT=${PORT}, PORT_MAP_PATH=${PORT_MAP_PATH}"

TMPPORT=$(python3 -c "import json, os; path=os.getenv('PORT_MAP_PATH', '/app/port_map.json'); print(json.load(open(path)).get('tmpserver', '8000'))")

export TMPPORT
echo "TMPPORT resolved to ${TMPPORT}"

envsubst '${PORT} ${TMPPORT}' < /etc/caddy/Caddyfile.template > /etc/caddy/Caddyfile

# Caddy 시작
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile