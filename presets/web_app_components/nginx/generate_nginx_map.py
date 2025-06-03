import json
import os

PORT_MAP_FILE = os.getenv("PORT_MAP_PATH", "/app/port_map.json")
NGINX_MAP_FILE = "/etc/nginx/nginx_port_map.conf"


def generate_nginx_map():
    """
    Generate an Nginx-compatible map configuration from port_map.json.
    """
    try:
        with open(PORT_MAP_FILE, "r") as json_file:
            port_map = json.load(json_file)

        with open(NGINX_MAP_FILE, "w") as nginx_file:
            for service, port in port_map.items():
                nginx_file.write(f"{service} {port};\n")

        print(f"Nginx map file generated at {NGINX_MAP_FILE}")
    except FileNotFoundError:
        print(f"Error: {PORT_MAP_FILE} not found.")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {PORT_MAP_FILE}: {e}")
    except Exception as e:
        print(f"Error generating Nginx map: {e}")


if __name__ == "__main__":
    generate_nginx_map()