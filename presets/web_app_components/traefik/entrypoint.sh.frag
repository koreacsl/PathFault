echo "Starting Traefik..."

TMPPORT=$(python3 -c "import json; print(json.load(open('${PORT_MAP_PATH:-/app/port_map.json}')).get('tmpserver', '8000'))")

export TMPPORT
echo "TMPPORT=${TMPPORT}"

echo "Using PORT=${PORT} and TMPPORT=${TMPPORT}"

# traefik.yaml 환경변수 치환하여 생성
envsubst '${PORT}' < /app/traefik.yaml.template > /app/traefik.yaml
envsubst '${TMPPORT}' < /app/dynamic_conf.yaml.template > /app/dynamic_conf.yaml

exec traefik --configFile=/app/traefik.yaml