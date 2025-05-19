import os
import json

port_map_path = os.getenv("PORT_MAP_PATH", "/app/port_map.json")
cfg_template = "/usr/local/etc/haproxy/haproxy.cfg.template"
cfg_output = "/usr/local/etc/haproxy/haproxy.cfg"

with open(port_map_path) as f:
    port_map = json.load(f)

tmp_port = port_map.get("tmpserver", 8000)
listen_port = os.getenv("PORT", "8080")

with open(cfg_template) as template, open(cfg_output, "w") as output:
    content = template.read()
    content = content.replace("${PORT}", listen_port)
    content = content.replace("${TMPPORT}", str(tmp_port))
    output.write(content)

print("HAProxy configuration written to", cfg_output)