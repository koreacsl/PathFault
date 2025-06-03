echo "Starting Nginx Web Server..."

if [ -f /etc/nginx/nginx.conf.template ]; then
    envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
    echo "Nginx configuration generated with PORT=$PORT"
else
    echo "Error: nginx.conf.template not found."
    exit 1
fi

echo "Starting Nginx Web Server..."

if [ ! -f /etc/nginx/nginx.conf ]; then
    echo "Error: nginx.conf not found in /etc/nginx. Ensure your configuration file is correctly mounted."
    exit 1
fi

exec nginx -g "daemon off;"