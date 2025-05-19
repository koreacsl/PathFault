import json
import os

# 환경 변수에서 파일 경로를 가져옴
PORT_MAP_FILE = os.getenv("PORT_MAP_PATH", "/app/port_map.json")  # 기본 경로 설정
APACHE_MAP_FILE = "/usr/local/apache2/conf/apache_proxy_map.conf"  # Apache map 파일 경로
APACHE_CONF_FILE = "/usr/local/apache2/conf/httpd.conf"  # Apache 설정 파일 경로

def generate_apache_map():
    """
    Generate an Apache-compatible map configuration from port_map.json.
    """
    try:
        # JSON 파일 읽기
        with open(PORT_MAP_FILE, "r") as json_file:
            port_map = json.load(json_file)

        # tmpserver 포트 가져오기 (없으면 기본값 8000)
        tmpserver_port = port_map.get("tmpserver", 8000)

        # Apache map 파일 생성
        with open(APACHE_MAP_FILE, "w") as apache_file:
            for service, port in port_map.items():
                apache_file.write(f"""
# Proxy configuration for {service}
SetEnvIf REQUEST_URI "^/{service}(/.*)?" TARGET_PORT={port}
ProxyPass /{service} http://{service}:{port}
ProxyPassReverse /{service} http://{service}:{port}
""")

            # tmpserver에 대한 기본 백엔드 설정 추가
            apache_file.write(f"""
# Default proxy fallback for unmapped services (tmpserver)
ProxyPassMatch ^/(?!tmpserver)([^/]+) http://tmpserver:{tmpserver_port}/$1
ProxyPassReverse / http://tmpserver:{tmpserver_port}/
""")

        # 🚀 Apache 설정 파일에 tmpserver 포트 값 업데이트
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