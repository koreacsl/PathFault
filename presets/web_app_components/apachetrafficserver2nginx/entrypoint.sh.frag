echo "Starting Apache Traffic Server..."

if [ ! -d "/usr/local/etc/trafficserver/var/log/trafficserver" ]; then
    mkdir -p /usr/local/etc/trafficserver/var/log/trafficserver
fi
if [ ! -d "/usr/local/etc/trafficserver/var/trafficserver" ]; then
    mkdir -p /usr/local/etc/trafficserver/var/trafficserver
fi
chown -R nobody:nogroup /usr/local/etc/trafficserver/var/log/trafficserver
chown -R nobody:nogroup /usr/local/etc/trafficserver/var/trafficserver
chmod -R 755 /usr/local/etc/trafficserver/var/log/trafficserver
chmod -R 755 /usr/local/etc/trafficserver/var/trafficserver

if [ -f /usr/local/etc/trafficserver/records.yaml.template ]; then
    envsubst '${PORT}' < /usr/local/etc/trafficserver/records.yaml.template > /usr/local/etc/trafficserver/records.yaml
    echo "ATS records.yaml generated with PORT=$PORT"
else
    echo "Error: records.yaml.template not found."
    exit 1
fi

if [ -f /usr/local/etc/trafficserver/etc/trafficserver/records.yaml ]; then
    sed -i "s/server_ports:.*/server_ports: '${PORT}'/" /usr/local/etc/trafficserver/etc/trafficserver/records.yaml
    echo "Updated server_ports in records.yaml to PORT=${PORT}"
else
    echo "Error: records.yaml not found."
    exit 1
fi

if python3 /usr/local/etc/trafficserver/generate_ats_map.py; then
    echo "remap.config generated successfully."
else
    echo "Error: Failed to generate remap.config."
    tail -f /dev/null
    exit 1
fi

if [ -f /usr/local/etc/trafficserver/remap.config ]; then
    mv /usr/local/etc/trafficserver/remap.config /usr/local/etc/trafficserver/etc/trafficserver/remap.config
    echo "Moved remap.config to /usr/local/etc/trafficserver/etc/trafficserver/"
else
    echo "Error: remap.config not found."
    tail -f /dev/null
    exit 1
fi

traffic_server -C verify_config || {
    echo "Error: ATS configuration syntax is invalid."
    exit 1
}

exec traffic_server