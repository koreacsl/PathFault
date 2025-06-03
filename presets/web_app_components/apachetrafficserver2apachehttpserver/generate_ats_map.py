import os

ATS_MAP_FILE = "/usr/local/etc/trafficserver/remap.config"
TMP_SERVER_PORT = os.getenv("TMP_SERVER_PORT", "8000")

def generate_ats_map():
    try:
        with open(ATS_MAP_FILE, "w") as ats_file:
            ats_file.write(f"map / http://apachehttpserver:{8001}/\n")

        print(f"ATS remap file generated at {ATS_MAP_FILE}, all requests forwarded to apachehttpserver:{8001}")
    except Exception as e:
        print(f"Error generating ATS remap file: {e}")

if __name__ == "__main__":
    generate_ats_map()