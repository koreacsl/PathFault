import json
import os

PORT_MAP_FILE = os.getenv("PORT_MAP_PATH", "/app/port_map.json")
APACHE_MAP_FILE = "/usr/local/apache2/conf/apache_proxy_map.conf"
APACHE_CONF_FILE = "/usr/local/apache2/conf/httpd.conf"

def generate_apache_map():
    """
    Generate an Apache-compatible map configuration from port_map.json.
    """
    try:
        with open(PORT_MAP_FILE, "r") as json_file:
            port_map = json.load(json_file)

        tmpserver_port = port_map.get("tmpserver", 8000)

        with open(APACHE_MAP_FILE, "w") as apache_file:
            for service, port in port_map.items():
                apache_file.write(f"""
# Proxy configuration for {service}
SetEnvIf REQUEST_URI "^/{service}(/.*)?" TARGET_PORT={port}
ProxyPass /{service} http://{service}:{port}
ProxyPassReverse /{service} http://{service}:{port}
""")

            apache_file.write(f"""
# Default proxy fallback for unmapped services (tmpserver)
ProxyPassMatch ^/(?!tmpserver)([^/]+) http://tmpserver:{tmpserver_port}/$1
ProxyPassReverse / http://tmpserver:{tmpserver_port}/
""")

        with open(APACHE_CONF_FILE, "r") as conf_file:
            conf_data = conf_file.read()

        conf_data = conf_data.replace('Define TMP_SERVER_PORT "8000"', f'Define TMP_SERVER_PORT "{tmpserver_port}"')

        with open(APACHE_CONF_FILE, "w") as conf_file:
            conf_file.write(conf_data)

        print(f"Apache proxy map file generated at {APACHE_MAP_FILE}")
        print(f"Apache configuration updated at {APACHE_CONF_FILE}")

    except FileNotFoundError:
        print(f"Error: {PORT_MAP_FILE} not found.")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {PORT_MAP_FILE}: {e}")
    except Exception as e:
        print(f"Error generating Apache proxy map: {e}")

if __name__ == "__main__":
    generate_apache_map()